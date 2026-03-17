from decimal import Decimal

from fastapi import APIRouter, Depends, Query

from app.routers.dependencies import get_catalog_service
from app.schemas import CategoriesResponse, ProductResponse, ProductsListResponse
from app.services import CatalogService

router = APIRouter(tags=["catalog"])


@router.get("/products", response_model=ProductsListResponse)
def get_products(
    min_price: Decimal | None = Query(default=None, ge=0),
    max_price: Decimal | None = Query(default=None, ge=0),
    category_id: int | None = Query(default=None, ge=1),
    sort: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    service: CatalogService = Depends(get_catalog_service),
) -> ProductsListResponse:
    return service.list_products(
        min_price=min_price,
        max_price=max_price,
        category_id=category_id,
        sort=sort,
        limit=limit,
        offset=offset,
    )


@router.get("/product/{product_id}", response_model=ProductResponse)
def get_product(product_id: int, service: CatalogService = Depends(get_catalog_service)) -> ProductResponse:
    return service.get_product(product_id=product_id)


@router.get("/categories", response_model=CategoriesResponse)
def get_categories(service: CatalogService = Depends(get_catalog_service)) -> CategoriesResponse:
    return service.list_categories()
