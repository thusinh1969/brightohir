"""
brightohir.registry
===================
Complete HL7 standards registry based on:
- FHIR R5 (v5.0.0) — 157 resources
- HL7 V2-to-FHIR IG v1.0.0 (STU, Oct 2025) — segment/message/datatype/vocabulary ConceptMaps
- FHIR R4↔R5 official transforms — field-level diffs

Source: https://hl7.org/fhir/R5/resourcelist.html
Source: https://build.fhir.org/ig/HL7/v2-to-fhir/
Source: http://hl7.org/fhir/5.0.0-draft-final/r4maps.html
"""

from __future__ import annotations

# ═══════════════════════════════════════════════════════════════════════════════
# 1. FHIR R5 RESOURCE REGISTRY — all 157 resources by category
# Source: https://hl7.org/fhir/R5/resourcelist.html (v5.0.0)
# ═══════════════════════════════════════════════════════════════════════════════

R5_RESOURCES: dict[str, list[str]] = {
    # ── Foundation ─────────────────────────────────────────────────────────
    "conformance": [
        "CapabilityStatement", "StructureDefinition", "ImplementationGuide",
        "SearchParameter", "MessageDefinition", "OperationDefinition",
        "CompartmentDefinition", "StructureMap", "GraphDefinition",
        "ExampleScenario",
    ],
    "terminology": [
        "CodeSystem", "ValueSet", "ConceptMap", "NamingSystem", "TerminologyCapabilities",
    ],
    "security": [
        "AuditEvent", "Provenance", "Consent", "Permission",
    ],
    "documents": [
        "Composition", "DocumentReference", "DocumentManifest",
    ],
    "other_foundation": [
        "Basic", "Binary", "Bundle", "MessageHeader",
        "OperationOutcome", "Parameters", "Subscription", "SubscriptionStatus",
        "SubscriptionTopic",
    ],
    # ── Base ───────────────────────────────────────────────────────────────
    "individuals": [
        "Patient", "Practitioner", "PractitionerRole", "RelatedPerson",
        "Person", "Group",
    ],
    "entities": [
        "Organization", "OrganizationAffiliation", "HealthcareService",
        "Location", "Endpoint",
    ],
    "devices": [
        "Device", "DeviceDefinition", "DeviceMetric",
    ],
    "workflow": [
        "Task", "Appointment", "AppointmentResponse", "Schedule", "Slot",
        "VerificationResult",
    ],
    "management": [
        "Encounter", "EncounterHistory", "EpisodeOfCare", "Flag", "List",
        "Library",
    ],
    # ── Clinical ──────────────────────────────────────────────────────────
    "summary": [
        "AllergyIntolerance", "Condition", "Procedure", "FamilyMemberHistory",
        "ClinicalImpression", "DetectedIssue",
    ],
    "diagnostics": [
        "Observation", "DiagnosticReport", "Specimen", "BodyStructure",
        "ImagingStudy", "ImagingSelection", "MolecularSequence",
        "GenomicStudy",
    ],
    "medications": [
        "MedicationRequest", "MedicationAdministration", "MedicationDispense",
        "MedicationStatement", "Medication", "MedicationKnowledge",
        "Immunization", "ImmunizationEvaluation", "ImmunizationRecommendation",
    ],
    "care_provision": [
        "CarePlan", "CareTeam", "Goal", "ServiceRequest", "NutritionOrder",
        "NutritionIntake", "NutritionProduct", "VisionPrescription",
        "RiskAssessment", "RequestOrchestration",
    ],
    "request_response": [
        "Communication", "CommunicationRequest", "DeviceRequest",
        "DeviceDispense", "DeviceUsage", "DeviceAssociation",
        "GuidanceResponse", "SupplyRequest", "SupplyDelivery",
        "Transport",
    ],
    # ── Financial ─────────────────────────────────────────────────────────
    "support": [
        "Coverage", "CoverageEligibilityRequest", "CoverageEligibilityResponse",
        "EnrollmentRequest", "EnrollmentResponse",
    ],
    "billing": [
        "Claim", "ClaimResponse", "Invoice",
    ],
    "payment": [
        "PaymentNotice", "PaymentReconciliation",
    ],
    "general_financial": [
        "Account", "ChargeItem", "ChargeItemDefinition", "Contract",
        "ExplanationOfBenefit", "InsurancePlan",
    ],
    # ── Specialized ───────────────────────────────────────────────────────
    "public_health": [
        "ResearchStudy", "ResearchSubject", "MeasureReport", "Measure",
    ],
    "definitional": [
        "ActivityDefinition", "PlanDefinition", "Questionnaire",
        "QuestionnaireResponse", "ObservationDefinition",
        "SpecimenDefinition", "EventDefinition", "Requirements",
        "ActorDefinition", "TestPlan", "TestScript", "TestReport",
    ],
    "evidence": [
        "Citation", "Evidence", "EvidenceReport", "EvidenceVariable",
        "ArtifactAssessment",
    ],
    "medication_definition": [
        "MedicinalProductDefinition", "PackagedProductDefinition",
        "AdministrableProductDefinition", "ManufacturedItemDefinition",
        "Ingredient", "ClinicalUseDefinition",
        "RegulatedAuthorization", "SubstanceDefinition",
    ],
    "quality": [
        "AdverseEvent",
    ],
    "other": [
        "Linkage", "InventoryItem", "InventoryReport",
        "BiologicallyDerivedProduct", "BiologicallyDerivedProductDispense",
        "FormularyItem", "SubstancePolymer", "SubstanceProtein",
        "SubstanceNucleicAcid", "SubstanceReferenceInformation",
        "SubstanceSourceMaterial",
    ],
}

