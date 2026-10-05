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
from app.analytics.scoring import has_trend_evidence
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.base import Base
from app.models.product import Product
from app.models.product_snapshot import ProductSnapshot
from app.models.quarantine import QuarantinedProduct
from app.services.product_service import ProductService
from app.services.trend_service import TrendService



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


def test_seven_day_analytics_exact_near_and_bounded_tolerance():
    now = datetime(2026, 9, 2, 12, 0, 0, tzinfo=timezone.utc)

    # 1. Exact 7-day observation (168 hours)
    exact_snaps = [
        SnapshotData(captured_at=now - timedelta(days=7), sold_count=1000, review_count=50),
        SnapshotData(captured_at=now, sold_count=1600, review_count=80),
    ]
    deltas_exact = calculate_product_deltas(exact_snaps, current_time=now)
    assert deltas_exact.sold_delta_7d == 600
    assert deltas_exact.review_delta_7d == 30

    # 2. Near 7-day observation within 4-hour tolerance (e.g., 170 hours ago, diff = 2h <= 4h)
    near_snaps_older = [
        SnapshotData(captured_at=now - timedelta(hours=170), sold_count=1050, review_count=55),
        SnapshotData(captured_at=now, sold_count=1600, review_count=80),
    ]
    deltas_near_older = calculate_product_deltas(near_snaps_older, current_time=now)
    assert deltas_near_older.sold_delta_7d == 550
    assert deltas_near_older.review_delta_7d == 25

    # 3. Near 7-day observation within 4-hour tolerance on recent side (e.g., 165 hours ago, diff = 3h <= 4h)
    near_snaps_recent = [
        SnapshotData(captured_at=now - timedelta(hours=165), sold_count=1100, review_count=60),
        SnapshotData(captured_at=now, sold_count=1600, review_count=80),
    ]
    deltas_near_recent = calculate_product_deltas(near_snaps_recent, current_time=now)
    assert deltas_near_recent.sold_delta_7d == 500
    assert deltas_near_recent.review_delta_7d == 20

    # 4. Outside bounded tolerance: 173 hours ago (5h diff > 4h tolerance) -> returns None
    too_old_snaps = [
        SnapshotData(captured_at=now - timedelta(hours=173), sold_count=1000, review_count=50),
        SnapshotData(captured_at=now, sold_count=1600, review_count=80),
    ]
    assert calculate_product_deltas(too_old_snaps, current_time=now).sold_delta_7d is None

    # 5. Outside bounded tolerance: 163 hours ago (5h diff > 4h tolerance) -> returns None
    too_recent_snaps = [
        SnapshotData(captured_at=now - timedelta(hours=163), sold_count=1000, review_count=50),
        SnapshotData(captured_at=now, sold_count=1600, review_count=80),
    ]
    assert calculate_product_deltas(too_recent_snaps, current_time=now).sold_delta_7d is None

    # 6. Bounded tolerance selection among candidates: selects closest to 168h
    # Candidate A: 171h ago (3h diff) with sold_count=1000
    # Candidate B: 167h ago (1h diff) with sold_count=1100 -> closest!
    multiple_candidates = [
        SnapshotData(captured_at=now - timedelta(hours=171), sold_count=1000),
        SnapshotData(captured_at=now - timedelta(hours=167), sold_count=1100),
        SnapshotData(captured_at=now, sold_count=1600),
    ]
    deltas_closest = calculate_product_deltas(multiple_candidates, current_time=now)
    assert deltas_closest.sold_delta_7d == 500  # 1600 - 1100 (candidate B was picked, not candidate A)


