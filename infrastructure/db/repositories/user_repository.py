from sqlalchemy import select
from sqlalchemy.orm import Session

from infrastructure.db.models import User
from infrastructure.db.repositories.base import BaseRepository


class UserRepository(BaseRepository):
    def __init__(self, session: Session) -> None:
        super().__init__(session)

    def create(self, email: str, phone: str, password_hash: str) -> User:
        user = User(email=email, phone=phone, password_hash=password_hash)
        self.session.add(user)
        self.flush()
        return user

    def get_by_id(self, user_id: int) -> User | None:
        stmt = select(User).where(User.id == user_id)
        return self.session.scalar(stmt)

    def get_by_email(self, email: str) -> User | None:
        stmt = select(User).where(User.email == email)
        return self.session.scalar(stmt)

    def get_by_phone(self, phone: str) -> User | None:
        stmt = select(User).where(User.phone == phone)
        return self.session.scalar(stmt)
