# Conversion reference — all supported mappings
# Tham chiếu chuyển đổi — tất cả mapping được hỗ trợ

---

## 1. V2 → FHIR R5 segment converters (19)
*Bộ chuyển đổi segment V2 → R5 (19 loại)*

These segments are **fully converted** with field-level mapping to validated FHIR R5 resources.

| # | V2 segment | → FHIR R5 resource | Key fields mapped |
|---|---|---|---|
| 1 | **AL1** | AllergyIntolerance | type, category, code, severity, reaction, onset |
| 2 | **DG1** | Condition | diagnosis code, date, type |
| 3 | **GT1** | Account | guarantor name, address, phone |
| 4 | **IN1** | Coverage | plan, company, effective dates, policy, subscriber |
| 5 | **MSH** | MessageHeader | event, source, destination |
| 6 | **NK1** | RelatedPerson | name, relationship, address, phone, contact role |
| 7 | **OBR** | DiagnosticReport | service ID, observation date, result status, provider |
| 8 | **OBX** | Observation | code, value (NM/ST/CWE/DT), units, interpretation, status, reference range |
| 9 | **ORC** | ServiceRequest | order control, placer/filler IDs, provider, status |
| 10 | **PID** | Patient | identifier, name, DOB, gender, address, telecom, marital status, death |
| 11 | **PRT** | PractitionerRole | role, person, specialty, period |
| 12 | **PV1** | Encounter | class, admit/discharge dates, disposition |
| 13 | **RXA** | Immunization | vaccine code, date, dose, lot number, status |
| 14 | **RXD** | MedicationDispense | dispense code, amount, date, prescription number |
| 15 | **RXE** | MedicationRequest | give code, dose, units, dispense amount, refills |
| 16 | **RXO** | MedicationRequest | requested give code, dose, dispense amount |
| 17 | **SCH** | Appointment | IDs, reason, timing, status |
| 18 | **SPM** | Specimen | type, collection date, body site, role, availability |
| 19 | **TXA** | DocumentReference | document type, format, date, provider, completion status |

## 2. FHIR R5 → V2 reverse converters (15)
*Bộ chuyển đổi ngược R5 → V2 (15 loại)*

| # | FHIR R5 resource | → V2 segment |
|---|---|---|
| 1 | **AllergyIntolerance** | AL1 |
| 2 | **Appointment** | SCH |
| 3 | **Condition** | DG1 |
| 4 | **Coverage** | IN1 |
| 5 | **DiagnosticReport** | OBR |
| 6 | **DocumentReference** | TXA |
| 7 | **Encounter** | PV1 |
| 8 | **Immunization** | RXA |
| 9 | **MedicationDispense** | RXD |
| 10 | **MedicationRequest** | RXE |
| 11 | **Observation** | OBX |
| 12 | **Patient** | PID |
| 13 | **RelatedPerson** | NK1 |
| 14 | **ServiceRequest** | ORC |
| 15 | **Specimen** | SPM |

## 3. R4 ↔ R5 resource transforms (59)
*Chuyển đổi resource R4 ↔ R5 (59 loại)*

