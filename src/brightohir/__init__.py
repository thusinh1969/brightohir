"""
brightohir — BrighTO HL7 Interoperability Runtime v2.1.0
========================================================
Production SDK: FHIR R5 (157 resources) | R4↔R5 | V2.x↔R5 | MLLP | ACK | PII masking
Vietnamese healthcare code systems: ICD-10 VN, BHYT, drugs, labs, procedures

    from brightohir import R5, v2_to_r5, r5_to_v2, r4_to_r5, r5_to_r4
    from brightohir import generate_ack, mask_v2, mask_fhir
    from brightohir.vn import VN
    from brightohir.transport import MLLPServer, MLLPClient
"""
__version__ = "2.1.1"

from .r5 import R5
from .convert_r4r5 import r4_to_r5, r5_to_r4, conversion_status
from .convert_v2 import v2_to_r5, r5_to_v2, V2Converter
from .ack import generate_ack, generate_batch_ack
from .security import mask_v2, mask_fhir, mask_bundle, PIIMasker
from .vn import VN, VNCodeSystem, VN_CODE_SYSTEMS
from .registry import (
    ALL_R5_RESOURCES, R5_RESOURCES, R4_TO_R5_MAP,
    V2_SEGMENT_TO_FHIR, V2_MESSAGE_TO_FHIR,
    V2_DATATYPE_TO_FHIR, V2_TABLE_TO_FHIR_SYSTEM,
)

__all__ = [
    "R5", "r4_to_r5", "r5_to_r4", "conversion_status",
    "v2_to_r5", "r5_to_v2", "V2Converter",
    "generate_ack", "generate_batch_ack",
    "mask_v2", "mask_fhir", "mask_bundle", "PIIMasker",
    "VN", "VNCodeSystem", "VN_CODE_SYSTEMS",
    "ALL_R5_RESOURCES", "R5_RESOURCES", "R4_TO_R5_MAP",
    "V2_SEGMENT_TO_FHIR", "V2_MESSAGE_TO_FHIR",
    "V2_DATATYPE_TO_FHIR", "V2_TABLE_TO_FHIR_SYSTEM",
]
