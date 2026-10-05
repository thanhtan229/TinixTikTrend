import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, patch
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.models import Product, ProductSnapshot, WatchlistItem, AlertRule, AlertEvent, SystemMetadata, QuarantinedProduct
from app.db.init_db import init_db
from app.services.alert_service import AlertService


def test_one_time_watchlist_bootstrap_and_unwatch_survives_restart(tmp_path):
    db_file = tmp_path / "bootstrap_test.db"
    db_url = f"sqlite:///{db_file}"

    # First session: setup tables & insert legacy products
    engine = create_engine(db_url)
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    now = datetime(2026, 10, 5, 12, 0, 0, tzinfo=timezone.utc)
    p1 = Product(external_product_id="leg_1", title="Legacy 1", url="https://shop.tiktok.com/view/product/leg_1", first_seen_at=now, last_seen_at=now)
    p2 = Product(external_product_id="leg_2", title="Legacy 2", url="https://shop.tiktok.com/view/product/leg_2", first_seen_at=now, last_seen_at=now)
    p3 = Product(external_product_id="leg_3", title="Legacy 3", url="https://shop.tiktok.com/view/product/leg_3", first_seen_at=now, last_seen_at=now)
    p_bad = Product(external_product_id="tt_item_legacy", title="Bad Legacy", url="https://shop.tiktok.com/view/product/bad", first_seen_at=now, last_seen_at=now)

    db.add_all([p1, p2, p3, p_bad])
    db.commit()

    # Run init_db for the first time
    init_db(db)

    # Verify backfill
    watched = db.query(WatchlistItem).all()
    watched_product_ids = {w.product_id for w in watched}
    assert p1.id in watched_product_ids
    assert p2.id in watched_product_ids
    assert p3.id in watched_product_ids
    assert p_bad.id not in watched_product_ids # Quarantined legacy product is excluded

    # Verify durable marker
    marker = db.get(SystemMetadata, "legacy_tracked_backfill_completed")
    assert marker is not None
    assert marker.value == "true"

    # Now simulate user unwatching all products (intentionally empty watchlist)
    db.query(WatchlistItem).delete()
    db.commit()
    assert db.query(WatchlistItem).count() == 0

    db.close()
    engine.dispose()

    # Second session: simulate server restart on the same file
    engine2 = create_engine(db_url)
    Session2 = sessionmaker(bind=engine2)
    db2 = Session2()

    # Run init_db on restart
    init_db(db2)

    # Invariant: Watchlist MUST remain empty; marker prevents repopulation
    assert db2.query(WatchlistItem).count() == 0
    assert db2.get(SystemMetadata, "legacy_tracked_backfill_completed").value == "true"

    db2.close()
    engine2.dispose()


def test_crash_before_bootstrap_completion_retry(tmp_path):
    db_file = tmp_path / "retry_test.db"
    db_url = f"sqlite:///{db_file}"

    engine = create_engine(db_url)
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    now = datetime(2026, 10, 5, 12, 0, 0, tzinfo=timezone.utc)
    p1 = Product(external_product_id="retry_1", title="Retry 1", url="https://shop.tiktok.com/view/product/retry_1", first_seen_at=now, last_seen_at=now)
    p2 = Product(external_product_id="retry_2", title="Retry 2", url="https://shop.tiktok.com/view/product/retry_2", first_seen_at=now, last_seen_at=now)
    db.add_all([p1, p2])
    db.commit()

    # Simulate crash during bootstrap: insert 1 item into Watchlist, but crash before committing marker
    db.add(WatchlistItem(product_id=p1.id))
    # Rollback simulates crash
    db.rollback()

    assert db.get(SystemMetadata, "legacy_tracked_backfill_completed") is None

    db.close()
    engine.dispose()

    # Reconnect and run init_db cleanly
    engine2 = create_engine(db_url)
    Session2 = sessionmaker(bind=engine2)
    db2 = Session2()

    init_db(db2)

    # Both products should now be in watchlist and marker saved
    assert db2.query(WatchlistItem).count() == 2
    assert db2.get(SystemMetadata, "legacy_tracked_backfill_completed") is not None

    db2.close()
    engine2.dispose()


