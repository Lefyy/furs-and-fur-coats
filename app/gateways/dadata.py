from __future__ import annotations

import time
from typing import Any
from dadata import Dadata

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

        response = self._request_clean_record_with_retry(structure=structure, record=record)
        return self._normalize_clean_record_response(response, structure=structure)
    

    def clean_contact_record(self, *, email: str = "", phone: str = "", address: str = "") -> dict[str, dict[str, Any]]:
        payload = self._build_clean_contact_payload(email=email, phone=phone, address=address)
        field_names = payload["field_names"]
        structure = payload["structure"]
        record = payload["record"]

        if not structure:
            return {"email": {}, "phone": {}, "address": {}}

        response = self._request_clean_record_with_retry(structure=structure, record=record)
        return self._parse_clean_contact_response(response, field_names=field_names, structure=structure)


    def _build_clean_contact_payload(self, *, email: str = "", phone: str = "", address: str = "") -> dict[str, list[str]]:
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

        return {"field_names": field_names, "structure": structure, "record": record}


    def _request_clean_record_with_retry(self, *, structure: list[str], record: list[str]) -> Any:
        last_error: Exception | None = None

        for attempt in range(settings.dadata_retry_count + 1):
            try:
                with Dadata(token=self._api_key, secret=self._secret_key, timeout=self._timeout) as dadata:
                    return dadata.clean_record(structure=structure, record=record)
            except Exception as error:
                last_error = error
                if attempt >= settings.dadata_retry_count:
                    break
                time.sleep(settings.dadata_retry_delay)

        raise RuntimeError("Dadata clean_record request failed") from last_error


    def _normalize_clean_record_response(self, response: Any, *, structure: list[str]) -> dict[str, Any]:
        if isinstance(response, dict):
            return response
        if isinstance(response, list):
            return {"structure": structure, "data": response}
        raise RuntimeError("Dadata clean_record returned unexpected response format")


    def _parse_clean_contact_response(self, response: Any, *, field_names: list[str], structure: list[str]) -> dict[str, dict[str, Any]]:
        normalized_response = self._normalize_clean_record_response(response, structure=structure)
        cleaned_values = normalized_response.get("data", [])

        if not isinstance(cleaned_values, list):
            cleaned_values = []

        if cleaned_values and all(isinstance(item, dict) for item in cleaned_values):
            records = cleaned_values
        else:
            first_record = cleaned_values[0] if cleaned_values else []
            records = first_record if isinstance(first_record, list) else []

        result = {"email": {}, "phone": {}, "address": {}}
        for field_name, cleaned_value in zip(field_names, records, strict=False):
            result[field_name] = cleaned_value if isinstance(cleaned_value, dict) else {}

        return result


    @property
    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Token {self._api_key}",
            "X-Secret": self._secret_key,
            "Content-Type": "application/json; charset=utf-8",
            "Accept": "application/json",
        }
