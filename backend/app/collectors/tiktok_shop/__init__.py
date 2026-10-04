from typing import List, Optional
from app.collectors.tiktok_shop.schemas import ExtractedProduct, DiscoveryQuery, DiscoveryResult
from app.collectors.tiktok_shop.browser import BrowserManager
from app.collectors.tiktok_shop.client import TikTokHttpClient
from app.collectors.tiktok_shop.discovery import ProductDiscovery
from app.collectors.tiktok_shop.product import ProductCollector
from app.core.logging import logger, log_event


class TikTokShopCollector:
    """
    Main isolated collector interface for TikTok Shop VN.
    Encapsulates HTTP client, Playwright fallback browser, discovery and product detail extractors.
    """
    def __init__(self):
        self.browser_manager: Optional[BrowserManager] = None
        self.http_client: Optional[TikTokHttpClient] = None
        self.discovery_engine: Optional[ProductDiscovery] = None
        self.product_collector: Optional[ProductCollector] = None

    async def initialize(self) -> None:
        self.browser_manager = await BrowserManager.get_instance()
        # Do not launch a browser for structured pages already served over HTTP.
        self.http_client = TikTokHttpClient()
        self.discovery_engine = ProductDiscovery(self.http_client, self.browser_manager)
        self.product_collector = ProductCollector(self.http_client, self.browser_manager)
        log_event("collector_initialized", "TikTokShopCollector ready with HTTP-first strategy.")

    async def discover_products(self, query: DiscoveryQuery) -> DiscoveryResult:
        if not self.discovery_engine:
            await self.initialize()
        return await self.discovery_engine.discover(query)

    async def get_product(self, url: str) -> Optional[ExtractedProduct]:
        if not self.product_collector:
            await self.initialize()
        return await self.product_collector.get_product_by_url(url)

    async def close(self) -> None:
        if self.http_client:
            await self.http_client.close()
        if self.browser_manager:
            await self.browser_manager.close()
        log_event("collector_closed", "TikTokShopCollector closed.")


__all__ = [
    "TikTokShopCollector",
    "ExtractedProduct",
    "DiscoveryQuery",
    "DiscoveryResult",
]
