# Implementation Plan: Document Categories Expansion

## Overview

This implementation adds 15 new document type categories to Scanner-Watcher2, expanding from 15 to 30 supported document types. The implementation leverages the existing three-tier classification architecture, requiring only enum expansion and prompt updates. All changes maintain backward compatibility with existing functionality.

## Tasks

- [x] 1. Update DocumentType enum with new categories
  - Add 15 new enum members to `src/scanner_watcher2/models.py`
  - Use UPPER_SNAKE_CASE for enum names (e.g., `PANEL_LIST`, `QME_APPOINTMENT_NOTIFICATION`)
  - Use Title Case with spaces for enum values (e.g., `"Panel List"`, `"QME Appointment Notification Form"`)
  - Maintain OTHER as the last enum member
  - New enum members: PANEL_LIST, QME_APPOINTMENT_NOTIFICATION, AME_REPORT, QME_REPORT, PTP_INITIAL_REPORT, PTP_PS_REPORT, RFA, UR_APPROVAL, UR_DENIAL, MODIFIED_UR, FINDING_AND_AWARD, FINDING_AND_ORDER, ADVOCACY_COVER_LETTER, DECLARATION_OF_READINESS, OBJECTION_TO_DOR
  - _Requirements: 1.1, 2.1, 3.1, 4.1, 5.1, 6.1, 7.1, 8.1, 9.1, 10.1, 11.1, 12.1, 13.1, 14.1, 15.1, 16.1, 17.1_

- [ ]* 1.1 Write property test for enum completeness
  - **Property 1: Enum completeness**
  - **Validates: Requirements 1.1, 2.1, 3.1, 4.1, 5.1, 6.1, 7.1, 8.1, 9.1, 10.1, 11.1, 12.1, 13.1, 14.1, 15.1, 17.1**
  - Test that all 15 new document types exist as DocumentType enum members
  - Use hypothesis to generate document type strings from the new categories list
  - Verify each document type exists in the enum values
  - _Requirements: 1.1, 2.1, 3.1, 4.1, 5.1, 6.1, 7.1, 8.1, 9.1, 10.1, 11.1, 12.1, 13.1, 14.1, 15.1, 17.1_

- [ ]* 1.2 Write property test for supported types count
  - **Property 2: Supported types count**
  - **Validates: Requirements 17.1, 17.4**
  - Test that get_supported_document_types() returns exactly 30 document types
  - Verify OTHER is excluded from the count
  - _Requirements: 17.1, 17.4_

- [x] 2. Update AI service system prompt with new categories
  - Update category_descriptions list in `src/scanner_watcher2/core/ai_service.py`
  - Add 15 new category descriptions with guidance for the AI model
  - Format: "- ENUM_NAME: Brief description of when to use this category"
  - Maintain three-tier priority structure (standard categories, specific types, OTHER fallback)
  - New descriptions:
    * PANEL_LIST: Medical evaluator panel assignment lists
    * QME_APPOINTMENT_NOTIFICATION: QME appointment scheduling forms
    * AME_REPORT: Agreed Medical Evaluator examination reports
    * QME_REPORT: Qualified Medical Evaluator examination reports
    * PTP_INITIAL_REPORT: Primary Treating Physician initial evaluation
    * PTP_PS_REPORT: Primary Treating Physician Permanent & Stationary report
    * RFA: Request for Authorization for medical treatment
    * UR_APPROVAL: Utilization Review approval decisions
    * UR_DENIAL: Utilization Review denial decisions
    * MODIFIED_UR: Modified Utilization Review decisions
    * FINDING_AND_AWARD: WCAB Finding and Award documents
    * FINDING_AND_ORDER: WCAB Finding & Order documents
    * ADVOCACY_COVER_LETTER: Advocacy letters and cover correspondence
    * DECLARATION_OF_READINESS: Declaration of Readiness to Proceed filings
    * OBJECTION_TO_DOR: Objections to Declaration of Readiness
  - _Requirements: 1.3, 2.3, 3.3, 4.3, 5.3, 6.3, 7.3, 8.3, 9.3, 10.3, 11.3, 12.3, 13.3, 14.3, 15.3, 17.2_

