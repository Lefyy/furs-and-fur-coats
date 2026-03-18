import httpx
import base64

from app.config import settings
from app.exceptions import UnauthorizedError
from app.services.auth_service import OAuthGateway, OAuthRequest, OAuthUserInfo


class HttpOAuthGateway(OAuthGateway):
    def fetch_user_info(self, request: OAuthRequest) -> OAuthUserInfo:
        if request.provider == "yandex":
            return self._fetch_yandex_user(request)

        elif request.provider == "vk":
            return self._fetch_vk_user(request)

        else:
            raise UnauthorizedError("Unsupported OAuth provider")

    def _fetch_yandex_user(self, request: OAuthRequest) -> OAuthUserInfo:
        code = self._require(request.code, "Missing code for Yandex")
        redirect_uri = request.redirect_uri or settings.yandex_client_redirect_uri
        redirect_uri = self._require(redirect_uri, "Missing redirect_uri for Yandex")

        token_response = httpx.post(
            settings.yandex_token_url,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": redirect_uri,
                "client_id": settings.yandex_client_id,
                "client_secret": settings.yandex_client_secret,
            },
            timeout=5.0,
        )

        if token_response.status_code >= 400:
            raise UnauthorizedError("Yandex OAuth failed")

        token_data = token_response.json()
        access_token = token_data.get("access_token")
        if not access_token:
            raise UnauthorizedError("No access token from Yandex")

        profile_response = httpx.get(
            settings.yandex_user_info_url,
            headers={"Authorization": f"Bearer {access_token}"},
            params={"format": "json"},
            timeout=5.0,
        )

        if profile_response.status_code >= 400:
            raise UnauthorizedError("Failed to fetch Yandex profile")

        profile = profile_response.json()

        subject = str(profile.get("sub") or profile.get("id") or "")
        email = profile.get("email") or profile.get("default_email")
        phone = None
        if isinstance(profile.get("default_phone"), dict):
            phone = profile["default_phone"].get("number")
        elif isinstance(profile.get("phone_number"), str):
            phone = profile.get("phone_number")

        if not subject:
            raise UnauthorizedError("Invalid Yandex profile")

        return OAuthUserInfo(
            provider="yandex",
            subject=subject,
            email=email,
            phone=phone,
            refresh_token=token_data.get("refresh_token"),
        )

    def _fetch_vk_user(self, request: OAuthRequest) -> OAuthUserInfo:
        code = self._require(request.code, "Missing code for VK")
        redirect_uri = request.redirect_uri or settings.vk_client_redirect_uri
        redirect_uri = self._require(redirect_uri, "Missing redirect_uri for VK")

        token_response = httpx.post(
            settings.vk_token_url,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": redirect_uri,
                "client_id": settings.vk_client_id,
                "client_secret": settings.vk_client_secret,
            },
            timeout=5.0,
        )

        if token_response.status_code >= 400:
            raise UnauthorizedError("VK OAuth failed")

        token_data = token_response.json()

        access_token = token_data.get("access_token")
        if not access_token:
            raise UnauthorizedError("No access token from VK")

        profile_response = httpx.post(
            settings.vk_user_info_url,
            data={"access_token": access_token, "client_id": settings.vk_client_id},
            timeout=5.0,
        )

        if profile_response.status_code >= 400:
            raise UnauthorizedError("Failed to fetch VK profile")

        profile_payload = profile_response.json()
        profile = profile_payload.get("user") if isinstance(profile_payload, dict) else None

        if not isinstance(profile, dict):
            raise UnauthorizedError("Invalid VK profile response")

        subject = str(profile.get("user_id") or profile.get("sub") or "")
        email = profile.get("email") or token_data.get("email")
        phone = profile.get("phone")

        if not subject:
            raise UnauthorizedError("Invalid VK profile")

        return OAuthUserInfo(
            provider="vk",
            subject=subject,
            email=email,
            phone=phone,
            refresh_token=token_data.get("refresh_token"),
        )

    @staticmethod
    def _require(value: str | None, message: str) -> str:
        if not value:
            raise UnauthorizedError(message)
        return value
