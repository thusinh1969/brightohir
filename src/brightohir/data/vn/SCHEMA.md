# Vietnamese Healthcare Code Systems — Data Schema
# Hệ thống mã y tế Việt Nam — Đặc tả dữ liệu
#
# Format: JSONL (one JSON object per line)
# Encoding: UTF-8
# Source authority: Bộ Y tế (MOH) — QĐ 4469/QĐ-BYT, QĐ 7603/QĐ-BYT, QĐ 824/QĐ-BYT

## File structure / Cấu trúc thư mục
#
# data/vn/
# ├── icd10_vn.jsonl          # ICD-10 VN (~14,400 codes)
# ├── icd10_yhct.jsonl         # Y học cổ truyền U-codes (~2,000)
# ├── drugs_western.jsonl      # Thuốc tân dược (~20,000+)
# ├── drugs_traditional.jsonl  # Thuốc YHCT (~5,000+)
# ├── lab_tests.jsonl          # Xét nghiệm (~3,000+)
# ├── procedures.jsonl         # Dịch vụ kỹ thuật (~8,000+)
# ├── medical_supplies.jsonl   # Vật tư y tế (~10,000+)
# ├── blood_products.jsonl     # Máu & chế phẩm (~200)
# ├── bhyt_objects.jsonl       # Đối tượng BHYT (~50)
# ├── hospital_tiers.jsonl     # Hạng bệnh viện + mã khám (~100)
# └── provinces.jsonl          # Mã tỉnh/thành (63 tỉnh)

## ═══════════════════════════════════════════════════════════════════
## SCHEMA DEFINITIONS — Mỗi file JSONL, mỗi dòng 1 JSON object
## ═══════════════════════════════════════════════════════════════════

## 1. icd10_vn.jsonl — Mã bệnh ICD-10 Việt Nam
## Source: icd.kcb.vn / QĐ 4469/QĐ-BYT
#
# {"code": "J06.9", "display_vi": "Nhiễm trùng hô hấp trên cấp tính, không đặc hiệu", "display_en": "Acute upper respiratory infection, unspecified", "chapter": "X", "chapter_name": "Bệnh hệ hô hấp", "block": "J00-J06", "block_name": "Nhiễm trùng hô hấp trên cấp tính", "parent": "J06", "level": 4, "billable": true}
# {"code": "E11.9", "display_vi": "Đái tháo đường typ 2, không có biến chứng", "display_en": "Type 2 diabetes mellitus without complications", "chapter": "IV", "chapter_name": "Bệnh nội tiết, dinh dưỡng và chuyển hóa", "block": "E10-E14", "block_name": "Đái tháo đường", "parent": "E11", "level": 4, "billable": true}

## 2. icd10_yhct.jsonl — Mã bệnh Y học cổ truyền
## Source: QĐ 6061/QĐ-BYT
#
# {"code": "U55.621", "icd10_ref": "G47", "display_vi": "Thất miên", "display_modern": "Rối loạn giấc ngủ", "display_en": "Sleep disorder", "chapter_yhct": "Thần kinh"}
# {"code": "U58.481", "icd10_ref": "I50", "display_vi": "Tâm quý", "display_modern": "Suy tim", "display_en": "Heart failure", "chapter_yhct": "Tim mạch"}

## 3. drugs_western.jsonl — Thuốc tân dược
## Source: QĐ 7603/QĐ-BYT Phụ lục 5 + TT 20/2022/TT-BYT
#
# {"code": "TD.001234", "atc": "N02BE01", "active_ingredient": "Paracetamol", "display_vi": "Paracetamol 500mg viên nén", "display_en": "Paracetamol 500mg tablet", "strength": "500mg", "form": "tablet", "route": "oral", "unit": "viên", "bhyt_covered": true, "bhyt_ratio": 100, "manufacturer": "Dược Hậu Giang", "country": "VN"}
# {"code": "TD.005678", "atc": "J01CA04", "active_ingredient": "Amoxicillin", "display_vi": "Amoxicillin 500mg viên nang", "display_en": "Amoxicillin 500mg capsule", "strength": "500mg", "form": "capsule", "route": "oral", "unit": "viên", "bhyt_covered": true, "bhyt_ratio": 100, "manufacturer": "Pymepharco", "country": "VN"}

