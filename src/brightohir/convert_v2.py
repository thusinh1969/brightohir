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


def _nk1_to_relatedperson(segment) -> dict:
    """NK1 segment → RelatedPerson resource."""
    rp: dict[str, Any] = {"resourceType": "RelatedPerson", "id": str(uuid.uuid4()), "active": True}
    # NK1-2: Name
    name_field = _get_field_value(segment, 2)
    if name_field:
        rp["name"] = [_xpn_to_humanname(name_field)]
    # NK1-3: Relationship
    rel = _get_field_value(segment, 3)
    if rel:
        rp["relationship"] = [_cwe_to_codeableconcept(rel) if hasattr(rel, "children") else {
            "coding": [{"system": V2_TABLE_TO_FHIR_SYSTEM.get("HL70063", ""), "code": _field_str(rel)}]}]
    # NK1-4: Address
    addr = _get_field_value(segment, 4)
    if addr:
        rp["address"] = [_xad_to_address(addr)]
    # NK1-5: Phone
    phone = _get_field_value(segment, 5)
    if phone:
        rp["telecom"] = [_xtn_to_contactpoint(phone)]
    # NK1-7: Contact Role
    role = _get_field_value(segment, 7)
    if role:
        rp.setdefault("relationship", []).append({"coding": [{
            "system": V2_TABLE_TO_FHIR_SYSTEM.get("HL70131", ""), "code": _field_str(role)}]})
    # NK1-8: Start Date
    start = _get_field_value(segment, 8)
    if start:
        dt = _ts_to_datetime(start)
        if dt:
            rp["period"] = {"start": dt}
    return rp


def _in1_to_coverage(segment) -> dict:
    """IN1 segment → Coverage resource."""
    cov: dict[str, Any] = {"resourceType": "Coverage", "id": str(uuid.uuid4()), "status": "active"}
    # IN1-2: Insurance Plan ID
    plan = _get_field_value(segment, 2)
    if plan:
        cov["type"] = _cwe_to_codeableconcept(plan) if hasattr(plan, "children") else {
            "coding": [{"code": _field_str(plan)}]}
    # IN1-3: Insurance Company ID
    company = _get_field_value(segment, 3)
    if company:
        org_id = str(uuid.uuid4())
        cov["_insurer_org"] = {"resourceType": "Organization", "id": org_id,
                                "identifier": [_cx_to_identifier(company)]}
        cov["insurer"] = {"reference": f"Organization/{org_id}"}
    # IN1-4: Insurance Company Name
    name = _get_field_value(segment, 4)
    if name and "_insurer_org" in cov:
        cov["_insurer_org"]["name"] = _field_str(name)
    # IN1-12: Plan Effective Date
    eff = _get_field_value(segment, 12)
    if eff:
        dt = _ts_to_datetime(eff)
        if dt:
            cov.setdefault("period", {})["start"] = dt
    # IN1-13: Plan Expiration Date
    exp = _get_field_value(segment, 13)
    if exp:
        dt = _ts_to_datetime(exp)
        if dt:
            cov.setdefault("period", {})["end"] = dt
    # IN1-15: Plan Type
    ptype = _get_field_value(segment, 15)
    if ptype:
        cov["class"] = [{"type": {"coding": [{"code": "plan"}]}, "value": {"coding": [{"code": _field_str(ptype)}]}}]
    # IN1-36: Policy Number
    policy = _get_field_value(segment, 36)
    if policy:
        cov["identifier"] = [{"value": _field_str(policy)}]
    # IN1-46: Subscriber ID (repeating)
    sub = _get_field_value(segment, 46)
    if not sub:
        sub = _get_field_value(segment, 49)
    if sub:
        cov["subscriberId"] = _field_str(sub)
    cov["kind"] = "insurance"
    return cov


def _gt1_to_account(segment) -> dict:
    """GT1 segment → Account resource (guarantor)."""
    acct: dict[str, Any] = {"resourceType": "Account", "id": str(uuid.uuid4()), "status": "active"}
    # GT1-3: Guarantor Name → create embedded RelatedPerson
    name = _get_field_value(segment, 3)
    rp_id = str(uuid.uuid4())
    rp: dict[str, Any] = {"resourceType": "RelatedPerson", "id": rp_id, "active": True}
    if name:
        rp["name"] = [_xpn_to_humanname(name)]
    # GT1-5: Guarantor Address
    addr = _get_field_value(segment, 5)
    if addr:
        rp["address"] = [_xad_to_address(addr)]
    # GT1-6: Guarantor Phone Home
    phone = _get_field_value(segment, 6)
    if phone:
        rp["telecom"] = [_xtn_to_contactpoint(phone)]
    acct["_guarantor_rp"] = rp
    acct["guarantor"] = [{"party": {"reference": f"RelatedPerson/{rp_id}"}}]
    return acct


