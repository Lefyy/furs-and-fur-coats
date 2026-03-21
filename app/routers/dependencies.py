from fastapi import Depends, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.config import settings
from app.exceptions import ForbiddenError, UnauthorizedError
from app.gateways.dadata import DadataGateway
from app.gateways.openrouter import OpenRouterGateway
from app.services.order_service import OrderService
from app.services.cart_service import CartService
from app.services.catalog_service import CatalogService
from app.services.address_formatting_service import AddressFormattingService
from app.services.auth_service import AuthService
from app.services.auth_token_factory import AuthTokenFactory
from app.services.contact_formatting_service import ContactFormattingService
from app.services.oauth_identity_policy import OAuthIdentityPolicy
from app.services.oauth_refresh_token_service import OAuthRefreshTokenService
from app.services.oauth_state_service import OAuthStateService
from app.services.product_description_generation_service import ProductDescriptionGenerationService
from app.utils.oauth import HttpOAuthGateway
from app.utils.security import decode_access_token
from infrastructure.db.db_session import get_db_session
from infrastructure.db.models import User
from infrastructure.db.repositories import CartRepository, CategoryRepository, OrderRepository, ProductRepository, UserRepository
from infrastructure.db.repositories.product_description_generation_repository import ProductDescriptionGenerationRepository


security = HTTPBearer(auto_error=False)


def get_user_repository(session: Session = Depends(get_db_session)) -> UserRepository:
    return UserRepository(session=session)


def get_current_user_id(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    authorization: str | None = Header(default=None),
) -> int:
    token: str | None = None

    if isinstance(credentials, HTTPAuthorizationCredentials):
        token = credentials.credentials
    elif authorization:
        scheme, _, value = authorization.partition(" ")
        if scheme.lower() != "bearer" or not value:
            raise UnauthorizedError("Invalid token")
        token = value

    if token is None:
        raise UnauthorizedError("Invalid token")
    payload = decode_access_token(token=token, secret_key=settings.jwt_secret_key)

    subject = payload.get("sub")
    if subject is None:
        raise UnauthorizedError("Invalid token")

    return int(subject)


def get_current_staff_user(
    user_id: int = Depends(get_current_user_id),
    user_repository: UserRepository = Depends(get_user_repository),
) -> User:
    user = user_repository.get_by_id(user_id)
    if user is None:
        raise UnauthorizedError("Invalid token")
    if not user.is_staff:
        raise ForbiddenError("Staff access required")
    return user


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
    user_repository = get_user_repository(session=session)
    dadata_gateway = DadataGateway()
    return AuthService(
        user_repository=user_repository,
        oauth_gateway=HttpOAuthGateway(),
        oauth_state_service=OAuthStateService(),
        oauth_refresh_token_service=OAuthRefreshTokenService(ttl_seconds=settings.oauth_refresh_token_ttl_seconds),
        contact_formatting_service=ContactFormattingService(dadata_gateway=dadata_gateway),
        jwt_secret=settings.jwt_secret_key,
        jwt_expire_minutes=settings.jwt_expire_minutes,
        oauth_identity_policy=OAuthIdentityPolicy(user_repository=user_repository),
        auth_token_factory=AuthTokenFactory(
            jwt_secret=settings.jwt_secret_key,
            jwt_expire_minutes=settings.jwt_expire_minutes,
        ),
    )


def get_product_description_generation_service(session: Session = Depends(get_db_session)) -> ProductDescriptionGenerationService:
    return ProductDescriptionGenerationService(
        product_repository=ProductRepository(session=session),
        generation_repository=ProductDescriptionGenerationRepository(session=session),
        openrouter_gateway=OpenRouterGateway(),
    )

