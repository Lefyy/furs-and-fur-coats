from app.services.address_formatting_service import AddressFormattingService
from app.services.contact_formatting_service import ContactFormattingService


class SuccessGateway:
    def __init__(self, payload):
        self.payload = payload

    def clean_contact_record(self, *, email: str = "", phone: str = "", address: str = ""):
        return self.payload


class FailingGateway:
    def clean_contact_record(self, *, email: str = "", phone: str = "", address: str = ""):
        raise RuntimeError("boom")


def test_contact_formatting_service_uses_canonical_values_from_gateway():
    service = ContactFormattingService(
        SuccessGateway(
            {
                "email": {"result": "user@example.com"},
                "phone": {"source": "+79991112233"},
                "address": {},
            }
        )
    )

    result = service.format(email="User@Example.com", phone="+7 (999) 111-22-33")

    assert result.email.canonical == "user@example.com"
    assert result.phone.canonical == "+79991112233"
    assert result.is_degraded is False
    assert result.status == "formatted"


def test_contact_formatting_service_falls_back_to_raw_values_on_runtime_error():
    service = ContactFormattingService(FailingGateway())

    result = service.format(email="User@Example.com", phone="+7 (999) 111-22-33")

    assert result.email.canonical == "User@Example.com"
    assert result.phone.canonical == "+7 (999) 111-22-33"
    assert result.is_degraded is True
    assert result.status == "pending_enrichment"


def test_address_formatting_service_reads_address_contract():
    service = AddressFormattingService(
        SuccessGateway(
            {
                "email": {},
                "phone": {},
                "address": {"result": "г Москва, ул Тверская, д 1", "postal_code": "125009"},
            }
        )
    )

    result = service.format(address="Москва Тверская 1")

    assert result.canonical == "г Москва, ул Тверская, д 1"
    assert result.postal_code == "125009"
    assert result.metadata["postal_code"] == "125009"
    assert result.is_degraded is False
    assert result.status == "formatted"


def test_address_formatting_service_falls_back_to_raw_address_on_runtime_error():
    service = AddressFormattingService(FailingGateway())

    result = service.format(address="Сырой адрес")

    assert result.canonical == "Сырой адрес"
    assert result.postal_code is None
    assert result.metadata == {}
    assert result.is_degraded is True
    assert result.status == "pending_enrichment"