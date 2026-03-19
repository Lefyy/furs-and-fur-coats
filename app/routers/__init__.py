from app.routers.cart_router import router as cart_router
from app.routers.catalog_router import router as catalog_router
from app.routers.order_router import router as order_router
from app.routers.auth_router import router as auth_router
from app.routers.admin_product_description_router import router as admin_product_description_router

__all__ = ["auth_router", "catalog_router", "cart_router", "order_router", "admin_product_description_router"]
