#!/usr/bin/env python3
"""
brightohir SDK — Interactive Demo
==================================
Run:      python demo.py
Jupyter:  Copy cells between # %% markers
"""
# %% Setup
import json
from brightohir import (
    R5, v2_to_r5, r5_to_v2, r4_to_r5, r5_to_r4,
    V2Converter, conversion_status,
    ALL_R5_RESOURCES, V2_SEGMENT_TO_FHIR, V2_MESSAGE_TO_FHIR, R4_TO_R5_MAP,
)
def pp(o):
    if hasattr(o, 'model_dump_json'): print(o.model_dump_json(indent=2, exclude_none=True))
    else: print(json.dumps(o, indent=2, ensure_ascii=False, default=str))
print(f"✅ brightohir — {len(ALL_R5_RESOURCES)} R5 resources\n")

# %% 2. Create R5 Resources
print("="*60, "\n📋 Create FHIR R5\n" + "="*60)
patient = R5.create("Patient", id="lc-001", active=True,
    name=[{"family": "Nguyễn", "given": ["Văn", "A"], "use": "official"}],
    gender="male", birthDate="1990-01-15",
    address=[{"line": ["123 Nguyễn Huệ"], "city": "Hồ Chí Minh", "country": "VN"}],
    telecom=[{"system": "phone", "value": "0901234567", "use": "mobile"}])
print("🧑 Patient:"); pp(patient)

obs = R5.create("Observation", id="obs-001", status="final",
    code={"coding": [{"system": "http://loinc.org", "code": "29463-7", "display": "Body Weight"}]},
    subject={"reference": "Patient/lc-001"},
    valueQuantity={"value": 72.5, "unit": "kg", "system": "http://unitsofmeasure.org", "code": "kg"})
print("\n📊 Observation:"); pp(obs)

med = R5.create("MedicationRequest", id="rx-001", status="active", intent="order",
    medication={"concept": {"coding": [{"system": "http://snomed.info/sct", "code": "387517004", "display": "Paracetamol"}]}},
    subject={"reference": "Patient/lc-001"},
    dosageInstruction=[{"text": "500mg x 3 lần/ngày sau ăn",
        "timing": {"repeat": {"frequency": 3, "period": 1, "periodUnit": "d"}},
        "doseAndRate": [{"doseQuantity": {"value": 500, "unit": "mg"}}]}])
print("\n💊 MedicationRequest:"); pp(med)

# %% 3. Bundle
print("\n" + "="*60, "\n📦 Bundle\n" + "="*60)
bundle = R5.bundle("transaction", [patient, obs, med])
d = R5.to_dict(bundle)
for e in d['entry']:
    print(f"  {e['resource']['resourceType']}/{e['resource'].get('id','?')}  [{e.get('request',{}).get('method','')}]")

# %% 4. Validate
print("\n" + "="*60, "\n✅ Validate\n" + "="*60)
print(f"Valid Patient:  {R5.validate('Patient', {'active': True})}")
print(f"Invalid Obs:    {len(R5.validate('Observation', {'status': 'BOGUS'}))} error(s)")

# %% 5. R4 ↔ R5
print("\n" + "="*60, "\n🔄 R4 ↔ R5\n" + "="*60)
r4_enc = {"resourceType": "Encounter", "id": "e1", "status": "in-progress",
    "class": {"system": "http://terminology.hl7.org/CodeSystem/v3-ActCode", "code": "AMB"},
    "hospitalization": {"dischargeDisposition": {"text": "home"}}}
r5_enc = r4_to_r5(r4_enc)
print(f"Encounter R4→R5: class={r5_enc['class']}")
print(f"  hospitalization → admission={r5_enc.get('admission')}")

r4_mr = {"resourceType": "MedicationRequest", "status": "active", "intent": "order",
    "medicationCodeableConcept": {"coding": [{"code": "387517004", "display": "Paracetamol"}]}}
r5_mr = r4_to_r5(r4_mr)
print(f"\nMedRequest R4→R5: medication={r5_mr['medication']}")
r4_back = r5_to_r4(r5_mr); r5_rt = r4_to_r5(r4_back)
print(f"Round-trip match: {r5_mr['medication'] == r5_rt['medication']}")

