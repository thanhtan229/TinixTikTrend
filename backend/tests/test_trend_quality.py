import pytest
from datetime import datetime, timezone, timedelta
from app.analytics.deltas import SnapshotData, calculate_product_deltas
from app.analytics.scoring import calculate_trend_score
from app.analytics.evidence import calculate_trend_evidence, calculate_trend_reasons, TrendEvidence
from app.analytics.rising_products import AnalyzedProduct
from app.services.trend_service import TrendService
from app.services.product_service import ProductService
from app.models import Product, ProductSnapshot, QuarantinedProduct
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.base import Base
from fastapi.testclient import TestClient
from app.main import app


def test_evidence_confidence_tiers():
    now = datetime(2026, 10, 5, 12, 0, 0, tzinfo=timezone.utc)

    # 1. LOW: Only 1 snapshot (insufficient measured signal)
    snaps_1 = [SnapshotData(captured_at=now, sold_count=500, rating=4.8)]
    deltas_1 = calculate_product_deltas(snaps_1, current_time=now)
    ev_1 = calculate_trend_evidence(snaps_1, deltas_1, current_time=now)
    assert ev_1.ranking_state == "insufficient_measured_signal"
    assert ev_1.confidence == "low"
    assert ev_1.observation_count == 1
    assert ev_1.observation_span_hours == 0.0

    # 2. LOW: Stale product (last snapshot 9h ago)
    snaps_stale = [
        SnapshotData(captured_at=now - timedelta(hours=33), sold_count=100),
        SnapshotData(captured_at=now - timedelta(hours=9), sold_count=200),
    ]
    deltas_stale = calculate_product_deltas(snaps_stale, current_time=now)
    ev_stale = calculate_trend_evidence(snaps_stale, deltas_stale, current_time=now)
    assert ev_stale.ranking_state == "stale"
    assert ev_stale.confidence == "low"

    # 3. LOW: Eligible but only 2 snapshots with 4h span (short/sparse, estimated velocity)
    snaps_sparse = [
        SnapshotData(captured_at=now - timedelta(hours=4), sold_count=100),
        SnapshotData(captured_at=now, sold_count=150),
    ]
    deltas_sparse = calculate_product_deltas(snaps_sparse, current_time=now)
    ev_sparse = calculate_trend_evidence(snaps_sparse, deltas_sparse, current_time=now)
    assert ev_sparse.ranking_state == "eligible"
    assert ev_sparse.confidence == "low"
    assert ev_sparse.primary_signal_interval.is_estimated is True
    assert ev_sparse.signals["sales_velocity"] == "estimated"

    # 4. MEDIUM: 3 snapshots, 10h span, measured interval (6h anchor)
    snaps_med = [
        SnapshotData(captured_at=now - timedelta(hours=10), sold_count=100),
        SnapshotData(captured_at=now - timedelta(hours=6), sold_count=150),
        SnapshotData(captured_at=now, sold_count=250),
    ]
    deltas_med = calculate_product_deltas(snaps_med, current_time=now)
    ev_med = calculate_trend_evidence(snaps_med, deltas_med, current_time=now)
    assert ev_med.ranking_state == "eligible"
    assert ev_med.confidence == "medium"
    assert ev_med.observation_count == 3
    assert ev_med.observation_span_hours == 10.0
    assert ev_med.signals["sales_velocity"] == "estimated"

    # 5. HIGH: 5 snapshots, 24h span, measured 24h window, not estimated
    snaps_high = [
        SnapshotData(captured_at=now - timedelta(hours=24), sold_count=100, review_count=10),
        SnapshotData(captured_at=now - timedelta(hours=18), sold_count=140, review_count=12),
        SnapshotData(captured_at=now - timedelta(hours=12), sold_count=180, review_count=15),
        SnapshotData(captured_at=now - timedelta(hours=6), sold_count=220, review_count=18),
        SnapshotData(captured_at=now, sold_count=300, review_count=25),
    ]
    deltas_high = calculate_product_deltas(snaps_high, current_time=now)
    ev_high = calculate_trend_evidence(snaps_high, deltas_high, current_time=now)
    assert ev_high.ranking_state == "eligible"
    assert ev_high.confidence == "high"
    assert ev_high.observation_count == 5
    assert ev_high.observation_span_hours == 24.0
    assert ev_high.has_24h_window is True
    assert ev_high.primary_signal_interval.is_estimated is False


