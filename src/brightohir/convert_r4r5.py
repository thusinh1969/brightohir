"""
brightohir.convert_r4r5
=======================
Bidirectional R4 ↔ R5 conversion engine.

Based on:
- Official FHIR R4↔R5 StructureMaps: http://hl7.org/fhir/5.0.0-draft-final/r4maps.html
- FHIR R5 diff: https://hl7.org/fhir/R5/diff.html

Strategy:
1. For "compatible" resources → rename resourceType, apply field-level transforms
2. For "restructured" resources → apply registered transform functions
3. For "new_r5" resources → no R4 equivalent, raise clear error
4. For "renamed" resources → swap resourceType + apply transforms

Usage:
    from brightohir.convert_r4r5 import r4_to_r5, r5_to_r4
    r5_dict = r4_to_r5(r4_patient_dict)
    r4_dict = r5_to_r4(r5_encounter_dict)
"""

from __future__ import annotations

import copy
from typing import Any

from .registry import R4_TO_R5_MAP, R5_FROM_R4


# ═══════════════════════════════════════════════════════════════════════════════
# Transform functions for restructured resources
# Each function: (dict) → dict, modifies in place and returns
# ═══════════════════════════════════════════════════════════════════════════════

def _encounter_r4_to_r5(d: dict) -> dict:
    """Encounter R4 → R5: class Coding→CodeableConcept, hospitalization→admission."""
    # class: Coding → CodeableConcept
    if "class" in d and isinstance(d["class"], dict):
        c = d["class"]
        if "coding" not in c:  # R4 format: direct Coding
            d["class"] = [{"coding": [c]}]
    # hospitalization → admission
    if "hospitalization" in d:
        d["admission"] = d.pop("hospitalization")
    # Remove R4-only fields
    d.pop("classHistory", None)
    d.pop("statusHistory", None)
    return d


def _encounter_r5_to_r4(d: dict) -> dict:
    """Encounter R5 → R4: reverse transforms."""
    # class: CodeableConcept[] → Coding
    if "class" in d and isinstance(d["class"], list) and d["class"]:
        cc = d["class"][0]
        if "coding" in cc and cc["coding"]:
            d["class"] = cc["coding"][0]
    # admission → hospitalization
    if "admission" in d:
        d["hospitalization"] = d.pop("admission")
    return d


def _condition_r4_to_r5(d: dict) -> dict:
    """Condition R4 → R5: recorder/asserter → participant."""
    participants = []
    if "recorder" in d:
        participants.append({
            "type": {"coding": [{"system": "http://hl7.org/fhir/provenance-participant-type", "code": "author"}]},
            "actor": d.pop("recorder"),
        })
    if "asserter" in d:
        participants.append({
            "type": {"coding": [{"system": "http://hl7.org/fhir/provenance-participant-type", "code": "informant"}]},
            "actor": d.pop("asserter"),
        })
    if participants:
        d.setdefault("participant", []).extend(participants)
    return d


def _condition_r5_to_r4(d: dict) -> dict:
    """Condition R5 → R4: participant → recorder/asserter."""
    if "participant" in d:
        for p in d.get("participant", []):
            ptype = ""
            if "type" in p:
                codings = p["type"].get("coding", [])
                if codings:
                    ptype = codings[0].get("code", "")
            if ptype == "author" and "actor" in p:
                d["recorder"] = p["actor"]
            elif ptype == "informant" and "actor" in p:
                d["asserter"] = p["actor"]
        d.pop("participant", None)
    return d


def _allergy_r4_to_r5(d: dict) -> dict:
    """AllergyIntolerance R4 → R5: same pattern as Condition."""
    return _condition_r4_to_r5(d)  # Same recorder/asserter → participant


def _allergy_r5_to_r4(d: dict) -> dict:
    return _condition_r5_to_r4(d)


def _medication_request_r4_to_r5(d: dict) -> dict:
    """MedicationRequest R4 → R5: medication[x] → medication CodeableReference."""
    # medication[x] → medication (CodeableReference)
    if "medicationCodeableConcept" in d:
        d["medication"] = {"concept": d.pop("medicationCodeableConcept")}
    elif "medicationReference" in d:
        d["medication"] = {"reference": d.pop("medicationReference")}
    # reported[x] → informationSource
    if "reportedBoolean" in d:
        d.pop("reportedBoolean")  # No direct R5 equivalent for boolean
    if "reportedReference" in d:
        d["informationSource"] = [d.pop("reportedReference")]
    return d


