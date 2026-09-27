"""
Tests for accent-insensitive, indexed Vietnamese code search.

Run: pytest tests/test_vn_search.py -v
"""
import pytest


@pytest.fixture(scope="module", autouse=True)
def _load():
    from brightohir.vn import VN
    VN.load_bundled()


class TestNormalize:
    def test_normalize_vietnamese(self):
        from brightohir.vn import _normalize_vn_text
        assert _normalize_vn_text("Đái tháo đường") == "dai thao duong"
        assert _normalize_vn_text("Nhiễm trùng hô hấp trên") == "nhiem trung ho hap tren"
        assert _normalize_vn_text("Paracetamol 500mg") == "paracetamol 500mg"
        assert _normalize_vn_text("Tăng huyết áp") == "tang huyet ap"


class TestAccentInsensitiveSearch:
    def test_no_accent_query_matches_accented_data(self):
        from brightohir.vn import VN
        results = VN.search("icd10", "dai thao duong")
        assert any(r["code"].startswith("E11") for r in results)

    def test_accented_query_still_works(self):
        from brightohir.vn import VN
        results = VN.search("icd10", "đái tháo đường")
        assert any(r["code"].startswith("E11") for r in results)

    def test_multi_token_no_accent(self):
        from brightohir.vn import VN
        results = VN.search("icd10", "nhiem trung ho hap")
        assert any(r["code"] == "J06.9" for r in results)

    def test_partial_word_substring_fallback(self):
        from brightohir.vn import VN
        results = VN.search("drug", "paracet")
        assert any("paracetamol" in r.get("display_vi", "").lower() for r in results)

    def test_token_index_is_populated(self):
        from brightohir.vn import VN
        cs = VN.system("icd10")
        assert len(cs._token_index) > 0

    def test_load_records_is_searchable(self):
        from brightohir.vn import _VNRegistry
        reg = _VNRegistry()
        reg.load_records("icd10", [
            {"code": "E11.9", "display_vi": "Đái tháo đường typ 2"},
            {"code": "J06.9", "display_vi": "Nhiễm trùng hô hấp trên"},
        ])
        results = reg.search("icd10", "dai thao")
        assert len(results) >= 1
        assert results[0]["code"] == "E11.9"
