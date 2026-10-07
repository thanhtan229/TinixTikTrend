from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class TikTokVideo(Base):
    __tablename__ = "tiktok_videos"

    video_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    canonical_url: Mapped[str] = mapped_column(String(512), nullable=False)
    creator_handle: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    creator_name: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    thumbnail_url: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    last_attempt_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    refresh_status: Mapped[str] = mapped_column(String(32), default="not_refreshed", nullable=False)
    refresh_message: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    snapshots: Mapped[list["VideoSnapshot"]] = relationship(
        "VideoSnapshot", back_populates="video", cascade="all, delete-orphan"
    )


class VideoSnapshot(Base):
    __tablename__ = "video_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    video_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("tiktok_videos.video_id", ondelete="RESTRICT"), nullable=False
    )
    view_count: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    like_count: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    comment_count: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    share_count: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    collect_count: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    source: Mapped[str] = mapped_column(String(32), nullable=False)
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    video: Mapped[TikTokVideo] = relationship("TikTokVideo", back_populates="snapshots")

    __table_args__ = (
        Index("ix_video_snapshots_video_captured", "video_id", captured_at.desc()),
    )
