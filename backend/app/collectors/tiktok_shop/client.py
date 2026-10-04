import asyncio
import random
from typing import Optional, Dict, Any
import httpx
from urllib.parse import urljoin
from app.core.urls import validate_tiktok_url, validate_public_destination

from app.core.config import settings
from app.core.logging import logger, log_event
from app.collectors.tiktok_shop.browser import MOBILE_UA
from app.collectors.tiktok_shop.session import load_state, http_cookies


class TikTokHttpClient:
    """
    HTTP Client for TikTok Shop with conservative rate limiting, random jitter,
    retries with exponential backoff, and mobile session headers.
    """
    def __init__(self, cookies: Optional[Dict[str, str]] = None):
        self.headers = {
            "User-Agent": MOBILE_UA,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
            "Sec-Ch-Ua-Mobile": "?1",
            "Sec-Ch-Ua-Platform": '"iOS"',
            "Upgrade-Insecure-Requests": "1",
        }
        self.cookies = cookies or {}
        self._client: Optional[httpx.AsyncClient] = None
        self._semaphore = asyncio.Semaphore(settings.max_concurrency)

    async def get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                headers=self.headers,
                cookies=self.cookies or http_cookies(load_state()),
                timeout=float(settings.request_timeout),
                follow_redirects=False,
                trust_env=False,
            )
        return self._client

    async def _apply_rate_limit(self) -> None:
        """Applies configured delay + small random jitter."""
        delay = random.uniform(settings.request_delay_min, settings.request_delay_max)
        await asyncio.sleep(delay)

    async def fetch_html(self, url: str) -> Optional[str]:
        """
        Fetches HTML string for a URL with retries and exponential backoff.
        """
        url = validate_tiktok_url(url)
        async with self._semaphore:
            client = await self.get_client()
            
            for attempt in range(1, settings.max_retries + 1):
                try:
                    await self._apply_rate_limit()
                    log_event("request_started", f"GET {url} (Attempt {attempt}/{settings.max_retries})")
                    
                    current = url
                    for redirect in range(6):
                        await validate_public_destination(current)
                        response = await client.get(current)
                        if response.status_code not in (301, 302, 303, 307, 308):
                            break
                        current = validate_tiktok_url(urljoin(current, response.headers.get("location", "")))
                    else:
                        raise ValueError("Too many redirects.")
                    
                    if response.status_code == 200:
                        return response.text
                    elif response.status_code in (429, 403):
                        log_event("request_failed", f"HTTP {response.status_code} for {url}", {"status_code": response.status_code})
                        if attempt < settings.max_retries:
                            backoff = (2 ** attempt) + random.uniform(0.5, 2.0)
                            await asyncio.sleep(backoff)
                    else:
                        log_event("request_failed", f"HTTP {response.status_code} for {url}", {"status_code": response.status_code})
                        return None
                except Exception as e:
                    log_event("request_failed", f"Network error on {url}: {str(e)}", {"error": str(e)})
                    if attempt < settings.max_retries:
                        backoff = (2 ** attempt) + random.uniform(0.5, 2.0)
                        await asyncio.sleep(backoff)
                        
            return None

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None
