from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, Integer, Float, Boolean, DateTime, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class AlertEvent(Base):
    __tablename__ = "alert_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    rule_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("alert_rules.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    product_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    triggering_snapshot_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("product_snapshots.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    rule_type: Mapped[str] = mapped_column(String(50), nullable=False)
    threshold: Mapped[float] = mapped_column(Float, nullable=False)
    actual_value: Mapped[float] = mapped_column(Float, nullable=False)
    actual_direction: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    message: Mapped[str] = mapped_column(String(500), nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    rule = relationship("AlertRule", back_populates="events")
    product = relationship("Product", back_populates="alert_events")
    triggering_snapshot = relationship("ProductSnapshot")

    __table_args__ = (
        UniqueConstraint("rule_id", "triggering_snapshot_id", name="uq_alert_events_rule_snapshot"),
        Index("ix_alert_events_unread_created", "is_read", "created_at"),
        Index("ix_alert_events_product_created", "product_id", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<AlertEvent(id={self.id}, rule_id={self.rule_id}, product_id={self.product_id}, is_read={self.is_read})>"
