from app.routers.cart_router import router as cart_router
from app.routers.catalog_router import router as catalog_router
from app.routers.order_router import router as order_router

__all__ = ["catalog_router", "cart_router", "order_router"]
