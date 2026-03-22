"""
brightohir.convert_v2
=====================
HL7 V2.x ↔ FHIR R5 bidirectional converter.

Based on:
- HL7 V2-to-FHIR IG v1.0.0 (STU, Oct 2025)
  https://build.fhir.org/ig/HL7/v2-to-fhir/
- Segment→Resource ConceptMaps (400+ CSV mappings → 250+ ConceptMaps)

Architecture:
    V2 ER7 string
        → hl7apy parse
        → segment extraction
        → field-level mapping (registry-driven)
        → fhir.resources R5 validation
        → FHIR R5 dict / Bundle

Usage:
    from brightohir.convert_v2 import v2_to_r5, r5_to_v2, V2Converter

    # Quick convert
    bundle = v2_to_r5(adt_a01_string)

    # Full control
    conv = V2Converter()
    bundle = conv.convert(adt_a01_string)
    patient = conv.extract_resource("Patient")

    # Reverse: FHIR → V2
    v2_msg = r5_to_v2(patient_dict, message_type="ADT_A01")
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from .registry import (
    V2_DATATYPE_TO_FHIR,
    V2_MESSAGE_TO_FHIR,
    V2_SEGMENT_TO_FHIR,
    V2_TABLE_TO_FHIR_SYSTEM,
)


# ═══════════════════════════════════════════════════════════════════════════════
# V2 Datatype → FHIR Datatype converters
# ═══════════════════════════════════════════════════════════════════════════════

def _xpn_to_humanname(field) -> dict:
    """XPN (Extended Person Name) → HumanName."""
    result: dict[str, Any] = {}
    try:
        comps = _get_components(field)
        if len(comps) > 0 and comps[0]:
            result["family"] = str(comps[0])
        if len(comps) > 1 and comps[1]:
            result["given"] = [str(comps[1])]
            if len(comps) > 2 and comps[2]:
                result["given"].append(str(comps[2]))
        if len(comps) > 4 and comps[4]:
            result["prefix"] = [str(comps[4])]
        if len(comps) > 5 and comps[5]:
            result["suffix"] = [str(comps[5])]
        if len(comps) > 6 and comps[6]:
            name_type = str(comps[6])
            result["use"] = {"L": "official", "A": "usual", "N": "nickname",
                             "D": "old", "M": "maiden", "B": "old"}.get(name_type, "official")
    except (IndexError, AttributeError):
        pass
    return result


def _xad_to_address(field) -> dict:
    """XAD (Extended Address) → Address."""
    result: dict[str, Any] = {}
    try:
        comps = _get_components(field)
        lines = []
        if len(comps) > 0 and comps[0]:
            lines.append(str(comps[0]))
        if len(comps) > 1 and comps[1]:
            lines.append(str(comps[1]))
        if lines:
            result["line"] = lines
        if len(comps) > 2 and comps[2]:
            result["city"] = str(comps[2])
        if len(comps) > 3 and comps[3]:
            result["state"] = str(comps[3])
        if len(comps) > 4 and comps[4]:
            result["postalCode"] = str(comps[4])
        if len(comps) > 5 and comps[5]:
            result["country"] = str(comps[5])
        if len(comps) > 6 and comps[6]:
            addr_type = str(comps[6])
            result["use"] = {"H": "home", "B": "work", "O": "work",
                             "M": "home", "C": "temp"}.get(addr_type, "home")
    except (IndexError, AttributeError):
        pass
    return result


def _xtn_to_contactpoint(field) -> dict:
    """XTN (Extended Telecom) → ContactPoint."""
    result: dict[str, Any] = {}
    try:
        comps = _get_components(field)
        # XTN-1: telephone number (deprecated but widely used)
        if len(comps) > 0 and comps[0]:
            result["value"] = str(comps[0])
        # XTN-3: telecom equipment type
        if len(comps) > 2 and comps[2]:
            eq_type = str(comps[2])
            result["system"] = {"PH": "phone", "FX": "fax", "CP": "phone",
                                "BP": "pager", "Internet": "email",
                                "X.400": "email"}.get(eq_type, "phone")
        # XTN-2: telecom use code
        if len(comps) > 1 and comps[1]:
            use = str(comps[1])
            result["use"] = {"PRN": "home", "WPN": "work", "ORN": "old",
                             "NET": "home", "BPN": "work"}.get(use, "home")
        # XTN-4: email (if present, overrides XTN-1)
        if len(comps) > 3 and comps[3]:
            result["value"] = str(comps[3])
            result["system"] = "email"
        # XTN-12: unformatted telephone (preferred over XTN-1)
        if len(comps) > 11 and comps[11]:
            result["value"] = str(comps[11])
    except (IndexError, AttributeError):
        pass
    return result


def _cx_to_identifier(field) -> dict:
    """CX (Extended Composite ID) → Identifier."""
    result: dict[str, Any] = {}
    try:
        comps = _get_components(field)
        if len(comps) > 0 and comps[0]:
            result["value"] = str(comps[0])
        if len(comps) > 3 and comps[3]:
            # Assigning authority (HD)
            auth = str(comps[3])
            result["system"] = f"urn:oid:{auth}" if "." in auth else auth
        if len(comps) > 4 and comps[4]:
            id_type = str(comps[4])
            system = V2_TABLE_TO_FHIR_SYSTEM.get("HL70203", "http://terminology.hl7.org/CodeSystem/v2-0203")
            result["type"] = {"coding": [{"system": system, "code": id_type}]}
    except (IndexError, AttributeError):
        pass
    return result


def _cwe_to_codeableconcept(field) -> dict:
    """CWE/CNE/CE (Coded) → CodeableConcept."""
    result: dict[str, Any] = {"coding": []}
    try:
        comps = _get_components(field)
        coding: dict[str, str] = {}
        if len(comps) > 0 and comps[0]:
            coding["code"] = str(comps[0])
        if len(comps) > 1 and comps[1]:
            coding["display"] = str(comps[1])
        if len(comps) > 2 and comps[2]:
            coding["system"] = str(comps[2])
        if coding:
            result["coding"].append(coding)
        # Alternate coding (CWE-4,5,6)
        if len(comps) > 3 and comps[3]:
            alt: dict[str, str] = {"code": str(comps[3])}
            if len(comps) > 4 and comps[4]:
                alt["display"] = str(comps[4])
            if len(comps) > 5 and comps[5]:
                alt["system"] = str(comps[5])
            result["coding"].append(alt)
        # CWE-9: Original text
        if len(comps) > 8 and comps[8]:
            result["text"] = str(comps[8])
    except (IndexError, AttributeError):
        pass
    return result


def _ts_to_datetime(field) -> str | None:
    """TS/DTM → FHIR dateTime string."""
    try:
        val = str(field.value if hasattr(field, "value") else field).strip()
        if not val:
            return None
        # YYYYMMDD[HHmmss[.S[S[S[S]]]]][+/-ZZZZ]
        if len(val) >= 8:
            dt = f"{val[0:4]}-{val[4:6]}-{val[6:8]}"
            if len(val) >= 12:
                dt += f"T{val[8:10]}:{val[10:12]}"
                if len(val) >= 14:
                    dt += f":{val[12:14]}"
            return dt
        return val
    except (ValueError, AttributeError):
        return None


def _get_components(field) -> list:
    """Extract component string values from an hl7apy field/component safely."""
    # hl7apy ElementProxy/Field with children
    if hasattr(field, "children"):
        children = list(field.children)
        if children:
            return [c.value if hasattr(c, "value") else str(c) for c in children]
    # hl7apy object with .value containing ^ delimiters
    if hasattr(field, "value") and field.value:
        parts = str(field.value).split("^")
        if len(parts) > 1:
            return parts
        return [str(field.value)]
    # Plain string
    if isinstance(field, str):
        parts = field.split("^")
        return parts
    return [str(field)] if field else []


def _field_str(field) -> str:
    """Extract plain string value from an hl7apy field."""
    if field is None:
        return ""
    if hasattr(field, "value"):
        return str(field.value) if field.value else ""
    return str(field)


# ═══════════════════════════════════════════════════════════════════════════════
# Segment → FHIR Resource converters
# ═══════════════════════════════════════════════════════════════════════════════

def _pid_to_patient(segment) -> dict:
    """PID segment → Patient resource."""
    patient: dict[str, Any] = {"resourceType": "Patient", "id": str(uuid.uuid4())}

    # PID-3: Patient Identifier List (repeating)
    identifiers = []
    for rep in _get_field_repetitions(segment, 3):
        ident = _cx_to_identifier(rep)
        if ident:
            identifiers.append(ident)
    if identifiers:
        patient["identifier"] = identifiers

    # PID-5: Patient Name (repeating)
    names = []
    for rep in _get_field_repetitions(segment, 5):
        name = _xpn_to_humanname(rep)
        if name:
            names.append(name)
    if names:
        patient["name"] = names

    # PID-7: Date of Birth
    dob = _get_field_value(segment, 7)
    if dob:
        dt = _ts_to_datetime(dob)
        if dt:
            patient["birthDate"] = dt[:10]  # date only

    # PID-8: Administrative Sex
    sex = _get_field_value(segment, 8)
    if sex:
        sex_str = _field_str(sex)
        patient["gender"] = {"M": "male", "F": "female", "O": "other",
                              "U": "unknown", "A": "other"}.get(sex_str, "unknown")

    # PID-11: Patient Address (repeating)
    addresses = []
    for rep in _get_field_repetitions(segment, 11):
        addr = _xad_to_address(rep)
        if addr:
            addresses.append(addr)
    if addresses:
        patient["address"] = addresses

    # PID-13: Phone Home (repeating)
    telecoms = []
    for rep in _get_field_repetitions(segment, 13):
        cp = _xtn_to_contactpoint(rep)
        if cp:
            cp.setdefault("use", "home")
            telecoms.append(cp)
    # PID-14: Phone Business
    for rep in _get_field_repetitions(segment, 14):
        cp = _xtn_to_contactpoint(rep)
        if cp:
            cp["use"] = "work"
            telecoms.append(cp)
    if telecoms:
        patient["telecom"] = telecoms

    # PID-16: Marital Status
    ms = _get_field_value(segment, 16)
    if ms:
        patient["maritalStatus"] = _cwe_to_codeableconcept(ms) if hasattr(ms, "children") else {
            "coding": [{"system": V2_TABLE_TO_FHIR_SYSTEM.get("HL70002", ""), "code": _field_str(ms)}]
        }

    # PID-15: Primary Language
    lang = _get_field_value(segment, 15)
    if lang:
        patient["communication"] = [{"language": {"coding": [{"code": _field_str(lang)}]}}]

    # PID-29: Patient Death Date
    death_dt = _get_field_value(segment, 29)
    if death_dt:
        patient["deceasedDateTime"] = _ts_to_datetime(death_dt)
    else:
        # PID-30: Patient Death Indicator
        death_ind = _get_field_value(segment, 30)
        if death_ind and _field_str(death_ind).upper() == "Y":
            patient["deceasedBoolean"] = True

    patient["active"] = True
    return patient


def _pv1_to_encounter(segment) -> dict:
    """PV1 segment → Encounter resource."""
    encounter: dict[str, Any] = {"resourceType": "Encounter", "id": str(uuid.uuid4())}

    # PV1-2: Patient Class → class (R5: CodeableConcept[])
    pc = _get_field_value(segment, 2)
    if pc:
        encounter["class"] = [{"coding": [{
            "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
            "code": {"I": "IMP", "O": "AMB", "E": "EMER", "P": "PRENC",
                     "R": "IMP", "B": "IMP"}.get(_field_str(pc), _field_str(pc)),
        }]}]

    # PV1-44: Admit Date/Time
    admit_dt = _get_field_value(segment, 44)
    if admit_dt:
        dt = _ts_to_datetime(admit_dt)
        if dt:
            encounter.setdefault("actualPeriod", {})["start"] = dt

    # PV1-45: Discharge Date/Time
    disch_dt = _get_field_value(segment, 45)
    if disch_dt:
        dt = _ts_to_datetime(disch_dt)
        if dt:
            encounter.setdefault("actualPeriod", {})["end"] = dt

    # PV1-36: Discharge Disposition
    disp = _get_field_value(segment, 36)
    if disp:
        encounter.setdefault("admission", {})["dischargeDisposition"] = {
            "coding": [{"system": V2_TABLE_TO_FHIR_SYSTEM.get("HL70112", ""), "code": _field_str(disp)}]
        }

    encounter["status"] = "in-progress"  # Default; override from EVN/context
    return encounter


def _obx_to_observation(segment) -> dict:
    """OBX segment → Observation resource."""
    obs: dict[str, Any] = {"resourceType": "Observation", "id": str(uuid.uuid4())}

    # OBX-3: Observation Identifier → code
    code_field = _get_field_value(segment, 3)
    if code_field:
        obs["code"] = _cwe_to_codeableconcept(code_field) if hasattr(code_field, "children") else {
            "coding": [{"code": _field_str(code_field)}]
        }

    # OBX-2: Value Type + OBX-5: Observation Value
    vtype = _get_field_value(segment, 2)
    val = _get_field_value(segment, 5)
    if val and vtype:
        vtype_str = _field_str(vtype)
        if vtype_str in ("NM", "SN"):
            try:
                obs["valueQuantity"] = {"value": float(_field_str(val))}
            except ValueError:
                obs["valueString"] = _field_str(val)
        elif vtype_str == "ST":
            obs["valueString"] = _field_str(val)
        elif vtype_str == "TX":
            obs["valueString"] = _field_str(val)
        elif vtype_str in ("CWE", "CE", "CNE"):
            obs["valueCodeableConcept"] = _cwe_to_codeableconcept(val) if hasattr(val, "children") else {
                "coding": [{"code": _field_str(val)}]
            }
        elif vtype_str == "DT":
            obs["valueDateTime"] = _ts_to_datetime(val)
        else:
            obs["valueString"] = _field_str(val)

    # OBX-6: Units
    units = _get_field_value(segment, 6)
    if units and "valueQuantity" in obs:
        if hasattr(units, "children"):
            comps = _get_components(units)
            if comps:
                obs["valueQuantity"]["unit"] = str(comps[0]) if comps[0] else None
                if len(comps) > 2 and comps[2]:
                    obs["valueQuantity"]["system"] = str(comps[2])
                if len(comps) > 0 and comps[0]:
                    obs["valueQuantity"]["code"] = str(comps[0])
        else:
            obs["valueQuantity"]["unit"] = _field_str(units)

    # OBX-8: Interpretation
    interp = _get_field_value(segment, 8)
    if interp:
        obs["interpretation"] = [{"coding": [{
            "system": V2_TABLE_TO_FHIR_SYSTEM.get("HL70078", ""),
            "code": _field_str(interp),
        }]}]

    # OBX-11: Observation Result Status
    status = _get_field_value(segment, 11)
    if status:
        obs["status"] = {"F": "final", "P": "preliminary", "C": "corrected",
                         "R": "registered", "I": "registered", "D": "cancelled",
                         "X": "cancelled", "W": "entered-in-error"}.get(_field_str(status), "unknown")
    else:
        obs["status"] = "unknown"

    # OBX-14: Date/Time of Observation
    obs_dt = _get_field_value(segment, 14)
    if obs_dt:
        obs["effectiveDateTime"] = _ts_to_datetime(obs_dt)

    # OBX-7: Reference Range
    ref_range = _get_field_value(segment, 7)
    if ref_range:
        obs["referenceRange"] = [{"text": _field_str(ref_range)}]

    return obs


def _al1_to_allergy(segment) -> dict:
    """AL1 segment → AllergyIntolerance resource."""
    allergy: dict[str, Any] = {"resourceType": "AllergyIntolerance", "id": str(uuid.uuid4())}

    # AL1-2: Allergen Type Code
    atype = _get_field_value(segment, 2)
    if atype:
        type_map = {"DA": "allergy", "FA": "allergy", "MA": "allergy",
                     "MC": "allergy", "EA": "allergy", "AA": "allergy",
                     "LA": "allergy", "PA": "allergy"}
        allergy["type"] = type_map.get(_field_str(atype), "allergy")
        cat_map = {"DA": "medication", "FA": "food", "EA": "environment",
                   "LA": "environment", "PA": "biologic"}
        cat = cat_map.get(_field_str(atype))
        if cat:
            allergy["category"] = [cat]

    # AL1-3: Allergen Code
    code = _get_field_value(segment, 3)
    if code:
        allergy["code"] = _cwe_to_codeableconcept(code) if hasattr(code, "children") else {
            "coding": [{"code": _field_str(code)}]
        }

    # AL1-4: Allergy Severity Code
    sev = _get_field_value(segment, 4)
    if sev:
        allergy["criticality"] = {"SV": "high", "MO": "low", "MI": "low",
                                   "U": "unable-to-assess"}.get(_field_str(sev), "unable-to-assess")

    # AL1-5: Allergy Reaction
    reaction = _get_field_value(segment, 5)
    if reaction:
        allergy["reaction"] = [{"manifestation": [{"concept": {"text": _field_str(reaction)}}]}]

    # AL1-6: Identification Date
    idate = _get_field_value(segment, 6)
    if idate:
        allergy["onsetDateTime"] = _ts_to_datetime(idate)

    allergy["clinicalStatus"] = {
        "coding": [{"system": "http://terminology.hl7.org/CodeSystem/allergyintolerance-clinical", "code": "active"}]
    }
    allergy["verificationStatus"] = {
        "coding": [{"system": "http://terminology.hl7.org/CodeSystem/allergyintolerance-verification", "code": "confirmed"}]
    }
    return allergy


def _dg1_to_condition(segment) -> dict:
    """DG1 segment → Condition resource."""
    condition: dict[str, Any] = {"resourceType": "Condition", "id": str(uuid.uuid4())}

    # DG1-3: Diagnosis Code
    code = _get_field_value(segment, 3)
    if code:
        condition["code"] = _cwe_to_codeableconcept(code) if hasattr(code, "children") else {
            "coding": [{"code": _field_str(code)}]
        }

    # DG1-5: Diagnosis Date/Time
    dt = _get_field_value(segment, 5)
    if dt:
        condition["onsetDateTime"] = _ts_to_datetime(dt)

    # DG1-6: Diagnosis Type
    dtype = _get_field_value(segment, 6)
    if dtype:
        condition["category"] = [{"coding": [{
            "code": {"A": "encounter-diagnosis", "W": "encounter-diagnosis",
                     "F": "problem-list-item"}.get(_field_str(dtype), "encounter-diagnosis")
        }]}]

    condition["clinicalStatus"] = {
        "coding": [{"system": "http://terminology.hl7.org/CodeSystem/condition-clinical", "code": "active"}]
    }
    return condition


def _rxa_to_immunization(segment) -> dict:
    """RXA segment → Immunization resource."""
    imm: dict[str, Any] = {"resourceType": "Immunization", "id": str(uuid.uuid4())}

    # RXA-3: Date/Time Start of Administration
    dt = _get_field_value(segment, 3)
    if dt:
        imm["occurrenceDateTime"] = _ts_to_datetime(dt)

    # RXA-5: Administered Code
    code = _get_field_value(segment, 5)
    if code:
        imm["vaccineCode"] = _cwe_to_codeableconcept(code) if hasattr(code, "children") else {
            "coding": [{"code": _field_str(code)}]
        }

    # RXA-6: Administered Amount
    amt = _get_field_value(segment, 6)
    if amt:
        try:
            imm["doseQuantity"] = {"value": float(_field_str(amt))}
        except ValueError:
            pass

    # RXA-7: Administered Units
    units = _get_field_value(segment, 7)
    if units and "doseQuantity" in imm:
        imm["doseQuantity"]["unit"] = _field_str(units)

    # RXA-15: Substance Lot Number
    lot = _get_field_value(segment, 15)
    if lot:
        imm["lotNumber"] = _field_str(lot)

    # RXA-16: Substance Expiration Date
    exp = _get_field_value(segment, 16)
    if exp:
        imm["expirationDate"] = _ts_to_datetime(exp)

    # RXA-9: Administration Notes → Completion Status
    status_note = _get_field_value(segment, 9)
    if status_note:
        s = _field_str(status_note).upper()
        imm["status"] = "completed" if s in ("CP", "00") else "not-done"
    else:
        imm["status"] = "completed"

    return imm


def _msh_to_messageheader(segment) -> dict:
    """MSH segment → MessageHeader resource."""
    mh: dict[str, Any] = {"resourceType": "MessageHeader", "id": str(uuid.uuid4())}

    # MSH-9: Message Type
    msg_type = _get_field_value(segment, 9)
    if msg_type:
        comps = _field_str(msg_type).split("^") if not hasattr(msg_type, "children") else [str(c) for c in _get_components(msg_type)]
        event_code = comps[1] if len(comps) > 1 else comps[0] if comps else ""
        mh["eventCoding"] = {
            "system": "http://terminology.hl7.org/CodeSystem/v2-0003",
            "code": event_code,
        }

    # MSH-3: Sending Application → source.name
    src = _get_field_value(segment, 3)
    if src:
        mh["source"] = {"name": _field_str(src), "endpoint": f"urn:oid:{src}"}
    else:
        mh["source"] = {"endpoint": "urn:oid:unknown"}

    # MSH-5: Receiving Application → destination
    dst = _get_field_value(segment, 5)
    if dst:
        mh["destination"] = [{"name": _field_str(dst), "endpoint": f"urn:oid:{dst}"}]

    return mh


# ═══════════════════════════════════════════════════════════════════════════════
# Segment converter registry
# ═══════════════════════════════════════════════════════════════════════════════

_SEGMENT_CONVERTERS: dict[str, tuple[str, Any]] = {
    "PID": ("Patient", _pid_to_patient),
    "PV1": ("Encounter", _pv1_to_encounter),
    "OBX": ("Observation", _obx_to_observation),
    "AL1": ("AllergyIntolerance", _al1_to_allergy),
    "DG1": ("Condition", _dg1_to_condition),
    "RXA": ("Immunization", _rxa_to_immunization),
    "MSH": ("MessageHeader", _msh_to_messageheader),
}


# ═══════════════════════════════════════════════════════════════════════════════
# Helper: field access on hl7apy segments
# ═══════════════════════════════════════════════════════════════════════════════

def _get_field_value(segment, index: int) -> Any:
    """Get field value from hl7apy segment by 1-based index."""
    try:
        seg_name = segment.name if hasattr(segment, "name") else str(type(segment).__name__)
        field_name = f"{seg_name.lower()}_{index}"
        field = getattr(segment, field_name, None)
        if field is None:
            # Fallback: try by children index
            children = list(segment.children) if hasattr(segment, "children") else []
            if index < len(children):
                return children[index]
            return None
        return field
    except Exception:
        return None


def _get_field_repetitions(segment, index: int) -> list:
    """Get all repetitions of a repeating field."""
    try:
        seg_name = segment.name if hasattr(segment, "name") else str(type(segment).__name__)
        field_name = f"{seg_name.lower()}_{index}"
        # hl7apy: repeating fields are accessed via list
        field = getattr(segment, field_name, None)
        if field is None:
            return []
        if isinstance(field, list):
            return field
        return [field]
    except Exception:
        return []


# ═══════════════════════════════════════════════════════════════════════════════
# Message normalization — fix common issues before hl7apy parse
# ═══════════════════════════════════════════════════════════════════════════════

# hl7apy supported versions — dynamically loaded, with fallback
try:
    from hl7apy import SUPPORTED_LIBRARIES as _HL7APY_LIBS
    _HL7APY_VERSIONS = set(_HL7APY_LIBS.keys())
except ImportError:
    _HL7APY_VERSIONS = {"2.1", "2.2", "2.3", "2.3.1", "2.4", "2.5", "2.5.1", "2.6", "2.7", "2.8", "2.8.1", "2.8.2"}

def _normalize_v2_message(raw: str) -> str:
    """Normalize a V2 ER7 message for reliable parsing.

    Fixes:
    1. Line endings: \\n → \\r (V2 standard = \\r)
    2. Version: 2.5.1 → 2.5 if hl7apy doesn't support the sub-minor
    3. Strip leading/trailing whitespace
    4. Remove blank lines
    """
    import re

    # 1. Normalize line endings: \r\n → \r, \n → \r
    msg = raw.strip()
    msg = msg.replace("\r\n", "\r").replace("\n", "\r")

    # 2. Remove blank segments
    segments = [s for s in msg.split("\r") if s.strip()]

    # 3. Fix version in MSH-12 if hl7apy doesn't support it
    if segments and segments[0].startswith("MSH"):
        fields = segments[0].split("|")
        if len(fields) > 11:
            version = fields[11].strip()
            if version and version not in _HL7APY_VERSIONS:
                # Try truncating: "2.5.1" → "2.5", "2.8.1" → "2.8"
                parts = version.split(".")
                if len(parts) >= 2:
                    truncated = f"{parts[0]}.{parts[1]}"
                    if truncated in _HL7APY_VERSIONS:
                        fields[11] = truncated
                    else:
                        # Default to 2.5 as safest widely-supported version
                        fields[11] = "2.5"
                else:
                    fields[11] = "2.5"
            segments[0] = "|".join(fields)

    return "\r".join(segments) + "\r"


# ═══════════════════════════════════════════════════════════════════════════════
# V2Converter: Main converter class
# ═══════════════════════════════════════════════════════════════════════════════

class V2Converter:
    """Stateful V2 → FHIR R5 converter.

    Holds converted resources for cross-referencing (e.g. Encounter → Patient ref).

    Example:
        conv = V2Converter()
        bundle = conv.convert(adt_a01_er7_string)
        patient = conv.extract_resource("Patient")
    """

    def __init__(self) -> None:
        self._resources: dict[str, list[dict]] = {}
        self._raw_message = None

    def convert(self, er7_message: str, *, message_type: str | None = None) -> dict:
        """Convert a V2 ER7 message string to a FHIR R5 Bundle.

        Args:
            er7_message: Raw HL7 V2 pipe-delimited message
            message_type: Override message type (auto-detected from MSH-9)

        Returns:
            FHIR R5 Bundle dict
        """
        self._resources.clear()

        # ── Normalize message ─────────────────────────────────────────
        er7_message = _normalize_v2_message(er7_message)

        try:
            from hl7apy.parser import parse_message
            msg = parse_message(er7_message, find_groups=False)
        except ImportError:
            # Fallback: manual parse
            msg = None
            return self._convert_manual(er7_message, message_type)
        except Exception as e:
            # UnsupportedVersion, InvalidName, or any parse error → manual fallback
            msg = None
            return self._convert_manual(er7_message, message_type)

        self._raw_message = msg

        # Process each segment
        for segment in msg.children:
            seg_name = segment.name if hasattr(segment, "name") else ""
            if seg_name in _SEGMENT_CONVERTERS:
                resource_type, converter = _SEGMENT_CONVERTERS[seg_name]
                resource = converter(segment)
                self._resources.setdefault(resource_type, []).append(resource)
            # NTE → attach as note to last Observation/ServiceRequest
            elif seg_name == "NTE":
                note_text = _get_field_value(segment, 3)
                if note_text:
                    self._attach_note(_field_str(note_text))

        # Build cross-references
        self._link_references()

        # Build Bundle
        all_resources = []
        for res_list in self._resources.values():
            all_resources.extend(res_list)

        return self._build_bundle(all_resources, message_type)

    def _convert_manual(self, er7: str, message_type: str | None) -> dict:
        """Fallback manual parser when hl7apy not available or parse fails."""
        self._resources.clear()
        import re
        for line in re.split(r'[\r\n]+', er7.strip()):
            line = line.strip()
            if not line or len(line) < 3:
                continue
            seg_name = line[:3]
            resource = None
            rtype = None
            if seg_name == "MSH":
                resource = self._manual_msh(line)
                rtype = "MessageHeader"
            elif seg_name == "PID":
                resource = self._manual_pid(line)
                rtype = "Patient"
            elif seg_name == "PV1":
                resource = self._manual_pv1(line)
                rtype = "Encounter"
            elif seg_name == "OBX":
                resource = self._manual_obx(line)
                rtype = "Observation"
            elif seg_name == "AL1":
                resource = self._manual_al1(line)
                rtype = "AllergyIntolerance"
            elif seg_name == "DG1":
                resource = self._manual_dg1(line)
                rtype = "Condition"
            if resource and rtype:
                self._resources.setdefault(rtype, []).append(resource)

        self._link_references()
        all_resources = []
        for res_list in self._resources.values():
            all_resources.extend(res_list)
        return self._build_bundle(all_resources, message_type)

    def _manual_pid(self, line: str) -> dict:
        """Minimal PID parsing without hl7apy."""
        fields = line.split("|")
        patient: dict[str, Any] = {"resourceType": "Patient", "id": str(uuid.uuid4()), "active": True}
        if len(fields) > 5 and fields[5]:
            comps = fields[5].split("^")
            name: dict[str, Any] = {}
            if comps[0]:
                name["family"] = comps[0]
            if len(comps) > 1 and comps[1]:
                name["given"] = [comps[1]]
            if name:
                patient["name"] = [name]
        if len(fields) > 7 and fields[7]:
            raw = fields[7]
            if len(raw) >= 8:
                patient["birthDate"] = f"{raw[0:4]}-{raw[4:6]}-{raw[6:8]}"
        if len(fields) > 8 and fields[8]:
            patient["gender"] = {"M": "male", "F": "female"}.get(fields[8], "unknown")
        return patient

    def _manual_msh(self, line: str) -> dict:
        """Minimal MSH parsing without hl7apy."""
        fields = line.split("|")
        mh: dict[str, Any] = {"resourceType": "MessageHeader", "id": str(uuid.uuid4())}
        if len(fields) > 8 and fields[8]:
            parts = fields[8].split("^")
            mh["eventCoding"] = {
                "system": "http://terminology.hl7.org/CodeSystem/v2-0003",
                "code": parts[1] if len(parts) > 1 else parts[0],
            }
        if len(fields) > 2 and fields[2]:
            mh["source"] = {"name": fields[2], "endpoint": f"urn:oid:{fields[2]}"}
        else:
            mh["source"] = {"endpoint": "urn:oid:unknown"}
        return mh

    def _manual_pv1(self, line: str) -> dict:
        """Minimal PV1 parsing without hl7apy."""
        fields = line.split("|")
        enc: dict[str, Any] = {"resourceType": "Encounter", "id": str(uuid.uuid4()), "status": "in-progress"}
        if len(fields) > 2 and fields[2]:
            code = {"I": "IMP", "O": "AMB", "E": "EMER", "P": "PRENC"}.get(fields[2].strip(), fields[2].strip())
            enc["class"] = [{"coding": [{"system": "http://terminology.hl7.org/CodeSystem/v3-ActCode", "code": code}]}]
        return enc

    def _manual_obx(self, line: str) -> dict:
        """Minimal OBX parsing without hl7apy."""
        fields = line.split("|")
        obs: dict[str, Any] = {"resourceType": "Observation", "id": str(uuid.uuid4()), "status": "unknown"}
        if len(fields) > 3 and fields[3]:
            comps = fields[3].split("^")
            coding: dict[str, str] = {}
            if comps[0]: coding["code"] = comps[0]
            if len(comps) > 1 and comps[1]: coding["display"] = comps[1]
            if len(comps) > 2 and comps[2]: coding["system"] = comps[2]
            obs["code"] = {"coding": [coding]}
        if len(fields) > 5 and fields[5]:
            vtype = fields[2] if len(fields) > 2 else "ST"
            if vtype == "NM":
                try:
                    obs["valueQuantity"] = {"value": float(fields[5])}
                    if len(fields) > 6 and fields[6]:
                        obs["valueQuantity"]["unit"] = fields[6]
                except ValueError:
                    obs["valueString"] = fields[5]
            else:
                obs["valueString"] = fields[5]
        if len(fields) > 11 and fields[11]:
            obs["status"] = {"F": "final", "P": "preliminary", "C": "corrected"}.get(fields[11], "unknown")
        return obs

    def _manual_al1(self, line: str) -> dict:
        """Minimal AL1 parsing without hl7apy."""
        fields = line.split("|")
        allergy: dict[str, Any] = {"resourceType": "AllergyIntolerance", "id": str(uuid.uuid4())}
        if len(fields) > 3 and fields[3]:
            comps = fields[3].split("^")
            coding = {"code": comps[0]}
            if len(comps) > 1: coding["display"] = comps[1]
            allergy["code"] = {"coding": [coding]}
        if len(fields) > 4 and fields[4]:
            allergy["criticality"] = {"SV": "high", "MO": "low", "MI": "low"}.get(fields[4], "unable-to-assess")
        allergy["clinicalStatus"] = {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/allergyintolerance-clinical", "code": "active"}]}
        return allergy

    def _manual_dg1(self, line: str) -> dict:
        """Minimal DG1 parsing without hl7apy."""
        fields = line.split("|")
        cond: dict[str, Any] = {"resourceType": "Condition", "id": str(uuid.uuid4())}
        if len(fields) > 3 and fields[3]:
            comps = fields[3].split("^")
            coding = {"code": comps[0]}
            if len(comps) > 1: coding["display"] = comps[1]
            if len(comps) > 2: coding["system"] = comps[2]
            cond["code"] = {"coding": [coding]}
        cond["clinicalStatus"] = {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/condition-clinical", "code": "active"}]}
        return cond

    def _attach_note(self, text: str) -> None:
        """Attach NTE note to last Observation or ServiceRequest."""
        for rt in ("Observation", "ServiceRequest", "DiagnosticReport"):
            if rt in self._resources and self._resources[rt]:
                last = self._resources[rt][-1]
                last.setdefault("note", []).append({"text": text})
                return

    def _link_references(self) -> None:
        """Add cross-references between resources (Patient→Encounter, etc.)."""
        patient_ref = None
        if "Patient" in self._resources and self._resources["Patient"]:
            pid = self._resources["Patient"][0]["id"]
            patient_ref = {"reference": f"Patient/{pid}"}

        if patient_ref:
            for rt in ("Encounter", "Observation", "AllergyIntolerance",
                       "Condition", "Immunization", "MedicationRequest"):
                for r in self._resources.get(rt, []):
                    r["subject"] = patient_ref

        # Encounter → Observation.encounter
        if "Encounter" in self._resources and self._resources["Encounter"]:
            enc_id = self._resources["Encounter"][0]["id"]
            enc_ref = {"reference": f"Encounter/{enc_id}"}
            for rt in ("Observation", "Condition", "AllergyIntolerance"):
                for r in self._resources.get(rt, []):
                    r["encounter"] = enc_ref

    def _build_bundle(self, resources: list[dict], message_type: str | None) -> dict:
        """Assemble the final FHIR Bundle."""
        entries = []
        for r in resources:
            entries.append({
                "fullUrl": f"urn:uuid:{r.get('id', uuid.uuid4())}",
                "resource": r,
            })
        return {
            "resourceType": "Bundle",
            "id": str(uuid.uuid4()),
            "type": "message",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "entry": entries,
        }

    def extract_resource(self, resource_type: str, index: int = 0) -> dict | None:
        """Extract a specific resource from the last conversion."""
        resources = self._resources.get(resource_type, [])
        return resources[index] if index < len(resources) else None

    def extract_all(self, resource_type: str) -> list[dict]:
        """Extract all resources of a type from the last conversion."""
        return self._resources.get(resource_type, [])


# ═══════════════════════════════════════════════════════════════════════════════
# FHIR R5 → V2.x reverse converter
# ═══════════════════════════════════════════════════════════════════════════════

def _patient_to_pid(patient: dict) -> str:
    """Patient resource → PID segment ER7."""
    fields = [""] * 31
    fields[0] = "PID"

    # PID-3: Identifier
    for i, ident in enumerate(patient.get("identifier", [])):
        val = ident.get("value", "")
        system = ident.get("system", "")
        fields[3] = f"{val}^^^{system}^MR"
        break  # First only for PID-3

    # PID-5: Name
    for name in patient.get("name", []):
        family = name.get("family", "")
        given = name.get("given", [""])[0] if name.get("given") else ""
        fields[5] = f"{family}^{given}"
        break

    # PID-7: DOB
    dob = patient.get("birthDate", "")
    if dob:
        fields[7] = dob.replace("-", "")

    # PID-8: Gender
    gender = patient.get("gender", "")
    fields[8] = {"male": "M", "female": "F", "other": "O", "unknown": "U"}.get(gender, "U")

    # PID-11: Address
    for addr in patient.get("address", []):
        line = addr.get("line", [""])[0] if addr.get("line") else ""
        city = addr.get("city", "")
        state = addr.get("state", "")
        postal = addr.get("postalCode", "")
        country = addr.get("country", "")
        fields[11] = f"{line}^^{city}^{state}^{postal}^{country}"
        break

    # PID-13: Telecom
    for cp in patient.get("telecom", []):
        if cp.get("system") == "phone":
            fields[13] = cp.get("value", "")
            break

    return "|".join(fields)


def _encounter_to_pv1(encounter: dict) -> str:
    """Encounter resource → PV1 segment ER7."""
    fields = [""] * 46
    fields[0] = "PV1"

    # PV1-2: Patient Class
    classes = encounter.get("class", [])
    if classes and isinstance(classes, list) and classes:
        codings = classes[0].get("coding", [])
        if codings:
            code = codings[0].get("code", "")
            fields[2] = {"IMP": "I", "AMB": "O", "EMER": "E", "PRENC": "P"}.get(code, code)

    # PV1-44: Admit DateTime
    period = encounter.get("actualPeriod", {})
    if "start" in period:
        fields[44] = period["start"].replace("-", "").replace("T", "").replace(":", "")[:14]
    if "end" in period:
        fields[45] = period["end"].replace("-", "").replace("T", "").replace(":", "")[:14]

    return "|".join(fields)


_R5_TO_V2_CONVERTERS: dict[str, Any] = {
    "Patient": _patient_to_pid,
    "Encounter": _encounter_to_pv1,
}


def r5_to_v2(
    resources: dict | list[dict],
    *,
    message_type: str = "ADT_A01",
    version: str = "2.5.1",
    sending_app: str = "BRIGHTOHIR",
    receiving_app: str = "EXTERNAL",
) -> str:
    """Convert FHIR R5 resource(s) to V2 ER7 message string.

    Args:
        resources: Single resource dict or list of resource dicts
        message_type: V2 message structure (e.g. "ADT_A01", "ORU_R01")
        version: V2 version string
        sending_app: MSH-3
        receiving_app: MSH-5

    Returns:
        ER7-formatted V2 message string
    """
    if isinstance(resources, dict):
        # If it's a Bundle, extract entries
        if resources.get("resourceType") == "Bundle":
            resources = [e["resource"] for e in resources.get("entry", []) if "resource" in e]
        else:
            resources = [resources]

    segments: list[str] = []

    # MSH
    msg_parts = message_type.split("_")
    msg_code = msg_parts[0] if msg_parts else "ADT"
    trigger = msg_parts[1] if len(msg_parts) > 1 else "A01"
    now = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    msh = (
        f"MSH|^~\\&|{sending_app}||{receiving_app}||{now}||"
        f"{msg_code}^{trigger}^{message_type}|{uuid.uuid4().hex[:10]}|P|{version}"
    )
    segments.append(msh)

    # EVN
    segments.append(f"EVN|{trigger}|{now}")

    # Convert each resource
    for res in resources:
        rt = res.get("resourceType", "")
        converter = _R5_TO_V2_CONVERTERS.get(rt)
        if converter:
            seg = converter(res)
            if seg:
                segments.append(seg)

    return "\r".join(segments) + "\r"


# ═══════════════════════════════════════════════════════════════════════════════
# Convenience functions
# ═══════════════════════════════════════════════════════════════════════════════

def v2_to_r5(er7_message: str) -> dict:
    """Quick-convert a V2 message to FHIR R5 Bundle.

    Args:
        er7_message: Raw HL7 V2 ER7 string

    Returns:
        FHIR R5 Bundle dict
    """
    return V2Converter().convert(er7_message)