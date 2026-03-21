from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from infrastructure.db.models import Cart, CartItem, Order, OrderItem, OrderStatus, OrderStatusName, Product
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
    
    def get_required_by_id(self, order_id: int) -> Order:
        order = self.get_by_id(order_id=order_id)
        if order is None:
            raise ValueError("Order not found")
        return order

    def get_status_by_name(self, name: str) -> OrderStatus | None:
        stmt = select(OrderStatus).where(OrderStatus.name == name)
        return self.session.scalar(stmt)
    
    def _get_required_status(self, status_name: str) -> OrderStatus:
        status = self.get_status_by_name(name=status_name)
        if status is None:
            raise ValueError(f"Order status '{status_name}' does not exist")
        return status

    def _get_required_cart_for_user(self, user_id: int) -> Cart:
        cart_stmt = select(Cart).where(Cart.user_id == user_id)
        cart = self.session.scalar(cart_stmt)
        if cart is None:
            raise ValueError("User cart does not exist")
        return cart

    def _get_cart_rows(self, cart_id: int) -> list[tuple[CartItem, Product]]:
        items_stmt = (
            select(CartItem, Product)
            .join(Product, Product.id == CartItem.product_id)
            .where(CartItem.cart_id == cart_id)
        )
        rows = list(self.session.execute(items_stmt).all())
        if not rows:
            raise ValueError("Cannot create order from empty cart")
        return rows

    def _build_order(
        self,
        user_id: int,
        status_id: int,
        rows: list[tuple[CartItem, Product]],
        address: str,
        address_raw: str | None,
        postal_code: str | None,
        address_metadata: dict | None,
        address_enrichment_status: str | None,
    ) -> Order:
        total = sum(Decimal(product.price) * item.quantity for item, product in rows)
        order = Order(
            user_id=user_id,
            status_id=status_id,
            total_price=total,
            address=address,
            address_raw=address_raw,
            postal_code=postal_code,
            address_metadata=address_metadata,
            address_enrichment_status=address_enrichment_status,
        )
        self.session.add(order)
        self.flush()
        return order

    def _create_order_items(self, order_id: int, rows: list[tuple[CartItem, Product]]) -> None:
        for item, product in rows:
            self.session.add(
                OrderItem(
                    order_id=order_id,
                    product_id=product.id,
                    quantity=item.quantity,
                    price=product.price,
                )
            )

    def _clear_cart(self, cart_id: int) -> None:
        self.session.query(CartItem).filter(CartItem.cart_id == cart_id).delete(synchronize_session=False)

    def create(
        self,
        user_id: int,
        address: str,
        address_raw: str | None,
        postal_code: str | None,
        address_metadata: dict | None,
        address_enrichment_status: str | None,
        status_name: str = OrderStatusName.CREATED.value,
    ) -> Order:

        cart: Cart | None = None

        def operation() -> Order:
            nonlocal cart
            status = self._get_required_status(status_name=status_name)
            cart = self._get_required_cart_for_user(user_id=user_id)
            rows = self._get_cart_rows(cart_id=cart.id)
            order = self._build_order(
                user_id=user_id,
                status_id=status.id,
                rows=rows,
                address=address,
                address_raw=address_raw,
                postal_code=postal_code,
                address_metadata=address_metadata,
                address_enrichment_status=address_enrichment_status,
            )
            self._create_order_items(order_id=order.id, rows=rows)
            self._clear_cart(cart_id=cart.id)
            self.flush()
            return self.get_required_by_id(order_id=order.id)

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
            order = self.get_required_by_id(order_id)
            order.address = address
            order.postal_code = postal_code
            order.address_metadata = address_metadata
            order.address_enrichment_status = address_enrichment_status
            return order

        return self.run_in_transaction(operation)

