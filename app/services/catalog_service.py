from decimal import Decimal

from app.exceptions import BadRequestError, NotFoundError
from app.schemas import CategoriesResponse, CategoryNodeResponse, ProductResponse, ProductsListResponse
from infrastructure.db.repositories import CategoryRepository, ProductRepository


class CatalogService:
    def __init__(self, product_repository: ProductRepository, category_repository: CategoryRepository) -> None:
        self.product_repository = product_repository
        self.category_repository = category_repository

    def list_products(
        self,
        min_price: Decimal | None,
        max_price: Decimal | None,
        category_id: int | None,
        sort: str | None,
        limit: int,
        offset: int,
    ) -> ProductsListResponse:
        if min_price is not None and max_price is not None and min_price > max_price:
            raise BadRequestError("min_price must be less than or equal to max_price")

        if sort not in {None, "price_asc", "price_desc"}:
            raise BadRequestError("sort must be one of: price_asc, price_desc")

        products = self.product_repository.list(
            min_price=min_price,
            max_price=max_price,
            category_id=category_id,
            sort=sort,
            limit=limit,
            offset=offset,
        )
        return ProductsListResponse(items=[ProductResponse.model_validate(product) for product in products], limit=limit, offset=offset)

    def get_product(self, product_id: int) -> ProductResponse:
        product = self.product_repository.get_by_id(product_id=product_id)
        if product is None:
            raise NotFoundError("Product not found")
        return ProductResponse.model_validate(product)

    def list_categories(self) -> CategoriesResponse:
        tree = self.category_repository.get_tree()
        return CategoriesResponse(items=[CategoryNodeResponse.model_validate(node) for node in tree])
