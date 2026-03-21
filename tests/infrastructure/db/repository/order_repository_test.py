from decimal import Decimal

from infrastructure.db.models import Category, OrderItem, OrderStatus, OrderStatusName, Product, User
from infrastructure.db.repositories import CartRepository, OrderRepository


def test_create_order_from_cart_creates_items_and_clears_cart(db_session):
    user = User(email="o@example.com", email_raw="o@example.com", phone="78880000000", phone_raw="78880000000", password_hash="hash", is_staff=False)
    category = Category(name="Premium")
    status = OrderStatus(name=OrderStatusName.CREATED.value)
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

    order = order_repo.create(
        user_id=user.id,
        address="Moscow",
        address_raw="Moscow",
        postal_code="101000",
        address_metadata={"postal_code": "101000"},
        address_enrichment_status="formatted",
    )
    db_session.commit()

    assert Decimal(order.total_price) == Decimal("800.00")
    assert order.postal_code == "101000"
    assert order.address_metadata["postal_code"] == "101000"
    order_items = db_session.query(OrderItem).filter(OrderItem.order_id == order.id).all()
    assert len(order_items) == 2

    cart = cart_repo.get_for_user(user_id=user.id)
    assert cart is not None
    assert len(cart.items) == 0

def test_order_repository_updates_address_enrichment_fields(db_session):
    user = User(email="u@example.com", email_raw="u@example.com", phone="79990000000", phone_raw="79990000000", password_hash="hash", is_staff=False)
    category = Category(name="Premium")
    status = OrderStatus(name=OrderStatusName.CREATED.value)
    db_session.add_all([user, category, status])
    db_session.flush()
    product = Product(name="Fox", description="fox", price=Decimal("200.00"), category_id=category.id)
    db_session.add(product)
    db_session.flush()
    CartRepository(session=db_session).add_item(user_id=user.id, product_id=product.id, quantity=1)
    db_session.commit()

    repository = OrderRepository(session=db_session)
    order = repository.create(
        user_id=user.id,
        address="Raw address",
        address_raw="Raw address",
        postal_code=None,
        address_metadata={},
        address_enrichment_status="pending_enrichment",
    )

    updated = repository.update_address_enrichment(
        order_id=order.id,
        address="Formatted address",
        postal_code="101000",
        address_metadata={"postal_code": "101000"},
        address_enrichment_status="formatted",
    )

    assert updated.address == "Formatted address"
    assert updated.postal_code == "101000"
    assert updated.address_metadata["postal_code"] == "101000"
    assert updated.address_enrichment_status == "formatted"