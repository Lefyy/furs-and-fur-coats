from fastapi import APIRouter, Depends

from app.auth import get_current_user_id
from app.routers.dependencies import get_order_service
from app.schemas import OrderCreateRequest, OrderResponse
from app.services import OrderService

router = APIRouter(tags=["orders"])


@router.post("/order", response_model=OrderResponse)
def create_order(
    payload: OrderCreateRequest,
    user_id: int = Depends(get_current_user_id),
    service: OrderService = Depends(get_order_service),
) -> OrderResponse:
    return service.create_order(user_id=user_id, address=payload.address)
