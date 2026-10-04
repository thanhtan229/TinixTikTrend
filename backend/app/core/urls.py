"""Network boundaries for the local TikTok collector."""
import asyncio
import ipaddress
import re
import socket
from urllib.parse import urlsplit, urlunsplit

TIKTOK_HOSTS = {"tiktok.com", "www.tiktok.com", "shop.tiktok.com"}
PRODUCT_PATH = re.compile(r"/(?:view/product|product|item|vn/pdp)/(\d+)/?$")


def validate_tiktok_url(url: str) -> str:
    try:
        parts = urlsplit(url)
        valid = (parts.scheme == "https" and parts.hostname in TIKTOK_HOSTS
                 and parts.port in (None, 443) and not parts.username and not parts.password)
    except ValueError:
        valid = False
    if not valid or any(c.isspace() for c in url) or "\\" in url:
        raise ValueError("Only HTTPS TikTok URLs without credentials are supported.")
    return urlunsplit(("https", parts.hostname, parts.path, parts.query, ""))


def validate_product_url(url: str) -> str:
    clean = validate_tiktok_url(url)
    parts = urlsplit(clean)
    if not PRODUCT_PATH.fullmatch(parts.path):
        raise ValueError("Paste a full TikTok Shop product URL ending in a numeric product ID.")
    # Tracking/query parameters must not change the resource being fetched.
    return urlunsplit((parts.scheme, parts.netloc, parts.path.rstrip("/"), "", ""))


def product_id_from_url(url: str) -> str:
    return PRODUCT_PATH.fullmatch(urlsplit(validate_product_url(url)).path).group(1)


async def validate_public_destination(url: str) -> None:
    """Reject DNS answers pointing at localhost/private/reserved networks."""
    host = urlsplit(url).hostname
    if urlsplit(url).scheme != "https" or not host:
        raise ValueError("Only public HTTPS destinations are permitted.")
    records = await asyncio.get_running_loop().getaddrinfo(host, 443, type=socket.SOCK_STREAM)
    if not records or any(not ipaddress.ip_address(r[4][0]).is_global for r in records):
        raise ValueError("Private or reserved network destinations are not permitted.")
