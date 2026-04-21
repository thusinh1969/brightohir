# brightohir V2.1.2

## Pure Python. HL7 V2.x ↔ FHIR R5. One `pip install`.
## Python thuần. HL7 V2.x ↔ FHIR R5. Một lệnh `pip install`.

```bash
pip install brightohir
```

### What is it / Là gì

brightohir is a **pure-Python** SDK for healthcare data interoperability. No Java. No .NET. No external services. It converts between HL7 V2.x (the pipe-delimited messages that run in 95% of hospitals worldwide) and FHIR R5 (the modern REST/JSON standard mandated by US ONC, EU EHDS, and increasingly by Vietnamese MOH).

*brightohir là SDK **Python thuần** cho tương tác dữ liệu y tế. Không Java. Không .NET. Không dịch vụ ngoài. Chuyển đổi giữa HL7 V2.x (tin nhắn pipe chạy trong 95% bệnh viện toàn cầu) và FHIR R5 (chuẩn REST/JSON hiện đại được yêu cầu bởi US ONC, EU EHDS, và Bộ Y tế Việt Nam).*

### Coverage / Phạm vi

| Area | Coverage | Detail |
|---|---|---|
| **FHIR R5 resources** | **157/157 (100%)** | Create, validate, serialize, bundle — all resource types. See [FHIR_R5_RESOURCES.md](FHIR_R5_RESOURCES.md) |
| **V2→R5 converters** | **51 segment types** (31 creators + 20 enrichers) | Out of ~120 segment types in the V2 spec. These 51 cover Tiers 1–3: ADT, ORM, ORU, pharmacy, immunization, scheduling, financial, documents, personnel, infrastructure — an estimated **98% of real-world V2 exchange**. See [CONVERSION_REFERENCE.md](CONVERSION_REFERENCE.md) |
| **R5→V2 reverse** | **23 resource types** | Patient, Encounter, Observation, AllergyIntolerance, Condition, Immunization, MedicationRequest, MedicationDispense, MedicationAdministration, ServiceRequest, DiagnosticReport, Specimen, Coverage, RelatedPerson, DocumentReference, Appointment, Procedure, Provenance, Device, Practitioner, Organization, Consent, OperationOutcome |
| **R4↔R5 transforms** | **59 resources** | Including all 11 resources with breaking changes (Encounter, MedicationRequest, Condition, etc.) plus 20 new-in-R5 resources. The remaining ~98 R5 resources that are unchanged from R4 pass through without modification. |
| **V2 segment registry** | **57 mappings** | Segment→FHIR target mapping per HL7 V2-to-FHIR IG v1.0.0 (Oct 2025) |
| **V2 message types** | **25 structures** | ADT (A01–A40), ORM, ORU, OML, RDE, RDS, RAS, VXU, MDM, SIU, BAR, DFT |
| **V2 datatype maps** | **39 types** | CWE→CodeableConcept, XPN→HumanName, XAD→Address, CX→Identifier, etc. |
| **V2 vocabulary maps** | **23 tables** | HL7 Table→FHIR CodeSystem URI |
| **V2 versions** | **2.1 through 2.8.2** | All versions supported by hl7apy, auto-normalized |

**What is NOT covered:** ~70 V2 segment types that are rarely seen in production (e.g. OM1-OM7 observation definition segments, CSR/CSP clinical study segments, EQU/ISD equipment segments). These segments are parsed by hl7apy but pass through the converter unconverted. You can extend the converter registry for any missing segment.

*~70 segment types hiếm gặp trong production (như OM1-OM7, CSR/CSP, EQU/ISD) không được convert tự động. Chúng được parse nhưng không chuyển đổi. Bạn có thể mở rộng registry cho bất kỳ segment nào còn thiếu.*

### Privacy & compliance / Quyền riêng tư & tuân thủ

brightohir includes a PII masking module with 4 strategies (redact, hash, pseudonym, partial) that operates on both V2 messages and FHIR resources. This is a **technical tool**, not a legal certification.

**What the masking module does:**
- Identifies and masks PII fields in PID, NK1, GT1, IN1/IN2 segments (V2) and Patient, RelatedPerson, Practitioner, Coverage resources (FHIR)
- Supports deterministic hashing for de-identified data linkage
- Preserves data structure while removing identifiable content
- Does NOT modify data in transit — you call it explicitly in your code

