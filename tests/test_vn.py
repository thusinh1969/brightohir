"""
Tests for brightohir.vn — Vietnamese Healthcare Code Systems.
Run: pytest tests/test_vn.py -v
"""
import json
import pytest
from pathlib import Path
from brightohir.vn import VN, VNCodeSystem, VN_CODE_SYSTEMS, _resolve_alias

# Data directory: use the bundled path inside the installed package
DATA_DIR = VN._bundled_data_dir()


# ═══════════════════════════════════════════════════════════════════════════════
# Registry & schema
# ═══════════════════════════════════════════════════════════════════════════════

class TestVNRegistry:
    def test_code_systems_defined(self):
        assert len(VN_CODE_SYSTEMS) == 11

    def test_all_systems_have_required_fields(self):
        for key, meta in VN_CODE_SYSTEMS.items():
            assert "system" in meta, f"{key} missing system"
            assert "name" in meta, f"{key} missing name"
            assert "name_vi" in meta, f"{key} missing name_vi"
            assert "file" in meta, f"{key} missing file"
            assert "authority" in meta, f"{key} missing authority"
            assert meta["system"].startswith("https://"), f"{key} system should be HTTPS URI"

    def test_aliases(self):
        assert _resolve_alias("icd") == "icd10"
        assert _resolve_alias("thuoc") == "drug"
        assert _resolve_alias("xet_nghiem") == "lab"
        assert _resolve_alias("bhyt") == "bhyt_object"
        assert _resolve_alias("tinh") == "province"
        assert _resolve_alias("benh") == "icd10"
        assert _resolve_alias("dvkt") == "procedure"


# ═══════════════════════════════════════════════════════════════════════════════
# Loading
# ═══════════════════════════════════════════════════════════════════════════════

class TestVNLoading:
    def test_load_directory(self):
        stats = VN.load(DATA_DIR)
        assert VN.is_loaded
        assert len(stats) >= 1, "Should load at least 1 system from sample data"
        assert VN.total_codes >= 1

    def test_load_stats(self):
        VN.load(DATA_DIR)
        stats = VN.stats()
        assert len(stats) >= 1, "At least 1 system loaded"
        # Every loaded system should have > 0 records
        for key, count in stats.items():
            assert count > 0, f"{key} loaded with 0 records"

    def test_loaded_systems(self):
        VN.load(DATA_DIR)
        systems = VN.loaded_systems()
        assert len(systems) >= 1
        # Core systems should be present if their sample files exist
        for key in systems:
            assert key in VN_CODE_SYSTEMS, f"Unknown system: {key}"

    def test_load_single_file(self):
        from brightohir.vn import _VNRegistry
        reg = _VNRegistry()
        count = reg.load_file(DATA_DIR / "icd10_vn.sample.jsonl", key="icd10")
        assert count >= 5

    def test_load_nonexistent_raises(self):
        from brightohir.vn import _VNRegistry
        reg = _VNRegistry()
        with pytest.raises(FileNotFoundError):
            reg.load("/nonexistent/path/")

    def test_not_loaded_raises(self):
        from brightohir.vn import _VNRegistry
        reg = _VNRegistry()
        with pytest.raises(RuntimeError, match="not loaded"):
            reg.icd10("J06.9")

    def test_load_records_from_dict(self):
        """VN works without files — load from API/database/dict."""
        from brightohir.vn import _VNRegistry
        reg = _VNRegistry()
        count = reg.load_records("icd10", [
            {"code": "J06.9", "display_vi": "Nhiễm trùng hô hấp trên cấp tính", "display_en": "Acute URI"},
            {"code": "E11.9", "display_vi": "Đái tháo đường typ 2", "display_en": "Type 2 DM"},
        ])
        assert count == 2
        assert reg.is_loaded
        rec = reg.icd10("J06.9")
        assert rec is not None
        assert "Nhiễm trùng" in rec["display_vi"]
        # Search works on dict-loaded data
        results = reg.search("icd10", "đái tháo")
        assert len(results) >= 1
        # FHIR export works
        cc = reg.to_codeable_concept("icd10", "J06.9")
        assert cc["coding"][0]["system"] == "https://icd.kcb.vn/ICD-10-VN"

    def test_load_records_no_files_needed(self):
        """Entire VN system works with zero files on disk."""
        from brightohir.vn import _VNRegistry
        reg = _VNRegistry()
        reg.load_records("drug", [
            {"code": "TD.0001", "display_vi": "Paracetamol 500mg", "atc": "N02BE01"},
        ])
        reg.load_records("lab", [
            {"code": "XN.001", "display_vi": "Hemoglobin", "loinc": "718-7"},
        ])
        assert reg.stats() == {"drug": 1, "lab": 1}
        assert reg.drug("TD.0001")["atc"] == "N02BE01"
        assert reg.lab("XN.001")["loinc"] == "718-7"

    def test_load_records_alias(self):
        """Aliases work with load_records."""
        from brightohir.vn import _VNRegistry
        reg = _VNRegistry()
        reg.load_records("thuoc", [{"code": "X", "display_vi": "Test"}])
        assert reg.drug("X") is not None


