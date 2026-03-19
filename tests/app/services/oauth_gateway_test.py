import httpx

from app.utils.oauth import HttpOAuthGateway
from app.services.auth_service import OAuthRequest


class DummyResponse:
    def __init__(self, payload: dict, status_code: int = 200) -> None:
        self._payload = payload
        self.status_code = status_code

    def json(self) -> dict:
        return self._payload


def test_vk_oauth_uses_minimal_payload(monkeypatch):
    gateway = HttpOAuthGateway()
    calls: list[tuple[str, dict]] = []

    def fake_post(url, data=None, timeout=None):
        calls.append((url, dict(data)))
        if url.endswith('/oauth2/auth'):
            return DummyResponse({'access_token': 'vk-token', 'refresh_token': 'vk-refresh', 'email': 'vk@example.com'})
        return DummyResponse({'user': {'user_id': 42, 'email': 'vk@example.com', 'phone': '+79990000000'}})

    monkeypatch.setattr('app.utils.oauth.settings.vk_client_id', 'vk-client')
    monkeypatch.setattr('app.utils.oauth.settings.vk_client_secret', '')
    monkeypatch.setattr('app.utils.oauth.settings.vk_client_redirect_uri', '')
    monkeypatch.setattr(httpx, 'post', fake_post)

    user = gateway.fetch_user_info(OAuthRequest(provider='vk', code='vk-code', state='oauth-state'))

    token_url, token_payload = calls[0]
    assert token_url == 'https://id.vk.com/oauth2/auth'
    assert token_payload == {
        'grant_type': 'authorization_code',
        'code': 'vk-code',
        'client_id': 'vk-client',
        'state': 'oauth-state',
    }
    assert user.subject == '42'
    assert user.email == 'vk@example.com'
    assert user.refresh_token == 'vk-refresh'


def test_vk_oauth_sends_optional_pkce_fields_when_present(monkeypatch):
    gateway = HttpOAuthGateway()
    calls: list[tuple[str, dict]] = []

    def fake_post(url, data=None, timeout=None):
        calls.append((url, dict(data)))
        if len(calls) == 1:
            return DummyResponse({'access_token': 'vk-token'})
        return DummyResponse({'user': {'user_id': 'sub-1'}})

    monkeypatch.setattr('app.utils.oauth.settings.vk_client_id', 'vk-client')
    monkeypatch.setattr('app.utils.oauth.settings.vk_client_secret', 'vk-secret')
    monkeypatch.setattr('app.utils.oauth.settings.vk_client_redirect_uri', 'https://app/callback')
    monkeypatch.setattr(httpx, 'post', fake_post)

    gateway.fetch_user_info(OAuthRequest(
        provider='vk',
        code='vk-code',
        state='oauth-state',
        redirect_uri='https://frontend/callback',
        device_id='device-1',
        code_verifier='verifier-1',
    ))

    _, token_payload = calls[0]
    assert token_payload == {
        'grant_type': 'authorization_code',
        'code': 'vk-code',
        'client_id': 'vk-client',
        'redirect_uri': 'https://frontend/callback',
        'client_secret': 'vk-secret',
        'state': 'oauth-state',
        'device_id': 'device-1',
        'code_verifier': 'verifier-1',
    }


def test_yandex_oauth_keeps_flow_simple_and_optional(monkeypatch):
    gateway = HttpOAuthGateway()
    posts: list[dict] = []

    def fake_post(url, data=None, timeout=None):
        posts.append(dict(data))
        return DummyResponse({'access_token': 'ya-token', 'refresh_token': 'ya-refresh'})

    def fake_get(url, headers=None, params=None, timeout=None):
        assert headers == {'Authorization': 'Bearer ya-token'}
        assert params == {'format': 'json'}
        return DummyResponse({'id': 'ya-sub', 'default_email': 'ya@example.com'})

    monkeypatch.setattr('app.utils.oauth.settings.yandex_client_id', 'ya-client')
    monkeypatch.setattr('app.utils.oauth.settings.yandex_client_secret', 'ya-secret')
    monkeypatch.setattr(httpx, 'post', fake_post)
    monkeypatch.setattr(httpx, 'get', fake_get)

    user = gateway.fetch_user_info(OAuthRequest(provider='yandex', code='ya-code'))

    assert posts[0] == {
        'grant_type': 'authorization_code',
        'code': 'ya-code',
        'client_id': 'ya-client',
        'client_secret': 'ya-secret',
    }
    assert user.subject == 'ya-sub'
    assert user.email == 'ya@example.com'
    assert user.refresh_token == 'ya-refresh'