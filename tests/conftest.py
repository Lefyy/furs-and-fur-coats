from collections.abc import Generator
from decimal import Decimal
from pathlib import Path
import sys

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from infrastructure.db import models
from infrastructure.db.models import Category, OrderStatus, OrderStatusName, Product, User
from infrastructure.db.models.base import Base


@pytest.fixture()
def db_session() -> Generator[Session, None, None]:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(bind=engine)
    session_local = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)

    session = session_local()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture()
def user_factory() -> callable:
    counter = 0

    def factory(**overrides) -> User:
        nonlocal counter
        counter += 1
        defaults = {
            "email": f"user{counter}@example.com",
            "email_raw": f"User{counter}@Example.com",
            "phone": f"79990000{counter:03d}",
            "phone_raw": f"+7 (999) 000-0{counter:03d}",
            "contacts_enrichment_status": "pending",
            "password_hash": "hash",
            "is_staff": False,
        }
        defaults.update(overrides)
        return User(**defaults)

    return factory


@pytest.fixture()
def product_factory() -> callable:
    counter = 0

    def factory(category_id: int, **overrides) -> Product:
        nonlocal counter
        counter += 1
        defaults = {
            "name": f"Product {counter}",
            "description": f"Description {counter}",
            "old_description": f"Legacy description {counter}",
            "brand": "FurHouse",
            "fur_type": "mink",
            "color": "black",
            "length": "midi",
            "size_range": "42-48",
            "features": ["hood", "belt"],
            "material_composition": "100% natural fur",
            "target_audience": "women",
            "season": "winter",
            "style_tags": ["classic", "premium"],
            "price": Decimal("100.00"),
            "category_id": category_id,
        }
        defaults.update(overrides)
        return Product(**defaults)

    return factory


@pytest.fixture()
def order_status_factory() -> callable:
    def factory(**overrides) -> OrderStatus:
        defaults = {"name": OrderStatusName.CREATED.value}
        defaults.update(overrides)
        return OrderStatus(**defaults)

    return factory


@pytest.fixture()
def category_factory() -> callable:
    counter = 0

    def factory(**overrides) -> Category:
        nonlocal counter
        counter += 1
        defaults = {"name": f"Category {counter}"}
        defaults.update(overrides)
        return Category(**defaults)

    return factory


