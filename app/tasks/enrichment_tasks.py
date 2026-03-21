from __future__ import annotations

from app.gateways.dadata import DadataGateway
from app.services.address_formatting_service import AddressFormattingService
from app.services.contact_formatting_service import ContactFormattingService
from infrastructure.db.db_session import SessionLocal
from infrastructure.db.repositories import OrderRepository, UserRepository
from infrastructure.tasks_queue.celery_app import CELERY_TASK_DEFAULTS, celery_app


dadata_gateway = DadataGateway()
contact_formatting_service = ContactFormattingService(dadata_gateway=dadata_gateway)
address_formatting_service = AddressFormattingService(dadata_gateway=dadata_gateway)


@celery_app.task(name="app.tasks.enrichment.enrich_contact_details", bind=True, **CELERY_TASK_DEFAULTS)
def enrich_contact_details(self, payload: dict[str, str]) -> dict[str, dict]:
    return dadata_gateway.clean_contact_record(
        email=payload.get("email", ""),
        phone=payload.get("phone", ""),
        address=payload.get("address", ""),
    )

@celery_app.task(name="app.tasks.enrichment.enrich_user_contacts", bind=True, **CELERY_TASK_DEFAULTS)
def enrich_user_contacts(self, user_id: int) -> dict[str, str] | None:
    with SessionLocal() as session:
        repository = UserRepository(session=session)
        user = repository.get_by_id(user_id=user_id)
        if user is None:
            return None

        result = contact_formatting_service.format(email=user.email_raw or user.email, phone=user.phone_raw or user.phone)
        repository.update_contact_enrichment(
            user_id=user_id,
            email=result.email.canonical,
            phone=result.phone.canonical,
            contacts_enrichment_status=result.status,
        )
        return {"email": result.email.canonical, "phone": result.phone.canonical, "status": result.status}


@celery_app.task(name="app.tasks.enrichment.enrich_order_address", bind=True, **CELERY_TASK_DEFAULTS)
def enrich_order_address(self, order_id: int) -> dict[str, str | None] | None:
    with SessionLocal() as session:
        repository = OrderRepository(session=session)
        order = repository.get_by_id(order_id=order_id)
        if order is None:
            return None

        result = address_formatting_service.format(address=order.address_raw or order.address)
        repository.update_address_enrichment(
            order_id=order_id,
            address=result.canonical,
            postal_code=result.postal_code,
            address_metadata=result.metadata,
            address_enrichment_status=result.status,
        )
        return {"address": result.canonical, "postal_code": result.postal_code, "status": result.status}

