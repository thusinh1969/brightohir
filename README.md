# brightohir — BrighTO HL7 Interoperability Runtime

Production-grade Python SDK for **FHIR R5**, **R4↔R5 conversion**, and **HL7 V2.x↔R5 bidirectional conversion**.

## Standards Compliance

| Standard | Version | Coverage |
|----------|---------|----------|
| FHIR R5 | v5.0.0 | All 157 resources |
| HL7 V2-to-FHIR IG | v1.0.0 STU (Oct 2025) | 50+ segment maps, 25+ message structures, 30+ datatype maps, 40+ vocabulary maps |
| FHIR R4↔R5 | Official StructureMaps | 50+ resource transforms with field-level diffs |
| HL7 V2.x | 2.1–2.8.2 (via hl7apy) | Full parse/create/validate |

## Install

```bash
pip install fhir.resources hl7apy pyyaml    # core deps
pip install fhirpy                           # optional: FHIR server client
pip install fhirpathpy                       # optional: FHIRPath expressions
```

## Quick Start

### 1. Create FHIR R5 Resources

```python
from brightohir import R5

# Create a Patient
patient = R5.create("Patient",
    id="p001", active=True,
    name=[{"family": "Nguyen", "given": ["Van A"]}],
    gender="male", birthDate="1990-01-15")

# Create an Observation
obs = R5.create("Observation",
    id="obs001", status="final",
    code={"coding": [{"system": "http://loinc.org", "code": "29463-7", "display": "Body Weight"}]},
    valueQuantity={"value": 72, "unit": "kg"})

# Build a Bundle
bundle = R5.bundle("transaction", [patient, obs])

# Serialize
json_str = R5.to_json(patient)
patient_dict = R5.to_dict(patient)

# Validate
errors = R5.validate("Patient", {"active": "INVALID"})
# Returns list of error strings (empty = valid)

# List all 157 R5 resources
all_types = R5.list_resources()
meds = R5.list_resources("medications")  # Category filter
```

### 2. R4 ↔ R5 Conversion

```python
from brightohir import r4_to_r5, r5_to_r4, conversion_status

# R4 → R5 (handles breaking changes automatically)
r4_encounter = {
    "resourceType": "Encounter", "id": "enc-001", "status": "in-progress",
    "class": {"system": "http://terminology.hl7.org/CodeSystem/v3-ActCode", "code": "AMB"},
    "hospitalization": {"dischargeDisposition": {"text": "home"}},
}
r5_encounter = r4_to_r5(r4_encounter)
# class: Coding → CodeableConcept[]
# hospitalization → admission
# classHistory/statusHistory removed

# R5 → R4 (downgrades gracefully)
r4_back = r5_to_r4(r5_encounter)

# MedicationRequest: medication[x] → CodeableReference
r4_med = {
    "resourceType": "MedicationRequest", "status": "active", "intent": "order",
    "medicationCodeableConcept": {"coding": [{"code": "12345"}]},
}
r5_med = r4_to_r5(r4_med)
# r5_med["medication"]["concept"]["coding"][0]["code"] == "12345"

# Check conversion status for any resource
info = conversion_status("Encounter")
# {"r5": "Encounter", "r4": "Encounter", "status": "restructured", "changes": [...]}
```

### 3. V2.x → FHIR R5

```python
from brightohir import v2_to_r5, V2Converter

# Quick convert
adt_a01 = """MSH|^~\\&|HATTO|LC_PHARMACY|EHR|HOSPITAL|20260322090000||ADT^A01^ADT_A01|MSG001|P|2.5.1
PID|1||12345^^^LC^MR||NGUYEN^VAN A||19900115|M|||123 NGUYEN HUE^^HCM^VN^70000
PV1|1|I|W^101^1|||12345^TRAN^BAC SI|||MED
AL1|1|DA|ASPIRIN|SV|Rash
DG1|1||J06.9^URTI^ICD10|||A
OBX|1|NM|29463-7^Body Weight^LN||72|kg|||||F"""

bundle = v2_to_r5(adt_a01)
# Returns FHIR R5 Bundle with: MessageHeader, Patient, Encounter,
# AllergyIntolerance, Condition, Observation — all cross-referenced

# Full control with V2Converter
conv = V2Converter()
bundle = conv.convert(adt_a01)
patient = conv.extract_resource("Patient")      # First Patient
obs_list = conv.extract_all("Observation")       # All Observations
encounter = conv.extract_resource("Encounter")   # First Encounter
```

