from decimal import Decimal

from app.routers.cart_router import add_to_cart, get_cart
from app.routers.order_router import create_order
from app.schemas import CartItemRequest, OrderCreateRequest
from app.services import CartService, OrderService
from infrastructure.db.models import Category, OrderStatus, Product, User
from infrastructure.db.repositories import CartRepository, OrderRepository, ProductRepository


def test_order_router_handlers(db_session):
    user = User(email="api-order@example.com", phone="79994444444", password_hash="hash")
    category = Category(name="fur")
    status = OrderStatus(name="created")
    db_session.add_all([user, category, status])
    db_session.flush()

    product = Product(name="Fox", description="warm", price=Decimal("250.00"), category_id=category.id)
    db_session.add(product)
    db_session.commit()

    cart_service = CartService(CartRepository(db_session), ProductRepository(db_session))
    order_service = OrderService(OrderRepository(db_session))

    add_to_cart(
        payload=CartItemRequest(product_id=product.id, quantity=2),
        user_id=user.id,
        service=cart_service,
    )

    order_response = create_order(payload=OrderCreateRequest(address="Moscow"), user_id=user.id, service=order_service)
    assert order_response.status == "created"

    cart_response = get_cart(user_id=user.id, service=cart_service)
    assert cart_response.items == []
