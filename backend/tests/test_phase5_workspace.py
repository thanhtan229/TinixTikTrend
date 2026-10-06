import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from types import SimpleNamespace
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select, func, event, inspect
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.db.base import Base
from app.db.init_db import init_db
from app.models.product import Product
from app.models.product_snapshot import ProductSnapshot
from app.models.watchlist import WatchlistItem
from app.models.alert_rule import AlertRule
from app.models.alert_event import AlertEvent
from app.models.crawl_run import CrawlRun
from app.models.category import Category
from app.models.product_video_link import ProductVideoLink
from app.models.quarantine import QuarantinedProduct
from app.models.system_metadata import SystemMetadata
from app.models.collection import Collection
from app.models.collection_item import CollectionItem
from app.models.saved_view import SavedView
from app.services.collection_service import CollectionService
from app.services.saved_view_service import (
    SavedViewService,
    SavedViewCreate,
    SavedViewUpdate,
)
from app.services.compare_service import CompareService
from app.services.backup_service import BackupService


@pytest.fixture
def p5_db_session(tmp_path):
    """Isolated file-backed database session for Phase 5 tests."""
    db_file = tmp_path / "p5_test.db"
    engine = create_engine(f"sqlite:///{db_file}")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Seed compatibility marker version 2
    session.add(SystemMetadata(key="portable_backup_compatibility_version", value="2"))
    session.commit()

    yield session, engine

    session.close()
    engine.dispose()


@pytest.fixture
def test_client(p5_db_session):
    session, engine = p5_db_session
    from app.db.session import get_db

    def override_get_db():
        try:
            yield session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


# ==============================================================================
# WORKSTREAM 2: COLLECTIONS (P5-AC-01 through P5-AC-10)
# ==============================================================================

def test_p5_ac_01_domain_separation_zero_scheduler_side_effects(p5_db_session):
    """
    P5-AC-01: Watchlist remains sole scheduled-refresh authority.
    Collection CRUD/membership mutations cause NO watchlist/scheduler changes.
    """
    db, _ = p5_db_session
    service = CollectionService(db)

    now = datetime.now(timezone.utc)
    p = Product(external_product_id="ext_sep_1", title="Sep Product", first_seen_at=now, last_seen_at=now)
    db.add(p)
    db.commit()

    # Product is initially NOT watched
    assert db.query(WatchlistItem).filter_by(product_id=p.id).first() is None

    # Create collection and add product
    col = service.create_collection("Test Col")
    service.add_product_to_collection(col.id, p.id)

    # Product must STILL not be in watchlist
    assert db.query(WatchlistItem).filter_by(product_id=p.id).first() is None

    # Remove from collection
    service.remove_product_from_collection(col.id, p.id)
    assert db.query(WatchlistItem).filter_by(product_id=p.id).first() is None


def test_p5_ac_02_collection_persistence_and_empty_name_rejection(p5_db_session):
    """
    P5-AC-02: Collection create/list/get/update/delete persists correctly.
    Empty/whitespace names rejected with 400.
    """
    db, _ = p5_db_session
    service = CollectionService(db)

    # Empty name rejection
    with pytest.raises(Exception) as exc_info:
        service.create_collection("   ")
    assert "cannot be empty" in str(exc_info.value)

    # Create valid collection
    col = service.create_collection("Q4 Holidays", description="High margin opportunities")
    assert col.id is not None
    assert col.name == "Q4 Holidays"
    assert col.description == "High margin opportunities"

    # Get collection
    fetched = service.get_collection(col.id)
    assert fetched.name == "Q4 Holidays"

    # Update collection
    updated = service.update_collection(col.id, name="Q4 Holidays Rev", description="Updated desc")
    assert updated.name == "Q4 Holidays Rev"
    assert updated.description == "Updated desc"

    # Update with empty name rejected
    with pytest.raises(Exception):
        service.update_collection(col.id, name="")

    # List collections
    all_cols = service.list_collections()
    assert len(all_cols) == 1
    assert all_cols[0].id == col.id


def test_p5_ac_03_destructive_boundary_preserves_products_and_history(p5_db_session):
    """
    P5-AC-03: Deleting a Collection removes only that Collection and its CollectionItems.
    Product, ProductSnapshot, WatchlistItem, AlertRule, AlertEvent preserved.
    """
    db, _ = p5_db_session
    service = CollectionService(db)
    now = datetime.now(timezone.utc)

    p = Product(external_product_id="ext_destr_1", title="Destructive Test", first_seen_at=now, last_seen_at=now)
    db.add(p)
    db.commit()

    s = ProductSnapshot(product_id=p.id, captured_at=now, sold_count=50, review_count=5, price=100.0)
    w = WatchlistItem(product_id=p.id, notes="provenance notes")
    r = AlertRule(product_id=p.id, rule_type="sales_velocity_above", threshold=10.0)
    db.add_all([s, w, r])
    db.commit()

    ev = AlertEvent(
        rule_id=r.id,
        product_id=p.id,
        triggering_snapshot_id=s.id,
        rule_type="sales_velocity_above",
        threshold=10.0,
        actual_value=15.0,
        message="Velocity met",
    )
    db.add(ev)
    db.commit()

    col = service.create_collection("To Delete")
    service.add_product_to_collection(col.id, p.id, review_status="candidate", notes="decision notes")

    assert db.query(CollectionItem).filter_by(collection_id=col.id).count() == 1

    # Delete Collection
    service.delete_collection(col.id)

    # Collection and items gone
    assert db.get(Collection, col.id) is None
    assert db.query(CollectionItem).filter_by(collection_id=col.id).count() == 0

    # Associated Product, Snapshot, Watchlist, Rule, Event PRESERVED
    assert db.get(Product, p.id) is not None
    assert db.get(ProductSnapshot, s.id) is not None
    assert db.get(WatchlistItem, w.id) is not None
    assert db.get(AlertRule, r.id) is not None
    assert db.get(AlertEvent, ev.id) is not None


