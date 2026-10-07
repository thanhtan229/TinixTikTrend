import pytest
import time
from datetime import datetime, timezone, timedelta
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.models import Product, ProductSnapshot, WatchlistItem, AlertRule, AlertEvent
from app.services.watchlist_service import WatchlistService
from app.services.trend_service import TrendService
from app.services.alert_service import AlertService


def test_zero_n_plus_one_queries_watchlist_and_alerts():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    now = datetime(2026, 10, 5, 12, 0, 0, tzinfo=timezone.utc)

    # Insert 10 products with snapshots, watchlist items, and alert events
    for i in range(10):
        p = Product(
            external_product_id=f"p_{i}",
            title=f"Product {i}",
            first_seen_at=now - timedelta(days=2),
            last_seen_at=now,
        )
        db.add(p)
        db.flush()
        db.add(WatchlistItem(product_id=p.id))

        for h in range(5):
            db.add(ProductSnapshot(
                product_id=p.id,
                captured_at=now - timedelta(hours=h * 4),
                sold_count=100 + i * 10 + h * 5,
                price=50000.0,
            ))

        rule = AlertRule(product_id=p.id, rule_type="sales_velocity_above", threshold=10.0)
        db.add(rule)
        db.flush()

        db.add(AlertEvent(
            rule_id=rule.id,
            product_id=p.id,
            triggering_snapshot_id=1,
            rule_type="sales_velocity_above",
            threshold=10.0,
            actual_value=25.0,
            message=f"Alert {i}",
            is_read=False,
            created_at=now,
        ))

    db.commit()

    # Query counter
    query_count = 0

    def query_listener(conn, cursor, statement, parameters, context, executemany):
        nonlocal query_count
        query_count += 1

    event.listen(engine, "after_cursor_execute", query_listener)

    # 1. Watchlist query with joinedload must not do N+1 queries
    query_count = 0
    wl_service = WatchlistService(db)
    items, total = wl_service.get_watched_products()
    assert total == 10
    assert len(items) == 10
    # Single or at most 2 queries (main + joinedload/quarantine subquery), NOT 10+
    assert query_count <= 2

    # 2. Alert events query with joinedload must not do N+1 queries
    query_count = 0
    alert_service = AlertService(db)
    events, total_ev = alert_service.get_events(limit=50)
    assert total_ev == 10
    assert len(events) == 10
    # Must be at most 2 queries (count + joinedload), NOT 10+
    assert query_count <= 2

    event.remove(engine, "after_cursor_execute", query_listener)
    db.close()
    engine.dispose()


