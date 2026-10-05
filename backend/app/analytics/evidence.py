from datetime import datetime, timezone
from typing import List, Optional, Dict
from pydantic import BaseModel
from app.analytics.config import AnalyticsConfig, default_analytics_config
from app.analytics.deltas import DeltaMetrics, SnapshotData, ensure_utc
from app.analytics.normalization import log_scale_score
from app.analytics.scoring import has_trend_evidence


class PrimarySignalInterval(BaseModel):
    elapsed_hours: Optional[float] = None
    is_estimated: bool = False


class TrendEvidence(BaseModel):
    observation_count: int
    observation_span_hours: float
    latest_observation_age_hours: float
    ranking_state: str  # "eligible" | "stale" | "insufficient_measured_signal"
    confidence: str  # "low" | "medium" | "high"
    primary_signal_interval: Optional[PrimarySignalInterval] = None
    signals: Dict[str, str] = {}  # "measured" | "estimated" | "missing"
    has_24h_window: bool = False
    has_7d_window: bool = False
    missing_metrics: List[str] = []


class TrendReason(BaseModel):
    reason_code: str  # "sales_velocity_up" | "sales_acceleration_up" | "review_velocity_up"
    contribution: float
    value: float
    formatted_text: str


def calculate_trend_evidence(
    snapshots: List[SnapshotData],
    deltas: DeltaMetrics,
    current_time: Optional[datetime] = None,
) -> TrendEvidence:
    """
    Computes deterministic evidence sufficiency and confidence for trend ranking.
    Separates data quality from score strength without multiplying them together.
    """
    now = ensure_utc(current_time) if current_time else datetime.now(timezone.utc)
    obs_count = len(snapshots)

    if obs_count == 0:
        return TrendEvidence(
            observation_count=0,
            observation_span_hours=0.0,
            latest_observation_age_hours=0.0,
            ranking_state="stale",
            confidence="low",
            signals={
                "sales_velocity": "missing",
                "sales_acceleration": "missing",
                "review_velocity": "missing",
            },
            has_24h_window=False,
            has_7d_window=False,
            missing_metrics=[
                "sales_velocity_24h",
                "sales_acceleration",
                "review_delta_24h",
                "sold_delta_7d",
                "review_delta_7d",
                "rating",
                "price",
                "commission_rate",
            ],
        )

    ordered = sorted(snapshots, key=lambda s: ensure_utc(s.captured_at))
    earliest_dt = ensure_utc(ordered[0].captured_at)
    latest_dt = ensure_utc(ordered[-1].captured_at)

    span_hours = round(max(0.0, (latest_dt - earliest_dt).total_seconds() / 3600.0), 1)
    age_hours = round(max(0.0, (now - latest_dt).total_seconds() / 3600.0), 1)

    # Ranking state
    if deltas.is_stale:
        ranking_state = "stale"
    elif not has_trend_evidence(deltas):
        ranking_state = "insufficient_measured_signal"
    else:
        ranking_state = "eligible"

    # Per-signal evidence status
    sales_velocity_status = "missing"
    if deltas.sales_velocity_24h is not None:
        sales_velocity_status = "estimated" if deltas.velocity_is_estimated else "measured"

    sales_accel_status = "missing" if deltas.sales_acceleration is None else "measured"
    review_velocity_status = "missing" if deltas.review_delta_24h is None else "measured"

    signals = {
        "sales_velocity": sales_velocity_status,
        "sales_acceleration": sales_accel_status,
        "review_velocity": review_velocity_status,
    }

    # Primary signal interval metadata
    primary_interval = PrimarySignalInterval(
        elapsed_hours=deltas.primary_elapsed_hours,
        is_estimated=deltas.velocity_is_estimated,
    )

    # Missing metrics list
    missing_metrics: List[str] = []
    if deltas.sales_velocity_24h is None:
        missing_metrics.append("sales_velocity_24h")
    if deltas.sales_acceleration is None:
        missing_metrics.append("sales_acceleration")
    if deltas.review_delta_24h is None:
        missing_metrics.append("review_delta_24h")
    if deltas.sold_delta_7d is None:
        missing_metrics.append("sold_delta_7d")
    if deltas.review_delta_7d is None:
        missing_metrics.append("review_delta_7d")
    if deltas.latest_rating is None:
        missing_metrics.append("rating")
    if deltas.latest_price is None:
        missing_metrics.append("price")
    if deltas.latest_commission_rate is None:
        missing_metrics.append("commission_rate")

    # Deterministic Confidence Semantics:
    # LOW: Ineligible or only minimum measured evidence or estimated-only interval
    # MEDIUM: Fresh latest observation (age <= 8h), at least 1 measured sales/review interval, >=3 observations spanning >=8h
    # HIGH: Fresh latest observation (age <= 8h), at least 1 measured ~24h comparison (has_24h_window=True), >=5 observations spanning >=20h, primary interval NOT estimated
    has_measured_interval = any(
        v is not None
        for v in (
            deltas.sold_delta_6h,
            deltas.sold_delta_12h,
            deltas.sold_delta_24h,
            deltas.review_delta_24h,
        )
    )

    if ranking_state != "eligible" or age_hours > 8.0:
        confidence = "low"
    elif (
        obs_count >= 5
        and span_hours >= 20.0
        and deltas.has_24h_window
        and not deltas.velocity_is_estimated
    ):
        confidence = "high"
    elif (
        obs_count >= 3
        and span_hours >= 8.0
        and has_measured_interval
    ):
        confidence = "medium"
    else:
        confidence = "low"

    return TrendEvidence(
        observation_count=obs_count,
        observation_span_hours=span_hours,
        latest_observation_age_hours=age_hours,
        ranking_state=ranking_state,
        confidence=confidence,
        primary_signal_interval=primary_interval,
        signals=signals,
        has_24h_window=deltas.has_24h_window,
        has_7d_window=deltas.has_7d_window,
        missing_metrics=missing_metrics,
    )


