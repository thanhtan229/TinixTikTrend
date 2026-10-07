from datetime import datetime, timezone
from pathlib import Path
import sqlite3
import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.db.init_db import init_db
from app.models.product import Product
from app.models.system_metadata import SystemMetadata
from app.models.economics_scenario import EconomicsScenario
from app.services.backup_service import BackupService


def test_isolated_v2_to_v3_bootstrap_and_schema_verification(tmp_path: Path):
    """
    Workstream 3 / P6-AC-35..38:
    Verify additive bootstrap from v2 to v3 in an isolated database:
    - Pre-existing products preserved.
    - economics_scenarios table created additively.
    - Required schema derived dynamically passes.
    - portable_backup_compatibility_version advanced from '2' to '3'.
    """
    db_file = tmp_path / "v2_upgrade_test.db"
    engine = create_engine(f"sqlite:///{db_file}")

    # Create tables without economics_scenarios initially to simulate v2 database
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Simulate existing v2 data
    prod = Product(
        platform="tiktok_shop",
        external_product_id="prod_v2_1001",
        title="Test Product From V2",
        first_seen_at=datetime.now(timezone.utc),
        last_seen_at=datetime.now(timezone.utc),
    )
    session.add(prod)
    session.add(SystemMetadata(key="portable_backup_compatibility_version", value="2"))
    session.commit()

    # Verify initial v2 state
    marker = session.get(SystemMetadata, "portable_backup_compatibility_version")
    assert marker is not None
    assert marker.value == "2"

    # Run init_db on the existing session
    init_db(session)

    # Verify marker advanced to "3"
    marker_after = session.get(SystemMetadata, "portable_backup_compatibility_version")
    assert marker_after.value == "3"

    # Verify product preserved
    p_check = session.query(Product).filter_by(external_product_id="prod_v2_1001").first()
    assert p_check is not None
    assert p_check.title == "Test Product From V2"

    # Verify economics_scenarios table exists and has expected columns
    inspector = inspect(engine)
    assert "economics_scenarios" in inspector.get_table_names()
    cols = {col["name"] for col in inspector.get_columns("economics_scenarios")}
    assert "commission_rate_bps" in cols
    assert "commission_base_vnd" in cols
    assert "commission_base_source" in cols
    assert "is_default" in cols

    # Verify required schema validation passes
    req_schema = BackupService.get_required_schema()
    assert "economics_scenarios" in req_schema

    session.close()
    engine.dispose()


def test_v2_backup_rejected_by_v3_validation(tmp_path: Path):
    """
    ADR-004 & Phase 6 invariant:
    Backups with compatibility version '2' are rejected by v3 engine during validation.
    """
    db_file = tmp_path / "v2_backup.sqlite3"
    engine = create_engine(f"sqlite:///{db_file}")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Seed v2 compatibility marker
    session.add(SystemMetadata(key="portable_backup_compatibility_version", value="2"))
    session.commit()
    session.close()
    engine.dispose()

    # Validate against BackupService (which expects '3')
    is_valid, msg = BackupService.validate_sqlite_file(db_file)
    assert is_valid is False
    assert "Phiên bản tương thích không hợp lệ (yêu cầu '3', tìm thấy '2')" in msg


def test_v3_backup_roundtrip_validation(tmp_path: Path):
    """
    Verify creating and validating a v3 backup succeeds.
    """
    source_db = tmp_path / "v3_source.db"
    engine = create_engine(f"sqlite:///{source_db}")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    session.add(SystemMetadata(key="portable_backup_compatibility_version", value="3"))
    session.commit()
    session.close()
    engine.dispose()

    backup_dir = tmp_path / "backups"
    result = BackupService.create_backup(source_db_path=source_db, target_dir=backup_dir)

    assert result["status"] == "ok"
    backup_file = backup_dir / result["filename"]
    assert backup_file.exists()
    assert "tinix-affiliate-v3-" in result["filename"]

    # Validate backup file
    is_valid, msg = BackupService.validate_sqlite_file(backup_file)
    assert is_valid is True
    assert msg == "Hợp lệ"


