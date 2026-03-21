from decimal import Decimal

from app.exceptions import BadRequestError, NotFoundError
from app.schemas import CartItemResponse, CartResponse
from infrastructure.db.models import Cart, CartItem, Product
from infrastructure.db.repositories import CartRepository, ProductRepository


class CartService:
    def __init__(self, cart_repository: CartRepository, product_repository: ProductRepository) -> None:
        self.cart_repository = cart_repository
        self.product_repository = product_repository

    def get_cart(self, user_id: int) -> CartResponse:
        return self._get_cart_response(user_id=user_id)

    def add_item(self, user_id: int, product_id: int, quantity: int) -> CartResponse:
        self._validate_quantity(quantity=quantity)
        self._get_required_product(product_id=product_id)

        self.cart_repository.add_item(user_id=user_id, product_id=product_id, quantity=quantity)
        return self._get_cart_response(user_id=user_id)

    def update_item(self, user_id: int, product_id: int, quantity: int) -> CartResponse:
        self._validate_quantity(quantity=quantity)
        updated = self.cart_repository.update_item_quantity(user_id=user_id, product_id=product_id, quantity=quantity)
        if updated is None:
            raise NotFoundError("Cart item not found")

        return self._get_cart_response(user_id=user_id)

    def remove_item(self, user_id: int, product_id: int) -> CartResponse:
        removed = self.cart_repository.remove_item(user_id=user_id, product_id=product_id)
        if not removed:
            raise NotFoundError("Cart item not found")
        
        return self._get_cart_response(user_id=user_id)

    @staticmethod
    def _validate_quantity(quantity: int) -> None:
        if quantity <= 0:
            raise BadRequestError("quantity must be greater than zero")

    def _get_required_product(self, product_id: int) -> Product:
        product = self.product_repository.get_by_id(product_id=product_id)
        if product is None:
            raise NotFoundError("Product not found")
        return product

    def _get_cart_response(self, user_id: int) -> CartResponse:
        cart = self.cart_repository.get_for_user(user_id=user_id)
        return self._to_response(user_id=user_id, cart=cart)

    @classmethod
    def _to_response(cls, user_id: int, cart: Cart | None) -> CartResponse:
        if cart is None:
            return cls._empty_cart_response(user_id=user_id)

        items = [cls._build_cart_item_response(item=item) for item in cart.items]
        total = cls._calculate_total(cart=cart)

        return CartResponse(id=cart.id, user_id=user_id, items=items, total_price=total)
    
    @staticmethod
    def _empty_cart_response(user_id: int) -> CartResponse:
        return CartResponse(id=None, user_id=user_id, items=[], total_price=Decimal("0.00"))

    @staticmethod
    def _build_cart_item_response(item: CartItem) -> CartItemResponse:
        price = Decimal(item.product.price)
        return CartItemResponse(
            id=item.id,
            product_id=item.product_id,
            quantity=item.quantity,
            price=price,
            product_name=item.product.name,
        )

    @staticmethod
    def _calculate_total(cart: Cart) -> Decimal:
        return sum((Decimal(item.product.price) * item.quantity for item in cart.items), start=Decimal("0.00"))