def _orc_to_servicerequest(segment) -> dict:
    """ORC segment → ServiceRequest resource."""
    sr: dict[str, Any] = {"resourceType": "ServiceRequest", "id": str(uuid.uuid4())}
    # ORC-1: Order Control → status/intent
    ctrl = _get_field_value(segment, 1)
    if ctrl:
        ctrl_str = _field_str(ctrl)
        sr["status"] = {"NW": "active", "CA": "revoked", "DC": "completed",
                        "HD": "on-hold", "SC": "active", "RP": "active",
                        "OC": "revoked", "CR": "active"}.get(ctrl_str, "active")
    sr["intent"] = "order"
    # ORC-2: Placer Order Number → identifier
    placer = _get_field_value(segment, 2)
    if placer:
        sr.setdefault("identifier", []).append({**_cx_to_identifier(placer), "use": "usual"} if hasattr(placer, "children") else {"value": _field_str(placer), "use": "usual"})
    # ORC-3: Filler Order Number → identifier
    filler = _get_field_value(segment, 3)
    if filler:
        sr.setdefault("identifier", []).append({**_cx_to_identifier(filler), "use": "official"} if hasattr(filler, "children") else {"value": _field_str(filler), "use": "official"})
    # ORC-9: Date/Time of Transaction
    txdt = _get_field_value(segment, 9)
    if txdt:
        sr["authoredOn"] = _ts_to_datetime(txdt)
    # ORC-12: Ordering Provider
    prov = _get_field_value(segment, 12)
    if prov:
        comps = _get_components(prov)
        if comps:
            sr["requester"] = {"display": " ".join(str(c) for c in comps[:3] if c)}
    # ORC-5: Order Status
    ostatus = _get_field_value(segment, 5)
    if ostatus:
        s = _field_str(ostatus)
        sr["status"] = {"A": "active", "CA": "revoked", "CM": "completed",
                        "DC": "revoked", "HD": "on-hold", "IP": "active",
                        "SC": "active"}.get(s, sr.get("status", "active"))
    # ORC-16: Order Control Code Reason
    reason = _get_field_value(segment, 16)
    if reason:
        sr["reasonCode"] = [_cwe_to_codeableconcept(reason)] if hasattr(reason, "children") else [{"text": _field_str(reason)}]
    # ORC-15: Order Effective Date/Time
    eff = _get_field_value(segment, 15)
    if eff:
        sr["occurrenceDateTime"] = _ts_to_datetime(eff)
    return sr


def _obr_to_diagnosticreport(segment) -> dict:
    """OBR segment → DiagnosticReport resource."""
    dr: dict[str, Any] = {"resourceType": "DiagnosticReport", "id": str(uuid.uuid4())}
    # OBR-2: Placer Order Number
    placer = _get_field_value(segment, 2)
    if placer:
        dr["identifier"] = [{"value": _field_str(placer), "use": "usual"}]
    # OBR-4: Universal Service Identifier → code
    code = _get_field_value(segment, 4)
    if code:
        dr["code"] = _cwe_to_codeableconcept(code) if hasattr(code, "children") else {"coding": [{"code": _field_str(code)}]}
    # OBR-7: Observation Date/Time
    obsdt = _get_field_value(segment, 7)
    if obsdt:
        dt = _ts_to_datetime(obsdt)
        if dt:
            dr["effectiveDateTime"] = dt
    # OBR-22: Results Rpt/Status Chng Date
    rptdt = _get_field_value(segment, 22)
    if rptdt:
        dr["issued"] = _ts_to_datetime(rptdt)
    # OBR-25: Result Status
    rstat = _get_field_value(segment, 25)
    if rstat:
        s = _field_str(rstat)
        dr["status"] = {"F": "final", "P": "preliminary", "C": "corrected",
                        "A": "partial", "R": "registered", "I": "registered",
                        "O": "registered", "X": "cancelled"}.get(s, "unknown")
    else:
        dr["status"] = "unknown"
    # OBR-16: Ordering Provider
    prov = _get_field_value(segment, 16)
    if prov:
        comps = _get_components(prov)
        if comps:
            dr["performer"] = [{"display": " ".join(str(c) for c in comps[:3] if c)}]
    # OBR-24: Diagnostic Serv Sect ID
    sect = _get_field_value(segment, 24)
    if sect:
        dr["category"] = [{"coding": [{"code": _field_str(sect)}]}]
    return dr


