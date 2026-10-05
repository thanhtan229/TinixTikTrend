from datetime import datetime, timezone, timedelta
from typing import List, Optional
from pydantic import BaseModel


def ensure_utc(dt: datetime) -> datetime:
    return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt.astimezone(timezone.utc)


class SnapshotData(BaseModel):
    captured_at: datetime
    sold_count: Optional[int] = None
    review_count: Optional[int] = None
    rating: Optional[float] = None
    price: Optional[float] = None
    original_price: Optional[float] = None
    commission_rate: Optional[float] = None


class DeltaMetrics(BaseModel):
    latest_sold_count: Optional[int] = None
    latest_review_count: Optional[int] = None
    latest_rating: Optional[float] = None
    latest_price: Optional[float] = None
    latest_commission_rate: Optional[float] = None
    sold_delta_6h: Optional[int] = None
    sold_delta_12h: Optional[int] = None
    sold_delta_24h: Optional[int] = None
    sold_delta_7d: Optional[int] = None
    review_delta_24h: Optional[int] = None
    review_delta_7d: Optional[int] = None
    sales_velocity_24h: Optional[float] = None
    sales_acceleration: Optional[float] = None
    is_anomaly: bool = False
    is_stale: bool = False
    velocity_is_estimated: bool = False
    has_24h_window: bool = False
    has_7d_window: bool = False
    primary_elapsed_hours: Optional[float] = None
    last_observed_at: Optional[datetime] = None


def find_closest_snapshot(snapshots: List[SnapshotData], target_time: datetime,
                          max_tolerance_seconds: int = 3600) -> Optional[SnapshotData]:
    target = ensure_utc(target_time)
    candidates = [s for s in snapshots
                  if abs((ensure_utc(s.captured_at) - target).total_seconds()) <= max_tolerance_seconds]
    return min(candidates, key=lambda s: abs((ensure_utc(s.captured_at) - target).total_seconds())) if candidates else None


def calculate_delta(latest_val: Optional[int], past_val: Optional[int]) -> Optional[int]:
    return None if latest_val is None or past_val is None else max(0, latest_val - past_val)


def calculate_product_deltas(snapshots: List[SnapshotData], current_time: Optional[datetime] = None) -> DeltaMetrics:
    if not snapshots:
        return DeltaMetrics()
    ordered = sorted(snapshots, key=lambda s: ensure_utc(s.captured_at))
    latest = ordered[-1]
    observed = ensure_utc(latest.captured_at)
    now = ensure_utc(current_time) if current_time else observed
    metrics = DeltaMetrics(latest_sold_count=latest.sold_count, latest_review_count=latest.review_count,
        latest_rating=latest.rating, latest_price=latest.price,
        latest_commission_rate=latest.commission_rate, last_observed_at=observed,
        is_stale=(now - observed).total_seconds() > 8 * 3600 or observed > now + timedelta(minutes=5),
        is_anomaly=any(a.sold_count is not None and b.sold_count is not None and b.sold_count < a.sold_count
                       for a, b in zip(ordered, ordered[1:])))
    if metrics.is_stale:
        return metrics
    past = ordered[:-1]
    anchors = {}
    for label, hours in [('6h', 6), ('12h', 12), ('24h', 24), ('7d', 168)]:
        # Narrow coverage on both sides; sparse history is not a full window.
        anchor = find_closest_snapshot(past, observed - timedelta(hours=hours), 3600 if hours < 168 else 4*3600)
        anchors[label] = anchor
        if anchor:
            setattr(metrics, 'sold_delta_' + label, calculate_delta(latest.sold_count, anchor.sold_count))
            if label in ('24h', '7d'):
                setattr(metrics, 'review_delta_' + label, calculate_delta(latest.review_count, anchor.review_count))
    metrics.has_24h_window = anchors.get('24h') is not None
    metrics.has_7d_window = anchors.get('7d') is not None
    # Prefer recent coverage and scale by the actual elapsed interval.
    baseline = next((anchors[k] for k in ('24h', '12h', '6h')
                     if anchors[k] and anchors[k].sold_count is not None), None)
    if baseline is None:
        recent = [s for s in past if s.sold_count is not None
                  and 0.5 <= (observed - ensure_utc(s.captured_at)).total_seconds()/3600 <= 24]
        baseline = recent[0] if recent else None
    if baseline and latest.sold_count is not None:
        hours = (observed - ensure_utc(baseline.captured_at)).total_seconds()/3600
        metrics.sales_velocity_24h = calculate_delta(latest.sold_count, baseline.sold_count) * 24 / hours
        metrics.velocity_is_estimated = abs(hours - 24) > 0.05
        metrics.primary_elapsed_hours = round(hours, 2)
    # Two disjoint comparable periods are necessary for acceleration.
    for width, recent_key, older_key in [(6, '6h', '12h'), (12, '12h', '24h')]:
        recent, older = anchors[recent_key], anchors[older_key]
        if not recent or not older or recent is older:
            continue
        current_delta = calculate_delta(latest.sold_count, recent.sold_count)
        prior_delta = calculate_delta(recent.sold_count, older.sold_count)
        first_hours = (observed - ensure_utc(recent.captured_at)).total_seconds()/3600
        prior_hours = (ensure_utc(recent.captured_at) - ensure_utc(older.captured_at)).total_seconds()/3600
        if current_delta is not None and prior_delta is not None and first_hours > 0 and prior_hours > 0:
            metrics.sales_acceleration = current_delta * width / first_hours - prior_delta * width / prior_hours
            break
    return metrics
