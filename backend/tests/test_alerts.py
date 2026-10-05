import pytest
from datetime import datetime, timezone, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError
from fastapi.testclient import TestClient

from app.db.base import Base
from app.db.session import get_db
from app.models import Product, ProductSnapshot, AlertRule, AlertEvent
from app.main import app
from app.services.alert_service import AlertService


from tests.conftest import TestingSessionLocal


@pytest.fixture
def db():
    session = TestingSessionLocal()
    yield session
    session.rollback()
    for pid in ["prod_val", "prod_price", "prod_cd", "prod_uniq", "prod_read"]:
        p = session.query(Product).filter_by(external_product_id=pid).first()
        if p:
            session.delete(p)
    session.commit()
    session.close()


def test_rule_type_and_direction_validation(db, client):
    now = datetime(2026, 10, 5, 12, 0, 0, tzinfo=timezone.utc)
    p = Product(external_product_id="prod_val", title="Validation Product", first_seen_at=now, last_seen_at=now)
    db.add(p)
    db.commit()

    # 1. Invalid rule type rejected
    res = client.post("/api/alerts/rules", json={"product_id": p.id, "rule_type": "review_delta", "threshold": 50.0})
    assert res.status_code == 400

    # 2. Non-positive threshold rejected
    res = client.post("/api/alerts/rules", json={"product_id": p.id, "rule_type": "sales_velocity_above", "threshold": 0.0})
    assert res.status_code == 422 # Pydantic Field(gt=0) validation

    res = client.post("/api/alerts/rules", json={"product_id": p.id, "rule_type": "sales_velocity_above", "threshold": -5.0})
    assert res.status_code == 422

    # 3. Direction supplied to non-price rule rejected
    res = client.post("/api/alerts/rules", json={
        "product_id": p.id,
        "rule_type": "sales_velocity_above",
        "threshold": 100.0,
        "direction": "up",
    })
    assert res.status_code == 400
    assert "Direction is not permitted for non-price rule" in res.json()["detail"]

    # 4. Missing direction for price rule rejected
    res = client.post("/api/alerts/rules", json={
        "product_id": p.id,
        "rule_type": "price_change_pct",
        "threshold": 10.0,
    })
    assert res.status_code == 400
    assert "Direction is required for price_change_pct" in res.json()["detail"]

    # 5. Invalid direction for price rule rejected
    res = client.post("/api/alerts/rules", json={
        "product_id": p.id,
        "rule_type": "price_change_pct",
        "threshold": 10.0,
        "direction": "sideways",
    })
    assert res.status_code == 400

    # 6. Valid rule creations
    for r_type in ["sales_velocity_above", "trend_score_above"]:
        res = client.post("/api/alerts/rules", json={"product_id": p.id, "rule_type": r_type, "threshold": 50.0})
        assert res.status_code == 201

    for d in ["up", "down", "either"]:
        res = client.post("/api/alerts/rules", json={
            "product_id": p.id,
            "rule_type": "price_change_pct",
            "threshold": 15.0,
            "direction": d,
        })
        assert res.status_code == 201


