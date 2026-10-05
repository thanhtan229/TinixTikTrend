from datetime import datetime, timezone, timedelta
from typing import List, Optional, Tuple, Dict, Any
import math
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, desc, asc

from app.models.product import Product
from app.models.product_snapshot import ProductSnapshot
from app.models.alert_rule import AlertRule
from app.models.alert_event import AlertEvent
from app.analytics.deltas import SnapshotData, calculate_product_deltas, ensure_utc
from app.analytics.scoring import calculate_trend_score
from app.analytics.evidence import calculate_trend_evidence
from app.core.logging import logger, log_event


VALID_RULE_TYPES = {"sales_velocity_above", "trend_score_above", "price_change_pct"}
VALID_PRICE_DIRECTIONS = {"up", "down", "either"}


class AlertEvaluationResult:
    def __init__(
        self,
        rule: AlertRule,
        condition_met: bool,
        is_crossing: bool,
        is_suppressed: bool,
        should_emit: bool,
        actual_value: float,
        actual_direction: Optional[str],
        message: str,
    ):
        self.rule = rule
        self.condition_met = condition_met
        self.is_crossing = is_crossing
        self.is_suppressed = is_suppressed
        self.should_emit = should_emit
        self.actual_value = actual_value
        self.actual_direction = actual_direction
        self.message = message


