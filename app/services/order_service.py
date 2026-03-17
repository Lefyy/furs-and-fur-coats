from app.exceptions import BadRequestError
from app.schemas import OrderResponse
from infrastructure.db.repositories import OrderRepository


class OrderService:
    def __init__(self, order_repository: OrderRepository) -> None:
        self.order_repository = order_repository

    def create_order(self, user_id: int, address: str) -> OrderResponse:
        try:
            order = self.order_repository.create(user_id=user_id, address=address, status_name="created")
        except ValueError as exc:
            raise BadRequestError(str(exc)) from exc

        refreshed = self.order_repository.get_by_id(order_id=order.id)
        if refreshed is None:
            raise BadRequestError("Order was not created")

        return OrderResponse(
            id=refreshed.id,
            user_id=refreshed.user_id,
            status=refreshed.status.name,
            total_price=refreshed.total_price,
            address=refreshed.address,
            items=refreshed.items,
        )
