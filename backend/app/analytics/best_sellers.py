from typing import List, Literal
from app.analytics.rising_products import AnalyzedProduct


RankByOption = Literal["total_sold", "sold_delta_24h", "sold_delta_7d"]


def rank_best_sellers(
    products: List[AnalyzedProduct],
    rank_by: RankByOption = "total_sold",
    limit: int = 50,
) -> List[AnalyzedProduct]:
    """
    Ranks best-selling products by total cumulative sold count or recent sales volume (24h, 7d).
    """
    if rank_by == "sold_delta_24h":
        products = [p for p in products if p.deltas.sold_delta_24h is not None and not p.deltas.is_stale]
        key_func = lambda p: (p.deltas.sold_delta_24h or 0, p.deltas.latest_sold_count or 0)
    elif rank_by == "sold_delta_7d":
        products = [p for p in products if p.deltas.sold_delta_7d is not None and not p.deltas.is_stale]
        key_func = lambda p: (p.deltas.sold_delta_7d or 0, p.deltas.latest_sold_count or 0)
    else:
        # Default: lifetime sold count
        key_func = lambda p: (p.deltas.latest_sold_count or 0, p.deltas.sold_delta_24h or 0)

    return sorted(products, key=key_func, reverse=True)[:limit]