**What it does NOT do:**
- It does not certify GDPR, HIPAA, or Vietnamese Cybersecurity Law (Luật An ninh mạng 24/2018/QH14) compliance
- It does not provide encryption in transit (use TLS at the transport layer)
- It does not enforce access control or audit logging (those are infrastructure concerns)
- It does not guarantee de-identification meets any specific regulatory threshold

**How it helps with compliance / Cách nó hỗ trợ tuân thủ:**

| Regulation | How brightohir helps | What you still need |
|---|---|---|
| **GDPR** (EU) | PII masking for data minimization (Art. 5), pseudonymization (Art. 4(5)) | DPO, DPIA, consent management, encryption at rest |
| **HIPAA** (US) | Supports Safe Harbor de-identification (§164.514(b)) via redact/hash | BAA with vendors, access controls, audit trails |
| **Luật ANM VN** (24/2018/QH14) | Che dấu dữ liệu cá nhân khi xử lý, lưu trữ, truyền tải | Đánh giá tác động, đăng ký hệ thống, mã hóa lưu trữ |

*brightohir cung cấp công cụ kỹ thuật che dấu PII. Đây là công cụ — không phải chứng nhận tuân thủ. Bạn vẫn cần đánh giá tác động, quản lý đồng ý, mã hóa, kiểm soát truy cập, và log kiểm toán ở tầng hạ tầng.*

### Where it works / Dùng ở đâu

HL7 and FHIR are **international standards** maintained by HL7 International, used in 55+ countries. brightohir works anywhere these standards are used:

| Region | Standards in use | brightohir applicability |
|---|---|---|
| **Vietnam** | V2.x widely deployed in hospital HIS; FHIR adoption growing per MOH direction | V2↔R5 conversion, PII masking, **built-in Vietnamese code systems** (ICD-10 VN, BHYT, drugs, labs, procedures) |
| **United States** | FHIR R4 mandated by ONC 21st Century Cures; V2 in 95% of hospitals | R4→R5 migration, V2 legacy integration |
| **European Union** | FHIR R5 for EHDS (European Health Data Space); GDPR requirements | R5 resource creation, PII masking |
| **Australia, Canada, UK** | FHIR adoption mandated by national agencies | Full R5 support |
| **Southeast Asia** | V2 dominant in hospital infrastructure; FHIR emerging | V2→R5 modernization path |

The core library follows HL7 International specifications with no region-specific dependencies. For **Vietnam**, brightohir includes a dedicated `vn` module with 11 Vietnamese healthcare code systems per QĐ 4469/QĐ-BYT, QĐ 7603/QĐ-BYT, and QĐ 824/QĐ-BYT — covering ICD-10 VN, BHYT beneficiary types, drug codes, lab tests, procedures, medical supplies, blood products, hospital tiers, and provinces. When VN data is loaded, V2→R5 converters auto-enrich with Vietnamese system URIs and display names.

*Thư viện cốt lõi tuân theo HL7 International. Riêng cho **Việt Nam**, brightohir có module `vn` với 11 hệ thống mã y tế theo QĐ 4469, QĐ 7603, QĐ 824 — bao gồm ICD-10 VN, đối tượng BHYT, mã thuốc, xét nghiệm, dịch vụ kỹ thuật, vật tư y tế, chế phẩm máu, hạng bệnh viện, và mã tỉnh/thành. Khi data VN được load, các converter V2→R5 tự động gắn URI hệ mã VN và tên hiển thị tiếng Việt.*

---

## Installation — Cài đặt

```bash
pip install brightohir                  # Core / Cốt lõi
pip install brightohir[client]          # + FHIR server client
pip install brightohir[all]             # Everything / Tất cả
```

**From source / Từ source:**
```bash
git clone https://github.com/thusinh1969/brightohir.git
cd brightohir
pip install -e ".[dev]"
pytest tests/ -v  # 170 tests
```

**Requirements:** Python ≥ 3.10 — **Dependencies:** `fhir.resources` ≥ 8.0.0, `hl7apy` ≥ 1.3.5, `pyyaml` ≥ 6.0

