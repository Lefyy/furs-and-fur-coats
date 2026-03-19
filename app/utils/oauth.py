import httpx

from app.config import settings
from app.exceptions import UnauthorizedError
from app.services.auth_service import YandexOAuthGateway, YandexUserInfo, YandexAccessTokenResponse


class HttpOAuthGateway(YandexOAuthGateway):
    def exchange_code_for_token(self, code: str) -> YandexAccessTokenResponse:
        payload = self._post_form(
            settings.yandex_token_url,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "client_id": self._require(settings.yandex_client_id, "Missing Yandex client_id"),
                "client_secret": self._require(settings.yandex_client_secret, "Missing Yandex client_secret"),
            },
            error_message="Failed Yandex OAuth token request",
        )

        access_token = payload.get("access_token")
        if not access_token:
            raise UnauthorizedError("No access token from Yandex")

        return YandexAccessTokenResponse(access_token=access_token, refresh_token=payload.get("refresh_token"))

    def get_user_data(self, access_token: YandexAccessTokenResponse) -> dict:
        return self._get_json(
            settings.yandex_user_info_url,
            headers={"Authorization": f"OAuth {access_token.access_token}"},
            params={"format": "json"},
            error_message="Failed to fetch Yandex user info",
        )

    def fetch_user_info(self, code: str) -> YandexUserInfo:
        access_token = self.exchange_code_for_token(code=code)
        user_data = self.get_user_data(access_token=access_token)

        subject = str(user_data["id"])
        email = user_data.get("default_email")
        phone = user_data.get("default_phone", {}).get("number")

        if not subject:
            raise UnauthorizedError("Invalid Yandex profile")

        return YandexUserInfo(subject=subject, email=email, phone=phone, refresh_token=access_token.refresh_token)

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