def _rxe_to_medicationrequest(segment) -> dict:
    """RXE segment → MedicationRequest (encoded order)."""
    mr: dict[str, Any] = {"resourceType": "MedicationRequest", "id": str(uuid.uuid4()),
                           "status": "active", "intent": "order"}
    # RXE-2: Give Code → medication
    code = _get_field_value(segment, 2)
    if code:
        mr["medication"] = {"concept": _cwe_to_codeableconcept(code) if hasattr(code, "children") else {"coding": [{"code": _field_str(code)}]}}
    # RXE-3: Give Amount Minimum
    amt = _get_field_value(segment, 3)
    dose: dict[str, Any] = {}
    if amt:
        try:
            dose["doseAndRate"] = [{"doseQuantity": {"value": float(_field_str(amt))}}]
        except ValueError:
            pass
    # RXE-5: Give Units
    units = _get_field_value(segment, 5)
    if units and "doseAndRate" in dose:
        dose["doseAndRate"][0]["doseQuantity"]["unit"] = _field_str(units)
    # RXE-1: Quantity/Timing → text
    timing = _get_field_value(segment, 1)
    if timing:
        dose["text"] = _field_str(timing)
    if dose:
        mr["dosageInstruction"] = [dose]
    # RXE-10: Dispense Amount
    disp_amt = _get_field_value(segment, 10)
    if disp_amt:
        try:
            mr.setdefault("dispenseRequest", {})["quantity"] = {"value": float(_field_str(disp_amt))}
        except ValueError:
            pass
    # RXE-11: Dispense Units
    disp_units = _get_field_value(segment, 11)
    if disp_units and "dispenseRequest" in mr:
        mr["dispenseRequest"]["quantity"]["unit"] = _field_str(disp_units)
    # RXE-12: Number of Refills
    refills = _get_field_value(segment, 12)
    if refills:
        try:
            mr.setdefault("dispenseRequest", {})["numberOfRepeatsAllowed"] = int(_field_str(refills))
        except ValueError:
            pass
    # RXE-15: Prescription Number → identifier
    rxnum = _get_field_value(segment, 15)
    if rxnum:
        mr["identifier"] = [{"value": _field_str(rxnum), "use": "official"}]
    return mr


def _rxd_to_medicationdispense(segment) -> dict:
    """RXD segment → MedicationDispense resource."""
    md: dict[str, Any] = {"resourceType": "MedicationDispense", "id": str(uuid.uuid4()), "status": "completed"}
    # RXD-2: Dispense/Give Code
    code = _get_field_value(segment, 2)
    if code:
        md["medication"] = {"concept": _cwe_to_codeableconcept(code) if hasattr(code, "children") else {"coding": [{"code": _field_str(code)}]}}
    # RXD-4: Actual Dispense Amount
    amt = _get_field_value(segment, 4)
    if amt:
        try:
            md["quantity"] = {"value": float(_field_str(amt))}
        except ValueError:
            pass
    # RXD-5: Actual Dispense Units
    units = _get_field_value(segment, 5)
    if units and "quantity" in md:
        md["quantity"]["unit"] = _field_str(units)
    # RXD-3: Date/Time Dispensed
    dtdisp = _get_field_value(segment, 3)
    if dtdisp:
        md["whenHandedOver"] = _ts_to_datetime(dtdisp)
    # RXD-7: Prescription Number → authorizingPrescription
    rxnum = _get_field_value(segment, 7)
    if rxnum:
        md["authorizingPrescription"] = [{"identifier": {"value": _field_str(rxnum)}}]
    # RXD-10: Dispenser → performer
    disp = _get_field_value(segment, 10)
    if disp:
        comps = _get_components(disp)
        md["performer"] = [{"actor": {"display": " ".join(str(c) for c in comps[:3] if c)}}]
    # RXD-20: Substance Lot Number
    lot = _get_field_value(segment, 20)
    if lot:
        md["_lotNumber"] = _field_str(lot)
    return md


def _rxo_to_medicationrequest(segment) -> dict:
    """RXO segment → MedicationRequest (original order)."""
    mr: dict[str, Any] = {"resourceType": "MedicationRequest", "id": str(uuid.uuid4()),
                           "status": "active", "intent": "order"}
    # RXO-1: Requested Give Code
    code = _get_field_value(segment, 1)
    if code:
        mr["medication"] = {"concept": _cwe_to_codeableconcept(code) if hasattr(code, "children") else {"coding": [{"code": _field_str(code)}]}}
    # RXO-2: Requested Give Amount Minimum
    amt = _get_field_value(segment, 2)
    dose: dict[str, Any] = {}
    if amt:
        try:
            dose["doseAndRate"] = [{"doseQuantity": {"value": float(_field_str(amt))}}]
        except ValueError:
            pass
    # RXO-4: Requested Give Units
    units = _get_field_value(segment, 4)
    if units and "doseAndRate" in dose:
        dose["doseAndRate"][0]["doseQuantity"]["unit"] = _field_str(units)
    if dose:
        mr["dosageInstruction"] = [dose]
    # RXO-10: Requested Dispense Amount
    disp = _get_field_value(segment, 10)
    if disp:
        try:
            mr.setdefault("dispenseRequest", {})["quantity"] = {"value": float(_field_str(disp))}
        except ValueError:
            pass
    # RXO-12: Number of Refills
    refills = _get_field_value(segment, 12)
    if refills:
        try:
            mr.setdefault("dispenseRequest", {})["numberOfRepeatsAllowed"] = int(_field_str(refills))
        except ValueError:
            pass
    return mr