---

## Quick test — Kiểm tra nhanh

```python
from brightohir import R5, v2_to_r5, r5_to_v2, r4_to_r5, generate_ack, mask_fhir

# 1. Create R5 Patient
patient = R5.create("Patient", id="test-001", active=True,
    name=[{"family": "Nguyen", "given": ["Van A"]}], gender="male", birthDate="1990-01-15")
print(R5.to_json(patient))

# 2. V2 → R5 (auto-normalizes \n and \r)
bundle = v2_to_r5("""MSH|^~\\&|PMS|PHARMACY|HIS|HOSPITAL|20260322||ADT^A01^ADT_A01|1|P|2.5.1
PID|1||12345^^^LC^MR||NGUYEN^VAN A||19900115|M
PV1|1|I|W^101
OBX|1|NM|29463-7^Body Weight^LN||72|kg|||||F""")
print(f"Converted: {len(bundle['entry'])} FHIR resources")

# 3. R4 → R5
r5 = r4_to_r5({"resourceType": "Encounter", "status": "in-progress",
    "class": {"code": "AMB"}, "hospitalization": {"dischargeDisposition": {"text": "home"}}})
print(f"class → {type(r5['class']).__name__}, hospitalization → admission")

# 4. ACK
ack = generate_ack("MSH|^~\\&|A|B|C|D|20260322||ADT^A01|1|P|2.5\rPID|1||999\r")
print(f"ACK contains AA: {'AA' in ack}")

# 5. PII masking
masked = mask_fhir(R5.to_dict(patient))
print(f"Name masked: {masked['name'][0]['family']}")  # [REDACTED]

print("✅ All working!")
```

```bash
# Run full test suite
pytest tests/ -v    # Expected: 170 passed
```

---

## Usage guide — Hướng dẫn sử dụng

### 1. Create FHIR R5 resources / Tạo resource R5

```python
from brightohir import R5

patient = R5.create("Patient",
    id="lc-001", active=True,
    name=[{"family": "Nguyễn", "given": ["Văn", "A"], "use": "official"}],
    gender="male", birthDate="1990-01-15",
    identifier=[{"system": "https://longchau.vn/mrn", "value": "LC-12345"}])

obs = R5.create("Observation", status="final",
    code={"coding": [{"system": "http://loinc.org", "code": "29463-7", "display": "Body Weight"}]},
    subject={"reference": "Patient/lc-001"},
    valueQuantity={"value": 72.5, "unit": "kg"})

# Serialize / Validate / Bundle
json_str = R5.to_json(patient)
errors = R5.validate("Patient", {"gender": "INVALID"})  # → ["1 validation error..."]
bundle = R5.bundle("transaction", [patient, obs])

# All 157 resource types available
R5.list_resources()                  # All 157
R5.list_resources("medications")     # By category
```

### 2. V2.x → FHIR R5

```python
from brightohir import v2_to_r5, V2Converter

bundle = v2_to_r5(adt_a01_string)                # Quick
conv = V2Converter()
bundle = conv.convert(adt_a01_string)             # Full control
patient = conv.extract_resource("Patient")
obs_list = conv.extract_all("Observation")
```

### 3. FHIR R5 → V2.x

```python
from brightohir import r5_to_v2

v2_msg = r5_to_v2(bundle_dict,
    message_type="ADT_A01",
    sending_app="LONG_CHAU_PMS",
    receiving_app="HOSPITAL_HIS")
```

### 4. R4 ↔ R5

```python
from brightohir import r4_to_r5, r5_to_r4, conversion_status

r5 = r4_to_r5(r4_encounter)    # Handles all breaking changes
r4 = r5_to_r4(r5_encounter)    # Graceful downgrade
info = conversion_status("Encounter")  # → {"status": "restructured", "changes": [...]}
```

### 5. ACK/NAK

```python
from brightohir import generate_ack

ack = generate_ack(incoming_msg)                                              # AA
nak = generate_ack(incoming_msg, ack_code="AE", error_msg="Patient not found") # AE
```

### 6. PII masking

