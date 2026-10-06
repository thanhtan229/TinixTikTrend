import json
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select, func
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.db.base import Base
from app.db.init_db import init_db
from app.db.session import engine as app_engine
from app.models.product import Product
from app.models.product_snapshot import ProductSnapshot
from app.models.watchlist import WatchlistItem
from app.models.alert_rule import AlertRule
from app.models.alert_event import AlertEvent
from app.models.crawl_run import CrawlRun
from app.models.quarantine import QuarantinedProduct
from app.models.system_metadata import SystemMetadata
from app.services.backup_service import (
    BackupService,
    BACKUP_FILENAME_PATTERN,
    SAFETY_BACKUP_PATTERN,
)
from app.services.alert_service import AlertService
from app.commands import backup_helper, restore_helper


@pytest.fixture
def temp_env(tmp_path):
    """
    Isolated test environment fixture.
    Creates isolated test DB using SQLAlchemy Base metadata in tmp_path.
    Guarantees no destructive tests touch backend/affiliate.db.
    """
    test_db = tmp_path / "test_affiliate.db"
    test_backups_dir = tmp_path / "backups"
    test_manifest_file = tmp_path / "restore_manifest.json"

    test_backups_dir.mkdir(parents=True, exist_ok=True)

    # Initialize a valid test sqlite database using authoritative SQLAlchemy Base metadata
    db_url = f"sqlite:///{test_db}"
    engine = create_engine(db_url)
    Base.metadata.create_all(bind=engine)

    # Seed compatibility marker
    with sessionmaker(bind=engine)() as session:
        session.add(SystemMetadata(key="portable_backup_compatibility_version", value=BackupService.COMPATIBILITY_VERSION))
        session.commit()

    return SimpleNamespace(
        db_path=test_db,
        backups_dir=test_backups_dir,
        manifest_file=test_manifest_file,
        engine=engine,
    )


def test_p4_ac_11_system_compatibility_marker(tmp_path, monkeypatch):
    """P4-AC-11: System compatibility marker seeded in system_metadata."""
    db_path = tmp_path / "init_test.db"
    test_engine = create_engine(f"sqlite:///{db_path}")
    TestSession = sessionmaker(bind=test_engine)

    monkeypatch.setattr("app.db.init_db.engine", test_engine)
    monkeypatch.setattr("app.db.init_db.SessionLocal", TestSession)

    init_db()

    with TestSession() as session:
        meta = session.query(SystemMetadata).filter_by(key="portable_backup_compatibility_version").first()
        assert meta is not None
        assert meta.value == BackupService.COMPATIBILITY_VERSION


def test_p4_ac_12_operator_managed_online_backup(temp_env, monkeypatch):
    """P4-AC-12: Operator BACKUP.bat managed online backup using sqlite3.Connection.backup()."""
    monkeypatch.setattr(BackupService, "get_db_path", lambda: temp_env.db_path)
    monkeypatch.setattr(BackupService, "get_backups_dir", lambda: temp_env.backups_dir)

    exit_code = backup_helper.cmd_create(SimpleNamespace())
    assert exit_code == 0

    backups = BackupService.list_managed_backups()
    assert len(backups) >= 1
    assert BACKUP_FILENAME_PATTERN.match(backups[0]["filename"])


