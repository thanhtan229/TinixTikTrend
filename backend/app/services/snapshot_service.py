from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.orm import Session

from app.models.product_snapshot import ProductSnapshot
from app.collectors.tiktok_shop.schemas import ExtractedProduct
from app.core.logging import log_event


class SnapshotService:
    def __init__(self, db: Session):
        self.db = db

    def create_snapshot_from_extracted(
        self,
        product_id: int,
        extracted: ExtractedProduct,
        crawl_run_id: Optional[int] = None,
    ) -> ProductSnapshot:
        """
        Appends an immutable historical snapshot for a product.
        Old snapshots are strictly preserved.
        """
        snapshot = ProductSnapshot(
            product_id=product_id,
            crawl_run_id=crawl_run_id,
            captured_at=extracted.captured_at,
            price=extracted.price,
            original_price=extracted.original_price,
            sold_count=extracted.sold_count,
            review_count=extracted.review_count,
            rating=extracted.rating,
            stock_count=extracted.stock_count,
            commission_rate=extracted.commission_rate,
            is_partial=extracted.is_partial,
        )
        self.db.add(snapshot)
        self.db.flush()
        
        log_event(
            "snapshot_created",
            f"Created snapshot for product_id={product_id} (sold={extracted.sold_count}, price={extracted.price})",
            {"product_id": product_id, "snapshot_id": snapshot.id}
        )
        return snapshot