def _medication_request_r5_to_r4(d: dict) -> dict:
    """MedicationRequest R5 → R4: reverse."""
    if "medication" in d:
        med = d.pop("medication")
        if "concept" in med:
            d["medicationCodeableConcept"] = med["concept"]
        elif "reference" in med:
            d["medicationReference"] = med["reference"]
    if "informationSource" in d:
        sources = d.pop("informationSource")
        if sources:
            d["reportedReference"] = sources[0]
    return d


def _medication_admin_r4_to_r5(d: dict) -> dict:
    """MedicationAdministration R4 → R5."""
    if "medicationCodeableConcept" in d:
        d["medication"] = {"concept": d.pop("medicationCodeableConcept")}
    elif "medicationReference" in d:
        d["medication"] = {"reference": d.pop("medicationReference")}
    if "context" in d:
        d["encounter"] = d.pop("context")
    return d


def _medication_admin_r5_to_r4(d: dict) -> dict:
    if "medication" in d:
        med = d.pop("medication")
        if "concept" in med:
            d["medicationCodeableConcept"] = med["concept"]
        elif "reference" in med:
            d["medicationReference"] = med["reference"]
    if "encounter" in d:
        d["context"] = d.pop("encounter")
    return d


def _medication_dispense_r4_to_r5(d: dict) -> dict:
    if "medicationCodeableConcept" in d:
        d["medication"] = {"concept": d.pop("medicationCodeableConcept")}
    elif "medicationReference" in d:
        d["medication"] = {"reference": d.pop("medicationReference")}
    if "context" in d:
        d["encounter"] = d.pop("context")
    return d


def _medication_dispense_r5_to_r4(d: dict) -> dict:
    if "medication" in d:
        med = d.pop("medication")
        if "concept" in med:
            d["medicationCodeableConcept"] = med["concept"]
        elif "reference" in med:
            d["medicationReference"] = med["reference"]
    if "encounter" in d:
        d["context"] = d.pop("encounter")
    return d


def _document_reference_r4_to_r5(d: dict) -> dict:
    """DocumentReference R4 → R5: flatten context, masterIdentifier → identifier."""
    if "masterIdentifier" in d:
        mi = d.pop("masterIdentifier")
        mi["use"] = "official"
        d.setdefault("identifier", []).insert(0, mi)
    if "context" in d:
        ctx = d.pop("context")
        if "encounter" in ctx:
            d["context"] = ctx["encounter"]  # R5: context is Reference[] not BackboneElement
        if "period" in ctx:
            d["period"] = ctx["period"]
        if "facilityType" in ctx:
            d["facilityType"] = ctx["facilityType"]
        if "practiceSetting" in ctx:
            d["practiceSetting"] = ctx["practiceSetting"]
        if "event" in ctx:
            d["event"] = [{"concept": e} for e in ctx["event"]]
    return d


def _document_reference_r5_to_r4(d: dict) -> dict:
    context: dict[str, Any] = {}
    if "period" in d:
        context["period"] = d.pop("period")
    if "facilityType" in d:
        context["facilityType"] = d.pop("facilityType")
    if "practiceSetting" in d:
        context["practiceSetting"] = d.pop("practiceSetting")
    # R5 context is Reference[] for encounter; R4 context.encounter
    if "context" in d:
        context["encounter"] = d.pop("context")
    if context:
        d["context"] = context
    return d


def _body_structure_r4_to_r5(d: dict) -> dict:
    included = {}
    if "location" in d:
        included["structure"] = d.pop("location")
    if "locationQualifier" in d:
        quals = d.pop("locationQualifier")
        if quals:
            included["laterality"] = quals[0]
    if included:
        d["includedStructure"] = [included]
    return d


def _body_structure_r5_to_r4(d: dict) -> dict:
    if "includedStructure" in d:
        inc = d["includedStructure"]
        if inc:
            first = inc[0]
            if "structure" in first:
                d["location"] = first["structure"]
            if "laterality" in first:
                d["locationQualifier"] = [first["laterality"]]
        d.pop("includedStructure")
    return d


def _consent_r4_to_r5(d: dict) -> dict:
    d.pop("scope", None)
    return d


def _consent_r5_to_r4(d: dict) -> dict:
    # R4 requires scope; default to "patient-privacy"
    if "scope" not in d:
        d["scope"] = {
            "coding": [{"system": "http://terminology.hl7.org/CodeSystem/consentscope", "code": "patient-privacy"}]
        }
    return d


def _appointment_r4_to_r5(d: dict) -> dict:
    return d  # Additive only in R5


def _appointment_r5_to_r4(d: dict) -> dict:
    d.pop("class", None)
    d.pop("subject", None)
    d.pop("recurrenceId", None)
    d.pop("recurrenceTemplate", None)
    return d


