from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import mapped_column, relationship

from infrastructure.db.models.base import Base


class ProductDescriptionGeneration(Base):
    __tablename__ = "product_description_generations"

    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_id = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    status = mapped_column(String(32), nullable=False)
    generated_text = mapped_column(Text, nullable=True)
    model_name = mapped_column(String(255), nullable=True)
    prompt_version = mapped_column(String(64), nullable=True)
    error_message = mapped_column(Text, nullable=True)
    created_at = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    started_at = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at = mapped_column(DateTime(timezone=True), nullable=True)

    product = relationship("Product", back_populates="description_generations", lazy="selectin")