## 4. drugs_traditional.jsonl — Thuốc & vị thuốc YHCT
## Source: QĐ 7603/QĐ-BYT Phụ lục 6
#
# {"code": "YT.000123", "display_vi": "Hoàng kỳ", "display_en": "Astragalus", "latin": "Astragalus membranaceus", "part_used": "rễ", "form": "sống", "processing": "sao vàng", "bhyt_covered": true}

## 5. lab_tests.jsonl — Xét nghiệm
## Source: QĐ 7603/QĐ-BYT Phụ lục 11
#
# {"code": "XN.001", "loinc": "718-7", "display_vi": "Hemoglobin (Hb)", "display_en": "Hemoglobin", "category": "hematology", "unit": "g/dL", "ref_low": 12.0, "ref_high": 16.0, "ref_note": "Nữ: 12-16, Nam: 13.5-17.5", "specimen": "blood", "bhyt_covered": true, "bhyt_price": 25000}
# {"code": "XN.002", "loinc": "2345-7", "display_vi": "Glucose máu", "display_en": "Blood glucose", "category": "biochemistry", "unit": "mmol/L", "ref_low": 3.9, "ref_high": 6.1, "ref_note": "Lúc đói", "specimen": "blood", "bhyt_covered": true, "bhyt_price": 20000}

## 6. procedures.jsonl — Dịch vụ kỹ thuật
## Source: QĐ 7603/QĐ-BYT Phụ lục 1
#
# {"code": "DVKT.001234", "display_vi": "Phẫu thuật cắt ruột thừa nội soi", "display_en": "Laparoscopic appendectomy", "category": "surgery", "tier_required": 2, "bhyt_covered": true, "bhyt_price": 5500000, "notes": "Hạng 2 trở lên"}
# {"code": "DVKT.002345", "display_vi": "Siêu âm bụng tổng quát", "display_en": "Abdominal ultrasound", "category": "imaging", "tier_required": 4, "bhyt_covered": true, "bhyt_price": 100000}

## 7. medical_supplies.jsonl — Vật tư y tế
## Source: QĐ 7603/QĐ-BYT Phụ lục 8
#
# {"code": "VT.001234", "display_vi": "Bơm tiêm 5ml", "display_en": "Syringe 5ml", "category": "consumable", "unit": "cái", "bhyt_covered": true, "bhyt_price": 3000}

## 8. blood_products.jsonl — Máu và chế phẩm máu
## Source: QĐ 7603/QĐ-BYT Phụ lục 9
#
# {"code": "MAU.001", "display_vi": "Hồng cầu lắng", "display_en": "Packed red blood cells", "unit": "đơn vị", "storage": "2-6°C", "shelf_life_days": 42, "bhyt_covered": true}

## 9. bhyt_objects.jsonl — Đối tượng BHYT
## Source: QĐ 7603 + QĐ 2010/QĐ-BYT (2025)
#
# {"code": "1", "display_vi": "Người lao động", "display_en": "Employee", "contribution_rate": 4.5, "employer_share": 3.0, "employee_share": 1.5, "copay_percent": 20}
# {"code": "2", "display_vi": "Hưu trí", "display_en": "Retiree", "contribution_rate": 4.5, "employer_share": 4.5, "employee_share": 0, "copay_percent": 5}
# {"code": "3", "display_vi": "Trẻ em dưới 6 tuổi", "display_en": "Children under 6", "contribution_rate": 0, "employer_share": 0, "employee_share": 0, "copay_percent": 0}
# {"code": "4", "display_vi": "Hộ nghèo", "display_en": "Poor household", "contribution_rate": 0, "employer_share": 0, "employee_share": 0, "copay_percent": 5}
# {"code": "5", "display_vi": "Học sinh, sinh viên", "display_en": "Student", "contribution_rate": 4.5, "employer_share": 3.0, "employee_share": 1.5, "copay_percent": 20}

