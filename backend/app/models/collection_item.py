from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Integer, DateTime, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.collection import Collection
    from app.models.product import Product


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


ALLOWED_REVIEW_STATUSES = {"new", "reviewing", "candidate", "rejected"}


class CollectionItem(Base):
    __tablename__ = "collection_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    collection_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("collections.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    product_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
    )
    review_status: Mapped[str] = mapped_column(String(50), default="new", nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(String(2000), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    collection: Mapped["Collection"] = relationship("Collection", back_populates="items")
    product: Mapped["Product"] = relationship("Product", back_populates="collection_items")

    __table_args__ = (
        UniqueConstraint("collection_id", "product_id", name="uq_collection_items_collection_product"),
        Index("ix_collection_items_product_id", "product_id"),
    )

    def __repr__(self) -> str:
        return f"<CollectionItem(id={self.id}, collection_id={self.collection_id}, product_id={self.product_id}, status='{self.review_status}')>"
