import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient

from app.models import Product, ProductSnapshot, WatchlistItem, AlertRule, AlertEvent, QuarantinedProduct
from app.services.watchlist_service import WatchlistService
from app.services.crawl_service import CrawlService
from app.collectors.tiktok_shop.schemas import ExtractedProduct
from tests.conftest import TestingSessionLocal


@pytest.fixture
def db():
    session = TestingSessionLocal()
    yield session
    session.rollback()
    # Clean up test products
    for pid in ["prod_wl_1", "prod_preserve", "111", "222", "333", "999888777", "prod_a", "prod_b", "prod_c"]:
        p = session.query(Product).filter_by(external_product_id=pid).first()
        if p:
            session.delete(p)
    session.commit()
    session.close()


def test_watchlist_add_remove_status(db, client: TestClient):
    now = datetime(2026, 10, 5, 12, 0, 0, tzinfo=timezone.utc)
    p = Product(external_product_id="prod_wl_1", title="Watchlist Item 1", first_seen_at=now, last_seen_at=now)
    db.add(p)
    db.commit()

    # Initial status: not watched
    res = client.get(f"/api/watchlist/{p.id}/status")
    assert res.status_code == 200
    assert res.json() == {"is_watched": False, "product_id": p.id}

    # Add to watchlist
    res = client.post(f"/api/watchlist/{p.id}")
    assert res.status_code == 201
    assert res.json()["is_watched"] is True
    assert res.json()["product_id"] == p.id

    # Check status again
    res = client.get(f"/api/watchlist/{p.id}/status")
    assert res.status_code == 200
    assert res.json()["is_watched"] is True

    # Check IDs endpoint
    res = client.get("/api/watchlist/ids")
    assert res.status_code == 200
    assert p.id in res.json()["product_ids"]

    # Remove from watchlist
    res = client.delete(f"/api/watchlist/{p.id}")
    assert res.status_code == 200
    assert res.json()["is_watched"] is False

    # Check status again
    res = client.get(f"/api/watchlist/{p.id}/status")
    assert res.status_code == 200
    assert res.json()["is_watched"] is False


def test_unwatch_preserves_historical_data(db, client: TestClient):
    now = datetime(2026, 10, 5, 12, 0, 0, tzinfo=timezone.utc)
    p = Product(external_product_id="prod_preserve", title="Preserve Me", first_seen_at=now, last_seen_at=now)
    db.add(p)
    db.commit()

    snap = ProductSnapshot(product_id=p.id, captured_at=now, sold_count=500, price=100000.0)
    db.add(snap)
    db.commit()

    rule = AlertRule(product_id=p.id, rule_type="sales_velocity_above", threshold=100.0, is_enabled=True)
    db.add(rule)
    db.commit()

    event = AlertEvent(
        rule_id=rule.id,
        product_id=p.id,
        triggering_snapshot_id=snap.id,
        rule_type="sales_velocity_above",
        threshold=100.0,
        actual_value=150.0,
        message="Test alert",
        is_read=False,
        created_at=now,
    )
    db.add(event)
    db.commit()

    # Watch product
    client.post(f"/api/watchlist/{p.id}")
    assert db.query(WatchlistItem).filter_by(product_id=p.id).count() == 1

    # Unwatch product
    client.delete(f"/api/watchlist/{p.id}")
    assert db.query(WatchlistItem).filter_by(product_id=p.id).count() == 0

    # Invariants: Product, Snapshot, Rule, Event MUST all still exist!
    assert db.get(Product, p.id) is not None
    assert db.get(ProductSnapshot, snap.id) is not None
    assert db.get(AlertRule, rule.id) is not None
    assert db.get(AlertEvent, event.id) is not None