## 10. hospital_tiers.jsonl — Hạng bệnh viện
## Source: Nghị định 146/2018/NĐ-CP + QĐ 7603
#
# {"code": "HANG_DAC_BIET", "tier": 0, "display_vi": "Hạng đặc biệt", "display_en": "Special tier", "examples": "BV Bạch Mai, Chợ Rẫy", "exam_price": 39000}
# {"code": "HANG_1", "tier": 1, "display_vi": "Hạng I", "display_en": "Tier 1", "examples": "BV Đa khoa tỉnh", "exam_price": 35000}
# {"code": "HANG_2", "tier": 2, "display_vi": "Hạng II", "display_en": "Tier 2", "examples": "BV quận/huyện lớn", "exam_price": 29000}
# {"code": "HANG_3", "tier": 3, "display_vi": "Hạng III", "display_en": "Tier 3", "examples": "BV quận/huyện nhỏ", "exam_price": 25000}
# {"code": "HANG_4", "tier": 4, "display_vi": "Hạng IV", "display_en": "Tier 4", "examples": "Trạm y tế xã, phòng khám tư", "exam_price": 22000}

## 11. provinces.jsonl — Mã tỉnh/thành (for patient address, BHXH routing)
#
# {"code": "01", "display_vi": "Thành phố Hà Nội", "display_en": "Hanoi", "region": "north"}
# {"code": "79", "display_vi": "Thành phố Hồ Chí Minh", "display_en": "Ho Chi Minh City", "region": "south"}
# {"code": "48", "display_vi": "Thành phố Đà Nẵng", "display_en": "Da Nang", "region": "central"}

## ═══════════════════════════════════════════════════════════════════
## COMMON FIELDS across all files / Các trường chung
## ═══════════════════════════════════════════════════════════════════
#
# Required:
#   code        — string, unique within file, the official MOH/BHXH code
#   display_vi  — string, Vietnamese display name (UTF-8)
#
# Optional (nhưng nên có):
#   display_en  — string, English display name
#   bhyt_covered — bool, BHYT có chi trả không
#   bhyt_price   — int, giá BHYT (VND), 0 if not applicable
#   bhyt_ratio   — int, tỷ lệ chi trả (%), 0-100
#
# Naming convention:
#   - File: lowercase, underscore separated
#   - Code prefix: ICD10 codes as-is (J06.9), MOH codes keep prefix (TD., XN., DVKT., VT., MAU.)
#   - All dates: YYYY-MM-DD
#   - All prices: VND integer (no decimals)

## ═══════════════════════════════════════════════════════════════════
## FHIR R5 MAPPING — Mỗi file map vào CodeSystem nào
## ═══════════════════════════════════════════════════════════════════
#
# icd10_vn.jsonl          → CodeSystem: https://icd.kcb.vn/ICD-10-VN
# icd10_yhct.jsonl         → CodeSystem: https://icd.kcb.vn/YHCT
# drugs_western.jsonl      → CodeSystem: https://dmdc.moh.gov.vn/thuoc-tan-duoc
# drugs_traditional.jsonl  → CodeSystem: https://dmdc.moh.gov.vn/thuoc-yhct
# lab_tests.jsonl          → CodeSystem: https://dmdc.moh.gov.vn/xet-nghiem
# procedures.jsonl         → CodeSystem: https://dmdc.moh.gov.vn/dvkt
# medical_supplies.jsonl   → CodeSystem: https://dmdc.moh.gov.vn/vtyt
# blood_products.jsonl     → CodeSystem: https://dmdc.moh.gov.vn/mau
# bhyt_objects.jsonl       → CodeSystem: https://baohiemxahoi.gov.vn/doi-tuong
# hospital_tiers.jsonl     → CodeSystem: https://dmdc.moh.gov.vn/hang-bv
# provinces.jsonl          → CodeSystem: https://danhmuchanhchinh.gso.gov.vn
#
# NOTE: These URIs are proposed OIDs for brightohir. Official FHIR URIs
# for Vietnamese code systems do not exist yet as of March 2026.
# When MOH publishes official FHIR IG for Vietnam, update these URIs.
