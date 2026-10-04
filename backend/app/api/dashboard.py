from typing import Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.trend_service import TrendService

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("", response_model=Dict[str, Any])
def get_dashboard_summary(db: Session = Depends(get_db)):
    service = TrendService(db)
    return service.get_dashboard_summary()
