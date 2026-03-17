from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, Text, func
from sqlalchemy.orm import mapped_column, relationship

from infrastructure.db.models.base import Base


class Order(Base):
    __tablename__ = "orders"

    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    status_id = mapped_column(ForeignKey("order_statuses.id"), nullable=False, index=True)
    total_price = mapped_column(Numeric(10, 2), nullable=False)
    address = mapped_column(Text, nullable=False)
    created_at = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user = relationship("User", back_populates="orders", lazy="selectin")
    status = relationship("OrderStatus", back_populates="orders", lazy="selectin")
    items = relationship(
        "OrderItem",
        back_populates="order",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

