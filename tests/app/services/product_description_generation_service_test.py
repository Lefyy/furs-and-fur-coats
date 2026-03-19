from app.exceptions import BadRequestError
from app.services.product_description_generation_service import ProductDescriptionGenerationService
from infrastructure.db.repositories import ProductRepository
from infrastructure.db.repositories.product_description_generation_repository import ProductDescriptionGenerationRepository


class StubOpenRouterGateway:
    def __init__(self, text: str = "Generated text") -> None:
        self.text = text
        self.messages: list[dict[str, str]] | None = None

    def generate_product_description(self, *, messages: list[dict[str, str]]) -> str:
        self.messages = messages
        return self.text


def test_product_description_generation_service_generate_and_apply(db_session, category_factory, product_factory):
    category = category_factory()
    db_session.add(category)
    db_session.flush()
    product = product_factory(category_id=category.id, description="Old description")
    db_session.add(product)
    db_session.commit()

    gateway = StubOpenRouterGateway(text="Новое описание")
    service = ProductDescriptionGenerationService(
        product_repository=ProductRepository(db_session),
        generation_repository=ProductDescriptionGenerationRepository(db_session),
        openrouter_gateway=gateway,
    )

    generation = service.create_generation(product_id=product.id)
    result = service.generate_text(generation_id=generation.id)
    completed_status = result.generation.status
    completed_text = result.generation.generated_text
    applied = service.apply_generation(product_id=product.id, generation_id=generation.id)

    db_session.refresh(product)
    assert completed_status == "completed"
    assert completed_text == "Новое описание"
    assert gateway.messages is not None
    assert "Product name" in gateway.messages[1]["content"]
    assert product.old_description == "Old description"
    assert product.description == "Новое описание"
    assert applied.status == "applied"


def test_product_description_generation_service_prevents_duplicate_active_generation(db_session, category_factory, product_factory):
    category = category_factory()
    db_session.add(category)
    db_session.flush()
    product = product_factory(category_id=category.id)
    db_session.add(product)
    db_session.commit()

    service = ProductDescriptionGenerationService(
        product_repository=ProductRepository(db_session),
        generation_repository=ProductDescriptionGenerationRepository(db_session),
        openrouter_gateway=StubOpenRouterGateway(),
    )

    service.create_generation(product_id=product.id)

    try:
        service.create_generation(product_id=product.id)
    except BadRequestError as exc:
        assert exc.detail["code"] == "bad_request"
    else:
        raise AssertionError("Expected BadRequestError")


def test_product_description_generation_service_retry_creates_new_generation(db_session, category_factory, product_factory):
    category = category_factory()
    db_session.add(category)
    db_session.flush()
    product = product_factory(category_id=category.id)
    db_session.add(product)
    db_session.commit()

    repository = ProductDescriptionGenerationRepository(db_session)
    generation = repository.run_in_transaction(lambda: repository.create(product_id=product.id, status="failed"))
    service = ProductDescriptionGenerationService(
        product_repository=ProductRepository(db_session),
        generation_repository=repository,
        openrouter_gateway=StubOpenRouterGateway(),
    )

    retried = service.retry_generation(product_id=product.id, generation_id=generation.id)

    assert retried.id != generation.id
    assert retried.status == "queued"