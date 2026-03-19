from sqlalchemy.orm import mapped_column, relationship
from sqlalchemy import JSON, DateTime, ForeignKey, Integer, Numeric, String, Text, func

from infrastructure.db.models.base import Base


class Product(Base):
    __tablename__ = "products"

    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    name = mapped_column(String(255), nullable=False)
    description = mapped_column(Text, nullable=True)
    old_description = mapped_column(Text, nullable=True)
    brand = mapped_column(String(255), nullable=True)
    fur_type = mapped_column(String(255), nullable=True)
    color = mapped_column(String(255), nullable=True)
    length = mapped_column(String(255), nullable=True)
    size_range = mapped_column(String(255), nullable=True)
    features = mapped_column(JSON, nullable=True)
    material_composition = mapped_column(Text, nullable=True)
    target_audience = mapped_column(String(255), nullable=True)
    season = mapped_column(String(255), nullable=True)
    style_tags = mapped_column(JSON, nullable=True)
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
    description_generations = relationship(
        "ProductDescriptionGeneration",
        back_populates="product",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

