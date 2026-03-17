import httpx

from app.config import settings
from app.exceptions import UnauthorizedError
from app.services.auth_service import OAuthGateway, OAuthRequest, OAuthUserInfo


class HttpOAuthGateway(OAuthGateway):
    def fetch_user_info(self, request: OAuthRequest) -> OAuthUserInfo:
        if request.provider == "yandex":
            if not request.code or not request.redirect_uri:
                raise UnauthorizedError("Missing code or redirect_uri for Yandex")
            return self._fetch_yandex_user(request.code, request.redirect_uri)

        elif request.provider == "vk":
            if not request.token:
                raise UnauthorizedError("Missing token for VK")
            return self._fetch_vk_user(request.token)

        else:
            raise UnauthorizedError("Unsupported OAuth provider")

    def _fetch_yandex_user(self, code: str, redirect_uri: str) -> OAuthUserInfo:
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
            raise UnauthorizedError("No access token")

        profile_response = httpx.get(
            settings.yandex_user_info_url,
            headers={"Authorization": f"OAuth {access_token}"},
            timeout=5.0,
        )

        if profile_response.status_code >= 400:
            raise UnauthorizedError("Failed to fetch Yandex profile")

        profile = profile_response.json()

        subject = str(profile.get("id"))
        email = profile.get("default_email") or (profile.get("emails") or [None])[0]
        phone = None
        if isinstance(profile.get("default_phone"), dict):
            phone = profile["default_phone"].get("number")

        if not subject:
            raise UnauthorizedError("Invalid Yandex profile")

        return OAuthUserInfo(
            provider="yandex",
            subject=subject,
            email=email,
            phone=phone,
        )

    def _fetch_vk_user(self, code: str, redirect_uri: str) -> OAuthUserInfo:
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
        user_id = token_data.get("user_id")
        email = token_data.get("email")

        if not access_token or not user_id:
            raise UnauthorizedError("Invalid VK token response")

        profile_response = httpx.get(
            settings.vk_user_info_url,
            params={
                "access_token": access_token,
                "v": "5.131",
            },
            timeout=5.0,
        )

        if profile_response.status_code >= 400:
            raise UnauthorizedError("Failed to fetch VK profile")

        profile_data = profile_response.json()
        users = profile_data.get("response", [])

        if not users:
            raise UnauthorizedError("VK profile is empty")

        subject = str(users[0].get("id"))

        if not subject:
            raise UnauthorizedError("Invalid VK profile")

        return OAuthUserInfo(
            provider="vk",
            subject=subject,
            email=email,
            phone=None,
        )