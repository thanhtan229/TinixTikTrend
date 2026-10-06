from datetime import datetime, timezone
from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import String, Integer, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.watchlist import WatchlistItem
    from app.models.alert_rule import AlertRule
    from app.models.alert_event import AlertEvent
    from app.models.collection_item import CollectionItem


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    platform: Mapped[str] = mapped_column(String(50), default="tiktok_shop", nullable=False)
    external_product_id: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    
    title: Mapped[str] = mapped_column(String(500), index=True, nullable=False)
    url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    image_url: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    
    shop_id: Mapped[Optional[str]] = mapped_column(String(100), index=True, nullable=True)
    shop_name: Mapped[Optional[str]] = mapped_column(String(255), index=True, nullable=True)
    
    category: Mapped[Optional[str]] = mapped_column(String(255), index=True, nullable=True)
    
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False, index=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    snapshots: Mapped[List["ProductSnapshot"]] = relationship(
        "ProductSnapshot",
        back_populates="product",
        cascade="all, delete-orphan",
        order_by="ProductSnapshot.captured_at.asc()",
    )
    
    video_links: Mapped[List["ProductVideoLink"]] = relationship(
        "ProductVideoLink",
        back_populates="product",
        cascade="all, delete-orphan",
    )

    watchlist_item: Mapped[Optional["WatchlistItem"]] = relationship(
        "WatchlistItem",
        back_populates="product",
        uselist=False,
        cascade="all, delete-orphan",
    )

    alert_rules: Mapped[List["AlertRule"]] = relationship(
        "AlertRule",
        back_populates="product",
        cascade="all, delete-orphan",
    )

    alert_events: Mapped[List["AlertEvent"]] = relationship(
        "AlertEvent",
        back_populates="product",
        cascade="all, delete-orphan",
    )

    collection_items: Mapped[List["CollectionItem"]] = relationship(
        "CollectionItem",
        back_populates="product",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Product(id={self.id}, ext_id='{self.external_product_id}', title='{self.title[:30]}...')>"