class AlertService:
    def __init__(self, db: Session):
        self.db = db

    def validate_rule_params(
        self,
        rule_type: str,
        threshold: float,
        direction: Optional[str] = None,
        cooldown_minutes: int = 0,
    ) -> None:
        if rule_type not in VALID_RULE_TYPES:
            raise ValueError(f"Invalid rule_type '{rule_type}'. Must be one of {sorted(VALID_RULE_TYPES)}")

        if not math.isfinite(threshold) or threshold <= 0:
            raise ValueError("Threshold must be a finite number strictly greater than 0.")

        if cooldown_minutes < 0:
            raise ValueError("cooldown_minutes must be greater than or equal to 0.")

        if rule_type == "price_change_pct":
            if not direction or direction not in VALID_PRICE_DIRECTIONS:
                raise ValueError("Direction is required for price_change_pct and must be 'up', 'down', or 'either'.")
        else:
            if direction is not None:
                raise ValueError(f"Direction is not permitted for non-price rule '{rule_type}'.")

    def create_rule(
        self,
        product_id: int,
        rule_type: str,
        threshold: float,
        direction: Optional[str] = None,
        cooldown_minutes: int = 0,
    ) -> AlertRule:
        self.validate_rule_params(
            rule_type=rule_type,
            threshold=threshold,
            direction=direction,
            cooldown_minutes=cooldown_minutes,
        )

        product = self.db.get(Product, product_id)
        if product is None:
            raise ValueError(f"Product {product_id} not found.")

        # Baseline initialization: no retroactive baseline alerts
        latest_snapshot = (
            self.db.query(ProductSnapshot)
            .filter(ProductSnapshot.product_id == product_id)
            .order_by(desc(ProductSnapshot.captured_at), desc(ProductSnapshot.id))
            .first()
        )

        initial_cursor = latest_snapshot.id if latest_snapshot else None
        initial_condition_met = False

        if latest_snapshot:
            # Check if condition is already met on latest snapshot
            initial_condition_met = self._check_condition_on_snapshot(
                product=product,
                snapshot=latest_snapshot,
                rule_type=rule_type,
                threshold=threshold,
                direction=direction,
            )

        rule = AlertRule(
            product_id=product_id,
            rule_type=rule_type,
            threshold=threshold,
            direction=direction,
            cooldown_minutes=cooldown_minutes,
            is_enabled=True,
            last_evaluated_snapshot_id=initial_cursor,
            last_condition_met=initial_condition_met,
            last_triggered_at=None,
        )
        self.db.add(rule)
        self.db.commit()
        self.db.refresh(rule)
        return rule

    def update_rule(
        self,
        rule_id: int,
        threshold: Optional[float] = None,
        direction: Optional[str] = None,
        cooldown_minutes: Optional[int] = None,
        is_enabled: Optional[bool] = None,
    ) -> AlertRule:
        rule = self.db.get(AlertRule, rule_id)
        if rule is None:
            raise ValueError(f"AlertRule {rule_id} not found.")

        new_rule_type = rule.rule_type
        new_threshold = threshold if threshold is not None else rule.threshold
        new_direction = direction if direction is not None else rule.direction
        new_cooldown = cooldown_minutes if cooldown_minutes is not None else rule.cooldown_minutes

        self.validate_rule_params(
            rule_type=new_rule_type,
            threshold=new_threshold,
            direction=new_direction,
            cooldown_minutes=new_cooldown,
        )

        re_enabling = (is_enabled is True and not rule.is_enabled)
        threshold_changed = (threshold is not None and threshold != rule.threshold)

        rule.threshold = new_threshold
        rule.direction = new_direction
        rule.cooldown_minutes = new_cooldown
        if is_enabled is not None:
            rule.is_enabled = is_enabled

        # Baseline reset on edit or re-enable: no retroactive alerts
        if re_enabling or threshold_changed:
            product = self.db.get(Product, rule.product_id)
            latest_snapshot = (
                self.db.query(ProductSnapshot)
                .filter(ProductSnapshot.product_id == rule.product_id)
                .order_by(desc(ProductSnapshot.captured_at), desc(ProductSnapshot.id))
                .first()
            )
            if latest_snapshot:
                rule.last_evaluated_snapshot_id = latest_snapshot.id
                rule.last_condition_met = self._check_condition_on_snapshot(
                    product=product,
                    snapshot=latest_snapshot,
                    rule_type=new_rule_type,
                    threshold=new_threshold,
                    direction=new_direction,
                )

        self.db.commit()
        self.db.refresh(rule)
        return rule

    def delete_rule(self, rule_id: int) -> bool:
        rule = self.db.get(AlertRule, rule_id)
        if rule is None:
            return False
        self.db.delete(rule)
        self.db.commit()
        return True

    def get_rules_for_product(self, product_id: int) -> List[AlertRule]:
        return self.db.query(AlertRule).filter(AlertRule.product_id == product_id).all()

    def get_active_rules_for_product(self, product_id: int) -> List[AlertRule]:
        return (
            self.db.query(AlertRule)
            .filter(AlertRule.product_id == product_id, AlertRule.is_enabled == True)
            .all()
        )

    def _check_condition_on_snapshot(
        self,
        product: Product,
        snapshot: ProductSnapshot,
        rule_type: str,
        threshold: float,
        direction: Optional[str],
    ) -> bool:
        """Helper to check if condition is satisfied on a single snapshot without side effects."""
        res = self._compute_rule_condition(
            product=product,
            snapshot=snapshot,
            rule_type=rule_type,
            threshold=threshold,
            direction=direction,
        )
        return res[0]

    def _get_bounded_snapshots_as_of(
        self, product_id: int, as_of_time: datetime
    ) -> List[ProductSnapshot]:
        """Loads bounded snapshots for as-of evaluation (up to 172 hours before as_of_time)."""
        window_start = as_of_time - timedelta(hours=172)
        return (
            self.db.query(ProductSnapshot)
            .filter(
                ProductSnapshot.product_id == product_id,
                ProductSnapshot.captured_at <= as_of_time,
                ProductSnapshot.captured_at >= window_start,
            )
            .order_by(asc(ProductSnapshot.captured_at), asc(ProductSnapshot.id))
            .all()
        )

    def _compute_rule_condition(
        self,
        product: Product,
        snapshot: ProductSnapshot,
        rule_type: str,
        threshold: float,
        direction: Optional[str],
        precomputed_analytics: Optional[Dict[str, Any]] = None,
    ) -> Tuple[bool, float, Optional[str], str]:
        """
        Computes (condition_met, actual_value, actual_direction, message)
        deterministic for snapshot as-of snapshot.captured_at.
        """
        as_of_time = ensure_utc(snapshot.captured_at)

        if rule_type == "price_change_pct":
            # Price rule requires previous snapshot with positive price
            prev_snapshot = (
                self.db.query(ProductSnapshot)
                .filter(
                    ProductSnapshot.product_id == product.id,
                    ProductSnapshot.captured_at < as_of_time,
                    ProductSnapshot.price.is_not(None),
                    ProductSnapshot.price > 0,
                )
                .order_by(desc(ProductSnapshot.captured_at), desc(ProductSnapshot.id))
                .first()
            )

            current_price = snapshot.price
            if current_price is None or current_price <= 0 or prev_snapshot is None or prev_snapshot.price is None or prev_snapshot.price <= 0:
                return False, 0.0, None, "Không đủ dữ liệu giá để so sánh."

            prev_price = prev_snapshot.price
            pct_change = ((current_price - prev_price) / prev_price) * 100.0
            actual_dir = "up" if pct_change >= 0 else "down"

            condition_met = False
            if direction == "up":
                condition_met = (pct_change >= threshold)
            elif direction == "down":
                condition_met = (-pct_change >= threshold)
            elif direction == "either":
                condition_met = (abs(pct_change) >= threshold)

            # Never describe as "trending"
            if actual_dir == "up":
                msg = f"Giá tăng +{pct_change:.1f}% (từ {prev_price:,.0f} đ lên {current_price:,.0f} đ)"
            else:
                msg = f"Giá giảm {pct_change:.1f}% (từ {prev_price:,.0f} đ xuống {current_price:,.0f} đ)"

            return condition_met, pct_change, actual_dir, msg

        # Non-price rules share Phase 2 analytics
        if precomputed_analytics is None:
            snapshots = self._get_bounded_snapshots_as_of(product.id, as_of_time)
            snap_data = [
                SnapshotData(
                    captured_at=s.captured_at,
                    sold_count=s.sold_count,
                    review_count=s.review_count,
                    rating=s.rating,
                    price=s.price,
                    original_price=s.original_price,
                    commission_rate=s.commission_rate,
                )
                for s in snapshots
            ]
            deltas = calculate_product_deltas(snap_data, current_time=as_of_time)
            trend_score = calculate_trend_score(
                deltas, first_seen_at=product.first_seen_at, current_time=as_of_time
            )
            evidence = calculate_trend_evidence(snap_data, deltas, current_time=as_of_time)
            analytics = {
                "deltas": deltas,
                "trend_score": trend_score,
                "evidence": evidence,
            }
        else:
            analytics = precomputed_analytics

        deltas = analytics["deltas"]
        trend_score = analytics["trend_score"]
        evidence = analytics["evidence"]

        if rule_type == "sales_velocity_above":
            # Phase 2 gating: must have measured/eligible signal; velocity cannot be None or estimated
            if evidence.ranking_state != "eligible" or deltas.sales_velocity_24h is None:
                return False, 0.0, None, "Chưa đủ dữ liệu tốc độ bán đo lường được."
            
            velocity = deltas.sales_velocity_24h
            condition_met = (velocity >= threshold)
            msg = f"Tốc độ bán đạt {velocity:.1f} đơn/ngày (vượt ngưỡng {threshold:.1f})"
            return condition_met, velocity, None, msg

        elif rule_type == "trend_score_above":
            # Phase 2 gating: must be eligible; stale or insufficient signal cannot qualify
            if evidence.ranking_state != "eligible":
                return False, 0.0, None, "Sản phẩm chưa đủ điều kiện tính điểm xu hướng hợp lệ."

            condition_met = (trend_score >= threshold)
            msg = f"Điểm xu hướng đạt {trend_score:.1f} (vượt ngưỡng {threshold:.1f})"
            return condition_met, trend_score, None, msg

        return False, 0.0, None, "Loại quy tắc không xác định."

    def evaluate_rule_against_snapshot(
        self,
        rule: AlertRule,
        product: Product,
        snapshot: ProductSnapshot,
        precomputed_analytics: Optional[Dict[str, Any]] = None,
    ) -> AlertEvaluationResult:
        """
        Evaluates a single rule against a snapshot.
        Enforces false-to-true crossing and cooldown semantics.
        """
        condition_met, actual_value, actual_direction, message = self._compute_rule_condition(
            product=product,
            snapshot=snapshot,
            rule_type=rule.rule_type,
            threshold=rule.threshold,
            direction=rule.direction,
            precomputed_analytics=precomputed_analytics,
        )

        is_crossing = (not rule.last_condition_met) and condition_met

        is_suppressed = False
        should_emit = False

        if is_crossing:
            # Check cooldown window
            trigger_time = ensure_utc(snapshot.captured_at)
            if rule.cooldown_minutes > 0 and rule.last_triggered_at is not None:
                last_triggered = ensure_utc(rule.last_triggered_at)
                cooldown_delta = timedelta(minutes=rule.cooldown_minutes)
                # Suppress ONLY when trigger_time - last_triggered_at < cooldown_duration
                # Exact boundary and after boundary are eligible!
                if trigger_time - last_triggered < cooldown_delta:
                    is_suppressed = True

            if not is_suppressed:
                should_emit = True

        return AlertEvaluationResult(
            rule=rule,
            condition_met=condition_met,
            is_crossing=is_crossing,
            is_suppressed=is_suppressed,
            should_emit=should_emit,
            actual_value=actual_value,
            actual_direction=actual_direction,
            message=message,
        )

    def evaluate_snapshot(self, product_id: int, snapshot_id: int) -> List[AlertEvent]:
        """
        Evaluates all active rules for product_id on snapshot_id in a single atomic transaction.
        Advances cursors and condition states.
        """
        product = self.db.get(Product, product_id)
        snapshot = self.db.get(ProductSnapshot, snapshot_id)
        if product is None or snapshot is None:
            return []

        rules = self.get_active_rules_for_product(product_id)
        if not rules:
            return []

        # Filter to rules where snapshot_id > last_evaluated_snapshot_id
        pending_rules = [
            r for r in rules
            if r.last_evaluated_snapshot_id is None or snapshot.id > r.last_evaluated_snapshot_id
        ]
        if not pending_rules:
            return []

        # Precompute analytics once for non-price rules
        as_of_time = ensure_utc(snapshot.captured_at)
        bounded_snapshots = self._get_bounded_snapshots_as_of(product.id, as_of_time)
        snap_data = [
            SnapshotData(
                captured_at=s.captured_at,
                sold_count=s.sold_count,
                review_count=s.review_count,
                rating=s.rating,
                price=s.price,
                original_price=s.original_price,
                commission_rate=s.commission_rate,
            )
            for s in bounded_snapshots
        ]
        deltas = calculate_product_deltas(snap_data, current_time=as_of_time)
        trend_score = calculate_trend_score(
            deltas, first_seen_at=product.first_seen_at, current_time=as_of_time
        )
        evidence = calculate_trend_evidence(snap_data, deltas, current_time=as_of_time)
        precomputed = {
            "deltas": deltas,
            "trend_score": trend_score,
            "evidence": evidence,
        }

        emitted_events = []
        try:
            for rule in pending_rules:
                eval_res = self.evaluate_rule_against_snapshot(
                    rule=rule,
                    product=product,
                    snapshot=snapshot,
                    precomputed_analytics=precomputed,
                )

                rule.last_evaluated_snapshot_id = snapshot.id
                rule.last_condition_met = eval_res.condition_met

                if eval_res.should_emit:
                    rule.last_triggered_at = snapshot.captured_at
                    event = AlertEvent(
                        rule_id=rule.id,
                        product_id=product.id,
                        triggering_snapshot_id=snapshot.id,
                        rule_type=rule.rule_type,
                        threshold=rule.threshold,
                        actual_value=eval_res.actual_value,
                        actual_direction=eval_res.actual_direction,
                        message=eval_res.message,
                        is_read=False,
                        created_at=snapshot.captured_at,
                    )
                    self.db.add(event)
                    emitted_events.append(event)

            self.db.commit()
            return emitted_events
        except Exception:
            self.db.rollback()
            raise

    def catch_up_alerts(self, max_batch_snapshots: int = 1000) -> int:
        """
        Synchronously replays un-evaluated snapshots for all active rules in chronological order.
        Returns total number of alert events emitted.
        Fails / raises exception if any error occurs.
        """
        active_rules = self.db.query(AlertRule).filter(AlertRule.is_enabled == True).all()
        if not active_rules:
            return 0

        # Group rules by product_id
        product_rules: Dict[int, List[AlertRule]] = {}
        for r in active_rules:
            product_rules.setdefault(r.product_id, []).append(r)

        total_emitted = 0

        for product_id, rules in product_rules.items():
            product = self.db.get(Product, product_id)
            if not product:
                continue

            # Determine minimum evaluated cursor across rules for this product
            min_cursor = min((r.last_evaluated_snapshot_id or 0) for r in rules)

            # Query all pending snapshots for this product above min_cursor
            pending_snapshots = (
                self.db.query(ProductSnapshot)
                .filter(
                    ProductSnapshot.product_id == product_id,
                    ProductSnapshot.id > min_cursor,
                )
                .order_by(asc(ProductSnapshot.captured_at), asc(ProductSnapshot.id))
                .limit(max_batch_snapshots)
                .all()
            )

            for snapshot in pending_snapshots:
                events = self.evaluate_snapshot(product_id=product.id, snapshot_id=snapshot.id)
                total_emitted += len(events)

        log_event("alert_catch_up", f"Alert catch-up completed with {total_emitted} events emitted.")
        return total_emitted

    # Event query and read state methods
    def get_events(
        self,
        product_id: Optional[int] = None,
        is_read: Optional[bool] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> Tuple[List[AlertEvent], int]:
        q = self.db.query(AlertEvent)
        if product_id is not None:
            q = q.filter(AlertEvent.product_id == product_id)
        if is_read is not None:
            q = q.filter(AlertEvent.is_read == is_read)

        total = q.count()
        events = (
            q.order_by(desc(AlertEvent.created_at), desc(AlertEvent.id))
            .offset(skip)
            .limit(limit)
            .all()
        )
        return events, total

    def get_unread_count(self) -> int:
        return self.db.query(AlertEvent).filter(AlertEvent.is_read == False).count()

    def mark_event_read(self, event_id: int) -> bool:
        event = self.db.get(AlertEvent, event_id)
        if event is None:
            return False
        event.is_read = True
        self.db.commit()
        return True

    def mark_all_events_read(self, product_id: Optional[int] = None) -> int:
        q = self.db.query(AlertEvent).filter(AlertEvent.is_read == False)
        if product_id is not None:
            q = q.filter(AlertEvent.product_id == product_id)
        
        count = 0
        for ev in q.all():
            ev.is_read = True
            count += 1
        self.db.commit()
        return count
