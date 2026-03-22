"""
brightohir.security
===================
Dual-layer PII masking for HL7 V2 and FHIR R5 resources.

Layer 1: V2 ER7 masking — mask PII fields in raw pipe-delimited messages
Layer 2: FHIR resource masking — mask PII in FHIR JSON dicts

Masking strategies:
    - "redact"   — replace with "[REDACTED]"
    - "hash"     — SHA-256 hash (one-way, deterministic for linking)
    - "pseudonym" — generate fake but structurally valid replacements
    - "partial"  — keep first/last chars, mask middle: "Nguyen" → "N****n"

Usage:
    from brightohir.security import mask_v2, mask_fhir, PIIMasker

    # Quick mask
    masked_v2 = mask_v2(raw_v2_message)
    masked_patient = mask_fhir(patient_dict)

    # Custom config
    masker = PIIMasker(strategy="hash")
    masked = masker.mask_fhir(patient_dict)
"""

from __future__ import annotations

import copy
import hashlib
import re
import uuid
from typing import Any, Literal

MaskStrategy = Literal["redact", "hash", "pseudonym", "partial"]

# ═══════════════════════════════════════════════════════════════════════════════
# V2 PII fields by segment (field index, description)
# Based on HL7 V2 PII guidance and HIPAA Safe Harbor
# ═══════════════════════════════════════════════════════════════════════════════

V2_PII_FIELDS: dict[str, list[int]] = {
    "PID": [3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 19, 20, 26, 27, 29, 30],
    # 3=Identifier, 5=Name, 7=DOB, 8=Sex, 11=Address, 13=Phone, 19=SSN, 20=DL
    "NK1": [2, 4, 5, 6, 7, 12, 30, 31, 32, 33],
    # 2=Name, 4=Address, 5=Phone, 12=SSN
    "GT1": [3, 5, 6, 7, 12, 19, 20],
    # 3=Name, 5=Address, 6=Phone, 12=SSN
    "IN1": [16, 18, 19, 49],
    # 16=Name, 18=DOB, 19=Address, 49=Subscriber ID
    "IN2": [1, 2, 3, 6, 7, 9, 26, 40, 41, 49, 52, 61],
    # Various subscriber/employer details
}

# FHIR PII paths by resource type
FHIR_PII_PATHS: dict[str, list[str]] = {
    "Patient": [
        "identifier", "name", "telecom", "gender", "birthDate",
        "address", "maritalStatus", "photo", "contact",
        "communication", "managingOrganization", "deceasedDateTime",
        "deceasedBoolean", "multipleBirthBoolean", "multipleBirthInteger",
    ],
    "RelatedPerson": [
        "identifier", "name", "telecom", "gender", "birthDate", "address", "photo",
    ],
    "Practitioner": [
        "identifier", "name", "telecom", "address", "birthDate", "photo",
    ],
    "Coverage": [
        "identifier", "subscriberId", "beneficiary",
    ],
    "Account": [
        "guarantor",
    ],
}


