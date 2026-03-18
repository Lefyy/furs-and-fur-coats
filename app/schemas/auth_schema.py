from pydantic import BaseModel, Field


class RegisterRequest(BaseModel):
    email: str
    phone: str = Field(min_length=5, max_length=32)
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    email: str
    password: str = Field(min_length=8, max_length=128)


class OAuthLoginRequest(BaseModel):
    code: str
    state: str
    redirect_uri: str | None = None

class YandexOAuthLoginRequest(OAuthLoginRequest):
    device_id: str | None = Field(default=None, min_length=6, max_length=50)
    device_name: str | None = Field(default=None, min_length=1, max_length=100)
    code_verifier: str | None = Field(default=None, min_length=1)


class VkOAuthLoginRequest(OAuthLoginRequest):
    device_id: str = Field(min_length=1)
    code_verifier: str = Field(min_length=1)

class UserAuthResponse(BaseModel):
    id: int
    email: str
    phone: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserAuthResponse


