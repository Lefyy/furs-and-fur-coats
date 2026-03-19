import httpx

from app.config import settings
from app.exceptions import UnauthorizedError
from app.services.auth_service import OAuthGateway, OAuthRequest, OAuthUserInfo


class HttpOAuthGateway(OAuthGateway):
    def fetch_user_info(self, request: OAuthRequest) -> OAuthUserInfo:
        code = self._require(request.code, "Missing code for Yandex")
        token_payload = {
            "grant_type": "authorization_code",
            "code": code,
            "client_id": self._require(settings.yandex_client_id, "Missing Yandex client_id"),
            "client_secret": self._require(settings.yandex_client_secret, "Missing Yandex client_secret"),
        }
        if request.device_id:
            token_payload["device_id"] = request.device_id
        if request.device_name:
            token_payload["device_name"] = request.device_name
        if request.code_verifier:
            token_payload["code_verifier"] = request.code_verifier

        token_data = self._post_form(
            settings.yandex_token_url,
            data=token_payload,
            error_message="Failed Yandex OAuth token request"
        )

        access_token = token_data.get("access_token")
        if not access_token:
            raise UnauthorizedError("No access token from Yandex")

        profile = self._get_json(
            settings.yandex_user_info_url,
            headers={"Authorization": f"Bearer {access_token}"},
            params={"format": "json"},
            error_message="Failed to fetch Yandex user info"
        )

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

    @staticmethod
    def _post_form(url: str, data: dict[str, str], error_message: str) -> dict:
        response = httpx.post(url, data=data, timeout=10.0)
        return HttpOAuthGateway._parse_json_response(response, error_message)

    @staticmethod
    def _get_json(url: str, headers: dict[str, str], params: dict[str, str], error_message: str) -> dict:
        response = httpx.get(url, headers=headers, params=params, timeout=10.0)
        return HttpOAuthGateway._parse_json_response(response, error_message)

    @staticmethod
    def _parse_json_response(response: httpx.Response, error_message: str) -> dict:
        try:
            payload = response.json()
        except ValueError as exc:
            raise UnauthorizedError(error_message) from exc

        if response.status_code >= 400 or payload.get("error"):
            description = payload.get("error_description") or payload.get("error")
            if description:
                raise UnauthorizedError(f"{error_message}: {description}")
            raise UnauthorizedError(error_message)

        if not isinstance(payload, dict):
            raise UnauthorizedError(error_message)

        return payload

    @staticmethod
    def _require(value: str | None, message: str) -> str:
        if not value:
            raise UnauthorizedError(message)
        return value
