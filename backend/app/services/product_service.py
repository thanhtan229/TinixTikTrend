from typing import List, Optional, Tuple
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, func
from datetime import datetime, timezone
from sqlalchemy import select
from app.models.quarantine import QuarantinedProduct

from app.models.product import Product
from app.models.product_snapshot import ProductSnapshot
from app.analytics.deltas import SnapshotData, calculate_product_deltas, ensure_utc
from app.analytics.scoring import calculate_trend_score
from app.analytics.rising_products import AnalyzedProduct
from app.analytics.evidence import calculate_trend_evidence, calculate_trend_reasons


def get_analyzed_product(product: Product, current_time: Optional[datetime] = None) -> AnalyzedProduct:
    """Converts a DB Product model and its snapshots into an AnalyzedProduct."""
    now = ensure_utc(current_time) if current_time else datetime.now(timezone.utc)
    snap_data_list = [
        SnapshotData(
            captured_at=s.captured_at,
            sold_count=s.sold_count,
            review_count=s.review_count,
            rating=s.rating,
            price=s.price,
            original_price=s.original_price,
            commission_rate=s.commission_rate,
        )
        for s in product.snapshots
    ]
    deltas = calculate_product_deltas(snap_data_list, current_time=now)
    trend_score = calculate_trend_score(deltas, first_seen_at=product.first_seen_at, current_time=now)
    evidence = calculate_trend_evidence(snap_data_list, deltas, current_time=now)
    reasons = calculate_trend_reasons(deltas, trend_score)

    return AnalyzedProduct(
        product_id=product.id,
        external_product_id=product.external_product_id,
        title=product.title,
        url=product.url,
        image_url=product.image_url,
        shop_id=product.shop_id,
        shop_name=product.shop_name,
        category=product.category,
        first_seen_at=ensure_utc(product.first_seen_at),
        last_seen_at=ensure_utc(product.last_seen_at),
        deltas=deltas,
        trend_score=trend_score,
        evidence=evidence,
        reasons=reasons,
    )


class ProductService:
    def __init__(self, db: Session):
        self.db = db

    def get_product_by_id(self, product_id: int) -> Optional[Product]:
        return (
            self.db.query(Product)
            .options(joinedload(Product.snapshots), joinedload(Product.video_links))
            .filter(Product.id == product_id, Product.id.not_in(select(QuarantinedProduct.product_id)))
            .first()
        )

    def list_products(
        self,
        category: Optional[str] = None,
        query: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> Tuple[List[Product], int]:
        q = self.db.query(Product).options(joinedload(Product.snapshots)).filter(
            Product.id.not_in(select(QuarantinedProduct.product_id)))
        
        if category:
            q = q.filter(Product.category == category)
        if query:
            search = f"%{query}%"
            q = q.filter((Product.title.ilike(search)) | (Product.shop_name.ilike(search)))
            
        total = q.count()
        products = q.order_by(desc(Product.last_seen_at)).offset(skip).limit(limit).all()
        return products, total

    def get_all_analyzed_products(
        self,
        category: Optional[str] = None,
        current_time: Optional[datetime] = None,
    ) -> List[AnalyzedProduct]:
        q = self.db.query(Product).options(joinedload(Product.snapshots)).filter(
            Product.id.not_in(select(QuarantinedProduct.product_id)))
        if category:
            q = q.filter(Product.category == category)
        products = q.all()
        return [get_analyzed_product(p, current_time=current_time) for p in products]
