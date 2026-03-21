from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.gateways.dadata import DadataGateway


@dataclass(frozen=True)
class AddressFormattingResult:
    raw: str
    canonical: str
    postal_code: str | None
    metadata: dict[str, Any]
    is_degraded: bool
    status: str


class AddressFormattingService:
    def __init__(self, dadata_gateway: DadataGateway) -> None:
        self.dadata_gateway = dadata_gateway

    def format(self, *, address: str) -> AddressFormattingResult:
        try:
            payload = self.dadata_gateway.clean_contact_record(address=address)
        except RuntimeError:
            return AddressFormattingResult(
                raw=address,
                canonical=address,
                postal_code=None,
                metadata={},
                is_degraded=True,
                status="pending_enrichment",
            )

        cleaned = payload.get('address') or {}
        canonical = str(cleaned.get('result') or cleaned.get('source') or address)
        postal_code = cleaned.get('postal_code')
        return AddressFormattingResult(
            raw=address,
            canonical=canonical,
            postal_code=str(postal_code) if postal_code else None,
            metadata=cleaned,
            is_degraded=False,
            status="formatted",
        )