def test_estimated_intervals_cannot_escalate_confidence_to_high():
    now = datetime(2026, 10, 5, 12, 0, 0, tzinfo=timezone.utc)
    # 5 snapshots spanning 22 hours, but no 24h anchor (so velocity is estimated from recent baseline)
    snaps = [
        SnapshotData(captured_at=now - timedelta(hours=22), sold_count=100),
        SnapshotData(captured_at=now - timedelta(hours=16), sold_count=130),
        SnapshotData(captured_at=now - timedelta(hours=10), sold_count=170),
        SnapshotData(captured_at=now - timedelta(hours=4), sold_count=210),
        SnapshotData(captured_at=now, sold_count=260),
    ]
    deltas = calculate_product_deltas(snaps, current_time=now)
    # 22h is outside 24h tolerance (1h), so no 24h anchor
    assert not deltas.has_24h_window
    ev = calculate_trend_evidence(snaps, deltas, current_time=now)
    # Cannot be HIGH because has_24h_window is False and velocity is estimated
    assert ev.confidence != "high"


def test_trend_reasons_deterministic_selection():
    now = datetime(2026, 10, 5, 12, 0, 0, tzinfo=timezone.utc)
    snaps = [
        SnapshotData(captured_at=now - timedelta(hours=24), sold_count=100, review_count=10),
        SnapshotData(captured_at=now - timedelta(hours=12), sold_count=150, review_count=15),
        SnapshotData(captured_at=now - timedelta(hours=6), sold_count=200, review_count=20),
        SnapshotData(captured_at=now, sold_count=350, review_count=35),
    ]
    deltas = calculate_product_deltas(snaps, current_time=now)
    score = calculate_trend_score(deltas, first_seen_at=now - timedelta(days=2), current_time=now)
    assert score > 0

    reasons = calculate_trend_reasons(deltas, score)
    assert len(reasons) >= 1
    codes = [r.reason_code for r in reasons]
    # Positive sales velocity, review delta and acceleration should be captured
    assert "sales_velocity_up" in codes
    assert "review_velocity_up" in codes
    if deltas.sales_acceleration and deltas.sales_acceleration > 0:
        assert "sales_acceleration_up" in codes

    # Reasons must be ordered by contribution descending
    for i in range(len(reasons) - 1):
        assert reasons[i].contribution >= reasons[i + 1].contribution

    # Neither freshness nor rating should be included as reasons
    for r in reasons:
        assert r.reason_code not in ("freshness_up", "rating_up")


def test_trend_reasons_empty_for_ineligible_or_zero():
    now = datetime(2026, 10, 5, 12, 0, 0, tzinfo=timezone.utc)
    # Product with zero score / no momentum
    snaps = [SnapshotData(captured_at=now, sold_count=50000)]
    deltas = calculate_product_deltas(snaps, current_time=now)
    score = calculate_trend_score(deltas, first_seen_at=now, current_time=now)
    assert score == 0.0

    reasons = calculate_trend_reasons(deltas, score)
    assert reasons == []


@pytest.fixture
def memory_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


