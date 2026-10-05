import argparse
import sys
from pathlib import Path

from app.services.backup_service import BackupService


def cmd_create(args) -> int:
    try:
        result = BackupService.create_backup()
        print("=========================================================================")
        print(" THÀNH CÔNG: Đã tạo bản sao lưu trực tuyến chuẩn SQLite!")
        print("=========================================================================")
        print(f" Tập tin: {result['filename']}")
        print(f" Đường dẫn: {result['file_path']}")
        print(f" Kích thước: {result['size_bytes']} bytes")
        print(f" Thời gian tạo (UTC): {result['created_at']}")
        print(f" Phiên bản tương thích: v{result['compatibility_version']}")
        print("=========================================================================")
        return 0
    except Exception as e:
        print(f"LỖI: Tiến trình sao lưu thất bại: {e}", file=sys.stderr)
        return 1


def main():
    parser = argparse.ArgumentParser(description="Operator CLI for managed hot SQLite backups.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("create", help="Create a validated point-in-time hot backup")

    args = parser.parse_args()
    if args.command == "create":
        sys.exit(cmd_create(args))
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
