from fastapi import APIRouter, Depends, status

from app.routers.dependencies import get_current_staff_user, get_product_description_generation_service
from app.schemas.product_description_generation_schema import ProductDescriptionGenerationResponse
from app.services.product_description_generation_service import ProductDescriptionGenerationService
from app.tasks.product_description_tasks import generate_product_description

router = APIRouter(prefix="/admin", tags=["admin-product-descriptions"], dependencies=[Depends(get_current_staff_user)])


@router.post(
    "/products/{product_id}/description-generations",
    response_model=ProductDescriptionGenerationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_product_description_generation(
    product_id: int,
    service: ProductDescriptionGenerationService = Depends(get_product_description_generation_service),
) -> ProductDescriptionGenerationResponse:
    generation = service.create_generation(product_id=product_id)
    generate_product_description.delay(generation.id)
    return generation


@router.get(
    "/products/{product_id}/description-generations/latest",
    response_model=ProductDescriptionGenerationResponse,
)
def get_latest_product_description_generation(
    product_id: int,
    service: ProductDescriptionGenerationService = Depends(get_product_description_generation_service),
) -> ProductDescriptionGenerationResponse:
    return service.get_latest_generation(product_id=product_id)


@router.post(
    "/products/{product_id}/description-generations/{generation_id}/apply",
    response_model=ProductDescriptionGenerationResponse,
)
def apply_product_description_generation(
    product_id: int,
    generation_id: int,
    service: ProductDescriptionGenerationService = Depends(get_product_description_generation_service),
) -> ProductDescriptionGenerationResponse:
    return service.apply_generation(product_id=product_id, generation_id=generation_id)


@router.post(
    "/products/{product_id}/description-generations/{generation_id}/retry",
    response_model=ProductDescriptionGenerationResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def retry_product_description_generation(
    product_id: int,
    generation_id: int,
    service: ProductDescriptionGenerationService = Depends(get_product_description_generation_service),
) -> ProductDescriptionGenerationResponse:
    generation = service.retry_generation(product_id=product_id, generation_id=generation_id)
    generate_product_description.delay(generation.id)
    return generation
