from app.exceptions import BadRequestError, UnauthorizedError
from app.services.auth_service import AuthService, OAuthGateway, OAuthUserInfo
from app.utils.security import decode_access_token
from infrastructure.db.repositories import UserRepository


class StubOAuthGateway(OAuthGateway):
    def fetch_user_info(self, provider: str, code: str, redirect_uri: str) -> OAuthUserInfo:
        return OAuthUserInfo(provider=provider, subject=f"{provider}-sub", email=f"{provider}@example.com")


def test_auth_service_register_and_login(db_session):
    service = AuthService(
        user_repository=UserRepository(db_session),
        oauth_gateway=StubOAuthGateway(),
        jwt_secret="test-secret",
        jwt_expire_minutes=15,
    )

    token_response = service.register(email="user@example.com", phone="79000000000", password="password123")
    payload = decode_access_token(token_response.access_token, "test-secret")
    assert int(payload["sub"]) == token_response.user.id

    login_response = service.login(email="user@example.com", password="password123")
    assert login_response.user.id == token_response.user.id


def test_auth_service_rejects_duplicate_email(db_session):
    repository = UserRepository(db_session)
    service = AuthService(repository, StubOAuthGateway(), jwt_secret="test-secret", jwt_expire_minutes=15)
    service.register(email="user@example.com", phone="79000000000", password="password123")

    try:
        service.register(email="user@example.com", phone="79000000001", password="password123")
        assert False
    except BadRequestError:
        assert True


def test_auth_service_oauth_login_creates_user(db_session):
    service = AuthService(
        user_repository=UserRepository(db_session),
        oauth_gateway=StubOAuthGateway(),
        jwt_secret="test-secret",
        jwt_expire_minutes=15,
    )

    response = service.oauth_login(provider="vk", code="abc", redirect_uri="https://app/callback")
    assert response.user.email == "vk@example.com"

    linked_user = UserRepository(db_session).get_by_oauth(provider="vk", oauth_subject="vk-sub")
    assert linked_user is not None
    assert linked_user.id == response.user.id


def test_auth_service_login_invalid_password(db_session):
    service = AuthService(
        user_repository=UserRepository(db_session),
        oauth_gateway=StubOAuthGateway(),
        jwt_secret="test-secret",
        jwt_expire_minutes=15,
    )
    service.register(email="user@example.com", phone="79000000000", password="password123")

    try:
        service.login(email="user@example.com", password="bad-password")
        assert False
    except UnauthorizedError:
        assert True