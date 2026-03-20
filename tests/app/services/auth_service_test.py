from app.exceptions import BadRequestError, UnauthorizedError
from app.services.auth_service import AuthService, YandexUserInfo
from app.services.contact_formatting_service import CanonicalFieldResult, ContactFormattingResult
from app.utils.security import decode_access_token
from infrastructure.db.repositories import UserRepository


class StubYandexOAuthGateway:
    def __init__(self, user_info: YandexUserInfo | None = None) -> None:
        self.user_info = user_info or YandexUserInfo(
            subject="yandex-sub",
            email="yandex@example.com",
            phone="79990000000",
            refresh_token="refresh-token",
        )

    def fetch_user_info(self, code: str):
        return self.user_info
    

class StubOAuthStateService:
    def validate_state(self, state: str) -> None:
        if state != "valid-state":
            raise UnauthorizedError("Invalid state")


class StubOAuthRefreshTokenService:
    def __init__(self) -> None:
        self.storage: dict[str, str] = {}

    def save_if_present(self, *, provider: str, subject: str, token: str | None) -> None:
        if not token:
            return
        self.save_or_update_token(provider=provider, subject=subject, token=token)

    def save_or_update_token(self, provider: str, subject: str, token: str) -> None:
        self.storage[f"{provider}:{subject}"] = token


class StubContactFormattingService:
    def __init__(self, *, degraded: bool = False) -> None:
        self.degraded = degraded

    def format(self, *, email: str, phone: str) -> ContactFormattingResult:
        if self.degraded:
            return ContactFormattingResult(
                email=CanonicalFieldResult(raw=email, canonical=email, data={}),
                phone=CanonicalFieldResult(raw=phone, canonical=phone, data={}),
                is_degraded=True,
                status="pending_enrichment",
            )
        return ContactFormattingResult(
            email=CanonicalFieldResult(raw=email, canonical=email.lower(), data={"result": email.lower()}),
            phone=CanonicalFieldResult(raw=phone, canonical="79990000000", data={"result": "79990000000"}),
            is_degraded=False,
            status="formatted",
        )


def build_service(
    db_session,
    *,
    degraded: bool = False,
    oauth_user: YandexUserInfo | None = None,
) -> tuple[AuthService, StubOAuthRefreshTokenService]:
    refresh_service = StubOAuthRefreshTokenService()
    service = AuthService(
        user_repository=UserRepository(db_session),
        oauth_gateway=StubYandexOAuthGateway(user_info=oauth_user),
        oauth_state_service=StubOAuthStateService(),
        oauth_refresh_token_service=refresh_service,
        contact_formatting_service=StubContactFormattingService(degraded=degraded),
        jwt_secret="test-secret",
        jwt_expire_minutes=15,
    )
    return service, refresh_service


def test_auth_service_register_and_login(db_session):
    service, _ = build_service(db_session)

    token_response = service.register(email="User@Example.com", phone="+7 (999) 111-22-33", password="password123")
    payload = decode_access_token(token_response.access_token, "test-secret")
    assert int(payload["sub"]) == token_response.user.id
    assert token_response.user.email == "user@example.com"
    assert token_response.user.phone == "79990000000"

    login_response = service.login(email="user@example.com", password="password123")
    assert login_response.user.id == token_response.user.id


def test_auth_service_rejects_duplicate_email_by_canonical_value(db_session):
    service, _ = build_service(db_session)
    service.register(email="User@Example.com", phone="79000000000", password="password123")

    try:
        service.register(email="user@example.com", phone="79000000001", password="password123")
        assert False
    except BadRequestError:
        assert True


def test_auth_service_degraded_mode_saves_raw_values_and_enqueues_enrichment(db_session, monkeypatch):
    service, _ = build_service(db_session, degraded=True)
    captured: dict[str, int] = {}

    class DelayStub:
        @staticmethod
        def delay(*, user_id: int) -> None:
            captured["user_id"] = user_id

    monkeypatch.setattr("app.services.auth_service.enrich_user_contacts", DelayStub)

    response = service.register(email="Raw@Example.com", phone="+7 (111) 222-33-44", password="password123")

    user = UserRepository(db_session).get_by_id(response.user.id)
    assert user is not None
    assert user.email == "Raw@Example.com"
    assert user.email_raw == "Raw@Example.com"
    assert user.phone == "+7 (111) 222-33-44"
    assert user.phone_raw == "+7 (111) 222-33-44"
    assert user.contacts_enrichment_status == "pending_enrichment"
    assert user.is_staff is False
    assert captured["user_id"] == user.id


def test_auth_service_oauth_login_creates_user_and_saves_refresh_token(db_session):
    service, refresh_service = build_service(db_session)

    response = service.yandex_login(request=type("Req", (), {"code": "abc", "state": "valid-state"})())
    assert response.user.email == "yandex@example.com"

    linked_user = UserRepository(db_session).get_by_oauth(provider="yandex", oauth_subject="yandex-sub")
    assert linked_user is not None
    assert linked_user.id == response.user.id
    assert linked_user.is_staff is False
    assert refresh_service.storage["yandex:yandex-sub"] == "refresh-token"


def test_auth_service_oauth_login_builds_fallback_phone_when_missing(db_session):
    oauth_user = YandexUserInfo(subject="missing-phone-sub", email="no-phone@example.com", phone=None, refresh_token=None)
    service, refresh_service = build_service(db_session, oauth_user=oauth_user)

    response = service.yandex_login(request=type("Req", (), {"code": "abc", "state": "valid-state"})())

    assert response.user.phone.startswith("oauth_")
    assert refresh_service.storage == {}
