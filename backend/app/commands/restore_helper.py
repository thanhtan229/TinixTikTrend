import argparse
import json
import os
import shutil
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

from app.services.backup_service import BackupService


RESTORE_DIR = Path(__file__).resolve().parent.parent.parent / ".local" / "restore"
DEFAULT_MANIFEST_FILE = RESTORE_DIR / "manifest.json"
MANIFEST_FILE = DEFAULT_MANIFEST_FILE
TERMINAL_STATES = {"COMPLETED", "ROLLED_BACK", "ABORTED"}


def get_manifest_path() -> Path:
    global MANIFEST_FILE
    if MANIFEST_FILE != DEFAULT_MANIFEST_FILE:
        return Path(MANIFEST_FILE).resolve()
    override = os.environ.get("RESTORE_MANIFEST_PATH")
    if override:
        return Path(override).resolve()
    return MANIFEST_FILE


def get_manifest() -> dict:
    manifest_file = get_manifest_path()
    if not manifest_file.exists():
        return {"state": "IDLE"}
    try:
        with open(manifest_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        return {"state": "CORRUPTED", "error": str(e)}


def save_manifest(manifest: dict) -> None:
    manifest_file = get_manifest_path()
    manifest_file.parent.mkdir(parents=True, exist_ok=True)
    manifest["updated_at"] = datetime.now(timezone.utc).isoformat()
    with open(manifest_file, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)


def cmd_check_guard(args) -> int:
    """Pre-start guard: blocks normal start/restart if manifest is non-terminal."""
    manifest = get_manifest()
    state = manifest.get("state", "IDLE")
    if state == "IDLE" or state in TERMINAL_STATES:
        return 0

    print(
        f"CRITICAL: Phát hiện tiến trình phục hồi cơ sở dữ liệu chưa hoàn tất (Trạng thái: {state}).\n"
        f"Khởi động dịch vụ bị CHẶN để bảo vệ tính toàn vẹn của dữ liệu.\n"
        f"Vui lòng chạy 'RESTORE.bat --recover' để khôi phục hoặc đưa về trạng thái an toàn.",
        file=sys.stderr,
    )
    return 1


def cmd_validate_candidate(args) -> int:
    candidate_path = Path(args.candidate_file).resolve()
    valid, reason = BackupService.validate_sqlite_file(candidate_path)
    if not valid:
        print(f"LỖI KIỂM ĐỊNH TẬP TIN ỨNG VIÊN: {reason}", file=sys.stderr)
        return 1
    print(f"XÁC MINH HỢP LỆ: Tập tin '{candidate_path.name}' đạt tất cả tiêu chuẩn tương thích và toàn vẹn.")
    return 0


def cmd_init_manifest(args) -> int:
    candidate_path = str(Path(args.candidate_file).resolve())
    manifest = {
        "state": "VALIDATING_CANDIDATE",
        "candidate_file": candidate_path,
        "safety_backup_file": None,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "error": None,
    }
    save_manifest(manifest)
    return 0


def cmd_update_manifest(args) -> int:
    manifest = get_manifest()
    manifest["state"] = args.state
    if args.error:
        manifest["error"] = args.error
    if args.safety_backup:
        manifest["safety_backup_file"] = str(Path(args.safety_backup).resolve())
    save_manifest(manifest)
    return 0


def cmd_create_safety_backup(args) -> int:
    """
    Creates pre-restore safety backup using the validated SQLite Online Backup API.
    Enforces compatibility, schema, integrity_check, and foreign_key_check before acceptance.
    Strictly prevents silent overwriting of existing safety backups.
    """
    target_db = Path(args.target_db).resolve()
    safety_path = Path(args.safety_backup).resolve()
    safety_path.parent.mkdir(parents=True, exist_ok=True)

    if not target_db.exists():
        print(f"Lỗi: Không tìm thấy target DB '{target_db}'", file=sys.stderr)
        return 1

    # Check collision before starting: never overwrite or delete existing safety backup!
    if safety_path.exists():
        print(
            f"LỖI XUNG ĐỘT TẬP TIN: Bản sao lưu an toàn '{safety_path.name}' đã tồn tại.\n"
            f"Từ chối ghi đè để bảo vệ bản sao lưu an toàn hiện có.\n"
            f"Dừng tiến trình phục hồi trước khi thay thế database.",
            file=sys.stderr,
        )
        return 1

    staging_path = safety_path.parent / f".staging_{safety_path.name}"
    if staging_path.exists():
        try:
            staging_path.unlink()
        except OSError:
            pass

    try:
        # 1. Hot online backup using SQLite Online Backup API (not raw filesystem copy)
        src = sqlite3.connect(f"file:{target_db}?mode=ro", uri=True)
        dst = sqlite3.connect(staging_path)
        try:
            src.backup(dst, pages=250, sleep=0.005)
        finally:
            dst.close()
            src.close()

        # 2. Strict validation of safety backup before acceptance
        valid, reason = BackupService.validate_sqlite_file(staging_path)
        if not valid:
            print(f"LỖI KIỂM ĐỊNH SAFETY BACKUP: {reason}", file=sys.stderr)
            if staging_path.exists():
                try:
                    staging_path.unlink()
                except OSError:
                    pass
            return 1

        # 3. Final collision check before publication
        if safety_path.exists():
            if staging_path.exists():
                try:
                    staging_path.unlink()
                except OSError:
                    pass
            print(
                f"LỖI XUNG ĐỘT TẬP TIN: Bản sao lưu an toàn '{safety_path.name}' đã tồn tại khi xuất bản.\n"
                f"Từ chối ghi đè để bảo vệ bản sao lưu hiện có.",
                file=sys.stderr,
            )
            return 1

        staging_path.rename(safety_path)
        print(f"Đã tạo bản sao lưu an toàn trước phục hồi bằng SQLite backup: {safety_path.name}")
        return 0
    except Exception as e:
        print(f"Lỗi khi tạo safety backup: {e}", file=sys.stderr)
        if staging_path.exists():
            try:
                staging_path.unlink()
            except OSError:
                pass
        return 1


def cmd_replace_db(args) -> int:
    candidate_path = Path(args.candidate_file).resolve()
    target_db = Path(args.target_db).resolve()

    if not candidate_path.exists():
        print(f"Lỗi: Không tìm thấy tập tin candidate '{candidate_path}'", file=sys.stderr)
        return 1

    # Atomic copy to a temp sibling then rename
    temp_target = target_db.parent / f".tmp_{target_db.name}"
    try:
        shutil.copy2(candidate_path, temp_target)
        if target_db.exists():
            target_db.unlink()
        temp_target.rename(target_db)
        print(f"Đã thay thế cơ sở dữ liệu mục tiêu bằng tập tin ứng viên thành công.")
        return 0
    except Exception as e:
        if temp_target.exists():
            try:
                temp_target.unlink()
            except OSError:
                pass
        print(f"Lỗi khi thay thế cơ sở dữ liệu: {e}", file=sys.stderr)
        return 1


def cmd_rollback(args) -> int:
    safety_path = Path(args.safety_backup).resolve()
    target_db = Path(args.target_db).resolve()

    if not safety_path.exists():
        print(f"LỖI NGHIÊM TRỌNG: Không tìm thấy safety backup '{safety_path}' để rollback!", file=sys.stderr)
        return 1

    try:
        temp_target = target_db.parent / f".tmp_rollback_{target_db.name}"
        shutil.copy2(safety_path, temp_target)
        if target_db.exists():
            target_db.unlink()
        temp_target.rename(target_db)
        print(f"Rollback thành công: Đã phục hồi cơ sở dữ liệu từ bản sao lưu an toàn.")
        return 0
    except Exception as e:
        print(f"LỖI ROLLBACK: Không thể phục hồi từ safety backup: {e}", file=sys.stderr)
        return 1


def cmd_recover(args) -> int:
    manifest = get_manifest()
    state = manifest.get("state", "IDLE")

    if state == "IDLE":
        print("Không có tiến trình phục hồi nào đang dang dở.")
        return 0

    if state in TERMINAL_STATES:
        print(f"Tiến trình phục hồi trước đó đã kết thúc ở trạng thái chuẩn: {state}.")
        return 0

    print(f"Bắt đầu khôi phục sự cố phục hồi (Trạng thái hiện tại: {state})...")
    safety_file = manifest.get("safety_backup_file")
    target_db = BackupService.get_db_path()

    # Pre-replacement states can safely abort
    if state in ("VALIDATING_CANDIDATE", "STOPPING_SERVICES", "SAFETY_BACKUP_CREATED"):
        print("Sự cố xảy ra trước khi thay thế cơ sở dữ liệu. Cơ sở dữ liệu gốc chưa bị tác động.")
        manifest["state"] = "ABORTED"
        manifest["error"] = "Phục hồi sự cố: Hủy bỏ an toàn tiến trình gián đoạn trước khi thay thế."
        save_manifest(manifest)
        print("Trạng thái đã chuyển về ABORTED. Khởi động thông thường đã được mở khóa.")
        return 0

    # At or after REPLACEMENT_STARTED: must reach verified COMPLETED or verified ROLLED_BACK
    print("Sự cố xảy ra từ hoặc sau bước REPLACEMENT_STARTED. Tiến hành kiểm tra và phục hồi an toàn...")
    if not safety_file or not Path(safety_file).exists():
        print(f"LỖI KHÔNG THỂ PHỤC HỒI: Không tìm thấy safety backup ({safety_file}). Startup tiếp tục bị khóa!", file=sys.stderr)
        return 1

    # Attempt rollback to safety backup
    print(f"Đang tiến hành rollback về bản sao lưu an toàn: {safety_file}...")
    temp_target = target_db.parent / f".tmp_recover_{target_db.name}"
    try:
        shutil.copy2(Path(safety_file), temp_target)
        if target_db.exists():
            target_db.unlink()
        temp_target.rename(target_db)

        # Validate restored DB
        valid, reason = BackupService.validate_sqlite_file(target_db)
        if not valid:
            print(f"Lỗi kiểm định sau rollback: {reason}", file=sys.stderr)
            return 1

        manifest["state"] = "ROLLED_BACK"
        manifest["error"] = "Phục hồi sự cố: Đã rollback về bản sao lưu an toàn."
        save_manifest(manifest)
        print("Rollback thành công. Trạng thái đã chuyển về ROLLED_BACK. Khởi động thông thường đã được mở khóa.")
        return 0
    except Exception as e:
        print(f"Lỗi trong quá trình phục hồi: {e}", file=sys.stderr)
        return 1


def cmd_list_candidates(args) -> int:
    """
    AC-17: When no arguments are provided to restore, check manifest precedence first,
    then enumerate ONLY managed backups in backend/.local/backups/.
    No general filesystem browsing occurs.
    """
    manifest = get_manifest()
    state = manifest.get("state", "IDLE")
    if state != "IDLE" and state not in TERMINAL_STATES:
        print(
            f"CRITICAL: Phát hiện tiến trình phục hồi chưa hoàn tất (Trạng thái: {state}).\n"
            f"Khôi phục sự cố có độ ưu tiên cao hơn việc nhận ứng viên mới.\n"
            f"Vui lòng chạy 'RESTORE.bat --recover' để khôi phục hoặc đưa về trạng thái an toàn.",
            file=sys.stderr,
        )
        return 1

    backups = BackupService.list_managed_backups()
    print("=========================================================================")
    print(" DANH SÁCH BẢN SAO LƯU QUẢN LÝ (backend/.local/backups/):")
    print("=========================================================================")
    if not backups:
        print(" Không tìm thấy bản sao lưu nào trong thư mục quản lý.")
    else:
        for b in backups:
            print(f" - {b['filename']} ({b['size_bytes']} bytes, sửa đổi: {b['modified_at']})")
    print("=========================================================================")
    print(" Cú pháp phục hồi: .\\RESTORE.bat <đường_dẫn_bản_sao_lưu>")
    print(" Cú pháp khắc phục: .\\RESTORE.bat --recover")
    print("=========================================================================")
    return 0


def cmd_safety_filename(args) -> int:
    """Prints the authoritative safety backup filename using microsecond UTC timestamp."""
    print(BackupService.generate_safety_backup_filename())
    return 0


def main():
    parser = argparse.ArgumentParser(description="Helper CLI for restore lifecycle and manifest management.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # check-guard
    subparsers.add_parser("check-guard")

    # validate-candidate
    p_val = subparsers.add_parser("validate-candidate")
    p_val.add_argument("candidate_file", help="Path to candidate SQLite backup file")

    # init-manifest
    p_init = subparsers.add_parser("init-manifest")
    p_init.add_argument("candidate_file", help="Path to candidate SQLite backup file")

    # update-manifest
    p_upd = subparsers.add_parser("update-manifest")
    p_upd.add_argument("state", help="Manifest state")
    p_upd.add_argument("--error", default=None, help="Error message")
    p_upd.add_argument("--safety-backup", default=None, help="Path to safety backup file")

    # create-safety-backup
    p_sb = subparsers.add_parser("create-safety-backup")
    p_sb.add_argument("target_db", help="Path to active target DB")
    p_sb.add_argument("safety_backup", help="Path to safety backup output file")

    # replace-db
    p_rep = subparsers.add_parser("replace-db")
    p_rep.add_argument("candidate_file", help="Path to candidate file")
    p_rep.add_argument("target_db", help="Path to active target DB")

    # rollback
    p_rb = subparsers.add_parser("rollback")
    p_rb.add_argument("safety_backup", help="Path to safety backup file")
    p_rb.add_argument("target_db", help="Path to active target DB")

    # recover
    subparsers.add_parser("recover")

    # list-candidates (AC-17)
    subparsers.add_parser("list-candidates")

    # safety-filename
    subparsers.add_parser("safety-filename")

    args = parser.parse_args()

    commands = {
        "check-guard": cmd_check_guard,
        "validate-candidate": cmd_validate_candidate,
        "init-manifest": cmd_init_manifest,
        "update-manifest": cmd_update_manifest,
        "create-safety-backup": cmd_create_safety_backup,
        "replace-db": cmd_replace_db,
        "rollback": cmd_rollback,
        "recover": cmd_recover,
        "list-candidates": cmd_list_candidates,
        "safety-filename": cmd_safety_filename,
    }

    cmd_fn = commands.get(args.command)
    if not cmd_fn:
        parser.print_help()
        sys.exit(1)

    sys.exit(cmd_fn(args))


if __name__ == "__main__":
    main()

