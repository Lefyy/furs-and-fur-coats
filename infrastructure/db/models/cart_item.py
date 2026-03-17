from sqlalchemy import CheckConstraint, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import mapped_column, relationship

from infrastructure.db.base import Base


class CartItem(Base):
    __tablename__ = "cart_items"
    __table_args__ = (
        UniqueConstraint("cart_id", "product_id", name="uq_cart_items_cart_product"),
        CheckConstraint("quantity > 0", name="ck_cart_items_quantity_positive"),
    )

    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    cart_id = mapped_column(ForeignKey("carts.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = mapped_column(ForeignKey("products.id"), nullable=False, index=True)
    quantity = mapped_column(Integer, nullable=False, default=1)

    cart = relationship("Cart", back_populates="items", lazy="selectin")
    product = relationship("Product", back_populates="cart_items", lazy="selectin")

