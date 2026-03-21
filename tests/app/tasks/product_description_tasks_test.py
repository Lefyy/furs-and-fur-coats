from contextlib import contextmanager

from app.tasks.product_description_tasks import generate_product_description
from app.utils.redis_lock import RedisLockError
from infrastructure.db.repositories.product_description_generation_repository import ProductDescriptionGenerationRepository


class StubService:
    def __init__(self, *, should_fail: bool = False) -> None:
        self.should_fail = should_fail

    def generate_text(self, *, generation_id: int):
        if self.should_fail:
            raise RuntimeError("boom")
        return type("Result", (), {"generation": type("Generation", (), {"id": generation_id, "status": "completed"})(), "product": type("Product", (), {"id": 1})()})


@contextmanager
def _noop_lock(*args, **kwargs):
    yield "token"


@contextmanager
def _busy_lock(*args, **kwargs):
    raise RedisLockError("lock busy")
    yield


def test_generate_product_description_task_completes(db_session, category_factory, product_factory, monkeypatch):
    category = category_factory()
    db_session.add(category)
    db_session.flush()
    product = product_factory(category_id=category.id)
    db_session.add(product)
    db_session.commit()

    repository = ProductDescriptionGenerationRepository(db_session)
    generation = repository.run_in_transaction(lambda: repository.create(product_id=product.id, status="queued"))

    monkeypatch.setattr("app.tasks.product_description_tasks.SessionLocal", lambda: db_session)
    monkeypatch.setattr("app.tasks.product_description_tasks.product_description_generation_lock.acquire", _noop_lock)
    monkeypatch.setattr("app.tasks.product_description_tasks.ProductDescriptionGenerationService", lambda **kwargs: StubService())

    result = generate_product_description.run(generation.id)
    updated = repository.get_by_id(generation.id)

    assert result == {"generation_id": generation.id, "product_id": product.id, "status": "completed"}
    assert updated is not None
    assert updated.status == "processing"


def test_generate_product_description_task_marks_failed_when_lock_is_busy(db_session, category_factory, product_factory, monkeypatch):
    category = category_factory()
    db_session.add(category)
    db_session.flush()
    product = product_factory(category_id=category.id)
    db_session.add(product)
    db_session.commit()

    repository = ProductDescriptionGenerationRepository(db_session)
    generation = repository.run_in_transaction(lambda: repository.create(product_id=product.id, status="queued"))

    monkeypatch.setattr("app.tasks.product_description_tasks.SessionLocal", lambda: db_session)
    monkeypatch.setattr("app.tasks.product_description_tasks.product_description_generation_lock.acquire", _busy_lock)
    monkeypatch.setattr("app.tasks.product_description_tasks.ProductDescriptionGenerationService", lambda **kwargs: StubService())

    result = generate_product_description.run(generation.id)
    updated = repository.get_by_id(generation.id)

    assert result == {"generation_id": generation.id, "product_id": product.id, "status": "failed"}
    assert updated is not None
    assert updated.status == "failed"
    assert updated.error_message == "lock busy"