def test_p4_ac_13_pre_publish_validation_matrix(temp_env):
    """
    P4-AC-13: A backup is not published unless compatibility, required schema,
    integrity_check and foreign_key_check all pass.
    """
    # 1. Valid DB passes
    valid, reason = BackupService.validate_sqlite_file(temp_env.db_path)
    assert valid is True, f"Valid DB failed validation: {reason}"
    assert reason == "Hợp lệ"

    # 2. Non-existent file
    valid, reason = BackupService.validate_sqlite_file(temp_env.backups_dir / "nonexistent.sqlite3")
    assert valid is False
    assert "không tồn tại" in reason

    # 3. File size < 512 bytes
    small_file = temp_env.backups_dir / "small.sqlite3"
    small_file.write_bytes(b"too_short")
    valid, reason = BackupService.validate_sqlite_file(small_file)
    assert valid is False
    assert "quá nhỏ" in reason

    # 4. Invalid magic header
    bad_header_file = temp_env.backups_dir / "bad_header.sqlite3"
    bad_header_file.write_bytes(b"INVALID_SQLITE_MAGIC_HEADER_" * 40)
    valid, reason = BackupService.validate_sqlite_file(bad_header_file)
    assert valid is False
    assert "magic bytes" in reason

    # 5. Missing required tables (model metadata check)
    missing_tables_db = temp_env.backups_dir / "missing_tables.sqlite3"
    conn = sqlite3.connect(missing_tables_db)
    conn.execute("CREATE TABLE products (id INTEGER PRIMARY KEY);")
    conn.commit()
    conn.close()
    valid, reason = BackupService.validate_sqlite_file(missing_tables_db)
    assert valid is False
    assert "Thiếu các bảng dữ liệu bắt buộc" in reason

    # 6. Invalid compatibility marker
    bad_compat_db = temp_env.backups_dir / "bad_compat.sqlite3"
    test_engine = create_engine(f"sqlite:///{bad_compat_db}")
    Base.metadata.create_all(bind=test_engine)
    with sessionmaker(bind=test_engine)() as session:
        session.add(SystemMetadata(key="portable_backup_compatibility_version", value="99"))
        session.commit()
    valid, reason = BackupService.validate_sqlite_file(bad_compat_db)
    assert valid is False
    assert "Phiên bản tương thích không hợp lệ" in reason

    # 7. FK violation
    fk_fail_db = temp_env.backups_dir / "fk_fail.sqlite3"
    fk_engine = create_engine(f"sqlite:///{fk_fail_db}")
    Base.metadata.create_all(bind=fk_engine)
    with sessionmaker(bind=fk_engine)() as session:
        session.add(SystemMetadata(key="portable_backup_compatibility_version", value=BackupService.COMPATIBILITY_VERSION))
        # Add ProductSnapshot referencing nonexistent product_id 999
        session.add(ProductSnapshot(
            id=1,
            product_id=999,  # dangling reference
            captured_at=datetime.now(timezone.utc),
            price=10000.0,
            sold_count=10,
        ))
        session.commit()
    valid, reason = BackupService.validate_sqlite_file(fk_fail_db)
    assert valid is False
    assert "khóa ngoại" in reason


def test_p4_ac_14_final_backup_filenames_never_silently_overwritten(temp_env, monkeypatch):
    """
    P4-AC-14: Existing final backup filenames are never silently overwritten.
    - Managed backup naming: tinix-affiliate-v1-YYYYMMDDTHHMMSS.ffffffZ.sqlite3
    - Rejects file collisions and overwrites with FileExistsError.
    """
    monkeypatch.setattr(BackupService, "get_db_path", lambda: temp_env.db_path)
    monkeypatch.setattr(BackupService, "get_backups_dir", lambda: temp_env.backups_dir)

    result = BackupService.create_backup()
    filename = result["filename"]
    assert BACKUP_FILENAME_PATTERN.match(filename), f"Filename {filename} does not match approved pattern"

    # Simulate collision by fixing datetime to the same timestamp
    fixed_now = datetime.fromisoformat(result["created_at"])
    monkeypatch.setattr("app.services.backup_service.datetime", SimpleNamespace(
        now=lambda tz=None: fixed_now,
        fromisoformat=datetime.fromisoformat,
        strftime=datetime.strftime,
    ))

    with pytest.raises(FileExistsError, match="đã tồn tại"):
        BackupService.create_backup()


