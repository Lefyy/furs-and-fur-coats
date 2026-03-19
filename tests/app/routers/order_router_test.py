from app.routers.order_router import create_order
from app.schemas import OrderCreateRequest
from tests.app.services.order_service_test import StubAddressFormattingService, seed_order_context
from app.services.order_service import OrderService
from infrastructure.db.repositories import OrderRepository


def test_order_router_handlers(db_session):
    user = seed_order_context(db_session)
    order_service = OrderService(OrderRepository(db_session), StubAddressFormattingService())


    order_response = create_order(payload=OrderCreateRequest(address="Москва Тверская 1"), user_id=user.id, service=order_service)
    assert order_response.status == "created"
    assert order_response.address == "г Москва, ул Тверская, д 1"
