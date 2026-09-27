"""
brightohir.custom
=================
Z-segment extension framework and declarative (YAML/JSON) mapping loader.

Hospital HL7 feeds almost always carry custom ``Zxx`` segments that brightohir
does not know about. This module lets you map them to FHIR resources without
writing Python — via a small YAML/JSON file — or programmatically via
:meth:`V2Converter.register_segment` / :meth:`V2Converter.register_enricher`.

YAML schema (also accepted as JSON)::

    version: 1
    segments:
      ZAL:
        resource: AllergyIntolerance          # FHIR resource type
        defaults:                             # optional base fields
          clinicalStatus:
            coding:
              - system: "http://terminology.hl7.org/CodeSystem/allergyintolerance-clinical"
                code: active
        fields:
          - source: 2                         # ZAL-2
            target: code                      # -> AllergyIntolerance.code
            datatype: CWE
          - source: 3                         # ZAL-3
            target: onsetDateTime
            datatype: TS

Supported ``datatype`` values: CWE, CE, CNE, CX, XPN, XAD, XTN, TS, DTM, DT,
NM, SN, ST, TX, FT, SI, ID, IS. ``target`` may be a dotted path such as
``valueQuantity.value``.

Usage:
    from brightohir.custom import load_custom_mappings
    load_custom_mappings("mappings/zsegments.yaml")
    bundle = v2_to_r5(raw_message)   # now converts ZAL too
"""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any

from .convert_v2 import (
    _SEGMENT_CONVERTERS,
    _SEGMENT_ENRICHERS,
    _cwe_to_codeableconcept,
    _cx_to_identifier,
    _field_str,
    _get_field_repetitions,
    _get_field_value,
    _ts_to_datetime,
    _xad_to_address,
    _xpn_to_humanname,
    _xtn_to_contactpoint,
)

__all__ = [
    "DATATYPE_TRANSFORMS",
    "load_custom_mappings",
    "register_custom_mappings",
    "register_enricher",
    "register_segment",
]


def _nm_to_number(field) -> float | str:
    """NM/SN → float, falling back to the raw string on parse failure."""
    s = _field_str(field)
    try:
        return float(s)
    except (ValueError, TypeError):
        return s


# V2 datatype → transform function mapping
DATATYPE_TRANSFORMS: dict[str, Any] = {
    "CWE": _cwe_to_codeableconcept,
    "CE": _cwe_to_codeableconcept,
    "CNE": _cwe_to_codeableconcept,
    "CX": _cx_to_identifier,
    "XPN": _xpn_to_humanname,
    "XAD": _xad_to_address,
    "XTN": _xtn_to_contactpoint,
    "TS": _ts_to_datetime,
    "DTM": _ts_to_datetime,
    "DT": _ts_to_datetime,
    "NM": _nm_to_number,
    "SN": _nm_to_number,
    "ST": _field_str,
    "TX": _field_str,
    "FT": _field_str,
    "SI": _field_str,
    "ID": _field_str,
    "IS": _field_str,
}


def _set_nested(obj: dict, path: str, value: Any) -> None:
    """Set a (possibly dotted) path in a dict, creating intermediate dicts."""
    keys = path.split(".")
    for key in keys[:-1]:
        obj = obj.setdefault(key, {})
    obj[keys[-1]] = value


def _make_field_mapping_converter(
    resource_type: str,
    fields: list[dict],
    *,
    defaults: dict | None = None,
) -> Any:
    """Build a segment→resource converter from a declarative field map."""
    def converter(segment) -> dict:
        resource: dict[str, Any] = {"resourceType": resource_type, "id": str(uuid.uuid4())}
        if defaults:
            _deep_update(resource, defaults)
        for spec in fields:
            index = spec["source"]
            target = spec["target"]
            datatype = spec.get("datatype", "ST").upper()

            # Repeating source → list of transformed values.
            reps = _get_field_repetitions(segment, index)
            values = []
            for rep in (reps or [_get_field_value(segment, index)]):
                if rep is None:
                    continue
                transform = DATATYPE_TRANSFORMS.get(datatype, _field_str)
                value = transform(rep)
                if value in (None, "", []):
                    continue
                values.append(value)

            if not values:
                continue
            if datatype in ("XPN", "XAD", "XTN", "CX", "CWE", "CE", "CNE"):
                # These transforms produce composite FHIR types; store a list
                # only when the source field actually repeats.
                if len(values) == 1:
                    _set_nested(resource, target, values[0])
                else:
                    _set_nested(resource, target, values)
            else:
                _set_nested(resource, target, values[0])
        return resource

    return converter


def _deep_update(target: dict, update: dict) -> None:
    """Recursively merge ``update`` into ``target`` (mutates target)."""
    for key, value in update.items():
        if isinstance(value, dict) and isinstance(target.get(key), dict):
            _deep_update(target[key], value)
        else:
            target[key] = value


def register_segment(segment_name: str, resource_type: str, converter: Any) -> None:
    """Register a custom segment → resource converter."""
    _SEGMENT_CONVERTERS[segment_name.upper()] = (resource_type, converter)


def register_enricher(segment_name: str, enricher: Any) -> None:
    """Register a custom segment enricher."""
    _SEGMENT_ENRICHERS[segment_name.upper()] = enricher


def register_custom_mappings(mapping: dict) -> list[str]:
    """Register converters from a declarative mapping dict.

    Returns the list of segment names registered.
    """
    if not isinstance(mapping, dict):
        raise ValueError("Custom mapping must be a dict with a 'segments' key")

    segments = mapping.get("segments")
    if not isinstance(segments, dict):
        raise ValueError("Custom mapping must contain a 'segments' mapping")

    registered: list[str] = []
    for seg_name, spec in segments.items():
        if not isinstance(spec, dict) or "resource" not in spec:
            raise ValueError(f"Segment {seg_name!r} must map to a 'resource' type")
        resource_type = spec["resource"]
        fields = spec.get("fields", [])
        if not isinstance(fields, list):
            raise ValueError(f"Segment {seg_name!r} 'fields' must be a list")
        converter = _make_field_mapping_converter(
            resource_type, fields, defaults=spec.get("defaults"),
        )
        register_segment(seg_name, resource_type, converter)
        registered.append(seg_name)
    return registered


def load_custom_mappings(path: str | Path) -> list[str]:
    """Load and register converters from a YAML or JSON mapping file.

    Returns the list of segment names registered.
    """
    path = Path(path)
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() in (".json",):
        data = json.loads(text)
    else:
        try:
            import yaml
        except ImportError as exc:  # pragma: no cover - yaml is a core dep
            raise ImportError("PyYAML is required to load YAML custom mappings") from exc
        data = yaml.safe_load(text)
    return register_custom_mappings(data)