def test_seven_day_analytics_invariants_nullability_and_zeros():
    now = datetime(2026, 9, 2, 12, 0, 0, tzinfo=timezone.utc)

    # 1. Insufficient history (< 164 hours) returns null/None, never invents a value
    for days in [1, 2, 3, 5, 6]:
        snaps = [
            SnapshotData(captured_at=now - timedelta(days=days), sold_count=1000, review_count=50),
            SnapshotData(captured_at=now, sold_count=1600, review_count=80),
        ]
        d = calculate_product_deltas(snaps, current_time=now)
        assert d.sold_delta_7d is None, f"Expected None for {days} days of history, got {d.sold_delta_7d}"
        assert d.review_delta_7d is None

    # 2. Missing metrics remain nullable (never fabricated as 0)
    missing_past_metric = [
        SnapshotData(captured_at=now - timedelta(days=7), sold_count=None, review_count=None),
        SnapshotData(captured_at=now, sold_count=1600, review_count=80, commission_rate=None),
    ]
    d_missing = calculate_product_deltas(missing_past_metric, current_time=now)
    assert d_missing.sold_delta_7d is None
    assert d_missing.review_delta_7d is None
    assert d_missing.latest_commission_rate is None

    missing_latest_metric = [
        SnapshotData(captured_at=now - timedelta(days=7), sold_count=1000, review_count=50),
        SnapshotData(captured_at=now, sold_count=None, review_count=None),
    ]
    d_missing_latest = calculate_product_deltas(missing_latest_metric, current_time=now)
    assert d_missing_latest.sold_delta_7d is None
    assert d_missing_latest.review_delta_7d is None
    assert d_missing_latest.latest_sold_count is None

    # 3. Zero values remain valid integer zeros (not coerced to None or dropped)
    zero_growth_snaps = [
        SnapshotData(captured_at=now - timedelta(days=7), sold_count=1000, review_count=50, price=0.0),
        SnapshotData(captured_at=now, sold_count=1000, review_count=50, price=0.0),
    ]
    d_zero = calculate_product_deltas(zero_growth_snaps, current_time=now)
    assert d_zero.sold_delta_7d == 0
    assert d_zero.review_delta_7d == 0
    assert d_zero.latest_price == 0.0
    assert d_zero.sold_delta_7d is not None
    assert d_zero.review_delta_7d is not None

    # 4. Real elapsed time semantics preserved
    assert d_zero.last_observed_at == now
    # 24h velocity with exact 24h baseline is unestimated
    exact_24h = [
        SnapshotData(captured_at=now - timedelta(hours=24), sold_count=900),
        SnapshotData(captured_at=now, sold_count=1000),
    ]
    d_24h = calculate_product_deltas(exact_24h, current_time=now)
    assert d_24h.sales_velocity_24h == 100.0
    assert d_24h.velocity_is_estimated is False

    # 18h baseline scales proportionally and flags velocity_is_estimated = True
    partial_18h = [
        SnapshotData(captured_at=now - timedelta(hours=18), sold_count=925),
        SnapshotData(captured_at=now, sold_count=1000),
    ]
    d_18h = calculate_product_deltas(partial_18h, current_time=now)
    assert d_18h.sales_velocity_24h == 100.0  # 75 * 24 / 18 = 100.0
    assert d_18h.velocity_is_estimated is True


def test_stale_observations_cannot_create_current_trend_evidence():
    now = datetime(2026, 9, 2, 12, 0, 0, tzinfo=timezone.utc)

    # Last observation was 9 hours ago (> 8h staleness threshold)
    stale_snaps = [
        SnapshotData(captured_at=now - timedelta(days=7), sold_count=1000),
        SnapshotData(captured_at=now - timedelta(hours=24), sold_count=1500),
        SnapshotData(captured_at=now - timedelta(hours=9), sold_count=2000),
    ]
    deltas = calculate_product_deltas(stale_snaps, current_time=now)
    assert deltas.is_stale is True
    assert deltas.sold_delta_7d is None
    assert deltas.sold_delta_24h is None
    assert deltas.sales_velocity_24h is None
    assert deltas.sales_acceleration is None
    assert calculate_trend_score(deltas, first_seen_at=now - timedelta(days=30), current_time=now) == 0.0


