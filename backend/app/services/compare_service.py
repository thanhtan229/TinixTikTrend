from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any, Union
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from fastapi import HTTPException, status
from pydantic import BaseModel, Field

from app.models.product import Product
from app.models.quarantine import QuarantinedProduct
from app.models.collection import Collection
from app.models.collection_item import CollectionItem
from app.models.alert_event import AlertEvent
from app.services.product_service import get_analyzed_product
from app.analytics.deltas import ensure_utc
from app.analytics.evidence import TrendReason
from app.schemas.economics import EconomicsScenarioResponse
from app.services.economics_service import EconomicsService


class CompareRequest(BaseModel):
    product_ids: List[int]
    collection_id: Optional[int] = None


class CollectionContext(BaseModel):
    collection_id: int
    review_status: str
    notes: Optional[str] = None


class ComparedProductResponse(BaseModel):
    product_id: int
    external_product_id: str
    title: str
    url: Optional[str] = None
    image_url: Optional[str] = None
    shop_id: Optional[str] = None
    shop_name: Optional[str] = None
    category: Optional[str] = None
    first_seen_at: datetime
    last_seen_at: datetime
    is_watched: bool
    collection_context: Optional[CollectionContext] = None

    # Authoritative Phase 2 analytics fields
    trend_score: float
    trend_state: str
    confidence: Optional[str] = None
    reasons: List[Union[TrendReason, str]] = Field(default_factory=list)
    sales_velocity_24h: Optional[float] = None
    velocity_is_estimated: bool = False
    sold_delta_24h: Optional[int] = None
    sold_delta_7d: Optional[int] = None
    sales_acceleration: Optional[float] = None
    review_delta_24h: Optional[int] = None
    review_delta_7d: Optional[int] = None
    freshness_hours: Optional[float] = None
    current_price: Optional[float] = None
    rating: Optional[float] = None
    review_count: Optional[int] = None

    # Bounded 7d alert summary
    recent_alert_count_7d: int = 0
    latest_alert_at: Optional[datetime] = None

    # Phase 6: Default economics scenario
    default_economics: Optional[EconomicsScenarioResponse] = None


class CompareResponse(BaseModel):
    as_of_utc: datetime
    collection_id: Optional[int] = None
    products: List[ComparedProductResponse]


