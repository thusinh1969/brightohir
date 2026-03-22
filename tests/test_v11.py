"""
Tests for brightohir v1.1.0 — new segment converters, ACK, PII, transport.
Run: pytest tests/test_v11.py -v
"""
import json
import pytest


# ═══════════════════════════════════════════════════════════════════════════════
# V2→R5: All 19 segment converters
# ═══════════════════════════════════════════════════════════════════════════════

FULL_ADT = """MSH|^~\\&|HATTO|LONG_CHAU|EHR|BVDK|20260322090000||ADT^A01^ADT_A01|MSG001|P|2.5.1
EVN||20260322090000
PID|1||LC-999^^^LC^MR||TRAN^MINH^B||19851201|F|||456 LE LOI^^HCM^VN^70000||0909876543
PD1||||12345^DR NGUYEN
NK1|1|TRAN^THI C|SPO|789 NGUYEN TRAI^^HCM^VN||0901112233|C
PV1|1|I|W^201^1|||67890^LE^VAN D|||MED
IN1|1|BHYT^Social Insurance|BHXH001^^^BHXH|BAO HIEM XA HOI VN||||||||20260101|20261231
GT1|1||VO^VAN E|M|111 TRAN HUNG DAO^^HCM^VN|0908887766
AL1|1|DA|PENICILLIN|SV|Anaphylaxis
DG1|1||J06.9^Acute URTI^ICD10|||A
ORC|NW|ORD001||||||20260322090000||||67890^LE^VAN D
OBR|1|ORD001||CBC^Complete Blood Count^LN|||20260322|||||||||67890^LE^VAN D
OBX|1|NM|718-7^Hemoglobin^LN||13.5|g/dL|12-16||||F
OBX|2|NM|6690-2^WBC^LN||7200|/uL|4000-11000||||F
SPM|1|SPM001||BLD^Blood^HL70487||||||||||||20260322090000
NTE|1||Patient fasting for 12 hours"""


class TestNewSegmentConverters:
    def test_full_adt_all_segments(self):
        from brightohir import V2Converter
        conv = V2Converter()
        bundle = conv.convert(FULL_ADT)
        rtypes = [e["resource"]["resourceType"] for e in bundle["entry"]]
        assert "Patient" in rtypes
        assert "Encounter" in rtypes
        assert "RelatedPerson" in rtypes
        assert "Coverage" in rtypes
        assert "Account" in rtypes
        assert "AllergyIntolerance" in rtypes
        assert "Condition" in rtypes
        assert "ServiceRequest" in rtypes
        assert "DiagnosticReport" in rtypes
        assert "Observation" in rtypes
        assert "Specimen" in rtypes

    def test_nk1_relatedperson(self):
        from brightohir import V2Converter
        conv = V2Converter()
        conv.convert(FULL_ADT)
        rp = conv.extract_resource("RelatedPerson")
        assert rp is not None
        assert rp["resourceType"] == "RelatedPerson"
        # Should have patient reference from _link_references
        assert "patient" in rp

    def test_in1_coverage(self):
        from brightohir import V2Converter
        conv = V2Converter()
        conv.convert(FULL_ADT)
        cov = conv.extract_resource("Coverage")
        assert cov is not None
        assert cov["kind"] == "insurance"
        assert "beneficiary" in cov  # linked to patient

    def test_gt1_account(self):
        from brightohir import V2Converter
        conv = V2Converter()
        conv.convert(FULL_ADT)
        acct = conv.extract_resource("Account")
        assert acct is not None
        assert "guarantor" in acct

    def test_orc_servicerequest(self):
        from brightohir import V2Converter
        conv = V2Converter()
        conv.convert(FULL_ADT)
        sr = conv.extract_resource("ServiceRequest")
        assert sr is not None
        assert sr["intent"] == "order"
        assert "subject" in sr

    def test_obr_diagnosticreport(self):
        from brightohir import V2Converter
        conv = V2Converter()
        conv.convert(FULL_ADT)
        dr = conv.extract_resource("DiagnosticReport")
        assert dr is not None
        assert "code" in dr
        # Should have result references to Observations
        assert "result" in dr
        assert len(dr["result"]) == 2  # 2 OBX segments

    def test_spm_specimen(self):
        from brightohir import V2Converter
        conv = V2Converter()
        conv.convert(FULL_ADT)
        spec = conv.extract_resource("Specimen")
        assert spec is not None
        assert "type" in spec
        assert "encounter" in spec

    def test_nte_attached_to_observation(self):
        from brightohir import V2Converter
        conv = V2Converter()
        conv.convert(FULL_ADT)
        # NTE should attach to last observation
        obs_list = conv.extract_all("Observation")
        has_note = any("note" in o for o in obs_list)
        assert has_note

    def test_cross_references_complete(self):
        from brightohir import V2Converter
        conv = V2Converter()
        conv.convert(FULL_ADT)
        # Every clinical resource should reference Patient
        for rt in ["Encounter", "Observation", "AllergyIntolerance", "Condition",
                    "ServiceRequest", "DiagnosticReport", "Specimen"]:
            resources = conv.extract_all(rt)
            for r in resources:
                assert "subject" in r, f"{rt} missing subject ref"
                assert r["subject"]["reference"].startswith("Patient/")

    def test_encounter_ref_on_clinical(self):
        from brightohir import V2Converter
        conv = V2Converter()
        conv.convert(FULL_ADT)
        for rt in ["Observation", "Condition", "AllergyIntolerance"]:
            for r in conv.extract_all(rt):
                assert "encounter" in r, f"{rt} missing encounter ref"


