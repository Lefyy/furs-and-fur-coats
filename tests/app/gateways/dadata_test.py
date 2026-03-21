from app.gateways.dadata import DadataGateway


class StubDadataGateway(DadataGateway):
    def __init__(self, response=None, error: Exception | None = None) -> None:
        super().__init__(api_key="token", secret_key="secret", timeout=1.0)
        self.response = response
        self.error = error
        self.calls: list[tuple[list[str], list[str]]] = []

    def _request_clean_record_with_retry(self, *, structure: list[str], record: list[str]):
        self.calls.append((structure, record))
        if self.error is not None:
            raise self.error
        return self.response


def test_clean_record_returns_normalized_dict_response():
    gateway = StubDadataGateway(response=[[{"result": "user@example.com"}]])

    result = gateway.clean_record(structure=["EMAIL"], record=["User@Example.com"])

    assert result == {
        "structure": ["EMAIL"],
        "data": [[{"result": "user@example.com"}]],
    }


def test_clean_contact_record_builds_payload_and_maps_response():
    gateway = StubDadataGateway(
        response=[[{"result": "user@example.com"}, {"result": "+7 999 111-22-33"}]],
    )

    result = gateway.clean_contact_record(email="User@Example.com", phone="+79991112233")

    assert gateway.calls == [(["EMAIL", "PHONE"], ["User@Example.com", "+79991112233"])]
    assert result == {
        "email": {"result": "user@example.com"},
        "phone": {"result": "+7 999 111-22-33"},
        "address": {},
    }


def test_clean_contact_record_returns_empty_contract_for_missing_values():
    gateway = StubDadataGateway(response=[])

    result = gateway.clean_contact_record()

    assert gateway.calls == []
    assert result == {"email": {}, "phone": {}, "address": {}}