def test_acceleration_uses_distinct_intervals_and_null_when_insufficient():
    now = datetime(2026, 9, 2, 12, 0, 0, tzinfo=timezone.utc)

    # Case A: Only 6h anchor exists (no 12h and no 24h) -> acceleration must be None
    only_6h = [
        SnapshotData(captured_at=now - timedelta(hours=6), sold_count=100),
        SnapshotData(captured_at=now, sold_count=200),
    ]
    assert calculate_product_deltas(only_6h, current_time=now).sales_acceleration is None

    # Case B: Only 7d anchor exists -> acceleration must be None
    only_7d = [
        SnapshotData(captured_at=now - timedelta(days=7), sold_count=100),
        SnapshotData(captured_at=now, sold_count=200),
    ]
    assert calculate_product_deltas(only_7d, current_time=now).sales_acceleration is None

    # Case C: 6h and 12h resolve to distinct intervals:
    # 12h: sold=100, 6h: sold=150 (growth=50), now: sold=250 (growth=100) -> accel = 100 - 50 = +50
    valid_accel = [
        SnapshotData(captured_at=now - timedelta(hours=12), sold_count=100),
        SnapshotData(captured_at=now - timedelta(hours=6), sold_count=150),
        SnapshotData(captured_at=now, sold_count=250),
    ]
    deltas = calculate_product_deltas(valid_accel, current_time=now)
    assert deltas.sales_acceleration == 50.0

    # Case D: Missing sold count in one interval -> acceleration must be None
    missing_sold_accel = [
        SnapshotData(captured_at=now - timedelta(hours=12), sold_count=None),
        SnapshotData(captured_at=now - timedelta(hours=6), sold_count=150),
        SnapshotData(captured_at=now, sold_count=250),
    ]
    assert calculate_product_deltas(missing_sold_accel, current_time=now).sales_acceleration is None


def test_quarantine_data_excluded_from_all_analytics():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()
    try:
        now = datetime.now(timezone.utc)
        # Add normal active product
        active_prod = Product(
            platform="tiktok_shop",
            external_product_id="active_123",
            title="Active Product",
            category="Fashion",
            first_seen_at=now - timedelta(days=2),
            last_seen_at=now,
        )
        # Add quarantined product
        quarantined_prod = Product(
            platform="tiktok_shop",
            external_product_id="quarantine_456",
            title="Quarantined Product",
            category="Fashion",
            first_seen_at=now - timedelta(days=2),
            last_seen_at=now,
        )
        db.add_all([active_prod, quarantined_prod])
        db.commit()
        db.refresh(active_prod)
        db.refresh(quarantined_prod)

        # Mark second product as quarantined
        q_record = QuarantinedProduct(
            product_id=quarantined_prod.id,
            reason="Contaminated legacy data",
            quarantined_at=now,
        )
        db.add(q_record)

        # Add snapshots for both
        db.add_all([
            ProductSnapshot(product_id=active_prod.id, captured_at=now - timedelta(hours=24), sold_count=100),
            ProductSnapshot(product_id=active_prod.id, captured_at=now, sold_count=200),
            ProductSnapshot(product_id=quarantined_prod.id, captured_at=now - timedelta(hours=24), sold_count=100),
            ProductSnapshot(product_id=quarantined_prod.id, captured_at=now, sold_count=5000),
        ])
        db.commit()

        prod_service = ProductService(db)
        trend_service = TrendService(db)

        # 1. ProductService.get_all_analyzed_products excludes quarantined product
        analyzed = prod_service.get_all_analyzed_products()
        assert len(analyzed) == 1
        assert analyzed[0].external_product_id == "active_123"

        # 2. ProductService.get_product_by_id excludes quarantined product
        assert prod_service.get_product_by_id(quarantined_prod.id) is None
        assert prod_service.get_product_by_id(active_prod.id) is not None

        # 3. ProductService.list_products excludes quarantined product
        listed, total = prod_service.list_products()
        assert total == 1
        assert listed[0].id == active_prod.id

        # 4. TrendService methods exclude quarantined product
        trending = trend_service.get_trending_products()
        assert all(p.external_product_id != "quarantine_456" for p in trending)

        rising = trend_service.get_rising_products()
        assert all(p.external_product_id != "quarantine_456" for p in rising)

        best_sellers = trend_service.get_best_sellers()
        assert all(p.external_product_id != "quarantine_456" for p in best_sellers)

        summary = trend_service.get_dashboard_summary()
        assert summary["stats"]["total_products"] == 1
        assert all(p.external_product_id != "quarantine_456" for p in summary["trending"])
        assert all(p.external_product_id != "quarantine_456" for p in summary["rising"])
        assert all(p.external_product_id != "quarantine_456" for p in summary["best_sellers"])
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()

