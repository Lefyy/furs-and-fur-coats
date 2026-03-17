from sqlalchemy import DateTime, ForeignKey, Integer, func
from sqlalchemy.orm import mapped_column, relationship

from infrastructure.db.base import Base


class Cart(Base):
    __tablename__ = "carts"

    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id = mapped_column(ForeignKey("users.id"), nullable=False, unique=True, index=True)
    modified_at = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    user = relationship("User", back_populates="cart", lazy="selectin")
    items = relationship(
        "CartItem",
        back_populates="cart",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

