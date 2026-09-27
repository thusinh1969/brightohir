"""
brightohir.client
=================
FHIR server client with a ``$validate`` helper and CRUD convenience methods.

CRUD operations use `fhirpy <https://github.com/beda-software/fhir-py>`_,
which is an optional dependency (install ``pip install brightohir[client]``).
Server-side ``$validate`` uses ``requests`` directly, so it works without
fhirpy.

Usage:
    from brightohir.client import FHIRClient

    client = FHIRClient("https://fhir.example.com/r5", authorization="Bearer TOKEN")

    outcome = client.validate(patient_dict)      # POST Patient/$validate
    ok = client.is_valid(patient_dict)           # True if no error/fatal issue

    pat = client.create(patient_dict)            # requires fhirpy
    results = client.search("Patient", name="Nguyen")
"""

from __future__ import annotations

from typing import Any

__all__ = ["FHIRClient", "is_valid_resource", "validate_resource"]


class FHIRClient:
    """Minimal FHIR R5 server client.

    Args:
        base_url: Base URL of the FHIR server (e.g. "https://fhir.example.com/r5").
        authorization: Optional Authorization header value (e.g. "Bearer TOKEN").
        extra_headers: Additional HTTP headers for ``$validate`` calls.
        timeout: Timeout (seconds) for ``$validate`` HTTP requests.
    """

    def __init__(
        self,
        base_url: str,
        authorization: str | None = None,
        *,
        extra_headers: dict[str, str] | None = None,
        timeout: float = 60.0,
    ):
        self.base_url = base_url.rstrip("/")
        self.authorization = authorization
        self.extra_headers = dict(extra_headers or {})
        self.timeout = timeout
        self._fhirpy_client: Any = None

    def _headers(self) -> dict[str, str]:
        headers = {
            "Accept": "application/fhir+json",
            "Content-Type": "application/fhir+json",
        }
        if self.authorization:
            headers["Authorization"] = self.authorization
        headers.update(self.extra_headers)
        return headers

    def _get_fhirpy(self):
        """Lazily construct the fhirpy client (optional dependency)."""
        if self._fhirpy_client is None:
            try:
                from fhirpy import SyncFHIRClient
            except ImportError as exc:
                raise ImportError(
                    "fhirpy is required for FHIR CRUD operations. "
                    "Install it with: pip install brightohir[client]"
                ) from exc
            self._fhirpy_client = SyncFHIRClient(
                self.base_url, authorization=self.authorization
            )
        return self._fhirpy_client

    # ── Validation ──────────────────────────────────────────────────────

    def validate(self, resource: dict) -> dict:
        """Run server-side ``$validate`` on a resource.

        Args:
            resource: FHIR resource dict (must include ``resourceType``).

        Returns:
            The parsed OperationOutcome (or Parameters) response dict.
        """
        import requests

        resource_type = resource.get("resourceType")
        if not resource_type:
            raise ValueError("resource must have a 'resourceType'")

        url = f"{self.base_url}/{resource_type}/$validate"
        response = requests.post(
            url, json=resource, headers=self._headers(), timeout=self.timeout
        )
        response.raise_for_status()
        return response.json()

    def is_valid(self, resource: dict) -> bool:
        """Return True if ``$validate`` reports no error/fatal issue."""
        outcome = self.validate(resource)

        issues: list[dict] = []
        if "issue" in outcome:
            issues = outcome["issue"]
        else:
            # Some servers return a Parameters resource wrapping OperationOutcome.
            for parameter in outcome.get("parameter", []):
                if parameter.get("name") == "issue" and isinstance(parameter.get("resource"), dict):
                    issues.extend(parameter["resource"].get("issue", []))

        return not any(
            issue.get("severity") in ("error", "fatal") for issue in issues
        )

    # ── CRUD (requires fhirpy) ──────────────────────────────────────────

    def read(self, resource_type: str, id_: str):
        """Read a resource by id."""
        return self._get_fhirpy().resource(resource_type, id=id_).get()

    def create(self, resource: dict):
        """Create a resource on the server. Returns the fhirpy resource.

        A client-side ``id`` is honored (fhirpy then uses PUT semantics), which
        pairs well with ``deterministic=True`` conversions.
        """
        resource_type = resource.get("resourceType")
        if not resource_type:
            raise ValueError("resource must have a 'resourceType'")
        data = {k: v for k, v in resource.items() if k != "resourceType"}
        fhirpy_resource = self._get_fhirpy().resource(resource_type, **data)
        fhirpy_resource.save()
        return fhirpy_resource

    def update(self, resource: dict):
        """Update an existing resource (must include an id)."""
        resource_type = resource.get("resourceType")
        resource_id = resource.get("id")
        if not resource_type or not resource_id:
            raise ValueError("resource must have 'resourceType' and 'id'")
        fhirpy_resource = self._get_fhirpy().resource(resource_type, id=resource_id)
        for key, value in resource.items():
            if key not in ("resourceType", "id"):
                setattr(fhirpy_resource, key, value)
        fhirpy_resource.save()
        return fhirpy_resource

    def search(self, resource_type: str, **params):
        """Search resources. Returns a list of resource dicts."""
        return (
            self._get_fhirpy()
            .resources(resource_type)
            .search(**params)
            .fetch_all()
        )

    def delete(self, resource_type: str, id_: str) -> None:
        """Delete a resource by id."""
        self._get_fhirpy().resource(resource_type, id=id_).delete()


def validate_resource(resource: dict, base_url: str, authorization: str | None = None) -> dict:
    """Convenience: run ``$validate`` against a FHIR server.

    Args:
        resource: FHIR resource dict.
        base_url: FHIR server base URL.
        authorization: Optional Authorization header value.

    Returns:
        The parsed OperationOutcome (or Parameters) response dict.
    """
    return FHIRClient(base_url, authorization=authorization).validate(resource)


def is_valid_resource(resource: dict, base_url: str, authorization: str | None = None) -> bool:
    """Convenience: run ``$validate`` and return whether it passed."""
    return FHIRClient(base_url, authorization=authorization).is_valid(resource)
