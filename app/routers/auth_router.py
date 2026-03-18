from fastapi import APIRouter, Depends

from app.routers.dependencies import get_auth_service
from app.schemas.auth_schema import LoginRequest, OAuthLoginRequest, RegisterRequest, TokenResponse, VkOAuthLoginRequest, YandexOAuthLoginRequest
from app.services.auth_service import AuthService, OAuthRequest

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse)
def register(payload: RegisterRequest, service: AuthService = Depends(get_auth_service)) -> TokenResponse:
    return service.register(email=payload.email, phone=payload.phone, password=payload.password)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, service: AuthService = Depends(get_auth_service)) -> TokenResponse:
    return service.login(email=payload.email, password=payload.password)


@router.post("/oauth/yandex", response_model=TokenResponse)
def oauth_yandex(payload: YandexOAuthLoginRequest, service: AuthService = Depends(get_auth_service)) -> TokenResponse:
    return service.oauth_login(
        request=OAuthRequest(
            provider="yandex",
            code=payload.code,
            redirect_uri=payload.redirect_uri,
            state=payload.state,
            device_id=payload.device_id,
            device_name=payload.device_name,
            code_verifier=payload.code_verifier,
        )
    )


@router.post("/oauth/vk", response_model=TokenResponse)
def oauth_vk(payload: VkOAuthLoginRequest, service: AuthService = Depends(get_auth_service)) -> TokenResponse:
    return service.oauth_login(
        request=OAuthRequest(
            provider="vk",
            code=payload.code,
            redirect_uri=payload.redirect_uri,
            state=payload.state,
            device_id=payload.device_id,
            code_verifier=payload.code_verifier,
        )
    )


@router.get("/oauth/state")
def get_oauth_state(service: AuthService = Depends(get_auth_service)) -> dict:
    state = service.oauth_state_service.create_state()
    return {"state": state}