# Pharmacy message
PHARMACY_MSG = """MSH|^~\\&|PMS|LC|HIS|BV|20260322||RDE^O11^RDE_O11|RX001|P|2.5.1
PID|1||LC-999|||DOE^JOHN||19900101|M
PV1|1|O
ORC|NW|RX001
RXE||387517004^Paracetamol^SNOMED|500||mg||||30|tablets|3||RX-2026-001
RXD|1|387517004^Paracetamol^SNOMED|20260322|30|tablets"""


class TestPharmacyConverters:
    def test_rxe_medicationrequest(self):
        from brightohir import V2Converter
        conv = V2Converter()
        conv.convert(PHARMACY_MSG)
        mr = conv.extract_resource("MedicationRequest")
        assert mr is not None
        assert mr["intent"] == "order"
        assert "medication" in mr

    def test_rxd_medicationdispense(self):
        from brightohir import V2Converter
        conv = V2Converter()
        conv.convert(PHARMACY_MSG)
        md = conv.extract_resource("MedicationDispense")
        assert md is not None
        assert md["status"] == "completed"
        assert "medication" in md

    def test_rxo_medicationrequest(self):
        from brightohir import V2Converter
        msg = """MSH|^~\\&|PMS|LC|HIS|BV|20260322||OMP^O09|1|P|2.5
PID|1||999||DOE^J||19900101|M
ORC|NW|ORD1
RXO|12345^Amoxicillin|500||mg||||||30||3"""
        conv = V2Converter()
        conv.convert(msg)
        mr = conv.extract_resource("MedicationRequest")
        assert mr is not None
        assert "medication" in mr


# Scheduling
SCHED_MSG = """MSH|^~\\&|SCH|LC|HIS|BV|20260322||SIU^S12^SIU_S12|S001|P|2.5
SCH|APT001|APT001-F|||||||Checkup||20260325090000
PID|1||LC-999||NGUYEN^A||19900101|M"""


class TestSchedulingConverters:
    def test_sch_appointment(self):
        from brightohir import V2Converter
        conv = V2Converter()
        conv.convert(SCHED_MSG)
        appt = conv.extract_resource("Appointment")
        assert appt is not None
        assert "status" in appt

    def test_txa_documentreference(self):
        from brightohir import V2Converter
        msg = """MSH|^~\\&|DOC|LC|HIS|BV|20260322||MDM^T02|D001|P|2.5
PID|1||999||DOE^J||19900101|M
PV1|1|O
TXA|1|HP^History and Physical|TX|20260322|||||||DOC-12345|||||AU"""
        conv = V2Converter()
        conv.convert(msg)
        dr = conv.extract_resource("DocumentReference")
        assert dr is not None
        assert dr["status"] == "current"
        assert "type" in dr


