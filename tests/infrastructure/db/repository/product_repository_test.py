from decimal import Decimal

from infrastructure.db.models import Category, Product
from infrastructure.db.repositories import ProductRepository


def test_list_products_with_filters_sort_and_pagination(db_session):
    category = Category(name="coats")
    db_session.add(category)
    db_session.flush()

    db_session.add_all(
        [
            Product(name="A", description="a", price=Decimal("10.00"), category_id=category.id),
            Product(name="B", description="b", price=Decimal("50.00"), category_id=category.id),
            Product(name="C", description="c", price=Decimal("100.00"), category_id=category.id),
        ]
    )
    db_session.commit()

    repo = ProductRepository(session=db_session)

    products = repo.list(min_price=Decimal("20.00"), sort="price_desc", limit=1, offset=0)

    assert len(products) == 1
    assert products[0].name == "C"


def test_get_product_by_id(db_session):
    category = Category(name="hats")
    db_session.add(category)
    db_session.flush()
    product = Product(name="Hat", description="warm", price=Decimal("25.00"), category_id=category.id)
    db_session.add(product)
    db_session.commit()

    repo = ProductRepository(session=db_session)

    found = repo.get_by_id(product_id=product.id)

    assert found is not None
    assert found.name == "Hat"