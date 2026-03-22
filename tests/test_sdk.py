"""
Tests for brightohir SDK.
Run: pytest tests/ -v
"""

import json
import uuid

import pytest


# ═══════════════════════════════════════════════════════════════════════════════
# Registry tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestRegistry:
    def test_r5_resource_count(self):
        from brightohir.registry import ALL_R5_RESOURCES
        # FHIR R5 spec defines 157 resources
        assert len(ALL_R5_RESOURCES) >= 150, f"Expected ≥150 R5 resources, got {len(ALL_R5_RESOURCES)}"

    def test_r5_key_resources_present(self):
        from brightohir.registry import ALL_R5_RESOURCES
        for rt in ["Patient", "Encounter", "Observation", "MedicationRequest",
                    "AllergyIntolerance", "Immunization", "Coverage", "Bundle",
                    "DiagnosticReport", "Condition", "Procedure", "Specimen"]:
            assert rt in ALL_R5_RESOURCES, f"{rt} missing from R5 resources"

    def test_v2_segment_mappings_populated(self):
        from brightohir.registry import V2_SEGMENT_TO_FHIR
        assert len(V2_SEGMENT_TO_FHIR) >= 35, f"Expected ≥35 segment mappings, got {len(V2_SEGMENT_TO_FHIR)}"
        assert "PID" in V2_SEGMENT_TO_FHIR
        assert "OBX" in V2_SEGMENT_TO_FHIR
        assert "MSH" in V2_SEGMENT_TO_FHIR

    def test_v2_message_mappings_populated(self):
        from brightohir.registry import V2_MESSAGE_TO_FHIR
        assert len(V2_MESSAGE_TO_FHIR) >= 15
        assert "ADT_A01" in V2_MESSAGE_TO_FHIR
        assert "ORU_R01" in V2_MESSAGE_TO_FHIR
        assert "VXU_V04" in V2_MESSAGE_TO_FHIR

    def test_v2_datatype_mappings_populated(self):
        from brightohir.registry import V2_DATATYPE_TO_FHIR
        assert "CWE" in V2_DATATYPE_TO_FHIR
        assert "CodeableConcept" in V2_DATATYPE_TO_FHIR["CWE"]
        assert "XPN" in V2_DATATYPE_TO_FHIR
        assert "HumanName" in V2_DATATYPE_TO_FHIR["XPN"]

    def test_r4_to_r5_map(self):
        from brightohir.registry import R4_TO_R5_MAP
        assert "Encounter" in R4_TO_R5_MAP
        assert R4_TO_R5_MAP["Encounter"]["status"] == "restructured"
        assert "RequestOrchestration" in R4_TO_R5_MAP
        assert R4_TO_R5_MAP["RequestOrchestration"]["r4"] == "RequestGroup"

    def test_vocabulary_mapping(self):
        from brightohir.registry import V2_TABLE_TO_FHIR_SYSTEM
        assert "HL70001" in V2_TABLE_TO_FHIR_SYSTEM  # Admin Sex
        assert "HL70085" in V2_TABLE_TO_FHIR_SYSTEM  # Obs Result Status


# ═══════════════════════════════════════════════════════════════════════════════
# R5 Resource Factory tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestR5Factory:
    def test_create_patient(self):
        from brightohir.r5 import R5
        pat = R5.create("Patient", id="test-001", active=True,
                        name=[{"family": "Nguyen", "given": ["Van A"]}],
                        gender="male", birthDate="1990-01-15")
        assert pat.id == "test-001"
        assert pat.active is True
        assert pat.name[0].family == "Nguyen"
        assert pat.gender == "male"

    def test_create_observation(self):
        from brightohir.r5 import R5
        obs = R5.create("Observation", id="obs-001", status="final",
                        code={"coding": [{"system": "http://loinc.org", "code": "29463-7"}]})
        assert obs.status == "final"

    def test_to_json_roundtrip(self):
        from brightohir.r5 import R5
        pat = R5.create("Patient", id="rt-001", active=True)
        json_str = R5.to_json(pat)
        pat2 = R5.from_json("Patient", json_str)
        assert pat2.id == "rt-001"
        assert pat2.active is True

    def test_to_dict(self):
        from brightohir.r5 import R5
        pat = R5.create("Patient", id="dict-001", active=True)
        d = R5.to_dict(pat)
        assert d["resourceType"] == "Patient"
        assert d["id"] == "dict-001"

    def test_bundle_creation(self):
        from brightohir.r5 import R5
        pat = R5.create("Patient", id="b-001", active=True)
        obs = R5.create("Observation", id="b-002", status="final",
                        code={"coding": [{"code": "test"}]})
        bundle = R5.bundle("transaction", [pat, obs])
        d = R5.to_dict(bundle)
        assert d["type"] == "transaction"
        assert len(d["entry"]) == 2
        assert d["entry"][0]["request"]["method"] == "POST"

    def test_validate_valid_data(self):
        from brightohir.r5 import R5
        errors = R5.validate("Patient", {"active": True})
        assert errors == []

    def test_validate_invalid_data(self):
        from brightohir.r5 import R5
        errors = R5.validate("Observation", {"status": "INVALID"})
        assert len(errors) > 0

    def test_unknown_resource_raises(self):
        from brightohir.r5 import R5
        with pytest.raises(ValueError, match="Unknown R5 resource"):
            R5.create("FakeResource")

    def test_list_resources(self):
        from brightohir.r5 import R5
        all_res = R5.list_resources()
        assert len(all_res) >= 150
        meds = R5.list_resources("medications")
        assert "MedicationRequest" in meds
        assert "Immunization" in meds