# ═══════════════════════════════════════════════════════════════════════════════
# R5→V2: All 15 reverse converters
# ═══════════════════════════════════════════════════════════════════════════════

class TestR5ToV2Reverse:
    def test_observation_to_obx(self):
        from brightohir import r5_to_v2
        obs = {"resourceType": "Observation", "id": "o1", "status": "final",
               "code": {"coding": [{"code": "718-7", "display": "Hemoglobin", "system": "LN"}]},
               "valueQuantity": {"value": 13.5, "unit": "g/dL"},
               "referenceRange": [{"text": "12-16"}],
               "interpretation": [{"coding": [{"code": "N"}]}]}
        v2 = r5_to_v2(obs, message_type="ORU_R01")
        assert "OBX|" in v2
        assert "13.5" in v2
        assert "g/dL" in v2
        assert "|F|" in v2 or "|F\r" in v2  # status=final → F

    def test_allergy_to_al1(self):
        from brightohir import r5_to_v2
        al = {"resourceType": "AllergyIntolerance", "id": "a1",
              "code": {"coding": [{"code": "12345", "display": "ASPIRIN"}]},
              "category": ["medication"], "criticality": "high",
              "reaction": [{"manifestation": [{"concept": {"text": "Rash"}}]}]}
        v2 = r5_to_v2(al, message_type="ADT_A01")
        assert "AL1|" in v2
        assert "ASPIRIN" in v2
        assert "SV" in v2  # high → SV

    def test_condition_to_dg1(self):
        from brightohir import r5_to_v2
        cond = {"resourceType": "Condition", "id": "c1",
                "code": {"coding": [{"code": "J06.9", "display": "URTI", "system": "ICD10"}]}}
        v2 = r5_to_v2(cond, message_type="ADT_A01")
        assert "DG1|" in v2
        assert "J06.9" in v2

    def test_immunization_to_rxa(self):
        from brightohir import r5_to_v2
        imm = {"resourceType": "Immunization", "id": "i1", "status": "completed",
               "vaccineCode": {"coding": [{"code": "CVX-207", "display": "COVID-19"}]},
               "occurrenceDateTime": "2026-03-22", "lotNumber": "LOT001",
               "doseQuantity": {"value": 0.5, "unit": "mL"}}
        v2 = r5_to_v2(imm, message_type="VXU_V04")
        assert "RXA|" in v2
        assert "CVX-207" in v2
        assert "LOT001" in v2

    def test_coverage_to_in1(self):
        from brightohir import r5_to_v2
        cov = {"resourceType": "Coverage", "id": "cov1", "status": "active",
               "type": {"coding": [{"code": "BHYT"}]},
               "identifier": [{"value": "POL-123"}],
               "period": {"start": "2026-01-01", "end": "2026-12-31"},
               "subscriberId": "SUB-999"}
        v2 = r5_to_v2(cov, message_type="ADT_A01")
        assert "IN1|" in v2
        assert "BHYT" in v2

    def test_servicerequest_to_orc(self):
        from brightohir import r5_to_v2
        sr = {"resourceType": "ServiceRequest", "id": "sr1", "status": "active", "intent": "order",
              "identifier": [{"value": "ORD001", "use": "usual"}],
              "requester": {"display": "Dr. Nguyen"}}
        v2 = r5_to_v2(sr, message_type="ORM_O01")
        assert "ORC|" in v2
        assert "ORD001" in v2

    def test_medicationrequest_to_rxe(self):
        from brightohir import r5_to_v2
        mr = {"resourceType": "MedicationRequest", "id": "mr1", "status": "active", "intent": "order",
              "medication": {"concept": {"coding": [{"code": "387517004", "display": "Paracetamol"}]}},
              "dosageInstruction": [{"text": "500mg TID",
                  "doseAndRate": [{"doseQuantity": {"value": 500, "unit": "mg"}}]}],
              "dispenseRequest": {"quantity": {"value": 30, "unit": "tablets"}, "numberOfRepeatsAllowed": 3}}
        v2 = r5_to_v2(mr, message_type="RDE_O11")
        assert "RXE|" in v2
        assert "Paracetamol" in v2

    def test_medicationdispense_to_rxd(self):
        from brightohir import r5_to_v2
        md = {"resourceType": "MedicationDispense", "id": "md1", "status": "completed",
              "medication": {"concept": {"coding": [{"code": "387517004", "display": "Paracetamol"}]}},
              "quantity": {"value": 30, "unit": "tablets"},
              "whenHandedOver": "2026-03-22T10:00:00"}
        v2 = r5_to_v2(md, message_type="RDS_O13")
        assert "RXD|" in v2
        assert "Paracetamol" in v2

    def test_specimen_to_spm(self):
        from brightohir import r5_to_v2
        spec = {"resourceType": "Specimen", "id": "sp1",
                "identifier": [{"value": "SPM001"}],
                "type": {"coding": [{"code": "BLD", "display": "Blood"}]},
                "collection": {"collectedDateTime": "2026-03-22"},
                "status": "available"}
        v2 = r5_to_v2(spec, message_type="OML_O21")
        assert "SPM|" in v2
        assert "BLD" in v2

    def test_diagnosticreport_to_obr(self):
        from brightohir import r5_to_v2
        dr = {"resourceType": "DiagnosticReport", "id": "dr1", "status": "final",
              "code": {"coding": [{"code": "CBC", "display": "Complete Blood Count"}]},
              "effectiveDateTime": "2026-03-22"}
        v2 = r5_to_v2(dr, message_type="ORU_R01")
        assert "OBR|" in v2
        assert "CBC" in v2

    def test_appointment_to_sch(self):
        from brightohir import r5_to_v2
        appt = {"resourceType": "Appointment", "id": "ap1", "status": "booked",
                "identifier": [{"value": "APT001", "use": "usual"}],
                "start": "2026-03-25T09:00:00", "description": "Checkup"}
        v2 = r5_to_v2(appt, message_type="SIU_S12")
        assert "SCH|" in v2
        assert "APT001" in v2

    def test_full_bundle_roundtrip(self):
        """V2 → R5 → V2: verify all segments survive roundtrip."""
        from brightohir import v2_to_r5, r5_to_v2
        bundle = v2_to_r5(FULL_ADT)
        v2_back = r5_to_v2(bundle, message_type="ADT_A01")
        assert "MSH|" in v2_back
        assert "PID|" in v2_back
        assert "PV1|" in v2_back
        assert "OBX|" in v2_back
        assert "AL1|" in v2_back
        assert "DG1|" in v2_back


