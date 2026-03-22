# brightohir

## Pure Python. HL7 V2.x ↔ FHIR R5. One `pip install`.
## Python thuần. HL7 V2.x ↔ FHIR R5. Một lệnh `pip install`.

```bash
pip install brightohir
```

### What is it / Là gì

brightohir is a **pure-Python** SDK for healthcare data interoperability. No Java. No .NET. No external services. It converts between HL7 V2.x (the pipe-delimited messages that run in 95% of hospitals worldwide) and FHIR R5 (the modern REST/JSON standard mandated by US ONC, EU EHDS, and increasingly by Vietnamese MOH).

*brightohir là SDK **Python thuần** cho tương tác dữ liệu y tế. Không Java. Không .NET. Không dịch vụ ngoài. Chuyển đổi giữa HL7 V2.x (tin nhắn pipe chạy trong 95% bệnh viện toàn cầu) và FHIR R5 (chuẩn REST/JSON hiện đại được yêu cầu bởi US ONC, EU EHDS, và Bộ Y tế Việt Nam).*

### Coverage — honest numbers / Phạm vi — số liệu thật

| Area | Coverage | Detail |
|---|---|---|
| **FHIR R5 resources** | **157/157 (100%)** | Create, validate, serialize, bundle — all resource types. See [FHIR_R5_RESOURCES.md](FHIR_R5_RESOURCES.md) |
| **V2→R5 converters** | **19 segment types** | Out of ~120 segment types in the V2 spec. These 19 cover the segments present in ADT, ORM, ORU, pharmacy, immunization, scheduling, financial, and document messages — the traffic that makes up an estimated 85–90% of real-world V2 exchange. See [CONVERSION_REFERENCE.md](CONVERSION_REFERENCE.md) |
| **R5→V2 reverse** | **15 resource types** | Patient, Encounter, Observation, AllergyIntolerance, Condition, Immunization, MedicationRequest, MedicationDispense, ServiceRequest, DiagnosticReport, Specimen, Coverage, RelatedPerson, DocumentReference, Appointment |
| **R4↔R5 transforms** | **59 resources** | Including all 11 resources with breaking changes (Encounter, MedicationRequest, Condition, etc.) plus 20 new-in-R5 resources. The remaining ~98 R5 resources that are unchanged from R4 pass through without modification. |
| **V2 segment registry** | **57 mappings** | Segment→FHIR target mapping per HL7 V2-to-FHIR IG v1.0.0 (Oct 2025) |
| **V2 message types** | **25 structures** | ADT (A01–A40), ORM, ORU, OML, RDE, RDS, RAS, VXU, MDM, SIU, BAR, DFT |
| **V2 datatype maps** | **39 types** | CWE→CodeableConcept, XPN→HumanName, XAD→Address, CX→Identifier, etc. |
| **V2 vocabulary maps** | **23 tables** | HL7 Table→FHIR CodeSystem URI |
| **V2 versions** | **2.1 through 2.8.2** | All versions supported by hl7apy, auto-normalized |

**What is NOT covered:** ~100 V2 segment types that are rarely seen in production (e.g. MFA, MFI master file segments, OM1-OM7 observation definition segments, CSR/CSP clinical study segments, EQU/ISD equipment segments). These segments are parsed by hl7apy but pass through the converter unconverted. You can extend the converter registry for any missing segment.

*~100 segment types hiếm gặp trong production (như MFA, OM1-OM7, CSR/CSP, EQU/ISD) không được convert tự động. Chúng được parse nhưng không chuyển đổi. Bạn có thể mở rộng registry cho bất kỳ segment nào còn thiếu.*

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
| **Vietnam** | V2.x widely deployed in hospital HIS; FHIR adoption growing per MOH direction | V2↔R5 conversion, PII masking for Luật ANM |
| **United States** | FHIR R4 mandated by ONC 21st Century Cures; V2 in 95% of hospitals | R4→R5 migration, V2 legacy integration |
| **European Union** | FHIR R5 for EHDS (European Health Data Space); GDPR requirements | R5 resource creation, PII masking |
| **Australia, Canada, UK** | FHIR adoption mandated by national agencies | Full R5 support |
| **Southeast Asia** | V2 dominant in hospital infrastructure; FHIR emerging | V2→R5 modernization path |

