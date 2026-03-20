from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from app.config import settings
from app.exceptions import BadRequestError, NotFoundError
from app.gateways.openrouter import OpenRouterGateway
from app.utils.product_description_prompt import build_product_description_messages
from infrastructure.db.models import Product, ProductDescriptionGeneration
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
                attributes=self._build_prompt_attributes(product),
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
    def _serialize_price(price: Decimal | Any) -> str | None:
        if isinstance(price, Decimal):
            return format(price, "f")
        return str(price) if price is not None else None

    @classmethod
    def _build_prompt_attributes(cls, product: Product) -> dict[str, Any]:
        return {
            "brand": product.brand,
            "fur_type": product.fur_type,
            "color": product.color,
            "length": product.length,
            "size_range": product.size_range,
            "features": product.features,
            "material_composition": product.material_composition,
            "target_audience": product.target_audience,
            "season": product.season,
            "style_tags": product.style_tags,
            "price": cls._serialize_price(product.price),
            "category_id": product.category_id,
        }
