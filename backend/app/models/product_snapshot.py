from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import Integer, Float, DateTime, Boolean, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ProductSnapshot(Base):
    __tablename__ = "product_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    crawl_run_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("crawl_runs.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    
    captured_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
        index=True,
    )
    
    # Core Pricing & Metric snapshots (all nullable to never fabricate missing data)
    price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    original_price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    sold_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    review_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    rating: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    stock_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    rank_position: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Creator & Video Intelligence counts (future-ready)
    creator_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    video_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Affiliate potential
    commission_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Data quality flags
    is_partial: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_anomaly: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    product: Mapped["Product"] = relationship("Product", back_populates="snapshots")
    crawl_run: Mapped[Optional["CrawlRun"]] = relationship("CrawlRun", back_populates="snapshots")

    __table_args__ = (
        Index("ix_product_snapshots_product_captured", "product_id", "captured_at"),
    )

    def __repr__(self) -> str:
        return f"<ProductSnapshot(id={self.id}, product_id={self.product_id}, sold={self.sold_count}, captured_at='{self.captured_at}')>"
