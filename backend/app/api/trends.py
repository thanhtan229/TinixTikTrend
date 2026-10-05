from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.trend_service import TrendService
from app.services.export_service import ExportService
from app.analytics.rising_products import AnalyzedProduct
from app.analytics.best_sellers import RankByOption

router = APIRouter(prefix="/trends", tags=["Trends"])


@router.get("", response_model=List[AnalyzedProduct])
def get_all_trends(
    category: Optional[str] = Query(None, description="Filter by product category"),
    trend_state: str = Query("eligible", description="Ranking state: eligible, all, stale, insufficient_signal"),
    confidence: Optional[str] = Query(None, description="Confidence level: low, medium, high, medium_or_high"),
    evidence: Optional[str] = Query(None, description="Evidence requirement: measured_only"),
    sort_by: str = Query("trend_score", description="Sort by: trend_score, sales_velocity, sales_delta, review_delta, freshness"),
    order: str = Query("desc", description="Sort order: desc or asc"),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    service = TrendService(db)
    return service.get_trending_products(
        category=category,
        trend_state=trend_state,
        confidence=confidence,
        evidence=evidence,
        sort_by=sort_by,
        order=order,
        limit=limit,
    )


@router.get("/rising", response_model=List[AnalyzedProduct])
def get_rising_trends(
    category: Optional[str] = Query(None),
    min_velocity: Optional[float] = Query(None, description="Minimum 24h sales velocity"),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    service = TrendService(db)
    return service.get_rising_products(category=category, limit=limit, min_velocity=min_velocity)


@router.get("/new", response_model=List[AnalyzedProduct])
def get_new_products(
    category: Optional[str] = Query(None),
    hours: int = Query(72, ge=1, le=720, description="Max hours since first detected (e.g. 24, 72, 168)"),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    service = TrendService(db)
    return service.get_new_products(category=category, time_window_hours=hours, limit=limit)


@router.get("/best-sellers", response_model=List[AnalyzedProduct])
def get_best_sellers(
    category: Optional[str] = Query(None),
    rank_by: RankByOption = Query("total_sold", description="Ranking metric: total_sold, sold_delta_24h, sold_delta_7d"),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    service = TrendService(db)
    return service.get_best_sellers(category=category, rank_by=rank_by, limit=limit)


@router.get("/export")
def export_trends_csv(
    category: Optional[str] = Query(None, description="Filter by product category"),
    trend_state: str = Query("eligible", description="Ranking state: eligible, all, stale, insufficient_signal"),
    confidence: Optional[str] = Query(None, description="Confidence level: low, medium, high, medium_or_high"),
    evidence: Optional[str] = Query(None, description="Evidence requirement: measured_only"),
    sort_by: str = Query("trend_score", description="Sort by: trend_score, sales_velocity, sales_delta, review_delta, freshness"),
    order: str = Query("desc", description="Sort order: desc or asc"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """
    Export currently filtered and paginated trends as a UTF-8 BOM CSV.
    """
    generator = ExportService.export_trends_csv(
        category=category,
        trend_state=trend_state,
        confidence=confidence,
        evidence=evidence,
        sort_by=sort_by,
        sort_order=order,
        limit=limit,
        offset=offset,
    )
    filename = "trends_export.csv"
    return StreamingResponse(
        generator,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
