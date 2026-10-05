from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime

from app.db.session import get_db
from app.models.product import Product
from app.services.product_service import ProductService, get_analyzed_product
from app.services.export_service import ExportService
from app.analytics.rising_products import AnalyzedProduct
from app.analytics.deltas import ensure_utc

router = APIRouter(prefix="/products", tags=["Products"])


class ProductDetailResponse(BaseModel):
    id: int
    platform: str
    external_product_id: str
    title: str
    url: Optional[str] = None
    image_url: Optional[str] = None
    shop_id: Optional[str] = None
    shop_name: Optional[str] = None
    category: Optional[str] = None
    first_seen_at: datetime
    last_seen_at: datetime
    analysis: AnalyzedProduct
    snapshots: List[dict]


@router.get("", response_model=dict)
def list_products(
    category: Optional[str] = Query(None, description="Filter by category"),
    q: Optional[str] = Query(None, description="Search query in title or shop"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    service = ProductService(db)
    products, total = service.list_products(category=category, query=q, skip=skip, limit=limit)
    
    items = [get_analyzed_product(p) for p in products]
    return {
        "items": items,
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.get("/{product_id}", response_model=ProductDetailResponse)
def get_product(product_id: int, db: Session = Depends(get_db)):
    service = ProductService(db)
    product = service.get_product_by_id(product_id)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    analysis = get_analyzed_product(product)
    snapshots_data = [
        {
            "id": s.id,
            "captured_at": ensure_utc(s.captured_at),
            "price": s.price,
            "original_price": s.original_price,
            "sold_count": s.sold_count,
            "review_count": s.review_count,
            "rating": s.rating,
            "commission_rate": s.commission_rate,
        }
        for s in product.snapshots
    ]

    return ProductDetailResponse(
        id=product.id,
        platform=product.platform,
        external_product_id=product.external_product_id,
        title=product.title,
        url=product.url,
        image_url=product.image_url,
        shop_id=product.shop_id,
        shop_name=product.shop_name,
        category=product.category,
        first_seen_at=ensure_utc(product.first_seen_at),
        last_seen_at=ensure_utc(product.last_seen_at),
        analysis=analysis,
        snapshots=snapshots_data,
    )


@router.get("/{product_id}/export-history")
def export_product_history(product_id: int, range: str = Query("24h"), db: Session = Depends(get_db)):
    """
    Export chronological historical snapshots for a product as a UTF-8 BOM CSV.
    Supports only '24h', '7d', '30d'. Rejects 'all' or invalid ranges with 400.
    """
    allowed_ranges = {"24h", "7d", "30d"}
    if range not in allowed_ranges:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Khoảng thời gian '{range}' không được hỗ trợ để xuất CSV. "
                "Chỉ hỗ trợ: 24h, 7d, 30d. Khoảng 'Tất cả' chỉ hỗ trợ xem trực quan trên giao diện."
            ),
        )

    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Sản phẩm không tồn tại")

    generator = ExportService.stream_product_history(product_id=product_id, time_range=range)
    filename = f"product_{product_id}_history_{range}.csv"
    return StreamingResponse(
        generator,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )

