"""
brightohir.r5
=============
FHIR R5 resource factory. Thin wrapper over fhir.resources with:
- Dynamic resource creation by name
- Bundle builder
- JSON/XML round-trip
- Validation

Usage:
    from brightohir.r5 import R5
    patient = R5.create("Patient", id="p001", active=True, name=[{"text": "Nguyễn Văn A"}])
    bundle = R5.bundle("message", [patient, encounter])
    json_str = R5.to_json(patient)
    patient2 = R5.from_json("Patient", json_str)
"""

from __future__ import annotations

import importlib
import json
import uuid
from datetime import datetime, timezone
from typing import Any

from .registry import ALL_R5_RESOURCES


class R5:
    """Static factory for FHIR R5 resources."""

    _cache: dict[str, type] = {}

    @classmethod
    def _get_class(cls, resource_type: str) -> type:
        """Import and cache the fhir.resources class for a given resource type."""
        if resource_type in cls._cache:
            return cls._cache[resource_type]
        if resource_type not in ALL_R5_RESOURCES:
            raise ValueError(
                f"Unknown R5 resource: {resource_type!r}. "
                f"See brightohir.registry.ALL_R5_RESOURCES for all 157 types."
            )
        module_name = resource_type.lower()
        mod = importlib.import_module(f"fhir.resources.{module_name}")
        klass = getattr(mod, resource_type)
        cls._cache[resource_type] = klass
        return klass

    @classmethod
    def create(cls, resource_type: str, **kwargs: Any) -> Any:
        """Create a validated FHIR R5 resource.

        Args:
            resource_type: e.g. "Patient", "Observation", "MedicationRequest"
            **kwargs: Resource fields

        Returns:
            fhir.resources.<type> instance (Pydantic model)

        Example:
            pat = R5.create("Patient", id="p001", active=True,
                            name=[{"family": "Nguyen", "given": ["Van A"]}],
                            birthDate="1990-01-15", gender="male")
        """
        klass = cls._get_class(resource_type)
        return klass(**kwargs)

    @classmethod
    def from_dict(cls, resource_type: str, data: dict) -> Any:
        """Create resource from a Python dict."""
        klass = cls._get_class(resource_type)
        return klass(**data)

    @classmethod
    def from_json(cls, resource_type: str, json_str: str) -> Any:
        """Create resource from a JSON string."""
        klass = cls._get_class(resource_type)
        return klass.model_validate_json(json_str)

    @classmethod
    def to_json(cls, resource: Any, indent: int | None = 2) -> str:
        """Serialize resource to JSON string."""
        return resource.model_dump_json(indent=indent, exclude_none=True)

    @classmethod
    def to_dict(cls, resource: Any) -> dict:
        """Serialize resource to Python dict."""
        return resource.model_dump(exclude_none=True)

    @classmethod
    def validate(cls, resource_type: str, data: dict) -> list[str]:
        """Validate data against R5 schema. Returns list of error messages (empty = valid)."""
        try:
            cls._get_class(resource_type)(**data)
            return []
        except Exception as e:
            return [str(e)]

    @classmethod
    def bundle(
        cls,
        bundle_type: str = "message",
        resources: list[Any] | None = None,
        bundle_id: str | None = None,
    ) -> Any:
        """Build a FHIR R5 Bundle from a list of resources.

        Args:
            bundle_type: "message" | "transaction" | "batch" | "collection" | "document"
            resources: List of fhir.resources instances
            bundle_id: Optional UUID; auto-generated if not provided

        Returns:
            fhir.resources.bundle.Bundle instance
        """
        bid = bundle_id or str(uuid.uuid4())
        entries = []
        for r in (resources or []):
            entry = {
                "fullUrl": f"urn:uuid:{uuid.uuid4()}",
                "resource": json.loads(r.model_dump_json(exclude_none=True)),
            }
            if bundle_type == "transaction":
                rt = r.resource_type if hasattr(r, "resource_type") else r.__class__.__name__
                entry["request"] = {"method": "POST", "url": rt}
            entries.append(entry)

        return cls.create(
            "Bundle",
            id=bid,
            type=bundle_type,
            timestamp=datetime.now(timezone.utc).isoformat(),
            entry=entries,
        )

    @classmethod
    def list_resources(cls, category: str | None = None) -> list[str]:
        """List available R5 resource names, optionally filtered by category.

        Categories: conformance, terminology, security, documents, individuals,
        entities, devices, workflow, management, summary, diagnostics, medications,
        care_provision, request_response, support, billing, payment, etc.
        """
        from .registry import R5_RESOURCES

        if category:
            return R5_RESOURCES.get(category, [])
        return sorted(ALL_R5_RESOURCES)
