from sqlalchemy import Integer, String
from sqlalchemy.orm import mapped_column, relationship

from infrastructure.db.models.base import Base


class OrderStatus(Base):
    __tablename__ = "order_statuses"

    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    name = mapped_column(String(32), nullable=False, unique=True)

    orders = relationship("Order", back_populates="status", lazy="selectin")
