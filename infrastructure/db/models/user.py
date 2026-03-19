from sqlalchemy import Boolean, DateTime, Integer, String, func, text
from sqlalchemy.orm import mapped_column, relationship

from infrastructure.db.models.base import Base


class User(Base):
    __tablename__ = "users"

    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    email = mapped_column(String(255), unique=True, nullable=False, index=True)
    email_raw = mapped_column(String(255), nullable=True)
    phone = mapped_column(String(32), unique=True, nullable=False, index=True)
    phone_raw = mapped_column(String(32), nullable=True)
    contacts_enrichment_status = mapped_column(String(32), nullable=True)
    is_staff = mapped_column(Boolean, nullable=False, default=False, server_default=text("false"))
    password_hash = mapped_column(String(255), nullable=True)
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
    oauth_accounts = relationship(
        "OAuthAccount",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


