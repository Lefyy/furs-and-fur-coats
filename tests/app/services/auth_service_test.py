from app.exceptions import BadRequestError, UnauthorizedError
from app.services.auth_service import AuthService, OAuthGateway, OAuthRequest, OAuthUserInfo
from app.utils.security import decode_access_token
from infrastructure.db.repositories import UserRepository


class StubOAuthGateway(OAuthGateway):
    def fetch_user_info(self, request: OAuthRequest) -> OAuthUserInfo:
        return OAuthUserInfo(
            provider=request.provider,
            subject=f"{request.provider}-sub",
            email=f"{request.provider}@example.com",
            refresh_token=f"{request.provider}-refresh",
        )



class StubOAuthStateService:
    def validate_state(self, state: str) -> None:
        if state != "valid-state":
            raise UnauthorizedError("Invalid state")


class StubOAuthRefreshTokenService:
    def __init__(self) -> None:
        self.storage: dict[str, str] = {}

    def save_or_update_token(self, provider: str, subject: str, token: str) -> None:
        self.storage[f"{provider}:{subject}"] = token


def build_service(db_session) -> tuple[AuthService, StubOAuthRefreshTokenService]:
    refresh_service = StubOAuthRefreshTokenService()
    service = AuthService(
        user_repository=UserRepository(db_session),
        oauth_gateway=StubOAuthGateway(),
        oauth_state_service=StubOAuthStateService(),
        oauth_refresh_token_service=refresh_service,
        jwt_secret="test-secret",
        jwt_expire_minutes=15,
    )
    return service, refresh_service


def test_auth_service_register_and_login(db_session):
    service, _ = build_service(db_session)


    token_response = service.register(email="user@example.com", phone="79000000000", password="password123")
    payload = decode_access_token(token_response.access_token, "test-secret")
    assert int(payload["sub"]) == token_response.user.id

    login_response = service.login(email="user@example.com", password="password123")
    assert login_response.user.id == token_response.user.id


def test_auth_service_rejects_duplicate_email(db_session):
    service, _ = build_service(db_session)
    service.register(email="user@example.com", phone="79000000000", password="password123")

    try:
        service.register(email="user@example.com", phone="79000000001", password="password123")
        assert False
    except BadRequestError:
        assert True


def test_auth_service_oauth_login_creates_user_and_saves_refresh_token(db_session):
    service, refresh_service = build_service(db_session)

    response = service.oauth_login(
        request=OAuthRequest(provider="vk", code="abc", redirect_uri="https://app/callback"),
        state="valid-state",
    )
    assert response.user.email == "vk@example.com"

    linked_user = UserRepository(db_session).get_by_oauth(provider="vk", oauth_subject="vk-sub")
    assert linked_user is not None
    assert linked_user.id == response.user.id

    assert refresh_service.storage["vk:vk-sub"] == "vk-refresh"


def test_auth_service_login_invalid_password(db_session):
    service, _ = build_service(db_session)
    service.register(email="user@example.com", phone="79000000000", password="password123")

    try:
        service.login(email="user@example.com", password="bad-password")
        assert False
    except UnauthorizedError:
        assert True