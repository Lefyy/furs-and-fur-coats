from fastapi import Depends
from sqlalchemy.orm import Session

from app.config import settings
from app.gateways.dadata import DadataGateway
from app.gateways.openrouter import OpenRouterGateway
from app.services import CartService, CatalogService, OrderService
from app.services.product_description_generation_service import ProductDescriptionGenerationService
from app.services.address_formatting_service import AddressFormattingService
from app.services.auth_service import AuthService
from app.services.contact_formatting_service import ContactFormattingService
from app.services.oauth_refresh_token_service import OAuthRefreshTokenService
from app.services.oauth_state_service import OAuthStateService
from app.utils.oauth import HttpOAuthGateway
from infrastructure.db.db_session import get_db_session
from infrastructure.db.repositories import CartRepository, CategoryRepository, OrderRepository, ProductRepository, UserRepository
from infrastructure.db.repositories.product_description_generation_repository import ProductDescriptionGenerationRepository


def get_user_repository(session: Session = Depends(get_db_session)) -> UserRepository:
    return UserRepository(session=session)


def get_catalog_service(session: Session = Depends(get_db_session)) -> CatalogService:
    return CatalogService(
        product_repository=ProductRepository(session=session),
        category_repository=CategoryRepository(session=session),
    )


def get_cart_service(session: Session = Depends(get_db_session)) -> CartService:
    return CartService(
        cart_repository=CartRepository(session=session),
        product_repository=ProductRepository(session=session),
    )


def get_order_service(session: Session = Depends(get_db_session)) -> OrderService:
    dadata_gateway = DadataGateway()
    return OrderService(
        order_repository=OrderRepository(session=session),
        address_formatting_service=AddressFormattingService(dadata_gateway=dadata_gateway),
    )


def get_auth_service(session: Session = Depends(get_db_session)) -> AuthService:
    dadata_gateway = DadataGateway()
    return AuthService(
        user_repository=get_user_repository(session=session),
        oauth_gateway=HttpOAuthGateway(),
        oauth_state_service=OAuthStateService(),
        oauth_refresh_token_service=OAuthRefreshTokenService(ttl_seconds=settings.oauth_refresh_token_ttl_seconds),
        contact_formatting_service=ContactFormattingService(dadata_gateway=dadata_gateway),
        jwt_secret=settings.jwt_secret_key,
        jwt_expire_minutes=settings.jwt_expire_minutes,
    )


def get_product_description_generation_service(session: Session = Depends(get_db_session)) -> ProductDescriptionGenerationService:
    return ProductDescriptionGenerationService(
        product_repository=ProductRepository(session=session),
        generation_repository=ProductDescriptionGenerationRepository(session=session),
        openrouter_gateway=OpenRouterGateway(),
    )