def test_p4_ac_30_representative_200_products_5000_snapshots_benchmark(tmp_path):
    """
    P4-AC-30: Existing Phase 2/3 normal read paths show no material regression
    under the existing representative fixture (200 products, 5,000 snapshots,
    representative Watchlist population, deterministic isolated/file-backed database).
    Records:
    - Trends latency and query count
    - Watchlist latency and query count
    """
    db_file = tmp_path / "bench_repr.db"
    engine = create_engine(f"sqlite:///{db_file}")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    now = datetime(2026, 10, 5, 12, 0, 0, tzinfo=timezone.utc)

    # Seed 200 products, each with 25 snapshots (total 5,000 snapshots)
    products = []
    for i in range(200):
        p = Product(
            external_product_id=f"bench_p_{i}",
            title=f"Benchmark Product {i}",
            first_seen_at=now - timedelta(days=5),
            last_seen_at=now,
            category="Fashion" if i % 2 == 0 else "Beauty",
        )
        products.append(p)
    db.add_all(products)
    db.flush()

    # Watch half of them (100 products)
    watchlist_items = [WatchlistItem(product_id=p.id) for p in products[:100]]
    db.add_all(watchlist_items)

    snapshots = []
    for p in products:
        for s_idx in range(25):
            snapshots.append(ProductSnapshot(
                product_id=p.id,
                captured_at=now - timedelta(hours=(24 - s_idx) * 4),
                sold_count=100 + s_idx * 10,
                review_count=10 + s_idx,
                rating=4.5,
                price=100000.0,
            ))
    db.add_all(snapshots)
    db.commit()

    # Warm-up call
    trend_service = TrendService(db)
    trend_service.get_trending_products(limit=50, current_time=now)

    query_count = 0

    def query_listener(conn, cursor, statement, parameters, context, executemany):
        nonlocal query_count
        query_count += 1

    event.listen(engine, "after_cursor_execute", query_listener)

    # Measure Trends query count and latency
    query_count = 0
    t0 = time.perf_counter()
    trending = trend_service.get_trending_products(limit=50, current_time=now)
    trends_latency_ms = (time.perf_counter() - t0) * 1000.0
    trends_queries = query_count

    # Benchmark TrendService (best of 5)
    timings_trend = [trends_latency_ms]
    for _ in range(4):
        t0 = time.perf_counter()
        trend_service.get_trending_products(limit=50, current_time=now)
        timings_trend.append((time.perf_counter() - t0) * 1000.0)
    best_trend_ms = min(timings_trend)

    assert len(trending) > 0
    assert best_trend_ms < 200.0, f"TrendService took {best_trend_ms:.2f}ms, exceeding 200ms gate"
    assert trends_queries <= 2, f"TrendService executed {trends_queries} queries (expected <= 2)"

    # Measure Watchlist query count and latency
    wl_service = WatchlistService(db)
    query_count = 0
    t0 = time.perf_counter()
    watched_items, total_watched = wl_service.get_watched_products(limit=50, current_time=now)
    wl_latency_ms = (time.perf_counter() - t0) * 1000.0
    wl_queries = query_count

    # Benchmark WatchlistService (best of 5)
    timings_wl = [wl_latency_ms]
    for _ in range(4):
        t0 = time.perf_counter()
        wl_service.get_watched_products(limit=50, current_time=now)
        timings_wl.append((time.perf_counter() - t0) * 1000.0)
    best_wl_ms = min(timings_wl)

    assert total_watched == 100
    assert len(watched_items) == 50
    assert best_wl_ms < 200.0, f"WatchlistService took {best_wl_ms:.2f}ms, exceeding 200ms gate"
    assert wl_queries <= 2, f"WatchlistService executed {wl_queries} queries (expected <= 2)"

    event.remove(engine, "after_cursor_execute", query_listener)
    db.close()
    engine.dispose()



def test_deterministic_as_of_analytics_replay_excludes_future_observations():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    now = datetime(2026, 10, 5, 12, 0, 0, tzinfo=timezone.utc)
    p = Product(external_product_id="as_of_prod", title="As Of Prod", first_seen_at=now - timedelta(days=5), last_seen_at=now)
    db.add(p)
    db.commit()

    # Three snapshots:
    # S1 at T - 24h: sold = 100
    # S2 at T - 12h: sold = 500  (Rapid growth: velocity = (400 / 12) * 24 = 800)
    # S3 at T:       sold = 500  (Zero growth: velocity drops to (400 / 24) * 24 = 400)
    s1 = ProductSnapshot(product_id=p.id, captured_at=now - timedelta(hours=24), sold_count=100)
    s2 = ProductSnapshot(product_id=p.id, captured_at=now - timedelta(hours=12), sold_count=500)
    s3 = ProductSnapshot(product_id=p.id, captured_at=now, sold_count=500)
    db.add_all([s1, s2, s3])
    db.commit()

    alert_service = AlertService(db)
    # Rule with threshold = 600.
    # At S2: velocity is 800 >= 600 -> TRIGGER!
    # At S3: velocity is 400 < 600 -> NO TRIGGER!
    rule = AlertRule(product_id=p.id, rule_type="sales_velocity_above", threshold=600.0, is_enabled=True)
    rule.last_evaluated_snapshot_id = s1.id
    rule.last_condition_met = False
    db.add(rule)
    db.commit()

    # Replay evaluation for S2 (while S3 already exists in database!)
    res_s2 = alert_service.evaluate_rule_against_snapshot(rule, p, s2)
    # Must evaluate strictly as of S2, ignoring S3
    assert res_s2.condition_met is True
    assert round(res_s2.actual_value, 1) == 800.0
    assert res_s2.should_emit is True

    # Now evaluate as of S3
    rule.last_condition_met = True
    rule.last_evaluated_snapshot_id = s2.id
    res_s3 = alert_service.evaluate_rule_against_snapshot(rule, p, s3)
    assert res_s3.condition_met is False
    assert round(res_s3.actual_value, 1) == 400.0
    assert res_s3.should_emit is False

    db.close()
    engine.dispose()


