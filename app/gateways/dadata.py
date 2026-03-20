from __future__ import annotations

import time
from typing import Any
from dadata import Dadata

import json

from app.config import settings


class DadataGateway:

    def __init__(self, *, api_key: str | None = None, secret_key: str | None = None, timeout: float | None = None) -> None:
        self._api_key = api_key or settings.dadata_api_key
        self._secret_key = secret_key or settings.dadata_secret_key
        self._timeout = timeout or settings.dadata_timeout

    def clean_record(self, *, structure: list[str], record: list[str]) -> dict[str, Any]:
        if not structure or not record:
            return {"structure": structure, "data": []}

        if len(structure) != len(record):
            raise ValueError("Dadata structure and record must have the same length")

        for attempt in range(settings.dadata_retry_count + 1):
            with Dadata(token=self._api_key, secret=self._secret_key, timeout=self._timeout) as dadata:
                response = dadata.clean_record(structure=structure, record=record)
                return json.dumps(response)
            
            if attempt >= settings.dadata_retry_count:
                break
            time.sleep(settings.dadata_retry_delay)

        raise RuntimeError("Dadata clean_record request failed")

    def clean_contact_record(self, *, email: str = "", phone: str = "", address: str = "") -> dict[str, dict[str, Any]]:
        structure: list[str] = []
        record: list[str] = []
        field_names: list[str] = []

        for field_name, field_type, value in (
            ("email", "EMAIL", email),
            ("phone", "PHONE", phone),
            ("address", "ADDRESS", address),
        ):
            if value:
                field_names.append(field_name)
                structure.append(field_type)
                record.append(value)

        if not structure:
            return {"email": {}, "phone": {}, "address": {}}

        response = self.clean_record(structure=structure, record=record)
        cleaned_values = response.get("data", [[]])
        first_record = cleaned_values[0] if cleaned_values else []

        result = {"email": {}, "phone": {}, "address": {}}
        for field_name, cleaned_value in zip(field_names, first_record, strict=False):
            result[field_name] = cleaned_value or {}

        return result

    @property
    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Token {self._api_key}",
            "X-Secret": self._secret_key,
            "Content-Type": "application/json; charset=utf-8",
            "Accept": "application/json",
        }
