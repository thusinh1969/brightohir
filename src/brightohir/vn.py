"""
Vietnamese Healthcare Code Systems — Loader, Lookup, FHIR Integration.

Hệ thống mã y tế Việt Nam theo QĐ 4469/QĐ-BYT, QĐ 7603/QĐ-BYT, QĐ 824/QĐ-BYT.

Usage:
    from brightohir.vn import VN

    VN.load("data/vn/")              # Load all JSONL files
    code = VN.icd10("J06.9")         # Lookup ICD-10
    cc = VN.to_codeable_concept("icd10", "J06.9")  # FHIR CodeableConcept
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

__all__ = ["VN", "VNCodeSystem"]

# ═══════════════════════════════════════════════════════════════════════════════
# FHIR CodeSystem URIs for Vietnamese code systems
# ═══════════════════════════════════════════════════════════════════════════════

VN_CODE_SYSTEMS: dict[str, dict[str, str]] = {
    "icd10": {
        "system": "https://icd.kcb.vn/ICD-10-VN",
        "name": "ICD-10 Vietnam",
        "name_vi": "Mã bệnh ICD-10 Việt Nam",
        "authority": "QĐ 4469/QĐ-BYT (28/10/2020)",
        "file": "icd10_vn.jsonl",
    },
    "yhct": {
        "system": "https://icd.kcb.vn/YHCT",
        "name": "Traditional Medicine ICD",
        "name_vi": "Mã bệnh Y học cổ truyền",
        "authority": "QĐ 6061/QĐ-BYT (29/12/2017)",
        "file": "icd10_yhct.jsonl",
    },
    "drug": {
        "system": "https://dmdc.moh.gov.vn/thuoc-tan-duoc",
        "name": "Western Drug Codes",
        "name_vi": "Mã thuốc tân dược",
        "authority": "QĐ 7603/QĐ-BYT Phụ lục 5",
        "file": "drugs_western.jsonl",
    },
    "drug_trad": {
        "system": "https://dmdc.moh.gov.vn/thuoc-yhct",
        "name": "Traditional Drug Codes",
        "name_vi": "Mã thuốc YHCT",
        "authority": "QĐ 7603/QĐ-BYT Phụ lục 6",
        "file": "drugs_traditional.jsonl",
    },
    "lab": {
        "system": "https://dmdc.moh.gov.vn/xet-nghiem",
        "name": "Lab Test Codes",
        "name_vi": "Mã xét nghiệm",
        "authority": "QĐ 7603/QĐ-BYT Phụ lục 11",
        "file": "lab_tests.jsonl",
    },
    "procedure": {
        "system": "https://dmdc.moh.gov.vn/dvkt",
        "name": "Procedure Codes",
        "name_vi": "Mã dịch vụ kỹ thuật",
        "authority": "QĐ 7603/QĐ-BYT Phụ lục 1",
        "file": "procedures.jsonl",
    },
    "supply": {
        "system": "https://dmdc.moh.gov.vn/vtyt",
        "name": "Medical Supply Codes",
        "name_vi": "Mã vật tư y tế",
        "authority": "QĐ 7603/QĐ-BYT Phụ lục 8",
        "file": "medical_supplies.jsonl",
    },
    "blood": {
        "system": "https://dmdc.moh.gov.vn/mau",
        "name": "Blood Product Codes",
        "name_vi": "Mã máu và chế phẩm máu",
        "authority": "QĐ 7603/QĐ-BYT Phụ lục 9",
        "file": "blood_products.jsonl",
    },
    "bhyt_object": {
        "system": "https://baohiemxahoi.gov.vn/doi-tuong",
        "name": "BHYT Beneficiary Types",
        "name_vi": "Đối tượng BHYT",
        "authority": "QĐ 7603 + QĐ 2010/QĐ-BYT (2025)",
        "file": "bhyt_objects.jsonl",
    },
    "hospital_tier": {
        "system": "https://dmdc.moh.gov.vn/hang-bv",
        "name": "Hospital Tiers",
        "name_vi": "Hạng bệnh viện",
        "authority": "NĐ 146/2018/NĐ-CP",
        "file": "hospital_tiers.jsonl",
    },
    "province": {
        "system": "https://danhmuchanhchinh.gso.gov.vn",
        "name": "Province Codes",
        "name_vi": "Mã tỉnh/thành phố",
        "authority": "Tổng cục Thống kê",
        "file": "provinces.jsonl",
    },
}

# Aliases for convenience
_ALIASES: dict[str, str] = {
    "icd": "icd10", "icd10_vn": "icd10", "benh": "icd10",
    "yhct": "yhct", "co_truyen": "yhct",
    "thuoc": "drug", "drugs": "drug", "medication": "drug",
    "thuoc_yhct": "drug_trad",
    "xet_nghiem": "lab", "test": "lab", "loinc": "lab",
    "dvkt": "procedure", "surgery": "procedure",
    "vtyt": "supply", "vat_tu": "supply",
    "mau": "blood",
    "bhyt": "bhyt_object", "insurance": "bhyt_object",
    "bv": "hospital_tier", "tier": "hospital_tier",
    "tinh": "province", "city": "province",
}


def _resolve_alias(key: str) -> str:
    """Resolve alias to canonical code system key."""
    key = key.lower().strip()
    return _ALIASES.get(key, key)


# ═══════════════════════════════════════════════════════════════════════════════
# VNCodeSystem — single code system store
# ═══════════════════════════════════════════════════════════════════════════════

class VNCodeSystem:
    """A loaded Vietnamese code system with lookup and search."""

    def __init__(self, key: str, meta: dict[str, str]):
        self.key = key
        self.system = meta["system"]
        self.name = meta["name"]
        self.name_vi = meta["name_vi"]
        self.authority = meta["authority"]
        self._codes: dict[str, dict[str, Any]] = {}  # code → full record
        self._search_index: list[tuple[str, str]] = []  # (lowered text, code)

    def load_jsonl(self, path: str | Path) -> int:
        """Load JSONL file. Returns number of records loaded."""
        count = 0
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    continue
                code = record.get("code")
                if not code:
                    continue
                self._codes[str(code)] = record
                # Build search index: combine all display fields
                search_parts = []
                for field in ("display_vi", "display_en", "display_modern",
                              "active_ingredient", "latin", "code"):
                    val = record.get(field)
                    if val:
                        search_parts.append(str(val).lower())
                self._search_index.append((" ".join(search_parts), str(code)))
                count += 1
        return count

    def get(self, code: str) -> dict[str, Any] | None:
        """Lookup by exact code."""
        return self._codes.get(str(code))

    def search(self, query: str, max_results: int = 10) -> list[dict[str, Any]]:
        """Search by Vietnamese or English name. Simple substring match."""
        q = query.lower().strip()
        if not q:
            return []
        results = []
        for text, code in self._search_index:
            if q in text:
                results.append(self._codes[code])
                if len(results) >= max_results:
                    break
        return results

    def to_codeable_concept(self, code: str) -> dict[str, Any] | None:
        """Convert code to FHIR R5 CodeableConcept."""
        record = self.get(code)
        if not record:
            return None
        coding: dict[str, Any] = {
            "system": self.system,
            "code": str(record["code"]),
        }
        # Use display_vi as primary display
        display = record.get("display_vi") or record.get("display_en")
        if display:
            coding["display"] = display
        result: dict[str, Any] = {"coding": [coding]}
        # Add English as text if different from display
        en = record.get("display_en")
        if en and en != display:
            result["text"] = en
        return result

    def to_coding(self, code: str) -> dict[str, Any] | None:
        """Convert code to FHIR R5 Coding (single coding, not wrapped in CodeableConcept)."""
        record = self.get(code)
        if not record:
            return None
        coding: dict[str, Any] = {
            "system": self.system,
            "code": str(record["code"]),
        }
        display = record.get("display_vi") or record.get("display_en")
        if display:
            coding["display"] = display
        return coding

    def to_fhir_codesystem(self) -> dict[str, Any]:
        """Export as FHIR R5 CodeSystem resource."""
        concepts = []
        for code, record in self._codes.items():
            concept: dict[str, Any] = {"code": str(code)}
            display = record.get("display_vi") or record.get("display_en")
            if display:
                concept["display"] = display
            designations = []
            if record.get("display_vi"):
                designations.append({
                    "language": "vi",
                    "value": record["display_vi"],
                })
            if record.get("display_en"):
                designations.append({
                    "language": "en",
                    "value": record["display_en"],
                })
            if designations:
                concept["designation"] = designations
            # Add properties from record
            props = []
            for prop_key in ("chapter", "block", "category", "atc", "loinc",
                             "bhyt_covered", "bhyt_price", "bhyt_ratio",
                             "copay_percent", "contribution_rate", "tier",
                             "ref_low", "ref_high", "form", "route", "unit"):
                val = record.get(prop_key)
                if val is not None:
                    if isinstance(val, bool):
                        props.append({"code": prop_key, "valueBoolean": val})
                    elif isinstance(val, (int, float)):
                        props.append({"code": prop_key, "valueDecimal": val})
                    else:
                        props.append({"code": prop_key, "valueString": str(val)})
            if props:
                concept["property"] = props
            concepts.append(concept)

        return {
            "resourceType": "CodeSystem",
            "url": self.system,
            "name": self.name.replace(" ", ""),
            "title": f"{self.name} / {self.name_vi}",
            "status": "active",
            "content": "complete",
            "count": len(concepts),
            "concept": concepts,
        }

    @property
    def count(self) -> int:
        return len(self._codes)

    def codes(self) -> list[str]:
        """Return all codes."""
        return list(self._codes.keys())

    def all(self) -> list[dict[str, Any]]:
        """Return all records."""
        return list(self._codes.values())

    def __len__(self) -> int:
        return len(self._codes)

    def __contains__(self, code: str) -> bool:
        return str(code) in self._codes

    def __repr__(self) -> str:
        return f"VNCodeSystem({self.key!r}, {self.count} codes)"


# ═══════════════════════════════════════════════════════════════════════════════
# VN — Main API (singleton-style class methods)
# ═══════════════════════════════════════════════════════════════════════════════

class _VNRegistry:
    """Internal registry holding all loaded Vietnamese code systems."""

    def __init__(self):
        self._systems: dict[str, VNCodeSystem] = {}
        self._loaded = False
        self._data_dir: str | None = None

    @staticmethod
    def _bundled_data_dir() -> Path:
        """Find the data/vn/ directory bundled inside the brightohir package."""
        return Path(__file__).parent / "data" / "vn"

    def load_bundled(self) -> dict[str, int]:
        """Load bundled Vietnamese sample data (ships with pip package).

        Usage:
            from brightohir.vn import VN
            VN.load_bundled()   # zero config — just works
        """
        return self.load(self._bundled_data_dir())

    def load(self, data_dir: str | Path | None = None) -> dict[str, int]:
        """Load all JSONL files from data directory.

        Args:
            data_dir: Path to directory with JSONL files.
                      If None, loads bundled data from package.

        Returns dict of {system_key: record_count}.
        Skips .sample.jsonl files unless no non-sample version exists.
        """
        if data_dir is None:
            data_dir = self._bundled_data_dir()
        data_dir = Path(data_dir)
        if not data_dir.is_dir():
            raise FileNotFoundError(f"Data directory not found: {data_dir}")

        self._data_dir = str(data_dir)
        stats: dict[str, int] = {}

        for key, meta in VN_CODE_SYSTEMS.items():
            expected_file = meta["file"]
            full_path = data_dir / expected_file
            sample_path = data_dir / expected_file.replace(".jsonl", ".sample.jsonl")

            # Prefer real file, fallback to sample
            if full_path.exists():
                path = full_path
            elif sample_path.exists():
                path = sample_path
            else:
                continue

            cs = VNCodeSystem(key, meta)
            count = cs.load_jsonl(path)
            if count > 0:
                self._systems[key] = cs
                stats[key] = count

        self._loaded = True
        return stats

    def load_file(self, path: str | Path, key: str | None = None) -> int:
        """Load a single JSONL file. Auto-detects code system from filename."""
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        # Auto-detect key from filename
        if key is None:
            fname = path.name.replace(".sample.jsonl", ".jsonl")
            for k, meta in VN_CODE_SYSTEMS.items():
                if meta["file"] == fname:
                    key = k
                    break
            if key is None:
                raise ValueError(f"Cannot auto-detect code system for: {path.name}. "
                                 f"Pass key= explicitly.")

        meta = VN_CODE_SYSTEMS.get(key)
        if not meta:
            raise ValueError(f"Unknown code system key: {key}")

        cs = VNCodeSystem(key, meta)
        count = cs.load_jsonl(path)
        if count > 0:
            self._systems[key] = cs
        self._loaded = True
        return count

    def _get_system(self, key: str) -> VNCodeSystem:
        key = _resolve_alias(key)
        cs = self._systems.get(key)
        if cs is None:
            available = list(self._systems.keys()) if self._loaded else []
            if not self._loaded:
                raise RuntimeError("VN data not loaded. Call VN.load('data/vn/') first.")
            raise KeyError(f"Code system '{key}' not loaded. Available: {available}")
        return cs

    # ── Shortcut lookups ──

    def icd10(self, code: str) -> dict[str, Any] | None:
        return self._get_system("icd10").get(code)

    def yhct(self, code: str) -> dict[str, Any] | None:
        return self._get_system("yhct").get(code)

    def drug(self, code: str) -> dict[str, Any] | None:
        return self._get_system("drug").get(code)

    def drug_trad(self, code: str) -> dict[str, Any] | None:
        return self._get_system("drug_trad").get(code)

    def lab(self, code: str) -> dict[str, Any] | None:
        return self._get_system("lab").get(code)

    def procedure(self, code: str) -> dict[str, Any] | None:
        return self._get_system("procedure").get(code)

    def supply(self, code: str) -> dict[str, Any] | None:
        return self._get_system("supply").get(code)

    def bhyt_object(self, code: str) -> dict[str, Any] | None:
        return self._get_system("bhyt_object").get(code)

    def hospital_tier(self, code: str) -> dict[str, Any] | None:
        return self._get_system("hospital_tier").get(code)

    def province(self, code: str) -> dict[str, Any] | None:
        return self._get_system("province").get(code)

    # ── Generic API ──

    def get(self, system_key: str, code: str) -> dict[str, Any] | None:
        return self._get_system(system_key).get(code)

    def search(self, system_key: str, query: str, max_results: int = 10) -> list[dict[str, Any]]:
        return self._get_system(system_key).search(query, max_results)

    def to_codeable_concept(self, system_key: str, code: str) -> dict[str, Any] | None:
        return self._get_system(system_key).to_codeable_concept(code)

    def to_coding(self, system_key: str, code: str) -> dict[str, Any] | None:
        return self._get_system(system_key).to_coding(code)

    def to_fhir_codesystem(self, system_key: str) -> dict[str, Any]:
        return self._get_system(system_key).to_fhir_codesystem()

    def system(self, key: str) -> VNCodeSystem:
        """Get the raw VNCodeSystem object."""
        return self._get_system(key)

    def stats(self) -> dict[str, int]:
        return {k: cs.count for k, cs in self._systems.items()}

    def loaded_systems(self) -> list[str]:
        return list(self._systems.keys())

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    @property
    def total_codes(self) -> int:
        return sum(cs.count for cs in self._systems.values())


# Singleton instance
VN = _VNRegistry()
