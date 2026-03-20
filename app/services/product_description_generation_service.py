from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from app.config import settings
from app.exceptions import BadRequestError, NotFoundError
from app.gateways.openrouter import OpenRouterGateway
from app.utils.product_description_prompt import ProductPromptContext, build_product_description_messages
from infrastructure.db.models import Category, Product, ProductDescriptionGeneration
from infrastructure.db.repositories import ProductRepository
from infrastructure.db.repositories.product_description_generation_repository import ProductDescriptionGenerationRepository


@dataclass(slots=True)
class ProductDescriptionGenerationResult:
    generation: ProductDescriptionGeneration
    product: Product


class ProductDescriptionGenerationService:
    def __init__(
        self,
        *,
        product_repository: ProductRepository,
        generation_repository: ProductDescriptionGenerationRepository,
        openrouter_gateway: OpenRouterGateway,
    ) -> None:
        self.product_repository = product_repository
        self.generation_repository = generation_repository
        self.openrouter_gateway = openrouter_gateway

    def create_generation(self, *, product_id: int) -> ProductDescriptionGeneration:
        product = self._get_product(product_id)
        if self.generation_repository.has_active_generation(product_id=product.id):
            raise BadRequestError("Active generation already exists for this product")

        return self.generation_repository.run_in_transaction(
            lambda: self.generation_repository.create(product_id=product.id, status="queued")
        )

    def get_latest_generation(self, *, product_id: int) -> ProductDescriptionGeneration:
        self._get_product(product_id)
        generation = self.generation_repository.get_latest_by_product_id(product_id)
        if generation is None:
            raise NotFoundError("Product description generation not found")
        return generation

    def get_generation(self, *, product_id: int, generation_id: int) -> ProductDescriptionGeneration:
        self._get_product(product_id)
        generation = self.generation_repository.get_by_id(generation_id)
        if generation is None or generation.product_id != product_id:
            raise NotFoundError("Product description generation not found")
        return generation

    def generate_text(self, *, generation_id: int) -> ProductDescriptionGenerationResult:
        generation = self.generation_repository.get_by_id(generation_id)
        if generation is None:
            raise NotFoundError("Product description generation not found")

        product = self._get_product(generation.product_id)
        generated_text = self.openrouter_gateway.generate_product_description(
            messages=build_product_description_messages(
                product_name=product.name,
                context=self._build_prompt_context(product),
            )
        )

        def operation() -> ProductDescriptionGenerationResult:
            saved_generation = self.generation_repository.save_generation_result(
                generation_id=generation_id,
                generated_text=generated_text,
                model_name=settings.openrouter_model,
                prompt_version=settings.openrouter_prompt_version,
                status="completed",
            )
            assert saved_generation is not None
            return ProductDescriptionGenerationResult(generation=saved_generation, product=product)

        return self.generation_repository.run_in_transaction(operation)

    def apply_generation(self, *, product_id: int, generation_id: int) -> ProductDescriptionGeneration:
        generation = self.get_generation(product_id=product_id, generation_id=generation_id)
        if not generation.generated_text:
            raise BadRequestError("Generation result is empty")

        product = self._get_product(product_id)

        def operation() -> ProductDescriptionGeneration:
            product.old_description = product.description
            product.description = generation.generated_text
            applied_generation = self.generation_repository.mark_as_applied(generation_id=generation.id)
            assert applied_generation is not None
            self.product_repository.flush()
            return applied_generation

        return self.product_repository.run_in_transaction(operation)

    def retry_generation(self, *, product_id: int, generation_id: int) -> ProductDescriptionGeneration:
        self.get_generation(product_id=product_id, generation_id=generation_id)
        if self.generation_repository.has_active_generation(product_id=product_id):
            raise BadRequestError("Active generation already exists for this product")
        return self.create_generation(product_id=product_id)

    def _get_product(self, product_id: int) -> Product:
        product = self.product_repository.get_by_id(product_id)
        if product is None:
            raise NotFoundError("Product not found")
        return product

    @staticmethod
    def _serialize_price(price: Decimal | object) -> str | None:
        if isinstance(price, Decimal):
            return format(price, "f")
        return str(price) if price is not None else None
    
    @staticmethod
    def _build_category_path(category: Category | None) -> list[str]:
        if category is None:
            return []

        path: list[str] = []
        current: Category | None = category
        seen_ids: set[int] = set()
        while current is not None and current.id not in seen_ids:
            seen_ids.add(current.id)
            path.append(current.name)
            current = current.parent

        return list(reversed(path))
    
    @staticmethod
    def _serialize_prompt_list(values: object) -> list[str] | None:
        if not isinstance(values, list):
            return None if values is None else [str(values)]

        serialized_values = [str(value) for value in values if value not in (None, "")]
        return serialized_values or None

    @classmethod
    def _build_prompt_context(cls, product: Product) -> ProductPromptContext:
        category_path = cls._build_category_path(product.category)
        parent_category_name = category_path[-2] if len(category_path) > 1 else None

        return ProductPromptContext(
            brand=product.brand,
            fur_type=product.fur_type,
            color=product.color,
            length=product.length,
            size_range=product.size_range,
            features=cls._serialize_prompt_list(product.features),
            material_composition=product.material_composition,
            target_audience=product.target_audience,
            season=product.season,
            style_tags=cls._serialize_prompt_list(product.style_tags),
            price=cls._serialize_price(product.price),
            category_name=product.category.name if product.category is not None else None,
            parent_category_name=parent_category_name,
            category_path=category_path or None,
        )

