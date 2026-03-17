from decimal import Decimal

from app.exceptions import BadRequestError, NotFoundError
from app.schemas import CartResponse
from infrastructure.db.models import Cart
from infrastructure.db.repositories import CartRepository, ProductRepository


class CartService:
    def __init__(self, cart_repository: CartRepository, product_repository: ProductRepository) -> None:
        self.cart_repository = cart_repository
        self.product_repository = product_repository

    def get_cart(self, user_id: int) -> CartResponse:
        cart = self.cart_repository.get_for_user(user_id=user_id)
        return self._to_response(user_id=user_id, cart=cart)

    def add_item(self, user_id: int, product_id: int, quantity: int) -> CartResponse:
        if quantity <= 0:
            raise BadRequestError("quantity must be greater than zero")

        product = self.product_repository.get_by_id(product_id=product_id)
        if product is None:
            raise NotFoundError("Product not found")

        self.cart_repository.add_item(user_id=user_id, product_id=product_id, quantity=quantity)
        cart = self.cart_repository.get_for_user(user_id=user_id)
        return self._to_response(user_id=user_id, cart=cart)

    def update_item(self, user_id: int, product_id: int, quantity: int) -> CartResponse:
        if quantity <= 0:
            raise BadRequestError("quantity must be greater than zero")

        updated = self.cart_repository.update_item_quantity(user_id=user_id, product_id=product_id, quantity=quantity)
        if updated is None:
            raise NotFoundError("Cart item not found")

        cart = self.cart_repository.get_for_user(user_id=user_id)
        return self._to_response(user_id=user_id, cart=cart)

    def remove_item(self, user_id: int, product_id: int) -> CartResponse:
        removed = self.cart_repository.remove_item(user_id=user_id, product_id=product_id)
        if not removed:
            raise NotFoundError("Cart item not found")

        cart = self.cart_repository.get_for_user(user_id=user_id)
        return self._to_response(user_id=user_id, cart=cart)

    @staticmethod
    def _to_response(user_id: int, cart: Cart | None) -> CartResponse:
        if cart is None:
            return CartResponse(id=None, user_id=user_id, items=[], total_price=Decimal("0.00"))

        items = []
        total = Decimal("0.00")
        for item in cart.items:
            price = Decimal(item.product.price)
            total += price * item.quantity
            items.append(
                {
                    "id": item.id,
                    "product_id": item.product_id,
                    "quantity": item.quantity,
                    "price": price,
                    "product_name": item.product.name,
                }
            )

        return CartResponse(id=cart.id, user_id=user_id, items=items, total_price=total)
