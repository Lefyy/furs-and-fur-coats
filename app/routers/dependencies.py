from fastapi import Depends
from sqlalchemy.orm import Session

from app.config import settings
from app.services import CartService, CatalogService, OrderService
from app.services.auth_service import AuthService
from app.utils.oauth import HttpOAuthGateway
from infrastructure.db.db_session import get_db_session
from infrastructure.db.repositories import CartRepository, CategoryRepository, OrderRepository, ProductRepository, UserRepository


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
    return OrderService(order_repository=OrderRepository(session=session))


def get_auth_service(session: Session = Depends(get_db_session)) -> AuthService:
    return AuthService(
        user_repository=UserRepository(session=session),
        oauth_gateway=HttpOAuthGateway(),
        jwt_secret=settings.jwt_secret_key,
        jwt_expire_minutes=settings.jwt_expire_minutes,
    )