| # | R5 resource | R4 name | Status | Changes |
|---|---|---|---|---|
| 1 | **Account** | Account | compatible | add: billingStatus; add: relatedAccount; add: balance |
| 2 | **ActorDefinition** | — | new_r5 | — |
| 3 | **AllergyIntolerance** | AllergyIntolerance | compatible | add: participant; remove: recorder; remove: asserter |
| 4 | **Appointment** | Appointment | restructured | add: class; add: subject; add: recurrenceId |
| 5 | **ArtifactAssessment** | — | new_r5 | — |
| 6 | **BiologicallyDerivedProductDispense** | — | new_r5 | — |
| 7 | **BodyStructure** | BodyStructure | restructured | add: includedStructure; remove: location; remove: locationQualifier |
| 8 | **Bundle** | Bundle | compatible | add: issues |
| 9 | **CarePlan** | CarePlan | restructured | remove: activity.detail; add: custodian |
| 10 | **CareTeam** | CareTeam | compatible | — |
| 11 | **Citation** | — | new_r5 | — |
| 12 | **Claim** | Claim | compatible | add: diagnosisSequence |
| 13 | **Composition** | Composition | compatible | add: url; add: version; add: name |
| 14 | **Condition** | Condition | restructured | rename: verificationStatus; add: participant; remove: recorder |
| 15 | **Consent** | Consent | restructured | remove: scope; rename: provision; add: regulatoryBasis |
| 16 | **Coverage** | Coverage | compatible | add: insurancePlan; add: paymentBy |
| 17 | **DeviceAssociation** | — | new_r5 | — |
| 18 | **DeviceDispense** | — | new_r5 | — |
| 19 | **DiagnosticReport** | DiagnosticReport | compatible | add: note; add: composition; add: supportingInfo |
| 20 | **DocumentReference** | DocumentReference | restructured | remove: masterIdentifier; rename: content.attachment; add: basedOn |
| 21 | **Encounter** | Encounter | restructured | remove: class; rename: hospitalization; add: virtualService |
| 22 | **EncounterHistory** | — | new_r5 | — |
| 23 | **EvidenceReport** | — | new_r5 | — |
| 24 | **FormularyItem** | — | new_r5 | — |
| 25 | **GenomicStudy** | — | new_r5 | — |
| 26 | **Goal** | Goal | compatible | — |
| 27 | **ImagingSelection** | — | new_r5 | — |
| 28 | **Immunization** | Immunization | compatible | add: administeredProduct; rename: performer |
| 29 | **InventoryItem** | — | new_r5 | — |
| 30 | **InventoryReport** | — | new_r5 | — |
| 31 | **Location** | Location | compatible | add: characteristic |
| 32 | **Medication** | Medication | compatible | add: definition; add: totalVolume |
| 33 | **MedicationAdministration** | MedicationAdministration | restructured | rename: medication[x]; rename: context; add: subPotentReason |
| 34 | **MedicationDispense** | MedicationDispense | restructured | rename: medication[x]; rename: context; add: notPerformedReason |
| 35 | **MedicationRequest** | MedicationRequest | restructured | rename: reported; rename: performer; add: device |
| 36 | **MedicationStatement** | MedicationStatement | restructured | rename: medication[x]; rename: statusReason; rename: reasonCode |
| 37 | **MessageHeader** | MessageHeader | compatible | — |
| 38 | **NutritionIntake** | — | new_r5 | — |
| 39 | **Observation** | Observation | compatible | add: triggeredBy; add: instantiates |
| 40 | **OperationOutcome** | OperationOutcome | compatible | — |
| 41 | **Organization** | Organization | compatible | add: description; add: qualification |
| 42 | **Patient** | Patient | compatible | add: communication.preferred |
| 43 | **Permission** | — | new_r5 | — |
| 44 | **Practitioner** | Practitioner | compatible | — |
| 45 | **PractitionerRole** | PractitionerRole | compatible | rename: availableTime |
| 46 | **Procedure** | Procedure | compatible | add: focus; rename: performer.onBehalfOf |
| 47 | **Provenance** | Provenance | compatible | — |
| 48 | **RelatedPerson** | RelatedPerson | compatible | — |
| 49 | **RequestOrchestration** | RequestGroup | renamed | — |
| 50 | **Requirements** | — | new_r5 | — |
| 51 | **Schedule** | Schedule | compatible | add: name |
| 52 | **ServiceRequest** | ServiceRequest | compatible | add: focus; add: bodyStructure |
| 53 | **Slot** | Slot | compatible | — |
| 54 | **Specimen** | Specimen | compatible | add: combined; add: role |
| 55 | **SubscriptionStatus** | — | new_r5 | — |
| 56 | **SubscriptionTopic** | — | new_r5 | — |
| 57 | **Task** | Task | compatible | add: requestedPerformer |
| 58 | **TestPlan** | — | new_r5 | — |
| 59 | **Transport** | — | new_r5 | — |

## 4. V2 message structures (25)
*Cấu trúc message V2 (25 loại)*