The library has no region-specific dependencies. All code systems, vocabularies, and mappings follow HL7 International specifications. Local extensions (Vietnamese ICD codes, BHXH insurance codes) can be added via the extensible registry.

*Thư viện không phụ thuộc vùng miền. Tất cả code system, vocabulary, mapping tuân theo HL7 International. Có thể mở rộng registry cho mã địa phương (ICD VN, mã BHXH).*

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
pytest tests/ -v  # 84 tests
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
pytest tests/ -v    # Expected: 84 passed
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
| V2 segments | 19 of ~120 types. Remaining pass through unconverted. | 19/~120 loại. Còn lại truyền qua không chuyển đổi. |
| R5→V2 | 15 of 19 converters have reverse. Missing: Account, PractitionerRole. | 15/19 có đảo ngược. Thiếu: Account, PractitionerRole. |
| MLLP | No built-in TLS. Use reverse proxy. | Không có TLS tích hợp. Dùng reverse proxy. |
| Z-segments | Custom Z-segments ignored. Pre-process before convert. | Z-segment bỏ qua. Tiền xử lý trước convert. |
| FHIR operations | No $validate, $process-message. Use fhirpy directly. | Không có $validate. Dùng fhirpy trực tiếp. |

### Roadmap

- **v1.2** — RXR, PD1, IN2, IN3, ARV, AIG/AIL/AIP/AIS segments
- **v1.3** — Z-segment extension framework, custom YAML mapping loader
- **v1.4** — CDA ↔ FHIR R5 (Vietnamese discharge summaries)
- **v2.0** — Async MLLP (asyncio), WebSocket, FHIR Subscription

---

## Reference files / Tài liệu tham chiếu

- **[FHIR_R5_RESOURCES.md](FHIR_R5_RESOURCES.md)** — Complete list of all 157 FHIR R5 resources supported (100%) / *Danh sách đầy đủ 157 resource R5 (100%)*
- **[CONVERSION_REFERENCE.md](CONVERSION_REFERENCE.md)** — All conversion mappings: V2→R5, R5→V2, R4↔R5, datatypes, vocabulary / *Tất cả mapping chuyển đổi*

---

## Testing — Kiểm thử

```bash
pytest tests/ -v                    # All 84 tests
pytest tests/test_sdk.py -v         # Core (37 tests)
pytest tests/test_v11.py -v         # v1.1 modules (47 tests)
pytest tests/ --cov=brightohir      # With coverage
```

---

## Architecture — Kiến trúc

```
src/brightohir/
├── __init__.py          # 30 public exports
├── r5.py                # R5 factory — 157 resources
├── convert_r4r5.py      # R4 ↔ R5 — 59 transforms
├── convert_v2.py        # V2 ↔ R5 — 19+15 converters
├── registry.py          # 203 standard mappings
├── ack.py               # ACK/NAK generator
├── transport.py         # MLLP server + client
├── security.py          # PII masking (4 strategies)
└── py.typed             # PEP 561
```

---

## License — Giấy phép

**MIT License** — Copyright (c) 2026 BrighTO Technology / Hatto AI

See [LICENSE](LICENSE) for full text.

## Contact — Liên hệ

**BrighTO Technology / Hatto AI** — nguyen@brighto.ai | nguyen@hatto.com

GitHub: [github.com/thusinh1969/brightohir](https://github.com/thusinh1969/brightohir)

---

*Built with inspiration from Long Châu Pharmacy Group (FPT Retail), who serving millions of patients across Vietnam everyday.*

*Được xây dựng với cảm hứng từ Nhà thuốc Long Châu (FPT Retail), nơi phục vụ hàng triệu bệnh nhân trên khắp Việt Nam mỗi ngày.*