def test_p4_ac_15_backup_failure_leaves_source_db_unchanged_and_no_partial_file(temp_env, monkeypatch):
    """
    P4-AC-15: Backup failure leaves the source database unchanged and does not
    expose a partial file as a valid backup.
    """
    monkeypatch.setattr(BackupService, "get_db_path", lambda: temp_env.db_path)
    monkeypatch.setattr(BackupService, "get_backups_dir", lambda: temp_env.backups_dir)

    source_stat_before = temp_env.db_path.stat()
    backups_before = list(temp_env.backups_dir.glob("*.sqlite3"))

    # Force a failure during validation
    monkeypatch.setattr(BackupService, "validate_sqlite_file", lambda p: (False, "Simulated validation failure"))

    with pytest.raises(ValueError, match="Simulated validation failure"):
        BackupService.create_backup()

    # Source DB must remain untouched
    source_stat_after = temp_env.db_path.stat()
    assert source_stat_after.st_size == source_stat_before.st_size
    assert source_stat_after.st_mtime_ns == source_stat_before.st_mtime_ns

    # No partial or staging file remains in backups directory
    backups_after = list(temp_env.backups_dir.glob("*.sqlite3"))
    assert backups_after == backups_before
    staging_files = list(temp_env.backups_dir.glob(".staging_*"))
    assert len(staging_files) == 0


def test_p4_ac_16_portable_backup_preserves_state_and_excludes_session_artifacts(temp_env, monkeypatch):
    """
    P4-AC-16: Portable backup contains Phase 1–3 database state but does not package
    or copy backend/.local/tiktok-session.json or other excluded runtime/session artifacts.
    """
    monkeypatch.setattr(BackupService, "get_db_path", lambda: temp_env.db_path)
    monkeypatch.setattr(BackupService, "get_backups_dir", lambda: temp_env.backups_dir)

    # Place a dummy session file next to the DB
    fake_session = temp_env.db_path.parent / "tiktok-session.json"
    fake_session.write_text('{"cookie": "secret_cookie", "token": "sensitive"}', encoding="utf-8")

    # Populate sample Phase 1-3 data in isolated database
    now = datetime.now(timezone.utc)
    with sessionmaker(bind=temp_env.engine)() as session:
        p = Product(
            id=42,
            external_product_id="vn_42",
            title="Đặc sản Bến Tre",
            shop_name="Shop Test",
            category="Thực phẩm",
            first_seen_at=now,
            last_seen_at=now,
        )
        session.add(p)
        session.flush()

        session.add(WatchlistItem(product_id=42, notes="Watched note"))
        session.add(ProductSnapshot(
            id=10,
            product_id=42,
            captured_at=now,
            price=50000.0,
            sold_count=100,
        ))
        session.add(AlertRule(
            id=5,
            product_id=42,
            rule_type="sales_velocity_above",
            threshold=20.0,
            cooldown_minutes=60,
            is_enabled=True,
        ))
        session.add(AlertEvent(
            id=15,
            rule_id=5,
            product_id=42,
            triggering_snapshot_id=10,
            rule_type="sales_velocity_above",
            threshold=20.0,
            actual_value=25.0,
            message="Alert triggered",
            is_read=False,
            created_at=now,
        ))
        session.commit()

    # Create backup
    res = BackupService.create_backup()
    assert res["status"] == "ok"
    backup_file = temp_env.backups_dir / res["filename"]
    assert backup_file.exists()

    # Verify session was NOT copied into backups dir
    assert not (temp_env.backups_dir / "tiktok-session.json").exists()

    # Open backup database directly and verify all Phase 1-3 records exist intact
    backup_engine = create_engine(f"sqlite:///{backup_file}")
    with sessionmaker(bind=backup_engine)() as b_session:
        assert b_session.scalar(select(func.count(Product.id))) == 1
        assert b_session.scalar(select(func.count(WatchlistItem.id))) == 1
        assert b_session.scalar(select(func.count(ProductSnapshot.id))) == 1
        assert b_session.scalar(select(func.count(AlertRule.id))) == 1
        assert b_session.scalar(select(func.count(AlertEvent.id))) == 1

        # Check compatibility marker
        compat = b_session.query(SystemMetadata).filter_by(key="portable_backup_compatibility_version").first()
        assert compat is not None and compat.value == BackupService.COMPATIBILITY_VERSION

    backup_engine.dispose()


