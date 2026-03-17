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
    redirect_uri: str


class UserAuthResponse(BaseModel):
    id: int
    email: str
    phone: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserAuthResponse


