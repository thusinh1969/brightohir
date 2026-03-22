"""
brightohir — BrighTO HL7 Interoperability Runtime
==================================================
Production-grade Python SDK for FHIR R5, R4↔R5, and V2.x↔R5 conversion.

Standards compliance:
    - FHIR R5 v5.0.0 (157 resources)
    - HL7 V2-to-FHIR IG v1.0.0 STU (Oct 2025)
    - FHIR R4↔R5 official StructureMaps

Quick start:
    from brightohir import R5, v2_to_r5, r5_to_v2, r4_to_r5, r5_to_r4

    # Create R5 resource
    patient = R5.create("Patient", id="p001", active=True,
                        name=[{"family": "Nguyen", "given": ["Van A"]}])

    # V2 → R5
    bundle = v2_to_r5(adt_a01_string)

    # R5 → V2
    v2_msg = r5_to_v2(patient_dict, message_type="ADT_A01")

    # R4 ↔ R5
    r5_data = r4_to_r5(r4_encounter_dict)
    r4_data = r5_to_r4(r5_encounter_dict)

Install:
    pip install fhir.resources hl7apy pyyaml
"""

__version__ = "1.0.0"

from .r5 import R5
from .convert_r4r5 import r4_to_r5, r5_to_r4, conversion_status
from .convert_v2 import v2_to_r5, r5_to_v2, V2Converter
from .registry import (
    ALL_R5_RESOURCES,
    R5_RESOURCES,
    R4_TO_R5_MAP,
    V2_SEGMENT_TO_FHIR,
    V2_MESSAGE_TO_FHIR,
    V2_DATATYPE_TO_FHIR,
    V2_TABLE_TO_FHIR_SYSTEM,
)

__all__ = [
    # Core
    "R5",
    # R4 ↔ R5
    "r4_to_r5",
    "r5_to_r4",
    "conversion_status",
    # V2 ↔ R5
    "v2_to_r5",
    "r5_to_v2",
    "V2Converter",
    # Registry
    "ALL_R5_RESOURCES",
    "R5_RESOURCES",
    "R4_TO_R5_MAP",
    "V2_SEGMENT_TO_FHIR",
    "V2_MESSAGE_TO_FHIR",
    "V2_DATATYPE_TO_FHIR",
    "V2_TABLE_TO_FHIR_SYSTEM",
]