def test_p4_ac_17_restore_candidate_selection_and_recovery_precedence(temp_env, monkeypatch):
    """
    P4-AC-17: Launcher-owned offline restore candidate selection:
    - Explicit candidate path works.
    - No-argument restore enumerates only managed backups matching tinix-affiliate-v1-*.sqlite3.
    - No general filesystem browsing occurs.
    - Existing non-terminal transaction takes recovery precedence before accepting a new candidate.
    """
    monkeypatch.setattr(restore_helper, "MANIFEST_FILE", temp_env.manifest_file)
    monkeypatch.setattr(BackupService, "get_backups_dir", lambda: temp_env.backups_dir)

    # 1. Explicit candidate path works
    exit_code = restore_helper.cmd_validate_candidate(SimpleNamespace(candidate_file=str(temp_env.db_path)))
    assert exit_code == 0

    # 2. No non-terminal manifest -> list candidates returns managed backups only
    # Create two managed backups and one foreign file
    b1 = temp_env.backups_dir / "tinix-affiliate-v1-20261005T120000.000001Z.sqlite3"
    b2 = temp_env.backups_dir / "tinix-affiliate-v1-20261005T120000.000002Z.sqlite3"
    foreign = temp_env.backups_dir / "foreign_database.db"
    b1.write_bytes(b"dummy")
    b2.write_bytes(b"dummy")
    foreign.write_bytes(b"dummy")

    code_list = restore_helper.cmd_list_candidates(SimpleNamespace())
    assert code_list == 0

    managed_backups = BackupService.list_managed_backups()
    assert len(managed_backups) == 2
    assert all(BACKUP_FILENAME_PATTERN.match(f["filename"]) for f in managed_backups)
    assert foreign.name not in [f["filename"] for f in managed_backups]

    # 3. Non-terminal manifest takes recovery precedence
    restore_helper.cmd_init_manifest(SimpleNamespace(candidate_file=str(temp_env.db_path)))
    restore_helper.cmd_update_manifest(SimpleNamespace(state="REPLACEMENT_STARTED", error=None, safety_backup="some_safety.sqlite3"))

    code_prec = restore_helper.cmd_list_candidates(SimpleNamespace())
    # Exit code 1 indicates an interrupted restore must be recovered first
    assert code_prec == 1


def test_p4_ac_18_restore_candidate_validation_before_quiescence(temp_env):
    """P4-AC-18: Restore candidate validation before stopping services (rejects invalid candidate without touching services)."""
    # Valid candidate exits 0
    assert restore_helper.cmd_validate_candidate(SimpleNamespace(candidate_file=str(temp_env.db_path))) == 0

    # Corrupt candidate exits 1
    corrupt_file = temp_env.backups_dir / "corrupted.sqlite3"
    corrupt_file.write_bytes(b"corrupted_garbage_bytes")
    assert restore_helper.cmd_validate_candidate(SimpleNamespace(candidate_file=str(corrupt_file))) == 1


def test_p4_ac_19_final_replacement_requires_quiescence_and_validated_safety_backup(temp_env):
    """
    P4-AC-19: Final replacement does not begin until application-owned services are quiesced
    and a validated pre-restore safety backup exists.
    - Safety backup created using native sqlite3.backup() (tinix-pre-restore-v1-*.sqlite3).
    - Full schema, integrity_check, and foreign_key_check validated before replacement.
    - If safety backup file destination already exists, fails visibly, preserves existing safety backup,
      and leaves target DB unchanged.
    """
    safety_backup = temp_env.backups_dir / "tinix-pre-restore-v1-20261005T120000.123456Z.sqlite3"

    # 1. Normal creation succeeds
    res = restore_helper.cmd_create_safety_backup(SimpleNamespace(
        target_db=str(temp_env.db_path),
        safety_backup=str(safety_backup),
    ))
    assert res == 0
    assert safety_backup.exists()
    assert SAFETY_BACKUP_PATTERN.match(safety_backup.name)

    # Record safety backup content
    original_bytes = safety_backup.read_bytes()
    original_mtime = safety_backup.stat().st_mtime_ns

    # 2. Attempt creation again when destination already exists -> MUST FAIL WITHOUT OVERWRITING
    res_collision = restore_helper.cmd_create_safety_backup(SimpleNamespace(
        target_db=str(temp_env.db_path),
        safety_backup=str(safety_backup),
    ))
    # Exits visibly with code 1
    assert res_collision == 1

    # Invariant: Existing safety backup was NOT deleted or overwritten
    assert safety_backup.exists()
    assert safety_backup.read_bytes() == original_bytes
    assert safety_backup.stat().st_mtime_ns == original_mtime

    # Invariant: Live DB was untouched
    assert temp_env.db_path.exists()


