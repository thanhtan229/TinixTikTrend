import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List
from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.db.session import get_db, SessionLocal
from app.core.config import settings
from app.collectors.tiktok_shop.session import session_status
from app.scheduler.jobs import scheduler
from app.services.backup_service import BackupService
from app.services.crawl_service import CrawlService
from app.models.product import Product
from app.models.product_snapshot import ProductSnapshot
from app.models.crawl_run import CrawlRun
from app.models.quarantine import QuarantinedProduct
from app.models.watchlist import WatchlistItem
from app.models.alert_rule import AlertRule
from app.models.alert_event import AlertEvent

router = APIRouter(prefix="/diagnostics", tags=["diagnostics"])


@router.get("", response_model=Dict[str, Any])
def get_system_diagnostics(db: Session = Depends(get_db)):
    """
    Allowlisted local diagnostics.
    Strictly excludes cookies, tokens, credentials, and full local session JSON.
    """
    db_path = BackupService.get_db_path()
    file_size_bytes = db_path.stat().st_size if db_path.exists() else 0

    # Table counts
    table_counts = {
        "products": db.scalar(select(func.count(Product.id))) or 0,
        "product_snapshots": db.scalar(select(func.count(ProductSnapshot.id))) or 0,
        "crawl_runs": db.scalar(select(func.count(CrawlRun.id))) or 0,
        "quarantined_products": db.scalar(select(func.count(QuarantinedProduct.product_id))) or 0,
        "watchlist_items": db.scalar(select(func.count(WatchlistItem.id))) or 0,
        "alert_rules": db.scalar(select(func.count(AlertRule.id))) or 0,
        "alert_events": db.scalar(select(func.count(AlertEvent.id))) or 0,
    }

    # Crawler state
    is_crawling = CrawlService.is_running()
    last_run = db.scalar(select(CrawlRun).order_by(CrawlRun.id.desc()).limit(1))

    # Scheduler jobs
    scheduled_jobs = []
    if scheduler.running:
        for job in scheduler.get_jobs():
            scheduled_jobs.append({
                "id": job.id,
                "name": job.name,
                "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
            })

    # Safe session status enum
    sess_status = session_status()

    return {
        "system": {
            "environment": settings.app_env,
            "region": "VN",
            "version": "1.0.0",
            "server_time_utc": datetime.now(timezone.utc).isoformat(),
        },
        "database": {
            "relative_path": "backend/affiliate.db",
            "size_bytes": file_size_bytes,
            "table_counts": table_counts,
        },
        "crawler": {
            "is_running": is_crawling,
            "last_run_id": last_run.id if last_run else None,
            "last_run_status": last_run.status if last_run else None,
            "last_run_finished_at": last_run.finished_at.isoformat() if last_run and last_run.finished_at else None,
            "quarantined_count": table_counts["quarantined_products"],
        },
        "scheduler": {
            "is_running": scheduler.running,
            "jobs": scheduled_jobs,
        },
        "tiktok_session": {
            "status": sess_status,
            "redacted": True,
            "notes": "Toàn bộ cookie, token và dữ liệu phiên được che giấu tuyệt đối vì lý do bảo mật.",
        },
    }


@router.get("/deep", response_model=Dict[str, Any])
def run_deep_diagnostics():
    """
    Explicit operator-triggered deep integrity and foreign key verification.
    Not executed automatically on dashboard view.
    """
    db_path = BackupService.get_db_path()
    if not db_path.exists():
        return {
            "status": "error",
            "message": "Không tìm thấy tập tin cơ sở dữ liệu.",
            "integrity_check": "missing",
            "foreign_key_check": "missing",
        }

    try:
        conn = sqlite3.connect(f"file:{db_path.resolve()}?mode=ro", uri=True)
        cursor = conn.cursor()

        cursor.execute("PRAGMA integrity_check;")
        integrity_rows = cursor.fetchall()
        integrity_status = "ok" if integrity_rows and integrity_rows[0][0] == "ok" else str(integrity_rows)

        cursor.execute("PRAGMA foreign_key_check;")
        fk_rows = cursor.fetchall()
        fk_status = "ok" if len(fk_rows) == 0 else [str(r) for r in fk_rows]

        conn.close()

        return {
            "status": "ok" if integrity_status == "ok" and fk_status == "ok" else "issues_found",
            "integrity_check": integrity_status,
            "foreign_key_check": fk_status,
            "checked_at": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Lỗi khi chạy kiểm tra toàn vẹn: {str(e)}",
            "integrity_check": "error",
            "foreign_key_check": "error",
        }
