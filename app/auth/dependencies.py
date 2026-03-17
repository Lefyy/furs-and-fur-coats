from fastapi import Header

from app.exceptions import UnauthorizedError


def get_current_user_id(x_user_id: int | None = Header(default=None)) -> int:
    if x_user_id is None:
        raise UnauthorizedError()
    return x_user_id
