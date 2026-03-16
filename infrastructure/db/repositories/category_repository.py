from sqlalchemy import select
from sqlalchemy.orm import Session

from infrastructure.db.models import Category
from infrastructure.db.repositories.base import BaseRepository


class CategoryRepository(BaseRepository):
    def __init__(self, session: Session) -> None:
        super().__init__(session)

    def get_by_id(self, category_id: int) -> Category | None:
        stmt = select(Category).where(Category.id == category_id)
        return self.session.scalar(stmt)

    def list_all(self) -> list[Category]:
        stmt = select(Category).order_by(Category.id)
        return list(self.session.scalars(stmt).all())

    def get_tree(self) -> list[dict]:
        categories = self.list_all()
        nodes: dict[int, dict] = {
            category.id: {
                "id": category.id,
                "name": category.name,
                "parent_id": category.parent_id,
                "children": [],
            }
            for category in categories
        }

        roots: list[dict] = []
        for node in nodes.values():
            if node["parent_id"] is None:
                roots.append(node)
                continue

            parent = nodes.get(node["parent_id"])
            if parent is not None:
                parent["children"].append(node)

        return roots
