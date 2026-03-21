from decimal import Decimal

from app.services.address_formatting_service import AddressFormattingResult
from app.services.order_service import OrderService
from infrastructure.db.models import Category, OrderStatus, OrderStatusName, Product, User
from infrastructure.db.repositories import CartRepository, OrderRepository

class StubAddressFormattingService:
    def __init__(self, *, degraded: bool = False) -> None:
        self.degraded = degraded

    def format(self, *, address: str) -> AddressFormattingResult:
        if self.degraded:
            return AddressFormattingResult(
                raw=address,
                canonical=address,
                postal_code=None,
                metadata={},
                is_degraded=True,
                status="pending_enrichment",
            )
        return AddressFormattingResult(
            raw=address,
            canonical="г Москва, ул Тверская, д 1",
            postal_code="125009",
            metadata={"result": "г Москва, ул Тверская, д 1", "postal_code": "125009"},
            is_degraded=False,
            status="formatted",
        )


def seed_order_context(db_session):
    user = User(email="order@example.com", email_raw="order@example.com", phone="79994444444", phone_raw="79994444444", password_hash="hash", is_staff=False)
    category = Category(name="fur")
    status = OrderStatus(name=OrderStatusName.CREATED.value)
    db_session.add_all([user, category, status])
    db_session.flush()

    product = Product(name="Fox", description="warm", price=Decimal("250.00"), category_id=category.id)
    db_session.add(product)
    db_session.flush()
    
    CartRepository(db_session).add_item(user_id=user.id, product_id=product.id, quantity=2)
    db_session.commit()
    return user

def test_order_service_formats_address_on_success(db_session):
    user = seed_order_context(db_session)
    service = OrderService(OrderRepository(db_session), StubAddressFormattingService())

    response = service.create_order(user_id=user.id, address="Москва Тверская 1")

    order = OrderRepository(db_session).get_by_id(response.id)
    assert order is not None
    assert order.address == "г Москва, ул Тверская, д 1"
    assert order.address_raw == "Москва Тверская 1"
    assert order.postal_code == "125009"
    assert order.address_metadata["postal_code"] == "125009"
    assert order.address_enrichment_status == "formatted"


def test_order_service_degraded_mode_saves_raw_address_and_enqueues_enrichment(db_session, monkeypatch):
    user = seed_order_context(db_session)
    service = OrderService(OrderRepository(db_session), StubAddressFormattingService(degraded=True))
    captured: dict[str, int] = {}

    class DelayStub:
        @staticmethod
        def delay(*, order_id: int) -> None:
            captured["order_id"] = order_id

    monkeypatch.setattr("app.services.order_service.enrich_order_address", DelayStub)

    response = service.create_order(user_id=user.id, address="Сырой адрес")

    order = OrderRepository(db_session).get_by_id(response.id)
    assert order is not None
    assert order.address == "Сырой адрес"
    assert order.address_raw == "Сырой адрес"
    assert order.postal_code is None
    assert order.address_metadata == {}
    assert order.address_enrichment_status == "pending_enrichment"
    assert captured["order_id"] == order.id