def test_trend_service_filters_and_sorts(memory_db):
    now = datetime(2026, 10, 5, 12, 0, 0, tzinfo=timezone.utc)

    # Product 1: High confidence, high trend score
    p1 = Product(external_product_id="prod_1", title="Trending Shoes", category="Fashion",
                 first_seen_at=now - timedelta(days=3), last_seen_at=now)
    # Product 2: Medium confidence, moderate trend score
    p2 = Product(external_product_id="prod_2", title="Trending Cream", category="Beauty",
                 first_seen_at=now - timedelta(days=2), last_seen_at=now)
    # Product 3: Stale product (>8h old)
    p3 = Product(external_product_id="prod_3", title="Old Trend", category="Fashion",
                 first_seen_at=now - timedelta(days=10), last_seen_at=now - timedelta(hours=10))
    # Product 4: Insufficient measured signal (only 1 snapshot)
    p4 = Product(external_product_id="prod_4", title="New Unmeasured", category="Tech",
                 first_seen_at=now, last_seen_at=now)

    memory_db.add_all([p1, p2, p3, p4])
    memory_db.commit()

    # Snapshots for p1 (5 snapshots over 24h -> High confidence)
    for h, sold, rev in [(24, 100, 10), (18, 160, 14), (12, 230, 20), (6, 320, 25), (0, 450, 35)]:
        memory_db.add(ProductSnapshot(product_id=p1.id, captured_at=now - timedelta(hours=h), sold_count=sold, review_count=rev))

    # Snapshots for p2 (3 snapshots over 10h -> Medium confidence)
    for h, sold, rev in [(10, 100, 5), (6, 130, 7), (0, 180, 10)]:
        memory_db.add(ProductSnapshot(product_id=p2.id, captured_at=now - timedelta(hours=h), sold_count=sold, review_count=rev))

    # Snapshots for p3 (stale)
    memory_db.add(ProductSnapshot(product_id=p3.id, captured_at=now - timedelta(hours=34), sold_count=100))
    memory_db.add(ProductSnapshot(product_id=p3.id, captured_at=now - timedelta(hours=10), sold_count=200))

    # Snapshots for p4 (single snapshot)
    memory_db.add(ProductSnapshot(product_id=p4.id, captured_at=now, sold_count=10000))

    memory_db.commit()

    trend_service = TrendService(memory_db)

    # Filter by trend_state: "eligible" (default) should return p1 and p2 only
    eligible = trend_service.get_trending_products(trend_state="eligible", current_time=now)
    assert len(eligible) == 2
    assert {p.external_product_id for p in eligible} == {"prod_1", "prod_2"}

    # Filter by trend_state: "stale" should return p3
    stale = trend_service.get_trending_products(trend_state="stale", current_time=now)
    assert len(stale) == 1
    assert stale[0].external_product_id == "prod_3"

    # Filter by trend_state: "insufficient_signal" should return p4
    insufficient = trend_service.get_trending_products(trend_state="insufficient_signal", current_time=now)
    assert len(insufficient) == 1
    assert insufficient[0].external_product_id == "prod_4"

    # Filter by trend_state: "all" should return all 4
    all_prods = trend_service.get_trending_products(trend_state="all", current_time=now)
    assert len(all_prods) == 4

    # Filter by confidence: "high"
    high_conf = trend_service.get_trending_products(trend_state="eligible", confidence="high", current_time=now)
    assert len(high_conf) == 1
    assert high_conf[0].external_product_id == "prod_1"

    # Filter by confidence: "medium_or_high"
    med_high = trend_service.get_trending_products(trend_state="eligible", confidence="medium_or_high", current_time=now)
    assert len(med_high) == 2

    # Filter by evidence: "measured_only"
    measured = trend_service.get_trending_products(trend_state="eligible", evidence="measured_only", current_time=now)
    assert len(measured) == 1
    assert measured[0].external_product_id == "prod_1"

    # Category filter: "Fashion"
    fashion = trend_service.get_trending_products(category="Fashion", trend_state="all", current_time=now)
    assert len(fashion) == 2
    assert {p.external_product_id for p in fashion} == {"prod_1", "prod_3"}

    # Sort by sales_velocity desc
    by_velocity = trend_service.get_trending_products(trend_state="all", sort_by="sales_velocity", order="desc", current_time=now)
    assert by_velocity[0].external_product_id == "prod_1"  # highest velocity
    # Nulls last: p4 has no sales_velocity_24h, must be last
    assert by_velocity[-1].external_product_id == "prod_4"


def test_api_trends_query_params_and_contract(client):
    # Test GET /api/trends with new Phase 2 query parameters
    response = client.get("/api/trends?trend_state=eligible&sort_by=trend_score&order=desc")
    assert response.status_code == 200
    items = response.json()
    assert isinstance(items, list)
    if items:
        first = items[0]
        assert "trend_score" in first
        assert "evidence" in first
        assert "reasons" in first
        if first["evidence"]:
            assert "confidence" in first["evidence"]
            assert "ranking_state" in first["evidence"]
            assert "observation_count" in first["evidence"]
            assert "observation_span_hours" in first["evidence"]
            assert "signals" in first["evidence"]

    # Category filter test via API
    res_beauty = client.get("/api/trends?category=S%E1%BB%A9c%20kh%E1%BB%8Fe%20%26%20L%C3%A0m%20%C4%91%E1%BA%B9p&trend_state=all")
    assert res_beauty.status_code == 200
    beauty_items = res_beauty.json()
    assert len(beauty_items) >= 1
    for item in beauty_items:
        assert item["category"] == "Sức khỏe & Làm đẹp"

    # Category filter with non-matching category returns empty list
    res_empty = client.get("/api/trends?category=NonExistentCategory&trend_state=all")
    assert res_empty.status_code == 200
    assert res_empty.json() == []

    # Combined filters: category + trend_state + sort_by + order
    res_combined = client.get(
        "/api/trends?category=S%E1%BB%A9c%20kh%E1%BB%8Fe%20%26%20L%C3%A0m%20%C4%91%E1%BA%B9p&trend_state=eligible&sort_by=sales_velocity&order=desc"
    )
    assert res_combined.status_code == 200
    combined_items = res_combined.json()
    assert isinstance(combined_items, list)

