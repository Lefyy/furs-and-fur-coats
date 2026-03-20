from app.schemas.auth_schema import TokenResponse, UserAuthResponse
from app.utils.security import create_access_token
from infrastructure.db.models import User


class AuthTokenFactory:
    def __init__(self, jwt_secret: str, jwt_expire_minutes: int) -> None:
        self.jwt_secret = jwt_secret
        self.jwt_expire_minutes = jwt_expire_minutes

    def build(self, user: User) -> TokenResponse:
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
