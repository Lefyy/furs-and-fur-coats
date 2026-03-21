from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from infrastructure.db.models import ProductDescriptionGeneration
from infrastructure.db.repositories.base import BaseRepository


ACTIVE_GENERATION_STATUSES = ("queued", "processing")


class ProductDescriptionGenerationRepository(BaseRepository):
    def __init__(self, session: Session) -> None:
        super().__init__(session)

    def create(self, *, product_id: int, status: str = "queued") -> ProductDescriptionGeneration:
        generation = ProductDescriptionGeneration(product_id=product_id, status=status)
        self.session.add(generation)
        self.flush()
        return generation

    def get_by_id(self, generation_id: int) -> ProductDescriptionGeneration | None:
        stmt = select(ProductDescriptionGeneration).where(ProductDescriptionGeneration.id == generation_id)
        return self.session.scalar(stmt)

    def get_latest_by_product_id(self, product_id: int) -> ProductDescriptionGeneration | None:
        stmt = (
            select(ProductDescriptionGeneration)
            .where(ProductDescriptionGeneration.product_id == product_id)
            .order_by(desc(ProductDescriptionGeneration.created_at), desc(ProductDescriptionGeneration.id))
            .limit(1)
        )
        return self.session.scalar(stmt)

    def update_status(
        self,
        *,
        generation_id: int,
        status: str,
        error_message: str | None = None,
        started_at: datetime | None = None,
        completed_at: datetime | None = None,
    ) -> ProductDescriptionGeneration | None:
        generation = self.get_by_id(generation_id)
        if generation is None:
            return None

        generation.status = status
        generation.error_message = error_message
        if started_at is not None:
            generation.started_at = started_at
        if completed_at is not None:
            generation.completed_at = completed_at
        self.flush()
        return generation

    def save_generation_result(
        self,
        *,
        generation_id: int,
        generated_text: str,
        model_name: str,
        prompt_version: str,
        status: str = "completed",
    ) -> ProductDescriptionGeneration | None:
        generation = self.get_by_id(generation_id)
        if generation is None:
            return None

        generation.generated_text = generated_text
        generation.model_name = model_name
        generation.prompt_version = prompt_version
        generation.status = status
        generation.error_message = None
        generation.completed_at = datetime.now(timezone.utc)
        self.flush()
        return generation

    def mark_as_applied(self, *, generation_id: int) -> ProductDescriptionGeneration | None:
        generation = self.get_by_id(generation_id)
        if generation is None:
            return None

        generation.status = "applied"
        generation.completed_at = generation.completed_at or datetime.now(timezone.utc)
        self.flush()
        return generation

    def has_active_generation(self, *, product_id: int) -> bool:
        stmt = (
            select(ProductDescriptionGeneration.id)
            .where(ProductDescriptionGeneration.product_id == product_id)
            .where(ProductDescriptionGeneration.status.in_(ACTIVE_GENERATION_STATUSES))
            .limit(1)
        )
        return self.session.scalar(stmt) is not None