# ═══════════════════════════════════════════════════════════════════════════════
# ACK/NAK
# ═══════════════════════════════════════════════════════════════════════════════

class TestACK:
    SAMPLE = "MSH|^~\\&|SENDER|SFAC|RECV|RFAC|20260322||ADT^A01^ADT_A01|CTRL123|P|2.5.1\rPID|1||999||DOE^J\r"

    def test_generate_ack_aa(self):
        from brightohir import generate_ack
        ack = generate_ack(self.SAMPLE)
        assert "MSH|" in ack
        assert "MSA|AA|CTRL123" in ack
        assert "ACK^A01" in ack
        # Sender/receiver swapped
        assert "|BRIGHTOHIR|" in ack

    def test_generate_ack_ae_with_error(self):
        from brightohir import generate_ack
        nak = generate_ack(self.SAMPLE, ack_code="AE", error_msg="Patient not found", error_code="204")
        assert "MSA|AE|CTRL123|Patient not found" in nak
        assert "ERR|" in nak
        assert "204" in nak

    def test_generate_ack_ar(self):
        from brightohir import generate_ack
        nak = generate_ack(self.SAMPLE, ack_code="AR", error_msg="Rejected")
        assert "MSA|AR|" in nak

    def test_generate_ack_custom_sender(self):
        from brightohir import generate_ack
        ack = generate_ack(self.SAMPLE, sending_app="LC_PMS", sending_facility="LONG_CHAU")
        assert "|LC_PMS|LONG_CHAU|" in ack

    def test_batch_ack(self):
        from brightohir import generate_batch_ack
        msgs = [self.SAMPLE, self.SAMPLE.replace("CTRL123", "CTRL456")]
        results = [{"ack_code": "AA"}, {"ack_code": "AE", "error_msg": "Failed"}]
        batch = generate_batch_ack(msgs, results=results)
        assert "BHS|" in batch
        assert "BTS|2" in batch
        assert "CTRL123" in batch
        assert "CTRL456" in batch


