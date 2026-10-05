import os
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional, Set

from app.core.config import settings
from app.core.logging import logger, log_event
from app.db.base import Base
import app.models  # Ensure all SQLAlchemy models are registered on Base.metadata

BACKUP_FILENAME_PATTERN = re.compile(r"^tinix-affiliate-v1-\d{8}T\d{6}\.\d{6}Z\.sqlite3$")
SAFETY_BACKUP_PATTERN = re.compile(r"^tinix-pre-restore-v1-\d{8}T\d{6}\.\d{6}Z\.sqlite3$")


class BackupService:
    @classmethod
    def get_required_schema(cls) -> Dict[str, Set[str]]:
        """
        Authoritative source of truth for required schema:
        Derives required modeled tables and column names dynamically from SQLAlchemy model metadata.
        """
        return {
            table_name: {col.name for col in table.columns}
            for table_name, table in Base.metadata.tables.items()
        }

    @staticmethod
    def generate_backup_filename(dt: Optional[datetime] = None) -> str:
        """Generates approved managed backup filename: tinix-affiliate-v1-YYYYMMDDTHHMMSS.ffffffZ.sqlite3"""
        if dt is None:
            dt = datetime.now(timezone.utc)
        elif dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        else:
            dt = dt.astimezone(timezone.utc)
        return f"tinix-affiliate-v1-{dt.strftime('%Y%m%dT%H%M%S')}.{dt.microsecond:06d}Z.sqlite3"

    @staticmethod
    def generate_safety_backup_filename(dt: Optional[datetime] = None) -> str:
        """Generates approved pre-restore safety backup filename: tinix-pre-restore-v1-YYYYMMDDTHHMMSS.ffffffZ.sqlite3"""
        if dt is None:
            dt = datetime.now(timezone.utc)
        elif dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        else:
            dt = dt.astimezone(timezone.utc)
        return f"tinix-pre-restore-v1-{dt.strftime('%Y%m%dT%H%M%S')}.{dt.microsecond:06d}Z.sqlite3"

    @staticmethod
    def get_db_path() -> Path:
        raw_url = settings.database_url
        if raw_url.startswith("sqlite:///"):
            clean_path = raw_url.replace("sqlite:///", "")
            p = Path(clean_path)
            if not p.is_absolute() and p.name == "affiliate.db":
                return (Path(__file__).resolve().parent.parent.parent / "affiliate.db").resolve()
            return p.resolve()
        return (Path(__file__).resolve().parent.parent.parent / "affiliate.db").resolve()

    @staticmethod
    def get_backups_dir() -> Path:
        backups_dir = (Path(__file__).resolve().parent.parent.parent / ".local" / "backups").resolve()
        backups_dir.mkdir(parents=True, exist_ok=True)
        return backups_dir

    @classmethod
    def list_managed_backups(cls, target_dir: Optional[Path] = None) -> List[Dict[str, Any]]:
        """
        Enumerates ONLY managed backups adhering to the approved filename contract in the managed backup directory.
        No arbitrary filesystem browsing occurs.
        """
        backups_dir = target_dir.resolve() if target_dir is not None else cls.get_backups_dir()
        if not backups_dir.exists():
            return []

        backups = []
        for f in backups_dir.iterdir():
            if f.is_file() and BACKUP_FILENAME_PATTERN.match(f.name):
                stat = f.stat()
                backups.append({
                    "filename": f.name,
                    "file_path": str(f.resolve()),
                    "size_bytes": stat.st_size,
                    "modified_at": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(),
                })
        backups.sort(key=lambda x: x["filename"], reverse=True)
        return backups

    @classmethod
    def validate_sqlite_file(cls, file_path: Path) -> Tuple[bool, str]:
        """
        Validates candidate SQLite file:
        1. Existence and size
        2. SQLite header magic bytes
        3. PRAGMA integrity_check
        4. PRAGMA foreign_key_check
        5. Required schema tables and columns derived dynamically from SQLAlchemy Base.metadata
        6. Compatibility marker 'portable_backup_compatibility_version' == '1'
        """
        if not file_path.exists() or not file_path.is_file():
            return False, f"Tập tin '{file_path.name}' không tồn tại hoặc không phải là tập tin hợp lệ."

        if file_path.stat().st_size < 512:
            return False, "Kích thước tập tin quá nhỏ, không phải là cơ sở dữ liệu SQLite."

        try:
            with open(file_path, "rb") as f:
                header = f.read(16)
                if header != b"SQLite format 3\x00":
                    return False, "Tập tin không có SQLite header magic bytes hợp lệ."

            conn = sqlite3.connect(f"file:{file_path.resolve()}?mode=ro", uri=True)
            cursor = conn.cursor()

            # 1. PRAGMA integrity_check
            cursor.execute("PRAGMA integrity_check;")
            integrity_rows = cursor.fetchall()
            if not integrity_rows or integrity_rows[0][0] != "ok":
                conn.close()
                return False, f"Kiểm tra tính toàn vẹn (integrity_check) thất bại: {integrity_rows}"

            # 2. PRAGMA foreign_key_check
            cursor.execute("PRAGMA foreign_key_check;")
            fk_violations = cursor.fetchall()
            if fk_violations:
                conn.close()
                return False, f"Phát hiện vi phạm ràng buộc khóa ngoại (foreign_key_check): {fk_violations}"

            # 3. Required schema tables and columns derived from SQLAlchemy model metadata
            required_schema = cls.get_required_schema()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            existing_tables = {row[0] for row in cursor.fetchall()}
            missing_tables = set(required_schema.keys()) - existing_tables
            if missing_tables:
                conn.close()
                return False, f"Thiếu các bảng dữ liệu bắt buộc từ SQLAlchemy model metadata: {sorted(list(missing_tables))}"

            for table_name, expected_columns in required_schema.items():
                cursor.execute(f"PRAGMA table_info('{table_name}');")
                actual_columns = {row[1] for row in cursor.fetchall()}
                missing_cols = expected_columns - actual_columns
                if missing_cols:
                    conn.close()
                    return False, f"Bảng '{table_name}' thiếu các cột bắt buộc: {sorted(list(missing_cols))}"

            # 4. Compatibility version marker
            cursor.execute("SELECT value FROM system_metadata WHERE key = 'portable_backup_compatibility_version';")
            row = cursor.fetchone()
            if not row or row[0] != "1":
                actual_val = row[0] if row else "missing"
                conn.close()
                return False, (
                    f"Phiên bản tương thích không hợp lệ (yêu cầu '1', tìm thấy '{actual_val}'). "
                    "Phase 4 chỉ hỗ trợ phục hồi cùng phiên bản."
                )

            conn.close()
            return True, "Hợp lệ"
        except Exception as e:
            return False, f"Lỗi khi kiểm định tập tin SQLite: {str(e)}"

    @classmethod
    def create_backup(
        cls,
        source_db_path: Optional[Path] = None,
        target_dir: Optional[Path] = None,
    ) -> Dict[str, Any]:
        """
        Creates a point-in-time hot backup using SQLite online backup API.
        Validates the backup before atomic publishing to backend/.local/backups/.
        Enforces no-overwrite semantics with application-controlled timestamp filenames.
        """
        if source_db_path is None:
            source_db_path = cls.get_db_path()
        if not source_db_path.exists():
            raise FileNotFoundError(f"Không tìm thấy cơ sở dữ liệu nguồn: {source_db_path}")

        backups_dir = target_dir.resolve() if target_dir is not None else cls.get_backups_dir()
        backups_dir.mkdir(parents=True, exist_ok=True)

        now = datetime.now(timezone.utc)
        target_filename = cls.generate_backup_filename(now)
        target_path = backups_dir / target_filename
        staging_path = backups_dir / f".staging_{target_filename}"

        if target_path.exists():
            raise FileExistsError(f"Tập tin sao lưu '{target_filename}' đã tồn tại. Từ chối ghi đè.")

        if staging_path.exists():
            staging_path.unlink()

        try:
            # 1. Hot online backup using SQLite Online Backup API
            src = sqlite3.connect(f"file:{source_db_path.resolve()}?mode=ro", uri=True)
            dst = sqlite3.connect(staging_path)
            try:
                src.backup(dst, pages=250, sleep=0.005)
            finally:
                dst.close()
                src.close()

            # 2. Pre-publish validation
            valid, reason = cls.validate_sqlite_file(staging_path)
            if not valid:
                if staging_path.exists():
                    staging_path.unlink()
                raise ValueError(f"Bản sao lưu không vượt qua kiểm tra toàn vẹn: {reason}")

            # 3. Atomic publish (with strict no-overwrite verification)
            if target_path.exists():
                raise FileExistsError(f"Tập tin sao lưu '{target_filename}' đã tồn tại khi xuất bản. Từ chối ghi đè.")

            staging_path.rename(target_path)
            log_event("backup_created", f"Created backup {target_filename} ({target_path.stat().st_size} bytes)")

            return {
                "status": "ok",
                "filename": target_filename,
                "file_path": str(target_path),
                "size_bytes": target_path.stat().st_size,
                "created_at": now.isoformat(),
                "compatibility_version": "1",
            }
        except Exception as e:
            if staging_path.exists():
                try:
                    staging_path.unlink()
                except OSError:
                    pass
            logger.error(f"Lỗi khi thực hiện sao lưu: {e}")
            raise
