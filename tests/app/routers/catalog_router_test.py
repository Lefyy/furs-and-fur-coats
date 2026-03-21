from decimal import Decimal

from app.routers.catalog_router import get_product, get_products
from app.services import CatalogService
from infrastructure.db.models import Category, Product
from infrastructure.db.repositories import CategoryRepository, ProductRepository


def test_catalog_router_handlers(db_session):
    category = Category(name="fur")
    db_session.add(category)
    db_session.flush()
    product = Product(name="Mink", description="warm", price=Decimal("500.00"), category_id=category.id)
    db_session.add(product)
    db_session.commit()

    service = CatalogService(ProductRepository(db_session), CategoryRepository(db_session))

    products_response = get_products(
        min_price=None,
        max_price=None,
        category_id=None,
        sort=None,
        limit=20,
        offset=0,
        service=service,
    )
    assert products_response.items[0].name == "Mink"

    product_response = get_product(product_id=product.id, service=service)
    assert product_response.id == product.id