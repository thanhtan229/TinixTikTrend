from datetime import datetime, timezone
from typing import Dict, Any
from sqlalchemy import String, Integer, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


ALLOWED_SCOPES = {"trends", "watchlist"}


class SavedView(Base):
    __tablename__ = "saved_views"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    scope: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    payload_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    payload: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    def __repr__(self) -> str:
        return f"<SavedView(id={self.id}, name='{self.name}', scope='{self.scope}', v={self.payload_version})>"
