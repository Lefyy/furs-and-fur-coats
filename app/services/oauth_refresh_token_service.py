from infrastructure.cache import redis_client


class OAuthRefreshTokenService:
    def __init__(self, ttl_seconds: int) -> None:
        self.ttl_seconds = ttl_seconds


    def save_if_present(self, *, provider: str, subject: str, token: str | None) -> None:
        if not token:
            return
        self.save_or_update_token(provider=provider, subject=subject, token=token)


    def save_or_update_token(self, provider: str, subject: str, token: str) -> None:
        redis_client.setex(
            name=self._build_key(provider=provider, subject=subject),
            time=self.ttl_seconds,
            value=token,
        )


    def get_token(self, provider: str, subject: str) -> str | None:
        token = redis_client.get(self._build_key(provider=provider, subject=subject))
        if token is None:
            return None
        return str(token)


    @staticmethod
    def _build_key(provider: str, subject: str) -> str:
        return f"oauth_refresh_token:{provider}:{subject}"