```python
from brightohir import mask_v2, mask_fhir, mask_bundle
from brightohir.security import PIIMasker

masked = mask_v2(v2_msg)                                    # Redact
masked = mask_fhir(patient_dict)                            # Redact
masked = PIIMasker(strategy="hash", salt="secret").mask_fhir(patient_dict)  # Deterministic hash
masked = PIIMasker(strategy="pseudonym").mask_v2(v2_msg)    # Fake but valid
masked = PIIMasker(strategy="partial").mask_fhir(patient_dict)  # N****n
```

### 7. Vietnamese code systems / Hệ thống mã y tế Việt Nam

```python
from brightohir.vn import VN

# Zero config — load bundled sample data (ships with pip package)
# Không cần config — load data mẫu đi kèm package
VN.load_bundled()                    # or VN.load() — same thing
print(VN.stats())                    # → {"icd10": 5, "drug": 3, "lab": 3, "bhyt_object": 5}

# Production — load full crawled data from your directory
# Production — load data đầy đủ đã crawl
# VN.load("path/to/your/data/vn/")  # → {"icd10": 14400, "drug": 20000, ...}

# Lookup / Tra cứu
icd = VN.icd10("J06.9")              # → {"code": "J06.9", "display_vi": "Nhiễm trùng hô hấp trên...", ...}
drug = VN.drug("TD.0001")            # → {"code": "TD.0001", "atc": "N02BE01", ...}
lab = VN.lab("XN.001")               # → {"code": "XN.001", "loinc": "718-7", ...}
bhyt = VN.bhyt_object("3")           # → {"code": "3", "display_vi": "Trẻ em dưới 6 tuổi", "copay_percent": 0}

# Search Vietnamese or English / Tìm kiếm tiếng Việt hoặc Anh
results = VN.search("icd10", "đái tháo đường")   # → [{"code": "E11.9", ...}]
results = VN.search("drug", "paracetamol")        # → [{"code": "TD.0001", ...}]

# FHIR CodeableConcept — 1 line
cc = VN.to_codeable_concept("icd10", "J06.9")
# → {"coding": [{"system": "https://icd.kcb.vn/ICD-10-VN", "code": "J06.9",
#     "display": "Nhiễm trùng hô hấp trên cấp tính, không đặc hiệu"}]}

# Export full FHIR CodeSystem / Xuất toàn bộ CodeSystem FHIR
cs = VN.to_fhir_codesystem("icd10")   # → {"resourceType": "CodeSystem", "count": 14400, ...}
```

**11 Vietnamese code systems / 11 hệ thống mã VN:**

| Key | System | Source |
|---|---|---|
| `icd10` | ICD-10 Vietnam (~14,400 mã) | QĐ 4469/QĐ-BYT |
| `yhct` | Y học cổ truyền U-codes (~2,000) | QĐ 6061/QĐ-BYT |
| `drug` | Thuốc tân dược (~20,000+) | QĐ 7603 Phụ lục 5 |
| `drug_trad` | Thuốc YHCT (~5,000+) | QĐ 7603 Phụ lục 6 |
| `lab` | Xét nghiệm (~3,000+) | QĐ 7603 Phụ lục 11 |
| `procedure` | Dịch vụ kỹ thuật (~8,000+) | QĐ 7603 Phụ lục 1 |
| `supply` | Vật tư y tế (~10,000+) | QĐ 7603 Phụ lục 8 |
| `blood` | Máu & chế phẩm (~200) | QĐ 7603 Phụ lục 9 |
| `bhyt_object` | Đối tượng BHYT (~50) | QĐ 7603 + QĐ 2010/2025 |
| `hospital_tier` | Hạng bệnh viện (~100) | NĐ 146/2018 |
| `province` | Mã tỉnh/thành (63) | GSO.gov.vn |

**Auto-enrichment:** When VN data is loaded, V2→R5 converters automatically enrich codes with Vietnamese system URIs and display names — DG1 (ICD-10), OBX (labs), RXE/RXD/RXO/RXG (drugs), PR1 (procedures). Zero code changes needed.

*Khi data VN được load, các converter V2→R5 tự động gắn URI hệ mã VN và tên hiển thị — DG1 (ICD-10), OBX (xét nghiệm), RXE/RXD/RXO/RXG (thuốc), PR1 (DVKT). Không cần thay đổi code.*

