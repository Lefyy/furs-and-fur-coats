from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import mapped_column, relationship

from infrastructure.db.base import Base


class Category(Base):
    __tablename__ = "categories"

    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    name = mapped_column(String(255), nullable=False)
    parent_id = mapped_column(ForeignKey("categories.id"), nullable=True)

    parent = relationship("Category", remote_side=[id], back_populates="children", lazy="selectin")
    children = relationship(
        "Category",
        back_populates="parent",
        cascade="all, delete-orphan",
        single_parent=True,
        lazy="selectin",
    )
    products = relationship("Product", back_populates="category", lazy="selectin")

