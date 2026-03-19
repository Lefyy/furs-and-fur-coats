import importlib

router_module = importlib.import_module("app.routers.admin_product_description_router")
from app.routers.admin_product_description_router import (
    apply_product_description_generation,
    create_product_description_generation,
    get_latest_product_description_generation,
    retry_product_description_generation,
)
from app.services.product_description_generation_service import ProductDescriptionGenerationService
from infrastructure.db.repositories import ProductRepository
from infrastructure.db.repositories.product_description_generation_repository import ProductDescriptionGenerationRepository


class StubOpenRouterGateway:
    def generate_product_description(self, *, messages: list[dict[str, str]]) -> str:
        return "Сгенерированное описание"


class DelaySpy:
    def __init__(self) -> None:
        self.calls: list[int] = []

    def __call__(self, generation_id: int) -> None:
        self.calls.append(generation_id)


def _build_service(db_session):
    return ProductDescriptionGenerationService(
        product_repository=ProductRepository(db_session),
        generation_repository=ProductDescriptionGenerationRepository(db_session),
        openrouter_gateway=StubOpenRouterGateway(),
    )


def test_admin_product_description_router_create_latest_apply_and_retry(db_session, category_factory, product_factory, monkeypatch):
    category = category_factory()
    db_session.add(category)
    db_session.flush()
    product = product_factory(category_id=category.id, description="Старое")
    db_session.add(product)
    db_session.commit()

    service = _build_service(db_session)
    delay_spy = DelaySpy()
    monkeypatch.setattr(router_module.generate_product_description, "delay", delay_spy)

    created = create_product_description_generation(product_id=product.id, service=service)
    created_status = created.status
    latest = get_latest_product_description_generation(product_id=product.id, service=service)
    service.generate_text(generation_id=created.id)
    applied = apply_product_description_generation(product_id=product.id, generation_id=created.id, service=service)
    retried = retry_product_description_generation(product_id=product.id, generation_id=created.id, service=service)

    assert created_status == "queued"
    assert latest.id == created.id
    assert applied.status == "applied"
    assert retried.status == "queued"
    assert delay_spy.calls == [created.id, retried.id]
