# brightohir

**The only Python SDK that does HL7 V2.x ↔ FHIR R5 bidirectional conversion, R4↔R5 migration, and MLLP transport in a single `pip install`.**

*Thư viện Python duy nhất chuyển đổi hai chiều HL7 V2.x ↔ FHIR R5, migration R4↔R5, và truyền tải MLLP — chỉ cần một lệnh `pip install`.*

```bash
pip install brightohir
```

```python
from brightohir import R5, v2_to_r5, r5_to_v2, r4_to_r5, generate_ack, mask_fhir

# Convert a hospital HL7 V2 message to FHIR R5 — one line
bundle = v2_to_r5(adt_a01_message)

# Create validated FHIR R5 resources — with full Pydantic typing
patient = R5.create("Patient", name=[{"family": "Nguyen"}], gender="male")
```

---

## Why this exists — Tại sao thư viện này cần tồn tại

### The problem / Vấn đề

Healthcare systems worldwide speak two languages that don't understand each other:

- **HL7 V2.x** (1987–present): Pipe-delimited messages running in 95% of hospital HIS systems globally. Every lab result, every patient admission, every prescription — V2.
- **FHIR R5** (2023–present): The modern REST/JSON standard. Required by US ONC, EU EHDS, and increasingly by Vietnamese MOH for new integrations.

There is no production-ready Python library that bridges both. The Java world has HAPI. The .NET world has Firely. Python had nothing — until now.

*Hệ thống y tế toàn cầu nói hai ngôn ngữ không hiểu nhau: HL7 V2.x (chạy 95% HIS bệnh viện) và FHIR R5 (chuẩn REST/JSON hiện đại). Không có thư viện Python production-ready nào nối cả hai. Java có HAPI. .NET có Firely. Python — trước đây không có gì.*

### What brightohir does / brightohir làm gì

One library. Three capabilities. Zero glue code.

| Capability | What it does | Khả năng |
|---|---|---|
| **V2.x → R5** | Parse any HL7 V2 message, convert 19 segment types to validated FHIR R5 resources with full cross-referencing | Chuyển đổi V2 sang R5 với 19 loại segment |
| **R5 → V2.x** | Reverse-convert 15 FHIR resource types back to V2 ER7 segments | Chuyển ngược 15 loại resource R5 sang V2 |
| **R4 ↔ R5** | Bidirectional migration handling all breaking changes (Encounter class restructure, medication[x] → CodeableReference, recorder/asserter → participant, etc.) | Migration hai chiều R4↔R5, xử lý mọi breaking change |
| **MLLP transport** | TCP server/client for receiving and sending V2 messages per HL7 standard | Server/client TCP cho gửi nhận V2 theo chuẩn HL7 |
| **ACK/NAK** | Auto-generate acknowledgment responses with proper MSH/MSA/ERR segments | Tự động tạo phản hồi ACK/NAK |
| **PII masking** | Dual-layer (V2 + FHIR) with 4 strategies: redact, hash, pseudonym, partial | Che dấu thông tin cá nhân hai lớp, 4 chiến lược |
| **R5 factory** | Create, validate, serialize any of the 157 FHIR R5 resources with Pydantic V2 models | Tạo, validate, serialize 157 resource R5 |

### Who is this for / Dành cho ai

- **Hospital IT teams** connecting legacy HIS (V2) to modern FHIR APIs — *Đội IT bệnh viện kết nối HIS cũ với FHIR mới*
- **Pharmacy chains** (like Long Châu with 2,500+ stores) integrating PMS ↔ hospital ↔ insurance — *Chuỗi nhà thuốc tích hợp PMS ↔ bệnh viện ↔ bảo hiểm*
- **Vaccination centers** reporting immunization records to national registries — *Trung tâm tiêm chủng báo cáo lên hệ thống quốc gia*
- **Health-tech startups** building FHIR-native apps that must interop with V2 hospitals — *Startup health-tech cần tương thích V2*
- **Government health agencies** modernizing data exchange infrastructure — *Cơ quan y tế hiện đại hóa hạ tầng trao đổi dữ liệu*
- **Any Python developer** who needs healthcare interoperability without learning Java/HAPI — *Lập trình viên Python cần interoperability mà không muốn học Java*

### Standards compliance / Tuân thủ chuẩn quốc tế

