# FHIR R5 resources — complete list (157/157 = 100%)
# Danh sách resource FHIR R5 — đầy đủ (157/157 = 100%)

All 157 FHIR R5 (v5.0.0) resources supported: **create**, **validate**, **serialize** (JSON/dict), **bundle**.

*Tất cả 157 resource FHIR R5 (v5.0.0) được hỗ trợ: **tạo**, **validate**, **serialize**, **gom bundle**.*

```python
from brightohir import R5
resource = R5.create("Patient", active=True, name=[{"family": "Nguyen"}])
```

Source: https://hl7.org/fhir/R5/resourcelist.html

## Conformance (10)

- 1. **CapabilityStatement**
- 2. **CompartmentDefinition**
- 3. **ExampleScenario**
- 4. **GraphDefinition**
- 5. **ImplementationGuide**
- 6. **MessageDefinition**
- 7. **OperationDefinition**
- 8. **SearchParameter**
- 9. **StructureDefinition**
- 10. **StructureMap**

## Terminology (5)

- 11. **CodeSystem**
- 12. **ConceptMap**
- 13. **NamingSystem**
- 14. **TerminologyCapabilities**
- 15. **ValueSet**

## Security (4)

- 16. **AuditEvent**
- 17. **Consent**
- 18. **Permission**
- 19. **Provenance**

## Documents (3)

- 20. **Composition**
- 21. **DocumentManifest**
- 22. **DocumentReference**

## Other Foundation (9)

- 23. **Basic**
- 24. **Binary**
- 25. **Bundle**
- 26. **MessageHeader**
- 27. **OperationOutcome**
- 28. **Parameters**
- 29. **Subscription**
- 30. **SubscriptionStatus**
- 31. **SubscriptionTopic**

## Individuals (6)

- 32. **Group**
- 33. **Patient**
- 34. **Person**
- 35. **Practitioner**
- 36. **PractitionerRole**
- 37. **RelatedPerson**

## Entities (5)

- 38. **Endpoint**
- 39. **HealthcareService**
- 40. **Location**
- 41. **Organization**
- 42. **OrganizationAffiliation**

## Devices (3)

- 43. **Device**
- 44. **DeviceDefinition**
- 45. **DeviceMetric**

## Workflow (6)

- 46. **Appointment**
- 47. **AppointmentResponse**
- 48. **Schedule**
- 49. **Slot**
- 50. **Task**
- 51. **VerificationResult**

## Management (6)

- 52. **Encounter**
- 53. **EncounterHistory**
- 54. **EpisodeOfCare**
- 55. **Flag**
- 56. **Library**
- 57. **List**

## Summary (6)

- 58. **AllergyIntolerance**
- 59. **ClinicalImpression**
- 60. **Condition**
- 61. **DetectedIssue**
- 62. **FamilyMemberHistory**
- 63. **Procedure**

## Diagnostics (8)

- 64. **BodyStructure**
- 65. **DiagnosticReport**
- 66. **GenomicStudy**
- 67. **ImagingSelection**
- 68. **ImagingStudy**
- 69. **MolecularSequence**
- 70. **Observation**
- 71. **Specimen**

## Medications (9)

- 72. **Immunization**
- 73. **ImmunizationEvaluation**
- 74. **ImmunizationRecommendation**
- 75. **Medication**
- 76. **MedicationAdministration**
- 77. **MedicationDispense**
- 78. **MedicationKnowledge**
- 79. **MedicationRequest**
- 80. **MedicationStatement**

## Care Provision (10)

- 81. **CarePlan**
- 82. **CareTeam**
- 83. **Goal**
- 84. **NutritionIntake**
- 85. **NutritionOrder**
- 86. **NutritionProduct**
- 87. **RequestOrchestration**
- 88. **RiskAssessment**
- 89. **ServiceRequest**
- 90. **VisionPrescription**

## Request Response (10)

- 91. **Communication**
- 92. **CommunicationRequest**
- 93. **DeviceAssociation**
- 94. **DeviceDispense**
- 95. **DeviceRequest**
- 96. **DeviceUsage**
- 97. **GuidanceResponse**
- 98. **SupplyDelivery**
- 99. **SupplyRequest**
- 100. **Transport**

## Support (5)

- 101. **Coverage**
- 102. **CoverageEligibilityRequest**
- 103. **CoverageEligibilityResponse**
- 104. **EnrollmentRequest**
- 105. **EnrollmentResponse**

## Billing (3)

- 106. **Claim**
- 107. **ClaimResponse**
- 108. **Invoice**

## Payment (2)

- 109. **PaymentNotice**
- 110. **PaymentReconciliation**

## General Financial (6)

- 111. **Account**
- 112. **ChargeItem**
- 113. **ChargeItemDefinition**
- 114. **Contract**
- 115. **ExplanationOfBenefit**
- 116. **InsurancePlan**

## Public Health (4)

- 117. **Measure**
- 118. **MeasureReport**
- 119. **ResearchStudy**
- 120. **ResearchSubject**

## Definitional (12)

- 121. **ActivityDefinition**
- 122. **ActorDefinition**
- 123. **EventDefinition**
- 124. **ObservationDefinition**
- 125. **PlanDefinition**
- 126. **Questionnaire**
- 127. **QuestionnaireResponse**
- 128. **Requirements**
- 129. **SpecimenDefinition**
- 130. **TestPlan**
- 131. **TestReport**
- 132. **TestScript**

## Evidence (5)

- 133. **ArtifactAssessment**
- 134. **Citation**
- 135. **Evidence**
- 136. **EvidenceReport**
- 137. **EvidenceVariable**

## Medication Definition (8)

- 138. **AdministrableProductDefinition**
- 139. **ClinicalUseDefinition**
- 140. **Ingredient**
- 141. **ManufacturedItemDefinition**
- 142. **MedicinalProductDefinition**
- 143. **PackagedProductDefinition**
- 144. **RegulatedAuthorization**
- 145. **SubstanceDefinition**

## Quality (1)

- 146. **AdverseEvent**

## Other (11)

- 147. **BiologicallyDerivedProduct**
- 148. **BiologicallyDerivedProductDispense**
- 149. **FormularyItem**
- 150. **InventoryItem**
- 151. **InventoryReport**
- 152. **Linkage**
- 153. **SubstanceNucleicAcid**
- 154. **SubstancePolymer**
- 155. **SubstanceProtein**
- 156. **SubstanceReferenceInformation**
- 157. **SubstanceSourceMaterial**

**Total: 157 / 157 — 100%**