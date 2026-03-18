from app.routers.auth_router import login, oauth_vk, oauth_yandex, register
from app.schemas.auth_schema import LoginRequest, OAuthLoginRequest, RegisterRequest
from app.services.auth_service import AuthService, OAuthGateway, OAuthRequest, OAuthUserInfo
from infrastructure.db.repositories import UserRepository


class StubOAuthGateway(OAuthGateway):
    def fetch_user_info(self, request: OAuthRequest) -> OAuthUserInfo:
        return OAuthUserInfo(provider=request.provider, subject="stub", email=f"{request.provider}@example.com", phone=None)


class StubOAuthStateService:
    def validate_state(self, state: str) -> None:
        assert state == "valid-state"


class StubOAuthRefreshTokenService:
    def save_or_update_token(self, provider: str, subject: str, token: str) -> None:
        return None

def test_auth_router_handlers(db_session):
    service = AuthService(
        user_repository=UserRepository(db_session),
        oauth_gateway=StubOAuthGateway(),
        oauth_state_service=StubOAuthStateService(),
        oauth_refresh_token_service=StubOAuthRefreshTokenService(),
        jwt_secret="test-secret",
        jwt_expire_minutes=15,
    )

    register_response = register(
        payload=RegisterRequest(email="user@example.com", phone="79000000000", password="password123"),
        service=service,
    )
    assert register_response.user.id > 0

    login_response = login(payload=LoginRequest(email="user@example.com", password="password123"), service=service)
    assert login_response.user.email == "user@example.com"

    yandex_response = oauth_yandex(
        payload=OAuthLoginRequest(code="code", redirect_uri="https://cb", state="valid-state"),
        service=service,
    )
    assert yandex_response.user.email == "yandex@example.com"

    vk_response = oauth_vk(
        payload=OAuthLoginRequest(code="code", redirect_uri="https://cb", state="valid-state"),
        service=service,
    )
    assert vk_response.user.email == "vk@example.com"