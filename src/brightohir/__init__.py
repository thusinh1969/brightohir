"""
brightohir — BrighTO HL7 Interoperability Runtime v2.2.0
========================================================
Production SDK: FHIR R5 (157 resources) | R4↔R5 | V2.x↔R5 | MLLP | ACK | PII masking
Vietnamese healthcare code systems: ICD-10 VN, BHYT, drugs, labs, procedures
Deterministic (idempotent) conversion for production integration engines.

    from brightohir import R5, v2_to_r5, r5_to_v2, r4_to_r5, r5_to_r4
    from brightohir import generate_ack, mask_v2, mask_fhir
    from brightohir.vn import VN
    from brightohir.transport import MLLPServer, MLLPClient
"""
__version__ = "2.2.0"

from .ack import generate_ack, generate_batch_ack
from .client import FHIRClient, is_valid_resource, validate_resource
from .convert_r4r5 import conversion_status, r4_to_r5, r5_to_r4
from .convert_v2 import V2Converter, r5_to_v2, v2_to_r5
from .custom import load_custom_mappings, register_custom_mappings
from .r5 import R5
from .registry import (
    ALL_R5_RESOURCES,
    R4_TO_R5_MAP,
    R5_RESOURCES,
    V2_DATATYPE_TO_FHIR,
    V2_MESSAGE_TO_FHIR,
    V2_SEGMENT_TO_FHIR,
    V2_TABLE_TO_FHIR_SYSTEM,
)
from .security import PIIMasker, mask_bundle, mask_fhir, mask_v2
from .vn import VN, VN_CODE_SYSTEMS, VNCodeSystem

__all__ = [
    "ALL_R5_RESOURCES",
    "R4_TO_R5_MAP",
    "R5",
    "R5_RESOURCES",
    "V2_DATATYPE_TO_FHIR",
    "V2_MESSAGE_TO_FHIR",
    "V2_SEGMENT_TO_FHIR",
    "V2_TABLE_TO_FHIR_SYSTEM",
    "VN",
    "VN_CODE_SYSTEMS",
    "FHIRClient",
    "PIIMasker",
    "V2Converter",
    "VNCodeSystem",
    "conversion_status",
    "generate_ack",
    "generate_batch_ack",
    "is_valid_resource",
    "load_custom_mappings",
    "mask_bundle",
    "mask_fhir",
    "mask_v2",
    "r4_to_r5",
    "r5_to_r4",
    "r5_to_v2",
    "register_custom_mappings",
    "v2_to_r5",
    "validate_resource",
]
