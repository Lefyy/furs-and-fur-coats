from sqlalchemy import func, select

from infrastructure.db.models import Category, Product, User
from app.scripts.seed_data import ensure_categories, ensure_products, ensure_superuser


def test_seed_helpers_create_superuser_and_fill_products(db_session, monkeypatch):
    monkeypatch.setattr("scripts.seed_data.DEFAULT_ADMIN_EMAIL", "boss@example.com")
    monkeypatch.setattr("scripts.seed_data.DEFAULT_ADMIN_PHONE", "79991112233")
    monkeypatch.setattr("scripts.seed_data.DEFAULT_ADMIN_PASSWORD", "secret123")

    categories = ensure_categories(db_session)
    admin = ensure_superuser(db_session)
    created_products = ensure_products(db_session, categories)

    assert len(categories) == 6
    assert admin.email == "boss@example.com"
    assert admin.is_staff is True
    assert created_products == 100
    assert db_session.scalar(select(func.count(Product.id))) == 100
    assert db_session.scalar(select(func.count(Category.id))) == 9
    assert db_session.scalar(select(func.count(User.id))) == 1


def test_seed_helpers_are_idempotent(db_session, monkeypatch):
    monkeypatch.setattr("scripts.seed_data.DEFAULT_ADMIN_EMAIL", "boss@example.com")
    monkeypatch.setattr("scripts.seed_data.DEFAULT_ADMIN_PHONE", "79991112233")
    monkeypatch.setattr("scripts.seed_data.DEFAULT_ADMIN_PASSWORD", "secret123")

    categories = ensure_categories(db_session)
    ensure_superuser(db_session)
    ensure_products(db_session, categories)

    categories = ensure_categories(db_session)
    admin = ensure_superuser(db_session)
    created_products = ensure_products(db_session, categories)

    assert admin.is_staff is True
    assert created_products == 0
    assert db_session.scalar(select(func.count(Product.id))) == 100