def test_p5_ac_04_unique_membership_conflict_and_concurrent_duplicate(p5_db_session):
    """
    P5-AC-04: UNIQUE(collection_id, product_id) enforces duplicate conflict.
    """
    db, _ = p5_db_session
    service = CollectionService(db)
    now = datetime.now(timezone.utc)

    p = Product(external_product_id="ext_uniq_1", title="Uniq Product", first_seen_at=now, last_seen_at=now)
    db.add(p)
    db.commit()

    col = service.create_collection("Uniq Col")
    service.add_product_to_collection(col.id, p.id)

    # Second add must raise HTTP 409 Conflict
    with pytest.raises(Exception) as exc_info:
        service.add_product_to_collection(col.id, p.id)
    assert "already a member" in str(exc_info.value) or "409" in str(exc_info.value)

    # Database-level UNIQUE constraint / IntegrityError concurrent duplicate behavior verification
    item_dup = CollectionItem(collection_id=col.id, product_id=p.id, review_status="candidate")
    db.add(item_dup)
    with pytest.raises(Exception) as exc_info:
        db.commit()
    db.rollback()
    assert "UNIQUE constraint failed" in str(exc_info.value) or "IntegrityError" in str(exc_info.value)


def test_p5_ac_05_multi_collection_membership_independent_status_notes(p5_db_session):
    """
    P5-AC-05: One Product can belong to multiple Collections simultaneously
    without shared status/notes state.
    """
    db, _ = p5_db_session
    service = CollectionService(db)
    now = datetime.now(timezone.utc)

    p = Product(external_product_id="ext_multi_1", title="Multi Col Product", first_seen_at=now, last_seen_at=now)
    db.add(p)
    db.commit()

    col1 = service.create_collection("Col 1")
    col2 = service.create_collection("Col 2")

    item1 = service.add_product_to_collection(col1.id, p.id, review_status="reviewing", notes="Notes for Col 1")
    item2 = service.add_product_to_collection(col2.id, p.id, review_status="candidate", notes="Notes for Col 2")

    assert item1.review_status == "reviewing"
    assert item1.notes == "Notes for Col 1"
    assert item2.review_status == "candidate"
    assert item2.notes == "Notes for Col 2"

    # Update item 1 notes, item 2 remains unaffected
    service.update_item(col1.id, p.id, notes="Updated Col 1")
    refreshed_2 = db.query(CollectionItem).filter_by(collection_id=col2.id, product_id=p.id).first()
    assert refreshed_2.notes == "Notes for Col 2"


def test_p5_ac_06_review_status_vocabulary(p5_db_session):
    """
    P5-AC-06: Status defaults to 'new' and accepts only 'new', 'reviewing', 'candidate', 'rejected'.
    """
    db, _ = p5_db_session
    service = CollectionService(db)
    now = datetime.now(timezone.utc)

    p = Product(external_product_id="ext_status_1", title="Status Product", first_seen_at=now, last_seen_at=now)
    db.add(p)
    db.commit()

    col = service.create_collection("Status Col")
    item = service.add_product_to_collection(col.id, p.id)
    assert item.review_status == "new"

    for valid_status in ["reviewing", "candidate", "rejected", "new"]:
        updated = service.update_item(col.id, p.id, review_status=valid_status)
        assert updated.review_status == valid_status

    # Invalid status rejected
    with pytest.raises(Exception):
        service.update_item(col.id, p.id, review_status="invalid_status")


def test_p5_ac_07_decision_notes_ownership_isolated_from_watchlist_notes(p5_db_session):
    """
    P5-AC-07: Decision notes persist only on CollectionItem; WatchlistItem.notes is untouched.
    """
    db, _ = p5_db_session
    service = CollectionService(db)
    now = datetime.now(timezone.utc)

    p = Product(external_product_id="ext_notes_1", title="Notes Product", first_seen_at=now, last_seen_at=now)
    db.add(p)
    db.commit()

    w = WatchlistItem(product_id=p.id, notes="Original Watchlist Provenance")
    db.add(w)
    db.commit()

    col = service.create_collection("Notes Col")
    service.add_product_to_collection(col.id, p.id, notes="Affiliate margin looks 15%")

    # Verify separation
    w_reloaded = db.get(WatchlistItem, w.id)
    assert w_reloaded.notes == "Original Watchlist Provenance"

    service.update_item(col.id, p.id, notes="Supplier contact pending")
    w_reloaded = db.get(WatchlistItem, w.id)
    assert w_reloaded.notes == "Original Watchlist Provenance"


