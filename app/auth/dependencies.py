from fastapi import Header

from app.config import settings
from app.exceptions import UnauthorizedError
from app.utils.security import decode_access_token


def get_current_user_id(authorization: str | None = Header(default=None)) -> int:
    if authorization is None or not authorization.startswith("Bearer "):
        raise UnauthorizedError()
    
    token = authorization.removeprefix("Bearer ").strip()
    payload = decode_access_token(token=token, secret_key=settings.jwt_secret_key)
    subject = payload.get("sub")
    if subject is None:
        raise UnauthorizedError("Invalid token")

    return int(subject)

