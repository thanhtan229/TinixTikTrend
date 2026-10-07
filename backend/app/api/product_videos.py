from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.product_video_link import ProductVideoLink
from app.models.tiktok_video import TikTokVideo, VideoSnapshot
from app.services.content_metrics import calculate_content_metrics
from app.services.video_service import (
    VideoInputError, attach_video, ensure_product_is_available, refresh_video,
)

router = APIRouter(prefix="/products/{product_id}/videos", tags=["Product videos"])


class VideoCreate(BaseModel):
    url: str = Field(min_length=1, max_length=2048)


@router.get("")
def list_product_videos(product_id: int, db: Session = Depends(get_db)):
    try:
        ensure_product_is_available(db, product_id)
    except LookupError:
        raise HTTPException(status_code=404, detail="Product not found")
    rows = db.execute(
        select(ProductVideoLink, TikTokVideo)
        .join(TikTokVideo, TikTokVideo.video_id == ProductVideoLink.external_video_id)
        .where(ProductVideoLink.product_id == product_id)
        .order_by(ProductVideoLink.first_seen_at.desc(), ProductVideoLink.id.desc())
    ).all()
    video_ids = [video.video_id for _, video in rows]
    snapshots_by_video = {video_id: [] for video_id in video_ids}
    if video_ids:
        rank = func.row_number().over(
            partition_by=VideoSnapshot.video_id,
            order_by=(VideoSnapshot.captured_at.desc(), VideoSnapshot.id.desc()),
        ).label("snapshot_rank")
        ranked = select(
            VideoSnapshot.id, VideoSnapshot.video_id, VideoSnapshot.view_count,
            VideoSnapshot.like_count, VideoSnapshot.comment_count, VideoSnapshot.share_count,
            VideoSnapshot.collect_count, VideoSnapshot.source, VideoSnapshot.captured_at,
            rank,
        ).where(VideoSnapshot.video_id.in_(video_ids)).subquery()
        recent = db.execute(
            select(ranked).where(ranked.c.snapshot_rank <= 2)
            .order_by(ranked.c.video_id, ranked.c.snapshot_rank)
        ).all()
        for item in recent:
            snapshots_by_video[item.video_id].append(VideoSnapshot(
                id=item.id, video_id=item.video_id, view_count=item.view_count,
                like_count=item.like_count, comment_count=item.comment_count,
                share_count=item.share_count, collect_count=item.collect_count,
                source=item.source, captured_at=item.captured_at,
            ))
    return {
        "items": [
            {
                "video_id": video.video_id,
                "url": video.canonical_url,
                "creator_handle": video.creator_handle,
                "creator_name": video.creator_name,
                "description": video.description,
                "thumbnail_url": video.thumbnail_url,
                "refresh_status": video.refresh_status,
                "refresh_message": video.refresh_message,
                "last_attempt_at": video.last_attempt_at,
                "snapshots": [
                    {
                        "captured_at": snapshot.captured_at,
                        **{key: getattr(snapshot, key) for key in (
                            "view_count", "like_count", "comment_count", "share_count", "collect_count"
                        )},
                        "source": snapshot.source,
                    }
                    for snapshot in snapshots_by_video[video.video_id]
                ],
                "content_metrics": calculate_content_metrics(snapshots_by_video[video.video_id]),
                "associated_at": link.first_seen_at,
            }
            for link, video in rows
        ]
    }


@router.post("", status_code=status.HTTP_201_CREATED)
def add_product_video(product_id: int, payload: VideoCreate, db: Session = Depends(get_db)):
    try:
        video = attach_video(db, product_id, payload.url)
    except VideoInputError as exc:
        raise HTTPException(status_code=422, detail={"code": "invalid_video_url", "message": str(exc)})
    except LookupError:
        raise HTTPException(status_code=404, detail="Product not found")
    except FileExistsError:
        raise HTTPException(status_code=409, detail={"code": "duplicate_video", "message": "Video đã được gắn."})
    return {"video_id": video.video_id, "url": video.canonical_url, "refresh_status": video.refresh_status}


@router.post("/{video_id}/refresh")
async def refresh_product_video(product_id: int, video_id: str, db: Session = Depends(get_db)):
    try:
        ensure_product_is_available(db, product_id)
    except LookupError:
        raise HTTPException(status_code=404, detail="Product not found")
    link = db.scalar(select(ProductVideoLink).where(
        ProductVideoLink.product_id == product_id,
        ProductVideoLink.external_video_id == video_id,
    ))
    video = db.get(TikTokVideo, video_id)
    if link is None or video is None:
        raise HTTPException(status_code=404, detail="Video association not found")
    await refresh_video(video)
    db.commit()
    return {
        "video_id": video.video_id, "refresh_status": video.refresh_status,
        "refresh_message": video.refresh_message, "last_attempt_at": video.last_attempt_at,
    }


@router.delete("/{video_id}", status_code=status.HTTP_204_NO_CONTENT)
def detach_product_video(product_id: int, video_id: str, db: Session = Depends(get_db)):
    try:
        ensure_product_is_available(db, product_id)
    except LookupError:
        raise HTTPException(status_code=404, detail="Product not found")
    link = db.scalar(select(ProductVideoLink).where(
        ProductVideoLink.product_id == product_id,
        ProductVideoLink.external_video_id == video_id,
    ))
    if link is None:
        raise HTTPException(status_code=404, detail="Video association not found")
    db.delete(link)
    db.commit()