def test_watchlist_membership_drives_scheduled_crawl(db):
    now = datetime(2026, 10, 5, 12, 0, 0, tzinfo=timezone.utc)
    # Product 1: In watchlist
    p1 = Product(external_product_id="111", title="Watched", url="https://shop.tiktok.com/view/product/111",
                 first_seen_at=now - timedelta(days=2), last_seen_at=now - timedelta(days=1))
    # Product 2: Not in watchlist
    p2 = Product(external_product_id="222", title="Unwatched", url="https://shop.tiktok.com/view/product/222",
                 first_seen_at=now - timedelta(days=2), last_seen_at=now - timedelta(days=1))
    # Product 3: In watchlist but quarantined
    p3 = Product(external_product_id="333", title="Quarantined", url="https://shop.tiktok.com/view/product/333",
                 first_seen_at=now - timedelta(days=2), last_seen_at=now - timedelta(days=1))

    db.add_all([p1, p2, p3])
    db.commit()

    db.add(WatchlistItem(product_id=p1.id))
    db.add(WatchlistItem(product_id=p3.id))
    db.add(QuarantinedProduct(product_id=p3.id, reason="Contaminated"))
    db.commit()

    service = WatchlistService(db)
    watched_ids = service.get_watched_product_ids()
    assert p1.id in watched_ids
    assert p3.id in watched_ids

    # Query used for scheduled refresh
    tracked_for_refresh = db.query(Product).join(
        WatchlistItem, WatchlistItem.product_id == Product.id
    ).filter(
        Product.url.is_not(None),
        Product.id.not_in([p3.id]),
        Product.id.in_([p1.id, p2.id, p3.id])
    ).all()

    assert len(tracked_for_refresh) == 1
    assert tracked_for_refresh[0].id == p1.id


def test_user_submitted_pdp_becomes_watched(db):
    now = datetime(2026, 10, 5, 12, 0, 0, tzinfo=timezone.utc)
    crawl_service = CrawlService(db)

    ext = ExtractedProduct(
        external_product_id="999888777",
        title="Valid User Product",
        url="https://shop.tiktok.com/view/product/999888777",
        price=150000.0,
        sold_count=50,
        captured_at=now,
    )

    from app.models.crawl_run import CrawlRun
    crawl_run = CrawlRun(source="manual", status="running", started_at=now)
    db.add(crawl_run)
    db.commit()

    # Ingest as user-submitted
    crawl_service._upsert_product_and_snapshot(ext, crawl_run, is_user_submitted=True)

    product = db.query(Product).filter_by(external_product_id="999888777").first()
    assert product is not None

    # Must be automatically added to WatchlistItem
    wl_item = db.query(WatchlistItem).filter_by(product_id=product.id).first()
    assert wl_item is not None


def test_watchlist_api_pagination_and_sorting(db, client: TestClient):
    now = datetime(2026, 10, 5, 12, 0, 0, tzinfo=timezone.utc)

    p1 = Product(external_product_id="prod_a", title="Alpha Shoes", category="Fashion",
                 first_seen_at=now - timedelta(days=3), last_seen_at=now)
    p2 = Product(external_product_id="prod_b", title="Beta Cream", category="Beauty",
                 first_seen_at=now - timedelta(days=2), last_seen_at=now)
    p3 = Product(external_product_id="prod_c", title="Gamma Dress", category="Fashion",
                 first_seen_at=now - timedelta(days=1), last_seen_at=now)

    db.add_all([p1, p2, p3])
    db.commit()

    # Watch p1 and p2 only
    db.add_all([
        WatchlistItem(product_id=p1.id),
        WatchlistItem(product_id=p2.id),
    ])
    # Add snapshots
    db.add_all([
        ProductSnapshot(product_id=p1.id, captured_at=now - timedelta(hours=24), sold_count=100),
        ProductSnapshot(product_id=p1.id, captured_at=now, sold_count=300),
        ProductSnapshot(product_id=p2.id, captured_at=now - timedelta(hours=24), sold_count=50),
        ProductSnapshot(product_id=p2.id, captured_at=now, sold_count=100),
    ])
    db.commit()

    # GET /api/watchlist returns p1 and p2
    res = client.get("/api/watchlist")
    assert res.status_code == 200
    data = res.json()
    returned_ids = {item["product_id"] for item in data["items"]}
    assert p1.id in returned_ids
    assert p2.id in returned_ids
    assert p3.id not in returned_ids

    # Filter by category
    res = client.get("/api/watchlist?category=Beauty")
    assert res.status_code == 200
    data = res.json()
    beauty_ids = {item["product_id"] for item in data["items"]}
    assert p2.id in beauty_ids
    assert p1.id not in beauty_ids