def _spm_to_specimen(segment) -> dict:
    """SPM segment → Specimen resource."""
    spec: dict[str, Any] = {"resourceType": "Specimen", "id": str(uuid.uuid4())}
    # SPM-2: Specimen ID
    sid = _get_field_value(segment, 2)
    if sid:
        spec["identifier"] = [{"value": _field_str(sid)}]
    # SPM-4: Specimen Type
    stype = _get_field_value(segment, 4)
    if stype:
        spec["type"] = _cwe_to_codeableconcept(stype) if hasattr(stype, "children") else {
            "coding": [{"system": V2_TABLE_TO_FHIR_SYSTEM.get("HL70487", ""), "code": _field_str(stype)}]}
    # SPM-17: Collection Date/Time → collection.collectedDateTime
    cdt = _get_field_value(segment, 17)
    if cdt:
        spec["collection"] = {"collectedDateTime": _ts_to_datetime(cdt)}
    # SPM-8: Specimen Source Site
    site = _get_field_value(segment, 8)
    if site:
        spec.setdefault("collection", {})["bodySite"] = {
            "concept": _cwe_to_codeableconcept(site) if hasattr(site, "children") else {"coding": [{"code": _field_str(site)}]}}
    # SPM-11: Specimen Role
    role = _get_field_value(segment, 11)
    if role:
        spec["role"] = [_cwe_to_codeableconcept(role) if hasattr(role, "children") else {"coding": [{"code": _field_str(role)}]}]
    # SPM-14: Specimen Description
    desc = _get_field_value(segment, 14)
    if desc:
        spec["note"] = [{"text": _field_str(desc)}]
    # SPM-20: Specimen Availability
    avail = _get_field_value(segment, 20)
    if avail:
        spec["status"] = {"Y": "available", "N": "unavailable"}.get(_field_str(avail), "available")
    return spec


def _sch_to_appointment(segment) -> dict:
    """SCH segment → Appointment resource."""
    appt: dict[str, Any] = {"resourceType": "Appointment", "id": str(uuid.uuid4())}
    # SCH-1: Placer Appointment ID
    pid = _get_field_value(segment, 1)
    if pid:
        appt["identifier"] = [{"value": _field_str(pid), "use": "usual"}]
    # SCH-2: Filler Appointment ID
    fid = _get_field_value(segment, 2)
    if fid:
        appt.setdefault("identifier", []).append({"value": _field_str(fid), "use": "official"})
    # SCH-7: Appointment Reason
    reason = _get_field_value(segment, 7)
    if reason:
        appt["reasonCode"] = [_cwe_to_codeableconcept(reason) if hasattr(reason, "children") else {"text": _field_str(reason)}]
    # SCH-11: Appointment Timing Quantity → start/end
    timing = _get_field_value(segment, 11)
    if timing:
        comps = _get_components(timing)
        if comps and comps[0]:
            dt = _ts_to_datetime(type("F", (), {"value": str(comps[0])})())
            if dt:
                appt["start"] = dt
    # SCH-25: Filler Status Code → status
    fstat = _get_field_value(segment, 25)
    if fstat:
        s = _field_str(fstat)
        appt["status"] = {"Booked": "booked", "Pending": "proposed", "Complete": "fulfilled",
                          "Cancelled": "cancelled", "Noshow": "noshow"}.get(s, "proposed")
    else:
        appt["status"] = "proposed"
    # SCH-6: Event Reason
    ereason = _get_field_value(segment, 6)
    if ereason:
        appt["description"] = _field_str(ereason)
    return appt


def _txa_to_documentreference(segment) -> dict:
    """TXA segment → DocumentReference resource."""
    dr: dict[str, Any] = {"resourceType": "DocumentReference", "id": str(uuid.uuid4()), "status": "current"}
    # TXA-2: Document Type
    dtype = _get_field_value(segment, 2)
    if dtype:
        dr["type"] = _cwe_to_codeableconcept(dtype) if hasattr(dtype, "children") else {
            "coding": [{"code": _field_str(dtype)}]}
    # TXA-3: Document Content Presentation
    pres = _get_field_value(segment, 3)
    if pres:
        p = _field_str(pres)
        dr["content"] = [{"attachment": {"contentType": {
            "TX": "text/plain", "FT": "text/plain", "PN": "text/plain",
            "AU": "audio/basic", "IM": "image/jpeg", "AP": "application/pdf",
        }.get(p, "application/octet-stream")}}]
    # TXA-4: Activity Date/Time
    adt = _get_field_value(segment, 4)
    if adt:
        dr["date"] = _ts_to_datetime(adt)
    # TXA-5: Primary Activity Provider
    prov = _get_field_value(segment, 5)
    if prov:
        comps = _get_components(prov)
        if comps:
            dr["author"] = [{"display": " ".join(str(c) for c in comps[:3] if c)}]
    # TXA-12: Unique Document Number → identifier
    docnum = _get_field_value(segment, 12)
    if docnum:
        dr["identifier"] = [{"value": _field_str(docnum)}]
    # TXA-17: Document Completion Status
    cstat = _get_field_value(segment, 17)
    if cstat:
        s = _field_str(cstat)
        dr["docStatus"] = {"DO": "preliminary", "IN": "preliminary", "IP": "preliminary",
                           "AU": "final", "DI": "amended", "LA": "final",
                           "PA": "preliminary"}.get(s, "preliminary")
    return dr