**Data format:** JSONL (one JSON per line). See [data/vn/SCHEMA.md](src/brightohir/data/vn/SCHEMA.md) for full spec. Sample data included in package; replace with full crawled data for production.

---

## Production deployment — Triển khai production

### MLLP listener — receive V2 messages from hospitals / Nhận V2 từ bệnh viện

```python
# server.py
from brightohir import v2_to_r5, generate_ack
from brightohir.transport import MLLPServer

def handle_message(raw_v2: str) -> str:
    try:
        bundle = v2_to_r5(raw_v2)
        store_to_database(bundle)  # your logic
        return generate_ack(raw_v2, ack_code="AA")
    except Exception as e:
        return generate_ack(raw_v2, ack_code="AE", error_msg=str(e)[:200])

server = MLLPServer(
    host="0.0.0.0",       # All interfaces
    port=2575,             # Standard HL7 port
    handler=handle_message,
    max_connections=50)

server.start()             # Blocking
# server.start_background() # Or threaded
```

### MLLP client — send V2 to external systems / Gửi V2 ra ngoài

```python
from brightohir import r5_to_v2
from brightohir.transport import MLLPClient

v2_msg = r5_to_v2(fhir_bundle, message_type="ADT_A08",
    sending_app="LC_PMS", receiving_app="HIS")

with MLLPClient("hospital-his.local", 2575, timeout=30) as client:
    ack = client.send(v2_msg)
    if "AA" in ack:
        print("Accepted")
```

### Network & security / Mạng & bảo mật

```
Hospital HIS (10.0.1.100) ──TCP/2575──▶ brightohir MLLP Server (10.0.2.50:2575)
                           ◀──ACK/NAK──
```

```bash
# Firewall: only allow known hospital IPs
sudo ufw allow from 10.0.1.0/24 to any port 2575 proto tcp
```

**Security checklist / Danh sách bảo mật:**

- [ ] Port 2575 restricted to known hospital IPs — *Chỉ mở cho IP bệnh viện đã biết*
- [ ] TLS via reverse proxy (nginx/HAProxy/stunnel) — *TLS qua reverse proxy*
- [ ] PII masking on all logged messages — *Che PII trên mọi log*
- [ ] Separate VLAN for HL7 traffic — *VLAN riêng cho traffic HL7*
- [ ] Monitor AE/AR responses — *Giám sát phản hồi AE/AR*
- [ ] Rate limiting at firewall — *Giới hạn tốc độ ở firewall*

### Running as systemd service

```ini
# /etc/systemd/system/brightohir-mllp.service
[Unit]
Description=BrighTO HL7 MLLP Integration Engine
After=network.target
[Service]
Type=simple
User=hl7service
WorkingDirectory=/opt/brightohir
ExecStart=/opt/brightohir/venv/bin/python server.py
Restart=always
RestartSec=5
[Install]
WantedBy=multi-user.target
```

---

## Other use cases — Cách dùng khác

**FHIR REST API:**
```python
from fhirpy import SyncFHIRClient  # pip install brightohir[client]
client = SyncFHIRClient("https://fhir.example.com/r5", authorization="Bearer TOKEN")
fhir_patient = client.resource("Patient", **R5.to_dict(patient))
fhir_patient.save()
```

**Batch file conversion / Chuyển đổi hàng loạt:**
```python
from pathlib import Path
from brightohir import v2_to_r5
import json

for f in Path("incoming_v2/").glob("*.hl7"):
    bundle = v2_to_r5(f.read_text())
    Path(f"fhir_out/{f.stem}.json").write_text(json.dumps(bundle, indent=2))
```

**Audit logging with PII protection:**
```python
from brightohir import v2_to_r5, mask_bundle
bundle = v2_to_r5(msg)
safe_log = mask_bundle(bundle, strategy="hash")  # Log this
```

---

## Debugging — Gỡ lỗi

**V2 version error:**
```python
# brightohir auto-normalizes \n→\r and unsupported versions
bundle = v2_to_r5(triple_quoted_string)  # ✅ just works
```

**Check supported segments:**
```python
from brightohir.convert_v2 import _SEGMENT_CONVERTERS
print(sorted(_SEGMENT_CONVERTERS.keys()))
```

