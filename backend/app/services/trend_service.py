from typing import List, Optional, Dict, Any
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
        limit: int = 50,
    ) -> List[AnalyzedProduct]:
        products = self.product_service.get_all_analyzed_products(category=category)
        evidenced = [p for p in products if has_trend_evidence(p.deltas)]
        return sorted(evidenced, key=lambda p: p.trend_score, reverse=True)[:limit]

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
        
        top_trending = sorted((p for p in all_prods if has_trend_evidence(p.deltas)),
                              key=lambda p: p.trend_score, reverse=True)[:5]
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
