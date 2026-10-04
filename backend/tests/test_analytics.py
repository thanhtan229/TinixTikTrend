import pytest
from datetime import datetime, timezone, timedelta
from app.analytics.config import AnalyticsConfig
from app.analytics.normalization import clamp, normalize_min_max, log_scale_score
from app.analytics.deltas import (
    SnapshotData,
    calculate_delta,
    calculate_product_deltas,
)
from app.analytics.scoring import (
    calculate_freshness_score,
    calculate_rating_score,
    calculate_trend_score,
)
from app.analytics.rising_products import AnalyzedProduct, rank_rising_products
from app.analytics.new_products import filter_and_rank_new_products
from app.analytics.best_sellers import rank_best_sellers


def test_normalization_and_clamp():
    assert clamp(150, 0, 100) == 100
    assert clamp(-50, 0, 100) == 0
    assert clamp(50, 0, 100) == 50

    # Min-Max
    assert normalize_min_max(50, 0, 100) == 50.0
    assert normalize_min_max(10, 10, 10) == 50.0  # Zero division guard
    assert normalize_min_max(None, 0, 100) == 0.0

    # Log scale
    assert log_scale_score(0) == 0.0
    assert log_scale_score(None) == 0.0
    assert log_scale_score(500, midpoint=500) > 60.0


def test_delta_windows_calculation():
    now = datetime(2026, 9, 2, 12, 0, 0, tzinfo=timezone.utc)
    
    snapshots = [
        SnapshotData(captured_at=now - timedelta(days=7), sold_count=1000, review_count=50),
        SnapshotData(captured_at=now - timedelta(hours=24), sold_count=1500, review_count=80),
        SnapshotData(captured_at=now - timedelta(hours=12), sold_count=1800, review_count=90),
        SnapshotData(captured_at=now - timedelta(hours=6), sold_count=2100, review_count=100),
        SnapshotData(captured_at=now, sold_count=2600, review_count=120, rating=4.9),
    ]

    deltas = calculate_product_deltas(snapshots, current_time=now)

    assert deltas.latest_sold_count == 2600
    assert deltas.sold_delta_6h == 500   # 2600 - 2100
    assert deltas.sold_delta_12h == 800  # 2600 - 1800
    assert deltas.sold_delta_24h == 1100 # 2600 - 1500
    assert deltas.sold_delta_7d == 1600  # 2600 - 1000
    assert deltas.review_delta_24h == 40 # 120 - 80
    assert deltas.sales_velocity_24h == 1100.0
    # Acceleration: current 6h (500) vs previous 6h (2100 - 1800 = 300) -> 500 - 300 = +200
    assert deltas.sales_acceleration == 200.0
    assert not deltas.is_anomaly


def test_missing_snapshots_and_single_snapshot():
    now = datetime(2026, 9, 2, 12, 0, 0, tzinfo=timezone.utc)
    
    # Empty list
    empty_deltas = calculate_product_deltas([])
    assert empty_deltas.latest_sold_count is None
    assert empty_deltas.sold_delta_24h is None

    # Single snapshot
    single_snap = [SnapshotData(captured_at=now, sold_count=50, rating=4.5)]
    single_deltas = calculate_product_deltas(single_snap, current_time=now)
    assert single_deltas.latest_sold_count == 50
    assert single_deltas.sold_delta_24h is None
    assert single_deltas.sales_velocity_24h is None


def test_negative_anomaly_handling():
    now = datetime(2026, 9, 2, 12, 0, 0, tzinfo=timezone.utc)
    
    # Sold count drops due to external platform recount / data bug
    snapshots = [
        SnapshotData(captured_at=now - timedelta(hours=24), sold_count=1000),
        SnapshotData(captured_at=now, sold_count=850),
    ]

    deltas = calculate_product_deltas(snapshots, current_time=now)
    assert deltas.is_anomaly is True
    # Delta should be non-negative (clamped to 0 instead of returning -150)
    assert deltas.sold_delta_24h == 0


