from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

class OrderCreateRequest(BaseModel):
    address: str = Field(min_length=3)


class OrderItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    product_id: int
    quantity: int
    price: Decimal


class OrderResponse(BaseModel):
    id: int
    user_id: int
    status: str
    total_price: Decimal
    address: str
    items: list[OrderItemResponse]