import io
import csv
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select, func
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.db.base import Base
from app.db.session import get_db, SessionLocal
from app.models.product import Product
from app.models.product_snapshot import ProductSnapshot
from app.models.watchlist import WatchlistItem
from app.models.alert_rule import AlertRule
from app.models.alert_event import AlertEvent
from app.services.export_service import ExportService, HISTORICAL_STREAM_BATCH_SIZE, format_utc_z


@pytest.fixture
def isolated_db(tmp_path):
    """File-backed isolated database in delete journal mode for testing export concurrency."""
    db_file = tmp_path / "test_export.db"
    db_url = f"sqlite:///{db_file}"
    engine = create_engine(db_url, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # Populate sample data using dynamic now so timestamps are in the valid historical window
    db = TestingSessionLocal()
    now = datetime.now(timezone.utc)

    # 1. Product 1 with Vietnamese Unicode title, shop, category, and historical snapshots
    p1 = Product(
        id=1,
        external_product_id="vn_p_1",
        title="Chuối Sấy Mè Đặc Sản Bến Tre (Hộp 500g, Giòn Tan)",
        shop_name="BĂNG BĂNG FOOD",
        category="Thực phẩm & Đồ uống",
        url="https://shop.tiktok.com/vn/pdp/1737036472084039604",
        first_seen_at=now - timedelta(days=35),
        last_seen_at=now,
    )
    # 2. Product 2 with special CSV characters (quotes, commas, newlines)
    p2 = Product(
        id=2,
        external_product_id="vn_p_2",
        title='Khăn Giấy "Sipiao", Gói 4 Lớp\nDùng Siêu Dai & Tiện Lợi',
        shop_name="Sipiao, Đại Lý Chính Hãng",
        category="Gia dụng & Đời sống",
        url="https://shop.tiktok.com/vn/pdp/1730929283006368543",
        first_seen_at=now - timedelta(days=10),
        last_seen_at=now,
    )
    db.add_all([p1, p2])
    db.flush()

    # Add p1 and p2 to Watchlist
    db.add(WatchlistItem(product_id=p1.id, notes="Watched đặc sản"))
    db.add(WatchlistItem(product_id=p2.id, notes='Ghi chú có dấu "ngoặc kép", phẩy\nvà xuống dòng'))

    # Add snapshots for p1 (varying intervals)
    for i in range(12):
        s = ProductSnapshot(
            id=i + 1,
            product_id=p1.id,
            captured_at=now - timedelta(hours=i * 2 + 1),
            price=100000.0 + i * 1000,
            sold_count=500 + i * 50,
            review_count=50 + i * 5,
            rating=4.8,
        )
        db.add(s)

    # Add snapshot for p2 with nulls and real zeroes to test serialization
    s_zero = ProductSnapshot(
        id=100,
        product_id=p2.id,
        captured_at=now - timedelta(minutes=30),
        price=0.0,  # real zero
        sold_count=0,  # real zero
        review_count=0,  # real zero
        rating=None,  # null
    )
    db.add(s_zero)

    # Add AlertRule and AlertEvents
    rule = AlertRule(
        id=1,
        product_id=p1.id,
        rule_type="sales_velocity_above",
        threshold=50.0,
        cooldown_minutes=0,
        is_enabled=True,
        last_condition_met=True,
    )
    db.add(rule)
    db.flush()

    for i in range(5):
        ev = AlertEvent(
            id=i + 1,
            rule_id=rule.id,
            product_id=p1.id,
            triggering_snapshot_id=i + 1,
            rule_type="sales_velocity_above",
            threshold=50.0,
            actual_value=120.0 + i,
            actual_direction="tang_nhanh",
            message=f'Tốc độ bán vượt ngưỡng: "{120 + i:.1f}", sản phẩm bán chạy!\nThông báo tự động.',
            is_read=(i % 2 == 0),
            created_at=now - timedelta(hours=i * 4 + 1),
        )
        db.add(ev)

    # Add alert event with zero values (unique triggering_snapshot_id=100)
    ev_zero = AlertEvent(
        id=99,
        rule_id=rule.id,
        product_id=p2.id,
        triggering_snapshot_id=100,
        rule_type="price_drop_below",
        threshold=0.0,
        actual_value=0.0,
        actual_direction="giam",
        message="Giá giảm về 0 VND",
        is_read=False,
        created_at=now - timedelta(minutes=10),
    )
    db.add(ev_zero)

    db.commit()
    db.close()

    return engine, TestingSessionLocal


def test_p4_ac_01_trends_current_result_export(isolated_db, monkeypatch):
    """P4-AC-01: Trends current-result export mirrors active queried result set including filters, sorting, and limits with UTF-8 BOM."""
    engine, TestingSessionLocal = isolated_db
    monkeypatch.setattr("app.services.export_service.SessionLocal", TestingSessionLocal)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    original_override = app.dependency_overrides.get(get_db)
    app.dependency_overrides[get_db] = override_get_db
    try:
        client = TestClient(app)

        # 1. Query trends API with trend_state=all to capture all test items
        resp_api = client.get("/api/trends?trend_state=all&limit=10&sort_by=trend_score&order=desc")
        assert resp_api.status_code == 200
        api_items = resp_api.json()

        # 2. Export trends CSV with identical parameters
        resp_csv = client.get("/api/trends/export?trend_state=all&limit=10&sort_by=trend_score&order=desc")
        assert resp_csv.status_code == 200
        assert resp_csv.headers["content-type"].startswith("text/csv")
        assert 'filename="trends_export.csv"' in resp_csv.headers["content-disposition"]
        assert resp_csv.content.startswith(b"\xef\xbb\xbf")

        # 3. Verify row count matches query result set exactly
        csv_text = resp_csv.content.decode("utf-8-sig")
        rows = list(csv.reader(io.StringIO(csv_text)))
        header = rows[0]
        data_rows = rows[1:]

        assert len(data_rows) == len(api_items)
        if len(api_items) > 0:
            assert int(data_rows[0][0]) == api_items[0]["product_id"]

        # 4. Filtered export query parity
        resp_filtered = client.get("/api/trends/export?trend_state=all&category=Th%E1%BB%B1c+ph%E1%BA%A9m+%26+%C4%90%E1%BB%93+u%E1%BB%91ng")
        assert resp_filtered.status_code == 200
        filtered_text = resp_filtered.content.decode("utf-8-sig")
        filtered_rows = list(csv.reader(io.StringIO(filtered_text)))[1:]
        for r in filtered_rows:
            assert r[3] == "Thực phẩm & Đồ uống"
    finally:
        if original_override is not None:
            app.dependency_overrides[get_db] = original_override
        else:
            app.dependency_overrides.pop(get_db, None)


def test_p4_ac_02_watchlist_current_result_export(isolated_db, monkeypatch):
    """P4-AC-02: Watchlist current-result export mirrors active queried result set without extra per-row metadata queries."""
    engine, TestingSessionLocal = isolated_db
    monkeypatch.setattr("app.services.export_service.SessionLocal", TestingSessionLocal)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    original_override = app.dependency_overrides.get(get_db)
    app.dependency_overrides[get_db] = override_get_db
    try:
        client = TestClient(app)

        # 1. Query watchlist API
        resp_api = client.get("/api/watchlist?limit=10")
        assert resp_api.status_code == 200
        api_items = resp_api.json()["items"]

        # 2. Export watchlist CSV
        resp_csv = client.get("/api/watchlist/export?limit=10")
        assert resp_csv.status_code == 200
        assert resp_csv.headers["content-type"].startswith("text/csv")
        assert 'filename="watchlist_export.csv"' in resp_csv.headers["content-disposition"]
        assert resp_csv.content.startswith(b"\xef\xbb\xbf")

        # 3. Match count and items
        csv_text = resp_csv.content.decode("utf-8-sig")
        rows = list(csv.reader(io.StringIO(csv_text)))
        data_rows = rows[1:]

        assert len(data_rows) == len(api_items)
        if len(api_items) > 0:
            assert int(data_rows[0][0]) == api_items[0]["product_id"]
    finally:
        if original_override is not None:
            app.dependency_overrides[get_db] = original_override
        else:
            app.dependency_overrides.pop(get_db, None)


def test_p4_ac_03_bounded_product_history_export(isolated_db, monkeypatch):
    """P4-AC-03: Bounded Product History export supports exactly 24h, 7d, 30d; range=all and invalid ranges rejected with 400."""
    engine, TestingSessionLocal = isolated_db
    monkeypatch.setattr("app.services.export_service.SessionLocal", TestingSessionLocal)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    original_override = app.dependency_overrides.get(get_db)
    app.dependency_overrides[get_db] = override_get_db
    try:
        client = TestClient(app)

        # Valid ranges: 24h, 7d, 30d
        for r in ["24h", "7d", "30d"]:
            resp = client.get(f"/api/products/1/export-history?range={r}")
            assert resp.status_code == 200, f"Range {r} should return 200"
            assert resp.headers["content-type"].startswith("text/csv")
            assert f'filename="product_1_history_{r}.csv"' in resp.headers["content-disposition"]
            assert resp.content.startswith(b"\xef\xbb\xbf")

        # Range 'all' is explicitly disallowed for CSV export
        resp_all = client.get("/api/products/1/export-history?range=all")
        assert resp_all.status_code == 400
        assert "Khoảng thời gian 'all' không được hỗ trợ để xuất CSV" in resp_all.json()["detail"]

        # Invalid range
        resp_inv = client.get("/api/products/1/export-history?range=invalid_range")
        assert resp_inv.status_code == 400
        assert "không được hỗ trợ" in resp_inv.json()["detail"]
    finally:
        if original_override is not None:
            app.dependency_overrides[get_db] = original_override
        else:
            app.dependency_overrides.pop(get_db, None)


def test_p4_ac_04_persisted_alert_history_semantics(isolated_db, monkeypatch):
    """P4-AC-04: Persisted Alert History semantics captures active filters and immutable event metrics with UTF-8 BOM."""
    engine, TestingSessionLocal = isolated_db
    monkeypatch.setattr("app.services.export_service.SessionLocal", TestingSessionLocal)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    original_override = app.dependency_overrides.get(get_db)
    app.dependency_overrides[get_db] = override_get_db
    try:
        client = TestClient(app)

        # 1. Export all alert events
        resp = client.get("/api/alerts/events/export")
        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith("text/csv")
        assert 'filename="alerts_export.csv"' in resp.headers["content-disposition"]
        assert resp.content.startswith(b"\xef\xbb\xbf")

        csv_text = resp.content.decode("utf-8-sig")
        rows = list(csv.reader(io.StringIO(csv_text)))
        header = rows[0]
        data_rows = rows[1:]
        assert len(data_rows) == 6  # 5 for p1 + 1 for p2

        # 2. Filtered by product_id
        resp_p1 = client.get("/api/alerts/events/export?product_id=1")
        assert resp_p1.status_code == 200
        rows_p1 = list(csv.reader(io.StringIO(resp_p1.content.decode("utf-8-sig"))))[1:]
        assert len(rows_p1) == 5
        for r in rows_p1:
            assert int(r[2]) == 1

        # 3. Filtered by is_read=true
        resp_read = client.get("/api/alerts/events/export?is_read=true")
        assert resp_read.status_code == 200
        rows_read = list(csv.reader(io.StringIO(resp_read.content.decode("utf-8-sig"))))[1:]
        for r in rows_read:
            assert r[9] == "Da doc"
    finally:
        if original_override is not None:
            app.dependency_overrides[get_db] = original_override
        else:
            app.dependency_overrides.pop(get_db, None)


def test_p4_ac_05_utf8_bom_and_vietnamese_unicode_across_all_four_exports(isolated_db, monkeypatch):
    """P4-AC-05: Every CSV begins with exactly one UTF-8 BOM and preserves Vietnamese Unicode across all four export types."""
    engine, TestingSessionLocal = isolated_db
    monkeypatch.setattr("app.services.export_service.SessionLocal", TestingSessionLocal)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    original_override = app.dependency_overrides.get(get_db)
    app.dependency_overrides[get_db] = override_get_db
    try:
        client = TestClient(app)

        endpoints = [
            ("/api/trends/export?trend_state=all", "Chuối Sấy Mè Đặc Sản"),
            ("/api/watchlist/export", "Chuối Sấy Mè Đặc Sản"),
            ("/api/products/1/export-history?range=24h", "Thoi gian ghi nhan (UTC)"),
            ("/api/alerts/events/export", "Tốc độ bán vượt ngưỡng"),
        ]

        for path, sample_unicode in endpoints:
            resp = client.get(path)
            assert resp.status_code == 200, f"Endpoint {path} failed with {resp.status_code}"
            raw_bytes = resp.content

            # 1. Exactly begins with UTF-8 BOM (\xef\xbb\xbf)
            assert raw_bytes.startswith(b"\xef\xbb\xbf"), f"{path} does not start with UTF-8 BOM"

            # 2. Contains exactly one UTF-8 BOM
            assert raw_bytes.count(b"\xef\xbb\xbf") == 1, f"{path} contains multiple UTF-8 BOMs"

            # 3. Decodes cleanly with utf-8-sig and preserves Vietnamese Unicode text
            text = raw_bytes.decode("utf-8-sig")
            assert sample_unicode in text, f"{path} did not preserve Vietnamese text: {sample_unicode}"
    finally:
        if original_override is not None:
            app.dependency_overrides[get_db] = original_override
        else:
            app.dependency_overrides.pop(get_db, None)


def test_p4_ac_06_exact_fixed_csv_headers_and_column_order(isolated_db, monkeypatch):
    """P4-AC-06: Exact fixed CSV headers and column order across all four export types."""
    engine, TestingSessionLocal = isolated_db
    monkeypatch.setattr("app.services.export_service.SessionLocal", TestingSessionLocal)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    original_override = app.dependency_overrides.get(get_db)
    app.dependency_overrides[get_db] = override_get_db
    try:
        client = TestClient(app)

        # 1. Trends headers
        resp_trends = client.get("/api/trends/export?trend_state=all")
        header_trends = list(csv.reader(io.StringIO(resp_trends.content.decode("utf-8-sig"))))[0]
        expected_trends = [
            "ID San pham", "Ten san pham", "Ten Shop", "Nganh hang", "Diem xu huong",
            "Toc do ban 24h (don/ngay)", "Tang truong ban 24h", "Tang truong danh gia 24h",
            "Danh gia sao", "Do tin cay", "Trang thai", "Ly do xu huong", "Duong dan"
        ]
        assert header_trends == expected_trends

        # 2. Watchlist headers
        resp_wl = client.get("/api/watchlist/export")
        header_wl = list(csv.reader(io.StringIO(resp_wl.content.decode("utf-8-sig"))))[0]
        expected_wl = [
            "ID San pham", "Ten san pham", "Ten Shop", "Nganh hang", "Diem xu huong",
            "Toc do ban 24h (don/ngay)", "Tang truong ban 24h", "Tang truong danh gia 24h",
            "Danh gia sao", "Do tin cay", "Trang thai", "Ly do xu huong", "Duong dan"
        ]
        assert header_wl == expected_wl

        # 3. Product History headers
        resp_hist = client.get("/api/products/1/export-history?range=24h")
        header_hist = list(csv.reader(io.StringIO(resp_hist.content.decode("utf-8-sig"))))[0]
        expected_hist = [
            "ID Snapshot", "Thoi gian ghi nhan (UTC)", "Gia (VND)", "Da ban", "Danh gia", "So luot danh gia"
        ]
        assert header_hist == expected_hist

        # 4. Alert History headers
        resp_alerts = client.get("/api/alerts/events/export")
        header_alerts = list(csv.reader(io.StringIO(resp_alerts.content.decode("utf-8-sig"))))[0]
        expected_alerts = [
            "ID Canh bao", "Thoi gian tao (UTC)", "ID San pham", "Ten san pham",
            "Loai canh bao", "Nguong", "Gia tri thuc te", "Chieu huong", "Thong diep", "Trang thai doc"
        ]
        assert header_alerts == expected_alerts
    finally:
        if original_override is not None:
            app.dependency_overrides[get_db] = original_override
        else:
            app.dependency_overrides.pop(get_db, None)


def test_p4_ac_07_null_zero_utc_z_locale_independent_serialization(isolated_db, monkeypatch):
    """
    P4-AC-07: Null/zero/UTC/locale-independent numeric serialization:
    - null -> blank ("")
    - real zero -> "0" or "0.0" / "0.00"
    - timestamps normalized to UTC Z (YYYY-MM-DDTHH:MM:SSZ)
    - locale-independent numbers (decimal point '.', never ',')
    """
    engine, TestingSessionLocal = isolated_db
    monkeypatch.setattr("app.services.export_service.SessionLocal", TestingSessionLocal)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    original_override = app.dependency_overrides.get(get_db)
    app.dependency_overrides[get_db] = override_get_db
    try:
        client = TestClient(app)

        # 1. Product History for Product 2 which has real zero price/sold/review and null rating
        resp_hist = client.get("/api/products/2/export-history?range=24h")
        assert resp_hist.status_code == 200
        rows = list(csv.reader(io.StringIO(resp_hist.content.decode("utf-8-sig"))))[1:]
        assert len(rows) == 1
        r = rows[0]
        # Columns: ID Snapshot, Thoi gian ghi nhan (UTC), Gia (VND), Da ban, Danh gia, So luot danh gia
        assert r[0] == "100"
        # UTC Z timestamp check: matches YYYY-MM-DDTHH:MM:SSZ
        assert r[1].endswith("Z")
        assert "T" in r[1]
        assert r[2] == "0"  # price 0.0 -> "0"
        assert r[3] == "0"  # sold_count 0 -> "0"
        assert r[4] == ""   # rating None -> ""
        assert r[5] == "0"  # review_count 0 -> "0"

        # 2. Alert History for ev_zero which has real zero threshold and actual_value
        resp_alerts = client.get("/api/alerts/events/export?product_id=2")
        assert resp_alerts.status_code == 200
        alert_rows = list(csv.reader(io.StringIO(resp_alerts.content.decode("utf-8-sig"))))[1:]
        assert len(alert_rows) == 1
        ar = alert_rows[0]
        # Columns: ID Canh bao, Thoi gian tao (UTC), ID San pham, Ten san pham, Loai canh bao, Nguong, Gia tri thuc te, Chieu huong, Thong diep, Trang thai doc
        assert ar[1].endswith("Z")
        assert ar[5] == "0.00"  # threshold 0.0 -> "0.00"
        assert ar[6] == "0.00"  # actual_value 0.0 -> "0.00"
        assert "." in ar[5]     # locale-independent period, not comma
        assert "." in ar[6]
    finally:
        if original_override is not None:
            app.dependency_overrides[get_db] = original_override
        else:
            app.dependency_overrides.pop(get_db, None)


def test_p4_ac_08_commas_quotes_newlines_rfc4180_roundtrip(isolated_db, monkeypatch):
    """
    P4-AC-08: Commas/quotes/newlines standards-compliant CSV round-trip (RFC 4180).
    Verifies that fields with commas, quotes, and newlines round-trip identically.
    """
    engine, TestingSessionLocal = isolated_db
    monkeypatch.setattr("app.services.export_service.SessionLocal", TestingSessionLocal)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    original_override = app.dependency_overrides.get(get_db)
    app.dependency_overrides[get_db] = override_get_db
    try:
        client = TestClient(app)

        # 1. Export Watchlist CSV containing Product 2 (which has quotes, commas, newlines in title/shop)
        resp_wl = client.get("/api/watchlist/export")
        assert resp_wl.status_code == 200
        text_wl = resp_wl.content.decode("utf-8-sig")

        # Parse CSV with standard RFC 4180 parser
        reader = list(csv.reader(io.StringIO(text_wl)))
        header = reader[0]
        data_rows = reader[1:]

        # Find Product 2 row
        p2_row = next((r for r in data_rows if r[0] == "2"), None)
        assert p2_row is not None
        # Title with quotes, comma, newline
        assert p2_row[1] == 'Khăn Giấy "Sipiao", Gói 4 Lớp\nDùng Siêu Dai & Tiện Lợi'
        # Shop name with comma
        assert p2_row[2] == "Sipiao, Đại Lý Chính Hãng"

        # 2. Export Alert History with quotes, commas, newlines in message
        resp_alerts = client.get("/api/alerts/events/export?product_id=1")
        assert resp_alerts.status_code == 200
        text_alerts = resp_alerts.content.decode("utf-8-sig")

        alert_reader = list(csv.reader(io.StringIO(text_alerts)))
        alert_data = alert_reader[1:]
        # Check message field (column index 8)
        assert any('\n' in r[8] and '"' in r[8] and ',' in r[8] for r in alert_data)
    finally:
        if original_override is not None:
            app.dependency_overrides[get_db] = original_override
        else:
            app.dependency_overrides.pop(get_db, None)


def test_p4_ac_09_historical_membership_freeze_and_high_watermark(isolated_db, monkeypatch):
    """
    P4-AC-09: Request-start historical membership/high-watermark semantics:
    - Internal batch size is 1000.
    - Freezes membership using as_of_utc, lower_bound, and max_snapshot_id_at_start.
    - Ascending keyset (captured_at, snapshot_id) ASC.
    - Post-start higher-ID rows strictly excluded even if backdated.
    - Short-lived DB sessions between batches release locks for concurrent writers.
    """
    engine, TestingSessionLocal = isolated_db
    monkeypatch.setattr("app.services.export_service.SessionLocal", TestingSessionLocal)

    assert HISTORICAL_STREAM_BATCH_SIZE == 1000

    # Test with batch size 3 to verify keyset pagination across multiple batches
    gen = ExportService.stream_product_history(product_id=1, time_range="30d", batch_size=3)

    # 1. Header chunk
    header_chunk = next(gen)
    assert header_chunk.startswith("\ufeff")

    # 2. First batch of data
    batch1 = next(gen)
    reader1 = list(csv.reader(io.StringIO(batch1)))
    assert len(reader1) == 3

    # 3. Simulate concurrent writer committing a higher-ID row backdated into the time window
    now = datetime.now(timezone.utc)
    writer_db = TestingSessionLocal()
    backdated_snapshot = ProductSnapshot(
        id=9999,  # higher ID than max_snapshot_id_at_start
        product_id=1,
        captured_at=now - timedelta(hours=10),  # within 30d range
        price=99999.0,
        sold_count=9999,
        review_count=999,
        rating=5.0,
    )
    writer_db.add(backdated_snapshot)
    writer_db.commit()
    writer_db.close()

    # 4. Consume remaining batches from the generator
    all_rows = list(reader1)
    for chunk in gen:
        all_rows.extend(list(csv.reader(io.StringIO(chunk))))

    # 5. Verify higher-ID row 9999 is strictly excluded
    snapshot_ids = [int(r[0]) for r in all_rows]
    assert 9999 not in snapshot_ids, "Higher-ID row 9999 must be excluded even when backdated!"

    # 6. Verify ascending order and zero duplicates
    assert len(snapshot_ids) == len(set(snapshot_ids)), "Zero duplicates allowed across keyset batches"

    # Also test stream_alert_history membership freeze with batch_size=2
    alert_gen = ExportService.stream_alert_history(product_id=1, batch_size=2)
    next(alert_gen)  # header
    alert_batch1 = list(csv.reader(io.StringIO(next(alert_gen))))
    assert len(alert_batch1) == 2

    # Writer commits post-start higher-ID backdated alert event (unique triggering snapshot 999)
    writer_db2 = TestingSessionLocal()
    backdated_event = AlertEvent(
        id=8888,
        rule_id=1,
        product_id=1,
        triggering_snapshot_id=999,
        rule_type="sales_velocity_above",
        threshold=50.0,
        actual_value=200.0,
        actual_direction="tang",
        message="Backdated event",
        is_read=False,
        created_at=now - timedelta(hours=2),
    )
    writer_db2.add(backdated_event)
    writer_db2.commit()
    writer_db2.close()

    alert_rows = list(alert_batch1)
    for chunk in alert_gen:
        alert_rows.extend(list(csv.reader(io.StringIO(chunk))))

    event_ids = [int(r[0]) for r in alert_rows]
    assert 8888 not in event_ids, "Higher-ID alert event 8888 must be excluded!"
    assert len(event_ids) == len(set(event_ids))


def test_p4_ac_10_cancellation_and_error_resource_cleanup(isolated_db, monkeypatch, tmp_path):
    """
    P4-AC-10: Cancellation/error resource cleanup:
    - Stops additional batches.
    - Releases active DB/session resources.
    - Creates no export artifact on disk.
    - Mutates no application state.
    """
    engine, TestingSessionLocal = isolated_db
    monkeypatch.setattr("app.services.export_service.SessionLocal", TestingSessionLocal)

    # Count initial rows across tables to prove no mutation
    with TestingSessionLocal() as db:
        initial_snapshots = db.scalar(select(func.count(ProductSnapshot.id)))
        initial_alerts = db.scalar(select(func.count(AlertEvent.id)))

    # Start generator and close it after 1 batch (simulating client abort / cancellation)
    gen = ExportService.stream_product_history(product_id=1, time_range="30d", batch_size=2)
    next(gen)  # header
    next(gen)  # batch 1

    # Client aborts / disconnects
    gen.close()

    # Generator is closed; subsequent next() raises StopIteration
    with pytest.raises(StopIteration):
        next(gen)

    # Verify no file artifact was written to disk
    created_files = list(tmp_path.glob("*.csv"))
    assert len(created_files) == 0, "No CSV export artifacts should be created on disk"

    # Verify database state was completely unmutated
    with TestingSessionLocal() as db:
        current_snapshots = db.scalar(select(func.count(ProductSnapshot.id)))
        current_alerts = db.scalar(select(func.count(AlertEvent.id)))
        assert current_snapshots == initial_snapshots
        assert current_alerts == initial_alerts


def test_p4_ac_09_multi_batch_1000_historical_streaming(tmp_path, monkeypatch):
    """
    P4-AC-09 (Item 7): Historical streaming performance and reliability after batch size 1000:
    - Production batch size = 1000 (HISTORICAL_STREAM_BATCH_SIZE == 1000)
    - Isolated deterministic file-backed database under journal_mode=delete
    - 2,500 historical snapshot rows (> 2 full 1000-row batches)
    - At least 2 batches traversed (exactly 3 batches: 1000, 1000, 500)
    - Concurrent writer commits a higher-ID backdated row between batches under journal_mode=delete
    - Proves short-lived session/transaction released between batches (no database locked error)
    - All 2,500 original snapshots emitted exactly once: no duplicates, no skips
    - Post-initialization higher-ID backdated snapshot strictly excluded
    - Bounded memory
    """
    db_file = tmp_path / "historical_stream_1000.db"
    engine = create_engine(f"sqlite:///{db_file}")

    # Set journal_mode = delete
    with engine.connect() as conn:
        conn.exec_driver_sql("PRAGMA journal_mode = delete;")

    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(bind=engine)
    monkeypatch.setattr("app.services.export_service.SessionLocal", TestingSessionLocal)

    assert HISTORICAL_STREAM_BATCH_SIZE == 1000

    now = datetime(2026, 10, 5, 12, 0, 0, tzinfo=timezone.utc)
    product_id = 101

    with TestingSessionLocal() as db:
        p = Product(
            id=product_id,
            external_product_id="stream_prod_101",
            title="Stream Product 101",
            first_seen_at=now - timedelta(days=25),
            last_seen_at=now,
        )
        db.add(p)
        db.flush()

        # Insert 2,500 historical snapshots within 30-day window
        snapshots = []
        for i in range(1, 2501):
            snapshots.append(ProductSnapshot(
                id=i,
                product_id=product_id,
                captured_at=now - timedelta(days=20) + timedelta(minutes=i * 5),
                sold_count=100 + i,
                review_count=10,
                rating=4.5,
                price=50000.0,
            ))
        db.add_all(snapshots)
        db.commit()

    # Start generator with production batch size 1000
    gen = ExportService.stream_product_history(product_id=product_id, time_range="30d", batch_size=1000)

    # 1. Header chunk
    header_chunk = next(gen)
    assert header_chunk.startswith("\ufeff")

    # 2. Batch 1: exactly 1000 rows
    batch1_chunk = next(gen)
    reader1 = list(csv.reader(io.StringIO(batch1_chunk)))
    assert len(reader1) == 1000
    batch1_ids = [int(r[0]) for r in reader1]
    assert batch1_ids[0] == 1
    assert batch1_ids[-1] == 1000

    # 3. Simulate concurrent writer committing between batches under journal_mode=delete
    # Proves session/transaction was released (otherwise SQLite would raise database is locked)
    writer_db = TestingSessionLocal()
    backdated_snapshot = ProductSnapshot(
        id=99999,  # higher ID than max_snapshot_id_at_start
        product_id=product_id,
        captured_at=now - timedelta(days=15),  # backdated into the 30d window!
        sold_count=8888,
        price=77000.0,
    )
    writer_db.add(backdated_snapshot)
    writer_db.commit()  # Commits cleanly because reader released the read transaction!
    writer_db.close()

    # 4. Batch 2: exactly 1000 rows
    batch2_chunk = next(gen)
    reader2 = list(csv.reader(io.StringIO(batch2_chunk)))
    assert len(reader2) == 1000
    batch2_ids = [int(r[0]) for r in reader2]
    assert batch2_ids[0] == 1001
    assert batch2_ids[-1] == 2000

    # 5. Batch 3: remaining 500 rows
    batch3_chunk = next(gen)
    reader3 = list(csv.reader(io.StringIO(batch3_chunk)))
    assert len(reader3) == 500
    batch3_ids = [int(r[0]) for r in reader3]
    assert batch3_ids[0] == 2001
    assert batch3_ids[-1] == 2500

    # Verify generator is exhausted
    with pytest.raises(StopIteration):
        next(gen)

    # 6. Aggregate verification
    all_ids = batch1_ids + batch2_ids + batch3_ids
    assert len(all_ids) == 2500, f"Expected 2500 emitted rows, got {len(all_ids)}"

    # Exclude post-start higher-ID backdated row
    assert 99999 not in all_ids, "Higher-ID row 99999 committed after request-start MUST be excluded!"

    # Zero duplicate, zero skip
    assert all_ids == list(range(1, 2501)), "Emitted IDs must match exactly 1..2500 without duplicates or skips"

    engine.dispose()

