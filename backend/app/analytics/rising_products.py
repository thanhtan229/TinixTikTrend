from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from app.analytics.deltas import DeltaMetrics
from app.analytics.evidence import TrendEvidence, TrendReason


class AnalyzedProduct(BaseModel):
    product_id: int
    external_product_id: str
    title: str
    url: Optional[str] = None
    image_url: Optional[str] = None
    shop_id: Optional[str] = None
    shop_name: Optional[str] = None
    category: Optional[str] = None
    first_seen_at: Any
    last_seen_at: Any
    
    deltas: DeltaMetrics
    trend_score: float
    evidence: Optional[TrendEvidence] = None
    reasons: List[TrendReason] = []


def rank_rising_products(
    products: List[AnalyzedProduct],
    limit: int = 50,
    min_velocity: Optional[float] = None,
) -> List[AnalyzedProduct]:
    """
    Ranks products by their rising momentum (combining Trend Score, 24h sales velocity, and acceleration).
    """
    candidates = [p for p in products if not p.deltas.is_stale and (p.deltas.sales_velocity_24h or 0) > 0]
    if min_velocity is not None:
        candidates = [p for p in candidates if (p.deltas.sales_velocity_24h or 0) >= min_velocity]
        
    return sorted(
        candidates,
        key=lambda p: (
            p.trend_score,
            p.deltas.sales_velocity_24h or 0,
            p.deltas.sales_acceleration or 0,
            p.deltas.sold_delta_24h or 0,
            -p.product_id,
        ),
        reverse=True,
    )[:limit]