# ═══════════════════════════════════════════════════════════════════════════════
# R4 ↔ R5 Conversion tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestR4R5Conversion:
    def test_encounter_r4_to_r5(self):
        from brightohir.convert_r4r5 import r4_to_r5
        r4 = {
            "resourceType": "Encounter",
            "id": "enc-001",
            "status": "in-progress",
            "class": {"system": "http://terminology.hl7.org/CodeSystem/v3-ActCode", "code": "AMB"},
            "hospitalization": {"dischargeDisposition": {"text": "home"}},
            "classHistory": [{"class": {"code": "IMP"}}],
        }
        r5 = r4_to_r5(r4)
        assert r5["resourceType"] == "Encounter"
        # class should be CodeableConcept[] now
        assert isinstance(r5["class"], list)
        # hospitalization → admission
        assert "admission" in r5
        assert "hospitalization" not in r5
        # classHistory removed
        assert "classHistory" not in r5

    def test_encounter_r5_to_r4(self):
        from brightohir.convert_r4r5 import r5_to_r4
        r5 = {
            "resourceType": "Encounter",
            "id": "enc-002",
            "status": "completed",
            "class": [{"coding": [{"code": "AMB"}]}],
            "admission": {"dischargeDisposition": {"text": "home"}},
        }
        r4 = r5_to_r4(r5)
        assert r4["class"]["code"] == "AMB"
        assert "hospitalization" in r4

    def test_medication_request_r4_to_r5(self):
        from brightohir.convert_r4r5 import r4_to_r5
        r4 = {
            "resourceType": "MedicationRequest",
            "id": "mr-001",
            "status": "active",
            "intent": "order",
            "medicationCodeableConcept": {"coding": [{"code": "12345"}]},
            "reportedReference": {"reference": "Patient/p001"},
        }
        r5 = r4_to_r5(r4)
        assert "medication" in r5
        assert "concept" in r5["medication"]
        assert "medicationCodeableConcept" not in r5
        assert "informationSource" in r5

    def test_medication_request_r5_to_r4(self):
        from brightohir.convert_r4r5 import r5_to_r4
        r5 = {
            "resourceType": "MedicationRequest",
            "id": "mr-002",
            "status": "active",
            "intent": "order",
            "medication": {"concept": {"coding": [{"code": "67890"}]}},
            "informationSource": [{"reference": "Patient/p001"}],
        }
        r4 = r5_to_r4(r5)
        assert "medicationCodeableConcept" in r4
        assert "medication" not in r4
        assert "reportedReference" in r4

    def test_condition_r4_to_r5_participant(self):
        from brightohir.convert_r4r5 import r4_to_r5
        r4 = {
            "resourceType": "Condition",
            "id": "cond-001",
            "recorder": {"reference": "Practitioner/dr1"},
            "asserter": {"reference": "Patient/p1"},
        }
        r5 = r4_to_r5(r4)
        assert "participant" in r5
        assert len(r5["participant"]) == 2
        assert "recorder" not in r5

    def test_new_r5_resource_cannot_downgrade(self):
        from brightohir.convert_r4r5 import r5_to_r4
        with pytest.raises(ValueError, match="new in R5"):
            r5_to_r4({"resourceType": "ActorDefinition", "id": "ad-001"})

    def test_renamed_resource(self):
        from brightohir.convert_r4r5 import r4_to_r5, conversion_status
        info = conversion_status("RequestOrchestration")
        assert info["r4"] == "RequestGroup"
        assert info["status"] == "renamed"

    def test_compatible_resource_passthrough(self):
        from brightohir.convert_r4r5 import r4_to_r5
        r4 = {"resourceType": "Patient", "id": "p-001", "active": True}
        r5 = r4_to_r5(r4)
        assert r5["resourceType"] == "Patient"
        assert r5["active"] is True

    def test_document_reference_r4_to_r5(self):
        from brightohir.convert_r4r5 import r4_to_r5
        r4 = {
            "resourceType": "DocumentReference",
            "id": "dr-001",
            "masterIdentifier": {"system": "urn:oid:1.2.3", "value": "doc-123"},
            "context": {
                "encounter": [{"reference": "Encounter/e1"}],
                "period": {"start": "2025-01-01"},
                "facilityType": {"text": "Hospital"},
            },
        }
        r5 = r4_to_r5(r4)
        assert "masterIdentifier" not in r5
        assert r5["identifier"][0]["use"] == "official"
        assert "period" in r5
        assert "facilityType" in r5