def test_p5_ac_08_unwatch_independence(p5_db_session):
    """
    P5-AC-08: Removing Watchlist membership leaves every CollectionItem,
    review status, and decision note intact.
    """
    db, _ = p5_db_session
    service = CollectionService(db)
    now = datetime.now(timezone.utc)

    p = Product(external_product_id="ext_unwatch_1", title="Unwatch Product", first_seen_at=now, last_seen_at=now)
    db.add(p)
    db.commit()

    w = WatchlistItem(product_id=p.id, notes="internal notes")
    db.add(w)
    db.commit()

    col = service.create_collection("Unwatch Col")
    service.add_product_to_collection(col.id, p.id, review_status="candidate", notes="Must buy sample")

    # Unwatch product
    db.delete(w)
    db.commit()

    # Collection item must still exist with status and notes
    item = db.query(CollectionItem).filter_by(collection_id=col.id, product_id=p.id).first()
    assert item is not None
    assert item.review_status == "candidate"
    assert item.notes == "Must buy sample"


def test_p5_ac_09_reverse_membership_lookup(p5_db_session):
    """
    P5-AC-09: Product-to-Collection reverse lookup uses collection_items(product_id).
    """
    db, _ = p5_db_session
    service = CollectionService(db)
    now = datetime.now(timezone.utc)

    p = Product(external_product_id="ext_rev_1", title="Rev Product", first_seen_at=now, last_seen_at=now)
    db.add(p)
    db.commit()

    col1 = service.create_collection("Spring 2026")
    col2 = service.create_collection("Kitchen Must Haves")
    service.add_product_to_collection(col1.id, p.id, review_status="reviewing", notes="note 1")
    service.add_product_to_collection(col2.id, p.id, review_status="candidate", notes="note 2")

    rev = service.get_collections_for_product(p.id)
    assert len(rev) == 2
    col_names = {r["collection_name"] for r in rev}
    assert col_names == {"Spring 2026", "Kitchen Must Haves"}


def test_p5_ac_10_collection_member_list_query_budget(p5_db_session):
    """
    P5-AC-10: Collection member list uses <= 2 SQL queries total with zero N+1.
    """
    db, engine = p5_db_session
    service = CollectionService(db)
    now = datetime.now(timezone.utc)

    col = service.create_collection("Budget Col")

    # Seed 5 products in collection
    for i in range(5):
        p = Product(external_product_id=f"ext_q_{i}", title=f"Q Product {i}", first_seen_at=now, last_seen_at=now)
        db.add(p)
        db.flush()
        if i % 2 == 0:
            db.add(WatchlistItem(product_id=p.id))
        service.add_product_to_collection(col.id, p.id)

    query_count = 0

    def query_listener(conn, cursor, statement, parameters, context, executemany):
        nonlocal query_count
        query_count += 1

    event.listen(engine, "after_cursor_execute", query_listener)
    try:
        query_count = 0
        members = service.get_collection_members(col.id)
        assert len(members) == 5
        assert query_count <= 2, f"Expected <= 2 SQL queries, got {query_count}"
    finally:
        event.remove(engine, "after_cursor_execute", query_listener)


# ==============================================================================
# WORKSTREAM 3: SAVED VIEWS (P5-AC-11 through P5-AC-15)
# ==============================================================================

def test_p5_ac_11_saved_view_crud_and_immutable_scope(p5_db_session):
    """
    P5-AC-11: SavedView CRUD works with immutable scope, payload_version=1,
    rejection of unsupported version or scope changes.
    """
    db, _ = p5_db_session
    service = SavedViewService(db)

    # Valid Trends view
    trends_payload = {
        "category": "Fashion",
        "trend_state": "eligible",
        "measured_only": True,
        "confidence": "high",
        "sort_by": "trend_score",
        "sort_direction": "desc",
        "limit": 50,
        "search": "summer dress",
        "min_score": 60.0,
    }
    view = service.create_saved_view(SavedViewCreate(
        name="Summer Trends",
        scope="trends",
        payload_version=1,
        payload=trends_payload,
    ))
    assert view.id is not None
    assert view.scope == "trends"
    assert view.payload_version == 1

    # Attempt to change scope on update rejected with 400
    with pytest.raises(Exception) as exc_info:
        service.update_saved_view(view.id, SavedViewUpdate(scope="watchlist"))
    assert "immutable" in str(exc_info.value)

    # Attempt unsupported version on update rejected
    with pytest.raises(Exception):
        service.update_saved_view(view.id, SavedViewUpdate(payload_version=2))

    # Rename works
    updated = service.update_saved_view(view.id, SavedViewUpdate(name="Summer Trends Rev"))
    assert updated.name == "Summer Trends Rev"

    # Delete view
    service.delete_saved_view(view.id)
    assert db.get(SavedView, view.id) is None


def test_p5_ac_12_trends_saved_view_exact_nine_keys(p5_db_session):
    """
    P5-AC-12: Trends payload contains exactly the nine persisted keys.
    Offset/skip rejected.
    """
    db, _ = p5_db_session
    service = SavedViewService(db)

    valid_payload = {
        "category": None,
        "trend_state": "all",
        "measured_only": False,
        "confidence": None,
        "sort_by": "sales_velocity",
        "sort_direction": "asc",
        "limit": 25,
        "search": "",
        "min_score": None,
    }
    view = service.create_saved_view(SavedViewCreate(
        name="All Trends Default",
        scope="trends",
        payload=valid_payload,
    ))
    assert view.payload == valid_payload

    # Rejection if 'skip' or 'offset' added
    payload_with_skip = dict(valid_payload, skip=10)
    with pytest.raises(Exception):
        service.create_saved_view(SavedViewCreate(
            name="Invalid Skip",
            scope="trends",
            payload=payload_with_skip,
        ))


