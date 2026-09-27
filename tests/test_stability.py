"""
Tests for deterministic (idempotent) conversion and masking correctness fixes.

Run: pytest tests/test_stability.py -v
"""


ADT_A01 = (
    "MSH|^~\\&|A|B|C|D|20260322090000||ADT^A01|MSG001|P|2.5\r"
    "EVN||20260322090000\r"
    "PID|1||12345^^^LC^MR||DOE^JOHN||19850612|M\r"
    "PV1|1|I|W^101\r"
    "OBX|1|NM|29463-7^Body Weight^LN||72|kg|||||F\r"
)


def _resources(bundle):
    return {e["resource"]["resourceType"]: e["resource"] for e in bundle["entry"]}


# ═══════════════════════════════════════════════════════════════════════════════
# Deterministic / idempotent conversion
# ═══════════════════════════════════════════════════════════════════════════════

class TestDeterministicIDs:
    def test_same_message_same_ids(self):
        from brightohir import v2_to_r5
        b1 = v2_to_r5(ADT_A01, deterministic=True)
        b2 = v2_to_r5(ADT_A01, deterministic=True)
        r1 = _resources(b1)
        r2 = _resources(b2)
        assert r1["Patient"]["id"] == r2["Patient"]["id"]
        assert r1["Observation"]["id"] == r2["Observation"]["id"]

    def test_default_is_random(self):
        from brightohir import v2_to_r5
        b1 = v2_to_r5(ADT_A01)
        b2 = v2_to_r5(ADT_A01)
        assert _resources(b1)["Patient"]["id"] != _resources(b2)["Patient"]["id"]

    def test_references_rewritten_consistently(self):
        from brightohir import v2_to_r5
        b = v2_to_r5(ADT_A01, deterministic=True)
        r = _resources(b)
        assert r["Observation"]["subject"]["reference"] == f"Patient/{r['Patient']['id']}"
        assert r["Observation"]["encounter"]["reference"] == f"Encounter/{r['Encounter']['id']}"

    def test_different_patient_different_id(self):
        from brightohir import v2_to_r5
        msg_a = ADT_A01.replace("12345^^^LC^MR", "AAAA^^^LC^MR")
        msg_b = ADT_A01.replace("12345^^^LC^MR", "BBBB^^^LC^MR")
        id_a = _resources(v2_to_r5(msg_a, deterministic=True))["Patient"]["id"]
        id_b = _resources(v2_to_r5(msg_b, deterministic=True))["Patient"]["id"]
        assert id_a != id_b

    def test_instance_level_flag(self):
        from brightohir import V2Converter
        conv = V2Converter(deterministic=True)
        conv.convert(ADT_A01)
        id_a = conv.extract_resource("Patient")["id"]
        conv.convert(ADT_A01)
        id_b = conv.extract_resource("Patient")["id"]
        assert id_a == id_b

    def test_per_call_override(self):
        from brightohir import V2Converter
        conv = V2Converter()  # default: random
        conv.convert(ADT_A01, deterministic=True)
        id_a = conv.extract_resource("Patient")["id"]
        conv.convert(ADT_A01, deterministic=True)
        id_b = conv.extract_resource("Patient")["id"]
        assert id_a == id_b

    def test_deterministic_ids_are_stable_hash_format(self):
        from brightohir import v2_to_r5
        pid = _resources(v2_to_r5(ADT_A01, deterministic=True))["Patient"]["id"]
        assert len(pid) == 16
        assert all(c in "0123456789abcdef" for c in pid)


# ═══════════════════════════════════════════════════════════════════════════════
# Masking correctness fixes
# ═══════════════════════════════════════════════════════════════════════════════

class TestMaskingCorrectness:
    def test_redact_preserves_booleans_and_integers(self):
        """deceasedBoolean / multipleBirthInteger must stay typed, not become strings."""
        from brightohir.security import PIIMasker
        masker = PIIMasker(strategy="redact")
        out = masker.mask_fhir({
            "resourceType": "Patient",
            "deceasedBoolean": True,
            "multipleBirthBoolean": False,
            "multipleBirthInteger": 2,
        })
        assert out["deceasedBoolean"] is True
        assert out["multipleBirthBoolean"] is False
        assert out["multipleBirthInteger"] == 2

    def test_pseudonym_phone_format(self):
        """Phone values should pseudonymize as phone-shaped, not generic MASKED_."""
        from brightohir.security import PIIMasker
        masker = PIIMasker(strategy="pseudonym")
        out = masker.mask_fhir({
            "resourceType": "Patient",
            "telecom": [{"system": "phone", "value": "0901234567", "use": "home"}],
        })
        value = out["telecom"][0]["value"]
        assert value.startswith("000-")
        assert "MASKED_" not in value

    def test_email_pseudonym(self):
        from brightohir.security import PIIMasker
        masker = PIIMasker(strategy="pseudonym")
        out = masker.mask_fhir({
            "resourceType": "Patient",
            "telecom": [{"system": "email", "value": "jane@example.com"}],
        })
        # Email value is masked (not leaked), and structure preserved
        assert "jane@example.com" not in out["telecom"][0]["value"]
        assert out["telecom"][0]["system"] == "email"
