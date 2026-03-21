from decimal import Decimal

import pytest

from app.exceptions import BadRequestError, NotFoundError
from app.services import CatalogService
from infrastructure.db.models import Category, Product
from infrastructure.db.repositories import CategoryRepository, ProductRepository


def test_catalog_service_list_products(db_session):
    category = Category(name="coats")
    db_session.add(category)
    db_session.flush()
    db_session.add_all(
        [
            Product(name="A", description="a", price=Decimal("100.00"), category_id=category.id),
            Product(name="B", description="b", price=Decimal("200.00"), category_id=category.id),
        ]
    )
    db_session.commit()

    service = CatalogService(ProductRepository(db_session), CategoryRepository(db_session))

    response = service.list_products(
        min_price=Decimal("150.00"),
        max_price=None,
        category_id=category.id,
        sort="price_desc",
        limit=10,
        offset=0,
    )

    assert len(response.items) == 1
    assert response.items[0].name == "B"


def test_catalog_service_get_product_not_found(db_session):
    service = CatalogService(ProductRepository(db_session), CategoryRepository(db_session))

    with pytest.raises(NotFoundError):
        service.get_product(product_id=123)


def test_catalog_service_rejects_invalid_prices(db_session):
    service = CatalogService(ProductRepository(db_session), CategoryRepository(db_session))

    with pytest.raises(BadRequestError):
        service.list_products(
            min_price=Decimal("10"),
            max_price=Decimal("1"),
            category_id=None,
            sort=None,
            limit=10,
            offset=0,
        )
