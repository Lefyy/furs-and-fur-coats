from __future__ import annotations

from datetime import datetime, timezone
from app.config import settings
from app.gateways.openrouter import OpenRouterGateway
from app.services.product_description_generation_service import ProductDescriptionGenerationService
from app.utils.redis_lock import RedisLockError, product_description_generation_lock
from infrastructure.db.db_session import SessionLocal
from infrastructure.db.repositories import ProductRepository
from infrastructure.db.repositories.product_description_generation_repository import ProductDescriptionGenerationRepository
from infrastructure.tasks_queue.celery_app import CELERY_TASK_DEFAULTS, celery_app


@celery_app.task(name="app.tasks.product_description.generate", bind=True, **CELERY_TASK_DEFAULTS)
def generate_product_description(self, generation_id: int) -> dict[str, str | int] | None:
    with SessionLocal() as session:
        product_repository = ProductRepository(session=session)
        generation_repository = ProductDescriptionGenerationRepository(session=session)
        service = ProductDescriptionGenerationService(
            product_repository=product_repository,
            generation_repository=generation_repository,
            openrouter_gateway=OpenRouterGateway(),
        )

        generation = generation_repository.get_by_id(generation_id)
        if generation is None:
            return None

        started_at = datetime.now(timezone.utc)
        try:
            with product_description_generation_lock.acquire(
                str(generation.product_id),
                ttl_seconds=settings.generation_lock_ttl_seconds,
            ):
                generation_repository.run_in_transaction(
                    lambda: generation_repository.update_status(
                        generation_id=generation_id,
                        status="processing",
                        error_message=None,
                        started_at=started_at,
                    )
                )
                result = service.generate_text(generation_id=generation_id)
                return {
                    "generation_id": result.generation.id,
                    "product_id": result.product.id,
                    "status": result.generation.status,
                }
        except RedisLockError as exc:
            generation_repository.run_in_transaction(
                lambda: generation_repository.update_status(
                    generation_id=generation_id,
                    status="failed",
                    error_message=str(exc),
                    completed_at=datetime.now(timezone.utc),
                )
            )
            return {"generation_id": generation_id, "product_id": generation.product_id, "status": "failed"}
        except Exception as exc:
            generation_repository.run_in_transaction(
                lambda: generation_repository.update_status(
                    generation_id=generation_id,
                    status="failed",
                    error_message=str(exc),
                    completed_at=datetime.now(timezone.utc),
                )
            )
            raise
