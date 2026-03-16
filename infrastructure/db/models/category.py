from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import mapped_column, relationship

from infrastructure.db.base import Base


class Category(Base):
    __tablename__ = "categories"

    id = mapped_column(primary_key=True, autoincrement=True)
    name = mapped_column(String(255), nullable=False)
    parent_id = mapped_column(ForeignKey("categories.id"), nullable=True)

    parent = relationship("Category", remote_side=[id], back_populates="children")
    children = relationship("Category", back_populates="parent")
    products = relationship("Product", back_populates="category")