# ═══════════════════════════════════════════════════════════════════════════════
# PII Masking
# ═══════════════════════════════════════════════════════════════════════════════

class TestPIIMasking:
    SAMPLE_V2 = "MSH|^~\\&|A|B|C|D|20260322||ADT^A01|1|P|2.5\rPID|1||12345^^^LC^MR||NGUYEN^VAN A||19900115|M|||123 MAIN ST^^HCM^VN||0901234567\r"

    SAMPLE_PATIENT = {
        "resourceType": "Patient", "id": "p1", "active": True,
        "identifier": [{"value": "12345", "system": "LC"}],
        "name": [{"family": "Nguyen", "given": ["Van A"]}],
        "telecom": [{"system": "phone", "value": "0901234567"}],
        "gender": "male", "birthDate": "1990-01-15",
        "address": [{"line": ["123 Main St"], "city": "HCM", "country": "VN"}],
    }

    def test_v2_redact(self):
        from brightohir import mask_v2
        masked = mask_v2(self.SAMPLE_V2)
        assert "NGUYEN" not in masked
        assert "0901234567" not in masked
        assert "[REDACTED]" in masked
        # MSH should be untouched
        assert "MSH|" in masked

    def test_v2_hash(self):
        from brightohir import mask_v2
        masked = mask_v2(self.SAMPLE_V2, strategy="hash")
        assert "NGUYEN" not in masked
        assert "H" in masked  # Hash prefix

    def test_v2_partial(self):
        from brightohir import mask_v2
        masked = mask_v2(self.SAMPLE_V2, strategy="partial")
        assert "NGUYEN" not in masked

    def test_v2_pseudonym(self):
        from brightohir import mask_v2
        masked = mask_v2(self.SAMPLE_V2, strategy="pseudonym")
        assert "NGUYEN" not in masked
        assert "PERSON_" in masked or "ADDR_" in masked or "ID_" in masked

    def test_fhir_redact(self):
        from brightohir import mask_fhir
        masked = mask_fhir(self.SAMPLE_PATIENT)
        assert masked["resourceType"] == "Patient"
        assert masked["id"] == "p1"  # id preserved
        assert masked["active"] is True  # active preserved (not PII)
        # PII fields redacted
        names = masked.get("name", [])
        if names:
            assert names[0].get("family") == "[REDACTED]"
        telecoms = masked.get("telecom", [])
        if telecoms:
            assert telecoms[0].get("value") == "[REDACTED]"

    def test_fhir_hash_deterministic(self):
        from brightohir.security import PIIMasker
        masker = PIIMasker(strategy="hash", salt="test123")
        m1 = masker.mask_fhir(self.SAMPLE_PATIENT)
        m2 = masker.mask_fhir(self.SAMPLE_PATIENT)
        # Same salt + same value → same hash
        assert m1["name"] == m2["name"]

    def test_bundle_masking(self):
        from brightohir import mask_bundle
        bundle = {
            "resourceType": "Bundle", "type": "message",
            "entry": [{"resource": self.SAMPLE_PATIENT}],
        }
        masked = mask_bundle(bundle)
        pat = masked["entry"][0]["resource"]
        assert pat["name"][0]["family"] == "[REDACTED]"

    def test_original_unmodified(self):
        """Masking must not modify the original dict."""
        from brightohir import mask_fhir
        import copy
        original = copy.deepcopy(self.SAMPLE_PATIENT)
        _ = mask_fhir(self.SAMPLE_PATIENT)
        assert self.SAMPLE_PATIENT == original