class PIIMasker:
    """Configurable PII masking engine.

    Args:
        strategy: Masking strategy ("redact", "hash", "pseudonym", "partial")
        salt: Salt for hash strategy (for deterministic linking across records)
        preserve_structure: If True, masked values keep same field structure
    """

    def __init__(
        self,
        strategy: MaskStrategy = "redact",
        salt: str = "",
        preserve_structure: bool = True,
    ):
        self.strategy = strategy
        self.salt = salt
        self.preserve_structure = preserve_structure

    def _mask_value(self, value: str, field_type: str = "text") -> str:
        """Apply masking strategy to a single value."""
        if not value or value.strip() == "":
            return value

        if self.strategy == "redact":
            return "[REDACTED]"

        elif self.strategy == "hash":
            h = hashlib.sha256(f"{self.salt}{value}".encode()).hexdigest()[:16]
            return f"H{h.upper()}"

        elif self.strategy == "partial":
            if len(value) <= 2:
                return "*" * len(value)
            return value[0] + "*" * (len(value) - 2) + value[-1]

        elif self.strategy == "pseudonym":
            h = hashlib.md5(f"{self.salt}{value}".encode()).hexdigest()
            if field_type == "name":
                return f"PERSON_{h[:6].upper()}"
            elif field_type == "phone":
                return f"000-{h[:3]}-{h[3:7]}"
            elif field_type == "date":
                return "19000101"
            elif field_type == "address":
                return f"ADDR_{h[:6].upper()}"
            elif field_type == "id":
                return f"ID_{h[:8].upper()}"
            return f"MASKED_{h[:8].upper()}"

        return value

    # ── V2 Masking ────────────────────────────────────────────────────────

    def mask_v2(self, message: str) -> str:
        """Mask PII fields in a V2 ER7 message.

        Args:
            message: Raw V2 ER7 string

        Returns:
            Masked V2 ER7 string (same structure, PII replaced)
        """
        lines = re.split(r"[\r\n]+", message.strip())
        masked_lines = []

        for line in lines:
            if not line.strip() or len(line) < 3:
                masked_lines.append(line)
                continue
            seg_name = line[:3]
            if seg_name in V2_PII_FIELDS:
                line = self._mask_v2_segment(line, seg_name)
            masked_lines.append(line)

        return "\r".join(masked_lines) + "\r"

    def _mask_v2_segment(self, line: str, seg_name: str) -> str:
        """Mask specific fields in a V2 segment."""
        fields = line.split("|")
        pii_indices = V2_PII_FIELDS.get(seg_name, [])

        for idx in pii_indices:
            if idx < len(fields) and fields[idx]:
                if self.preserve_structure and "^" in fields[idx]:
                    # Mask each component separately
                    comps = fields[idx].split("^")
                    field_type = self._infer_v2_type(seg_name, idx)
                    comps = [self._mask_value(c, field_type) if c else "" for c in comps]
                    fields[idx] = "^".join(comps)
                else:
                    field_type = self._infer_v2_type(seg_name, idx)
                    fields[idx] = self._mask_value(fields[idx], field_type)

        return "|".join(fields)

    def _infer_v2_type(self, seg: str, idx: int) -> str:
        """Infer field type for pseudonym generation."""
        name_fields = {("PID", 5), ("PID", 6), ("PID", 9), ("NK1", 2), ("GT1", 3), ("IN1", 16)}
        phone_fields = {("PID", 13), ("PID", 14), ("NK1", 5), ("NK1", 6), ("GT1", 6)}
        date_fields = {("PID", 7), ("PID", 29), ("IN1", 18)}
        addr_fields = {("PID", 11), ("PID", 12), ("NK1", 4), ("GT1", 5), ("IN1", 19)}
        id_fields = {("PID", 3), ("PID", 4), ("PID", 19), ("PID", 20), ("IN1", 49)}

        key = (seg, idx)
        if key in name_fields:
            return "name"
        if key in phone_fields:
            return "phone"
        if key in date_fields:
            return "date"
        if key in addr_fields:
            return "address"
        if key in id_fields:
            return "id"
        return "text"

    # ── FHIR Masking ─────────────────────────────────────────────────────

    def mask_fhir(self, resource: dict) -> dict:
        """Mask PII in a FHIR R5 resource dict.

        Args:
            resource: FHIR resource dict (must have "resourceType")

        Returns:
            Deep copy with PII fields masked
        """
        result = copy.deepcopy(resource)
        rt = result.get("resourceType", "")
        pii_paths = FHIR_PII_PATHS.get(rt, [])

        for path in pii_paths:
            if path in result:
                result[path] = self._mask_fhir_field(result[path], path)

        return result

    def _mask_fhir_field(self, value: Any, field_name: str) -> Any:
        """Recursively mask a FHIR field value."""
        if value is None:
            return None

        if isinstance(value, str):
            ftype = self._infer_fhir_type(field_name)
            return self._mask_value(value, ftype)

        if isinstance(value, bool):
            return self._mask_value(str(value), "text") if self.strategy == "redact" else value

        if isinstance(value, list):
            return [self._mask_fhir_field(item, field_name) for item in value]

        if isinstance(value, dict):
            masked = {}
            for k, v in value.items():
                if k in ("system", "use", "type", "resourceType", "coding"):
                    # Preserve structural/coded fields
                    if k == "coding":
                        masked[k] = v  # Don't mask code systems
                    else:
                        masked[k] = v
                elif k in ("value", "family", "given", "text", "line", "city",
                           "state", "postalCode", "country", "display", "reference"):
                    masked[k] = self._mask_fhir_field(v, k)
                else:
                    masked[k] = self._mask_fhir_field(v, field_name)
            return masked

        return value

    def _infer_fhir_type(self, field_name: str) -> str:
        """Infer masking type from FHIR field name."""
        if field_name in ("name", "family", "given", "display", "text"):
            return "name"
        if field_name in ("telecom", "value") and "phone" in field_name.lower():
            return "phone"
        if field_name in ("birthDate", "deceasedDateTime"):
            return "date"
        if field_name in ("address", "line", "city", "state", "postalCode", "country"):
            return "address"
        if field_name in ("identifier", "subscriberId"):
            return "id"
        return "text"

    def mask_bundle(self, bundle: dict) -> dict:
        """Mask all resources in a FHIR Bundle."""
        result = copy.deepcopy(bundle)
        for entry in result.get("entry", []):
            if "resource" in entry:
                entry["resource"] = self.mask_fhir(entry["resource"])
        return result


# ═══════════════════════════════════════════════════════════════════════════════
# Convenience functions
# ═══════════════════════════════════════════════════════════════════════════════

def mask_v2(message: str, strategy: MaskStrategy = "redact") -> str:
    """Quick-mask PII in a V2 message (default: redact)."""
    return PIIMasker(strategy=strategy).mask_v2(message)


def mask_fhir(resource: dict, strategy: MaskStrategy = "redact") -> dict:
    """Quick-mask PII in a FHIR resource (default: redact)."""
    return PIIMasker(strategy=strategy).mask_fhir(resource)


def mask_bundle(bundle: dict, strategy: MaskStrategy = "redact") -> dict:
    """Quick-mask PII in all resources of a FHIR Bundle."""
    return PIIMasker(strategy=strategy).mask_bundle(bundle)