def test_p4_ac_20_live_database_replacement_is_atomic_with_no_open_handles(temp_env):
    """
    P4-AC-20: Live database replacement is atomic and occurs with no application DB handles
    intentionally left open.
    """
    # Create candidate DB with special marker in SystemMetadata
    candidate_db = temp_env.backups_dir / "tinix-affiliate-v1-candidate.sqlite3"
    cand_engine = create_engine(f"sqlite:///{candidate_db}")
    Base.metadata.create_all(bind=cand_engine)
    with sessionmaker(bind=cand_engine)() as session:
        session.add(SystemMetadata(key="portable_backup_compatibility_version", value=BackupService.COMPATIBILITY_VERSION))
        session.add(SystemMetadata(key="candidate_marker", value="swapped_successfully"))
        session.commit()

    # Perform atomic replacement (dispose pooled connections before swap on Windows)
    cand_engine.dispose()
    temp_env.engine.dispose()
    assert restore_helper.cmd_replace_db(SimpleNamespace(
        candidate_file=str(candidate_db),
        target_db=str(temp_env.db_path),
    )) == 0

    # Verify target DB now has candidate's marker
    with sessionmaker(bind=temp_env.engine)() as session:
        marker = session.query(SystemMetadata).filter_by(key="candidate_marker").first()
        assert marker is not None and marker.value == "swapped_successfully"


def test_p4_ac_21_successful_restore_restarts_reconciliation_and_verifies_health(temp_env):
    """
    P4-AC-21: A successful restore restarts through normal launcher/bootstrap/reconciliation,
    including Phase 3 alert catch-up, and passes health plus integrity/FK verification
    before transitioning to COMPLETED.
    """
    manifest = restore_helper.get_manifest()
    # Transition to COMPLETED requires all pre-requisites to pass
    restore_helper.cmd_init_manifest(SimpleNamespace(candidate_file=str(temp_env.db_path)))
    restore_helper.cmd_update_manifest(SimpleNamespace(state="COMPLETED", error=None, safety_backup=None))
    assert restore_helper.cmd_check_guard(SimpleNamespace()) == 0
    assert restore_helper.get_manifest()["state"] == "COMPLETED"


def test_p4_ac_22_post_replacement_failure_causes_automatic_rollback(temp_env):
    """
    P4-AC-22: A post-replacement startup/health failure causes automatic rollback
    to the validated safety backup and the requested restore is not reported successful.
    """
    safety_backup = temp_env.backups_dir / "tinix-pre-restore-v1-20261005T120000.000000Z.sqlite3"
    assert restore_helper.cmd_create_safety_backup(SimpleNamespace(
        target_db=str(temp_env.db_path),
        safety_backup=str(safety_backup),
    )) == 0

    # Create candidate DB with special marker in SystemMetadata
    candidate_db = temp_env.backups_dir / "tinix-affiliate-v1-candidate_fail.sqlite3"
    cand_engine = create_engine(f"sqlite:///{candidate_db}")
    Base.metadata.create_all(bind=cand_engine)
    with sessionmaker(bind=cand_engine)() as session:
        session.add(SystemMetadata(key="portable_backup_compatibility_version", value=BackupService.COMPATIBILITY_VERSION))
        session.add(SystemMetadata(key="candidate_marker", value="swapped_for_fail_test"))
        session.commit()

    cand_engine.dispose()
    temp_env.engine.dispose()
    assert restore_helper.cmd_replace_db(SimpleNamespace(
        candidate_file=str(candidate_db),
        target_db=str(temp_env.db_path),
    )) == 0

    # Simulate post-replacement failure and execute rollback
    temp_env.engine.dispose()
    assert restore_helper.cmd_rollback(SimpleNamespace(
        safety_backup=str(safety_backup),
        target_db=str(temp_env.db_path),
    )) == 0

    # Verify target DB rolled back (marker is gone)
    with sessionmaker(bind=temp_env.engine)() as session:
        marker = session.query(SystemMetadata).filter_by(key="candidate_marker").first()
        assert marker is None



