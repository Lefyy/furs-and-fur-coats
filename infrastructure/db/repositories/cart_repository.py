from sqlalchemy import delete, select
from sqlalchemy.orm import Session, joinedload

from infrastructure.db.models import Cart, CartItem
from infrastructure.db.repositories.base import BaseRepository


class CartRepository(BaseRepository):
    def __init__(self, session: Session) -> None:
        super().__init__(session)

    def _get_cart_for_user(self, user_id: int) -> Cart | None:
        stmt = select(Cart).where(Cart.user_id == user_id)
        return self.session.scalar(stmt)

    def _get_cart_item(self, cart_id: int, product_id: int) -> CartItem | None:
        stmt = select(CartItem).where(
            CartItem.cart_id == cart_id,
            CartItem.product_id == product_id,
        )
        return self.session.scalar(stmt)

    def _get_or_create_cart(self, user_id: int) -> Cart:
        cart = self._get_cart_for_user(user_id=user_id)
        if cart is not None:
            return cart

        cart = Cart(user_id=user_id)
        self.session.add(cart)
        self.session.flush([cart])
        return cart

    def get_or_create_for_user(self, user_id: int) -> Cart:
        def operation() -> Cart:
            return self._get_or_create_cart(user_id=user_id)
        return self.run_in_transaction(operation)

    def get_for_user(self, user_id: int) -> Cart | None:
        stmt = (
            select(Cart)
            .where(Cart.user_id == user_id)
            .options(joinedload(Cart.items).joinedload(CartItem.product))
        )
        return self.session.scalar(stmt)

    def add_item(self, user_id: int, product_id: int, quantity: int) -> CartItem:
        def operation() -> CartItem:
            cart = self._get_or_create_cart(user_id=user_id)
            cart_item = self._get_cart_item(cart_id=cart.id, product_id=product_id)
            if cart_item is None:
                cart_item = CartItem(cart_id=cart.id, product_id=product_id, quantity=quantity)
                self.session.add(cart_item)
            else:
                cart_item.quantity += quantity
            
            return cart_item

        return self.run_in_transaction(operation)

    def update_item_quantity(self, user_id: int, product_id: int, quantity: int) -> CartItem | None:
        def operation() -> CartItem | None:
            cart = self._get_cart_for_user(user_id=user_id)
            if cart is None:
                return None

            cart_item = self._get_cart_item(cart_id=cart.id, product_id=product_id)
            if cart_item is None:
                return None

            cart_item.quantity = quantity
            return cart_item

        return self.run_in_transaction(operation)

    def remove_item(self, user_id: int, product_id: int) -> bool:
        def operation() -> bool:
            cart = self._get_cart_for_user(user_id=user_id)
            if cart is None:
                return False

            cart_item = self._get_cart_item(cart_id=cart.id, product_id=product_id)
            if cart_item is None:
                return False

            self.session.delete(cart_item)
            return True

        return self.run_in_transaction(operation)

    def clear(self, user_id: int) -> None:
        def operation() -> None:
            cart = self._get_cart_for_user(user_id=user_id)
            if cart is None:
                return

            stmt = delete(CartItem).where(CartItem.cart_id == cart.id)
            self.session.execute(stmt)

        self.run_in_transaction(operation)