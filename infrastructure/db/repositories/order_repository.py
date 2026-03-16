from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from infrastructure.db.models import Cart, CartItem, Order, OrderItem, OrderStatus, Product
from infrastructure.db.repositories.base import BaseRepository


class OrderRepository(BaseRepository):
    def __init__(self, session: Session) -> None:
        super().__init__(session)

    def get_status_by_name(self, name: str) -> OrderStatus | None:
        stmt = select(OrderStatus).where(OrderStatus.name == name)
        return self.session.scalar(stmt)

    def create(self, user_id: int, address: str, status_name: str = "created") -> Order:
        status = self.get_status_by_name(name=status_name)
        if status is None:
            raise ValueError(f"Order status '{status_name}' does not exist")

        cart_stmt = select(Cart).where(Cart.user_id == user_id)
        cart = self.session.scalar(cart_stmt)
        if cart is None:
            raise ValueError("User cart does not exist")

        items_stmt = (
            select(CartItem, Product)
            .join(Product, Product.id == CartItem.product_id)
            .where(CartItem.cart_id == cart.id)
        )
        rows = list(self.session.execute(items_stmt).all())
        if not rows:
            raise ValueError("Cannot create order from empty cart")

        total = sum(Decimal(product.price) * item.quantity for item, product in rows)
        order = Order(user_id=user_id, status_id=status.id, total_price=total, address=address)
        self.session.add(order)
        self.flush()

        for item, product in rows:
            self.session.add(
                OrderItem(
                    order_id=order.id,
                    product_id=product.id,
                    quantity=item.quantity,
                    price=product.price,
                )
            )

        self.session.query(CartItem).filter(CartItem.cart_id == cart.id).delete(synchronize_session=False)
        self.flush()
        return order
