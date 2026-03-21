from importlib import import_module


__all__ = [
    "CatalogService",
    "CartService",
    "OrderService",
    "AuthService",
    "AuthTokenFactory",
    "OAuthIdentityPolicy",
    "OAuthRefreshTokenService",
    "OAuthStateService",
    "ProductDescriptionGenerationService",
]

_MODULE_BY_EXPORT = {
    "CatalogService": "app.services.catalog_service",
    "CartService": "app.services.cart_service",
    "OrderService": "app.services.order_service",
    "AuthService": "app.services.auth_service",
    "AuthTokenFactory": "app.services.auth_token_factory",
    "OAuthIdentityPolicy": "app.services.oauth_identity_policy",
    "OAuthRefreshTokenService": "app.services.oauth_refresh_token_service",
    "OAuthStateService": "app.services.oauth_state_service",
    "ProductDescriptionGenerationService": "app.services.product_description_generation_service",
}


def __getattr__(name: str):
    module_name = _MODULE_BY_EXPORT.get(name)
    if module_name is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    module = import_module(module_name)
    return getattr(module, name)