def test_post_snapshot_commit_pre_alert_commit_catch_up(tmp_path):
    db_file = tmp_path / "catchup_test.db"
    db_url = f"sqlite:///{db_file}"

    engine = create_engine(db_url)
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    init_db(db)

    now = datetime(2026, 10, 5, 12, 0, 0, tzinfo=timezone.utc)
    p = Product(external_product_id="catchup_prod", title="Catchup Prod", first_seen_at=now - timedelta(days=2), last_seen_at=now)
    db.add(p)
    db.commit()

    # Initial baseline snapshot
    s0 = ProductSnapshot(product_id=p.id, captured_at=now - timedelta(hours=12), sold_count=100)
    db.add(s0)
    db.commit()

    # Create active alert rule
    alert_service = AlertService(db)
    rule = alert_service.create_rule(product_id=p.id, rule_type="sales_velocity_above", threshold=100.0)
    assert rule.last_evaluated_snapshot_id == s0.id
    assert rule.last_condition_met is False

    # Simulate ingestion of s1: snapshot commits, but server crashes BEFORE alert evaluation
    s1 = ProductSnapshot(product_id=p.id, captured_at=now - timedelta(hours=6), sold_count=500)
    db.add(s1)
    db.commit()

    # Ingestion committed s1, but rule.last_evaluated_snapshot_id is still s0.id
    assert db.get(AlertRule, rule.id).last_evaluated_snapshot_id == s0.id
    assert db.query(AlertEvent).count() == 0

    rule_id = rule.id
    s1_id = s1.id

    db.close()
    engine.dispose()

    # On restart, run catch_up_alerts()
    engine2 = create_engine(db_url)
    Session2 = sessionmaker(bind=engine2)
    db2 = Session2()

    alert_service2 = AlertService(db2)
    emitted = alert_service2.catch_up_alerts()

    # Catch-up should have evaluated s1 and emitted 1 alert event
    assert emitted == 1
    events = db2.query(AlertEvent).filter_by(rule_id=rule_id).all()
    assert len(events) == 1
    assert events[0].triggering_snapshot_id == s1_id

    # Cursor must be advanced to s1
    reloaded_rule = db2.get(AlertRule, rule_id)
    assert reloaded_rule.last_evaluated_snapshot_id == s1_id
    assert reloaded_rule.last_condition_met is True

    db2.close()
    engine2.dispose()


def test_atomic_event_plus_cursor_rollback(tmp_path):
    db_file = tmp_path / "atomic_test.db"
    db_url = f"sqlite:///{db_file}"

    engine = create_engine(db_url)
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    init_db(db)

    now = datetime(2026, 10, 5, 12, 0, 0, tzinfo=timezone.utc)
    p = Product(external_product_id="atomic_prod", title="Atomic Prod", first_seen_at=now - timedelta(days=2), last_seen_at=now)
    db.add(p)
    db.commit()

    s0 = ProductSnapshot(product_id=p.id, captured_at=now - timedelta(hours=12), sold_count=100)
    s1 = ProductSnapshot(product_id=p.id, captured_at=now - timedelta(hours=6), sold_count=500)
    db.add_all([s0, s1])
    db.commit()

    alert_service = AlertService(db)
    rule = alert_service.create_rule(product_id=p.id, rule_type="sales_velocity_above", threshold=100.0)
    rule.last_evaluated_snapshot_id = s0.id
    rule.last_condition_met = False
    db.commit()

    # Inject failure during db.commit in evaluate_snapshot
    with patch.object(db, "commit", side_effect=RuntimeError("Disk I/O error")):
        with pytest.raises(RuntimeError):
            alert_service.evaluate_snapshot(product_id=p.id, snapshot_id=s1.id)

    # After rollback: event must not exist and cursor must not have moved
    assert db.query(AlertEvent).count() == 0
    refreshed_rule = db.get(AlertRule, rule.id)
    assert refreshed_rule.last_evaluated_snapshot_id == s0.id
    assert refreshed_rule.last_condition_met is False

    db.close()
    engine.dispose()


def test_commit_then_crash_idempotency(tmp_path):
    db_file = tmp_path / "idempotent_test.db"
    db_url = f"sqlite:///{db_file}"

    engine = create_engine(db_url)
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    init_db(db)

    now = datetime(2026, 10, 5, 12, 0, 0, tzinfo=timezone.utc)
    p = Product(external_product_id="idemp_prod", title="Idemp Prod", first_seen_at=now - timedelta(days=2), last_seen_at=now)
    db.add(p)
    db.commit()

    s0 = ProductSnapshot(product_id=p.id, captured_at=now - timedelta(hours=12), sold_count=100)
    s1 = ProductSnapshot(product_id=p.id, captured_at=now - timedelta(hours=6), sold_count=500)
    db.add_all([s0, s1])
    db.commit()

    alert_service = AlertService(db)
    rule = alert_service.create_rule(product_id=p.id, rule_type="sales_velocity_above", threshold=100.0)
    rule.last_evaluated_snapshot_id = s0.id
    rule.last_condition_met = False
    db.commit()

    # First evaluation succeeds
    events = alert_service.evaluate_snapshot(product_id=p.id, snapshot_id=s1.id)
    assert len(events) == 1
    assert db.query(AlertEvent).count() == 1

    # Replay on same snapshot must not duplicate events
    events_replay = alert_service.evaluate_snapshot(product_id=p.id, snapshot_id=s1.id)
    assert len(events_replay) == 0
    assert db.query(AlertEvent).count() == 1

    db.close()
    engine.dispose()