def _prt_to_practitionerrole(segment) -> dict:
    """PRT segment → PractitionerRole resource."""
    pr: dict[str, Any] = {"resourceType": "PractitionerRole", "id": str(uuid.uuid4()), "active": True}
    # PRT-4: Role of Participation
    role = _get_field_value(segment, 4)
    if role:
        pr["code"] = [_cwe_to_codeableconcept(role) if hasattr(role, "children") else {
            "coding": [{"system": V2_TABLE_TO_FHIR_SYSTEM.get("HL70443", ""), "code": _field_str(role)}]}]
    # PRT-5: Person → practitioner reference
    person = _get_field_value(segment, 5)
    if person:
        comps = _get_components(person)
        pract_id = str(uuid.uuid4())
        pr["practitioner"] = {"reference": f"Practitioner/{pract_id}",
                              "display": " ".join(str(c) for c in comps[:3] if c)}
    # PRT-6: Provider Type
    ptype = _get_field_value(segment, 6)
    if ptype:
        pr["specialty"] = [_cwe_to_codeableconcept(ptype) if hasattr(ptype, "children") else {"coding": [{"code": _field_str(ptype)}]}]
    # PRT-11: Begin Date/Time
    bdt = _get_field_value(segment, 11)
    if bdt:
        pr["period"] = {"start": _ts_to_datetime(bdt)}
    # PRT-12: End Date/Time
    edt = _get_field_value(segment, 12)
    if edt:
        pr.setdefault("period", {})["end"] = _ts_to_datetime(edt)
    return pr


# ═══════════════════════════════════════════════════════════════════════════════
# Segment converter registry
# ═══════════════════════════════════════════════════════════════════════════════