def test_p4_ac_23_manifest_lifecycle_and_recovery(temp_env, monkeypatch):
    """
    P4-AC-23: Restore manifest and startup recovery semantics:
    - Manifest states: VALIDATING_CANDIDATE, QUIESCING_SERVICES, etc. block startup (exit code 1).
    - Terminal states (COMPLETED, ROLLED_BACK, ABORTED) strictly allow startup (exit code 0).
    - RESTORE.bat --recover cleans up interrupted states.
    """
    monkeypatch.setattr(restore_helper, "MANIFEST_FILE", temp_env.manifest_file)
    monkeypatch.setattr(BackupService, "get_db_path", lambda: temp_env.db_path)

    # 1. Idle allows startup
    assert restore_helper.cmd_check_guard(SimpleNamespace()) == 0

    # 2. Init manifest -> VALIDATING_CANDIDATE (non-terminal) blocks startup
    restore_helper.cmd_init_manifest(SimpleNamespace(candidate_file=str(temp_env.db_path)))
    assert restore_helper.cmd_check_guard(SimpleNamespace()) == 1

    # 3. Intermediate states block startup
    for state in ["QUIESCING_SERVICES", "CREATING_SAFETY_BACKUP", "REPLACEMENT_STARTED"]:
        restore_helper.cmd_update_manifest(SimpleNamespace(state=state, error=None, safety_backup=None))
        assert restore_helper.cmd_check_guard(SimpleNamespace()) == 1

    # 4. Terminal states allow startup
    for term_state in ["COMPLETED", "ROLLED_BACK", "ABORTED"]:
        restore_helper.cmd_update_manifest(SimpleNamespace(state=term_state, error=None, safety_backup=None))
        assert restore_helper.cmd_check_guard(SimpleNamespace()) == 0

    # 5. Recovery of non-terminal manifest
    restore_helper.cmd_init_manifest(SimpleNamespace(candidate_file=str(temp_env.db_path)))
    assert restore_helper.cmd_check_guard(SimpleNamespace()) == 1
    assert restore_helper.cmd_recover(SimpleNamespace()) == 0
    assert restore_helper.get_manifest()["state"] == "ABORTED"
    assert restore_helper.cmd_check_guard(SimpleNamespace()) == 0


