# Conversion reference — all supported mappings (v2.0.0)
# Tham chiếu chuyển đổi — tất cả mapping (v2.0.0)

---

## 1. V2→R5 segment creators (31)
| # | Segment | → FHIR R5 | Tier |
|---|---|---|---|
| 1 | **ACC** | Account | 2 |
| 2 | **AFF** | Organization | 3 |
| 3 | **AL1** | AllergyIntolerance | 1 |
| 4 | **ARV** | Consent | 2 |
| 5 | **DG1** | Condition | 1 |
| 6 | **ERR** | OperationOutcome | 3 |
| 7 | **EVN** | Provenance | 2 |
| 8 | **GT1** | Account | 1 |
| 9 | **IAM** | AllergyIntolerance | 2 |
| 10 | **IN1** | Coverage | 1 |
| 11 | **MSH** | MessageHeader | 1 |
| 12 | **NK1** | RelatedPerson | 1 |
| 13 | **OBR** | DiagnosticReport | 1 |
| 14 | **OBX** | Observation | 1 |
| 15 | **ORC** | ServiceRequest | 1 |
| 16 | **ORG** | Organization | 3 |
| 17 | **PID** | Patient | 1 |
| 18 | **PR1** | Procedure | 2 |
| 19 | **PRT** | PractitionerRole | 1 |
| 20 | **PV1** | Encounter | 1 |
| 21 | **QPD** | Parameters | 3 |
| 22 | **RXA** | Immunization | 1 |
| 23 | **RXD** | MedicationDispense | 1 |
| 24 | **RXE** | MedicationRequest | 1 |
| 25 | **RXG** | MedicationAdministration | 2 |
| 26 | **RXO** | MedicationRequest | 1 |
| 27 | **SCH** | Appointment | 1 |
| 28 | **SFT** | Device | 2 |
| 29 | **SPM** | Specimen | 1 |
| 30 | **STF** | Practitioner | 3 |
| 31 | **TXA** | DocumentReference | 1 |

## 2. V2→R5 segment enrichers (20)
| # | Segment | Enriches | Tier |
|---|---|---|---|
| 1 | **AIG** | Appointment | 2 |
| 2 | **AIL** | Appointment | 2 |
| 3 | **AIP** | Appointment | 2 |
| 4 | **AIS** | Appointment | 2 |
| 5 | **CER** | Practitioner | 3 |
| 6 | **EDU** | Practitioner | 3 |
| 7 | **IN2** | Coverage | 2 |
| 8 | **IN3** | Coverage | 2 |
| 9 | **LAN** | Practitioner | 3 |
| 10 | **MSA** | MessageHeader | 3 |
| 11 | **NTE** | last clinical | 2 |
| 12 | **PD1** | Patient | 2 |
| 13 | **PV2** | Encounter | 2 |
| 14 | **ROL** | Encounter | 2 |
| 15 | **RXC** | MedicationRequest | 2 |
| 16 | **RXR** | MedicationRequest/Immunization | 2 |
| 17 | **SAC** | Specimen | 2 |
| 18 | **TQ1** | ServiceRequest/MedicationRequest | 2 |
| 19 | **TQ2** | ServiceRequest | 2 |
| 20 | **UAC** | MessageHeader | 3 |

## 3. R5→V2 reverse converters (23)
| # | FHIR R5 | → V2 | Tier |
|---|---|---|---|
| 1 | **AllergyIntolerance** | AL1 | 1 |
| 2 | **Appointment** | SCH | 1 |
| 3 | **Condition** | DG1 | 1 |
| 4 | **Consent** | ARV | 2/3 |
| 5 | **Coverage** | IN1 | 1 |
| 6 | **Device** | SFT | 2/3 |
| 7 | **DiagnosticReport** | OBR | 1 |
| 8 | **DocumentReference** | TXA | 1 |
| 9 | **Encounter** | PV1 | 1 |
| 10 | **Immunization** | RXA | 1 |
| 11 | **MedicationAdministration** | RXG | 2/3 |
| 12 | **MedicationDispense** | RXD | 1 |
| 13 | **MedicationRequest** | RXE | 1 |
| 14 | **Observation** | OBX | 1 |
| 15 | **OperationOutcome** | ERR | 2/3 |
| 16 | **Organization** | ORG | 2/3 |
| 17 | **Patient** | PID | 1 |
| 18 | **Practitioner** | STF | 2/3 |
| 19 | **Procedure** | PR1 | 2/3 |
| 20 | **Provenance** | EVN | 2/3 |
| 21 | **RelatedPerson** | NK1 | 1 |
| 22 | **ServiceRequest** | ORC | 1 |
| 23 | **Specimen** | SPM | 1 |

## 4. R4↔R5 transforms (59)
See registry.py — 11 restructured, 20 new-in-R5, 1 renamed.

## 5. V2 message structures: 25
## 6. V2 datatype maps: 39
## 7. V2 vocabulary maps: 23
## 8. V2 segment registry: 57

**Grand total: 277 mappings**