_SEGMENT_CONVERTERS: dict[str, tuple[str, Any]] = {
    "MSH": ("MessageHeader", _msh_to_messageheader),
    "PID": ("Patient", _pid_to_patient),
    "PV1": ("Encounter", _pv1_to_encounter),
    "OBX": ("Observation", _obx_to_observation),
    "AL1": ("AllergyIntolerance", _al1_to_allergy),
    "DG1": ("Condition", _dg1_to_condition),
    "RXA": ("Immunization", _rxa_to_immunization),
    "NK1": ("RelatedPerson", _nk1_to_relatedperson),
    "IN1": ("Coverage", _in1_to_coverage),
    "GT1": ("Account", _gt1_to_account),
    "ORC": ("ServiceRequest", _orc_to_servicerequest),
    "OBR": ("DiagnosticReport", _obr_to_diagnosticreport),
    "RXE": ("MedicationRequest", _rxe_to_medicationrequest),
    "RXD": ("MedicationDispense", _rxd_to_medicationdispense),
    "RXO": ("MedicationRequest", _rxo_to_medicationrequest),
    "SPM": ("Specimen", _spm_to_specimen),
    "SCH": ("Appointment", _sch_to_appointment),
    "TXA": ("DocumentReference", _txa_to_documentreference),
    "PRT": ("PractitionerRole", _prt_to_practitionerrole),
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
            for rt in ("Encounter", "Observation", "AllergyIntolerance", "Condition",
                       "Immunization", "MedicationRequest", "MedicationDispense",
                       "ServiceRequest", "DiagnosticReport", "Coverage", "Specimen",
                       "DocumentReference", "Appointment"):
                for r in self._resources.get(rt, []):
                    if rt in ("Coverage",):
                        r["beneficiary"] = patient_ref
                    elif rt in ("Appointment",):
                        r.setdefault("participant", []).append({"actor": patient_ref, "status": "accepted"})
                    else:
                        r["subject"] = patient_ref
            for r in self._resources.get("RelatedPerson", []):
                r["patient"] = patient_ref
            for r in self._resources.get("Account", []):
                r.setdefault("subject", []).append(patient_ref)

        # Encounter reference
        if "Encounter" in self._resources and self._resources["Encounter"]:
            enc_id = self._resources["Encounter"][0]["id"]
            enc_ref = {"reference": f"Encounter/{enc_id}"}
            for rt in ("Observation", "Condition", "AllergyIntolerance", "Immunization",
                       "MedicationRequest", "MedicationDispense", "ServiceRequest",
                       "DiagnosticReport", "Specimen", "DocumentReference"):
                for r in self._resources.get(rt, []):
                    r["encounter"] = enc_ref

        # ServiceRequest → DiagnosticReport.basedOn
        if "ServiceRequest" in self._resources and self._resources["ServiceRequest"]:
            sr_id = self._resources["ServiceRequest"][0]["id"]
            sr_ref = {"reference": f"ServiceRequest/{sr_id}"}
            for r in self._resources.get("DiagnosticReport", []):
                r["basedOn"] = [sr_ref]
            for r in self._resources.get("Specimen", []):
                r.setdefault("request", []).append(sr_ref)

        # DiagnosticReport → Observation.derivedFrom / result
        if "DiagnosticReport" in self._resources and self._resources["DiagnosticReport"]:
            dr = self._resources["DiagnosticReport"][0]
            obs_refs = [{"reference": f"Observation/{o['id']}"} for o in self._resources.get("Observation", [])]
            if obs_refs:
                dr["result"] = obs_refs

        # Extract embedded Organization from Coverage._insurer_org
        for cov in self._resources.get("Coverage", []):
            if "_insurer_org" in cov:
                org = cov.pop("_insurer_org")
                self._resources.setdefault("Organization", []).append(org)

        # Extract embedded RelatedPerson from Account._guarantor_rp
        for acct in self._resources.get("Account", []):
            if "_guarantor_rp" in acct:
                rp = acct.pop("_guarantor_rp")
                self._resources.setdefault("RelatedPerson", []).append(rp)

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


def _fhir_dt_to_v2(dt: str | None) -> str:
    """FHIR dateTime → V2 TS format."""
    if not dt:
        return ""
    return dt.replace("-", "").replace("T", "").replace(":", "").replace("Z", "")[:14]


def _fhir_code_to_v2(cc: dict | None) -> str:
    """CodeableConcept → V2 CWE format (code^display^system)."""
    if not cc:
        return ""
    codings = cc.get("coding", [])
    if not codings:
        return cc.get("text", "")
    c = codings[0]
    parts = [c.get("code", ""), c.get("display", ""), c.get("system", "")]
    return "^".join(parts).rstrip("^")


def _observation_to_obx(obs: dict) -> str:
    """Observation → OBX segment."""
    fields = [""] * 20
    fields[0] = "OBX"
    fields[1] = "1"
    # OBX-3: code
    fields[3] = _fhir_code_to_v2(obs.get("code"))
    # Determine value type and value
    if "valueQuantity" in obs:
        fields[2] = "NM"
        vq = obs["valueQuantity"]
        fields[5] = str(vq.get("value", ""))
        fields[6] = vq.get("unit", "")
    elif "valueString" in obs:
        fields[2] = "ST"
        fields[5] = obs["valueString"]
    elif "valueCodeableConcept" in obs:
        fields[2] = "CWE"
        fields[5] = _fhir_code_to_v2(obs["valueCodeableConcept"])
    elif "valueDateTime" in obs:
        fields[2] = "DT"
        fields[5] = _fhir_dt_to_v2(obs.get("valueDateTime"))
    # OBX-7: reference range
    rr = obs.get("referenceRange", [])
    if rr:
        fields[7] = rr[0].get("text", "")
    # OBX-8: interpretation
    interp = obs.get("interpretation", [])
    if interp:
        fields[8] = interp[0].get("coding", [{}])[0].get("code", "")
    # OBX-11: status
    status = obs.get("status", "")
    fields[11] = {"final": "F", "preliminary": "P", "corrected": "C", "registered": "R",
                  "cancelled": "X", "entered-in-error": "W", "unknown": "U"}.get(status, "F")
    # OBX-14: effective datetime
    fields[14] = _fhir_dt_to_v2(obs.get("effectiveDateTime"))
    return "|".join(fields)


def _allergy_to_al1(allergy: dict) -> str:
    """AllergyIntolerance → AL1 segment."""
    fields = [""] * 7
    fields[0] = "AL1"
    fields[1] = "1"
    # AL1-2: type → allergen type
    cats = allergy.get("category", [])
    if cats:
        fields[2] = {"medication": "DA", "food": "FA", "environment": "EA", "biologic": "PA"}.get(cats[0], "DA")
    # AL1-3: code
    fields[3] = _fhir_code_to_v2(allergy.get("code"))
    # AL1-4: severity
    crit = allergy.get("criticality", "")
    fields[4] = {"high": "SV", "low": "MI", "unable-to-assess": "U"}.get(crit, "")
    # AL1-5: reaction
    reactions = allergy.get("reaction", [])
    if reactions:
        manifests = reactions[0].get("manifestation", [])
        if manifests:
            fields[5] = manifests[0].get("concept", {}).get("text", "")
    # AL1-6: onset
    fields[6] = _fhir_dt_to_v2(allergy.get("onsetDateTime"))
    return "|".join(fields)


def _condition_to_dg1(condition: dict) -> str:
    """Condition → DG1 segment."""
    fields = [""] * 7
    fields[0] = "DG1"
    fields[1] = "1"
    fields[3] = _fhir_code_to_v2(condition.get("code"))
    fields[5] = _fhir_dt_to_v2(condition.get("onsetDateTime"))
    cats = condition.get("category", [])
    if cats:
        c = cats[0].get("coding", [{}])[0].get("code", "")
        fields[6] = {"encounter-diagnosis": "A", "problem-list-item": "F"}.get(c, "A")
    return "|".join(fields)


def _immunization_to_rxa(imm: dict) -> str:
    """Immunization → RXA segment."""
    fields = [""] * 22
    fields[0] = "RXA"
    fields[1] = "0"
    fields[2] = "1"
    fields[3] = _fhir_dt_to_v2(imm.get("occurrenceDateTime"))
    fields[4] = fields[3]  # End = Start for single admin
    fields[5] = _fhir_code_to_v2(imm.get("vaccineCode"))
    dq = imm.get("doseQuantity", {})
    if dq:
        fields[6] = str(dq.get("value", ""))
        fields[7] = dq.get("unit", "")
    fields[9] = {"completed": "CP", "not-done": "RE"}.get(imm.get("status", ""), "CP")
    fields[15] = imm.get("lotNumber", "")
    fields[16] = _fhir_dt_to_v2(imm.get("expirationDate"))
    return "|".join(fields)


def _relatedperson_to_nk1(rp: dict) -> str:
    """RelatedPerson → NK1 segment."""
    fields = [""] * 8
    fields[0] = "NK1"
    fields[1] = "1"
    names = rp.get("name", [])
    if names:
        n = names[0]
        fields[2] = f"{n.get('family', '')}^{(n.get('given', ['']))[0] if n.get('given') else ''}"
    rels = rp.get("relationship", [])
    if rels:
        fields[3] = _fhir_code_to_v2(rels[0])
    addrs = rp.get("address", [])
    if addrs:
        a = addrs[0]
        line = a.get("line", [""])[0] if a.get("line") else ""
        fields[4] = f"{line}^^{a.get('city', '')}^{a.get('state', '')}^{a.get('postalCode', '')}^{a.get('country', '')}"
    telecoms = rp.get("telecom", [])
    if telecoms:
        fields[5] = telecoms[0].get("value", "")
    return "|".join(fields)


def _coverage_to_in1(cov: dict) -> str:
    """Coverage → IN1 segment."""
    fields = [""] * 50
    fields[0] = "IN1"
    fields[1] = "1"
    fields[2] = _fhir_code_to_v2(cov.get("type"))
    idents = cov.get("identifier", [])
    if idents:
        fields[36] = idents[0].get("value", "")
    period = cov.get("period", {})
    fields[12] = _fhir_dt_to_v2(period.get("start"))
    fields[13] = _fhir_dt_to_v2(period.get("end"))
    if cov.get("subscriberId"):
        fields[49] = cov["subscriberId"]
    return "|".join(fields)


def _servicerequest_to_orc(sr: dict) -> str:
    """ServiceRequest → ORC segment."""
    fields = [""] * 17
    fields[0] = "ORC"
    status = sr.get("status", "")
    fields[1] = {"active": "NW", "revoked": "CA", "completed": "DC",
                 "on-hold": "HD"}.get(status, "NW")
    idents = sr.get("identifier", [])
    for ident in idents:
        if ident.get("use") == "usual":
            fields[2] = ident.get("value", "")
        elif ident.get("use") == "official":
            fields[3] = ident.get("value", "")
    fields[5] = {"active": "IP", "revoked": "CA", "completed": "CM",
                 "on-hold": "HD"}.get(status, "IP")
    fields[9] = _fhir_dt_to_v2(sr.get("authoredOn"))
    req = sr.get("requester", {})
    if req:
        fields[12] = req.get("display", "")
    return "|".join(fields)


def _medicationrequest_to_rxe(mr: dict) -> str:
    """MedicationRequest → RXE segment."""
    fields = [""] * 16
    fields[0] = "RXE"
    med = mr.get("medication", {})
    if "concept" in med:
        fields[2] = _fhir_code_to_v2(med["concept"])
    dosages = mr.get("dosageInstruction", [])
    if dosages:
        d = dosages[0]
        fields[1] = d.get("text", "")
        dr = d.get("doseAndRate", [{}])
        if dr:
            dq = dr[0].get("doseQuantity", {})
            fields[3] = str(dq.get("value", ""))
            fields[5] = dq.get("unit", "")
    disp = mr.get("dispenseRequest", {})
    if "quantity" in disp:
        fields[10] = str(disp["quantity"].get("value", ""))
        fields[11] = disp["quantity"].get("unit", "")
    if "numberOfRepeatsAllowed" in disp:
        fields[12] = str(disp["numberOfRepeatsAllowed"])
    idents = mr.get("identifier", [])
    if idents:
        fields[15] = idents[0].get("value", "")
    return "|".join(fields)


def _medicationdispense_to_rxd(md: dict) -> str:
    """MedicationDispense → RXD segment."""
    fields = [""] * 21
    fields[0] = "RXD"
    fields[1] = "1"
    med = md.get("medication", {})
    if "concept" in med:
        fields[2] = _fhir_code_to_v2(med["concept"])
    fields[3] = _fhir_dt_to_v2(md.get("whenHandedOver"))
    qty = md.get("quantity", {})
    if qty:
        fields[4] = str(qty.get("value", ""))
        fields[5] = qty.get("unit", "")
    auth = md.get("authorizingPrescription", [])
    if auth:
        fields[7] = auth[0].get("identifier", {}).get("value", "")
    return "|".join(fields)


def _specimen_to_spm(spec: dict) -> str:
    """Specimen → SPM segment."""
    fields = [""] * 21
    fields[0] = "SPM"
    fields[1] = "1"
    idents = spec.get("identifier", [])
    if idents:
        fields[2] = idents[0].get("value", "")
    fields[4] = _fhir_code_to_v2(spec.get("type"))
    coll = spec.get("collection", {})
    if coll:
        fields[17] = _fhir_dt_to_v2(coll.get("collectedDateTime"))
    fields[20] = {"available": "Y", "unavailable": "N"}.get(spec.get("status", ""), "Y")
    return "|".join(fields)


def _documentreference_to_txa(dr: dict) -> str:
    """DocumentReference → TXA segment."""
    fields = [""] * 18
    fields[0] = "TXA"
    fields[1] = "1"
    fields[2] = _fhir_code_to_v2(dr.get("type"))
    fields[4] = _fhir_dt_to_v2(dr.get("date"))
    authors = dr.get("author", [])
    if authors:
        fields[5] = authors[0].get("display", "")
    idents = dr.get("identifier", [])
    if idents:
        fields[12] = idents[0].get("value", "")
    ds = dr.get("docStatus", "")
    fields[17] = {"final": "AU", "preliminary": "IP", "amended": "DI"}.get(ds, "IP")
    return "|".join(fields)


def _diagnosticreport_to_obr(dr: dict) -> str:
    """DiagnosticReport → OBR segment."""
    fields = [""] * 26
    fields[0] = "OBR"
    fields[1] = "1"
    idents = dr.get("identifier", [])
    if idents:
        fields[2] = idents[0].get("value", "")
    fields[4] = _fhir_code_to_v2(dr.get("code"))
    fields[7] = _fhir_dt_to_v2(dr.get("effectiveDateTime"))
    fields[22] = _fhir_dt_to_v2(dr.get("issued"))
    status = dr.get("status", "")
    fields[25] = {"final": "F", "preliminary": "P", "corrected": "C",
                  "partial": "A", "registered": "O", "cancelled": "X"}.get(status, "F")
    return "|".join(fields)


def _appointment_to_sch(appt: dict) -> str:
    """Appointment → SCH segment."""
    fields = [""] * 26
    fields[0] = "SCH"
    idents = appt.get("identifier", [])
    for ident in idents:
        if ident.get("use") == "usual":
            fields[1] = ident.get("value", "")
        elif ident.get("use") == "official":
            fields[2] = ident.get("value", "")
    fields[6] = appt.get("description", "")
    reasons = appt.get("reasonCode", [])
    if reasons:
        fields[7] = _fhir_code_to_v2(reasons[0]) if "coding" in reasons[0] else reasons[0].get("text", "")
    fields[11] = _fhir_dt_to_v2(appt.get("start"))
    status = appt.get("status", "")
    fields[25] = {"booked": "Booked", "proposed": "Pending", "fulfilled": "Complete",
                  "cancelled": "Cancelled", "noshow": "Noshow"}.get(status, "Pending")
    return "|".join(fields)


_R5_TO_V2_CONVERTERS: dict[str, Any] = {
    "Patient": _patient_to_pid,
    "Encounter": _encounter_to_pv1,
    "Observation": _observation_to_obx,
    "AllergyIntolerance": _allergy_to_al1,
    "Condition": _condition_to_dg1,
    "Immunization": _immunization_to_rxa,
    "RelatedPerson": _relatedperson_to_nk1,
    "Coverage": _coverage_to_in1,
    "ServiceRequest": _servicerequest_to_orc,
    "MedicationRequest": _medicationrequest_to_rxe,
    "MedicationDispense": _medicationdispense_to_rxd,
    "Specimen": _specimen_to_spm,
    "DocumentReference": _documentreference_to_txa,
    "DiagnosticReport": _diagnosticreport_to_obr,
    "Appointment": _appointment_to_sch,
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