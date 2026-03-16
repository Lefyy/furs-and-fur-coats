from decimal import Decimal

from infrastructure.db.models import Category, OrderItem, OrderStatus, Product, User
from infrastructure.db.repositories import CartRepository, OrderRepository


def test_create_order_from_cart_creates_items_and_clears_cart(db_session):
    user = User(email="o@example.com", phone="78880000000", password_hash="hash")
    category = Category(name="Premium")
    status = OrderStatus(name="created")
    db_session.add_all([user, category, status])
    db_session.flush()

    product_1 = Product(name="Fox", description="fox", price=Decimal("200.00"), category_id=category.id)
    product_2 = Product(name="Lynx", description="lynx", price=Decimal("300.00"), category_id=category.id)
    db_session.add_all([product_1, product_2])
    db_session.flush()

    cart_repo = CartRepository(session=db_session)
    cart_repo.add_item(user_id=user.id, product_id=product_1.id, quantity=1)
    cart_repo.add_item(user_id=user.id, product_id=product_2.id, quantity=2)
    db_session.commit()

    order_repo = OrderRepository(session=db_session)

    order = order_repo.create(user_id=user.id, address="Moscow")
    db_session.commit()

    assert Decimal(order.total_price) == Decimal("800.00")
    order_items = db_session.query(OrderItem).filter(OrderItem.order_id == order.id).all()
    assert len(order_items) == 2

    cart = cart_repo.get_for_user(user_id=user.id)
    assert cart is not None
    assert len(cart.items) == 0