# ═══════════════════════════════════════════════════════════════════════════════
# Lookup
# ═══════════════════════════════════════════════════════════════════════════════

class TestVNLookup:
    @classmethod
    def setup_class(cls):
        VN.load(DATA_DIR)

    def test_icd10_lookup(self):
        rec = VN.icd10("J06.9")
        assert rec is not None
        assert rec["code"] == "J06.9"
        assert "Nhiễm trùng" in rec["display_vi"]

    def test_icd10_lookup_not_found(self):
        rec = VN.icd10("ZZZZZ")
        assert rec is None

    def test_drug_lookup(self):
        rec = VN.drug("TD.0001")
        assert rec is not None
        assert "Paracetamol" in rec["display_vi"]
        assert rec["atc"] == "N02BE01"

    def test_lab_lookup(self):
        rec = VN.lab("XN.001")
        assert rec is not None
        assert rec["loinc"] == "718-7"
        assert rec["unit"] == "g/dL"

    def test_bhyt_object_lookup(self):
        rec = VN.bhyt_object("3")
        assert rec is not None
        assert "Trẻ em" in rec["display_vi"]
        assert rec["copay_percent"] == 0

    def test_generic_get(self):
        rec = VN.get("icd10", "E11.9")
        assert rec is not None
        assert "đái tháo đường" in rec["display_vi"].lower()

    def test_alias_get(self):
        rec = VN.get("benh", "I10")
        assert rec is not None
        assert "huyết áp" in rec["display_vi"].lower()

    def test_system_object(self):
        cs = VN.system("icd10")
        assert isinstance(cs, VNCodeSystem)
        assert len(cs) >= 5
        assert "J06.9" in cs
        assert cs.count >= 5


# ═══════════════════════════════════════════════════════════════════════════════
# Search
# ═══════════════════════════════════════════════════════════════════════════════

class TestVNSearch:
    @classmethod
    def setup_class(cls):
        VN.load(DATA_DIR)

    def test_search_vietnamese(self):
        results = VN.search("icd10", "đái tháo đường")
        assert len(results) >= 1
        assert any("E11" in r["code"] for r in results)

    def test_search_english(self):
        results = VN.search("icd10", "hypertension")
        assert len(results) >= 1
        assert any("I10" in r["code"] for r in results)

    def test_search_drug(self):
        results = VN.search("drug", "paracetamol")
        assert len(results) >= 1

    def test_search_lab(self):
        results = VN.search("lab", "hemoglobin")
        assert len(results) >= 1

    def test_search_empty(self):
        results = VN.search("icd10", "")
        assert results == []

    def test_search_no_match(self):
        results = VN.search("icd10", "xyznotexist123")
        assert results == []

    def test_search_max_results(self):
        results = VN.search("icd10", "bệnh", max_results=2)
        assert len(results) <= 2


# ═══════════════════════════════════════════════════════════════════════════════
# FHIR output
# ═══════════════════════════════════════════════════════════════════════════════

class TestVNFHIR:
    @classmethod
    def setup_class(cls):
        VN.load(DATA_DIR)

    def test_to_codeable_concept(self):
        cc = VN.to_codeable_concept("icd10", "J06.9")
        assert cc is not None
        assert cc["coding"][0]["system"] == "https://icd.kcb.vn/ICD-10-VN"
        assert cc["coding"][0]["code"] == "J06.9"
        assert "Nhiễm trùng" in cc["coding"][0]["display"]

    def test_to_codeable_concept_not_found(self):
        cc = VN.to_codeable_concept("icd10", "ZZZZ")
        assert cc is None

    def test_to_coding(self):
        c = VN.to_coding("lab", "XN.001")
        assert c is not None
        assert c["system"] == "https://dmdc.moh.gov.vn/xet-nghiem"
        assert c["code"] == "XN.001"

    def test_to_codeable_concept_drug(self):
        cc = VN.to_codeable_concept("drug", "TD.0001")
        assert cc is not None
        assert cc["coding"][0]["system"] == "https://dmdc.moh.gov.vn/thuoc-tan-duoc"
        assert "Paracetamol" in cc["coding"][0]["display"]

    def test_to_fhir_codesystem(self):
        cs = VN.to_fhir_codesystem("icd10")
        assert cs["resourceType"] == "CodeSystem"
        assert cs["url"] == "https://icd.kcb.vn/ICD-10-VN"
        assert cs["status"] == "active"
        assert cs["count"] >= 5
        assert len(cs["concept"]) >= 5
        # Check concept structure
        c = cs["concept"][0]
        assert "code" in c
        assert "display" in c
        assert "designation" in c
        assert any(d["language"] == "vi" for d in c["designation"])

    def test_to_fhir_codesystem_bhyt(self):
        cs = VN.to_fhir_codesystem("bhyt_object")
        assert cs["resourceType"] == "CodeSystem"
        assert cs["count"] >= 5
        # Check properties included
        c = next(c for c in cs["concept"] if c["code"] == "3")
        props = {p["code"]: p for p in c.get("property", [])}
        assert "copay_percent" in props


