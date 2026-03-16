from sqlalchemy import delete, select
from sqlalchemy.orm import Session, joinedload

from infrastructure.db.models import Cart, CartItem
from infrastructure.db.repositories.base import BaseRepository


class CartRepository(BaseRepository):
    def __init__(self, session: Session) -> None:
        super().__init__(session)

    def get_or_create_for_user(self, user_id: int) -> Cart:
        stmt = select(Cart).where(Cart.user_id == user_id)
        cart = self.session.scalar(stmt)
        if cart is not None:
            return cart

        cart = Cart(user_id=user_id)
        self.session.add(cart)
        self.flush()
        return cart

    def get_for_user(self, user_id: int) -> Cart | None:
        stmt = (
            select(Cart)
            .where(Cart.user_id == user_id)
            .options(joinedload(Cart.items).joinedload(CartItem.product))
        )
        return self.session.scalar(stmt)

    def add_item(self, user_id: int, product_id: int, quantity: int) -> CartItem:
        cart = self.get_or_create_for_user(user_id=user_id)
        stmt = select(CartItem).where(
            CartItem.cart_id == cart.id,
            CartItem.product_id == product_id,
        )
        cart_item = self.session.scalar(stmt)
        if cart_item is None:
            cart_item = CartItem(cart_id=cart.id, product_id=product_id, quantity=quantity)
            self.session.add(cart_item)
        else:
            cart_item.quantity += quantity

        self.flush()
        return cart_item

    def update_item_quantity(self, user_id: int, product_id: int, quantity: int) -> CartItem | None:
        cart = self.get_for_user(user_id=user_id)
        if cart is None:
            return None

        stmt = select(CartItem).where(
            CartItem.cart_id == cart.id,
            CartItem.product_id == product_id,
        )
        cart_item = self.session.scalar(stmt)
        if cart_item is None:
            return None

        cart_item.quantity = quantity
        self.flush()
        return cart_item

    def remove_item(self, user_id: int, product_id: int) -> bool:
        cart = self.get_for_user(user_id=user_id)
        if cart is None:
            return False

        stmt = select(CartItem).where(
            CartItem.cart_id == cart.id,
            CartItem.product_id == product_id,
        )
        cart_item = self.session.scalar(stmt)
        if cart_item is None:
            return False

        self.session.delete(cart_item)
        self.flush()
        return True

    def clear(self, user_id: int) -> None:
        cart = self.get_for_user(user_id=user_id)
        if cart is None:
            return

        stmt = delete(CartItem).where(CartItem.cart_id == cart.id)
        self.session.execute(stmt)
        self.flush()
