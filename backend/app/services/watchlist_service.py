from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timezone
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select, desc

from app.models.product import Product
from app.models.watchlist import WatchlistItem
from app.models.quarantine import QuarantinedProduct
from app.services.product_service import get_analyzed_product
from app.analytics.rising_products import AnalyzedProduct


class WatchlistService:
    def __init__(self, db: Session):
        self.db = db

    def is_watched(self, product_id: int) -> bool:
        return self.db.query(WatchlistItem).filter_by(product_id=product_id).first() is not None

    def add_to_watchlist(self, product_id: int, notes: Optional[str] = None) -> Tuple[WatchlistItem, bool]:
        product = self.db.get(Product, product_id)
        if product is None:
            raise ValueError(f"Product {product_id} not found.")

        existing = self.db.query(WatchlistItem).filter_by(product_id=product_id).first()
        if existing is not None:
            if notes is not None and existing.notes != notes:
                existing.notes = notes
                self.db.commit()
            return existing, False

        item = WatchlistItem(product_id=product_id, notes=notes)
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item, True

    def remove_from_watchlist(self, product_id: int) -> bool:
        item = self.db.query(WatchlistItem).filter_by(product_id=product_id).first()
        if item is None:
            return False
        self.db.delete(item)
        self.db.commit()
        return True

    def get_watched_product_ids(self) -> List[int]:
        rows = self.db.query(WatchlistItem.product_id).all()
        return [r[0] for r in rows]

    def get_watched_products(
        self,
        category: Optional[str] = None,
        trend_state: str = "all",
        confidence: Optional[str] = None,
        evidence: Optional[str] = None,
        sort_by: str = "trend_score",
        order: str = "desc",
        skip: int = 0,
        limit: int = 50,
        current_time: Optional[datetime] = None,
    ) -> Tuple[List[AnalyzedProduct], int]:
        # Query products joined with WatchlistItem excluding quarantined products
        q = (
            self.db.query(Product)
            .join(WatchlistItem, WatchlistItem.product_id == Product.id)
            .options(joinedload(Product.snapshots))
            .filter(Product.id.not_in(select(QuarantinedProduct.product_id)))
        )

        if category:
            q = q.filter(Product.category == category)

        products = q.all()
        analyzed = [get_analyzed_product(p, current_time=current_time) for p in products]

        # 1. Filter by trend_state
        if trend_state == "eligible":
            candidates = [p for p in analyzed if p.evidence and p.evidence.ranking_state == "eligible"]
        elif trend_state == "stale":
            candidates = [p for p in analyzed if p.evidence and p.evidence.ranking_state == "stale"]
        elif trend_state == "insufficient_signal":
            candidates = [p for p in analyzed if p.evidence and p.evidence.ranking_state == "insufficient_measured_signal"]
        else:
            candidates = analyzed

        # 2. Filter by confidence
        if confidence:
            if confidence == "medium_or_high":
                candidates = [p for p in candidates if p.evidence and p.evidence.confidence in ("medium", "high")]
            else:
                candidates = [p for p in candidates if p.evidence and p.evidence.confidence == confidence]

        # 3. Filter by evidence
        if evidence == "measured_only":
            candidates = [
                p for p in candidates
                if p.evidence and p.evidence.signals.get("sales_velocity") == "measured"
                and not p.deltas.velocity_is_estimated
            ]

        # 4. Deterministic sorting
        is_desc = (order.lower() != "asc")

        if sort_by == "sales_velocity":
            candidates.sort(
                key=lambda p: (
                    p.deltas.sales_velocity_24h is None,
                    -(p.deltas.sales_velocity_24h or 0) if is_desc else (p.deltas.sales_velocity_24h or 0),
                    -p.trend_score,
                    p.product_id,
                )
            )
        elif sort_by == "sales_delta":
            candidates.sort(
                key=lambda p: (
                    p.deltas.sold_delta_24h is None,
                    -(p.deltas.sold_delta_24h or 0) if is_desc else (p.deltas.sold_delta_24h or 0),
                    -p.trend_score,
                    p.product_id,
                )
            )
        elif sort_by == "review_delta":
            candidates.sort(
                key=lambda p: (
                    p.deltas.review_delta_24h is None,
                    -(p.deltas.review_delta_24h or 0) if is_desc else (p.deltas.review_delta_24h or 0),
                    -p.trend_score,
                    p.product_id,
                )
            )
        elif sort_by == "freshness":
            candidates.sort(
                key=lambda p: (
                    (p.evidence.latest_observation_age_hours if p.evidence else 9999.0) if is_desc
                    else -(p.evidence.latest_observation_age_hours if p.evidence else 9999.0),
                    -p.trend_score,
                    p.product_id,
                )
            )
        else:  # default "trend_score"
            candidates.sort(
                key=lambda p: (
                    p.trend_score,
                    p.deltas.sales_velocity_24h or 0,
                    p.deltas.sales_acceleration or 0,
                    p.deltas.sold_delta_24h or 0,
                    -p.product_id,
                ),
                reverse=is_desc,
            )

        total = len(candidates)
        paginated = candidates[skip : skip + limit]
        return paginated, total