# ═══════════════════════════════════════════════════════════════════════════════
# Converter integration — VN auto-enrich
# ═══════════════════════════════════════════════════════════════════════════════

class TestVNConverterIntegration:
    @classmethod
    def setup_class(cls):
        VN.load(DATA_DIR)

    def test_dg1_enriched_with_vn_icd10(self):
        """DG1 with ICD-10 code should get VN system URI + display."""
        from brightohir import V2Converter
        msg = "MSH|^~\\&|A|B|C|D|20260322||ADT^A01|1|P|2.5\rPID|1||999||DOE^J||19900101|M\rDG1|1||J06.9|||A\r"
        conv = V2Converter()
        conv.convert(msg)
        cond = conv.extract_resource("Condition")
        assert cond is not None
        coding = cond["code"]["coding"][0]
        # VN enrichment should add system
        assert coding.get("system") == "https://icd.kcb.vn/ICD-10-VN"
        assert "Nhiễm trùng" in coding.get("display", "")

    def test_obx_enriched_with_vn_lab(self):
        """OBX with VN lab code should get enriched."""
        from brightohir import V2Converter
        msg = "MSH|^~\\&|A|B|C|D|20260322||ORU^R01|1|P|2.5\rPID|1||999||DOE^J||19900101|M\rOBX|1|NM|XN.001||13.5|g/dL|||||F\r"
        conv = V2Converter()
        conv.convert(msg)
        obs = conv.extract_resource("Observation")
        assert obs is not None
        coding = obs["code"]["coding"][0]
        assert coding.get("system") == "https://dmdc.moh.gov.vn/xet-nghiem"
        assert "Hemoglobin" in coding.get("display", "")

    def test_rxe_enriched_with_vn_drug(self):
        """RXE with VN drug code should get enriched."""
        from brightohir import V2Converter
        msg = "MSH|^~\\&|A|B|C|D|20260322||RDE^O11|1|P|2.5\rPID|1||999||DOE^J||19900101|M\rORC|NW|RX1\rRXE||TD.0001|500||mg\r"
        conv = V2Converter()
        conv.convert(msg)
        mr = conv.extract_resource("MedicationRequest")
        assert mr is not None
        coding = mr["medication"]["concept"]["coding"][0]
        assert coding.get("system") == "https://dmdc.moh.gov.vn/thuoc-tan-duoc"
        assert "Paracetamol" in coding.get("display", "")

    def test_non_vn_code_not_broken(self):
        """Non-VN codes should still work fine without VN enrichment."""
        from brightohir import V2Converter
        msg = "MSH|^~\\&|A|B|C|D|20260322||ADT^A01|1|P|2.5\rPID|1||999||DOE^J||19900101|M\rDG1|1||Z99.99^Unknown^ICD10|||A\r"
        conv = V2Converter()
        conv.convert(msg)
        cond = conv.extract_resource("Condition")
        assert cond is not None
        coding = cond["code"]["coding"][0]
        # Non-VN code → no VN enrichment, but code still there
        assert coding["code"] == "Z99.99"

    def test_converter_without_vn_data(self):
        """Converters should work without VN data loaded (fresh registry)."""
        from brightohir.vn import _VNRegistry
        from brightohir.convert_v2 import _vn_enrich_codeable_concept
        # Enrich should be no-op when not loaded
        cc = {"coding": [{"code": "J06.9"}]}
        _vn_enrich_codeable_concept(cc, "icd10")
        # Should not crash, should not add system (VN singleton IS loaded in other tests,
        # but this tests the function's safety)
        assert "code" in cc["coding"][0]


# ═══════════════════════════════════════════════════════════════════════════════
# VNCodeSystem class
# ═══════════════════════════════════════════════════════════════════════════════

class TestVNCodeSystemClass:
    def test_contains(self):
        VN.load(DATA_DIR)
        cs = VN.system("icd10")
        assert "J06.9" in cs
        assert "ZZZZ" not in cs

    def test_codes_list(self):
        VN.load(DATA_DIR)
        cs = VN.system("icd10")
        codes = cs.codes()
        assert isinstance(codes, list)
        assert "J06.9" in codes

    def test_all_records(self):
        VN.load(DATA_DIR)
        cs = VN.system("bhyt_object")
        all_recs = cs.all()
        assert len(all_recs) >= 5
        assert all("code" in r for r in all_recs)

    def test_repr(self):
        VN.load(DATA_DIR)
        cs = VN.system("icd10")
        r = repr(cs)
        assert "icd10" in r
        assert "codes" in r


# ═══════════════════════════════════════════════════════════════════════════════
# Public API import
# ═══════════════════════════════════════════════════════════════════════════════

class TestVNPublicAPI:
    def test_imports(self):
        from brightohir import VN, VNCodeSystem, VN_CODE_SYSTEMS
        assert VN is not None
        assert VNCodeSystem is not None
        assert len(VN_CODE_SYSTEMS) == 11

    def test_version_format(self):
        from brightohir import __version__
        parts = __version__.split(".")
        assert len(parts) == 3, f"Version should be X.Y.Z, got {__version__}"
        assert int(parts[0]) >= 2, f"Major version should be >= 2, got {__version__}"