for rt in ["Encounter", "Patient", "ActorDefinition", "RequestOrchestration"]:
    i = conversion_status(rt); print(f"  {rt}: {i['status']}, r4={i.get('r4','N/A')}")

# %% 6. V2 → R5
print("\n" + "="*60, "\n📨 V2 → R5\n" + "="*60)
adt = """MSH|^~\\&|HATTO|LONG_CHAU|EHR|BVDK|20260322090000||ADT^A01^ADT_A01|MSG001|P|2.5.1
PID|1||LC-12345^^^LONG_CHAU^MR||NGUYEN^VAN A^B||19900115|M||2028-9|123 NGUYEN HUE^^HCM^VN^70000||0901234567
PV1|1|I|W^101^1^^^3||||12345^TRAN^BAC SI|||MED
AL1|1|DA|12345^ASPIRIN^RxNorm|SV|Rash
DG1|1||J06.9^Acute URTI^ICD10|||A
OBX|1|NM|29463-7^Body Weight^LN||72.5|kg|60-90||||F
OBX|2|NM|8310-5^Body Temp^LN||37.2|Cel|36.1-37.2||||F
OBX|3|NM|8480-6^Systolic BP^LN||125|mm[Hg]|90-120|H|||F"""

conv = V2Converter()
b = conv.convert(adt)
print(f"📦 {len(b['entry'])} resources:")
for e in b["entry"]:
    r = e["resource"]; rt = r["resourceType"]; x = ""
    if rt == "Patient":
        n = r.get("name",[{}])[0]; x = f" → {n.get('family','')} {n.get('given',[''])[0]}, {r.get('gender','?')}"
    elif rt == "Observation":
        c = r.get("code",{}).get("coding",[{}])[0].get("display","?")
        v = r.get("valueQuantity",{}); x = f" → {c}: {v.get('value','?')} {v.get('unit','')}"
    elif rt == "AllergyIntolerance":
        x = f" → {r.get('code',{}).get('coding',[{}])[0].get('display','?')}"
    elif rt == "Condition":
        x = f" → {r.get('code',{}).get('coding',[{}])[0].get('display','?')}"
    elif rt == "Encounter":
        cls = r.get("class",[{}])[0].get("coding",[{}])[0].get("code","?") if r.get("class") else "?"
        x = f" → class={cls}"
    print(f"  {rt}{x}")

# %% 7. R5 → V2
print("\n" + "="*60, "\n📤 R5 → V2\n" + "="*60)
v2 = r5_to_v2(b, message_type="ADT_A01", sending_app="LONG_CHAU", receiving_app="HIS")
for line in v2.split("\r"):
    if line.strip(): print(f"  {line}")

# %% 8. Full pipeline
print("\n" + "="*60, "\n🔁 V2→R5→R4→R5→V2\n" + "="*60)
r5b = v2_to_r5(adt)
r5p = next(e["resource"] for e in r5b["entry"] if e["resource"]["resourceType"]=="Patient")
r4p = r5_to_r4(r5p); r5p2 = r4_to_r5(r4p)
v2f = r5_to_v2(r5p2, message_type="ADT_A08")
print(f"V2→R5: {len(r5b['entry'])} res | R5→R4→R5: name={r5p2.get('name',[{}])[0].get('family','?')}")
for line in v2f.split("\r"):
    if line.strip(): print(f"  {line}")

# %% 9. Registry
print("\n" + "="*60, "\n📚 Registry\n" + "="*60)
print(f"R5: {len(ALL_R5_RESOURCES)} resources | V2 segments: {len(V2_SEGMENT_TO_FHIR)} | V2 messages: {len(V2_MESSAGE_TO_FHIR)} | R4↔R5: {len(R4_TO_R5_MAP)}")
print(f"\nNew R5: {', '.join(rt for rt,i in R4_TO_R5_MAP.items() if i['status']=='new_r5')}")
print(f"\nRestructured:")
for rt, i in R4_TO_R5_MAP.items():
    if i["status"]=="restructured":
        print(f"  {rt:30s} {', '.join(f'{c[0]}:{c[1]}' for c in i.get('changes',[])[:3])}")

print("\n✅ Done — brightohir v1.0.0")
