import logging

from app.exceptions import BadRequestError
from app.schemas import OrderResponse
from app.services.address_formatting_service import AddressFormattingResult, AddressFormattingService
from app.tasks.enrichment_tasks import enrich_order_address
from infrastructure.db.models import Order
from infrastructure.db.repositories import OrderRepository


logger = logging.getLogger(__name__)


class OrderService:
    def __init__(self, order_repository: OrderRepository, address_formatting_service: AddressFormattingService) -> None:
        self.order_repository = order_repository
        self.address_formatting_service = address_formatting_service

    def create_order(self, user_id: int, address: str) -> OrderResponse:
        formatting_result = self.address_formatting_service.format(address=address)
        order = self._create_order_record(user_id=user_id, address=address, formatting_result=formatting_result)
        self._enqueue_degraded_enrichment_if_needed(user_id=user_id, order=order, is_degraded=formatting_result.is_degraded)
        loaded_order = self._get_fully_loaded_order(order=order)
        return self._to_response(order=loaded_order)

    def _create_order_record(
        self,
        user_id: int,
        address: str,
        formatting_result: AddressFormattingResult,
    ) -> Order:
        try:
            return self.order_repository.create(
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
        
    def _enqueue_degraded_enrichment_if_needed(self, user_id: int, order: Order, is_degraded: bool) -> None:
        if not is_degraded:
            return

        logger.warning("Saved order in degraded mode", extra={"user_id": user_id, "order_id": order.id})
        enrich_order_address.delay(order_id=order.id)

    def _get_fully_loaded_order(self, order: Order) -> Order:
        if order.status is not None and order.items is not None:
            return order
        return self.order_repository.get_required_by_id(order_id=order.id)

    @staticmethod
    def _to_response(order: Order) -> OrderResponse:
        return OrderResponse(
            id=order.id,
            user_id=order.user_id,
            status=order.status.name,
            total_price=order.total_price,
            address=order.address,
            items=order.items,
        )