# Flat set of all 157 R5 resource names
ALL_R5_RESOURCES: set[str] = set()
for _cat, _names in R5_RESOURCES.items():
    ALL_R5_RESOURCES.update(_names)


# ═══════════════════════════════════════════════════════════════════════════════
# 2. V2 SEGMENT → FHIR R5 RESOURCE MAPPING
# Source: HL7 V2-to-FHIR IG v1.0.0 (STU, Oct 2025)
#         https://build.fhir.org/ig/HL7/v2-to-fhir/segment_maps.html
#
# Format: segment → [(fhir_resource, flavor_note)]
# Multiple targets = context-dependent (message structure determines which)
# ═══════════════════════════════════════════════════════════════════════════════

V2_SEGMENT_TO_FHIR: dict[str, list[tuple[str, str]]] = {
    # ── Control / Infrastructure ──────────────────────────────────────────
    "MSH": [("MessageHeader", ""), ("Bundle", ""), ("Provenance", "originator"), ("Provenance", "translator")],
    "MSA": [("MessageHeader", "response")],
    "ERR": [("OperationOutcome", "")],
    "SFT": [("MessageHeader", "source"), ("Device", "software")],
    "UAC": [("MessageHeader", "auth")],
    "EVN": [("Provenance", "")],
    "BHS": [("Bundle", "batch")],
    "BTS": [("Bundle", "batch")],
    "FHS": [("Bundle", "batch")],
    "FTS": [("Bundle", "batch")],

    # ── Patient Administration ────────────────────────────────────────────
    "PID": [("Patient", ""), ("Account", "")],
    "PD1": [("Patient", "extension")],
    "NK1": [("RelatedPerson", ""), ("Patient", "contact")],
    "PV1": [("Encounter", ""), ("Patient", "class")],
    "PV2": [("Encounter", "extension")],
    "ARV": [("Consent", "access-restriction"), ("Observation", "")],
    "ROL": [("Encounter", "participant"), ("Patient", "generalPractitioner")],  # deprecated → PRT
    "PRT": [
        ("PractitionerRole", ""), ("RelatedPerson", ""), ("Patient", ""),
        ("Encounter", "participant"), ("Observation", "performer"),
    ],

    # ── Allergy / Problem ─────────────────────────────────────────────────
    "AL1": [("AllergyIntolerance", "")],
    "IAM": [("AllergyIntolerance", "detailed")],
    "IAR": [("AllergyIntolerance", "reaction")],
    "DG1": [("Condition", ""), ("EpisodeOfCare", "diagnosis"), ("Encounter", "diagnosis")],
    "PR1": [("Procedure", "")],

    # ── Orders / Observations ─────────────────────────────────────────────
    "ORC": [
        ("ServiceRequest", ""), ("DiagnosticReport", ""),
        ("Immunization", ""), ("Task", ""), ("Provenance", ""),
        ("MedicationRequest", ""),
    ],
    "OBR": [("ServiceRequest", ""), ("DiagnosticReport", "")],
    "OBX": [("Observation", ""), ("DocumentReference", "embedded")],
    "NTE": [("Observation", "note"), ("ServiceRequest", "note"), ("DiagnosticReport", "note")],
    "SPM": [("Specimen", "")],
    "SAC": [("Specimen", "container"), ("Location", "")],
    "TQ1": [("ServiceRequest", "timing"), ("MedicationRequest", "timing")],
    "TQ2": [("ServiceRequest", "timing-relationship")],

    # ── Results ───────────────────────────────────────────────────────────
    "TXA": [("DocumentReference", "")],

    # ── Pharmacy ──────────────────────────────────────────────────────────
    "RXA": [("Immunization", ""), ("MedicationAdministration", "")],
    "RXC": [("MedicationRequest", "component")],
    "RXD": [("MedicationDispense", "")],
    "RXE": [("MedicationRequest", "encoded"), ("MedicationDispense", "")],
    "RXG": [("MedicationAdministration", "give")],
    "RXO": [("MedicationRequest", "")],
    "RXR": [("MedicationRequest", "dosage-route"), ("Immunization", "route")],

    # ── Scheduling ────────────────────────────────────────────────────────
    "SCH": [("Appointment", ""), ("ServiceRequest", "")],
    "AIG": [("Appointment", "participant-group")],
    "AIL": [("Appointment", "participant-location")],
    "AIP": [("Appointment", "participant-person")],
    "AIS": [("Appointment", "participant-service")],

    # ── Financial ─────────────────────────────────────────────────────────
    "GT1": [("RelatedPerson", "guarantor"), ("Account", "guarantor"), ("Coverage", "")],
    "IN1": [("Coverage", ""), ("Organization", "insurer")],
    "IN2": [("Coverage", "extension"), ("RelatedPerson", "subscriber"), ("Patient", "")],
    "IN3": [("Coverage", "authorization")],
    "ACC": [("Account", "")],

    # ── Master Files ──────────────────────────────────────────────────────
    "MFI": [("Bundle", "message")],
    "MFE": [("Bundle", "entry")],

    # ── Personnel / Practitioner ──────────────────────────────────────────
    "STF": [("Practitioner", "")],
    "ORG": [("Organization", ""), ("PractitionerRole", "")],
    "AFF": [("Organization", "affiliation")],
    "LAN": [("Practitioner", "communication")],
    "EDU": [("Practitioner", "qualification")],
    "CER": [("Practitioner", "qualification")],
}