| # | Message | Name | V2 segments |
|---|---|---|---|
| 1 | **ADT_A01** | Admit/Visit Notification | MSH, EVN, PID, PD1, NK1, PV1, PV2, ARV... |
| 2 | **ADT_A02** | Transfer a Patient | MSH, EVN, PID, PD1, PV1, PV2, ARV, ROL |
| 3 | **ADT_A03** | Discharge/End Visit | MSH, EVN, PID, PD1, PV1, PV2, ARV, ROL... |
| 4 | **ADT_A04** | Register a Patient | MSH, EVN, PID, PD1, NK1, PV1, PV2, ARV... |
| 5 | **ADT_A05** | Pre-Admit a Patient | MSH, EVN, PID, PD1, NK1, PV1, PV2, AL1... |
| 6 | **ADT_A08** | Update Patient Information | MSH, EVN, PID, PD1, NK1, PV1, PV2, ARV... |
| 7 | **ADT_A28** | Add Person Information | MSH, EVN, PID, PD1, NK1, PV1, PV2, AL1... |
| 8 | **ADT_A31** | Update Person Information | MSH, EVN, PID, PD1, NK1, PV1, PV2, AL1... |
| 9 | **ADT_A34** | Merge Patient (PID Only) | MSH, EVN, PID, PD1 |
| 10 | **ADT_A40** | Merge Patient (Patient ID List) | MSH, EVN, PID, PD1 |
| 11 | **BAR_P01** | Add Patient Account | MSH, EVN, PID, PD1, PV1, DG1, PR1, GT1... |
| 12 | **DFT_P03** | Post Detail Financial Transaction | MSH, EVN, PID, PV1, OBR, OBX, DG1, PR1... |
| 13 | **MDM_T02** | Original Document Notification/Content | MSH, EVN, PID, PV1, TXA, OBX, NTE |
| 14 | **OML_O21** | Lab Order | MSH, PID, PD1, PV1, ORC, OBR, NTE, OBX... |
| 15 | **ORM_O01** | General Order | MSH, PID, PD1, PV1, PV2, ORC, OBR, NTE... |
| 16 | **ORU_R01** | Unsolicited Observation Result | MSH, PID, PD1, PV1, ORC, OBR, NTE, OBX... |
| 17 | **OUL_R22** | Unsolicited Specimen Observation | MSH, PID, PV1, ORC, OBR, OBX, SPM, SAC... |
| 18 | **RAS_O17** | Pharmacy/Treatment Administration | MSH, PID, PV1, ORC, RXA, RXR, OBX, NTE |
| 19 | **RDE_O11** | Pharmacy/Treatment Encoded Order | MSH, PID, PD1, PV1, PV2, ORC, RXO, RXE... |
| 20 | **RDS_O13** | Pharmacy/Treatment Dispense | MSH, PID, PD1, PV1, PV2, ORC, RXD, RXR... |
| 21 | **SIU_S12** | Notification of New Appointment Booking | MSH, SCH, PID, PV1, AIG, AIL, AIP, AIS... |
| 22 | **SIU_S13** | Notification of Appointment Rescheduling | MSH, SCH, PID, PV1, AIG, AIL, AIP, AIS... |
| 23 | **SIU_S14** | Notification of Appointment Modification | MSH, SCH, PID, PV1, AIG, AIL, AIP, AIS... |
| 24 | **SIU_S15** | Notification of Appointment Cancellation | MSH, SCH, PID, PV1, AIG, AIL, AIP, AIS... |
| 25 | **VXU_V04** | Unsolicited Vaccination Record Update | MSH, PID, PD1, NK1, PV1, ORC, RXA, RXR... |

## 5. V2 datatype → FHIR datatype mappings (39)
*Ánh xạ kiểu dữ liệu V2 → FHIR (39 loại)*

| V2 type | → FHIR type(s) |
|---|---|
| **CE** | CodeableConcept, Coding |
| **CF** | CodeableConcept |
| **CNE** | CodeableConcept, Coding, code |
| **CNN** | Practitioner |
| **CP** | Money |
| **CQ** | Quantity |
| **CWE** | CodeableConcept, Coding, code, string, Quantity |
| **CX** | Identifier, Reference |
| **DR** | Period |
| **DT** | date |
| **DTM** | dateTime, instant |
| **ED** | Attachment |
| **EI** | Identifier, Reference |
| **FT** | string, markdown |
| **HD** | Organization, Identifier, uri |
| **ID** | code, CodeableConcept, boolean, string |
| **IS** | code, CodeableConcept, string |
| **MO** | Money |
| **MSG** | Coding |
| **NDL** | PractitionerRole, Location |
| **NM** | decimal, integer, Quantity |
| **PL** | Location, Reference |
| **PT** | Meta |
| **RFR** | Range |
| **RI** | Timing |
| **RP** | Attachment, Reference |
| **RPT** | Timing |
| **SI** | positiveInt |
| **SN** | Quantity, Range, Ratio |
| **ST** | string |
| **TM** | time |
| **TS** | dateTime, instant |
| **TX** | string, markdown |
| **VID** | string |
| **XAD** | Address |
| **XCN** | Practitioner, PractitionerRole, Reference, HumanName |
| **XON** | Organization, string, Reference |
| **XPN** | HumanName |
| **XTN** | ContactPoint |

## 6. V2 vocabulary → FHIR code system (23)
*Ánh xạ bảng V2 → hệ mã FHIR (23 bảng)*

