from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.gateways.dadata import DadataGateway


@dataclass(frozen=True)
class CanonicalFieldResult:
    raw: str
    canonical: str
    data: dict[str, Any]


@dataclass(frozen=True)
class ContactFormattingResult:
    email: CanonicalFieldResult
    phone: CanonicalFieldResult
    is_degraded: bool
    status: str


class ContactFormattingService:
    def __init__(self, dadata_gateway: DadataGateway) -> None:
        self.dadata_gateway = dadata_gateway

    def format(self, *, email: str, phone: str) -> ContactFormattingResult:
        try:
            payload = self.dadata_gateway.clean_contact_record(email=email, phone=phone)
        except RuntimeError:
            return ContactFormattingResult(
                email=CanonicalFieldResult(raw=email, canonical=email, data={}),
                phone=CanonicalFieldResult(raw=phone, canonical=phone, data={}),
                is_degraded=True,
                status="pending_enrichment",
            )

        return ContactFormattingResult(
            email=CanonicalFieldResult(raw=email, canonical=self._canonical_contact_value(payload.get("email"), email), data=payload.get("email") or {}),
            phone=CanonicalFieldResult(raw=phone, canonical=self._canonical_contact_value(payload.get("phone"), phone), data=payload.get("phone") or {}),
            is_degraded=False,
            status="formatted",
        )

    @staticmethod
    def _canonical_contact_value(cleaned: dict[str, Any] | None, fallback: str) -> str:
        if not cleaned:
            return fallback
        return str(cleaned.get("result") or cleaned.get("value") or cleaned.get("source") or fallback)
