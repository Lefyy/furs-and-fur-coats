import logging

from app.exceptions import BadRequestError
from app.schemas import OrderResponse
from app.services.address_formatting_service import AddressFormattingService
from app.tasks.enrichment_tasks import enrich_order_address
from infrastructure.db.repositories import OrderRepository


logger = logging.getLogger(__name__)


class OrderService:
    def __init__(self, order_repository: OrderRepository, address_formatting_service: AddressFormattingService) -> None:
        self.order_repository = order_repository
        self.address_formatting_service = address_formatting_service

    def create_order(self, user_id: int, address: str) -> OrderResponse:
        formatting_result = self.address_formatting_service.format(address=address)

        try:
            order = self.order_repository.create(
                user_id=user_id,
                address=formatting_result.canonical,
                address_raw=address,
                postal_code=formatting_result.postal_code,
                address_metadata=formatting_result.metadata,
                address_enrichment_status=formatting_result.status,
                status_name="created",
            )
        except ValueError as exc:
            raise BadRequestError(str(exc)) from exc
        
        if formatting_result.is_degraded:
            logger.warning("Saved order in degraded mode", extra={"user_id": user_id, "order_id": order.id})
            enrich_order_address.delay(order_id=order.id)

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
