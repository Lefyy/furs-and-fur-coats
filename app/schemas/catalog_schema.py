from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class ProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str
    price: Decimal
    category_id: int
    image_url: str | None


class ProductsListResponse(BaseModel):
    items: list[ProductResponse]
    limit: int
    offset: int


class CategoryNodeResponse(BaseModel):
    id: int
    name: str
    parent_id: int | None
    children: list["CategoryNodeResponse"] = Field(default_factory=list)


class CategoriesResponse(BaseModel):
    items: list[CategoryNodeResponse]


CategoryNodeResponse.model_rebuild()
