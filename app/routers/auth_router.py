from urllib.parse import urlencode

from fastapi import APIRouter, Depends
from fastapi.responses import RedirectResponse

from app.config import settings
from app.routers.dependencies import get_auth_service
from app.schemas.auth_schema import LoginRequest, RegisterRequest, TokenResponse
from app.services.auth_service import AuthService, OAuthRequest

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse)
def register(payload: RegisterRequest, service: AuthService = Depends(get_auth_service)) -> TokenResponse:
    return service.register(email=payload.email, phone=payload.phone, password=payload.password)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, service: AuthService = Depends(get_auth_service)) -> TokenResponse:
    return service.login(email=payload.email, password=payload.password)

@router.get("/yandex/login")
def yandex_login(service: AuthService = Depends(get_auth_service)) -> RedirectResponse:
    state = service.oauth_state_service.create_state()
    query = urlencode(
        {
            "response_type": "code",
            "client_id": settings.yandex_client_id,
            "redirect_uri": settings.yandex_client_redirect_uri,
            "state": state,
        }
    )
    return RedirectResponse(url=f"{settings.yandex_auth_url}?{query}")


@router.get("/yandex/callback", response_model=TokenResponse)
def yandex_callback(code: str, state: str, service: AuthService = Depends(get_auth_service)) -> TokenResponse:
    return service.oauth_login(
        request=OAuthRequest(
            provider="yandex",
            code=code,
            redirect_uri=settings.yandex_client_redirect_uri,
            state=state,
        )
    )