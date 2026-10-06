from datetime import datetime, timezone
from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import String, Integer, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.collection_item import CollectionItem


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Collection(Base):
    __tablename__ = "collections"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    items: Mapped[List["CollectionItem"]] = relationship(
        "CollectionItem",
        back_populates="collection",
        cascade="all, delete-orphan",
        order_by="CollectionItem.created_at.asc()",
    )

    def __repr__(self) -> str:
        return f"<Collection(id={self.id}, name='{self.name}')>"