def test_p6_ac_33_collection_members_query_budget():
    """
    P6-AC-33: Collection member list displays default scenario summary via batched query.
    Query budget <= 3 SQL queries total; zero N+1.
    """
    from app.models.collection import Collection
    from app.models.collection_item import CollectionItem
    from app.models.economics_scenario import EconomicsScenario
    from app.services.collection_service import CollectionService

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    col = Collection(name="Econ Test Col")
    db.add(col)
    db.flush()

    now = datetime(2026, 10, 5, 12, 0, 0, tzinfo=timezone.utc)
    for i in range(5):
        p = Product(external_product_id=f"col_p_{i}", title=f"Col Prod {i}", first_seen_at=now, last_seen_at=now)
        db.add(p)
        db.flush()
        db.add(CollectionItem(collection_id=col.id, product_id=p.id))
        # Add default scenario for some products
        if i % 2 == 0:
            db.add(EconomicsScenario(
                product_id=p.id,
                name="Default Plan",
                commission_rate_bps=1000,
                commission_base_vnd=100_000,
                is_default=True,
            ))
    db.commit()

    query_count = 0
    def query_listener(conn, cursor, statement, parameters, context, executemany):
        nonlocal query_count
        query_count += 1

    event.listen(engine, "after_cursor_execute", query_listener)

    service = CollectionService(db)
    members = service.get_collection_members(col.id)

    assert len(members) == 5
    assert query_count <= 3, f"Expected <= 3 queries, got {query_count}"

    # Verify default economics attached
    has_econ = [m for m in members if m["default_economics"] is not None]
    assert len(has_econ) == 3

    event.remove(engine, "after_cursor_execute", query_listener)
    db.close()
    engine.dispose()


def test_p6_ac_34_compare_products_query_budget():
    """
    P6-AC-34: Compare products query budget:
    <= 3 queries without collection; <= 4 queries with collection. Zero N+1.
    """
    from app.models.collection import Collection
    from app.models.collection_item import CollectionItem
    from app.models.economics_scenario import EconomicsScenario
    from app.services.compare_service import CompareService

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    col = Collection(name="Compare Col")
    db.add(col)
    db.flush()
    col_id = col.id

    now = datetime(2026, 10, 5, 12, 0, 0, tzinfo=timezone.utc)
    p_ids = []
    for i in range(4):
        p = Product(external_product_id=f"cmp_p_{i}", title=f"Compare Prod {i}", first_seen_at=now, last_seen_at=now)
        db.add(p)
        db.flush()
        p_ids.append(p.id)
        db.add(CollectionItem(collection_id=col_id, product_id=p.id))
        db.add(ProductSnapshot(product_id=p.id, captured_at=now, sold_count=100, price=50000.0))
        db.add(EconomicsScenario(
            product_id=p.id,
            name="Plan 1",
            commission_rate_bps=1200,
            commission_base_vnd=50_000,
            is_default=True,
        ))
    db.commit()

    query_count = 0
    def query_listener(conn, cursor, statement, parameters, context, executemany):
        nonlocal query_count
        query_count += 1

    event.listen(engine, "after_cursor_execute", query_listener)

    service = CompareService(db)

    # 1. Compare without collection: <= 3 queries
    query_count = 0
    res_no_col = service.compare_products(product_ids=p_ids, collection_id=None)
    assert len(res_no_col.products) == 4
    assert query_count <= 3, f"Expected <= 3 queries without collection, got {query_count}"
    assert all(p.default_economics is not None for p in res_no_col.products)

    # 2. Compare with collection: <= 4 queries
    query_count = 0
    res_col = service.compare_products(product_ids=p_ids, collection_id=col_id)
    assert len(res_col.products) == 4
    assert query_count <= 4, f"Expected <= 4 queries with collection, got {query_count}"

    event.remove(engine, "after_cursor_execute", query_listener)
    db.close()
    engine.dispose()


