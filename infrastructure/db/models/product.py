from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import mapped_column, relationship

from infrastructure.db.base import Base


class Product(Base):
    __tablename__ = "products"

    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    name = mapped_column(String(255), nullable=False)
    description = mapped_column(Text, nullable=False)
    price = mapped_column(Numeric(10, 2), nullable=False)
    category_id = mapped_column(ForeignKey("categories.id"), nullable=False, index=True)
    image_url = mapped_column(String(2048), nullable=True)
    created_at = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    modified_at = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    category = relationship("Category", back_populates="products", lazy="selectin")
    cart_items = relationship("CartItem", back_populates="product", lazy="selectin")
    order_items = relationship("OrderItem", back_populates="product", lazy="selectin")