| Standard | Version | Source |
|---|---|---|
| FHIR R5 | v5.0.0 — all 157 resources | [hl7.org/fhir/R5](https://hl7.org/fhir/R5/) |
| HL7 V2-to-FHIR IG | v1.0.0 STU (Oct 2025) — 400+ CSV ConceptMaps | [build.fhir.org/ig/HL7/v2-to-fhir](https://build.fhir.org/ig/HL7/v2-to-fhir/) |
| FHIR R4↔R5 maps | Official StructureMaps — 59 resource transforms | [hl7.org/fhir/R5/r4maps.html](http://hl7.org/fhir/5.0.0-draft-final/r4maps.html) |
| HL7 V2.x | Versions 2.1–2.8.2 (via hl7apy) | [HL7 International](https://www.hl7.org/) |
| MLLP | RFC-compliant framing (VT/FS/CR) | [HL7 V2 Transport](https://www.hl7.org/implement/standards/product_brief.cfm?product_id=55) |

---

## Installation — Cài đặt

```bash
# Core (all you need for conversion)
# Cốt lõi (đủ dùng cho chuyển đổi)
pip install brightohir

# With FHIR server client / Kèm client kết nối FHIR server
pip install brightohir[client]

# Everything / Tất cả
pip install brightohir[all]
```

**From source / Từ source:**
```bash
git clone https://github.com/thusinh1969/brightohir.git
cd brightohir
pip install -e ".[dev]"
pytest tests/ -v  # 84 tests
```

**Requirements / Yêu cầu:** Python ≥ 3.10

**Dependencies / Phụ thuộc:**
| Package | Purpose | Mục đích |
|---|---|---|
| `fhir.resources` ≥ 8.0.0 | FHIR R5 Pydantic models | Model R5 Pydantic |
| `hl7apy` ≥ 1.3.5 | V2.x parse/create/validate | Parse/tạo/validate V2 |
| `pyyaml` ≥ 6.0 | Config mappings | Cấu hình mapping |

---

## Quick test — Kiểm tra nhanh

After installing, verify everything works in 30 seconds:

*Sau khi cài, kiểm tra mọi thứ hoạt động trong 30 giây:*

```python
from brightohir import R5, v2_to_r5, r5_to_v2, r4_to_r5, generate_ack, mask_fhir

# 1. Create R5 Patient / Tạo bệnh nhân R5
patient = R5.create("Patient", id="test-001", active=True,
    name=[{"family": "Nguyen", "given": ["Van A"]}], gender="male", birthDate="1990-01-15")
print(R5.to_json(patient))

# 2. Convert V2 → R5 (works with \n or \r — auto-normalized)
# Chuyển V2 → R5 (chấp nhận \n hoặc \r — tự chuẩn hóa)
bundle = v2_to_r5("""MSH|^~\\&|PMS|PHARMACY|HIS|HOSPITAL|20260322||ADT^A01^ADT_A01|1|P|2.5.1
PID|1||12345^^^LC^MR||NGUYEN^VAN A||19900115|M
PV1|1|I|W^101
OBX|1|NM|29463-7^Body Weight^LN||72|kg|||||F""")
print(f"Converted: {len(bundle['entry'])} FHIR resources")

# 3. Convert R4 → R5 / Chuyển R4 → R5
r5 = r4_to_r5({"resourceType": "Encounter", "status": "in-progress",
    "class": {"code": "AMB"}, "hospitalization": {"dischargeDisposition": {"text": "home"}}})
print(f"R4→R5: class is now {type(r5['class'])}, admission={r5.get('admission')}")

# 4. Generate ACK / Tạo ACK
ack = generate_ack("MSH|^~\\&|A|B|C|D|20260322||ADT^A01|MSG1|P|2.5\rPID|1||999\r")
print(f"ACK: {'AA' in ack}")

# 5. Mask PII / Che thông tin cá nhân
masked = mask_fhir(R5.to_dict(patient))
print(f"Masked name: {masked['name'][0]['family']}")  # → [REDACTED]

print("✅ All working!")
```

**Run tests / Chạy test:**
```bash
pytest tests/ -v
# Expected: 84 passed
```

---

## Usage guide — Hướng dẫn sử dụng

### 1. Create FHIR R5 resources / Tạo resource FHIR R5

```python
from brightohir import R5

# Any of the 157 R5 resources / Bất kỳ trong 157 resource R5
patient = R5.create("Patient",
    id="lc-001", active=True,
    name=[{"family": "Nguyễn", "given": ["Văn", "A"], "use": "official"}],
    gender="male", birthDate="1990-01-15",
    identifier=[{"system": "https://longchau.vn/mrn", "value": "LC-12345"}],
    address=[{"line": ["123 Nguyễn Huệ"], "city": "Hồ Chí Minh", "country": "VN"}],
    telecom=[{"system": "phone", "value": "0901234567", "use": "mobile"}])

observation = R5.create("Observation",
    status="final",
    code={"coding": [{"system": "http://loinc.org", "code": "29463-7", "display": "Body Weight"}]},
    subject={"reference": "Patient/lc-001"},
    valueQuantity={"value": 72.5, "unit": "kg", "system": "http://unitsofmeasure.org"})

medication = R5.create("MedicationRequest",
    status="active", intent="order",
    medication={"concept": {"coding": [{"system": "http://snomed.info/sct",
        "code": "387517004", "display": "Paracetamol"}]}},
    subject={"reference": "Patient/lc-001"},
    dosageInstruction=[{"text": "500mg x 3 lần/ngày",
        "timing": {"repeat": {"frequency": 3, "period": 1, "periodUnit": "d"}},
        "doseAndRate": [{"doseQuantity": {"value": 500, "unit": "mg"}}]}])

# Serialize / Xuất dữ liệu
json_str = R5.to_json(patient)       # → JSON string
patient_dict = R5.to_dict(patient)   # → Python dict

# Validate / Kiểm tra hợp lệ
errors = R5.validate("Patient", {"gender": "INVALID"})
# errors = ["1 validation error..."]

# Bundle / Gom gói
bundle = R5.bundle("transaction", [patient, observation, medication])

# Browse resources / Xem danh sách resource
R5.list_resources()                  # All 157 / Tất cả 157
R5.list_resources("medications")     # By category / Theo nhóm
```

### 2. Convert V2.x → FHIR R5 / Chuyển đổi V2 → R5

```python
from brightohir import v2_to_r5, V2Converter

# --- Quick convert / Chuyển nhanh ---
bundle = v2_to_r5(adt_a01_string)

# --- Full control / Kiểm soát đầy đủ ---
conv = V2Converter()
bundle = conv.convert(adt_a01_string)

# Extract individual resources / Trích xuất từng resource
patient   = conv.extract_resource("Patient")
encounter = conv.extract_resource("Encounter")
obs_list  = conv.extract_all("Observation")       # All observations
allergies = conv.extract_all("AllergyIntolerance") # All allergies
coverage  = conv.extract_resource("Coverage")      # Insurance
specimen  = conv.extract_resource("Specimen")      # Lab specimen
```

**Supported V2 segments (19 converters) / Các segment V2 được hỗ trợ:**

| Segment | → FHIR R5 Resource | Key fields mapped |
|---|---|---|
| MSH | MessageHeader | event, source, destination |
| PID | Patient | identifier, name, DOB, gender, address, telecom, marital status, death |
| PV1 | Encounter | class, admit/discharge dates, disposition |
| NK1 | RelatedPerson | name, relationship, address, phone |
| IN1 | Coverage | plan, company, effective dates, policy number, subscriber |
| GT1 | Account | guarantor name, address, phone |
| AL1 | AllergyIntolerance | type, category, code, severity, reaction, onset |
| DG1 | Condition | diagnosis code, date, type |
| ORC | ServiceRequest | order control, placer/filler IDs, provider, status |
| OBR | DiagnosticReport | service ID, observation date, result status, provider |
| OBX | Observation | code, value (NM/ST/CWE/DT), units, interpretation, status, reference range |
| RXA | Immunization | vaccine code, date, dose, lot number, status |
| RXE | MedicationRequest | give code, dose, units, dispense amount, refills |
| RXO | MedicationRequest | requested give code, dose, dispense amount |
| RXD | MedicationDispense | dispense code, amount, date, prescription number |
| SPM | Specimen | type, collection date, body site, availability |
| SCH | Appointment | IDs, reason, timing, status |
| TXA | DocumentReference | document type, format, date, provider, completion status |
| PRT | PractitionerRole | role, person, specialty, period |

**Supported V2 message types / Các loại message V2:**

ADT: A01, A02, A03, A04, A05, A08, A28, A31, A34, A40 · ORM_O01 · ORU_R01 · OML_O21 · OUL_R22 · RDE_O11 · RDS_O13 · RAS_O17 · VXU_V04 · MDM_T02 · SIU_S12–S15 · BAR_P01 · DFT_P03

### 3. Convert FHIR R5 → V2.x / Chuyển ngược R5 → V2

```python
from brightohir import r5_to_v2

# Single resource / Một resource
v2_msg = r5_to_v2(patient_dict, message_type="ADT_A01")

# Full bundle / Cả bundle
v2_msg = r5_to_v2(bundle_dict,
    message_type="ADT_A01",
    sending_app="LONG_CHAU_PMS",
    receiving_app="HOSPITAL_HIS",
    version="2.5.1")

# Output: proper V2 ER7 with MSH + EVN + all converted segments
```

**15 R5→V2 reverse converters:** Patient→PID, Encounter→PV1, Observation→OBX, AllergyIntolerance→AL1, Condition→DG1, Immunization→RXA, RelatedPerson→NK1, Coverage→IN1, ServiceRequest→ORC, MedicationRequest→RXE, MedicationDispense→RXD, Specimen→SPM, DocumentReference→TXA, DiagnosticReport→OBR, Appointment→SCH

### 4. R4 ↔ R5 migration / Migration R4 ↔ R5

```python
from brightohir import r4_to_r5, r5_to_r4, conversion_status

# R4 → R5 (handles all breaking changes automatically)
r5_encounter = r4_to_r5({
    "resourceType": "Encounter",
    "class": {"code": "AMB"},                           # Coding → CodeableConcept[]
    "hospitalization": {"dischargeDisposition": {"text": "home"}},  # → admission
    "classHistory": [{"class": {"code": "IMP"}}],       # → removed (use EncounterHistory)
})

r5_med = r4_to_r5({
    "resourceType": "MedicationRequest",
    "status": "active", "intent": "order",
    "medicationCodeableConcept": {"coding": [{"code": "387517004"}]},  # → medication.concept
    "reportedReference": {"reference": "Patient/1"},     # → informationSource
})

# R5 → R4 (graceful downgrade)
r4_back = r5_to_r4(r5_encounter)

# Check status / Kiểm tra trạng thái
info = conversion_status("Encounter")
# {"r5": "Encounter", "r4": "Encounter", "status": "restructured", "changes": [...]}

info = conversion_status("ActorDefinition")
# {"status": "new_r5"} — cannot downgrade to R4

info = conversion_status("RequestOrchestration")
# {"r4": "RequestGroup", "status": "renamed"}
```

**Handled breaking changes / Các breaking change được xử lý:**

| Resource | R4 → R5 change |
|---|---|
| Encounter | `class` Coding → CodeableConcept[], `hospitalization` → `admission`, classHistory/statusHistory removed |
| MedicationRequest | `medication[x]` → `medication` (CodeableReference), `reported[x]` → `informationSource` |
| MedicationAdministration | `medication[x]` → CodeableReference, `context` → `encounter` |
| MedicationDispense | `medication[x]` → CodeableReference, `context` → `encounter` |
| Condition | `recorder`/`asserter` → `participant[]` with type codes |
| AllergyIntolerance | `recorder`/`asserter` → `participant[]` |
| DocumentReference | `masterIdentifier` → `identifier`, `context` flattened |
| BodyStructure | `location`/`locationQualifier` → `includedStructure[]` |
| Consent | `scope` removed, `provision` restructured |
| Appointment | `class`, `subject`, `recurrenceTemplate` added |
| CarePlan | `activity.detail` removed → use RequestOrchestration |
| RequestOrchestration | Renamed from RequestGroup |

### 5. ACK/NAK responses / Phản hồi ACK/NAK

Every V2 message received **must** be acknowledged. brightohir generates proper ACK/NAK automatically.

*Mỗi message V2 nhận được **bắt buộc** phải trả ACK. brightohir tự động tạo ACK/NAK đúng chuẩn.*

```python
from brightohir import generate_ack, generate_batch_ack

# Accept / Chấp nhận
ack = generate_ack(incoming_v2_message)
# → MSH|...|ACK^A01^ACK|...|P|2.5.1\rMSA|AA|CTRL123\r

# Error / Lỗi
nak = generate_ack(incoming_v2_message,
    ack_code="AE",
    error_msg="Patient not found in system",
    error_code="204")
# → MSH|...\rMSA|AE|CTRL123|Patient not found\rERR|^^^204|E||Patient not found\r

# Reject / Từ chối
nak = generate_ack(incoming_v2_message, ack_code="AR", error_msg="Invalid message format")

# Batch ACK / ACK hàng loạt
batch = generate_batch_ack(
    [msg1, msg2, msg3],
    results=[
        {"ack_code": "AA"},
        {"ack_code": "AE", "error_msg": "Duplicate patient"},
        {"ack_code": "AA"},
    ])
```

### 6. PII masking / Che dấu thông tin cá nhân

HIPAA, GDPR, and Vietnamese Cybersecurity Law (86/2015/QH13) require PII protection. brightohir masks PII in both V2 and FHIR formats.

*Luật An ninh mạng VN (86/2015/QH13), HIPAA, GDPR đều yêu cầu bảo vệ PII. brightohir che dấu PII ở cả V2 lẫn FHIR.*

```python
from brightohir import mask_v2, mask_fhir, mask_bundle
from brightohir.security import PIIMasker

# Quick mask — default redact / Che nhanh — mặc định xóa
masked_v2 = mask_v2(raw_v2_message)
# PID|1||[REDACTED]|...|[REDACTED]^[REDACTED]||[REDACTED]|...

masked_patient = mask_fhir(patient_dict)
# {"name": [{"family": "[REDACTED]", "given": ["[REDACTED]"]}], ...}

masked_bundle = mask_bundle(fhir_bundle)

# Hash strategy — deterministic, linkable / Băm — xác định, liên kết được
masker = PIIMasker(strategy="hash", salt="your-secret-salt-2026")
m1 = masker.mask_fhir(patient1)
m2 = masker.mask_fhir(patient1)  # Same input → same hash

# Pseudonym — fake but structurally valid / Giả danh — giả nhưng đúng cấu trúc
masked = PIIMasker(strategy="pseudonym").mask_v2(v2_msg)
# PID|...|PERSON_A3F21B^PERSON_8C4E02||ID_7B2F9A01|...

# Partial — keep first/last chars / Che một phần
masked = PIIMasker(strategy="partial").mask_fhir(patient)
# {"name": [{"family": "N****n", "given": ["V**A"]}]}
```

**What gets masked / Những gì bị che:**

| V2 Segments | Fields masked |
|---|---|
| PID | Identifier, name, DOB, sex, address, phone, SSN, driver's license |
| NK1 | Name, address, phone, SSN |
| GT1 | Name, address, phone, SSN |
| IN1/IN2 | Name, DOB, address, subscriber ID |

| FHIR Resources | Fields masked |
|---|---|
| Patient | identifier, name, telecom, gender, birthDate, address, photo, deceased |
| RelatedPerson | identifier, name, telecom, address, birthDate |
| Practitioner | identifier, name, telecom, address, birthDate |
| Coverage | identifier, subscriberId, beneficiary |

---

## Production deployment — Triển khai production

### Setting up the MLLP listener / Cài đặt MLLP listener

This is how you receive V2 messages from hospital HIS systems over TCP. MLLP (Minimal Lower Layer Protocol) is the standard transport for HL7 V2 — it wraps each message in `<VT>message<FS><CR>` framing over raw TCP.

*Đây là cách nhận V2 messages từ HIS bệnh viện qua TCP. MLLP là giao thức truyền tải chuẩn cho V2 — bọc mỗi message trong frame `<VT>message<FS><CR>` trên TCP thuần.*

```python
# server.py — Long Châu MLLP Integration Engine
from brightohir import v2_to_r5, generate_ack
from brightohir.transport import MLLPServer
import logging

logging.basicConfig(level=logging.INFO)

def handle_message(raw_v2: str) -> str:
    """Process incoming V2 message, return ACK/NAK."""
    try:
        # Convert to FHIR R5
        bundle = v2_to_r5(raw_v2)

        # Your business logic here / Logic nghiệp vụ tại đây
        for entry in bundle["entry"]:
            resource = entry["resource"]
            store_to_database(resource)  # your function
            push_to_fhir_server(resource)  # your function

        # Success → ACK
        return generate_ack(raw_v2, ack_code="AA")

    except Exception as e:
        logging.error(f"Processing failed: {e}")
        # Error → NAK
        return generate_ack(raw_v2, ack_code="AE",
            error_msg=str(e)[:200],
            error_code="500")

# Start server / Khởi động server
server = MLLPServer(
    host="0.0.0.0",       # Listen on all interfaces / Lắng nghe tất cả interface
    port=2575,             # Standard HL7 port / Port chuẩn HL7
    handler=handle_message,
    max_connections=50,    # Concurrent connections / Kết nối đồng thời
    timeout=60.0,          # Per-connection timeout / Timeout mỗi kết nối
)

# Blocking mode / Chế độ chặn
server.start()

# Or background mode / Hoặc chế độ nền
# thread = server.start_background()
# ... do other work ...
# server.stop()
```

### Network & firewall configuration / Cấu hình mạng & firewall

```
┌──────────────────┐         TCP/2575          ┌──────────────────┐
│  Hospital HIS    │ ──────────────────────────▶│  brightohir      │
│  (V2 sender)     │                            │  MLLP Server     │
│  IP: 10.0.1.100  │ ◀────────────────────────  │  IP: 10.0.2.50   │
│                  │         ACK/NAK            │  Port: 2575      │
└──────────────────┘                            └──────────────────┘
```

**Firewall rules / Quy tắc firewall:**
```bash
# Allow inbound on HL7 port from hospital network only
# Cho phép kết nối đến port HL7 chỉ từ mạng bệnh viện
sudo ufw allow from 10.0.1.0/24 to any port 2575 proto tcp

# Or with iptables
sudo iptables -A INPUT -s 10.0.1.0/24 -p tcp --dport 2575 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 2575 -j DROP
```

**Security checklist / Danh sách bảo mật:**

- [ ] MLLP port (2575) restricted to known hospital IPs only — *Port MLLP chỉ mở cho IP bệnh viện đã biết*
- [ ] TLS termination via reverse proxy (nginx/HAProxy) in front of MLLP — *TLS qua reverse proxy phía trước*
- [ ] PII masking enabled for all logged messages — *Che PII cho mọi message được log*
- [ ] ACK timeout configured (default 60s) — *Timeout ACK đã cấu hình*
- [ ] Monitor: log all `AE`/`AR` responses for alerting — *Giám sát: log mọi phản hồi AE/AR để cảnh báo*
- [ ] Rate limiting at firewall level — *Giới hạn tốc độ ở tầng firewall*
- [ ] Separate VLAN for HL7 traffic — *VLAN riêng cho traffic HL7*

### Sending V2 messages to external systems / Gửi V2 đến hệ thống bên ngoài

```python
from brightohir import r5_to_v2
from brightohir.transport import MLLPClient

# Convert FHIR to V2 / Chuyển FHIR sang V2
v2_msg = r5_to_v2(fhir_bundle,
    message_type="ADT_A08",        # Update patient
    sending_app="LONG_CHAU_PMS",
    receiving_app="HOSPITAL_HIS",
    version="2.5.1")

# Send via MLLP / Gửi qua MLLP
with MLLPClient("hospital-his.local", 2575, timeout=30) as client:
    ack_response = client.send(v2_msg)
    if "AA" in ack_response:
        print("Accepted by hospital")
    elif "AE" in ack_response:
        print("Hospital reported error — retry or escalate")
```

### Running as a service / Chạy như service

```bash
# systemd service file: /etc/systemd/system/brightohir-mllp.service
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
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable brightohir-mllp
sudo systemctl start brightohir-mllp
sudo journalctl -u brightohir-mllp -f  # Watch logs / Xem log
```

---

## Other use cases — Các cách dùng khác

### FHIR REST API integration / Tích hợp FHIR REST API

```python
# pip install brightohir[client]
from brightohir import R5
from fhirpy import SyncFHIRClient

client = SyncFHIRClient("https://fhir.longchau.vn/r5", authorization="Bearer TOKEN")

# Create patient on FHIR server / Tạo bệnh nhân trên FHIR server
patient = R5.create("Patient", active=True, name=[{"family": "Nguyen"}], gender="male")
fhir_patient = client.resource("Patient", **R5.to_dict(patient))
fhir_patient.save()

# Search / Tìm kiếm
results = client.resources("Patient").search(name="Nguyen").limit(10).fetch()
```

### Batch file conversion / Chuyển đổi hàng loạt

```python
from brightohir import v2_to_r5
from pathlib import Path
import json

input_dir = Path("incoming_v2/")
output_dir = Path("converted_fhir/")
output_dir.mkdir(exist_ok=True)

for f in input_dir.glob("*.hl7"):
    raw = f.read_text()
    bundle = v2_to_r5(raw)
    out = output_dir / f"{f.stem}.json"
    out.write_text(json.dumps(bundle, indent=2, ensure_ascii=False))
    print(f"Converted {f.name} → {len(bundle['entry'])} resources")
```

### Data migration R4 → R5 / Migration dữ liệu R4 → R5

```python
from brightohir import r4_to_r5
import json

# Read existing R4 NDJSON export
with open("r4_export.ndjson") as f:
    for line in f:
        r4 = json.loads(line)
        r5 = r4_to_r5(r4)
        # POST to R5 server or write to file
```

### Audit logging with PII protection / Log kiểm toán với bảo vệ PII

```python
from brightohir import v2_to_r5, mask_bundle
import json, logging

logger = logging.getLogger("audit")

def process_and_log(v2_msg: str):
    bundle = v2_to_r5(v2_msg)

    # Log masked version for audit / Log bản đã che cho kiểm toán
    safe = mask_bundle(bundle, strategy="hash")
    logger.info(json.dumps(safe, ensure_ascii=False))

    # Process original (in memory only) / Xử lý bản gốc (chỉ trong RAM)
    return bundle
```

---

## Debugging — Gỡ lỗi

### Common issues / Các lỗi thường gặp

**1. `UnsupportedVersion: The version 2.5.1\nPID is not supported`**

Cause: V2 message uses `\n` line endings instead of `\r`.

*Nguyên nhân: Message V2 dùng `\n` thay vì `\r`.*

Fix: brightohir v1.1+ auto-normalizes this. If using raw hl7apy, replace `\n` with `\r` first.

```python
# brightohir handles this automatically — just pass the string
# brightohir tự xử lý — chỉ cần truyền chuỗi vào
bundle = v2_to_r5(triple_quoted_string)  # ✅ works with \n
```

**2. Segment not converting / Segment không được chuyển đổi**

Check if the segment is in the supported list:
```python
from brightohir.convert_v2 import _SEGMENT_CONVERTERS
print(list(_SEGMENT_CONVERTERS.keys()))
# ['MSH', 'PID', 'PV1', 'OBX', 'AL1', 'DG1', 'RXA', 'NK1', 'IN1', 'GT1',
#  'ORC', 'OBR', 'RXE', 'RXD', 'RXO', 'SPM', 'SCH', 'TXA', 'PRT']
```

**3. Validation errors / Lỗi validation**

```python
from brightohir import R5

# Check what's wrong / Kiểm tra lỗi gì
errors = R5.validate("Observation", my_data)
for e in errors:
    print(e)
```

**4. V2 field not mapped / Trường V2 không được map**

Use `V2Converter` for step-by-step inspection:

```python
from brightohir import V2Converter
import json

conv = V2Converter()
bundle = conv.convert(v2_message)

# Inspect each extracted resource / Kiểm tra từng resource được trích xuất
for rt in ["Patient", "Encounter", "Observation", "AllergyIntolerance"]:
    resources = conv.extract_all(rt)
    print(f"\n{rt}: {len(resources)} found")
    for r in resources:
        print(json.dumps(r, indent=2, ensure_ascii=False))
```

**5. R4→R5 conversion — checking what changed / Kiểm tra thay đổi R4→R5**

```python
from brightohir import conversion_status

info = conversion_status("Encounter")
print(f"Status: {info['status']}")
for action, field, detail in info['changes']:
    print(f"  {action}: {field} — {detail}")
```

**6. MLLP connection issues / Lỗi kết nối MLLP**

```python
import logging
logging.basicConfig(level=logging.DEBUG)
# brightohir.transport logs all connect/disconnect/send/receive events
```

```bash
# Test MLLP connectivity from command line
# Kiểm tra kết nối MLLP từ dòng lệnh
echo -e "\x0bMSH|^~\&|T|T|T|T|20260322||ADT^A01|1|P|2.5\rPID|1||999\r\x1c\x0d" | nc -w5 hospital-his.local 2575
```

---

## Architecture — Kiến trúc

```
brightohir/
├── __init__.py          # Public API — 30 exports
├── r5.py                # R5 factory: create/validate/serialize 157 resources
├── convert_r4r5.py      # R4 ↔ R5: 59 resource transforms, 10 restructured handlers
├── convert_v2.py        # V2 ↔ R5: 19 V2→R5 + 15 R5→V2 converters
│                        #           + message normalizer + manual fallback parser
├── registry.py          # Standards data: 203 total mappings
│                        #   157 R5 resources, 57 segment maps, 25 message maps,
│                        #   39 datatype maps, 23 vocab maps, 59 R4↔R5 diffs
├── ack.py               # ACK/NAK generator: AA/AE/AR + batch + ERR segment
├── transport.py         # MLLP: MLLPServer (threaded TCP) + MLLPClient
├── security.py          # PII masking: 4 strategies, dual V2+FHIR
├── mappings/            # YAML config extension point
└── py.typed             # PEP 561 marker
```

---

## Limitations & roadmap — Hạn chế & kế hoạch

### Current limitations / Hạn chế hiện tại

| Area | Limitation | Workaround |
|---|---|---|
| V2 segments | 19 of ~120 V2 segment types implemented. Remaining segments (e.g. RXR, AIG, AIL, AIP, AIS, IN2, IN3, PD1, ARV, SFT, UAC, ACC) pass through unconverted. | Use `_SEGMENT_CONVERTERS` registry to add custom converters. |
| R5→V2 reverse | 15 of 19 V2→R5 converters have reverse. Missing: Account→GT1, PractitionerRole→PRT. | Build V2 segments manually from FHIR dict. |
| MLLP | No built-in TLS. | Use TLS-terminating reverse proxy (nginx, HAProxy, stunnel). |
| Vocabulary | 23 V2 table→FHIR system mappings. Local code systems need custom mapping. | Extend `V2_TABLE_TO_FHIR_SYSTEM` dict. |
| Z-segments | Custom Z-segments are ignored during conversion. | Pre-process Z-segments before calling `v2_to_r5()`. |
| FHIR operations | No `$validate`, `$process-message`, `$everything` support. | Use `fhirpy` client directly for FHIR operations. |

### Roadmap / Kế hoạch phát triển

- **v1.2** — Remaining high-use V2 segments (RXR, PD1, IN2, IN3, ARV, AIG/AIL/AIP/AIS)
- **v1.3** — Z-segment extension framework, custom mapping YAML loader
- **v1.4** — CDA ↔ FHIR R5 conversion (Vietnamese hospital discharge summaries)
- **v2.0** — Async MLLP server (asyncio), WebSocket transport, FHIR Subscription support

---

## Testing — Kiểm thử

```bash
# Run all 84 tests / Chạy toàn bộ 84 test
pytest tests/ -v

# Run specific module / Chạy module cụ thể
pytest tests/test_sdk.py -v    # Core: R5, R4↔R5, V2→R5 basics (37 tests)
pytest tests/test_v11.py -v    # v1.1: new segments, ACK, PII, MLLP (47 tests)

# With coverage / Với coverage
pytest tests/ --cov=brightohir --cov-report=term-missing

# Quick smoke test / Test nhanh
python -c "from brightohir import *; print(f'v{__version__} OK — {len(ALL_R5_RESOURCES)} resources')"
```

---

## License — Giấy phép

**MIT License**

Copyright (c) 2026 BrighTO Technology / Hatto AI

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED.

---

## Contact — Liên hệ

**BrighTO Technology / Hatto AI**

- Email: nguyen@brighto.ai | nguyen@hatto.com
- GitHub: [github.com/thusinh1969/brightohir](https://github.com/thusinh1969/brightohir)
- Issues: [github.com/thusinh1969/brightohir/issues](https://github.com/thusinh1969/brightohir/issues)

---

*Built for Long Châu Pharmacy Group (FPT Retail) — 2,500+ stores, 250 vaccination centers, serving millions of patients across Vietnam.*
*Được xây dựng cho Nhà thuốc Long Châu (FPT Retail) — 2.500+ cửa hàng, 250 trung tâm tiêm chủng, phục vụ hàng triệu bệnh nhân trên khắp Việt Nam.*