from decimal import Decimal

from sqlalchemy import Select, asc, desc, select
from sqlalchemy.orm import Session

from infrastructure.db.models import Product
from infrastructure.db.repositories.base import BaseRepository


class ProductRepository(BaseRepository):
    def __init__(self, session: Session) -> None:
        super().__init__(session)

    def get_by_id(self, product_id: int) -> Product | None:
        stmt = select(Product).where(Product.id == product_id)
        return self.session.scalar(stmt)

    def list(
        self,
        min_price: Decimal | None = None,
        max_price: Decimal | None = None,
        category_id: int | None = None,
        sort: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[Product]:
        stmt: Select[tuple[Product]] = select(Product)

        if min_price is not None:
            stmt = stmt.where(Product.price >= min_price)
        if max_price is not None:
            stmt = stmt.where(Product.price <= max_price)
        if category_id is not None:
            stmt = stmt.where(Product.category_id == category_id)

        if sort == "price_asc":
            stmt = stmt.order_by(asc(Product.price))
        elif sort == "price_desc":
            stmt = stmt.order_by(desc(Product.price))
        else:
            stmt = stmt.order_by(desc(Product.created_at))

        stmt = stmt.offset(offset).limit(limit)
        return list(self.session.scalars(stmt).all())
