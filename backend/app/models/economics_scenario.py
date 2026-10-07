from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Integer, Boolean, DateTime, ForeignKey, Index, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.product import Product


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class EconomicsScenario(Base):
    __tablename__ = "economics_scenarios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    commission_rate_bps: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    commission_base_vnd: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    commission_base_source: Mapped[str] = mapped_column(String(32), default="user_entered", nullable=False)
    commission_base_observed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    sample_cost_vnd: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    content_cost_vnd: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    promotion_cost_vnd: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    variable_cost_per_attributed_order_vnd: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    expected_attributed_orders: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    product: Mapped["Product"] = relationship("Product", back_populates="economics_scenarios")

    __table_args__ = (
        UniqueConstraint("product_id", "name", name="uq_economics_scenarios_product_name"),
        Index("ix_economics_scenarios_product_id", "product_id"),
        Index(
            "uq_economics_scenarios_product_default",
            "product_id",
            unique=True,
            sqlite_where=text("is_default = 1"),
        ),
    )

    def __repr__(self) -> str:
        return f"<EconomicsScenario(id={self.id}, product_id={self.product_id}, name='{self.name}', is_default={self.is_default})>"