def test_all_three_price_directions_and_event_persistence(db):
    now = datetime(2026, 10, 5, 12, 0, 0, tzinfo=timezone.utc)
    p = Product(external_product_id="prod_price", title="Price Test", first_seen_at=now - timedelta(days=2), last_seen_at=now)
    db.add(p)
    db.commit()

    # Base snapshot: price = 100,000 VND
    s0 = ProductSnapshot(product_id=p.id, captured_at=now - timedelta(hours=2), price=100000.0, sold_count=10)
    db.add(s0)
    db.commit()

    service = AlertService(db)
    # Create rules for up, down, either with threshold 10%
    rule_up = service.create_rule(product_id=p.id, rule_type="price_change_pct", threshold=10.0, direction="up")
    rule_down = service.create_rule(product_id=p.id, rule_type="price_change_pct", threshold=10.0, direction="down")
    rule_either = service.create_rule(product_id=p.id, rule_type="price_change_pct", threshold=10.0, direction="either")

    # CASE 1: Price goes UP to 115,000 (+15%)
    s1 = ProductSnapshot(product_id=p.id, captured_at=now - timedelta(hours=1), price=115000.0, sold_count=10)
    db.add(s1)
    db.commit()

    events_1 = service.evaluate_snapshot(product_id=p.id, snapshot_id=s1.id)
    # rule_up and rule_either should fire; rule_down should NOT fire
    triggered_rules_1 = {ev.rule_id for ev in events_1}
    assert rule_up.id in triggered_rules_1
    assert rule_either.id in triggered_rules_1
    assert rule_down.id not in triggered_rules_1

    for ev in events_1:
        assert ev.actual_direction == "up"
        assert ev.actual_value == 15.0
        assert "trending" not in ev.message.lower()
        assert "xu hướng" not in ev.message.lower()

    # CASE 2: Price drops to 90,000 (-21.7% from 115,000)
    s2 = ProductSnapshot(product_id=p.id, captured_at=now, price=90000.0, sold_count=10)
    db.add(s2)
    db.commit()

    events_2 = service.evaluate_snapshot(product_id=p.id, snapshot_id=s2.id)
    triggered_rules_2 = {ev.rule_id for ev in events_2}
    # rule_down should fire; rule_either also has a new crossing (down)
    assert rule_down.id in triggered_rules_2
    for ev in events_2:
        if ev.rule_id == rule_down.id:
            assert ev.actual_direction == "down"
            assert round(ev.actual_value, 1) == -21.7
            assert "trending" not in ev.message.lower()


def test_cooldown_semantics_exact_boundaries(db):
    now = datetime(2026, 10, 5, 12, 0, 0, tzinfo=timezone.utc)
    p = Product(external_product_id="prod_cd", title="Cooldown Test", first_seen_at=now - timedelta(days=2), last_seen_at=now)
    db.add(p)
    db.commit()

    # 1. Cooldown 0: always eligible on valid crossing
    service = AlertService(db)
    rule_cd0 = service.create_rule(product_id=p.id, rule_type="sales_velocity_above", threshold=100.0, cooldown_minutes=0)

    # First crossing: should emit
    s1 = ProductSnapshot(product_id=p.id, captured_at=now - timedelta(hours=10), sold_count=100)
    s2 = ProductSnapshot(product_id=p.id, captured_at=now - timedelta(hours=6), sold_count=400) # velocity ~ 1200 > 100
    db.add_all([s1, s2])
    db.commit()

    res = service.evaluate_rule_against_snapshot(rule_cd0, p, s2)
    assert res.should_emit is True

    # 2. Cooldown 60 minutes: test before boundary, exact boundary, after boundary
    rule_cd60 = service.create_rule(product_id=p.id, rule_type="sales_velocity_above", threshold=100.0, cooldown_minutes=60)
    last_trig = now - timedelta(minutes=60)
    rule_cd60.last_triggered_at = last_trig
    rule_cd60.last_condition_met = False # New crossing

    # Case A: Just before boundary (59 minutes after last trigger -> diff is 59 min < 60 min)
    snap_before = ProductSnapshot(product_id=p.id, captured_at=last_trig + timedelta(minutes=59), sold_count=700)
    db.add(snap_before)
    db.commit()

    res_before = service.evaluate_rule_against_snapshot(rule_cd60, p, snap_before)
    assert res_before.is_crossing is True
    assert res_before.is_suppressed is True
    assert res_before.should_emit is False

    # Case B: Exactly at boundary (60 minutes after last trigger -> diff is 60 min >= 60 min)
    rule_cd60.last_condition_met = False
    snap_exact = ProductSnapshot(product_id=p.id, captured_at=last_trig + timedelta(minutes=60), sold_count=800)
    db.add(snap_exact)
    db.commit()

    res_exact = service.evaluate_rule_against_snapshot(rule_cd60, p, snap_exact)
    assert res_exact.is_crossing is True
    assert res_exact.is_suppressed is False
    assert res_exact.should_emit is True

    # Case C: Just after boundary (61 minutes after last trigger -> diff is 61 min >= 60 min)
    rule_cd60.last_condition_met = False
    snap_after = ProductSnapshot(product_id=p.id, captured_at=last_trig + timedelta(minutes=61), sold_count=900)
    db.add(snap_after)
    db.commit()

    res_after = service.evaluate_rule_against_snapshot(rule_cd60, p, snap_after)
    assert res_after.is_crossing is True
    assert res_after.is_suppressed is False
    assert res_after.should_emit is True


