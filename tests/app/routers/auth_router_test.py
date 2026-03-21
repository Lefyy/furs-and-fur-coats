from app.routers.auth_router import login, register
from app.schemas.auth_schema import LoginRequest, RegisterRequest
from tests.app.services.auth_service_test import build_service


def test_auth_router_handlers(db_session):
    service, _ = build_service(db_session)

    register_response = register(
        payload=RegisterRequest(email="User@Example.com", phone="79000000000", password="password123"),
        service=service,
    )
    assert register_response.user.id > 0

    login_response = login(payload=LoginRequest(email="user@example.com", password="password123"), service=service)
    assert login_response.user.email == "user@example.com"