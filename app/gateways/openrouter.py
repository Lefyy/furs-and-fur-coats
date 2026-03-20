from __future__ import annotations

from typing import Any

import httpx

from app.config import settings


class OpenRouterGateway:
    def __init__(self, *, api_key: str | None = None, base_url: str | None = None, timeout: float | None = None) -> None:
        self._api_key = api_key or settings.openrouter_api_key
        self._base_url = (base_url or settings.openrouter_base_url).rstrip("/")
        self._timeout = timeout or settings.openrouter_timeout

    def generate_product_description(self, *, messages: list[dict[str, Any]]) -> str:
        if not self._api_key:
            raise RuntimeError("OpenRouter API key is not configured")

        payload = {
            "model": settings.openrouter_model,
            "temperature": settings.openrouter_temperature,
            "messages": messages,
            "reasoning": {"enabled": False},
        }
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "HTTP-Referer": settings.openrouter_referer,
            "X-OpenRouter-Title": settings.openrouter_title,
            "Content-Type": "application/json",
        }
        with httpx.Client(timeout=self._timeout) as client:
            response = client.post(f"{self._base_url}", json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()

        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError("OpenRouter returned an unexpected response payload") from exc

        if isinstance(content, str):
            return content.strip()

        if isinstance(content, list):
            text_parts = [part.get("text", "") for part in content if isinstance(part, dict)]
            return "".join(text_parts).strip()

        raise RuntimeError("OpenRouter returned an unsupported message content type")
