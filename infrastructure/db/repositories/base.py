from collections.abc import Callable
from typing import TypeVar

from sqlalchemy.orm import Session


ResultT = TypeVar("ResultT")


class BaseRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def flush(self) -> None:
        self.session.flush()

    def commit(self) -> None:
        self.session.commit()

    def rollback(self) -> None:
        self.session.rollback()

    def run_in_transaction(self, operation: Callable[[], ResultT]) -> ResultT:
        try:
            result = operation()
            self.flush()
            self.commit()
            return result
        except Exception:
            self.rollback()
            raise