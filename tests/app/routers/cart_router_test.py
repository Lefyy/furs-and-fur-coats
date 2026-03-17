from decimal import Decimal

from app.routers.cart_router import add_to_cart, get_cart
from app.schemas import CartItemRequest
from app.services import CartService
from infrastructure.db.models import Category, Product, User
from infrastructure.db.repositories import CartRepository, ProductRepository


def test_cart_router_handlers(db_session):
    user = User(email="api@example.com", phone="79993333333", password_hash="hash")
    category = Category(name="fur")
    db_session.add_all([user, category])
    db_session.flush()

    product = Product(name="Fox", description="warm", price=Decimal("250.00"), category_id=category.id)
    db_session.add(product)
    db_session.commit()

    cart_service = CartService(CartRepository(db_session), ProductRepository(db_session))

    add_response = add_to_cart(
        payload=CartItemRequest(product_id=product.id, quantity=2),
        user_id=user.id,
        service=cart_service,
    )
    assert add_response.total_price == Decimal("500.00")

    cart_response = get_cart(user_id=user.id, service=cart_service)
    assert len(cart_response.items) == 1