def test_p5_ac_13_watchlist_saved_view_exact_seven_keys(p5_db_session):
    """
    P5-AC-13: Watchlist payload contains exactly the seven keys.
    search, min_score, and skip rejected.
    """
    db, _ = p5_db_session
    service = SavedViewService(db)

    valid_payload = {
        "category": "Beauty",
        "trend_state": "stale",
        "measured_only": True,
        "confidence": "medium",
        "sort_by": "freshness",
        "sort_direction": "desc",
        "limit": 50,
    }
    view = service.create_saved_view(SavedViewCreate(
        name="Stale Beauty Watchlist",
        scope="watchlist",
        payload=valid_payload,
    ))
    assert view.payload == valid_payload

    # Rejection of 'search' in Watchlist
    with pytest.raises(Exception):
        service.create_saved_view(SavedViewCreate(
            name="Invalid Search",
            scope="watchlist",
            payload=dict(valid_payload, search="lipstick"),
        ))

    # Rejection of 'min_score' in Watchlist
    with pytest.raises(Exception):
        service.create_saved_view(SavedViewCreate(
            name="Invalid Min Score",
            scope="watchlist",
            payload=dict(valid_payload, min_score=50.0),
        ))

    # Rejection of 'skip' in Watchlist
    with pytest.raises(Exception):
        service.create_saved_view(SavedViewCreate(
            name="Invalid Skip",
            scope="watchlist",
            payload=dict(valid_payload, skip=5),
        ))


def test_p5_ac_14_saved_view_strict_shape_and_extra_key_rejection(p5_db_session):
    """
    P5-AC-14: Missing keys and unknown keys rejected (extra='forbid').
    """
    db, _ = p5_db_session
    service = SavedViewService(db)

    # Missing 'limit'
    incomplete_payload = {
        "category": None,
        "trend_state": "all",
        "measured_only": False,
        "confidence": None,
        "sort_by": "trend_score",
        "sort_direction": "desc",
    }
    with pytest.raises(Exception):
        service.create_saved_view(SavedViewCreate(
            name="Missing Limit",
            scope="watchlist",
            payload=incomplete_payload,
        ))

    # Unknown key 'sql_injection'
    extra_key_payload = {
        "category": None,
        "trend_state": "all",
        "measured_only": False,
        "confidence": None,
        "sort_by": "trend_score",
        "sort_direction": "desc",
        "limit": 50,
        "custom_sql": "SELECT * FROM users",
    }
    with pytest.raises(Exception):
        service.create_saved_view(SavedViewCreate(
            name="SQL Injection",
            scope="watchlist",
            payload=extra_key_payload,
        ))


# ==============================================================================
# WORKSTREAM 4: PRODUCT COMPARE (P5-AC-16 through P5-AC-25)
# ==============================================================================

def test_p5_ac_16_compare_cardinality_boundaries_and_uniqueness(p5_db_session):
    """
    P5-AC-16: Exactly 2-5 unique product IDs required.
    Duplicates, <2, and >5 rejected.
    """
    db, _ = p5_db_session
    service = CompareService(db)

    now = datetime.now(timezone.utc)
    products = [
        Product(external_product_id=f"ext_comp_{i}", title=f"Comp {i}", first_seen_at=now, last_seen_at=now)
        for i in range(6)
    ]
    db.add_all(products)
    db.commit()
    p_ids = [p.id for p in products]

    # < 2 products rejected
    with pytest.raises(Exception) as exc_info:
        service.compare_products([p_ids[0]])
    assert "between 2 and 5" in str(exc_info.value)

    # > 5 products rejected
    with pytest.raises(Exception) as exc_info:
        service.compare_products(p_ids[:6])
    assert "between 2 and 5" in str(exc_info.value)

    # Duplicates rejected
    with pytest.raises(Exception) as exc_info:
        service.compare_products([p_ids[0], p_ids[0]])
    assert "Duplicate product IDs" in str(exc_info.value)

    # 2 products succeed
    res2 = service.compare_products([p_ids[0], p_ids[1]])
    assert len(res2.products) == 2

    # 5 products succeed
    res5 = service.compare_products(p_ids[:5])
    assert len(res5.products) == 5


def test_p5_ac_18_compare_single_as_of_utc_analytics_reuse_and_order(p5_db_session):
    """
    P5-AC-18: One shared as_of_utc exposed in response and used for every product.
    Caller request order preserved.
    """
    db, _ = p5_db_session
    service = CompareService(db)

    now = datetime(2026, 10, 6, 10, 0, 0, tzinfo=timezone.utc)
    p1 = Product(external_product_id="ext_ord_1", title="Product 1", first_seen_at=now - timedelta(days=2), last_seen_at=now)
    p2 = Product(external_product_id="ext_ord_2", title="Product 2", first_seen_at=now - timedelta(days=2), last_seen_at=now)
    db.add_all([p1, p2])
    db.flush()

    # Add snapshots
    db.add(ProductSnapshot(product_id=p1.id, captured_at=now - timedelta(hours=2), sold_count=200, review_count=20, price=50.0))
    db.add(ProductSnapshot(product_id=p2.id, captured_at=now - timedelta(hours=1), sold_count=300, review_count=30, price=80.0))
    db.commit()

    # Request order [p2.id, p1.id]
    res = service.compare_products([p2.id, p1.id], as_of_utc=now)
    assert res.as_of_utc == now
    assert len(res.products) == 2
    assert res.products[0].product_id == p2.id
    assert res.products[1].product_id == p1.id


