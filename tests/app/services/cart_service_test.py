from decimal import Decimal

import pytest

from app.exceptions import NotFoundError
from app.services import CartService
from infrastructure.db.models import Category, Product, User
from infrastructure.db.repositories import CartRepository, ProductRepository


def test_cart_service_add_and_get(db_session):
    user = User(email="svc@example.com", phone="79991111111", password_hash="hash")
    category = Category(name="cat")
    db_session.add_all([user, category])
    db_session.flush()
    product = Product(name="Coat", description="desc", price=Decimal("120.00"), category_id=category.id)
    db_session.add(product)
    db_session.commit()

    service = CartService(CartRepository(db_session), ProductRepository(db_session))

    response = service.add_item(user_id=user.id, product_id=product.id, quantity=2)

    assert response.total_price == Decimal("240.00")
    assert len(response.items) == 1


def test_cart_service_update_nonexistent_item(db_session):
    service = CartService(CartRepository(db_session), ProductRepository(db_session))

    with pytest.raises(NotFoundError):
        service.update_item(user_id=1, product_id=10, quantity=2)
