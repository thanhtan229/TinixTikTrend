from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime

from app.db.session import get_db
from app.services.product_service import ProductService, get_analyzed_product
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
