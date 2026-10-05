from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session

from app.services.product_service import ProductService
from app.analytics.rising_products import AnalyzedProduct, rank_rising_products
from app.analytics.new_products import filter_and_rank_new_products
from app.analytics.best_sellers import rank_best_sellers, RankByOption
from app.analytics.scoring import has_trend_evidence


class TrendService:
    def __init__(self, db: Session):
        self.db = db
        self.product_service = ProductService(db)

    def get_trending_products(
        self,
        category: Optional[str] = None,
        trend_state: str = "eligible",
        confidence: Optional[str] = None,
        evidence: Optional[str] = None,
        sort_by: str = "trend_score",
        order: str = "desc",
        limit: int = 50,
        current_time: Optional[datetime] = None,
    ) -> List[AnalyzedProduct]:
        products = self.product_service.get_all_analyzed_products(category=category, current_time=current_time)

        # 1. Filter by trend_state
        if trend_state == "eligible":
            candidates = [p for p in products if p.evidence and p.evidence.ranking_state == "eligible"]
        elif trend_state == "stale":
            candidates = [p for p in products if p.evidence and p.evidence.ranking_state == "stale"]
        elif trend_state == "insufficient_signal":
            candidates = [p for p in products if p.evidence and p.evidence.ranking_state == "insufficient_measured_signal"]
        else:  # "all" or any other fallback
            candidates = products

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
                    -p.product_id if is_desc else p.product_id,
                ),
                reverse=is_desc,
            )

        return candidates[:limit]

    def get_rising_products(
        self,
        category: Optional[str] = None,
        limit: int = 50,
        min_velocity: Optional[float] = None,
    ) -> List[AnalyzedProduct]:
        products = self.product_service.get_all_analyzed_products(category=category)
        return rank_rising_products(products, limit=limit, min_velocity=min_velocity)

    def get_new_products(
        self,
        category: Optional[str] = None,
        time_window_hours: int = 72,
        limit: int = 50,
    ) -> List[AnalyzedProduct]:
        products = self.product_service.get_all_analyzed_products(category=category)
        return filter_and_rank_new_products(products, time_window_hours=time_window_hours, limit=limit)

    def get_best_sellers(
        self,
        category: Optional[str] = None,
        rank_by: RankByOption = "total_sold",
        limit: int = 50,
    ) -> List[AnalyzedProduct]:
        products = self.product_service.get_all_analyzed_products(category=category)
        return rank_best_sellers(products, rank_by=rank_by, limit=limit)

    def get_dashboard_summary(self) -> Dict[str, Any]:
        all_prods = self.product_service.get_all_analyzed_products()
        
        # Calculate high level statistics
        total_products = len(all_prods)
        rising_count = sum(1 for p in all_prods if p.trend_score >= 70.0)
        
        top_trending = self.get_trending_products(limit=5)
        top_rising = rank_rising_products(all_prods, limit=5)
        top_new = filter_and_rank_new_products(all_prods, time_window_hours=72, limit=5)
        top_best_sellers = rank_best_sellers(all_prods, rank_by="total_sold", limit=5)

        return {
            "stats": {
                "total_products": total_products,
                "high_trend_count": rising_count,
            },
            "trending": top_trending,
            "rising": top_rising,
            "new_products": top_new,
            "best_sellers": top_best_sellers,
        }