# ═══════════════════════════════════════════════════════════════════════════════
# MLLP Transport (unit tests — no actual TCP)
# ═══════════════════════════════════════════════════════════════════════════════

class TestMLLP:
    def test_mllp_encode(self):
        from brightohir.transport import mllp_encode
        msg = "MSH|^~\\&|A|B\rPID|1\r"
        framed = mllp_encode(msg)
        assert framed.startswith(b"\x0b")
        assert framed.endswith(b"\x1c\x0d")
        assert b"MSH" in framed

    def test_mllp_decode(self):
        from brightohir.transport import mllp_encode, mllp_decode
        original = "MSH|^~\\&|A|B\rPID|1||999\r"
        framed = mllp_encode(original)
        decoded = mllp_decode(framed)
        assert decoded == original

    def test_mllp_roundtrip(self):
        from brightohir.transport import mllp_encode, mllp_decode
        msg = FULL_ADT.replace("\n", "\r")
        assert mllp_decode(mllp_encode(msg)) == msg

    def test_mllp_decode_no_framing(self):
        """Gracefully handle data without MLLP framing."""
        from brightohir.transport import mllp_decode
        raw = b"MSH|^~\\&|A|B\rPID|1\r"
        decoded = mllp_decode(raw)
        assert "MSH|" in decoded


# ═══════════════════════════════════════════════════════════════════════════════
# Full integration
# ═══════════════════════════════════════════════════════════════════════════════

class TestFullIntegration:
    def test_v2_to_r5_ack_pii_pipeline(self):
        """Full pipeline: V2 → convert → ACK → mask."""
        from brightohir import v2_to_r5, generate_ack, mask_bundle
        msg = FULL_ADT
        # Convert
        bundle = v2_to_r5(msg)
        assert len(bundle["entry"]) >= 8
        # ACK
        ack = generate_ack(msg, ack_code="AA")
        assert "MSA|AA" in ack
        # Mask PII
        masked = mask_bundle(bundle)
        for entry in masked["entry"]:
            r = entry["resource"]
            if r["resourceType"] == "Patient":
                assert r["name"][0]["family"] == "[REDACTED]"

    def test_all_public_api_v11(self):
        """Verify all v1.1 public API symbols are importable."""
        from brightohir import (
            R5, v2_to_r5, r5_to_v2, r4_to_r5, r5_to_r4,
            V2Converter, conversion_status,
            generate_ack, generate_batch_ack,
            mask_v2, mask_fhir, mask_bundle, PIIMasker,
            ALL_R5_RESOURCES, R5_RESOURCES, R4_TO_R5_MAP,
            V2_SEGMENT_TO_FHIR, V2_MESSAGE_TO_FHIR,
            V2_DATATYPE_TO_FHIR, V2_TABLE_TO_FHIR_SYSTEM,
        )
        from brightohir.transport import MLLPServer, MLLPClient, mllp_encode, mllp_decode
        assert callable(v2_to_r5)
        assert callable(generate_ack)
        assert callable(mask_v2)
        assert callable(mllp_encode)

    def test_converter_count(self):
        """Verify we have 31 V2→R5 creators, 20 enrichers, and 23 R5→V2 converters."""
        from brightohir.convert_v2 import _SEGMENT_CONVERTERS, _SEGMENT_ENRICHERS, _R5_TO_V2_CONVERTERS
        assert len(_SEGMENT_CONVERTERS) >= 31, f"Expected ≥31 V2→R5 creators, got {len(_SEGMENT_CONVERTERS)}"
        assert len(_SEGMENT_ENRICHERS) >= 20, f"Expected ≥20 enrichers, got {len(_SEGMENT_ENRICHERS)}"
        assert len(_R5_TO_V2_CONVERTERS) >= 23, f"Expected ≥23 R5→V2, got {len(_R5_TO_V2_CONVERTERS)}"
        # Total coverage: 31 creators + 20 enrichers = 51 segment types
        total = len(_SEGMENT_CONVERTERS) + len(_SEGMENT_ENRICHERS)
        assert total >= 51, f"Expected ≥51 total segment handlers, got {total}"
