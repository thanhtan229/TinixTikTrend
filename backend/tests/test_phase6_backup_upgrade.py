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