# ═══════════════════════════════════════════════════════════════════════════════
# V2 ↔ R5 Conversion tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestV2Conversion:
    ADT_A01 = (
        "MSH|^~\\&|HATTO|LC_PHARMACY|EHR|HOSPITAL|20260322090000||ADT^A01^ADT_A01|MSG001|P|2.5.1\r"
        "EVN||20260322090000\r"
        "PID|1||12345^^^LC^MR||NGUYEN^VAN A^B||19900115|M||2028-9|123 NGUYEN HUE^^HCM^VN^70000||0901234567|||M\r"
        "PV1|1|I|W^101^1^^^3||||12345^TRAN^BAC SI|||MED|||||A0\r"
        "AL1|1|DA|12345^ASPIRIN^RxNorm|SV|Rash\r"
        "DG1|1||J06.9^URTI^ICD10|||A\r"
        "OBX|1|NM|29463-7^Body Weight^LN||72|kg|||||F\r"
    )

    def test_v2_to_r5_produces_bundle(self):
        from brightohir.convert_v2 import v2_to_r5
        bundle = v2_to_r5(self.ADT_A01)
        assert bundle["resourceType"] == "Bundle"
        assert bundle["type"] == "message"
        assert len(bundle["entry"]) > 0

    def test_v2_converter_extract_patient(self):
        from brightohir.convert_v2 import V2Converter
        conv = V2Converter()
        conv.convert(self.ADT_A01)
        patient = conv.extract_resource("Patient")
        assert patient is not None
        assert patient["resourceType"] == "Patient"

    def test_v2_converter_extract_observation(self):
        from brightohir.convert_v2 import V2Converter
        conv = V2Converter()
        conv.convert(self.ADT_A01)
        obs = conv.extract_resource("Observation")
        assert obs is not None
        assert obs["status"] == "final"

    def test_v2_converter_cross_references(self):
        from brightohir.convert_v2 import V2Converter
        conv = V2Converter()
        conv.convert(self.ADT_A01)
        obs = conv.extract_resource("Observation")
        if obs:
            assert "subject" in obs
            assert obs["subject"]["reference"].startswith("Patient/")

    def test_r5_to_v2(self):
        from brightohir.convert_v2 import r5_to_v2
        patient = {
            "resourceType": "Patient",
            "id": "p-001",
            "name": [{"family": "Nguyen", "given": ["Van A"]}],
            "gender": "male",
            "birthDate": "1990-01-15",
            "address": [{"line": ["123 Main St"], "city": "HCM", "country": "VN"}],
        }
        v2 = r5_to_v2(patient, message_type="ADT_A01")
        assert "MSH|" in v2
        assert "PID|" in v2
        assert "NGUYEN" in v2.upper() or "Nguyen" in v2
        assert "ADT^A01" in v2

    def test_r5_bundle_to_v2(self):
        from brightohir.convert_v2 import r5_to_v2
        bundle = {
            "resourceType": "Bundle",
            "type": "message",
            "entry": [
                {"resource": {"resourceType": "Patient", "id": "p1", "name": [{"family": "Test"}], "gender": "male"}},
                {"resource": {"resourceType": "Encounter", "id": "e1", "status": "in-progress",
                              "class": [{"coding": [{"code": "IMP"}]}]}},
            ],
        }
        v2 = r5_to_v2(bundle, message_type="ADT_A01")
        assert "MSH|" in v2
        assert "PID|" in v2
        assert "PV1|" in v2

    def test_manual_fallback_parser(self):
        """Test the manual parser works without hl7apy."""
        from brightohir.convert_v2 import V2Converter
        conv = V2Converter()
        # Call the manual parse directly
        bundle = conv._convert_manual(self.ADT_A01, "ADT_A01")
        assert bundle["resourceType"] == "Bundle"
        # Should at least get MessageHeader + Patient
        resource_types = [e["resource"]["resourceType"] for e in bundle["entry"]]
        assert "MessageHeader" in resource_types
        assert "Patient" in resource_types

    def test_newline_delimited_message(self):
        """Bug fix: triple-quoted strings use \\n not \\r — must still parse."""
        from brightohir.convert_v2 import v2_to_r5
        # This is EXACTLY how users paste in Jupyter — \n line endings
        msg = """MSH|^~\\&|HATTO|LC_PHARMACY|EHR|HOSPITAL|20260322090000||ADT^A01^ADT_A01|MSG001|P|2.5.1
PID|1||12345^^^LC^MR||NGUYEN^VAN A||19900115|M|||123 NGUYEN HUE^^HCM^VN^70000
PV1|1|I|W^101^1|||12345^TRAN^BAC SI|||MED
AL1|1|DA|ASPIRIN|SV|Rash
DG1|1||J06.9^URTI^ICD10|||A
OBX|1|NM|29463-7^Body Weight^LN||72|kg|||||F"""
        bundle = v2_to_r5(msg)
        assert bundle["resourceType"] == "Bundle"
        assert len(bundle["entry"]) >= 3  # At least MSH + PID + PV1

    def test_unsupported_version_fallback(self):
        """Gracefully handle V2 versions not in hl7apy."""
        from brightohir.convert_v2 import v2_to_r5
        msg = "MSH|^~\\&|A|B|C|D|20260322||ADT^A01^ADT_A01|1|P|2.9\rPID|1||999||DOE^JOHN||19850612|M\r"
        bundle = v2_to_r5(msg)
        assert bundle["resourceType"] == "Bundle"


