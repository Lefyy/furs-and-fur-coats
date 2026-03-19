from fastapi import Depends, Header
from sqlalchemy.orm import Session

from app.config import settings
from app.exceptions import ForbiddenError, UnauthorizedError
from app.utils.security import decode_access_token
from infrastructure.db.db_session import get_db_session
from infrastructure.db.models import User
from infrastructure.db.repositories import UserRepository


def get_current_user_id(authorization: str | None = Header(default=None)) -> int:
    if authorization is None or not authorization.startswith("Bearer "):
        raise UnauthorizedError()
    
    token = authorization.removeprefix("Bearer ").strip()
    payload = decode_access_token(token=token, secret_key=settings.jwt_secret_key)
    subject = payload.get("sub")
    if subject is None:
        raise UnauthorizedError("Invalid token")

    return int(subject)


def get_user_repository(session: Session = Depends(get_db_session)) -> UserRepository:
    return UserRepository(session=session)


def get_current_staff_user(
    user_id: int = Depends(get_current_user_id),
    user_repository: UserRepository = Depends(get_user_repository),
) -> User:
    user = user_repository.get_by_id(user_id)
    if user is None:
        raise UnauthorizedError("Invalid token")
    if not user.is_staff:
        raise ForbiddenError("Staff access required")
    return user


