from __future__ import annotations

from infrastructure.tasks_queue.celery_app import CELERY_TASK_DEFAULTS, celery_app
from app.gateways.dadata import DadataGateway


dadata_gateway = DadataGateway()


@celery_app.task(name="app.tasks.enrichment.enrich_contact_details", bind=True, **CELERY_TASK_DEFAULTS)
def enrich_contact_details(self, payload: dict[str, str]) -> dict[str, dict]:
    return dadata_gateway.clean_contact_record(
        email=payload.get("email", ""),
        phone=payload.get("phone", ""),
        address=payload.get("address", ""),
    )
