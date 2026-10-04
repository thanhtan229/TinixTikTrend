from datetime import datetime, timezone
from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class QuarantinedProduct(Base):
    """Retain contaminated historical records without using them as live signals."""
    __tablename__ = "quarantined_products"
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey("products.id"), primary_key=True)
    reason: Mapped[str] = mapped_column(String(500), nullable=False)
    quarantined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