# ═══════════════════════════════════════════════════════════════════════════════
# Transform registry
# ═══════════════════════════════════════════════════════════════════════════════

_R4_TO_R5_TRANSFORMS: dict[str, Any] = {
    "Encounter": _encounter_r4_to_r5,
    "Condition": _condition_r4_to_r5,
    "AllergyIntolerance": _allergy_r4_to_r5,
    "MedicationRequest": _medication_request_r4_to_r5,
    "MedicationAdministration": _medication_admin_r4_to_r5,
    "MedicationDispense": _medication_dispense_r4_to_r5,
    "DocumentReference": _document_reference_r4_to_r5,
    "BodyStructure": _body_structure_r4_to_r5,
    "Consent": _consent_r4_to_r5,
    "Appointment": _appointment_r4_to_r5,
}

_R5_TO_R4_TRANSFORMS: dict[str, Any] = {
    "Encounter": _encounter_r5_to_r4,
    "Condition": _condition_r5_to_r4,
    "AllergyIntolerance": _allergy_r5_to_r4,
    "MedicationRequest": _medication_request_r5_to_r4,
    "MedicationAdministration": _medication_admin_r5_to_r4,
    "MedicationDispense": _medication_dispense_r5_to_r4,
    "DocumentReference": _document_reference_r5_to_r4,
    "BodyStructure": _body_structure_r5_to_r4,
    "Consent": _consent_r5_to_r4,
    "Appointment": _appointment_r5_to_r4,
}


# ═══════════════════════════════════════════════════════════════════════════════
# Public API
# ═══════════════════════════════════════════════════════════════════════════════

def r4_to_r5(data: dict, *, validate: bool = False) -> dict:
    """Convert an R4 resource dict to R5 format.

    Args:
        data: R4 resource as dict (must have "resourceType")
        validate: If True, validate result against R5 schema

    Returns:
        R5-formatted dict

    Raises:
        ValueError: If resourceType is unknown or has no R4→R5 path

    Example:
        r5 = r4_to_r5({"resourceType": "Encounter", "class": {"code": "AMB"}, ...})
    """
    result = copy.deepcopy(data)
    r4_type = result.get("resourceType")
    if not r4_type:
        raise ValueError("Missing resourceType in input data")

    # Check if R4 type was renamed in R5
    r5_type = R5_FROM_R4.get(r4_type, r4_type)
    result["resourceType"] = r5_type

    # Apply transform if available
    transform = _R4_TO_R5_TRANSFORMS.get(r5_type)
    if transform:
        result = transform(result)

    if validate:
        from .r5 import R5 as R5Factory
        errors = R5Factory.validate(r5_type, result)
        if errors:
            raise ValueError(f"R5 validation failed: {errors}")

    return result


def r5_to_r4(data: dict) -> dict:
    """Convert an R5 resource dict to R4 format.

    Args:
        data: R5 resource as dict (must have "resourceType")

    Returns:
        R4-formatted dict

    Raises:
        ValueError: If resource is new in R5 with no R4 equivalent
    """
    result = copy.deepcopy(data)
    r5_type = result.get("resourceType")
    if not r5_type:
        raise ValueError("Missing resourceType in input data")

    info = R4_TO_R5_MAP.get(r5_type)
    if info and info["status"] == "new_r5":
        raise ValueError(
            f"{r5_type} is new in R5 and has no R4 equivalent. "
            f"Cannot downgrade."
        )

    # Apply reverse transform
    transform = _R5_TO_R4_TRANSFORMS.get(r5_type)
    if transform:
        result = transform(result)

    # Rename if needed
    if info and info.get("r4") and info["r4"] != r5_type:
        result["resourceType"] = info["r4"]

    # Strip R5-only fields that have no R4 mapping
    _strip_r5_only_fields(result, r5_type)

    return result


def _strip_r5_only_fields(d: dict, r5_type: str) -> None:
    """Remove fields added in R5 that don't exist in R4."""
    info = R4_TO_R5_MAP.get(r5_type, {})
    for action, field, *_ in info.get("changes", []):
        if action == "add" and field in d:
            del d[field]


def conversion_status(resource_type: str) -> dict:
    """Check R4↔R5 conversion status for a resource type.

    Returns:
        {"r5": str, "r4": str|None, "status": str, "changes": list}
    """
    info = R4_TO_R5_MAP.get(resource_type)
    if info:
        return {"r5": resource_type, **info}
    # Maybe it's an R4 name
    r5_name = R5_FROM_R4.get(resource_type)
    if r5_name:
        info = R4_TO_R5_MAP[r5_name]
        return {"r5": r5_name, **info}
    return {"r5": resource_type, "r4": resource_type, "status": "unknown", "changes": []}
