from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import String, Integer, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class CrawlRun(Base):
    __tablename__ = "crawl_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False, index=True)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    source: Mapped[str] = mapped_column(String(50), default="manual", nullable=False)  # manual, scheduled
    status: Mapped[str] = mapped_column(String(50), default="running", nullable=False)  # running, completed, partial, failed
    
    products_found: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    products_created: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    products_updated: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    snapshots_created: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    error_message: Mapped[Optional[str]] = mapped_column(String(2000), nullable=True)

    # Relationships
    snapshots: Mapped[List["ProductSnapshot"]] = relationship(
        "ProductSnapshot",
        back_populates="crawl_run",
    )

    def __repr__(self) -> str:
        return f"<CrawlRun(id={self.id}, status='{self.status}', found={self.products_found}, snapshots={self.snapshots_created})>"