def test_db_uniqueness_composite_rule_snapshot(db):
    now = datetime(2026, 10, 5, 12, 0, 0, tzinfo=timezone.utc)
    p = Product(external_product_id="prod_uniq", title="Uniq", first_seen_at=now, last_seen_at=now)
    db.add(p)
    db.commit()

    snap = ProductSnapshot(product_id=p.id, captured_at=now, sold_count=100)
    db.add(snap)
    db.commit()

    rule = AlertRule(product_id=p.id, rule_type="sales_velocity_above", threshold=50.0)
    db.add(rule)
    db.commit()

    ev1 = AlertEvent(
        rule_id=rule.id,
        product_id=p.id,
        triggering_snapshot_id=snap.id,
        rule_type="sales_velocity_above",
        threshold=50.0,
        actual_value=80.0,
        message="Alert 1",
        created_at=now,
    )
    db.add(ev1)
    db.commit()

    # Second event with SAME (rule_id, triggering_snapshot_id) must fail with IntegrityError
    ev2 = AlertEvent(
        rule_id=rule.id,
        product_id=p.id,
        triggering_snapshot_id=snap.id,
        rule_type="sales_velocity_above",
        threshold=50.0,
        actual_value=90.0,
        message="Alert 2 duplicate",
        created_at=now,
    )
    db.add(ev2)
    with pytest.raises(IntegrityError):
        db.commit()
    db.rollback()


def test_notification_read_state_api(db, client):
    now = datetime(2026, 10, 5, 12, 0, 0, tzinfo=timezone.utc)
    p = Product(external_product_id="prod_read", title="Read Test", first_seen_at=now, last_seen_at=now)
    db.add(p)
    db.commit()

    snap = ProductSnapshot(product_id=p.id, captured_at=now, sold_count=100)
    db.add(snap)
    db.commit()

    rule = AlertRule(product_id=p.id, rule_type="sales_velocity_above", threshold=50.0)
    db.add(rule)
    db.commit()

    ev1 = AlertEvent(rule_id=rule.id, product_id=p.id, triggering_snapshot_id=snap.id,
                     rule_type="sales_velocity_above", threshold=50.0, actual_value=60.0,
                     message="Msg 1", is_read=False, created_at=now - timedelta(minutes=5))
    db.add(ev1)
    db.commit()

    # 1. Check unread count
    res = client.get("/api/alerts/unread-count")
    assert res.status_code == 200
    assert res.json()["unread_count"] == 1

    # 2. Mark event as read
    res = client.patch(f"/api/alerts/events/{ev1.id}/read")
    assert res.status_code == 200
    assert res.json()["is_read"] is True

    # Check unread count again
    res = client.get("/api/alerts/unread-count")
    assert res.status_code == 200
    assert res.json()["unread_count"] == 0

    # 3. Mark all read
    snap2 = ProductSnapshot(product_id=p.id, captured_at=now, sold_count=200)
    db.add(snap2)
    db.commit()
    ev2 = AlertEvent(rule_id=rule.id, product_id=p.id, triggering_snapshot_id=snap2.id,
                     rule_type="sales_velocity_above", threshold=50.0, actual_value=70.0,
                     message="Msg 2", is_read=False, created_at=now)
    db.add(ev2)
    db.commit()

    assert client.get("/api/alerts/unread-count").json()["unread_count"] == 1
    res = client.post("/api/alerts/events/mark-all-read")
    assert res.status_code == 200
    assert res.json()["marked_read_count"] == 1
    assert client.get("/api/alerts/unread-count").json()["unread_count"] == 0
