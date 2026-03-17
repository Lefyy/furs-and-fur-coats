from fastapi import FastAPI

from app.config import settings
from app.routers import auth_router, cart_router, catalog_router, order_router


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name)

    @app.get("/health")
    async def healthcheck() -> dict[str, str]:
        return {"status": "ok"}
    
    app.include_router(auth_router)
    app.include_router(catalog_router)
    app.include_router(cart_router)
    app.include_router(order_router)

    return app


app = create_app()
