from sqlalchemy import select
from sqlalchemy.orm import Session

from infrastructure.db.models import OAuthAccount, User
from infrastructure.db.repositories.base import BaseRepository


class UserRepository(BaseRepository):
    def __init__(self, session: Session) -> None:
        super().__init__(session)

    def create(self, email: str, phone: str, password_hash: str) -> User:
        def operation() -> User:
            user = User(email=email, phone=phone, password_hash=password_hash)
            self.session.add(user)
            return user
        
        return self.run_in_transaction(operation)

    def get_by_id(self, user_id: int) -> User | None:
        stmt = select(User).where(User.id == user_id)
        return self.session.scalar(stmt)

    def get_by_email(self, email: str) -> User | None:
        stmt = select(User).where(User.email == email)
        return self.session.scalar(stmt)

    def get_by_phone(self, phone: str) -> User | None:
        stmt = select(User).where(User.phone == phone)
        return self.session.scalar(stmt)
    
    def get_by_oauth(self, provider: str, oauth_subject: str) -> User | None:
        stmt = (
            select(User)
            .join(OAuthAccount, OAuthAccount.user_id == User.id)
            .where(OAuthAccount.provider == provider, OAuthAccount.oauth_subject == oauth_subject)
        )
        return self.session.scalar(stmt)

    def attach_oauth_account(self, user_id: int, provider: str, oauth_subject: str) -> User:
        def operation() -> User:
            user = self.get_by_id(user_id)
            if user is None:
                raise ValueError("User not found")
            account = OAuthAccount(provider=provider, oauth_subject=oauth_subject)
            user.oauth_accounts.append(account)
            return user

        return self.run_in_transaction(operation)

