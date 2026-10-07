import time
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any, Callable, TypeVar
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import OperationalError, IntegrityError
from sqlalchemy import text

from app.models.economics_scenario import EconomicsScenario
from app.models.product import Product
from app.models.product_snapshot import ProductSnapshot
from app.models.quarantine import QuarantinedProduct
from app.analytics.economics import (
    compute_derived_economics,
    normalize_snapshot_price_to_vnd,
)
from app.schemas.economics import (
    EconomicsScenarioCreate,
    EconomicsScenarioUpdate,
)

T = TypeVar("T")


class EconomicsService:
    def __init__(self, db: Session):
        self.db = db

    def _verify_product_eligible(self, product_id: int) -> Product:
        """
        P6-AC-08: Quarantined products cannot have economics scenarios created, updated, or retrieved.
        Returns HTTP 400 for quarantined products, HTTP 404 if product does not exist.
        """
        quarantined = (
            self.db.query(QuarantinedProduct)
            .filter(QuarantinedProduct.product_id == product_id)
            .first()
        )
        if quarantined:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Sản phẩm {product_id} nằm trong danh sách cách ly (quarantine) và không thể áp dụng tính toán kinh tế.",
            )

        product = self.db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Không tìm thấy sản phẩm {product_id}.",
            )
        return product

    def _begin_immediate(self) -> None:
        """Acquires SQLite reserved lock immediately to eliminate write-race deadlocks."""
        try:
            self.db.connection().execute(text("BEGIN IMMEDIATE"))
        except OperationalError as e:
            if "cannot start a transaction within a transaction" in str(e).lower():
                pass
            else:
                raise

    def _run_with_retry(self, operation: Callable[[], T], max_retries: int = 3) -> T:
        """
        Executes write operation with immediate locking and bounded exponential backoff retries.
        Maps partial unique index conflicts and lock exhaustion to structured HTTP 409 Conflict.
        """
        delays = [0.05, 0.1, 0.2]
        for attempt in range(max_retries):
            try:
                self._begin_immediate()
                result = operation()
                self.db.commit()
                return result
            except (OperationalError, IntegrityError) as e:
                self.db.rollback()
                err_msg = str(e).lower()
                is_name_conflict = (
                    "uq_economics_scenarios_product_name" in err_msg
                    or "economics_scenarios.product_id, economics_scenarios.name" in err_msg
                    or ("unique constraint failed" in err_msg and "name" in err_msg)
                )
                if is_name_conflict:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="Tên kịch bản đã tồn tại cho sản phẩm này.",
                    )

                is_locked = "locked" in err_msg or "busy" in err_msg
                is_default_conflict = (
                    "uq_economics_scenarios_product_default" in err_msg
                    or ("unique constraint failed" in err_msg and "is_default" in err_msg)
                    or ("unique constraint failed" in err_msg and "economics_scenarios.product_id" in err_msg and "name" not in err_msg)
                )

                if (is_locked or is_default_conflict) and attempt < max_retries - 1:
                    time.sleep(delays[attempt])
                    continue

                if is_default_conflict:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="Xung đột kịch bản mặc định do thao tác đồng thời. Vui lòng thử lại.",
                    )
                if is_locked:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="Cơ sở dữ liệu đang bận do thao tác đồng thời. Vui lòng thử lại.",
                    )
                raise

    def _to_response_dict(self, scenario: EconomicsScenario) -> Dict[str, Any]:
        """Calculates derived metrics on read without persisting them to database (P6-AC-26)."""
        derived = compute_derived_economics(
            base_vnd=scenario.commission_base_vnd,
            rate_bps=scenario.commission_rate_bps,
            sample_cost_vnd=scenario.sample_cost_vnd,
            content_cost_vnd=scenario.content_cost_vnd,
            promotion_cost_vnd=scenario.promotion_cost_vnd,
            variable_cost_per_order_vnd=scenario.variable_cost_per_attributed_order_vnd,
            expected_orders=scenario.expected_attributed_orders,
        )
        return {
            "id": scenario.id,
            "product_id": scenario.product_id,
            "name": scenario.name,
            "commission_rate_bps": scenario.commission_rate_bps,
            "commission_base_vnd": scenario.commission_base_vnd,
            "commission_base_source": scenario.commission_base_source,
            "commission_base_observed_at": scenario.commission_base_observed_at,
            "sample_cost_vnd": scenario.sample_cost_vnd,
            "content_cost_vnd": scenario.content_cost_vnd,
            "promotion_cost_vnd": scenario.promotion_cost_vnd,
            "variable_cost_per_attributed_order_vnd": scenario.variable_cost_per_attributed_order_vnd,
            "expected_attributed_orders": scenario.expected_attributed_orders,
            "is_default": scenario.is_default,
            "created_at": scenario.created_at,
            "updated_at": scenario.updated_at,
            "derived": derived.to_dict(),
        }

    def list_scenarios(self, product_id: int) -> List[Dict[str, Any]]:
        """
        Lists all scenarios for an eligible product ordered by created_at ASC, id ASC.
        Query budget: <= 2 SQL queries total.
        """
        self._verify_product_eligible(product_id)
        scenarios = (
            self.db.query(EconomicsScenario)
            .filter(EconomicsScenario.product_id == product_id)
            .order_by(EconomicsScenario.created_at.asc(), EconomicsScenario.id.asc())
            .all()
        )
        return [self._to_response_dict(s) for s in scenarios]

    def get_scenario(self, product_id: int, scenario_id: int) -> Dict[str, Any]:
        """Gets single scenario with read-time derived metrics."""
        self._verify_product_eligible(product_id)
        scenario = (
            self.db.query(EconomicsScenario)
            .filter(
                EconomicsScenario.id == scenario_id,
                EconomicsScenario.product_id == product_id,
            )
            .first()
        )
        if not scenario:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Không tìm thấy kịch bản {scenario_id} cho sản phẩm {product_id}.",
            )
        return self._to_response_dict(scenario)

    def create_scenario(self, product_id: int, data: EconomicsScenarioCreate) -> Dict[str, Any]:
        """
        Creates a new scenario adhering to default invariants:
        - P6-AC-11: First scenario is auto-default.
        - P6-AC-12: Subsequent scenario defaults to false unless requested true.
        - P6-AC-27: Frozen observed price proxy handling.
        """
        self._verify_product_eligible(product_id)
        clean_name = data.name.strip()
        if not clean_name:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Tên kịch bản không được để trống.",
            )

        if data.use_observed_price:
            if data.commission_base_vnd is not None:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Cannot supply manual commission_base_vnd when use_observed_price is true",
                )
            latest_snapshot = (
                self.db.query(ProductSnapshot)
                .filter(ProductSnapshot.product_id == product_id)
                .order_by(ProductSnapshot.captured_at.desc())
                .first()
            )
            if not latest_snapshot or latest_snapshot.price is None or latest_snapshot.price <= 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Không tìm thấy giá snapshot hợp lệ để dùng làm giá quan sát đóng băng.",
                )
            commission_base_vnd = normalize_snapshot_price_to_vnd(latest_snapshot.price)
            commission_base_source = "observed_price_proxy"
            commission_base_observed_at = latest_snapshot.captured_at
        else:
            commission_base_vnd = data.commission_base_vnd
            commission_base_source = "user_entered"
            commission_base_observed_at = None

        def _op() -> EconomicsScenario:
            existing_name = (
                self.db.query(EconomicsScenario)
                .filter(
                    EconomicsScenario.product_id == product_id,
                    EconomicsScenario.name == clean_name,
                )
                .first()
            )
            if existing_name:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Tên kịch bản đã tồn tại cho sản phẩm này.",
                )

            # Check existing scenario count for default invariant
            existing_count = (
                self.db.query(EconomicsScenario)
                .filter(EconomicsScenario.product_id == product_id)
                .count()
            )
            if existing_count == 0:
                target_default = True
            else:
                if data.is_default:
                    # Clear current default atomically
                    self.db.query(EconomicsScenario).filter(
                        EconomicsScenario.product_id == product_id,
                        EconomicsScenario.is_default == True,
                    ).update({"is_default": False})
                    self.db.flush()
                    target_default = True
                else:
                    target_default = False

            scenario = EconomicsScenario(
                product_id=product_id,
                name=clean_name,
                commission_rate_bps=data.commission_rate_bps,
                commission_base_vnd=commission_base_vnd,
                commission_base_source=commission_base_source,
                commission_base_observed_at=commission_base_observed_at,
                sample_cost_vnd=data.sample_cost_vnd,
                content_cost_vnd=data.content_cost_vnd,
                promotion_cost_vnd=data.promotion_cost_vnd,
                variable_cost_per_attributed_order_vnd=data.variable_cost_per_attributed_order_vnd,
                expected_attributed_orders=data.expected_attributed_orders,
                is_default=target_default,
            )
            self.db.add(scenario)
            self.db.flush()
            return scenario

        created = self._run_with_retry(_op)
        self.db.refresh(created)
        return self._to_response_dict(created)

    def update_scenario(
        self, product_id: int, scenario_id: int, data: EconomicsScenarioUpdate
    ) -> Dict[str, Any]:
        """
        Updates scenario assumptions adhering to P6-AC-29:
        - Generic PATCH editing commission_base_vnd resets source to 'user_entered' and clears timestamp.
        - Client cannot write is_default or proxy metadata via PATCH.
        """
        self._verify_product_eligible(product_id)
        update_fields = data.model_dump(exclude_unset=True)

        def _op() -> EconomicsScenario:
            scenario = (
                self.db.query(EconomicsScenario)
                .filter(
                    EconomicsScenario.id == scenario_id,
                    EconomicsScenario.product_id == product_id,
                )
                .first()
            )
            if not scenario:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Không tìm thấy kịch bản {scenario_id} cho sản phẩm {product_id}.",
                )

            if "name" in update_fields and update_fields["name"] is not None:
                clean_name = update_fields["name"].strip()
                if not clean_name:
                    raise HTTPException(
                        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                        detail="Tên kịch bản không được để trống.",
                    )
                scenario.name = clean_name

            if "commission_base_vnd" in update_fields:
                scenario.commission_base_vnd = update_fields["commission_base_vnd"]
                scenario.commission_base_source = "user_entered"
                scenario.commission_base_observed_at = None

            for field in [
                "commission_rate_bps",
                "sample_cost_vnd",
                "content_cost_vnd",
                "promotion_cost_vnd",
                "variable_cost_per_attributed_order_vnd",
                "expected_attributed_orders",
            ]:
                if field in update_fields:
                    setattr(scenario, field, update_fields[field])

            scenario.updated_at = datetime.now(timezone.utc)
            self.db.flush()
            return scenario

        updated = self._run_with_retry(_op)
        self.db.refresh(updated)
        return self._to_response_dict(updated)

    def set_default(self, product_id: int, scenario_id: int) -> Dict[str, Any]:
        """
        Atomically switches default scenario (P6-AC-13).
        Clears is_default on siblings and sets is_default = True on target.
        """
        self._verify_product_eligible(product_id)

        def _op() -> EconomicsScenario:
            scenario = (
                self.db.query(EconomicsScenario)
                .filter(
                    EconomicsScenario.id == scenario_id,
                    EconomicsScenario.product_id == product_id,
                )
                .first()
            )
            if not scenario:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Không tìm thấy kịch bản {scenario_id} cho sản phẩm {product_id}.",
                )
            if scenario.is_default:
                return scenario

            self.db.query(EconomicsScenario).filter(
                EconomicsScenario.product_id == product_id,
                EconomicsScenario.is_default == True,
            ).update({"is_default": False})
            self.db.flush()

            scenario.is_default = True
            scenario.updated_at = datetime.now(timezone.utc)
            self.db.flush()
            return scenario

        scenario = self._run_with_retry(_op)
        self.db.refresh(scenario)
        return self._to_response_dict(scenario)

    def duplicate_scenario(
        self, product_id: int, scenario_id: int, new_name: str
    ) -> Dict[str, Any]:
        """
        Clones an existing scenario (P6-AC-30).
        Cloned scenario always defaults to is_default = false.
        """
        self._verify_product_eligible(product_id)
        clean_name = new_name.strip() if new_name else ""
        if not clean_name:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Tên kịch bản nhân bản không được để trống.",
            )

        def _op() -> EconomicsScenario:
            existing = (
                self.db.query(EconomicsScenario)
                .filter(
                    EconomicsScenario.product_id == product_id,
                    EconomicsScenario.name == clean_name,
                )
                .first()
            )
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Tên kịch bản '{clean_name}' đã tồn tại cho sản phẩm này.",
                )

            target = (
                self.db.query(EconomicsScenario)
                .filter(
                    EconomicsScenario.id == scenario_id,
                    EconomicsScenario.product_id == product_id,
                )
                .first()
            )
            if not target:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Không tìm thấy kịch bản {scenario_id} cho sản phẩm {product_id}.",
                )

            clone = EconomicsScenario(
                product_id=product_id,
                name=clean_name,
                commission_rate_bps=target.commission_rate_bps,
                commission_base_vnd=target.commission_base_vnd,
                commission_base_source=target.commission_base_source,
                commission_base_observed_at=target.commission_base_observed_at,
                sample_cost_vnd=target.sample_cost_vnd,
                content_cost_vnd=target.content_cost_vnd,
                promotion_cost_vnd=target.promotion_cost_vnd,
                variable_cost_per_attributed_order_vnd=target.variable_cost_per_attributed_order_vnd,
                expected_attributed_orders=target.expected_attributed_orders,
                is_default=False,
            )
            self.db.add(clone)
            self.db.flush()
            return clone

        cloned = self._run_with_retry(_op)
        self.db.refresh(cloned)
        return self._to_response_dict(cloned)

    def rebase_price(self, product_id: int, scenario_id: int) -> Dict[str, Any]:
        """
        Explicitly rebases commission base from latest snapshot price (P6-AC-31).
        """
        self._verify_product_eligible(product_id)

        latest_snapshot = (
            self.db.query(ProductSnapshot)
            .filter(ProductSnapshot.product_id == product_id)
            .order_by(ProductSnapshot.captured_at.desc())
            .first()
        )
        if not latest_snapshot or latest_snapshot.price is None or latest_snapshot.price <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Không tìm thấy giá snapshot hợp lệ để cập nhật giá cơ sở.",
            )

        new_base_vnd = normalize_snapshot_price_to_vnd(latest_snapshot.price)
        observed_at = latest_snapshot.captured_at

        def _op() -> EconomicsScenario:
            scenario = (
                self.db.query(EconomicsScenario)
                .filter(
                    EconomicsScenario.id == scenario_id,
                    EconomicsScenario.product_id == product_id,
                )
                .first()
            )
            if not scenario:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Không tìm thấy kịch bản {scenario_id} cho sản phẩm {product_id}.",
                )

            scenario.commission_base_vnd = new_base_vnd
            scenario.commission_base_source = "observed_price_proxy"
            scenario.commission_base_observed_at = observed_at
            scenario.updated_at = datetime.now(timezone.utc)
            self.db.flush()
            return scenario

        updated = self._run_with_retry(_op)
        self.db.refresh(updated)
        return self._to_response_dict(updated)

    def delete_scenario(self, product_id: int, scenario_id: int) -> None:
        """
        Deletes scenario with deterministic default promotion (P6-AC-14, P6-AC-15):
        - If deleted scenario was default and alternatives remain, atomically promotes
          the oldest remaining scenario ordered by (created_at ASC, id ASC).
        - If deleted scenario was sole scenario, leaves 0 scenarios and 0 defaults.
        """
        self._verify_product_eligible(product_id)

        def _op() -> None:
            scenario = (
                self.db.query(EconomicsScenario)
                .filter(
                    EconomicsScenario.id == scenario_id,
                    EconomicsScenario.product_id == product_id,
                )
                .first()
            )
            if not scenario:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Không tìm thấy kịch bản {scenario_id} cho sản phẩm {product_id}.",
                )

            was_default = scenario.is_default
            if was_default:
                scenario.is_default = False
                self.db.flush()

                remaining = (
                    self.db.query(EconomicsScenario)
                    .filter(
                        EconomicsScenario.product_id == product_id,
                        EconomicsScenario.id != scenario_id,
                    )
                    .order_by(EconomicsScenario.created_at.asc(), EconomicsScenario.id.asc())
                    .all()
                )
                if remaining:
                    oldest = remaining[0]
                    oldest.is_default = True
                    oldest.updated_at = datetime.now(timezone.utc)
                    self.db.flush()

            self.db.delete(scenario)
            self.db.flush()

        self._run_with_retry(_op)

    def get_default_scenarios_for_products(
        self, product_ids: List[int]
    ) -> Dict[int, Dict[str, Any]]:
        """
        Batch-fetches default scenarios for a list of products.
        Query budget: exactly 1 SQL query; zero N+1 queries.
        """
        if not product_ids:
            return {}
        scenarios = (
            self.db.query(EconomicsScenario)
            .filter(
                EconomicsScenario.product_id.in_(product_ids),
                EconomicsScenario.is_default == True,
            )
            .all()
        )
        return {s.product_id: self._to_response_dict(s) for s in scenarios}