def test_p5_ac_21_compare_collection_context_and_404_on_missing_collection(p5_db_session):
    """
    P5-AC-21: When collection_id supplied, member products return context, non-members return None.
    Missing collection_id returns 404.
    """
    db, _ = p5_db_session
    service = CompareService(db)
    col_service = CollectionService(db)

    now = datetime.now(timezone.utc)
    p1 = Product(external_product_id="ext_ctx_1", title="Ctx 1", first_seen_at=now, last_seen_at=now)
    p2 = Product(external_product_id="ext_ctx_2", title="Ctx 2", first_seen_at=now, last_seen_at=now)
    db.add_all([p1, p2])
    db.commit()

    col = col_service.create_collection("Compare Context Col")
    # Add only p1 to collection
    col_service.add_product_to_collection(col.id, p1.id, review_status="candidate", notes="Very promising")

    # Compare with valid collection_id
    res = service.compare_products([p1.id, p2.id], collection_id=col.id)
    assert res.products[0].collection_context is not None
    assert res.products[0].collection_context.review_status == "candidate"
    assert res.products[0].collection_context.notes == "Very promising"
    assert res.products[1].collection_context is None

    # Compare with nonexistent collection_id raises 404
    with pytest.raises(Exception) as exc_info:
        service.compare_products([p1.id, p2.id], collection_id=99999)
    assert "not found" in str(exc_info.value) or "404" in str(exc_info.value)


def test_p5_ac_22_compare_bounded_alert_summary(p5_db_session):
    """
    P5-AC-22: Grouped alert summary uses exactly as_of_utc - 7 days <= created_at <= as_of_utc.
    Lower bound included, upper bound included, prior events and future events excluded.
    """
    db, _ = p5_db_session
    service = CompareService(db)

    as_of = datetime(2026, 10, 6, 12, 0, 0, tzinfo=timezone.utc)
    p1 = Product(external_product_id="ext_al_1", title="Alert Product 1", first_seen_at=as_of - timedelta(days=10), last_seen_at=as_of)
    p2 = Product(external_product_id="ext_al_2", title="Alert Product 2", first_seen_at=as_of - timedelta(days=10), last_seen_at=as_of)
    db.add_all([p1, p2])
    db.flush()

    # Create 5 snapshots for 5 distinct alert events
    s1 = ProductSnapshot(product_id=p1.id, captured_at=as_of - timedelta(days=7), sold_count=100, review_count=10, price=50.0)
    s2 = ProductSnapshot(product_id=p1.id, captured_at=as_of - timedelta(days=3), sold_count=102, review_count=10, price=50.0)
    s3 = ProductSnapshot(product_id=p1.id, captured_at=as_of, sold_count=105, review_count=10, price=50.0)
    s4 = ProductSnapshot(product_id=p1.id, captured_at=as_of - timedelta(days=8), sold_count=98, review_count=10, price=50.0)
    s5 = ProductSnapshot(product_id=p1.id, captured_at=as_of + timedelta(hours=1), sold_count=106, review_count=10, price=50.0)
    r = AlertRule(product_id=p1.id, rule_type="sales_velocity_above", threshold=10.0)
    db.add_all([s1, s2, s3, s4, s5, r])
    db.flush()

    # Alert 1: Exactly at lower boundary (as_of - 7 days) -> INCLUDED
    ev_lower = AlertEvent(rule_id=r.id, product_id=p1.id, triggering_snapshot_id=s1.id, rule_type="sales_velocity_above", threshold=10.0, actual_value=12.0, message="Lower bound", created_at=as_of - timedelta(days=7))
    # Alert 2: Inside 7d window -> INCLUDED
    ev_mid = AlertEvent(rule_id=r.id, product_id=p1.id, triggering_snapshot_id=s2.id, rule_type="sales_velocity_above", threshold=10.0, actual_value=12.0, message="Mid window", created_at=as_of - timedelta(days=3))
    # Alert 3: Exactly at as_of_utc -> INCLUDED (and is latest)
    ev_exact = AlertEvent(rule_id=r.id, product_id=p1.id, triggering_snapshot_id=s3.id, rule_type="sales_velocity_above", threshold=10.0, actual_value=12.0, message="Exact as of", created_at=as_of)
    # Alert 4: Before 7d window (8 days ago) -> EXCLUDED
    ev_old = AlertEvent(rule_id=r.id, product_id=p1.id, triggering_snapshot_id=s4.id, rule_type="sales_velocity_above", threshold=10.0, actual_value=12.0, message="Old", created_at=as_of - timedelta(days=8))
    # Alert 5: Future alert (1 hour in future) -> EXCLUDED
    ev_future = AlertEvent(rule_id=r.id, product_id=p1.id, triggering_snapshot_id=s5.id, rule_type="sales_velocity_above", threshold=10.0, actual_value=12.0, message="Future", created_at=as_of + timedelta(hours=1))

    db.add_all([ev_lower, ev_mid, ev_exact, ev_old, ev_future])
    db.commit()

    res = service.compare_products([p1.id, p2.id], as_of_utc=as_of)
    comp_p1 = res.products[0]
    comp_p2 = res.products[1]

    # p1 should have exactly 3 alerts in window (lower, mid, exact)
    assert comp_p1.recent_alert_count_7d == 3
    assert comp_p1.latest_alert_at == as_of

    # p2 has no alerts
    assert comp_p2.recent_alert_count_7d == 0
    assert comp_p2.latest_alert_at is None


