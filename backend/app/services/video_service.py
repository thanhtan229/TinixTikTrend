"""On-demand, metadata-only TikTok video support."""
import json
import re
from datetime import datetime, timezone
from urllib.parse import urlencode, urlsplit

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.urls import validate_public_destination
from app.models.product_video_link import ProductVideoLink
from app.models.quarantine import QuarantinedProduct
from app.models.product import Product
from app.models.tiktok_video import TikTokVideo

VIDEO_PATH = re.compile(r"/@([A-Za-z0-9._-]{1,24})/video/([0-9]{1,32})/?$")
MAX_RESPONSE_BYTES = 512 * 1024
OEMBED_URL = "https://www.tiktok.com/oembed"


class VideoInputError(ValueError):
    pass


def canonicalize_video_url(raw_url: str) -> tuple[str, str, str]:
    try:
        parts = urlsplit(raw_url.strip())
        match = VIDEO_PATH.fullmatch(parts.path)
        allowed_host = parts.hostname in {"www.tiktok.com", "tiktok.com"}
        valid = (
            parts.scheme == "https" and allowed_host and parts.port in (None, 443)
            and not parts.username and not parts.password and match
        )
    except ValueError:
        valid = False
        match = None
    if not valid or any(char.isspace() for char in raw_url) or "\\" in raw_url:
        raise VideoInputError("Dán liên kết HTTPS TikTok dạng /@creator/video/ID hợp lệ.")
    handle, video_id = match.groups()
    return f"https://www.tiktok.com/@{handle}/video/{video_id}", video_id, handle


def ensure_product_is_available(db: Session, product_id: int) -> Product:
    product = db.get(Product, product_id)
    if product is None or db.scalar(
        select(QuarantinedProduct.product_id).where(QuarantinedProduct.product_id == product_id)
    ) is not None:
        raise LookupError("Product not found")
    return product


async def refresh_video(video: TikTokVideo) -> None:
    """Fetch only the public oEmbed metadata; no cookies, redirects, retries, or counters."""
    video.last_attempt_at = datetime.now(timezone.utc)
    video.refresh_status = "unavailable"
    video.refresh_message = "TikTok no cung cấp bộ đếm tương tác qua nguồn metadata này."
    try:
        await validate_public_destination(OEMBED_URL)
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(8.0), follow_redirects=False, trust_env=False,
            headers={"Accept": "application/json", "User-Agent": "TinixTrendHunter/1.0"},
        ) as client:
            async with client.stream(
                "GET", f"{OEMBED_URL}?{urlencode({'url': video.canonical_url})}"
            ) as response:
                if response.status_code != 200:
                    video.refresh_status = "blocked" if response.status_code in (403, 429) else "unavailable"
                    video.refresh_message = f"Metadata không khả dụng (HTTP {response.status_code})."
                    return
                body = bytearray()
                async for chunk in response.aiter_bytes():
                    body.extend(chunk)
                    if len(body) > MAX_RESPONSE_BYTES:
                        video.refresh_message = "Phản hồi metadata vượt giới hạn an toàn."
                        return
        data = json.loads(body)
        if not isinstance(data, dict):
            raise ValueError("Unsupported metadata response")
        if isinstance(data.get("title"), str):
            video.description = data["title"][:10000]
        if isinstance(data.get("author_name"), str):
            video.creator_name = data["author_name"][:256]
        if isinstance(data.get("author_url"), str):
            author_path = urlsplit(data["author_url"])
            if author_path.scheme == "https" and author_path.hostname in {"www.tiktok.com", "tiktok.com"}:
                handle_match = re.fullmatch(r"/@([A-Za-z0-9._-]{1,24})/?", author_path.path)
                if handle_match:
                    video.creator_handle = handle_match.group(1)
        thumbnail = data.get("thumbnail_url")
        if isinstance(thumbnail, str) and len(thumbnail) <= 1024:
            try:
                await validate_public_destination(thumbnail)
                video.thumbnail_url = thumbnail
            except (ValueError, OSError):
                video.thumbnail_url = None
        video.refresh_status = "ok"
        video.refresh_message = "Metadata đã cập nhật; số liệu tương tác không được cung cấp."
    except (httpx.HTTPError, OSError, ValueError, json.JSONDecodeError):
        video.refresh_status = "unavailable"
        video.refresh_message = "TikTok không trả về metadata công khai có thể sử dụng."


def attach_video(db: Session, product_id: int, raw_url: str) -> TikTokVideo:
    product = ensure_product_is_available(db, product_id)
    canonical, video_id, handle = canonicalize_video_url(raw_url)
    video = db.get(TikTokVideo, video_id)
    if video is None:
        video = TikTokVideo(video_id=video_id, canonical_url=canonical, creator_handle=handle)
        db.add(video)
        db.flush()
    existing = db.scalar(
        select(ProductVideoLink.id).where(
            ProductVideoLink.product_id == product_id,
            ProductVideoLink.external_video_id == video_id,
        )
    )
    if existing is not None:
        raise FileExistsError("Video is already associated with this product")
    db.add(ProductVideoLink(
        product_id=product.id, external_video_id=video_id,
        creator_id=handle, source="operator", confidence=1.0,
    ))
    db.commit()
    db.refresh(video)
    return video