def test_freshness_and_rating_scores():
    now = datetime(2026, 9, 2, 12, 0, 0, tzinfo=timezone.utc)
    
    # Just detected (0 hours ago) -> 100 score
    assert calculate_freshness_score(now, current_time=now) == 100.0
    # 7 days old -> ~50 score
    assert 45.0 <= calculate_freshness_score(now - timedelta(days=7), current_time=now) <= 55.0
    # 15 days old (> 14 days max) -> 0 score
    assert calculate_freshness_score(now - timedelta(days=15), current_time=now) == 0.0

    # Rating score
    assert calculate_rating_score(5.0) == 100.0
    assert calculate_rating_score(3.5) == 0.0
    assert calculate_rating_score(None) == 50.0


def test_trend_score_core_principle():
    """
    Verifies Section 20 Principle:
    Product A: 100,000 lifetime sold, +50 today (flat)
    Product B: 5,000 lifetime sold, +1,500 today (rising)
    Product B MUST rank higher in Trend Score than Product A.
    """
    now = datetime(2026, 9, 2, 12, 0, 0, tzinfo=timezone.utc)
    
    # Product A: High lifetime, low velocity
    prod_a_snaps = [
        SnapshotData(captured_at=now - timedelta(hours=24), sold_count=100000, review_count=5000, rating=4.7),
        SnapshotData(captured_at=now, sold_count=100050, review_count=5002, rating=4.7),
    ]
    deltas_a = calculate_product_deltas(prod_a_snaps, current_time=now)
    score_a = calculate_trend_score(deltas_a, first_seen_at=now - timedelta(days=60), current_time=now)

    # Product B: Moderate lifetime, very high velocity & new
    prod_b_snaps = [
        SnapshotData(captured_at=now - timedelta(hours=24), sold_count=3500, review_count=200, rating=4.9),
        SnapshotData(captured_at=now, sold_count=5000, review_count=290, rating=4.9),
    ]
    deltas_b = calculate_product_deltas(prod_b_snaps, current_time=now)
    score_b = calculate_trend_score(deltas_b, first_seen_at=now - timedelta(days=2), current_time=now)

    assert score_b > score_a
    assert score_b >= 70.0
    assert score_a < 50.0


def test_trend_score_requires_observed_momentum_not_only_cumulative_metrics():
    now = datetime.now(timezone.utc)
    one_observation = calculate_product_deltas([
        SnapshotData(captured_at=now, sold_count=12808, review_count=730, rating=4.6),
    ], current_time=now)
    assert one_observation.latest_sold_count == 12808
    assert calculate_trend_score(one_observation, first_seen_at=now, current_time=now) == 0


def test_ranking_views():
    now = datetime(2026, 9, 2, 12, 0, 0, tzinfo=timezone.utc)

    p1 = AnalyzedProduct(
        product_id=1,
        external_product_id="p1",
        title="High Velocity Rising",
        first_seen_at=now - timedelta(hours=5),
        last_seen_at=now,
        deltas=calculate_product_deltas([
            SnapshotData(captured_at=now - timedelta(hours=5), sold_count=100),
            SnapshotData(captured_at=now, sold_count=600),
        ], current_time=now),
        trend_score=88.5,
    )

    p2 = AnalyzedProduct(
        product_id=2,
        external_product_id="p2",
        title="Old Giant Best Seller",
        first_seen_at=now - timedelta(days=90),
        last_seen_at=now,
        deltas=calculate_product_deltas([
            SnapshotData(captured_at=now - timedelta(hours=24), sold_count=80000),
            SnapshotData(captured_at=now, sold_count=80020),
        ], current_time=now),
        trend_score=35.0,
    )

    # Rising ranking
    rising = rank_rising_products([p2, p1])
    assert rising[0].product_id == 1  # p1 ranks #1 in Rising

    # Best Sellers ranking
    best_sellers = rank_best_sellers([p1, p2], rank_by="total_sold")
    assert best_sellers[0].product_id == 2  # p2 ranks #1 in Best Sellers (Lifetime total)

    # New products filter (last 24h)
    new_prods = filter_and_rank_new_products([p1, p2], time_window_hours=24, current_time=now)
    assert len(new_prods) == 1
    assert new_prods[0].product_id == 1
