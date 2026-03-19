from dataclasses import dataclass
import hashlib

from app.exceptions import BadRequestError, UnauthorizedError
from app.schemas.auth_schema import TokenResponse, UserAuthResponse, YandexUserInfo, YandexOAuthRequest
from app.services.oauth_state_service import OAuthStateService
from app.utils.security import create_access_token, hash_password, verify_password
from infrastructure.db.models import User
from infrastructure.db.repositories import UserRepository

YANDEX_OAUTH_PROVIDER = "yandex"

class YandexOAuthGateway:
    def fetch_user_info(self, code: str) -> YandexUserInfo:
        raise NotImplementedError


class AuthService:
    def __init__(
        self,
        user_repository: UserRepository,
        oauth_gateway: YandexOAuthGateway,
        oauth_state_service: OAuthStateService,
        jwt_secret: str,
        jwt_expire_minutes: int,
    ) -> None:
        self.user_repository = user_repository
        self.oauth_gateway = oauth_gateway
        self.oauth_state_service = oauth_state_service
        self.jwt_secret = jwt_secret
        self.jwt_expire_minutes = jwt_expire_minutes

    def register(self, email: str, phone: str, password: str) -> TokenResponse:
        if self.user_repository.get_by_email(email):
            raise BadRequestError("User with this email already exists")
        if self.user_repository.get_by_phone(phone):
            raise BadRequestError("User with this phone already exists")

        password_hash = hash_password(password)
        user = self.user_repository.create(email=email, phone=phone, password_hash=password_hash)
        return self._build_token_response(user)

    def login(self, email: str, password: str) -> TokenResponse:
        user = self.user_repository.get_by_email(email)
        if user is None or not verify_password(password, user.password_hash):
            raise UnauthorizedError("Invalid credentials")
        return self._build_token_response(user)

    def yandex_login(self, request: YandexOAuthRequest) -> TokenResponse:
        self.oauth_state_service.validate_state(request.state)

        oauth_user = self.oauth_gateway.fetch_user_info(code=request.code)

        user = self.user_repository.get_by_oauth(
            provider=YANDEX_OAUTH_PROVIDER,
            oauth_subject=oauth_user.subject,
        )

        if user is None and oauth_user.email:
            user = self.user_repository.get_by_email(oauth_user.email)
            if user:
                user = self.user_repository.attach_oauth_account(
                    user_id=user.id,
                    provider=YANDEX_OAUTH_PROVIDER,
                    oauth_subject=oauth_user.subject,
                )

        if user is None:
            generated_phone = oauth_user.phone or self._build_oauth_phone(subject=oauth_user.subject)

            if self.user_repository.get_by_phone(generated_phone):
                generated_phone = self._build_oauth_phone(subject=f"{oauth_user.subject}-alt")

            user = self.user_repository.create(
                email=oauth_user.email,
                phone=generated_phone,
                password_hash=None,
            )

            user = self.user_repository.attach_oauth_account(
                user_id=user.id,
                provider=YANDEX_OAUTH_PROVIDER,
                oauth_subject=oauth_user.subject,
            )

        return self._build_token_response(user)

    def _build_token_response(self, user: User) -> TokenResponse:
        token = create_access_token(
            subject=str(user.id),
            secret_key=self.jwt_secret,
            expires_minutes=self.jwt_expire_minutes,
        )
        return TokenResponse(
            access_token=token,
            user=UserAuthResponse(
                id=user.id,
                email=user.email,
                phone=user.phone,
            ),
        )

    @staticmethod
    def _build_oauth_phone(subject: str) -> str:
        suffix = hashlib.sha256(f"{YANDEX_OAUTH_PROVIDER}:{subject}".encode("utf-8")).hexdigest()[:12]
        return f"oauth_{suffix}"