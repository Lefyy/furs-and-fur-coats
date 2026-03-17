from decimal import Decimal

from pydantic import BaseModel, Field


class CartItemRequest(BaseModel):
    product_id: int
    quantity: int = Field(gt=0)


class CartItemResponse(BaseModel):
    id: int
    product_id: int
    quantity: int
    price: Decimal
    product_name: str


class CartResponse(BaseModel):
    id: int | None
    user_id: int
    items: list[CartItemResponse]
    total_price: Decimal


class DeleteCartItemRequest(BaseModel):
    product_id: int