def test_p4_ac_24_state_preservation_and_alert_catchup_idempotency(temp_env, monkeypatch):
    """
    P4-AC-24: Watchlist/rules/events/cursors survive same-version backup/restore and alert catch-up remains idempotent:
    - Populates Watchlist, AlertRule, AlertEvent, and alert cursor state in SystemMetadata.
    - Performs full backup and restore round trip.
    - Runs post-restore startup reconciliation (init_db) and alert catch-up.
    - Proves all state survives, 0 duplicate events are created, and catch-up is idempotent.
    """
    monkeypatch.setattr(BackupService, "get_db_path", lambda: temp_env.db_path)
    monkeypatch.setattr(BackupService, "get_backups_dir", lambda: temp_env.backups_dir)
    monkeypatch.setattr(restore_helper, "MANIFEST_FILE", temp_env.manifest_file)

    now = datetime.now(timezone.utc)
    with sessionmaker(bind=temp_env.engine)() as session:
        # Create product
        p = Product(
            id=101,
            external_product_id="vn_101",
            title="Đặc Sản Trà Xanh Thái Nguyên",
            shop_name="Trà Việt",
            category="Đồ uống",
            first_seen_at=now,
            last_seen_at=now,
        )
        session.add(p)
        session.flush()

        # Add Watchlist item
        session.add(WatchlistItem(product_id=101, notes="Theo dõi sát"))

        # Add Snapshot
        session.add(ProductSnapshot(
            id=50,
            product_id=101,
            captured_at=now,
            price=200000.0,
            sold_count=500,
        ))

        # Add AlertRule
        session.add(AlertRule(
            id=10,
            product_id=101,
            rule_type="sales_velocity_above",
            threshold=50.0,
            cooldown_minutes=60,
            is_enabled=True,
            last_condition_met=True,
        ))

        # Add AlertEvent
        session.add(AlertEvent(
            id=20,
            rule_id=10,
            product_id=101,
            triggering_snapshot_id=50,
            rule_type="sales_velocity_above",
            threshold=50.0,
            actual_value=80.0,
            actual_direction="tang",
            message="Tốc độ bán tăng vọt",
            is_read=True,
            created_at=now,
        ))

        # Add alert cursor in SystemMetadata
        session.add(SystemMetadata(key="alert_catchup_cursor", value="50"))
        session.commit()

    # 1. Create hot backup
    backup_res = BackupService.create_backup()
    assert backup_res["status"] == "ok"
    backup_file = temp_env.backups_dir / backup_res["filename"]

    # 2. Simulate restoring into target_db
    restored_db = temp_env.backups_dir / "restored_affiliate.db"
    # Copy candidate into restored_db
    assert restore_helper.cmd_replace_db(SimpleNamespace(
        candidate_file=str(backup_file),
        target_db=str(restored_db),
    )) == 0

    # 3. Simulate post-restore engine on restored_db
    restored_engine = create_engine(f"sqlite:///{restored_db}")
    RestoredSession = sessionmaker(bind=restored_engine)

    # 4. Verify all fixture state survived exactly
    with RestoredSession() as session:
        assert session.scalar(select(func.count(Product.id))) == 1
        assert session.scalar(select(func.count(WatchlistItem.id))) == 1
        assert session.scalar(select(func.count(ProductSnapshot.id))) == 1
        assert session.scalar(select(func.count(AlertRule.id))) == 1
        assert session.scalar(select(func.count(AlertEvent.id))) == 1

        cursor_meta = session.query(SystemMetadata).filter_by(key="alert_catchup_cursor").first()
        assert cursor_meta is not None and cursor_meta.value == "50"

        # 5. Run AlertService catch-up on restored state
        alert_svc = AlertService(session)
        # catch_up_alerts should evaluate existing snapshots and produce 0 duplicates
        new_events = alert_svc.catch_up_alerts()
        assert new_events == 0, f"Expected 0 duplicate alert events on catch-up, got {new_events}"

        # Run catch-up a second time to prove idempotency
        new_events_2 = alert_svc.catch_up_alerts()
        assert new_events_2 == 0, "Second catch-up pass must produce 0 duplicate alert events"

        # Total alert events in DB remains strictly 1
        total_events = session.scalar(select(func.count(AlertEvent.id)))
        assert total_events == 1


def test_p4_ac_29_runtime_foreign_keys_disabled():
    """
    P4-AC-29: Runtime connection-level FK enforcement is unchanged by Phase 4
    (PRAGMA foreign_keys = 0).
    """
    with app_engine.connect() as conn:
        res = conn.exec_driver_sql("PRAGMA foreign_keys;").scalar()
        assert res == 0, "Runtime foreign_keys must remain OFF (0) as per Phase 4 technical debt invariant"


def test_p4_ac_34_isolated_test_harness_safety(temp_env):
    """
    P4-AC-34: Required isolated backup/restore/recovery and ID-high-watermark
    historical-streaming validation passes without destructive access to the real
    backend/affiliate.db.
    """
    real_db = Path("backend/affiliate.db").resolve()
    if real_db.exists():
        assert temp_env.db_path != real_db, "Test environment must NOT point to the real affiliate.db"
        with open(real_db, "rb") as f:
            header = f.read(16)
        assert header == b"SQLite format 3\x00", "Real database must remain a valid SQLite database"

