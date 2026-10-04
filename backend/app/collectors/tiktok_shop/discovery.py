import urllib.parse
from app.collectors.tiktok_shop.schemas import DiscoveryQuery, DiscoveryResult
from app.collectors.tiktok_shop.parser import extract_product_urls_from_listing_html, is_security_check
from app.collectors.tiktok_shop.exceptions import BlockedError
from app.collectors.tiktok_shop.session import load_state
from app.core.urls import validate_product_url
from app.core.logging import log_event

CATEGORY_KEYWORDS = {
    'fashion-accessories': 'thời trang phụ kiện TikTok Shop',
    'beauty-personal-care': 'sức khỏe làm đẹp TikTok Shop',
    'home-living': 'gia dụng TikTok Shop',
    'electronics-gadgets': 'điện tử công nghệ TikTok Shop',
    'mom-baby': 'mẹ và bé TikTok Shop',
    'food-beverages': 'thực phẩm đồ uống TikTok Shop',
}

# Observed Shop VN breadcrumb destination, rather than a video search category.
CATEGORY_SHOP_URLS = {'food-beverages': 'https://shop.tiktok.com/vn/c/food-beverages/700437'}


class ProductDiscovery:
    def __init__(self, http_client, browser_manager):
        self.http_client = http_client
        self.browser_manager = browser_manager

    def build_discovery_url(self, query: DiscoveryQuery) -> str:
        if not query.keyword and query.category_slug in CATEGORY_SHOP_URLS:
            return CATEGORY_SHOP_URLS[query.category_slug]
        keyword = query.keyword or CATEGORY_KEYWORDS.get(query.category_slug)
        if query.category_slug and not keyword:
            raise ValueError('Unsupported category. Use a search keyword instead.')
        return ('https://www.tiktok.com/search?q=' + urllib.parse.quote_plus(keyword)
                if keyword else 'https://shop.tiktok.com/vn')

    async def discover(self, query: DiscoveryQuery) -> DiscoveryResult:
        url = self.build_discovery_url(query)
        urls = []
        html = await self.http_client.fetch_html(url)
        if is_security_check(html) and not load_state():
            raise BlockedError('TikTok returned a security check instead of discovery data.')
        if html:
            urls = extract_product_urls_from_listing_html(html, url)
        if not urls:
            page = await self.browser_manager.get_new_page()
            try:
                response = await page.goto(url, wait_until='domcontentloaded')
                if response and response.status >= 400:
                    raise RuntimeError('TikTok discovery page is unavailable or blocked.')
                for _ in range(3):
                    await page.evaluate('window.scrollBy(0, 1200)')
                    await page.wait_for_timeout(800)
                rendered = await page.content()
                if is_security_check(rendered):
                    raise BlockedError('TikTok returned a security check instead of discovery data.')
                urls = extract_product_urls_from_listing_html(rendered, url)
                client = await self.http_client.get_client()
                # Preserve domain/path attributes; never turn cookies into unscoped headers.
                context = await self.browser_manager.get_context()
                for cookie in await context.cookies():
                    client.cookies.set(cookie["name"], cookie["value"],
                        domain=cookie["domain"], path=cookie["path"])
            finally:
                await page.close()
        clean = []
        for url in urls:
            try:
                clean.append(validate_product_url(url))
            except ValueError:
                continue
        clean = list(dict.fromkeys(clean))[:query.limit]
        if not clean:
            raise RuntimeError('No verified TikTok Shop product links were available. Paste a full Shop product link or retry later; video feed items are not products.')
        log_event('discovery_completed', f'Discovered {len(clean)} verified product URLs')
        return DiscoveryResult(query=query, product_urls=clean, total_found=len(clean))
