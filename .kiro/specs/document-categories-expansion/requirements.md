# Requirements Document

## Introduction

This specification defines the expansion of document classification categories in Scanner-Watcher2 to support 15 additional legal document types commonly encountered in workers' compensation and legal workflows. The system currently supports 15 document categories and will be enhanced to support 30 total categories.

## Glossary

- **System**: Scanner-Watcher2 document processing application
- **DocumentType**: Enumeration of supported document categories for classification
- **AI_Service**: Component responsible for document classification using OpenAI GPT-4 Vision
- **Classification**: Result object containing document type, confidence score, and identifiers
- **Standard_Category**: A document type defined in the DocumentType enum
- **Supported_Document_Types**: The complete list of document categories the system can identify

## Requirements

### Requirement 1: Panel List Classification

**User Story:** As a legal office administrator, I want the system to recognize Panel List documents, so that medical evaluator panel assignments are properly organized.

#### Acceptance Criteria

1. WHEN the AI_Service classifies a document THEN the System SHALL support identification of Panel List documents
2. WHEN a Panel List document is classified THEN the System SHALL return "Panel List" as the document type
3. WHEN the AI_Service provides classification instructions to the AI model THEN the System SHALL include "Panel List" in the supported document types list

### Requirement 2: QME Appointment Notification Form Classification

**User Story:** As a legal office administrator, I want the system to recognize QME Appointment Notification Forms, so that qualified medical evaluator appointments are tracked.

#### Acceptance Criteria

1. WHEN the AI_Service classifies a document THEN the System SHALL support identification of QME Appointment Notification Form documents
2. WHEN a QME Appointment Notification Form is classified THEN the System SHALL return "QME Appointment Notification Form" as the document type
3. WHEN the AI_Service provides classification instructions to the AI model THEN the System SHALL include "QME Appointment Notification Form" in the supported document types list

### Requirement 3: Agreed Medical Evaluator Report Classification

**User Story:** As a legal office administrator, I want the system to recognize Agreed Medical Evaluator (AME) reports, so that agreed medical evaluations are distinguished from other medical reports.

#### Acceptance Criteria

1. WHEN the AI_Service classifies a document THEN the System SHALL support identification of Agreed Medical Evaluator Report documents
2. WHEN an Agreed Medical Evaluator Report is classified THEN the System SHALL return "Agreed Medical Evaluator Report" as the document type
3. WHEN the AI_Service provides classification instructions to the AI model THEN the System SHALL include "Agreed Medical Evaluator Report" in the supported document types list

### Requirement 4: Qualified Medical Evaluator Report Classification

**User Story:** As a legal office administrator, I want the system to recognize Qualified Medical Evaluator (QME) reports, so that QME evaluations are distinguished from other medical reports.

#### Acceptance Criteria

1. WHEN the AI_Service classifies a document THEN the System SHALL support identification of Qualified Medical Evaluator Report documents
2. WHEN a Qualified Medical Evaluator Report is classified THEN the System SHALL return "Qualified Medical Evaluator Report" as the document type
3. WHEN the AI_Service provides classification instructions to the AI model THEN the System SHALL include "Qualified Medical Evaluator Report" in the supported document types list

### Requirement 5: PTP Initial Report Classification

**User Story:** As a legal office administrator, I want the system to recognize Primary Treating Physician (PTP) initial reports, so that initial medical evaluations are properly categorized.

#### Acceptance Criteria

1. WHEN the AI_Service classifies a document THEN the System SHALL support identification of PTP Initial Report documents
2. WHEN a PTP Initial Report is classified THEN the System SHALL return "PTP Initial Report" as the document type
3. WHEN the AI_Service provides classification instructions to the AI model THEN the System SHALL include "PTP Initial Report" in the supported document types list

### Requirement 6: PTP P&S Report Classification

**User Story:** As a legal office administrator, I want the system to recognize Primary Treating Physician Permanent and Stationary (P&S) reports, so that final medical status reports are properly categorized.

#### Acceptance Criteria

1. WHEN the AI_Service classifies a document THEN the System SHALL support identification of PTP P&S Report documents
2. WHEN a PTP P&S Report is classified THEN the System SHALL return "PTP P&S Report" as the document type
3. WHEN the AI_Service provides classification instructions to the AI model THEN the System SHALL include "PTP P&S Report" in the supported document types list

### Requirement 7: RFA Classification

**User Story:** As a legal office administrator, I want the system to recognize Request for Authorization (RFA) documents, so that medical treatment authorization requests are tracked.

#### Acceptance Criteria

1. WHEN the AI_Service classifies a document THEN the System SHALL support identification of RFA documents
2. WHEN an RFA document is classified THEN the System SHALL return "RFA" as the document type
3. WHEN the AI_Service provides classification instructions to the AI model THEN the System SHALL include "RFA" in the supported document types list

### Requirement 8: UR Approval Classification

**User Story:** As a legal office administrator, I want the system to recognize Utilization Review (UR) approval documents, so that approved medical treatment authorizations are organized.

#### Acceptance Criteria

1. WHEN the AI_Service classifies a document THEN the System SHALL support identification of UR Approval documents
2. WHEN a UR Approval document is classified THEN the System SHALL return "UR Approval" as the document type
3. WHEN the AI_Service provides classification instructions to the AI model THEN the System SHALL include "UR Approval" in the supported document types list

