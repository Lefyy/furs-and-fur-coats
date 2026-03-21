from fastapi import APIRouter, Depends

from app.routers.dependencies import get_cart_service, get_current_user_id
from app.schemas import CartItemRequest, CartResponse, DeleteCartItemRequest
from app.services.cart_service import CartService

router = APIRouter(tags=["cart"])


@router.get("/cart", response_model=CartResponse)
def get_cart(
    user_id: int = Depends(get_current_user_id),
    service: CartService = Depends(get_cart_service),
) -> CartResponse:
    return service.get_cart(user_id=user_id)


@router.post("/cart", response_model=CartResponse)
def add_to_cart(
    payload: CartItemRequest,
    user_id: int = Depends(get_current_user_id),
    service: CartService = Depends(get_cart_service),
) -> CartResponse:
    return service.add_item(user_id=user_id, product_id=payload.product_id, quantity=payload.quantity)


@router.put("/cart", response_model=CartResponse)
def update_cart_item(
    payload: CartItemRequest,
    user_id: int = Depends(get_current_user_id),
    service: CartService = Depends(get_cart_service),
) -> CartResponse:
    return service.update_item(user_id=user_id, product_id=payload.product_id, quantity=payload.quantity)


@router.delete("/cart", response_model=CartResponse)
def delete_cart_item(
    payload: DeleteCartItemRequest,
    user_id: int = Depends(get_current_user_id),
    service: CartService = Depends(get_cart_service),
) -> CartResponse:
    return service.remove_item(user_id=user_id, product_id=payload.product_id)
