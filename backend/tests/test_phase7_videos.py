import asyncio
from datetime import datetime, timedelta, timezone

from app.models.tiktok_video import TikTokVideo, VideoSnapshot
from app.services.content_metrics import calculate_content_metrics
from app.services.video_service import canonicalize_video_url, refresh_video


def test_video_url_is_canonicalized_and_rejects_unsafe_or_non_video_urls():
    canonical, video_id, handle = canonicalize_video_url(
        "https://www.tiktok.com/@maker/video/123456789?lang=en#comments"
    )
    assert canonical == "https://www.tiktok.com/@maker/video/123456789"
    assert (video_id, handle) == ("123456789", "maker")
    for invalid in (
        "http://www.tiktok.com/@maker/video/123",
        "https://www.tiktok.com.evil.test/@maker/video/123",
        "https://www.tiktok.com/@maker/video/123/extra",
        "https://user@www.tiktok.com/@maker/video/123",
        "https://www.tiktok.com/@maker/photo/123",
    ):
        try:
            canonicalize_video_url(invalid)
            assert False, invalid
        except ValueError:
            pass


def test_video_velocity_uses_actual_window_and_preserves_decreases():
    now = datetime.now(timezone.utc)
    old = VideoSnapshot(
        video_id="123", source="fixture", captured_at=now - timedelta(hours=22),
        view_count=100, like_count=20, comment_count=None, share_count=2, collect_count=5,
    )
    latest = VideoSnapshot(
        video_id="123", source="fixture", captured_at=now,
        view_count=78, like_count=30, comment_count=None, share_count=2, collect_count=5,
    )
    result = calculate_content_metrics([latest, old])
    assert result["velocities"]["view_count"] == -24
    assert result["anomalies"]["view_count"] is True
    assert result["velocities"]["like_count"] == 10 / (22 / 24)
    assert result["velocities"]["comment_count"] is None
    assert result["engagement_rate"] is None


def test_product_video_api_shares_global_identity_and_detach_preserves_video(client):
    from app.db.session import get_db
    from app.main import app

    url = "https://www.tiktok.com/@maker/video/987654321"
    first = client.post("/api/products/1/videos", json={"url": url})
    second = client.post("/api/products/2/videos", json={"url": url})
    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["video_id"] == second.json()["video_id"] == "987654321"

    invalid = client.post("/api/products/1/videos", json={"url": "https://example.com/"})
    duplicate = client.post("/api/products/1/videos", json={"url": url})
    assert invalid.status_code == 422
    assert invalid.json()["detail"]["code"] == "invalid_video_url"
    assert duplicate.status_code == 409

    db_dependency = app.dependency_overrides[get_db]()
    db = next(db_dependency)
    try:
        db.add(VideoSnapshot(
            video_id="987654321", source="fixture",
            captured_at=datetime.now(timezone.utc), view_count=1234,
            like_count=56, comment_count=None, share_count=None, collect_count=None,
        ))
        db.commit()
    finally:
        db_dependency.close()

    detached = client.delete("/api/products/1/videos/987654321")
    assert detached.status_code == 204
    assert client.get("/api/products/1/videos").json()["items"] == []
    remaining = client.get("/api/products/2/videos").json()["items"]
    assert len(remaining) == 1
    assert remaining[0]["video_id"] == "987654321"
    assert len(remaining[0]["snapshots"]) == 1
    assert remaining[0]["snapshots"][0]["view_count"] == 1234
    assert client.post("/api/products/999999/videos", json={"url": url}).status_code == 404


def test_blocked_oembed_refresh_is_bounded_and_never_creates_metric_snapshot(monkeypatch):
    class FakeResponse:
        status_code = 429

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return None

    class FakeClient:
        def __init__(self, **kwargs):
            self.options = kwargs

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return None

        def stream(self, *args, **kwargs):
            return FakeResponse()

    async def allow_public_destination(_url):
        return None

    monkeypatch.setattr("app.services.video_service.validate_public_destination", allow_public_destination)
    monkeypatch.setattr("app.services.video_service.httpx.AsyncClient", FakeClient)
    video = TikTokVideo(
        video_id="123456", canonical_url="https://www.tiktok.com/@maker/video/123456",
        refresh_status="not_refreshed",
    )

    asyncio.run(refresh_video(video))

    assert video.refresh_status == "blocked"
    assert video.refresh_message == "Metadata không khả dụng (HTTP 429)."
    assert video.snapshots == []