# ═══════════════════════════════════════════════════════════════════════════════
# 3. V2 MESSAGE STRUCTURES → FHIR BUNDLE COMPOSITION
# Source: HL7 V2-to-FHIR IG v1.0.0 message_maps
# ═══════════════════════════════════════════════════════════════════════════════

V2_MESSAGE_TO_FHIR: dict[str, dict] = {
    # ── ADT (Patient Administration) ──────────────────────────────────────
    "ADT_A01": {"name": "Admit/Visit Notification", "segments": ["MSH", "EVN", "PID", "PD1", "NK1", "PV1", "PV2", "ARV", "ROL", "AL1", "DG1", "PR1", "GT1", "IN1", "IN2", "IN3"], "fhir_resources": ["Bundle", "MessageHeader", "Patient", "Encounter", "RelatedPerson", "AllergyIntolerance", "Condition", "Procedure", "Coverage", "Account", "Provenance"]},
    "ADT_A02": {"name": "Transfer a Patient", "segments": ["MSH", "EVN", "PID", "PD1", "PV1", "PV2", "ARV", "ROL"], "fhir_resources": ["Bundle", "MessageHeader", "Patient", "Encounter", "Provenance"]},
    "ADT_A03": {"name": "Discharge/End Visit", "segments": ["MSH", "EVN", "PID", "PD1", "PV1", "PV2", "ARV", "ROL", "DG1", "PR1"], "fhir_resources": ["Bundle", "MessageHeader", "Patient", "Encounter", "Condition", "Procedure", "Provenance"]},
    "ADT_A04": {"name": "Register a Patient", "segments": ["MSH", "EVN", "PID", "PD1", "NK1", "PV1", "PV2", "ARV", "ROL", "AL1", "DG1", "GT1", "IN1", "IN2", "IN3"], "fhir_resources": ["Bundle", "MessageHeader", "Patient", "Encounter", "RelatedPerson", "AllergyIntolerance", "Condition", "Coverage", "Account", "Provenance"]},
    "ADT_A05": {"name": "Pre-Admit a Patient", "segments": ["MSH", "EVN", "PID", "PD1", "NK1", "PV1", "PV2", "AL1", "DG1", "GT1", "IN1", "IN2", "IN3"], "fhir_resources": ["Bundle", "MessageHeader", "Patient", "Encounter", "RelatedPerson", "AllergyIntolerance", "Condition", "Coverage", "Account", "Provenance"]},
    "ADT_A08": {"name": "Update Patient Information", "segments": ["MSH", "EVN", "PID", "PD1", "NK1", "PV1", "PV2", "ARV", "ROL", "AL1", "DG1", "GT1", "IN1", "IN2", "IN3"], "fhir_resources": ["Bundle", "MessageHeader", "Patient", "Encounter", "RelatedPerson", "AllergyIntolerance", "Condition", "Coverage", "Account", "Provenance"]},
    "ADT_A28": {"name": "Add Person Information", "segments": ["MSH", "EVN", "PID", "PD1", "NK1", "PV1", "PV2", "AL1", "DG1", "GT1", "IN1", "IN2", "IN3"], "fhir_resources": ["Bundle", "MessageHeader", "Patient", "Encounter", "RelatedPerson", "AllergyIntolerance", "Condition", "Coverage", "Account", "Provenance"]},
    "ADT_A31": {"name": "Update Person Information", "segments": ["MSH", "EVN", "PID", "PD1", "NK1", "PV1", "PV2", "AL1", "DG1", "GT1", "IN1", "IN2", "IN3"], "fhir_resources": ["Bundle", "MessageHeader", "Patient", "Encounter", "RelatedPerson", "AllergyIntolerance", "Condition", "Coverage", "Account", "Provenance"]},
    "ADT_A34": {"name": "Merge Patient (PID Only)", "segments": ["MSH", "EVN", "PID", "PD1"], "fhir_resources": ["Bundle", "MessageHeader", "Patient", "Provenance"]},
    "ADT_A40": {"name": "Merge Patient (Patient ID List)", "segments": ["MSH", "EVN", "PID", "PD1"], "fhir_resources": ["Bundle", "MessageHeader", "Patient", "Provenance"]},

    # ── ORM/ORU (Orders / Results) ────────────────────────────────────────
    "ORM_O01": {"name": "General Order", "segments": ["MSH", "PID", "PD1", "PV1", "PV2", "ORC", "OBR", "NTE", "OBX", "DG1"], "fhir_resources": ["Bundle", "MessageHeader", "Patient", "Encounter", "ServiceRequest", "DiagnosticReport", "Observation", "Condition", "Provenance"]},
    "ORU_R01": {"name": "Unsolicited Observation Result", "segments": ["MSH", "PID", "PD1", "PV1", "ORC", "OBR", "NTE", "OBX", "SPM"], "fhir_resources": ["Bundle", "MessageHeader", "Patient", "Encounter", "DiagnosticReport", "Observation", "Specimen", "Provenance"]},
    "OML_O21": {"name": "Lab Order", "segments": ["MSH", "PID", "PD1", "PV1", "ORC", "OBR", "NTE", "OBX", "SPM", "SAC", "DG1"], "fhir_resources": ["Bundle", "MessageHeader", "Patient", "Encounter", "ServiceRequest", "Observation", "Specimen", "Condition", "Provenance"]},
    "OUL_R22": {"name": "Unsolicited Specimen Observation", "segments": ["MSH", "PID", "PV1", "ORC", "OBR", "OBX", "SPM", "SAC", "NTE"], "fhir_resources": ["Bundle", "MessageHeader", "Patient", "Encounter", "DiagnosticReport", "Observation", "Specimen", "Provenance"]},

    # ── Pharmacy ──────────────────────────────────────────────────────────
    "RDE_O11": {"name": "Pharmacy/Treatment Encoded Order", "segments": ["MSH", "PID", "PD1", "PV1", "PV2", "ORC", "RXO", "RXE", "RXR", "RXC", "NTE", "TQ1", "TQ2"], "fhir_resources": ["Bundle", "MessageHeader", "Patient", "Encounter", "MedicationRequest", "Provenance"]},
    "RDS_O13": {"name": "Pharmacy/Treatment Dispense", "segments": ["MSH", "PID", "PD1", "PV1", "PV2", "ORC", "RXD", "RXR", "RXC", "NTE", "TQ1"], "fhir_resources": ["Bundle", "MessageHeader", "Patient", "Encounter", "MedicationDispense", "Provenance"]},
    "RAS_O17": {"name": "Pharmacy/Treatment Administration", "segments": ["MSH", "PID", "PV1", "ORC", "RXA", "RXR", "OBX", "NTE"], "fhir_resources": ["Bundle", "MessageHeader", "Patient", "Encounter", "MedicationAdministration", "Observation", "Provenance"]},

    # ── Vaccination ───────────────────────────────────────────────────────
    "VXU_V04": {"name": "Unsolicited Vaccination Record Update", "segments": ["MSH", "PID", "PD1", "NK1", "PV1", "ORC", "RXA", "RXR", "OBX", "NTE"], "fhir_resources": ["Bundle", "MessageHeader", "Patient", "RelatedPerson", "Encounter", "Immunization", "Observation", "Provenance"]},

    # ── Documents ─────────────────────────────────────────────────────────
    "MDM_T02": {"name": "Original Document Notification/Content", "segments": ["MSH", "EVN", "PID", "PV1", "TXA", "OBX", "NTE"], "fhir_resources": ["Bundle", "MessageHeader", "Patient", "Encounter", "DocumentReference", "Provenance"]},

    # ── Scheduling ────────────────────────────────────────────────────────
    "SIU_S12": {"name": "Notification of New Appointment Booking", "segments": ["MSH", "SCH", "PID", "PV1", "AIG", "AIL", "AIP", "AIS", "NTE"], "fhir_resources": ["Bundle", "MessageHeader", "Patient", "Encounter", "Appointment", "Provenance"]},
    "SIU_S13": {"name": "Notification of Appointment Rescheduling", "segments": ["MSH", "SCH", "PID", "PV1", "AIG", "AIL", "AIP", "AIS", "NTE"], "fhir_resources": ["Bundle", "MessageHeader", "Patient", "Encounter", "Appointment", "Provenance"]},
    "SIU_S14": {"name": "Notification of Appointment Modification", "segments": ["MSH", "SCH", "PID", "PV1", "AIG", "AIL", "AIP", "AIS", "NTE"], "fhir_resources": ["Bundle", "MessageHeader", "Patient", "Encounter", "Appointment", "Provenance"]},
    "SIU_S15": {"name": "Notification of Appointment Cancellation", "segments": ["MSH", "SCH", "PID", "PV1", "AIG", "AIL", "AIP", "AIS", "NTE"], "fhir_resources": ["Bundle", "MessageHeader", "Patient", "Encounter", "Appointment", "Provenance"]},

    # ── Financial / Billing ───────────────────────────────────────────────
    "BAR_P01": {"name": "Add Patient Account", "segments": ["MSH", "EVN", "PID", "PD1", "PV1", "DG1", "PR1", "GT1", "IN1", "IN2", "IN3", "ACC"], "fhir_resources": ["Bundle", "MessageHeader", "Patient", "Encounter", "Condition", "Procedure", "Coverage", "Account", "Provenance"]},
    "DFT_P03": {"name": "Post Detail Financial Transaction", "segments": ["MSH", "EVN", "PID", "PV1", "OBR", "OBX", "DG1", "PR1", "GT1", "IN1", "IN2"], "fhir_resources": ["Bundle", "MessageHeader", "Patient", "Encounter", "DiagnosticReport", "Observation", "Condition", "Procedure", "Coverage", "Account", "Provenance"]},
}

