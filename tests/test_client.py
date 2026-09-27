"""
Tests for the FHIR client + $validate helper (no live server needed).

Run: pytest tests/test_client.py -v
"""
import pytest


class _FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


PATIENT = {
    "resourceType": "Patient",
    "id": "p1",
    "name": [{"family": "Nguyen", "given": ["Van A"]}],
}


class TestValidate:
    def test_validate_posts_correct_request(self, monkeypatch):
        from brightohir.client import FHIRClient

        captured = {}

        def fake_post(url, json=None, headers=None, timeout=None):
            captured["url"] = url
            captured["json"] = json
            captured["headers"] = headers
            captured["timeout"] = timeout
            return _FakeResponse({"resourceType": "OperationOutcome", "issue": []})

        monkeypatch.setattr("requests.post", fake_post)

        client = FHIRClient("https://fhir.example.com/r5/", authorization="Bearer T")
        outcome = client.validate(PATIENT)

        assert captured["url"] == "https://fhir.example.com/r5/Patient/$validate"
        assert captured["json"] == PATIENT
        assert captured["headers"]["Authorization"] == "Bearer T"
        assert captured["headers"]["Content-Type"] == "application/fhir+json"
        assert outcome["resourceType"] == "OperationOutcome"

    def test_validate_missing_resource_type(self):
        from brightohir.client import FHIRClient
        with pytest.raises(ValueError, match="resourceType"):
            FHIRClient("https://x").validate({"id": "no-type"})

    def test_is_valid_true(self, monkeypatch):
        from brightohir.client import FHIRClient
        client = FHIRClient("https://x")
        monkeypatch.setattr(client, "validate", lambda r: {
            "resourceType": "OperationOutcome",
            "issue": [{"severity": "information", "code": "informational"}],
        })
        assert client.is_valid(PATIENT) is True

    def test_is_valid_false_on_error(self, monkeypatch):
        from brightohir.client import FHIRClient
        client = FHIRClient("https://x")
        monkeypatch.setattr(client, "validate", lambda r: {
            "resourceType": "OperationOutcome",
            "issue": [{"severity": "error", "code": "invalid"}],
        })
        assert client.is_valid(PATIENT) is False

    def test_is_valid_handles_parameters_wrapper(self, monkeypatch):
        from brightohir.client import FHIRClient
        client = FHIRClient("https://x")
        monkeypatch.setattr(client, "validate", lambda r: {
            "resourceType": "Parameters",
            "parameter": [
                {"name": "issue", "resource": {
                    "resourceType": "OperationOutcome",
                    "issue": [{"severity": "fatal", "code": "structure"}],
                }},
            ],
        })
        assert client.is_valid(PATIENT) is False

    def test_validate_resource_convenience(self, monkeypatch):
        from brightohir.client import validate_resource

        def fake_post(url, json=None, headers=None, timeout=None):
            return _FakeResponse({"resourceType": "OperationOutcome", "issue": []})

        monkeypatch.setattr("requests.post", fake_post)
        outcome = validate_resource(PATIENT, "https://fhir.example.com/r5")
        assert outcome["resourceType"] == "OperationOutcome"


class TestCRUDRequiresFhirpy:
    def test_read_requires_fhirpy(self, monkeypatch):
        import builtins

        from brightohir.client import FHIRClient

        real_import = builtins.__import__

        def fake_import(name, *args, **kwargs):
            if name.startswith("fhirpy"):
                raise ImportError("no fhirpy here")
            return real_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", fake_import)
        client = FHIRClient("https://x")
        with pytest.raises(ImportError, match="brightohir\\[client\\]"):
            client.read("Patient", "p1")

    def test_create_requires_fhirpy(self, monkeypatch):
        import builtins

        from brightohir.client import FHIRClient

        real_import = builtins.__import__

        def fake_import(name, *args, **kwargs):
            if name.startswith("fhirpy"):
                raise ImportError("no fhirpy here")
            return real_import(name, *args, **kwargs)

        monkeypatch.setattr(builtins, "__import__", fake_import)
        client = FHIRClient("https://x")
        with pytest.raises(ImportError, match="brightohir\\[client\\]"):
            client.create(PATIENT)

    def test_update_requires_type_and_id(self):
        from brightohir.client import FHIRClient
        client = FHIRClient("https://x")
        with pytest.raises(ValueError, match="resourceType"):
            client.update({"name": [{"family": "x"}]})
