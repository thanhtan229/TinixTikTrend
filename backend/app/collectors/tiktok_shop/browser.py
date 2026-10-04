import asyncio
from typing import Optional
from playwright.async_api import async_playwright, Browser, BrowserContext, Page, Playwright
from app.core.config import settings
from app.core.logging import logger, log_event
from app.collectors.tiktok_shop.exceptions import BrowserInitError
from app.core.urls import validate_public_destination
from app.collectors.tiktok_shop.session import load_state, SessionStateError

DESKTOP_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)
MOBILE_UA = DESKTOP_UA


class BrowserManager:
    """
    Singleton Playwright browser lifecycle manager.
    Reuses browser context and session cookies to minimize CPU and RAM footprint.
    """
    _instance: Optional["BrowserManager"] = None
    _lock = asyncio.Lock()

    def __init__(self):
        self._playwright: Optional[Playwright] = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._is_initialized = False

    @classmethod
    async def get_instance(cls) -> "BrowserManager":
        async with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    async def initialize(self) -> None:
        if self._is_initialized and self._browser and self._browser.is_connected():
            return

        try:
            state = load_state()
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(
                headless=settings.headless,
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                ],
            )
            
            # Create a reusable shared browser context with VN locale and Desktop UA for full web feed rendering
            self._context = await self._browser.new_context(
                service_workers="block",
                storage_state=state,
                user_agent=DESKTOP_UA,
                locale="vi-VN",
                extra_http_headers={
                    "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
                },
                viewport={"width": 1280, "height": 800},
            )
            async def public_requests_only(route):
                try:
                    await validate_public_destination(route.request.url)
                except (ValueError, OSError):
                    await route.abort()
                    return
                await route.continue_()
            await self._context.route("**/*", public_requests_only)
            self._is_initialized = True
            log_event("browser_init", "Playwright headless browser initialized successfully.")
        except SessionStateError:
            await self.close()
            raise
        except Exception as e:
            logger.error(f"Failed to initialize Playwright browser: {e}")
            await self.close()
            raise BrowserInitError(f"Playwright initialization failed: {e}")

    async def get_context(self) -> BrowserContext:
        if not self._is_initialized or not self._browser or not self._browser.is_connected():
            await self.initialize()
        return self._context

    async def get_new_page(self) -> Page:
        ctx = await self.get_context()
        page = await ctx.new_page()
        page.set_default_timeout(settings.request_timeout * 1000)
        return page

    async def get_cookies_dict(self) -> dict:
        """Returns cookies from browser context for HTTP client session sharing."""
        if not self._context:
            return {}
        cookies = await self._context.cookies()
        return {c["name"]: c["value"] for c in cookies}

    async def close(self) -> None:
        try:
            if self._context:
                await self._context.close()
                self._context = None
            if self._browser:
                await self._browser.close()
                self._browser = None
            if self._playwright:
                await self._playwright.stop()
                self._playwright = None
            self._is_initialized = False
            log_event("browser_closed", "Playwright browser shut down cleanly.")
        except Exception as e:
            logger.warning(f"Error closing Playwright browser: {e}")
