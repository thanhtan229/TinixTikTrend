from datetime import datetime, timezone, timedelta
from typing import List, Optional
from app.analytics.deltas import ensure_utc
from app.analytics.rising_products import AnalyzedProduct


def filter_and_rank_new_products(
    products: List[AnalyzedProduct],
    time_window_hours: int = 72,  # default 3 days (72h)
    limit: int = 50,
    current_time: Optional[datetime] = None,
) -> List[AnalyzedProduct]:
    """
    Filters products first detected within the given time window (e.g. 24h, 72h, 168h/7d)
    and sorts by initial momentum (Trend Score, sales velocity).
    """
    now = ensure_utc(current_time) if current_time is not None else datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=time_window_hours)
    
    new_prods = []
    for p in products:
        first_seen = ensure_utc(p.first_seen_at)
        if first_seen >= cutoff:
            new_prods.append(p)
            
    # Sort new products by trend score (or first_seen_at if trend scores are equal)
    return sorted(
        new_prods,
        key=lambda p: (
            p.trend_score,
            p.deltas.sales_velocity_24h or 0,
            p.first_seen_at,
        ),
        reverse=True,
    )[:limit]