**Inspect conversion:**
```python
conv = V2Converter()
bundle = conv.convert(msg)
for rt in ["Patient", "Encounter", "Observation"]:
    print(f"{rt}: {len(conv.extract_all(rt))} found")
    for r in conv.extract_all(rt):
        print(json.dumps(r, indent=2))
```

**R4↔R5 change details:**
```python
from brightohir import conversion_status
info = conversion_status("Encounter")
for action, field, detail in info['changes']:
    print(f"  {action}: {field} — {detail}")
```

**MLLP debug logging:**
```python
import logging
logging.basicConfig(level=logging.DEBUG)
# brightohir.transport logs connect/disconnect/send/receive
```

---

## Limitations & roadmap — Hạn chế & kế hoạch

### Current limitations / Hạn chế hiện tại

| Area | Limitation | Hạn chế |
|---|---|---|
| V2 segments | 51 of ~120 types (31 creators + 20 enrichers). Remaining ~70 rare/obsolete types pass through unconverted. | 51/~120 loại. ~70 loại hiếm/lỗi thời truyền qua không chuyển đổi. |
| R5→V2 | 23 reverse converters. Missing niche types: Parameters, Account (guarantor). | 23 bộ đảo ngược. Thiếu vài loại đặc thù. |
| MLLP | No built-in TLS. Use reverse proxy. | Không có TLS tích hợp. Dùng reverse proxy. |
| Z-segments | Custom Z-segments ignored. Pre-process before convert. | Z-segment bỏ qua. Tiền xử lý trước convert. |
| FHIR operations | No $validate, $process-message. Use fhirpy directly. | Không có $validate. Dùng fhirpy trực tiếp. |

### Roadmap

- **v2.2** — Z-segment extension framework, custom YAML mapping loader
- **v2.3** — CDA ↔ FHIR R5 (Vietnamese discharge summaries)
- **v3.0** — Async MLLP (asyncio), WebSocket, FHIR Subscription

---

## Reference files / Tài liệu tham chiếu

- **[FHIR_R5_RESOURCES.md](FHIR_R5_RESOURCES.md)** — Complete list of all 157 FHIR R5 resources supported (100%) / *Danh sách đầy đủ 157 resource R5 (100%)*
- **[CONVERSION_REFERENCE.md](CONVERSION_REFERENCE.md)** — All conversion mappings: V2→R5, R5→V2, R4↔R5, datatypes, vocabulary / *Tất cả mapping chuyển đổi*
- **[data/vn/SCHEMA.md](src/brightohir/data/vn/SCHEMA.md)** — Vietnamese code system data schema (11 JSONL formats) / *Đặc tả dữ liệu 11 hệ thống mã y tế VN*

---

## Testing — Kiểm thử

```bash
pytest tests/ -v                    # All 170 tests
pytest tests/test_sdk.py -v         # Core: R5, R4↔R5, V2 basics (37 tests)
pytest tests/test_v11.py -v         # v1.1: ACK, PII, MLLP, segment converters (47 tests)
pytest tests/test_v20.py -v         # v2.0: Tier 2+3 creators, enrichers, reverse (45 tests)
pytest tests/test_vn.py -v          # v2.1: Vietnamese code systems, auto-enrich (41 tests)
pytest tests/ --cov=brightohir      # With coverage
```

---

## Architecture — Kiến trúc

```
src/brightohir/
├── __init__.py          # 33 public exports
├── r5.py                # R5 factory — 157 resources
├── convert_r4r5.py      # R4 ↔ R5 — 59 transforms
├── convert_v2.py        # V2 ↔ R5 — 31 creators + 20 enrichers + 23 reverse
├── vn.py                # Vietnamese code systems — 11 systems, JSONL loader, FHIR export
├── registry.py          # 277 standard mappings
├── ack.py               # ACK/NAK generator
├── transport.py         # MLLP server + client
├── security.py          # PII masking (4 strategies)
├── data/vn/             # Vietnamese JSONL data (sample + full)
│   ├── SCHEMA.md        # Data format specification
│   ├── icd10_vn.jsonl   # ICD-10 Vietnam
│   ├── drugs_western.jsonl
│   ├── lab_tests.jsonl
│   └── ...              # 11 files total
└── py.typed             # PEP 561
```