def calculate_trend_reasons(
    deltas: DeltaMetrics,
    trend_score: float,
    config: AnalyticsConfig = default_analytics_config,
) -> List[TrendReason]:
    """
    Computes at most 2-3 deterministic "Why trending?" reasons ordered by numeric component contribution descending.
    Uses structured reason codes with localized fallback messages.
    """
    if deltas.is_stale or not has_trend_evidence(deltas) or trend_score <= 0.0:
        return []

    weights = config.weights
    candidates: List[TrendReason] = []

    # 1. Sales velocity
    if deltas.sales_velocity_24h is not None and deltas.sales_velocity_24h > 0:
        velocity_score = log_scale_score(deltas.sales_velocity_24h, midpoint=300.0, target_max=100.0)
        contrib = round(velocity_score * weights.sales_velocity, 2)
        val = round(deltas.sales_velocity_24h, 1)
        if deltas.velocity_is_estimated and deltas.primary_elapsed_hours:
            txt = f"Tốc độ bán ước tính +{round(val)} đơn/ngày (chu kỳ {deltas.primary_elapsed_hours}h)"
        elif deltas.sold_delta_24h is not None:
            txt = f"Tăng +{deltas.sold_delta_24h} đơn trong ~24h (đo lường {deltas.primary_elapsed_hours or 24}h)"
        else:
            txt = f"Tốc độ bán +{round(val)} đơn/ngày trong ~24h"
        candidates.append(TrendReason(
            reason_code="sales_velocity_up",
            contribution=contrib,
            value=val,
            formatted_text=txt,
        ))

    # 2. Sales acceleration
    if deltas.sales_acceleration is not None and deltas.sales_acceleration > 0:
        accel_boost = log_scale_score(deltas.sales_acceleration, midpoint=150.0, target_max=50.0)
        contrib = round(accel_boost * weights.sales_acceleration, 2)
        val = round(deltas.sales_acceleration, 1)
        txt = f"Gia tốc bán hàng tăng +{round(val)} đơn/ngày so với chu kỳ trước"
        candidates.append(TrendReason(
            reason_code="sales_acceleration_up",
            contribution=contrib,
            value=val,
            formatted_text=txt,
        ))

    # 3. Review velocity
    if deltas.review_delta_24h is not None and deltas.review_delta_24h > 0:
        review_score = log_scale_score(deltas.review_delta_24h, midpoint=30.0, target_max=100.0)
        contrib = round(review_score * weights.review_velocity, 2)
        val = float(deltas.review_delta_24h)
        txt = f"+{deltas.review_delta_24h} lượt đánh giá mới trong ~24h"
        candidates.append(TrendReason(
            reason_code="review_velocity_up",
            contribution=contrib,
            value=val,
            formatted_text=txt,
        ))

    tie_break_priority = {
        "sales_velocity_up": 0,
        "sales_acceleration_up": 1,
        "review_velocity_up": 2,
    }
    candidates.sort(key=lambda r: (-r.contribution, tie_break_priority.get(r.reason_code, 99)))
    return candidates[:3]
