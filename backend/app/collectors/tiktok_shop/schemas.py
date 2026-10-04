from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ExtractedProduct(BaseModel):
    """
    Normalized internal schema for product data extracted from TikTok Shop.
    All unavailable metrics remain None (never fabricated).
    """
    platform: str = "tiktok_shop"
    external_product_id: str
    title: str
    url: Optional[str] = None
    image_url: Optional[str] = None
    
    shop_id: Optional[str] = None
    shop_name: Optional[str] = None
    category: Optional[str] = None
    
    # Snapshot metrics
    price: Optional[float] = Field(default=None, ge=0)
    original_price: Optional[float] = None
    sold_count: Optional[int] = Field(default=None, ge=0)
    review_count: Optional[int] = Field(default=None, ge=0)
    rating: Optional[float] = Field(default=None, ge=0, le=5)
    stock_count: Optional[int] = None
    commission_rate: Optional[float] = None
    
    captured_at: datetime = Field(default_factory=utc_now)
    is_partial: bool = False
    source_channel: str = "http"  # 'http' or 'playwright'


class DiscoveryQuery(BaseModel):
    category_slug: Optional[str] = None
    keyword: Optional[str] = None
    limit: int = 20


class DiscoveryResult(BaseModel):
    query: DiscoveryQuery
    product_urls: List[str] = []
    products: List[ExtractedProduct] = []
    total_found: int = 0
