from decimal import Decimal

from infrastructure.db.models import Category, Product, User
from infrastructure.db.repositories import CartRepository


def test_add_update_remove_cart_item(db_session):
    user = User(email="u@example.com", phone="79990000000", password_hash="hash")
    category = Category(name="Fur")
    db_session.add_all([user, category])
    db_session.flush()
    product = Product(name="Coat", description="desc", price=Decimal("150.00"), category_id=category.id)
    db_session.add(product)
    db_session.commit()

    repo = CartRepository(session=db_session)

    item = repo.add_item(user_id=user.id, product_id=product.id, quantity=2)
    assert item.quantity == 2

    updated = repo.update_item_quantity(user_id=user.id, product_id=product.id, quantity=4)
    assert updated is not None
    assert updated.quantity == 4

    removed = repo.remove_item(user_id=user.id, product_id=product.id)
    assert removed is True