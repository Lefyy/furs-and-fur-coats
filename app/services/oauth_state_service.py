import secrets

from app.exceptions import UnauthorizedError
from infrastructure.cache import redis_client


STATE_TTL_SECONDS = 300


class OAuthStateService:
    def create_state(self) -> str:
        state = secrets.token_urlsafe(32)

        redis_client.setex(
            name=f"oauth_state:{state}",
            time=STATE_TTL_SECONDS,
            value="1",
        )

        return state

    def validate_state(self, state: str) -> None:
        key = f"oauth_state:{state}"

        exists = redis_client.get(key)
        if not exists:
            raise UnauthorizedError("Invalid or expired OAuth state")

        redis_client.delete(key)