def test_no_retroactive_create_edit_reenable_alerts(tmp_path):
    db_file = tmp_path / "retroactive_test.db"
    db_url = f"sqlite:///{db_file}"

    engine = create_engine(db_url)
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    init_db(db)

    now = datetime(2026, 10, 5, 12, 0, 0, tzinfo=timezone.utc)
    p = Product(external_product_id="retro_prod", title="Retro Prod", first_seen_at=now - timedelta(days=3), last_seen_at=now)
    db.add(p)
    db.commit()

    # Product already has high sales velocity (>500) in database
    s0 = ProductSnapshot(product_id=p.id, captured_at=now - timedelta(hours=24), sold_count=100)
    s1 = ProductSnapshot(product_id=p.id, captured_at=now, sold_count=600)
    db.add_all([s0, s1])
    db.commit()

    alert_service = AlertService(db)

    # 1. CREATE RULE: must not alert retroactively on existing snapshots
    rule = alert_service.create_rule(product_id=p.id, rule_type="sales_velocity_above", threshold=50.0)
    assert db.query(AlertEvent).count() == 0
    assert rule.last_evaluated_snapshot_id == s1.id
    assert rule.last_condition_met is True

    # 2. EDIT RULE: threshold changed, must not alert retroactively
    alert_service.update_rule(rule_id=rule.id, threshold=20.0)
    assert db.query(AlertEvent).count() == 0

    # 3. RE-ENABLE RULE: toggle off and on, must not alert retroactively
    alert_service.update_rule(rule_id=rule.id, is_enabled=False)
    alert_service.update_rule(rule_id=rule.id, is_enabled=True)
    assert db.query(AlertEvent).count() == 0

    db.close()
    engine.dispose()


def test_durable_read_unread_state_across_restart(tmp_path):
    db_file = tmp_path / "read_state_test.db"
    db_url = f"sqlite:///{db_file}"

    engine = create_engine(db_url)
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    init_db(db)

    now = datetime(2026, 10, 5, 12, 0, 0, tzinfo=timezone.utc)
    p = Product(external_product_id="read_prod", title="Read Prod", first_seen_at=now, last_seen_at=now)
    db.add(p)
    db.commit()

    snap = ProductSnapshot(product_id=p.id, captured_at=now, sold_count=100)
    db.add(snap)
    db.commit()

    rule = AlertRule(product_id=p.id, rule_type="sales_velocity_above", threshold=50.0)
    db.add(rule)
    db.commit()

    ev = AlertEvent(rule_id=rule.id, product_id=p.id, triggering_snapshot_id=snap.id,
                    rule_type="sales_velocity_above", threshold=50.0, actual_value=80.0,
                    message="Msg", is_read=False, created_at=now)
    db.add(ev)
    db.commit()

    alert_service = AlertService(db)
    assert alert_service.get_unread_count() == 1

    # Mark read
    ev_id = ev.id
    alert_service.mark_event_read(ev_id)
    assert alert_service.get_unread_count() == 0

    db.close()
    engine.dispose()

    # Restart session
    engine2 = create_engine(db_url)
    Session2 = sessionmaker(bind=engine2)
    db2 = Session2()

    alert_service2 = AlertService(db2)
    assert alert_service2.get_unread_count() == 0
    reloaded_ev = db2.get(AlertEvent, ev_id)
    assert reloaded_ev.is_read is True

    db2.close()
    engine2.dispose()


@pytest.mark.asyncio
async def test_startup_ordering_and_catchup_failure_blocks_scheduler():
    from app.main import lifespan, app

    # Case 1: Normal startup runs in correct order
    call_order = []

    def mock_init_db():
        call_order.append("init_db")

    def mock_catch_up(self):
        call_order.append("catch_up_alerts")
        return 0

    def mock_start_scheduler():
        call_order.append("start_scheduler")

    def mock_shutdown_scheduler():
        call_order.append("shutdown_scheduler")

    with patch("app.main.init_db", side_effect=mock_init_db), \
         patch.object(AlertService, "catch_up_alerts", mock_catch_up), \
         patch("app.main.start_scheduler", side_effect=mock_start_scheduler), \
         patch("app.main.shutdown_scheduler", side_effect=mock_shutdown_scheduler):
        
        async with lifespan(app):
            call_order.append("app_ready")

    assert call_order == ["init_db", "catch_up_alerts", "start_scheduler", "app_ready", "shutdown_scheduler"]

    # Case 2: Catch-up failure halts startup and prevents start_scheduler
    call_order_fail = []

    def mock_catch_up_error(self):
        call_order_fail.append("catch_up_alerts")
        raise RuntimeError("Catch-up DB corruption")

    with patch("app.main.init_db", side_effect=lambda: call_order_fail.append("init_db")), \
         patch.object(AlertService, "catch_up_alerts", mock_catch_up_error), \
         patch("app.main.start_scheduler", side_effect=lambda: call_order_fail.append("start_scheduler")):
        
        with pytest.raises(RuntimeError, match="Catch-up DB corruption"):
            async with lifespan(app):
                pass

    assert "start_scheduler" not in call_order_fail
