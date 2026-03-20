from dataclasses import dataclass
import logging

from app.exceptions import BadRequestError, UnauthorizedError
from app.schemas.auth_schema import TokenResponse, YandexAccessTokenResponse, YandexOAuthRequest
from app.services.auth_token_factory import AuthTokenFactory
from app.services.contact_formatting_service import ContactFormattingService
from app.services.oauth_identity_policy import OAuthIdentityPolicy
from app.services.oauth_refresh_token_service import OAuthRefreshTokenService
from app.services.oauth_state_service import OAuthStateService
from app.tasks.enrichment_tasks import enrich_user_contacts
from app.utils.security import hash_password, verify_password
from infrastructure.db.models import User
from infrastructure.db.repositories import UserRepository

YANDEX_OAUTH_PROVIDER = "yandex"


@dataclass(slots=True)
class YandexUserInfo:
    subject: str
    email: str | None
    phone: str | None = None
    refresh_token: str | None = None


logger = logging.getLogger(__name__)


class YandexOAuthGateway:
    def exchange_code_for_token(self, code: str) -> YandexAccessTokenResponse:
        raise NotImplementedError

    def get_user_data(self, access_token: YandexAccessTokenResponse) -> dict:
        raise NotImplementedError
    
    def fetch_user_info(self, code: str) -> YandexUserInfo:
        raise NotImplementedError


class AuthService:
    def __init__(
        self,
        user_repository: UserRepository,
        oauth_gateway: YandexOAuthGateway,
        oauth_state_service: OAuthStateService,
        oauth_refresh_token_service: OAuthRefreshTokenService,
        contact_formatting_service: ContactFormattingService,
        jwt_secret: str,
        jwt_expire_minutes: int,
        oauth_identity_policy: OAuthIdentityPolicy | None = None,
        auth_token_factory: AuthTokenFactory | None = None,
    ) -> None:
        self.user_repository = user_repository
        self.oauth_gateway = oauth_gateway
        self.oauth_state_service = oauth_state_service
        self.oauth_refresh_token_service = oauth_refresh_token_service
        self.contact_formatting_service = contact_formatting_service
        self.oauth_identity_policy = oauth_identity_policy or OAuthIdentityPolicy(user_repository=user_repository)
        self.auth_token_factory = auth_token_factory or AuthTokenFactory(
            jwt_secret=jwt_secret,
            jwt_expire_minutes=jwt_expire_minutes,
        )


    def register(self, email: str, phone: str, password: str) -> TokenResponse:
        formatting_result = self.contact_formatting_service.format(email=email, phone=phone)

        canonical_email = formatting_result.email.canonical
        canonical_phone = formatting_result.phone.canonical

        if self.user_repository.get_by_email(canonical_email):

            raise BadRequestError("User with this email already exists")
        if self.user_repository.get_by_phone(canonical_phone):
            raise BadRequestError("User with this phone already exists")

        password_hash = hash_password(password)
        user = self.user_repository.create(
            email=canonical_email,
            email_raw=email,
            phone=canonical_phone,
            phone_raw=phone,
            password_hash=password_hash,
            contacts_enrichment_status=formatting_result.status,
            is_staff=False,
        )

        if formatting_result.is_degraded:
            logger.warning(
                "Saved user registration in degraded mode",
                extra={"email": email, "phone": phone, "user_id": user.id},
            )
            enrich_user_contacts.delay(user_id=user.id)

        return self.auth_token_factory.build(user)


    def login(self, email: str, password: str) -> TokenResponse:
        user = self.user_repository.get_by_email(email)
        if user is None or not verify_password(password, user.password_hash):
            raise UnauthorizedError("Invalid credentials")
        return self.auth_token_factory.build(user)


    def yandex_login(self, request: YandexOAuthRequest) -> TokenResponse:
        self.oauth_state_service.validate_state(request.state)

        oauth_user = self.oauth_gateway.fetch_user_info(code=request.code)
        user = self._get_or_create_oauth_user(oauth_user)
        self.oauth_refresh_token_service.save_if_present(
            provider=YANDEX_OAUTH_PROVIDER,
            subject=oauth_user.subject,
            token=oauth_user.refresh_token,
        )

        return self.auth_token_factory.build(user)


    def _get_or_create_oauth_user(self, oauth_user: YandexUserInfo) -> User:
        user = self._find_user_for_oauth_login(oauth_user)
        if user is not None:
            return user
        return self._create_oauth_user(oauth_user)


    def _find_user_for_oauth_login(self, oauth_user: YandexUserInfo) -> User | None:
        user = self.user_repository.get_by_oauth(
            provider=YANDEX_OAUTH_PROVIDER,
            oauth_subject=oauth_user.subject,
        )

        if user is not None:
            return user

        if not oauth_user.email:
            return None

        user = self.user_repository.get_by_email(oauth_user.email)
        if user is None:
            return None

        return self._attach_yandex_account(user=user, subject=oauth_user.subject)


    def _attach_yandex_account(self, user: User, subject: str) -> User:
        return self.user_repository.attach_oauth_account(
            user_id=user.id,
            provider=YANDEX_OAUTH_PROVIDER,
            oauth_subject=subject,
        )


    def _create_oauth_user(self, oauth_user: YandexUserInfo) -> User:
        generated_phone = oauth_user.phone or self.oauth_identity_policy.build_phone(
            provider=YANDEX_OAUTH_PROVIDER,
            subject=oauth_user.subject,
        )
        user = self.user_repository.create(
            email=oauth_user.email,
            email_raw=oauth_user.email,
            phone=generated_phone,
            phone_raw=generated_phone,
            password_hash=None,
            contacts_enrichment_status="formatted",
            is_staff=False,
        )

        return self._attach_yandex_account(user=user, subject=oauth_user.subject)