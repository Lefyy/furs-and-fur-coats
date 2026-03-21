import hashlib

from infrastructure.db.repositories import UserRepository


class OAuthIdentityPolicy:
    def __init__(self, user_repository: UserRepository) -> None:
        self.user_repository = user_repository

    def build_phone(self, *, provider: str, subject: str) -> str:
        generated_phone = self._build_oauth_phone(provider=provider, subject=subject)
        if self.user_repository.get_by_phone(generated_phone):
            return self._build_oauth_phone(provider=provider, subject=f"{subject}-alt")
        return generated_phone

    @staticmethod
    def _build_oauth_phone(*, provider: str, subject: str) -> str:
        suffix = hashlib.sha256(f"{provider}:{subject}".encode("utf-8")).hexdigest()[:12]
        return f"oauth_{suffix}"