# ═══════════════════════════════════════════════════════════════════════════════
# Integration tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestIntegration:
    def test_full_pipeline_v2_to_r5_validated(self):
        """V2 → R5 → validate → JSON → back."""
        from brightohir import R5, v2_to_r5

        msg = (
            "MSH|^~\\&|APP|FAC|REC|FAC|20260322||ADT^A01^ADT_A01|1|P|2.5\r"
            "PID|1||999^^^TEST^MR||DOE^JOHN||19850612|M\r"
        )
        bundle = v2_to_r5(msg)
        # Extract patient dict, validate as R5
        for entry in bundle["entry"]:
            res = entry["resource"]
            if res["resourceType"] == "Patient":
                errors = R5.validate("Patient", res)
                assert errors == [], f"Validation errors: {errors}"
                # Roundtrip JSON
                pat = R5.from_dict("Patient", res)
                json_str = R5.to_json(pat)
                assert "DOE" in json_str or "Doe" in json_str

    def test_full_pipeline_r4_to_r5_to_v2(self):
        """R4 → R5 → V2."""
        from brightohir import r4_to_r5, r5_to_v2

        r4_patient = {
            "resourceType": "Patient",
            "id": "pipe-001",
            "active": True,
            "name": [{"family": "Tran", "given": ["Minh"]}],
            "gender": "female",
            "birthDate": "1995-03-20",
        }
        r5 = r4_to_r5(r4_patient)
        assert r5["resourceType"] == "Patient"
        v2 = r5_to_v2(r5)
        assert "TRAN" in v2.upper() or "Tran" in v2
        assert "MSH|" in v2

    def test_public_api_imports(self):
        """Verify all public API symbols are importable."""
        from brightohir import (
            R5, v2_to_r5, r5_to_v2, r4_to_r5, r5_to_r4,
            V2Converter, conversion_status,
            ALL_R5_RESOURCES, R5_RESOURCES, R4_TO_R5_MAP,
            V2_SEGMENT_TO_FHIR, V2_MESSAGE_TO_FHIR,
            V2_DATATYPE_TO_FHIR, V2_TABLE_TO_FHIR_SYSTEM,
        )
        assert R5 is not None
        assert callable(v2_to_r5)
        assert callable(r5_to_v2)
        assert callable(r4_to_r5)
        assert callable(r5_to_r4)
