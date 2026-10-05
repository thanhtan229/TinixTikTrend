from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import String, Integer, Float, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class AlertRule(Base):
    __tablename__ = "alert_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    rule_type: Mapped[str] = mapped_column(String(50), nullable=False)
    threshold: Mapped[float] = mapped_column(Float, nullable=False)
    direction: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    cooldown_minutes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    last_evaluated_snapshot_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    last_condition_met: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_triggered_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    product = relationship("Product", back_populates="alert_rules")
    events = relationship("AlertEvent", back_populates="rule", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_alert_rules_product_active", "product_id", "is_enabled"),
    )

    def __repr__(self) -> str:
        return f"<AlertRule(id={self.id}, product_id={self.product_id}, rule_type='{self.rule_type}', threshold={self.threshold})>"