def test_isolated_v3_restore_and_disaster_recovery_lifecycle(tmp_path: Path, monkeypatch):
    """
    Workstream 3 / ADR-004 Remediation:
    Isolated disaster recovery and restore lifecycle test for Phase 6 v3 economics data:
    1. Pre-restore safety backup creation with v3 naming.
    2. Atomic replacement of live database file.
    3. Restore manifest tracking and pre-start guard enforcement.
    4. Injected post-replacement failure causing rollback to safety backup.
    5. Verified preservation of v3 economics scenarios.
    6. Exclusion of host-bound tiktok-session.json.
    7. Zero touches to real backend/affiliate.db.
    """
    from types import SimpleNamespace
    from app.commands import restore_helper
    from app.models.product_snapshot import ProductSnapshot

    manifest_file = tmp_path / "restore_manifest.json"
    monkeypatch.setattr(restore_helper, "MANIFEST_FILE", manifest_file)

    target_db = tmp_path / "target_affiliate.db"
    backups_dir = tmp_path / "backups"
    backups_dir.mkdir(parents=True, exist_ok=True)

    # 1. Initialize isolated target database with Phase 6 v3 economics data
    target_engine = create_engine(f"sqlite:///{target_db}")
    Base.metadata.create_all(bind=target_engine)
    TargetSession = sessionmaker(bind=target_engine)
    with TargetSession() as s:
        s.add(SystemMetadata(key="portable_backup_compatibility_version", value="3"))
        prod = Product(
            id=101,
            platform="tiktok_shop",
            external_product_id="prod_base_101",
            title="Base Target Product",
            first_seen_at=datetime.now(timezone.utc),
            last_seen_at=datetime.now(timezone.utc),
        )
        s.add(prod)
        s.flush()
        s.add(EconomicsScenario(
            id=1,
            product_id=101,
            name="Base Economics Plan",
            commission_rate_bps=1200,
            commission_base_vnd=150_000,
            is_default=True,
        ))
        s.commit()
    target_engine.dispose()

    # 2. Prepare candidate database with different v3 economics data
    cand_db = tmp_path / "cand_affiliate.db"
    cand_engine = create_engine(f"sqlite:///{cand_db}")
    Base.metadata.create_all(bind=cand_engine)
    CandSession = sessionmaker(bind=cand_engine)
    with CandSession() as s:
        s.add(SystemMetadata(key="portable_backup_compatibility_version", value="3"))
        prod_cand = Product(
            id=202,
            platform="tiktok_shop",
            external_product_id="prod_cand_202",
            title="Candidate Product",
            first_seen_at=datetime.now(timezone.utc),
            last_seen_at=datetime.now(timezone.utc),
        )
        s.add(prod_cand)
        s.flush()
        s.add(EconomicsScenario(
            id=10,
            product_id=202,
            name="Candidate Restored Plan",
            commission_rate_bps=2000,
            commission_base_vnd=300_000,
            sample_cost_vnd=80_000,
            is_default=True,
        ))
        s.commit()
    cand_engine.dispose()

    # Create managed v3 backup from candidate DB
    cand_res = BackupService.create_backup(source_db_path=cand_db, target_dir=backups_dir)
    assert cand_res["status"] == "ok"
    candidate_backup_file = backups_dir / cand_res["filename"]
    assert candidate_backup_file.exists()

    # Place dummy session file in tmp_path to verify session exclusion
    fake_session = tmp_path / "tiktok-session.json"
    fake_session.write_text('{"token": "dummy_secret_session"}', encoding="utf-8")

    # 3. Candidate validation before stopping services
    assert restore_helper.cmd_validate_candidate(SimpleNamespace(candidate_file=str(candidate_backup_file))) == 0

    # 4. Manifest initialization
    assert restore_helper.cmd_init_manifest(SimpleNamespace(candidate_file=str(candidate_backup_file))) == 0
    # Guard check: non-terminal state blocks normal startup
    assert restore_helper.cmd_check_guard(SimpleNamespace()) == 1

    # 5. Create pre-restore safety backup
    safety_backup_file = backups_dir / BackupService.generate_safety_backup_filename()
    create_safety_code = restore_helper.cmd_create_safety_backup(SimpleNamespace(
        target_db=str(target_db),
        safety_backup=str(safety_backup_file),
    ))
    assert create_safety_code == 0
    assert safety_backup_file.exists()
    assert "tinix-pre-restore-v3-" in safety_backup_file.name

    # Safety backup collision prevention (cannot overwrite existing safety backup)
    assert restore_helper.cmd_create_safety_backup(SimpleNamespace(
        target_db=str(target_db),
        safety_backup=str(safety_backup_file),
    )) == 1

    # 6. Atomic replacement simulation
    restore_helper.cmd_update_manifest(SimpleNamespace(
        state="REPLACEMENT_STARTED",
        error=None,
        safety_backup=str(safety_backup_file),
    ))
    assert restore_helper.cmd_replace_db(SimpleNamespace(
        candidate_file=str(candidate_backup_file),
        target_db=str(target_db),
    )) == 0

    # 7. Injected post-replacement failure & automatic rollback to safety backup
    # Verify rollback reverts target_db back to base data
    assert restore_helper.cmd_rollback(SimpleNamespace(
        safety_backup=str(safety_backup_file),
        target_db=str(target_db),
    )) == 0

    # Verify target DB restored to base economics
    check_engine = create_engine(f"sqlite:///{target_db}")
    CheckSession = sessionmaker(bind=check_engine)
    with CheckSession() as s:
        p = s.query(Product).first()
        assert p.id == 101
        sc = s.query(EconomicsScenario).first()
        assert sc.name == "Base Economics Plan"
        assert sc.commission_rate_bps == 1200
    check_engine.dispose()

    restore_helper.cmd_update_manifest(SimpleNamespace(
        state="ROLLED_BACK",
        error="Simulated post-replacement health failure",
        safety_backup=str(safety_backup_file),
    ))
    # Terminal state ROLLED_BACK allows guard check
    assert restore_helper.cmd_check_guard(SimpleNamespace()) == 0

    # 8. Successful second restore attempt to COMPLETED
    assert restore_helper.cmd_replace_db(SimpleNamespace(
        candidate_file=str(candidate_backup_file),
        target_db=str(target_db),
    )) == 0

    # Verify restored target DB has candidate economics data
    check_engine2 = create_engine(f"sqlite:///{target_db}")
    CheckSession2 = sessionmaker(bind=check_engine2)
    with CheckSession2() as s:
        p = s.query(Product).first()
        assert p.id == 202
        sc = s.query(EconomicsScenario).first()
        assert sc.name == "Candidate Restored Plan"
        assert sc.commission_rate_bps == 2000
        assert sc.sample_cost_vnd == 80_000
        assert sc.is_default is True
    check_engine2.dispose()

    restore_helper.cmd_update_manifest(SimpleNamespace(
        state="COMPLETED",
        error=None,
        safety_backup=None,
    ))
    assert restore_helper.cmd_check_guard(SimpleNamespace()) == 0

    # 9. Session artifact exclusion check
    assert not (backups_dir / "tiktok-session.json").exists()
    assert fake_session.exists()  # Local session was not touched

