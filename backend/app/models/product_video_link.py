from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, Integer, Float, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ProductVideoLink(Base):
    """
    Mapping model linking TikTok Shop Products to TikTok Videos/Creators with confidence scoring.
    """
    __tablename__ = "product_video_links"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    external_video_id: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    creator_id: Mapped[Optional[str]] = mapped_column(String(100), index=True, nullable=True)
    
    source: Mapped[str] = mapped_column(String(50), default="product_page", nullable=False)  # product_page, creator_page, video_metadata, heuristic
    confidence: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    product: Mapped["Product"] = relationship("Product", back_populates="video_links")

    __table_args__ = (
        Index("ix_pvl_product_video", "product_id", "external_video_id"),
    )

    def __repr__(self) -> str:
        return f"<ProductVideoLink(product_id={self.product_id}, video_id='{self.external_video_id}', conf={self.confidence})>"
