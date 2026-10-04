from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.core.revision import LOADED_REVISION

router = APIRouter(tags=["Health"])


@router.get("/health")
def health_check(db: Session = Depends(get_db)):
    """
    Health check endpoint returning application status, configuration info, and database connectivity.
    """
    db_status = "connected"
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    return {
        "status": "ok" if db_status == "connected" else "degraded",
        "app_name": settings.app_name,
        "environment": settings.app_env,
        "region": settings.tiktok_region,
        "database": db_status,
        "revision": LOADED_REVISION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