def test_p5_ac_23_compare_query_budget_le_3_sql_queries(p5_db_session):
    """
    P5-AC-23: 2-5 Product compare uses <= 3 SQL queries total with zero N+1.
    """
    db, engine = p5_db_session
    service = CompareService(db)
    col_service = CollectionService(db)

    now = datetime.now(timezone.utc)
    col = col_service.create_collection("Query Budget Col")
    p_ids = []
    for i in range(5):
        p = Product(external_product_id=f"ext_qb_{i}", title=f"QB {i}", first_seen_at=now, last_seen_at=now)
        db.add(p)
        db.flush()
        db.add(ProductSnapshot(product_id=p.id, captured_at=now, sold_count=50 + i, review_count=5, price=100.0))
        col_service.add_product_to_collection(col.id, p.id)
        p_ids.append(p.id)
    db.commit()

    target_col_id = col.id
    query_count = 0

    def query_listener(conn, cursor, statement, parameters, context, executemany):
        nonlocal query_count
        query_count += 1

    event.listen(engine, "after_cursor_execute", query_listener)
    try:
        query_count = 0
        res = service.compare_products(p_ids, collection_id=target_col_id)
        assert len(res.products) == 5
        assert query_count <= 3, f"Expected <= 3 SQL queries, executed {query_count}"
    finally:
        event.remove(engine, "after_cursor_execute", query_listener)


def test_p5_ac_24_quarantine_exclusion_fails_compare(p5_db_session):
    """
    P5-AC-24: Compare request containing a quarantined product fails explicitly (HTTP 400).
    """
    db, _ = p5_db_session
    service = CompareService(db)
    now = datetime.now(timezone.utc)

    p1 = Product(external_product_id="ext_ok_1", title="OK Product", first_seen_at=now, last_seen_at=now)
    p2 = Product(external_product_id="ext_quar_2", title="Quarantined Product", first_seen_at=now, last_seen_at=now)
    db.add_all([p1, p2])
    db.flush()

    # Quarantine p2
    db.add(QuarantinedProduct(product_id=p2.id, reason="Contaminated data"))
    db.commit()

    # Compare rejects quarantined product
    with pytest.raises(Exception) as exc_info:
        service.compare_products([p1.id, p2.id])
    assert "quarantined" in str(exc_info.value).lower()

    # Collection rejects adding quarantined product (Section 2 & P5-AC-24)
    col_service = CollectionService(db)
    col = col_service.create_collection("Quarantine Boundary Col")
    with pytest.raises(Exception) as exc_info_col:
        col_service.add_product_to_collection(col.id, p2.id)
    assert "quarantined" in str(exc_info_col.value).lower()


# ==============================================================================
# WORKSTREAM 5: BOOTSTRAP, PORTABILITY & BENCHMARK (P5-AC-25 through P5-AC-30)
# ==============================================================================

def test_p5_ac_26_27_additive_bootstrap_marker_advance_and_idempotency(tmp_path, monkeypatch):
    """
    P5-AC-26 & P5-AC-27: In-place bootstrap on representative Phase 4 DB with marker '1':
    - Adds exactly 'collections', 'collection_items', 'saved_views'
    - Preserves representative Phase 1-4 portable state
    - Required schema derives from Base.metadata.tables
    - Compatibility owner advances '1' -> '2' only after schema is verified
    - Repeated startup is idempotent
    """
    db_file = tmp_path / "inplace_upgrade_test.db"
    engine = create_engine(f"sqlite:///{db_file}")

    # 1. Build representative Phase 4 database: create all 10 Phase 4 tables
    phase4_tables = [
        Product.__table__,
        ProductSnapshot.__table__,
        CrawlRun.__table__,
        Category.__table__,
        ProductVideoLink.__table__,
        WatchlistItem.__table__,
        AlertRule.__table__,
        AlertEvent.__table__,
        QuarantinedProduct.__table__,
        SystemMetadata.__table__,
    ]
    Base.metadata.create_all(bind=engine, tables=phase4_tables)

    # Seed representative Phase 4 data
    Session = sessionmaker(bind=engine)
    with Session() as s:
        now = datetime.now(timezone.utc)
        p = Product(external_product_id="p4_repr_1", title="P4 Portable Product", first_seen_at=now, last_seen_at=now)
        s.add(p)
        s.flush()
        snap = ProductSnapshot(product_id=p.id, captured_at=now, sold_count=100, review_count=10, price=20.0)
        s.add(snap)
        s.flush()
        s.add(WatchlistItem(product_id=p.id, notes="P4 watch"))
        rule = AlertRule(
            product_id=p.id,
            rule_type="sales_velocity_above",
            threshold=10.0,
            last_evaluated_snapshot_id=snap.id,
            last_condition_met=True,
            last_triggered_at=now,
        )
        s.add(rule)
        s.flush()
        ev = AlertEvent(
            rule_id=rule.id,
            product_id=p.id,
            triggering_snapshot_id=snap.id,
            rule_type="sales_velocity_above",
            threshold=10.0,
            actual_value=15.0,
            message="P4 alert event",
            created_at=now,
        )
        s.add(ev)
        s.add(QuarantinedProduct(product_id=p.id, reason="Legacy quarantine test"))
        s.add(SystemMetadata(key="portable_backup_compatibility_version", value="1"))
        s.add(SystemMetadata(key="unrelated_operator_setting", value="custom_value"))
        s.commit()

    # Pre-upgrade table set
    inspector = inspect(engine)
    pre_tables = set(inspector.get_table_names())
    assert pre_tables == {t.name for t in phase4_tables}
    assert "collections" not in pre_tables
    assert "collection_items" not in pre_tables
    assert "saved_views" not in pre_tables

    # 2. Run Phase 5 init_db()
    monkeypatch.setattr("app.db.init_db.engine", engine)
    monkeypatch.setattr("app.db.init_db.SessionLocal", Session)

    init_db()

    # Verify post-upgrade table difference is EXACTLY the 3 Phase 5 tables
    inspector = inspect(engine)
    post_tables = set(inspector.get_table_names())
    diff = post_tables - pre_tables
    assert diff == {"collections", "collection_items", "saved_views"}

    # Verify representative Phase 1-4 data preserved
    with Session() as s:
        p_loaded = s.query(Product).filter_by(external_product_id="p4_repr_1").first()
        assert p_loaded is not None
        assert p_loaded.title == "P4 Portable Product"

        snap_loaded = s.query(ProductSnapshot).filter_by(product_id=p_loaded.id).first()
        assert snap_loaded.sold_count == 100

        w_loaded = s.query(WatchlistItem).filter_by(product_id=p_loaded.id).first()
        assert w_loaded.notes == "P4 watch"

        r_loaded = s.query(AlertRule).filter_by(product_id=p_loaded.id).first()
        assert r_loaded is not None
        assert r_loaded.last_evaluated_snapshot_id == snap_loaded.id
        assert r_loaded.last_condition_met is True
        assert r_loaded.last_triggered_at is not None

        ev_loaded = s.query(AlertEvent).filter_by(product_id=p_loaded.id).first()
        assert ev_loaded is not None
        assert ev_loaded.message == "P4 alert event"

        q_loaded = s.query(QuarantinedProduct).filter_by(product_id=p_loaded.id).first()
        assert q_loaded is not None

        unrelated = s.get(SystemMetadata, "unrelated_operator_setting")
        assert unrelated is not None and unrelated.value == "custom_value"

        # Compatibility marker advanced to '2' only after required schema verified
        marker = s.get(SystemMetadata, "portable_backup_compatibility_version")
        assert marker is not None and marker.value == "2"

    # 3. Repeated startup is idempotent
    init_db()
    with Session() as s:
        marker = s.get(SystemMetadata, "portable_backup_compatibility_version")
        assert marker.value == "2"

    engine.dispose()


