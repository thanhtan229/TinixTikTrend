from datetime import datetime, timezone
from typing import Optional
from app.analytics.config import AnalyticsConfig, default_analytics_config
from app.analytics.deltas import DeltaMetrics, ensure_utc
from app.analytics.normalization import clamp, log_scale_score, normalize_min_max


def has_trend_evidence(deltas: DeltaMetrics) -> bool:
    """Require measured recent sales/review momentum before assigning trend score."""
    return any(value is not None for value in (
        deltas.sales_velocity_24h, deltas.sales_acceleration, deltas.review_delta_24h,
    ))


def calculate_freshness_score(
    first_seen_at: datetime,
    current_time: Optional[datetime] = None,
    max_days: float = 14.0,
) -> float:
    """
    Freshness score: 100 for newly detected (today), decaying down to 0 at max_days.
    """
    t_now = ensure_utc(current_time) if current_time is not None else datetime.now(timezone.utc)
    t_first = ensure_utc(first_seen_at)
        
    days_old = max(0.0, (t_now - t_first).total_seconds() / 86400.0)
    if days_old >= max_days:
        return 0.0
    
    return clamp(100.0 * (1.0 - (days_old / max_days)), 0.0, 100.0)


def calculate_rating_score(rating: Optional[float], min_threshold: float = 3.5) -> float:
    """
    Scales rating from min_threshold (0 pts) to 5.0 (100 pts).
    """
    if rating is None or rating <= 0:
        # Neutral baseline if rating not available
        return 50.0
    
    if rating <= min_threshold:
        return 0.0
        
    return clamp(((rating - min_threshold) / (5.0 - min_threshold)) * 100.0, 0.0, 100.0)


def calculate_trend_score(
    deltas: DeltaMetrics,
    first_seen_at: datetime,
    config: AnalyticsConfig = default_analytics_config,
    current_time: Optional[datetime] = None,
) -> float:
    """
    Calculates the normalized Trend Score (0 to 100) combining:
    - sales_velocity (40%)
    - sales_acceleration (25%)
    - review_velocity (15%)
    - freshness (10%)
    - rating (10%)
    """
    if deltas.is_stale or not has_trend_evidence(deltas):
        return 0.0
    weights = config.weights
    
    # 1. Sales Velocity Score (0-100)
    # 500 units/day represents high velocity in local TikTok shop context
    velocity_score = log_scale_score(deltas.sales_velocity_24h, midpoint=300.0, target_max=100.0)
    
    # 2. Sales Acceleration Score (0-100)
    accel_score = 50.0  # Neutral baseline
    if deltas.sales_acceleration is not None:
        if deltas.sales_acceleration > 0:
            # Positive acceleration boosts up to 100
            accel_score = 50.0 + (log_scale_score(deltas.sales_acceleration, midpoint=150.0, target_max=50.0))
        else:
            # Negative acceleration decays down towards 0
            accel_score = 50.0 - (log_scale_score(abs(deltas.sales_acceleration), midpoint=150.0, target_max=50.0))
    accel_score = clamp(accel_score, 0.0, 100.0)
    
    # 3. Review Velocity Score (0-100)
    review_score = log_scale_score(deltas.review_delta_24h, midpoint=30.0, target_max=100.0)
    
    # 4. Freshness Score (0-100)
    fresh_score = calculate_freshness_score(first_seen_at, current_time, config.freshness_max_days)
    
    # 5. Rating Score (0-100)
    rat_score = calculate_rating_score(deltas.latest_rating, config.min_rating_threshold)
    
    # Total weighted score
    total_score = (
        (velocity_score * weights.sales_velocity) +
        (accel_score * weights.sales_acceleration) +
        (review_score * weights.review_velocity) +
        (fresh_score * weights.freshness) +
        (rat_score * weights.rating)
    )
    
    return round(clamp(total_score, 0.0, 100.0), 1)
