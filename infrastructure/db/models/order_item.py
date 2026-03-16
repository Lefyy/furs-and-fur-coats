from sqlalchemy import CheckConstraint, ForeignKey, Numeric
from sqlalchemy.orm import mapped_column, relationship

from infrastructure.db.base import Base


class OrderItem(Base):
    __tablename__ = "order_items"
    __table_args__ = (CheckConstraint("quantity > 0", name="ck_order_items_quantity_positive"),)

    id = mapped_column(primary_key=True, autoincrement=True)
    order_id = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = mapped_column(ForeignKey("products.id"), nullable=False, index=True)
    quantity = mapped_column(nullable=False)
    price = mapped_column(Numeric(10, 2), nullable=False)

    order = relationship("Order", back_populates="items", lazy="selectin")
    product = relationship("Product", back_populates="order_items", lazy="selectin")

