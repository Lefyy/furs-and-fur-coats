from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from infrastructure.db.models import Cart, CartItem, Order, OrderItem, OrderStatus, Product
from infrastructure.db.repositories.base import BaseRepository


class OrderRepository(BaseRepository):
    def __init__(self, session: Session) -> None:
        super().__init__(session)

    def get_by_id(self, order_id: int) -> Order | None:
        stmt = (
            select(Order)
            .where(Order.id == order_id)
            .options(joinedload(Order.items), joinedload(Order.status))
        )
        return self.session.scalar(stmt)

    def get_status_by_name(self, name: str) -> OrderStatus | None:
        stmt = select(OrderStatus).where(OrderStatus.name == name)
        return self.session.scalar(stmt)

    def create(
        self,
        user_id: int,
        address: str,
        address_raw: str | None,
        postal_code: str | None,
        address_metadata: dict | None,
        address_enrichment_status: str | None,
        status_name: str = "created",
    ) -> Order:

        cart: Cart | None = None

        def operation() -> Order:
            nonlocal cart
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
            order = Order(
                user_id=user_id,
                status_id=status.id,
                total_price=total,
                address=address,
                address_raw=address_raw,
                postal_code=postal_code,
                address_metadata=address_metadata,
                address_enrichment_status=address_enrichment_status,
            )
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
            return order

        order = self.run_in_transaction(operation)
        if cart is not None:
            self.session.expire(cart, ["items"])
        return order
    
    def update_address_enrichment(
        self,
        order_id: int,
        address: str,
        postal_code: str | None,
        address_metadata: dict | None,
        address_enrichment_status: str,
    ) -> Order:
        def operation() -> Order:
            order = self.get_by_id(order_id)
            if order is None:
                raise ValueError("Order not found")
            order.address = address
            order.postal_code = postal_code
            order.address_metadata = address_metadata
            order.address_enrichment_status = address_enrichment_status
            return order

        return self.run_in_transaction(operation)