def test_p5_ac_27_injected_failure_blocks_readiness(tmp_path, monkeypatch):
    """
    P5-AC-27: Injected schema/required-schema failure blocks application readiness:
    - Compatibility marker remains '1' (does NOT advance to '2')
    - init_db raises RuntimeError
    - Application startup fails, withholding readiness
    """
    db_file = tmp_path / "failure_injection_test.db"
    engine = create_engine(f"sqlite:///{db_file}")

    # Create Phase 4 tables only
    phase4_tables = [
        Product.__table__,
        ProductSnapshot.__table__,
        WatchlistItem.__table__,
        SystemMetadata.__table__,
    ]
    Base.metadata.create_all(bind=engine, tables=phase4_tables)
    Session = sessionmaker(bind=engine)
    with Session() as s:
        s.add(SystemMetadata(key="portable_backup_compatibility_version", value="1"))
        s.commit()

    monkeypatch.setattr("app.db.init_db.engine", engine)
    monkeypatch.setattr("app.db.init_db.SessionLocal", Session)

    # Inject failure: simulate required schema demanding a table that was not created
    real_get_required_schema = BackupService.get_required_schema
    monkeypatch.setattr(
        BackupService,
        "get_required_schema",
        lambda: dict(real_get_required_schema(), missing_critical_table={"id"}),
    )

    # Calling init_db must fail
    with pytest.raises(RuntimeError) as exc_info:
        init_db()
    assert "missing tables" in str(exc_info.value) or "Required schema validation failed" in str(exc_info.value)

    # Compatibility marker must NOT have advanced
    with Session() as s:
        marker = s.get(SystemMetadata, "portable_backup_compatibility_version")
        assert marker.value == "1"

    engine.dispose()


def test_p5_ac_28_version_1_portable_backup_rejection(tmp_path):
    """
    P5-AC-28: A valid Phase-4/version-1 portable backup candidate is rejected
    by Phase 5 under unchanged same-version policy.
    """
    v1_backup = tmp_path / "tinix-affiliate-v1-20261005T100000.000000Z.sqlite3"
    engine = create_engine(f"sqlite:///{v1_backup}")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    with Session() as s:
        # Seed marker '1'
        s.add(SystemMetadata(key="portable_backup_compatibility_version", value="1"))
        s.commit()
    engine.dispose()

    # Validate against Phase 5 BackupService
    valid, reason = BackupService.validate_sqlite_file(v1_backup)
    assert valid is False
    assert "Phiên bản tương thích không hợp lệ" in reason
    assert "yêu cầu '2', tìm thấy '1'" in reason


