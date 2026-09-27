"""
Tests for the Z-segment extension framework and YAML/JSON mapping loader.

Run: pytest tests/test_custom.py -v
"""
import json

import pytest


def _msg(extra_segment):
    return (
        "MSH|^~\\&|A|B|C|D|20260322||ADT^A01|1|P|2.5\r"
        "PID|1||999||DOE^JOHN||19900101|M\r"
        + extra_segment + "\r"
    )


class TestZSegmentCapture:
    def test_unregistered_z_segment_is_captured(self):
        from brightohir import V2Converter
        conv = V2Converter()
        conv.convert(_msg("ZXX|1|hello^world"))
        assert len(conv.z_segments) == 1
        assert conv.z_segments[0]["name"] == "ZXX"
        assert conv.z_segments[0]["raw"].startswith("ZXX|")

    def test_z_segments_cleared_between_conversions(self):
        from brightohir import V2Converter
        conv = V2Converter()
        conv.convert(_msg("ZXX|1|hello"))
        assert len(conv.z_segments) == 1
        conv.convert(_msg("PID|1||999\r"))  # no Z-segment
        assert conv.z_segments == []


class TestProgrammaticRegistration:
    def test_register_segment(self):
        from brightohir import V2Converter

        def zal_converter(segment):
            from brightohir.convert_v2 import _field_str, _get_field_value
            return {
                "resourceType": "Observation",
                "id": "custom-1",
                "status": "final",
                "valueString": _field_str(_get_field_value(segment, 2)),
            }

        V2Converter.register_segment("ZOB", "Observation", zal_converter)
        conv = V2Converter()
        conv.convert(_msg("ZOB|1|some value"))
        obs = conv.extract_resource("Observation")
        assert obs is not None
        assert obs["valueString"] == "some value"
        assert obs["status"] == "final"

    def test_register_enricher(self):
        from brightohir import V2Converter

        def zen_enricher(segment, resources):
            patients = resources.get("Patient", [])
            if patients:
                patients[-1].setdefault("extension", []).append(
                    {"url": "http://example.org/zen", "valueString": "enriched"}
                )

        V2Converter.register_enricher("ZEN", zen_enricher)
        conv = V2Converter()
        conv.convert(_msg("ZEN|1|anything"))
        patient = conv.extract_resource("Patient")
        assert patient is not None
        assert any(e["url"] == "http://example.org/zen" for e in patient.get("extension", []))


class TestDeclarativeMapping:
    YAML_MAPPING = """
version: 1
segments:
  ZAL:
    resource: AllergyIntolerance
    defaults:
      clinicalStatus:
        coding:
          - system: "http://terminology.hl7.org/CodeSystem/allergyintolerance-clinical"
            code: active
    fields:
      - source: 2
        target: code
        datatype: CWE
      - source: 3
        target: onsetDateTime
        datatype: TS
"""

    def test_load_yaml_mapping(self, tmp_path):
        from brightohir import V2Converter
        from brightohir.custom import load_custom_mappings

        path = tmp_path / "zsegments.yaml"
        path.write_text(self.YAML_MAPPING, encoding="utf-8")
        registered = load_custom_mappings(path)
        assert "ZAL" in registered

        conv = V2Converter()
        conv.convert(_msg("ZAL|1|J30.1^Allergic Rhinitis^ICD10|20260322"))
        allergy = conv.extract_resource("AllergyIntolerance")
        assert allergy is not None
        assert allergy["code"]["coding"][0]["code"] == "J30.1"
        assert allergy["onsetDateTime"] == "2026-03-22"
        assert allergy["clinicalStatus"]["coding"][0]["code"] == "active"

    def test_load_json_mapping(self, tmp_path):
        from brightohir import V2Converter
        from brightohir.custom import load_custom_mappings

        mapping = {
            "version": 1,
            "segments": {
                "ZQT": {
                    "resource": "Observation",
                    "defaults": {"status": "final"},
                    "fields": [
                        {"source": 2, "target": "valueQuantity.value", "datatype": "NM"},
                        {"source": 3, "target": "valueQuantity.unit", "datatype": "ST"},
                    ],
                }
            },
        }
        path = tmp_path / "zsegments.json"
        path.write_text(json.dumps(mapping), encoding="utf-8")
        registered = load_custom_mappings(path)
        assert registered == ["ZQT"]

        conv = V2Converter()
        conv.convert(_msg("ZQT|1|72|kg"))
        obs = conv.extract_resource("Observation")
        assert obs is not None
        assert obs["status"] == "final"
        assert obs["valueQuantity"]["value"] == 72.0
        assert obs["valueQuantity"]["unit"] == "kg"

    def test_register_custom_mappings_from_dict(self):
        from brightohir import V2Converter, register_custom_mappings

        mapping = {
            "segments": {
                "ZLB": {
                    "resource": "Observation",
                    "fields": [{"source": 2, "target": "valueString", "datatype": "ST"}],
                }
            }
        }
        registered = register_custom_mappings(mapping)
        assert registered == ["ZLB"]

        conv = V2Converter()
        conv.convert(_msg("ZLB|1|lab note"))
        obs = conv.extract_resource("Observation")
        assert obs is not None
        assert obs["valueString"] == "lab note"

    def test_invalid_mapping_raises(self):
        from brightohir.custom import register_custom_mappings
        with pytest.raises(ValueError, match="segments"):
            register_custom_mappings({"foo": "bar"})
        with pytest.raises(ValueError, match="resource"):
            register_custom_mappings({"segments": {"ZXX": {"fields": []}}})