### Requirement 9: UR Denial Classification

**User Story:** As a legal office administrator, I want the system to recognize Utilization Review (UR) denial documents, so that denied medical treatment authorizations are tracked separately from approvals.

#### Acceptance Criteria

1. WHEN the AI_Service classifies a document THEN the System SHALL support identification of UR Denial documents
2. WHEN a UR Denial document is classified THEN the System SHALL return "UR Denial" as the document type
3. WHEN the AI_Service provides classification instructions to the AI model THEN the System SHALL include "UR Denial" in the supported document types list

### Requirement 10: Modified UR Classification

**User Story:** As a legal office administrator, I want the system to recognize Modified Utilization Review documents, so that modified treatment authorizations are distinguished from initial approvals or denials.

#### Acceptance Criteria

1. WHEN the AI_Service classifies a document THEN the System SHALL support identification of Modified UR documents
2. WHEN a Modified UR document is classified THEN the System SHALL return "Modified UR" as the document type
3. WHEN the AI_Service provides classification instructions to the AI model THEN the System SHALL include "Modified UR" in the supported document types list

### Requirement 11: Finding and Award Classification

**User Story:** As a legal office administrator, I want the system to recognize Finding and Award documents, so that WCAB decisions with monetary awards are properly categorized.

#### Acceptance Criteria

1. WHEN the AI_Service classifies a document THEN the System SHALL support identification of Finding and Award documents
2. WHEN a Finding and Award document is classified THEN the System SHALL return "Finding and Award" as the document type
3. WHEN the AI_Service provides classification instructions to the AI model THEN the System SHALL include "Finding and Award" in the supported document types list

### Requirement 12: Finding & Order Classification

**User Story:** As a legal office administrator, I want the system to recognize Finding & Order documents, so that WCAB decisions with orders are properly categorized.

#### Acceptance Criteria

1. WHEN the AI_Service classifies a document THEN the System SHALL support identification of Finding & Order documents
2. WHEN a Finding & Order document is classified THEN the System SHALL return "Finding & Order" as the document type
3. WHEN the AI_Service provides classification instructions to the AI model THEN the System SHALL include "Finding & Order" in the supported document types list

### Requirement 13: Advocacy/Cover Letter Classification

**User Story:** As a legal office administrator, I want the system to recognize Advocacy and Cover Letter documents, so that correspondence and advocacy documents are properly organized.

#### Acceptance Criteria

1. WHEN the AI_Service classifies a document THEN the System SHALL support identification of Advocacy/Cover Letter documents
2. WHEN an Advocacy/Cover Letter document is classified THEN the System SHALL return "Advocacy/Cover Letter" as the document type
3. WHEN the AI_Service provides classification instructions to the AI model THEN the System SHALL include "Advocacy/Cover Letter" in the supported document types list

### Requirement 14: Declaration of Readiness to Proceed Classification

**User Story:** As a legal office administrator, I want the system to recognize Declaration of Readiness to Proceed documents, so that case readiness filings are tracked.

#### Acceptance Criteria

1. WHEN the AI_Service classifies a document THEN the System SHALL support identification of Declaration of Readiness to Proceed documents
2. WHEN a Declaration of Readiness to Proceed document is classified THEN the System SHALL return "Declaration of Readiness to Proceed" as the document type
3. WHEN the AI_Service provides classification instructions to the AI model THEN the System SHALL include "Declaration of Readiness to Proceed" in the supported document types list

### Requirement 15: Objection to Declaration of Readiness to Proceed Classification

**User Story:** As a legal office administrator, I want the system to recognize Objection to Declaration of Readiness to Proceed documents, so that objections to case readiness are tracked separately.

#### Acceptance Criteria

1. WHEN the AI_Service classifies a document THEN the System SHALL support identification of Objection to Declaration of Readiness to Proceed documents
2. WHEN an Objection to Declaration of Readiness to Proceed document is classified THEN the System SHALL return "Objection to Declaration of Readiness to Proceed" as the document type
3. WHEN the AI_Service provides classification instructions to the AI model THEN the System SHALL include "Objection to Declaration of Readiness to Proceed" in the supported document types list

### Requirement 16: Backward Compatibility

**User Story:** As a system maintainer, I want the new document categories to integrate seamlessly with existing functionality, so that current features continue to work without modification.

#### Acceptance Criteria

1. WHEN new document types are added THEN the System SHALL maintain compatibility with existing DocumentType enum structure
2. WHEN new document types are added THEN the System SHALL maintain compatibility with existing Classification dataclass
3. WHEN new document types are added THEN the System SHALL maintain compatibility with existing file naming conventions
4. WHEN new document types are added THEN the System SHALL maintain compatibility with existing logging and metrics
5. WHEN new document types are added THEN the System SHALL maintain compatibility with existing property-based tests

### Requirement 17: Complete Document Type Coverage

**User Story:** As a legal office administrator, I want all 30 document types to be available for classification, so that the system supports my complete document workflow.

#### Acceptance Criteria

1. WHEN the System initializes THEN the DocumentType enum SHALL contain 30 total categories (15 existing + 15 new)
2. WHEN the AI_Service provides classification instructions THEN the System SHALL include all 30 document types in the prompt
3. WHEN a document is classified THEN the System SHALL be capable of returning any of the 30 supported document types
4. WHEN the get_supported_document_types method is called THEN the System SHALL return all 30 document type names