### 4. FHIR R5 → V2.x

```python
from brightohir import r5_to_v2

# Single resource
patient_dict = {
    "resourceType": "Patient", "id": "p001",
    "name": [{"family": "Nguyen", "given": ["Van A"]}],
    "gender": "male", "birthDate": "1990-01-15",
}
v2_msg = r5_to_v2(patient_dict, message_type="ADT_A01")
# MSH|^~\&|BRIGHTOHIR||EXTERNAL||20260322...|ADT^A01^ADT_A01|...
# EVN|A01|...
# PID|...|Nguyen^Van A||19900115|M

# From a Bundle
v2_msg = r5_to_v2(bundle_dict, message_type="ADT_A01",
                   sending_app="LC_PHARMACY", receiving_app="HIS")
```

### 5. Access the Registry

```python
from brightohir import (
    ALL_R5_RESOURCES,       # Set of all 157 R5 resource names
    R5_RESOURCES,           # Dict by category
    V2_SEGMENT_TO_FHIR,    # PID → [(Patient, ""), ...], OBX → [(Observation, ""), ...]
    V2_MESSAGE_TO_FHIR,    # ADT_A01 → {segments, fhir_resources}
    V2_DATATYPE_TO_FHIR,   # CWE → [CodeableConcept, Coding, ...], XPN → [HumanName]
    V2_TABLE_TO_FHIR_SYSTEM, # HL70001 → admin-gender URI
    R4_TO_R5_MAP,           # Encounter → {status, changes, ...}
)
```

## Architecture

```
brightohir/
├── __init__.py          # Public API
├── r5.py                # R5 resource factory (create/validate/serialize)
├── convert_r4r5.py      # R4 ↔ R5 bidirectional converter
├── convert_v2.py        # V2.x ↔ R5 bidirectional converter
├── registry.py          # Standards registry (157 resources, mappings, diffs)
└── mappings/            # YAML configs (extensible)
```

## Supported V2 Message Types

ADT: A01, A02, A03, A04, A05, A08, A28, A31, A34, A40 •
ORM/ORU: O01, R01 • OML: O21 • OUL: R22 •
Pharmacy: RDE_O11, RDS_O13, RAS_O17 •
Vaccination: VXU_V04 • Documents: MDM_T02 •
Scheduling: SIU_S12–S15 • Financial: BAR_P01, DFT_P03

## Supported V2 Segment Converters

| Segment | → FHIR R5 Resource | Fields Mapped |
|---------|-------|------|
| PID | Patient | identifier, name, birthDate, gender, address, telecom, maritalStatus, communication, deceased |
| PV1 | Encounter | class, actualPeriod, admission |
| OBX | Observation | code, value[x], units, interpretation, status, effectiveDateTime, referenceRange |
| AL1 | AllergyIntolerance | type, category, code, criticality, reaction, onset |
| DG1 | Condition | code, onset, category, clinicalStatus |
| RXA | Immunization | occurrenceDateTime, vaccineCode, doseQuantity, lotNumber, status |
| MSH | MessageHeader | eventCoding, source, destination |

## Dependencies

- `fhir.resources` ≥8.0.0 — FHIR R5 Pydantic models (production-stable, Feb 2026)
- `hl7apy` ≥1.3.5 — V2.x parse/create/validate (V2.1–2.8.2)
- `pyyaml` ≥6.0 — YAML mapping configs

## License

MIT — BrighTO Technology / Hatto AI
