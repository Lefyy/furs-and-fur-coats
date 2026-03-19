from __future__ import annotations

from infrastructure.tasks_queue.celery_app import CELERY_TASK_DEFAULTS, celery_app
from app.config import settings
from app.gateways.openrouter import OpenRouterGateway
from app.utils.redis_lock import redis_lock


openrouter_gateway = OpenRouterGateway()


@celery_app.task(name="app.tasks.product_description.generate", bind=True, **CELERY_TASK_DEFAULTS)
def generate_product_description(self, product_id: int, product_name: str, attributes: dict | None = None) -> dict[str, str | int]:
    lock_key = f"product-description:{product_id}"
    with redis_lock(lock_key, ttl_seconds=settings.generation_lock_ttl_seconds):
        description = openrouter_gateway.generate_product_description(
            product_name=product_name,
            attributes=attributes or {},
        )

    return {
        "product_id": product_id,
        "description": description,
        "prompt_version": settings.openrouter_prompt_version,
    }