# ═══════════════════════════════════════════════════════════════════════════════
# 4. V2 DATATYPE → FHIR R5 DATATYPE MAPPING
# Source: HL7 V2-to-FHIR IG v1.0.0 datatype_maps
# ═══════════════════════════════════════════════════════════════════════════════

V2_DATATYPE_TO_FHIR: dict[str, list[str]] = {
    # Coded types
    "CWE": ["CodeableConcept", "Coding", "code", "string", "Quantity"],
    "CNE": ["CodeableConcept", "Coding", "code"],
    "CE":  ["CodeableConcept", "Coding"],
    "CF":  ["CodeableConcept"],
    "ID":  ["code", "CodeableConcept", "boolean", "string"],
    "IS":  ["code", "CodeableConcept", "string"],
    # Identifier
    "CX":  ["Identifier", "Reference"],
    "EI":  ["Identifier", "Reference"],
    "HD":  ["Organization", "Identifier", "uri"],
    "PL":  ["Location", "Reference"],
    # Name / Address / Telecom
    "XPN": ["HumanName"],
    "XAD": ["Address"],
    "XTN": ["ContactPoint"],
    "XCN": ["Practitioner", "PractitionerRole", "Reference", "HumanName"],
    "XON": ["Organization", "string", "Reference"],
    # Date/Time
    "TS":  ["dateTime", "instant"],
    "DTM": ["dateTime", "instant"],
    "DT":  ["date"],
    "TM":  ["time"],
    "DR":  ["Period"],
    # Numeric
    "NM":  ["decimal", "integer", "Quantity"],
    "SN":  ["Quantity", "Range", "Ratio"],
    "SI":  ["positiveInt"],
    # Quantity
    "CQ":  ["Quantity"],
    # Text
    "ST":  ["string"],
    "TX":  ["string", "markdown"],
    "FT":  ["string", "markdown"],
    "ED":  ["Attachment"],
    # Composite
    "MSG": ["Coding"],
    "PT":  ["Meta"],
    "VID": ["string"],
    "RP":  ["Attachment", "Reference"],
    # Financial
    "MO":  ["Money"],
    "CP":  ["Money"],
    # Structured Numeric
    "NDL": ["PractitionerRole", "Location"],
    "CNN": ["Practitioner"],
    # Reference
    "RI":  ["Timing"],
    "RFR": ["Range"],
    "RPT": ["Timing"],
}