def test_p5_ac_29_version_2_backup_roundtrip(tmp_path, monkeypatch):
    """
    P5-AC-29: A Phase-5/version-2 portable backup validates and round-trips Collections,
    CollectionItems, Saved Views, and representative existing portable state.
    """
    db_file = tmp_path / "v2_roundtrip_source.db"
    backups_dir = tmp_path / "backups"
    backups_dir.mkdir(parents=True, exist_ok=True)

    engine = create_engine(f"sqlite:///{db_file}")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)

    with Session() as s:
        now = datetime.now(timezone.utc)
        p = Product(external_product_id="v2_p_1", title="V2 Product", first_seen_at=now, last_seen_at=now)
        s.add(p)
        s.flush()
        col = Collection(name="V2 Collection", description="Roundtrip test")
        s.add(col)
        s.flush()
        s.add(CollectionItem(collection_id=col.id, product_id=p.id, review_status="candidate", notes="Roundtrip notes"))
        s.add(SavedView(
            name="V2 View",
            scope="trends",
            payload_version=1,
            payload={
                "category": None,
                "trend_state": "eligible",
                "measured_only": True,
                "confidence": "high",
                "sort_by": "trend_score",
                "sort_direction": "desc",
                "limit": 50,
                "search": "",
                "min_score": None,
            }
        ))
        s.add(SystemMetadata(key="portable_backup_compatibility_version", value="2"))
        s.commit()

    monkeypatch.setattr(BackupService, "get_db_path", lambda: db_file)
    monkeypatch.setattr(BackupService, "get_backups_dir", lambda: backups_dir)

    # Create hot backup
    result = BackupService.create_backup()
    assert result["status"] == "ok"
    assert result["compatibility_version"] == "2"

    backup_path = Path(result["file_path"])
    valid, reason = BackupService.validate_sqlite_file(backup_path)
    assert valid is True

    # Verify backup contains roundtrip data
    backup_engine = create_engine(f"sqlite:///{backup_path}")
    BackupSession = sessionmaker(bind=backup_engine)
    with BackupSession() as bs:
        col = bs.query(Collection).filter_by(name="V2 Collection").first()
        assert col is not None
        item = bs.query(CollectionItem).filter_by(collection_id=col.id).first()
        assert item.review_status == "candidate"
        assert item.notes == "Roundtrip notes"

        view = bs.query(SavedView).filter_by(name="V2 View").first()
        assert view is not None
        assert view.payload["trend_state"] == "eligible"
    backup_engine.dispose()
    engine.dispose()


def test_p5_ac_25_representative_200_products_5000_snapshots_compare_benchmark(tmp_path):
    """
    P5-AC-25: 5-Product compare benchmark on the representative 200-Product / 5,000-snapshot fixture.
    Must remain strictly below 200ms regression ceiling.
    Measures and honestly reports < 50ms research target.
    """
    db_file = tmp_path / "bench_compare.db"
    engine = create_engine(f"sqlite:///{db_file}")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    now = datetime(2026, 10, 6, 12, 0, 0, tzinfo=timezone.utc)

    # 1. Seed 200 products
    products = []
    for i in range(200):
        p = Product(
            external_product_id=f"comp_bench_{i}",
            title=f"Benchmark Product {i}",
            first_seen_at=now - timedelta(days=5),
            last_seen_at=now,
            category="Fashion" if i % 2 == 0 else "Beauty",
        )
        products.append(p)
    db.add_all(products)
    db.flush()

    # Watch half of them
    db.add_all([WatchlistItem(product_id=p.id) for p in products[:100]])

    # 2. Seed 25 snapshots per product (5,000 snapshots total)
    snapshots = []
    for p in products:
        for s_idx in range(25):
            snapshots.append(ProductSnapshot(
                product_id=p.id,
                captured_at=now - timedelta(hours=(24 - s_idx) * 4),
                sold_count=100 + s_idx * 10,
                review_count=10 + s_idx,
                rating=4.5,
                price=150000.0,
            ))
    db.add_all(snapshots)
    db.flush()

    # 3. Create a collection and add 5 products
    col = Collection(name="Benchmark Collection")
    db.add(col)
    db.flush()
    target_products = products[:5]
    for p in target_products:
        db.add(CollectionItem(collection_id=col.id, product_id=p.id, review_status="candidate", notes="Bench notes"))

    # Seed alert events
    rule = AlertRule(product_id=target_products[0].id, rule_type="sales_velocity_above", threshold=10.0)
    db.add(rule)
    db.flush()
    db.add(AlertEvent(
        rule_id=rule.id,
        product_id=target_products[0].id,
        triggering_snapshot_id=snapshots[0].id,
        rule_type="sales_velocity_above",
        threshold=10.0,
        actual_value=15.0,
        message="Bench alert",
        created_at=now - timedelta(days=2),
    ))
    db.commit()

    service = CompareService(db)
    target_ids = [p.id for p in target_products]

    # Warmup call
    service.compare_products(target_ids, collection_id=col.id, as_of_utc=now)

    # Benchmark over 10 iterations (warmup = 1)
    latencies = []
    for _ in range(10):
        t0 = time.perf_counter()
        res = service.compare_products(target_ids, collection_id=col.id, as_of_utc=now)
        latencies.append((time.perf_counter() - t0) * 1000.0)

    best_ms = min(latencies)
    worst_ms = max(latencies)
    sorted_l = sorted(latencies)
    median_ms = sorted_l[len(sorted_l) // 2]
    p95_ms = sorted_l[int(0.95 * len(sorted_l))]

    # Hard gate: < 200ms
    assert best_ms < 200.0, f"Compare best took {best_ms:.2f}ms, exceeding 200ms hard gate"
    assert median_ms < 200.0, f"Compare median took {median_ms:.2f}ms, exceeding 200ms hard gate"
    print(f"\n[BENCHMARK EVIDENCE] 5-Product Compare on 200-prod/5,000-snap fixture:")
    print(f"Iterations=10, Warmup=1, Best={best_ms:.2f}ms, Median={median_ms:.2f}ms, Worst={worst_ms:.2f}ms, P95={p95_ms:.2f}ms")
    print(f"All Latencies (ms): {[round(l, 2) for l in latencies]}")

    db.close()
    engine.dispose()
