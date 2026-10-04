import re
from typing import Optional
from app.collectors.tiktok_shop.client import TikTokHttpClient
from app.collectors.tiktok_shop.browser import BrowserManager
from app.collectors.tiktok_shop.parser import extract_product_from_html, is_security_check
from app.collectors.tiktok_shop.exceptions import BlockedError
from app.collectors.tiktok_shop.session import load_state, SessionStateError
from app.collectors.tiktok_shop.schemas import ExtractedProduct
from app.core.logging import log_event
from app.core.urls import validate_product_url


class ProductCollector:
    """
    Extracts normalized TikTok Shop product details using HTTP first,
    falling back to Playwright only when necessary.
    """
    def __init__(self, http_client: TikTokHttpClient, browser_manager: BrowserManager):
        self.http_client = http_client
        self.browser_manager = browser_manager

    async def get_product_by_url(self, url: str) -> Optional[ExtractedProduct]:
        url = validate_product_url(url)
        log_event("product_fetch_started", f"Fetching product: {url}")
        
        # 1. HTTP First
        html = await self.http_client.fetch_html(url)
        if is_security_check(html) and not load_state():
            raise BlockedError('TikTok returned a security check instead of product data.')
        if html:
            product = extract_product_from_html(html, page_url=url)
            if product and not product.is_partial:
                log_event("product_discovered", f"Product parsed via HTTP: {product.title[:30]}", {"id": product.external_product_id})
                return product

        # 2. Playwright Fallback
        log_event("product_fetch_fallback", f"HTTP yielded incomplete data for {url}. Falling back to Playwright.")
        try:
            page = await self.browser_manager.get_new_page()
            try:
                async def guard_navigation(route):
                    if route.request.is_navigation_request() and route.request.frame == page.main_frame:
                        try:
                            validate_product_url(route.request.url)
                        except ValueError:
                            await route.abort()
                            return
                    await route.fallback()
                await page.route("**/*", guard_navigation)
                response = await page.goto(url, wait_until="domcontentloaded")
                if response and response.status >= 400:
                    return None
                await page.wait_for_timeout(1000)
                
                # Try getting rendered HTML
                rendered_html = await page.content()
                if is_security_check(rendered_html):
                    raise BlockedError('TikTok returned a security check instead of product data.')
                product = extract_product_from_html(rendered_html, page_url=url)
                
                if product and not product.is_partial:
                    product.source_channel = "playwright"
                    log_event("product_discovered", f"Product parsed via Playwright: {product.title[:30]}", {"id": product.external_product_id})
                    return product
            finally:
                await page.close()
        except (BlockedError, SessionStateError):
            raise
        except Exception as e:
            log_event("product_fetch_failed", f"Failed fetching product via Playwright on {url}: {e}")

        return None