# ═══════════════════════════════════════════════════════════════════════════════
# 5. R4 ↔ R5 CONVERSION REGISTRY
# Source: http://hl7.org/fhir/5.0.0-draft-final/r4maps.html
#         https://hl7.org/fhir/R5/diff.html
#
# Key: R5 resource name → {"r4_name", "status", "field_changes"}
# status: "same" | "renamed" | "new_r5" | "removed_r5" | "restructured"
# field_changes: list of (action, field, detail)
# ═══════════════════════════════════════════════════════════════════════════════

R4_TO_R5_MAP: dict[str, dict] = {
    # ── No change / minimal change ────────────────────────────────────────
    "Patient":               {"r4": "Patient", "status": "compatible", "changes": [("add", "communication.preferred", "boolean")]},
    "Practitioner":          {"r4": "Practitioner", "status": "compatible", "changes": []},
    "PractitionerRole":      {"r4": "PractitionerRole", "status": "compatible", "changes": [("rename", "availableTime", "availability")]},
    "Organization":          {"r4": "Organization", "status": "compatible", "changes": [("add", "description", "markdown"), ("add", "qualification", "BackboneElement")]},
    "RelatedPerson":         {"r4": "RelatedPerson", "status": "compatible", "changes": []},
    "Location":              {"r4": "Location", "status": "compatible", "changes": [("add", "characteristic", "CodeableConcept")]},

    "Encounter":             {"r4": "Encounter", "status": "restructured", "changes": [
        ("remove", "class", "→ R5 uses 'class' as CodeableConcept not Coding"),
        ("rename", "hospitalization", "admission"),
        ("add", "virtualService", "VirtualServiceDetail"),
        ("remove", "classHistory", "→ use EncounterHistory"),
        ("remove", "statusHistory", "→ use EncounterHistory"),
    ]},
    "EncounterHistory":      {"r4": None, "status": "new_r5", "changes": []},

    "Condition":             {"r4": "Condition", "status": "restructured", "changes": [
        ("rename", "verificationStatus", "verificationStatus (CodeableConcept)"),
        ("add", "participant", "BackboneElement"),
        ("remove", "recorder", "→ participant"),
        ("remove", "asserter", "→ participant"),
    ]},
    "Observation":           {"r4": "Observation", "status": "compatible", "changes": [
        ("add", "triggeredBy", "BackboneElement"),
        ("add", "instantiates", "canonical|Reference"),
    ]},
    "DiagnosticReport":      {"r4": "DiagnosticReport", "status": "compatible", "changes": [
        ("add", "note", "Annotation"),
        ("add", "composition", "Reference(Composition)"),
        ("add", "supportingInfo", "BackboneElement"),
    ]},
    "Procedure":             {"r4": "Procedure", "status": "compatible", "changes": [
        ("add", "focus", "Reference"),
        ("rename", "performer.onBehalfOf", "performer.function → role change"),
    ]},
    "AllergyIntolerance":    {"r4": "AllergyIntolerance", "status": "compatible", "changes": [
        ("add", "participant", "BackboneElement"),
        ("remove", "recorder", "→ participant"),
        ("remove", "asserter", "→ participant"),
    ]},

    "ServiceRequest":        {"r4": "ServiceRequest", "status": "compatible", "changes": [
        ("add", "focus", "Reference"),
        ("add", "bodyStructure", "Reference(BodyStructure)"),
    ]},
    "MedicationRequest":     {"r4": "MedicationRequest", "status": "restructured", "changes": [
        ("rename", "reported", "informationSource"),
        ("rename", "performer", "performer → type changed"),
        ("add", "device", "CodeableReference"),
        ("add", "effectiveDosePeriod", "Period"),
        ("rename", "medication[x]", "medication (CodeableReference)"),
    ]},
    "MedicationAdministration": {"r4": "MedicationAdministration", "status": "restructured", "changes": [
        ("rename", "medication[x]", "medication (CodeableReference)"),
        ("rename", "context", "encounter"),
        ("add", "subPotentReason", "CodeableConcept"),
    ]},
    "MedicationDispense":    {"r4": "MedicationDispense", "status": "restructured", "changes": [
        ("rename", "medication[x]", "medication (CodeableReference)"),
        ("rename", "context", "encounter"),
        ("add", "notPerformedReason", "CodeableReference"),
    ]},
    "MedicationStatement":   {"r4": "MedicationStatement", "status": "restructured", "changes": [
        ("rename", "medication[x]", "medication (CodeableReference)"),
        ("rename", "statusReason", "reason"),
        ("rename", "reasonCode", "reason"),
    ]},
    "Medication":            {"r4": "Medication", "status": "compatible", "changes": [
        ("add", "definition", "Reference(MedicinalProductDefinition)"),
        ("add", "totalVolume", "Quantity"),
    ]},
    "Immunization":          {"r4": "Immunization", "status": "compatible", "changes": [
        ("add", "administeredProduct", "CodeableReference"),
        ("rename", "performer", "performer.actor → reference change"),
    ]},

    "Coverage":              {"r4": "Coverage", "status": "compatible", "changes": [
        ("add", "insurancePlan", "Reference(InsurancePlan)"),
        ("add", "paymentBy", "BackboneElement"),
    ]},
    "Claim":                 {"r4": "Claim", "status": "compatible", "changes": [("add", "diagnosisSequence", "changed")]},

    "Specimen":              {"r4": "Specimen", "status": "compatible", "changes": [
        ("add", "combined", "code"),
        ("add", "role", "CodeableConcept"),
    ]},
    "BodyStructure":         {"r4": "BodyStructure", "status": "restructured", "changes": [
        ("add", "includedStructure", "BackboneElement replaces location/locationQualifier"),
        ("remove", "location", "→ includedStructure.structure"),
        ("remove", "locationQualifier", "→ includedStructure.laterality"),
    ]},

    "DocumentReference":     {"r4": "DocumentReference", "status": "restructured", "changes": [
        ("remove", "masterIdentifier", "→ identifier"),
        ("rename", "content.attachment", "content.attachment"),
        ("add", "basedOn", "Reference"),
        ("add", "bodySite", "CodeableReference"),
        ("add", "modality", "CodeableConcept"),
        ("remove", "context", "flattened into resource root"),
    ]},
    "Composition":           {"r4": "Composition", "status": "compatible", "changes": [
        ("add", "url", "uri"),
        ("add", "version", "string"),
        ("add", "name", "string"),
    ]},

    "Bundle":                {"r4": "Bundle", "status": "compatible", "changes": [("add", "issues", "Resource")]},
    "MessageHeader":         {"r4": "MessageHeader", "status": "compatible", "changes": []},
    "OperationOutcome":      {"r4": "OperationOutcome", "status": "compatible", "changes": []},
    "Provenance":            {"r4": "Provenance", "status": "compatible", "changes": []},
    "Consent":               {"r4": "Consent", "status": "restructured", "changes": [
        ("remove", "scope", "removed"),
        ("rename", "provision", "provision restructured"),
        ("add", "regulatoryBasis", "CodeableConcept"),
    ]},

    "Appointment":           {"r4": "Appointment", "status": "restructured", "changes": [
        ("add", "class", "CodeableConcept"),
        ("add", "subject", "Reference"),
        ("add", "recurrenceId", "positiveInt"),
        ("add", "recurrenceTemplate", "BackboneElement"),
    ]},
    "Schedule":              {"r4": "Schedule", "status": "compatible", "changes": [("add", "name", "string")]},
    "Slot":                  {"r4": "Slot", "status": "compatible", "changes": []},

    "Task":                  {"r4": "Task", "status": "compatible", "changes": [
        ("add", "requestedPerformer", "CodeableReference"),
    ]},
    "CarePlan":              {"r4": "CarePlan", "status": "restructured", "changes": [
        ("remove", "activity.detail", "→ use RequestOrchestration"),
        ("add", "custodian", "Reference replaces author"),
    ]},
    "CareTeam":              {"r4": "CareTeam", "status": "compatible", "changes": []},
    "Goal":                  {"r4": "Goal", "status": "compatible", "changes": []},

    "Account":               {"r4": "Account", "status": "compatible", "changes": [
        ("add", "billingStatus", "CodeableConcept"),
        ("add", "relatedAccount", "BackboneElement"),
        ("add", "balance", "BackboneElement"),
    ]},

    # ── New R5 resources (no R4 equivalent) ──────────────────────────────
    "ActorDefinition":       {"r4": None, "status": "new_r5", "changes": []},
    "Requirements":          {"r4": None, "status": "new_r5", "changes": []},
    "SubscriptionTopic":     {"r4": None, "status": "new_r5", "changes": []},
    "TestPlan":              {"r4": None, "status": "new_r5", "changes": []},
    "Transport":             {"r4": None, "status": "new_r5", "changes": []},
    "InventoryItem":         {"r4": None, "status": "new_r5", "changes": []},
    "InventoryReport":       {"r4": None, "status": "new_r5", "changes": []},
    "DeviceAssociation":     {"r4": None, "status": "new_r5", "changes": []},
    "DeviceDispense":        {"r4": None, "status": "new_r5", "changes": []},
    "NutritionIntake":       {"r4": None, "status": "new_r5", "changes": []},
    "ImagingSelection":      {"r4": None, "status": "new_r5", "changes": []},
    "GenomicStudy":          {"r4": None, "status": "new_r5", "changes": []},
    "Permission":            {"r4": None, "status": "new_r5", "changes": []},
    "ArtifactAssessment":    {"r4": None, "status": "new_r5", "changes": []},
    "SubscriptionStatus":    {"r4": None, "status": "new_r5", "changes": []},
    "FormularyItem":         {"r4": None, "status": "new_r5", "changes": []},
    "BiologicallyDerivedProductDispense": {"r4": None, "status": "new_r5", "changes": []},
    "Citation":              {"r4": None, "status": "new_r5", "changes": []},
    "EvidenceReport":        {"r4": None, "status": "new_r5", "changes": []},
    "RequestOrchestration":  {"r4": "RequestGroup", "status": "renamed", "changes": []},
}