class CompareService:
    def __init__(self, db: Session):
        self.db = db

    def compare_products(
        self,
        product_ids: List[int],
        collection_id: Optional[int] = None,
        as_of_utc: Optional[datetime] = None,
    ) -> CompareResponse:
        """
        P5-AC-16 through P5-AC-25:
        Bulk compare 2-5 products against a shared request-level as_of_utc.
        Executes in <= 3 SQL queries total with zero N+1 queries.
        """
        # 1. Cardinality and Uniqueness check
        if not product_ids or len(product_ids) < 2 or len(product_ids) > 5:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Compare requires between 2 and 5 product IDs (received {len(product_ids)})."
            )

        if len(product_ids) != len(set(product_ids)):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Duplicate product IDs are not permitted in Compare request."
            )

        # 2. Capture single request-level as_of_utc
        if as_of_utc is None:
            now = datetime.now(timezone.utc)
        else:
            now = ensure_utc(as_of_utc)

        # QUERY 1: Products + snapshots + watchlist_item + quarantine check in ONE SQL query
        products_query = (
            self.db.query(Product, QuarantinedProduct.product_id)
            .outerjoin(QuarantinedProduct, Product.id == QuarantinedProduct.product_id)
            .options(
                joinedload(Product.snapshots),
                joinedload(Product.watchlist_item),
            )
            .filter(Product.id.in_(product_ids))
            .all()
        )

        found_map = {}
        quarantined_ids = []
        for p, q_id in products_query:
            if q_id is not None:
                quarantined_ids.append(p.id)
            found_map[p.id] = p

        # Missing or quarantined validation
        missing_ids = [pid for pid in product_ids if pid not in found_map]
        if missing_ids:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Products not found: {missing_ids}"
            )

        if quarantined_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Quarantined products cannot be compared: {quarantined_ids}"
            )

        # QUERY 2: Grouped recent 7d alert summary bounded by as_of_utc
        # Bound: as_of_utc - 7 days <= created_at <= as_of_utc (both boundaries inclusive)
        window_start = now - timedelta(days=7)
        alert_summary_rows = (
            self.db.query(
                AlertEvent.product_id,
                func.count(AlertEvent.id).label("count_7d"),
                func.max(AlertEvent.created_at).label("latest_at"),
            )
            .filter(
                AlertEvent.product_id.in_(product_ids),
                AlertEvent.created_at >= window_start,
                AlertEvent.created_at <= now,
            )
            .group_by(AlertEvent.product_id)
            .all()
        )
        alert_summary = {
            row[0]: (row[1], row[2]) for row in alert_summary_rows
        }

        # QUERY 3: Optional Collection context (only if collection_id provided)
        collection_items_map = {}
        if collection_id is not None:
            col_and_items = (
                self.db.query(
                    Collection.id,
                    CollectionItem.product_id,
                    CollectionItem.review_status,
                    CollectionItem.notes,
                )
                .outerjoin(
                    CollectionItem,
                    (CollectionItem.collection_id == Collection.id)
                    & (CollectionItem.product_id.in_(product_ids)),
                )
                .filter(Collection.id == collection_id)
                .all()
            )
            if not col_and_items:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Collection {collection_id} not found"
                )
            for cid, it_pid, it_status, it_notes in col_and_items:
                if it_pid is not None:
                    collection_items_map[it_pid] = (it_status, it_notes)

        # QUERY: Batch load default economics for compared products (P6-AC-34: <= 4 queries with collection, <= 3 without; zero N+1)
        econ_service = EconomicsService(self.db)
        default_economics_map = econ_service.get_default_scenarios_for_products(product_ids)

        # Build response preserving caller product order
        results = []
        for pid in product_ids:
            p = found_map[pid]
            # Reuse authoritative Phase 2 analytics with current_time = now
            analyzed = get_analyzed_product(p, current_time=now)

            # Collection context
            c_ctx = None
            if collection_id is not None and pid in collection_items_map:
                it_status, it_notes = collection_items_map[pid]
                c_ctx = CollectionContext(
                    collection_id=collection_id,
                    review_status=it_status,
                    notes=it_notes,
                )

            # Alert summary
            alert_count, latest_alert_at = alert_summary.get(pid, (0, None))
            if latest_alert_at is not None:
                latest_alert_at = ensure_utc(latest_alert_at)

            # Extract latest snapshot values for current display
            latest_snap = p.snapshots[-1] if p.snapshots else None
            current_price = latest_snap.price if latest_snap else None
            rating = latest_snap.rating if latest_snap else None
            review_count = latest_snap.review_count if latest_snap else None

            # Evidence / trend state
            trend_state = analyzed.evidence.ranking_state if analyzed.evidence else "insufficient_signal"
            confidence = analyzed.evidence.confidence if analyzed.evidence else None
            freshness_hours = analyzed.evidence.latest_observation_age_hours if analyzed.evidence else None

            results.append(
                ComparedProductResponse(
                    product_id=p.id,
                    external_product_id=p.external_product_id,
                    title=p.title,
                    url=p.url,
                    image_url=p.image_url,
                    shop_id=p.shop_id,
                    shop_name=p.shop_name,
                    category=p.category,
                    first_seen_at=analyzed.first_seen_at,
                    last_seen_at=analyzed.last_seen_at,
                    is_watched=p.watchlist_item is not None,
                    collection_context=c_ctx,
                    trend_score=analyzed.trend_score,
                    trend_state=trend_state,
                    confidence=confidence,
                    reasons=analyzed.reasons,
                    sales_velocity_24h=analyzed.deltas.sales_velocity_24h,
                    velocity_is_estimated=analyzed.deltas.velocity_is_estimated,
                    sold_delta_24h=analyzed.deltas.sold_delta_24h,
                    sold_delta_7d=analyzed.deltas.sold_delta_7d,
                    sales_acceleration=analyzed.deltas.sales_acceleration,
                    review_delta_24h=analyzed.deltas.review_delta_24h,
                    review_delta_7d=analyzed.deltas.review_delta_7d,
                    freshness_hours=freshness_hours,
                    current_price=current_price,
                    rating=rating,
                    review_count=review_count,
                    recent_alert_count_7d=alert_count,
                    latest_alert_at=latest_alert_at,
                    default_economics=default_economics_map.get(pid),
                )
            )

        return CompareResponse(
            as_of_utc=now,
            collection_id=collection_id,
            products=results,
        )
