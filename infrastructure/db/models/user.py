from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import mapped_column, relationship

from infrastructure.db.base import Base


class User(Base):
    __tablename__ = "users"

    id = mapped_column(primary_key=True, autoincrement=True)
    email = mapped_column(String(255), unique=True, nullable=False, index=True)
    phone = mapped_column(String(32), unique=True, nullable=False, index=True)
    password_hash = mapped_column(String(255), nullable=False)
    created_at = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    cart = relationship(
        "Cart",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
        single_parent=True,
        lazy="selectin",
    )
    orders = relationship(
        "Order",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