---

## Acknowledgments — Tri ân

brightohir would not exist without the exceptional open-source libraries it builds upon. We are deeply grateful to their authors and communities.

*brightohir không thể tồn tại nếu thiếu các thư viện mã nguồn mở xuất sắc mà nó được xây dựng trên đó. Chúng tôi trân trọng tri ân các tác giả và cộng đồng đằng sau chúng.*

| Library | Authors / Maintainers | Contribution to brightohir | License |
|---|---|---|---|
| **[fhir.resources](https://github.com/nazrulworld/fhir.resources)** | Md Nazrul Islam ([@nazrulworld](https://github.com/nazrulworld)) | The foundation of our FHIR R5 support — 157 Pydantic V2 models with full validation, serialization, and type safety. Without this library, every resource would need hand-written schemas. | BSD |
| **[fhir-core](https://github.com/nazrulworld/fhir-core)** | Md Nazrul Islam | Abstract base classes and primitive data types that power fhir.resources. The invisible engine underneath. | BSD |
| **[hl7apy](https://github.com/crs4/hl7apy)** | CRS4 — Vittorio Meloni, Giovanni Busonera, and contributors | Our V2 parsing backbone — grammar-driven, specification-compliant, covering V2.1 through V2.8.2. The quality of hl7apy's parser directly enables brightohir's segment-level conversion accuracy. | MIT |
| **[fhirpy](https://github.com/beda-software/fhir-py)** | beda.software ([@ir4y](https://github.com/ir4y), [@ruscoder](https://github.com/ruscoder)) | Async/sync FHIR client that powers our optional server connectivity. Clean, well-maintained, production-tested. | MIT |
| **[fhirpath-py](https://github.com/beda-software/fhirpath-py)** | beda.software | FHIRPath expression evaluator with R4/R5 model support. Essential for advanced querying. | MIT |
| **[Pydantic](https://github.com/pydantic/pydantic)** | Samuel Colvin ([@samuelcolvin](https://github.com/samuelcolvin)) and team | The validation engine behind fhir.resources. V2's performance and type-safety made FHIR resource handling practical in Python. | MIT |

We also acknowledge the standards bodies whose work defines the interoperability landscape:

*Chúng tôi cũng tri ân các tổ chức tiêu chuẩn đã định hình hạ tầng tương tác y tế:*

- **[HL7 International](https://www.hl7.org/)** — For HL7 V2, FHIR, and the V2-to-FHIR Implementation Guide that provides the computable mappings (400+ CSV ConceptMaps) on which our conversion logic is based.
- **[HL7 V2-to-FHIR Project](https://github.com/HL7/v2-to-fhir)** — Keith Boone, Craig Newman, and the Orders & Observations Workgroup — 7 years of mapping work culminating in the STU1 publication (Oct 2025) that made standardized V2↔FHIR conversion possible.
- **[SMART on FHIR](https://smarthealthit.org/)** — Boston Children's Hospital Computational Health Informatics Program — for fhir-parser and the client-py reference implementation that shaped the Python FHIR ecosystem.

To all these teams: your work enables healthcare interoperability for millions of patients. brightohir is simply a bridge that connects your tools.

*Gửi đến tất cả các đội ngũ trên: công trình của các bạn mang lại khả năng tương tác y tế cho hàng triệu bệnh nhân. brightohir chỉ đơn giản là cây cầu nối các công cụ của các bạn lại với nhau.*

---

## License — Giấy phép

**MIT License** — Copyright (c) 2026 BrighTO Technology / Hatto AI

See [LICENSE](LICENSE) for full text.

## Contact — Liên hệ

**BrighTO Technology / Hatto AI** — nguyen@brighto.ai | nguyen@hatto.com

GitHub: [github.com/thusinh1969/brightohir](https://github.com/thusinh1969/brightohir)

---

*Built with inspiration by Long Châu to serve millions of patients across Vietnam, everyday.*

*Được xây dựng với cảm hứng phục vụ hàng triệu bệnh nhân trên khắp Việt Nam, mỗi ngày của Chuỗi Nhà Thuốc Long Châu.*