# Reverse lookup: R4 name → R5 name
R5_FROM_R4: dict[str, str] = {}
for _r5, _info in R4_TO_R5_MAP.items():
    if _info.get("r4"):
        R5_FROM_R4[_info["r4"]] = _r5


# ═══════════════════════════════════════════════════════════════════════════════
# 6. V2 VOCABULARY → FHIR CODING SYSTEM MAPPING
# ═══════════════════════════════════════════════════════════════════════════════

V2_TABLE_TO_FHIR_SYSTEM: dict[str, str] = {
    "HL70001": "http://hl7.org/fhir/administrative-gender",         # Admin Sex
    "HL70002": "http://hl7.org/fhir/v2/0002",                       # Marital Status
    "HL70004": "http://hl7.org/fhir/encounter-status",              # Patient Class
    "HL70005": "urn:oid:2.16.840.1.113883.6.238",                   # Race
    "HL70006": "http://terminology.hl7.org/CodeSystem/v3-ReligiousAffiliation",
    "HL70007": "http://terminology.hl7.org/CodeSystem/v2-0007",     # Admission Type
    "HL70063": "http://terminology.hl7.org/CodeSystem/v3-RoleCode", # Relationship
    "HL70078": "http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation",
    "HL70085": "http://hl7.org/fhir/observation-status",            # Observation Result Status
    "HL70112": "http://hl7.org/fhir/discharge-disposition",         # Discharge Disposition
    "HL70127": "http://hl7.org/fhir/allergy-intolerance-type",     # Allergen Type
    "HL70128": "http://hl7.org/fhir/allergy-intolerance-criticality",
    "HL70131": "http://terminology.hl7.org/CodeSystem/v2-0131",     # Contact Role
    "HL70136": "http://hl7.org/fhir/ValueSet/yesnodontknow",       # Yes/No
    "HL70190": "http://hl7.org/fhir/address-use",                   # Address Type
    "HL70200": "http://hl7.org/fhir/name-use",                      # Name Type
    "HL70201": "http://hl7.org/fhir/contact-point-use",            # Telecom Use
    "HL70202": "http://hl7.org/fhir/contact-point-system",         # Telecom Type
    "HL70203": "http://terminology.hl7.org/CodeSystem/v2-0203",     # Identifier Type
    "HL70301": "http://terminology.hl7.org/CodeSystem/v2-0301",     # Universal ID Type
    "HL70443": "http://terminology.hl7.org/CodeSystem/v2-0443",     # Provider Role
    "HL70487": "http://terminology.hl7.org/CodeSystem/v2-0487",     # Specimen Type
    "HL70549": "http://terminology.hl7.org/CodeSystem/v2-0549",     # NDC Codes
}