| V2 table | FHIR system URI |
|---|---|
| **HL70001** | `http://hl7.org/fhir/administrative-gender` |
| **HL70002** | `http://hl7.org/fhir/v2/0002` |
| **HL70004** | `http://hl7.org/fhir/encounter-status` |
| **HL70005** | `urn:oid:2.16.840.1.113883.6.238` |
| **HL70006** | `http://terminology.hl7.org/CodeSystem/v3-ReligiousAffiliation` |
| **HL70007** | `http://terminology.hl7.org/CodeSystem/v2-0007` |
| **HL70063** | `http://terminology.hl7.org/CodeSystem/v3-RoleCode` |
| **HL70078** | `http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation` |
| **HL70085** | `http://hl7.org/fhir/observation-status` |
| **HL70112** | `http://hl7.org/fhir/discharge-disposition` |
| **HL70127** | `http://hl7.org/fhir/allergy-intolerance-type` |
| **HL70128** | `http://hl7.org/fhir/allergy-intolerance-criticality` |
| **HL70131** | `http://terminology.hl7.org/CodeSystem/v2-0131` |
| **HL70136** | `http://hl7.org/fhir/ValueSet/yesnodontknow` |
| **HL70190** | `http://hl7.org/fhir/address-use` |
| **HL70200** | `http://hl7.org/fhir/name-use` |
| **HL70201** | `http://hl7.org/fhir/contact-point-use` |
| **HL70202** | `http://hl7.org/fhir/contact-point-system` |
| **HL70203** | `http://terminology.hl7.org/CodeSystem/v2-0203` |
| **HL70301** | `http://terminology.hl7.org/CodeSystem/v2-0301` |
| **HL70443** | `http://terminology.hl7.org/CodeSystem/v2-0443` |
| **HL70487** | `http://terminology.hl7.org/CodeSystem/v2-0487` |
| **HL70549** | `http://terminology.hl7.org/CodeSystem/v2-0549` |

## 7. V2 segment → FHIR target registry (57)
*Đăng ký segment V2 → mục tiêu FHIR (57 mapping)*

This is the full mapping registry from the HL7 V2-to-FHIR IG. Not all have dedicated converters (19 do); the rest serve as reference.

| V2 segment | → FHIR target(s) |
|---|---|
| **ACC** | Account |
| **AFF** | Organization[affiliation] |
| **AIG** | Appointment[participant-group] |
| **AIL** | Appointment[participant-location] |
| **AIP** | Appointment[participant-person] |
| **AIS** | Appointment[participant-service] |
| **AL1** ✅ | AllergyIntolerance |
| **ARV** | Consent[access-restriction], Observation |
| **BHS** | Bundle[batch] |
| **BTS** | Bundle[batch] |
| **CER** | Practitioner[qualification] |
| **DG1** ✅ | Condition, EpisodeOfCare[diagnosis], Encounter[diagnosis] |
| **EDU** | Practitioner[qualification] |
| **ERR** | OperationOutcome |
| **EVN** | Provenance |
| **FHS** | Bundle[batch] |
| **FTS** | Bundle[batch] |
| **GT1** ✅ | RelatedPerson[guarantor], Account[guarantor], Coverage |
| **IAM** | AllergyIntolerance[detailed] |
| **IAR** | AllergyIntolerance[reaction] |
| **IN1** ✅ | Coverage, Organization[insurer] |
| **IN2** | Coverage[extension], RelatedPerson[subscriber], Patient |
| **IN3** | Coverage[authorization] |
| **LAN** | Practitioner[communication] |
| **MFE** | Bundle[entry] |
| **MFI** | Bundle[message] |
| **MSA** | MessageHeader[response] |
| **MSH** ✅ | MessageHeader, Bundle, Provenance[originator], Provenance[translator] |
| **NK1** ✅ | RelatedPerson, Patient[contact] |
| **NTE** | Observation[note], ServiceRequest[note], DiagnosticReport[note] |
| **OBR** ✅ | ServiceRequest, DiagnosticReport |
| **OBX** ✅ | Observation, DocumentReference[embedded] |
| **ORC** ✅ | ServiceRequest, DiagnosticReport, Immunization, Task, Provenance, MedicationRequest |
| **ORG** | Organization, PractitionerRole |
| **PD1** | Patient[extension] |
| **PID** ✅ | Patient, Account |
| **PR1** | Procedure |
| **PRT** ✅ | PractitionerRole, RelatedPerson, Patient, Encounter[participant], Observation[performer] |
| **PV1** ✅ | Encounter, Patient[class] |
| **PV2** | Encounter[extension] |
| **ROL** | Encounter[participant], Patient[generalPractitioner] |
| **RXA** ✅ | Immunization, MedicationAdministration |
| **RXC** | MedicationRequest[component] |
| **RXD** ✅ | MedicationDispense |
| **RXE** ✅ | MedicationRequest[encoded], MedicationDispense |
| **RXG** | MedicationAdministration[give] |
| **RXO** ✅ | MedicationRequest |
| **RXR** | MedicationRequest[dosage-route], Immunization[route] |
| **SAC** | Specimen[container], Location |
| **SCH** ✅ | Appointment, ServiceRequest |
| **SFT** | MessageHeader[source], Device[software] |
| **SPM** ✅ | Specimen |
| **STF** | Practitioner |
| **TQ1** | ServiceRequest[timing], MedicationRequest[timing] |
| **TQ2** | ServiceRequest[timing-relationship] |
| **TXA** ✅ | DocumentReference |
| **UAC** | MessageHeader[auth] |

✅ = has dedicated converter / có bộ chuyển đổi riêng

---

**Grand total: 237 mappings across all categories**
*Tổng cộng: 237 mapping trên tất cả danh mục*