- [ ]* 2.1 Write property test for prompt inclusion
  - **Property 3: Prompt inclusion**
  - **Validates: Requirements 1.3, 2.3, 3.3, 4.3, 5.3, 6.3, 7.3, 8.3, 9.3, 10.3, 11.3, 12.3, 13.3, 14.3, 15.3, 17.2**
  - Test that the system prompt includes all 30 document type categories
  - Mock the OpenAI API call to capture the system prompt
  - Verify all new category enum names appear in the prompt
  - _Requirements: 1.3, 2.3, 3.3, 4.3, 5.3, 6.3, 7.3, 8.3, 9.3, 10.3, 11.3, 12.3, 13.3, 14.3, 15.3, 17.2_

- [x] 3. Verify backward compatibility
  - [x] 3.1 Run existing unit tests to verify no regressions
    - Execute: `pytest -m unit`
    - Verify all existing tests pass
    - Update any tests that assert on enum count (should now expect 31 total members)
    - _Requirements: 16.1, 16.2, 16.3, 16.4_

  - [x] 3.2 Run existing property-based tests to verify no regressions
    - Execute: `pytest -m property`
    - Verify all existing property tests pass
    - Update any tests that assert on supported types count (should now expect 30)
    - _Requirements: 16.1, 16.2, 16.3, 16.4_

  - [x] 3.3 Run existing integration tests to verify no regressions
    - Execute: `pytest -m integration`
    - Verify all existing integration tests pass
    - _Requirements: 16.1, 16.2, 16.3, 16.4_

- [ ]* 3.4 Write property test for classification compatibility
  - **Property 4: Classification compatibility**
  - **Validates: Requirements 16.2**
  - Test that Classification dataclass handles all new document types
  - Use hypothesis to generate document types from all enum values (excluding OTHER)
  - Create Classification objects with each document type
  - Verify document_type is stored correctly
  - Verify is_standard_category() returns True
  - Verify is_other() returns False
  - _Requirements: 16.2_

- [ ]* 3.5 Write property test for filename generation compatibility
  - **Property 5: Filename generation compatibility**
  - **Validates: Requirements 16.3**
  - Test that file manager generates valid filenames with new document types
  - Use hypothesis to generate document types from all enum values (excluding OTHER)
  - Create test files and rename them with each document type
  - Verify filenames contain the document type (with or without underscores)
  - Verify file operations succeed
  - _Requirements: 16.3_

- [ ]* 3.6 Write property test for standard category recognition
  - **Property 6: Standard category recognition**
  - **Validates: Requirements 16.1, 16.2**
  - Test that Classification.is_standard_category() works with new enum values
  - Use hypothesis to generate document types from all enum values (excluding OTHER)
  - Create Classification objects with each document type
  - Verify is_standard_category() returns True for all enum values
  - _Requirements: 16.1, 16.2_

- [ ]* 3.7 Write property test for logging compatibility
  - **Property 7: Logging compatibility**
  - **Validates: Requirements 16.4**
  - Test that log entries include document_type field for new categories
  - Use hypothesis to generate document types from all enum values (excluding OTHER)
  - Mock file processing with each document type
  - Verify success log entries contain document_type field
  - Verify document_type value matches the classification result
  - _Requirements: 16.4_

- [ ]* 3.8 Write property test for new category classification
  - **Property 8: New category classification**
  - **Validates: Requirements 1.2, 2.2, 3.2, 4.2, 5.2, 6.2, 7.2, 8.2, 9.2, 10.2, 11.2, 12.2, 13.2, 14.2, 15.2, 17.3**
  - Test that AI service can return any of the 15 new document types
  - Use hypothesis to generate document types from the new categories list
  - Mock OpenAI responses with each new document type
  - Verify Classification objects are created correctly
  - Verify document_type matches the mocked response
  - _Requirements: 1.2, 2.2, 3.2, 4.2, 5.2, 6.2, 7.2, 8.2, 9.2, 10.2, 11.2, 12.2, 13.2, 14.2, 15.2, 17.3_

- [x] 4. Checkpoint - Ensure all tests pass
  - Run full test suite: `pytest`
  - Run with coverage: `pytest --cov=scanner_watcher2 --cov-report=html`
  - Verify code coverage remains above 80%
  - Verify no test failures or regressions
  - Ask the user if questions arise

- [x] 5. Update documentation
  - Update README.md with new document type categories
  - Add section listing all 30 supported document types
  - Group by category (medical reports, court documents, UR documents, etc.)
  - Update any configuration guides that reference document types
  - _Requirements: 1.1-15.3, 17.1-17.4_

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- The implementation leverages the existing three-tier classification architecture
- No changes required to Classification dataclass, FileManager, or FileProcessor
- The get_supported_document_types() method automatically returns all new types
- All property tests should run with minimum 100 iterations
- Backward compatibility is maintained throughout the implementation
