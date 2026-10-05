from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.db.session import get_db
from app.services.watchlist_service import WatchlistService
from app.services.export_service import ExportService
from app.analytics.rising_products import AnalyzedProduct

router = APIRouter(prefix="/watchlist", tags=["Watchlist"])


class WatchlistToggleResponse(BaseModel):
    is_watched: bool
    product_id: int
    message: Optional[str] = None


class WatchlistStatusResponse(BaseModel):
    is_watched: bool
    product_id: int


class WatchlistIdsResponse(BaseModel):
    product_ids: List[int]


class WatchlistItemsResponse(BaseModel):
    items: List[AnalyzedProduct]
    total: int
    skip: int
    limit: int


@router.get("", response_model=WatchlistItemsResponse)
def get_watchlist(
    category: Optional[str] = Query(None, description="Lọc theo danh mục"),
    trend_state: str = Query("all", description="Lọc theo trạng thái xu hướng: eligible, stale, insufficient_signal, all"),
    confidence: Optional[str] = Query(None, description="Lọc theo độ tin cậy: high, medium, low, medium_or_high"),
    evidence: Optional[str] = Query(None, description="Lọc theo bằng chứng: measured_only"),
    sort_by: str = Query("trend_score", description="Sắp xếp theo: trend_score, sales_velocity, sales_delta, review_delta, freshness"),
    order: str = Query("desc", description="Thứ tự: asc, desc"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    service = WatchlistService(db)
    items, total = service.get_watched_products(
        category=category,
        trend_state=trend_state,
        confidence=confidence,
        evidence=evidence,
        sort_by=sort_by,
        order=order,
        skip=skip,
        limit=limit,
    )
    return {
        "items": items,
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.get("/export")
def export_watchlist_csv(
    category: Optional[str] = Query(None, description="Lọc theo danh mục"),
    trend_state: str = Query("all", description="Lọc theo trạng thái xu hướng: eligible, stale, insufficient_signal, all"),
    confidence: Optional[str] = Query(None, description="Lọc theo độ tin cậy: high, medium, low, medium_or_high"),
    evidence: Optional[str] = Query(None, description="Lọc theo bằng chứng: measured_only"),
    sort_by: str = Query("trend_score", description="Sắp xếp theo: trend_score, sales_velocity, sales_delta, review_delta, freshness"),
    order: str = Query("desc", description="Thứ tự: asc, desc"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
):
    """
    Export currently filtered and paginated watched products as a UTF-8 BOM CSV.
    """
    generator = ExportService.export_watchlist_csv(
        category=category,
        trend_state=trend_state,
        confidence=confidence,
        evidence=evidence,
        sort_by=sort_by,
        sort_order=order,
        limit=limit,
        offset=skip,
    )
    filename = "watchlist_export.csv"
    return StreamingResponse(
        generator,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )



@router.get("/ids", response_model=WatchlistIdsResponse)
def get_watchlist_ids(db: Session = Depends(get_db)):
    service = WatchlistService(db)
    return {"product_ids": service.get_watched_product_ids()}


@router.get("/{product_id}/status", response_model=WatchlistStatusResponse)
def get_watchlist_status(product_id: int, db: Session = Depends(get_db)):
    service = WatchlistService(db)
    return {
        "is_watched": service.is_watched(product_id),
        "product_id": product_id,
    }


@router.post("/{product_id}", response_model=WatchlistToggleResponse, status_code=status.HTTP_201_CREATED)
def add_to_watchlist(product_id: int, db: Session = Depends(get_db)):
    service = WatchlistService(db)
    try:
        item, created = service.add_to_watchlist(product_id)
        return {
            "is_watched": True,
            "product_id": product_id,
            "message": "Đã thêm vào danh sách theo dõi." if created else "Sản phẩm đã có trong danh sách theo dõi.",
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/{product_id}", response_model=WatchlistToggleResponse)
def remove_from_watchlist(product_id: int, db: Session = Depends(get_db)):
    service = WatchlistService(db)
    removed = service.remove_from_watchlist(product_id)
    return {
        "is_watched": False,
        "product_id": product_id,
        "message": "Đã xóa khỏi danh sách theo dõi." if removed else "Sản phẩm không có trong danh sách theo dõi.",
    }
