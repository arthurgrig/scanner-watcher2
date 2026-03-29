# Design Document: Document Categories Expansion

## Overview

This design extends Scanner-Watcher2's document classification capabilities from 15 to 30 supported document types. The expansion adds 15 new legal document categories commonly encountered in California Workers' Compensation workflows while maintaining backward compatibility with existing functionality.

The implementation follows the existing three-tier classification architecture:
1. **Standard Categories**: High-level DocumentType enum values (e.g., "Medical Report")
2. **Specific Types**: Precise document names (e.g., "QME Appointment Notification Form")
3. **OTHER Fallback**: Unclassifiable documents with descriptions (e.g., "OTHER_Unknown Form")

The design minimizes code changes by leveraging the existing flexible classification system, requiring only enum expansion and prompt updates.

## Architecture

### Current Architecture

The system uses a flexible classification approach implemented in Task 24 (Optional Feature Enhancements):

```
┌─────────────────────────────────────────────────────────────┐
│                      AI Service                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Classification Prompt (System Message)                │ │
│  │  - Priority 1: Standard enum categories               │ │
│  │  - Priority 2: Specific document types                │ │
│  │  - Priority 3: OTHER_[description] fallback           │ │
│  └────────────────────────────────────────────────────────┘ │
│                           ↓                                  │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  OpenAI GPT-4 Vision API                              │ │
│  │  - Analyzes document images (up to 3 pages)           │ │
│  │  - Returns JSON classification                         │ │
│  └────────────────────────────────────────────────────────┘ │
│                           ↓                                  │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Response Parser                                       │ │
│  │  - Validates document_type field                      │ │
│  │  - Creates Classification object                      │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                   Classification Object                      │
│  - document_type: str (enum value, specific type, or OTHER) │
│  - confidence: float                                         │
│  - identifiers: dict[str, str]                              │
│  - raw_response: dict                                        │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    File Manager                              │
│  - Generates filename: YYYY-MM-DD_DocumentType_ID.pdf       │
│  - Uses document_type string directly in filename           │
└─────────────────────────────────────────────────────────────┘
```

### Design Decision: Enum vs. Specific Types

The current architecture supports **both** enum categories and specific document types. For the 15 new categories, we have two options:

**Option A: Add to DocumentType Enum**
- Pros: Standardized, type-safe, consistent with existing categories
- Cons: Enum becomes large (30 values), less flexible for future additions

**Option B: Keep as Specific Types (No Enum)**
- Pros: More flexible, AI can use exact names, easier to extend
- Cons: No type safety, inconsistent with existing categories

**Selected Approach: Hybrid (Option A with flexibility)**

We will add all 15 new categories to the DocumentType enum for consistency and type safety, while maintaining the AI's ability to return specific type names. The AI prompt will be updated to recognize these as standard categories.

**Rationale:**
1. Consistency: All supported types should be in the enum
2. Type Safety: Enum provides compile-time validation
3. Flexibility: AI can still return specific names; Classification.document_type remains a string
4. Backward Compatibility: Existing three-tier system continues to work

## Components and Interfaces

### 1. DocumentType Enum (models.py)

**Current Implementation:**
```python
class DocumentType(Enum):
    """Standard document type categories for classification."""
    MEDICAL_REPORT = "Medical Report"
    INJURY_REPORT = "Injury Report"
    CLAIM_FORM = "Claim Form"
    DEPOSITION = "Deposition"
    EXPERT_WITNESS_REPORT = "Expert Witness Report"
    SETTLEMENT_AGREEMENT = "Settlement Agreement"
    COURT_ORDER = "Court Order"
    INSURANCE_CORRESPONDENCE = "Insurance Correspondence"
    WAGE_STATEMENT = "Wage Statement"
    VOCATIONAL_REPORT = "Vocational Report"
    IME_REPORT = "IME Report"
    SURVEILLANCE_REPORT = "Surveillance Report"
    SUBPOENA = "Subpoena"
    MOTION = "Motion"
    BRIEF = "Brief"
    OTHER = "Other"
```

**Updated Implementation:**
```python
class DocumentType(Enum):
    """Standard document type categories for classification."""
    # Existing categories (15)
    MEDICAL_REPORT = "Medical Report"
    INJURY_REPORT = "Injury Report"
    CLAIM_FORM = "Claim Form"
    DEPOSITION = "Deposition"
    EXPERT_WITNESS_REPORT = "Expert Witness Report"
    SETTLEMENT_AGREEMENT = "Settlement Agreement"
    COURT_ORDER = "Court Order"
    INSURANCE_CORRESPONDENCE = "Insurance Correspondence"
    WAGE_STATEMENT = "Wage Statement"
    VOCATIONAL_REPORT = "Vocational Report"
    IME_REPORT = "IME Report"
    SURVEILLANCE_REPORT = "Surveillance Report"
    SUBPOENA = "Subpoena"
    MOTION = "Motion"
    BRIEF = "Brief"
    
    # New categories (15)
    PANEL_LIST = "Panel List"
    QME_APPOINTMENT_NOTIFICATION = "QME Appointment Notification Form"
    AME_REPORT = "Agreed Medical Evaluator Report"
    QME_REPORT = "Qualified Medical Evaluator Report"
    PTP_INITIAL_REPORT = "PTP Initial Report"
    PTP_PS_REPORT = "PTP P&S Report"
    RFA = "RFA"
    UR_APPROVAL = "UR Approval"
    UR_DENIAL = "UR Denial"
    MODIFIED_UR = "Modified UR"
    FINDING_AND_AWARD = "Finding and Award"
    FINDING_AND_ORDER = "Finding & Order"
    ADVOCACY_COVER_LETTER = "Advocacy/Cover Letter"
    DECLARATION_OF_READINESS = "Declaration of Readiness to Proceed"
    OBJECTION_TO_DOR = "Objection to Declaration of Readiness to Proceed"
    
    OTHER = "Other"
```

**Changes:**
- Add 15 new enum members with descriptive values
- Maintain OTHER as the last enum member
- Use clear, consistent naming: UPPER_SNAKE_CASE for enum names, Title Case for values
- Total: 31 enum members (30 categories + OTHER)

### 2. AIService (core/ai_service.py)

**Method: get_supported_document_types()**

No changes required. This method already returns all enum values except OTHER:

```python
def get_supported_document_types(self) -> list[str]:
    """Return list of supported document type categories."""
    return [dt.value for dt in DocumentType if dt != DocumentType.OTHER]
```

After enum expansion, this will automatically return 30 document types.

**Method: classify_document()**

The system prompt must be updated to include the new categories. The current prompt uses a category_descriptions list that maps enum categories to descriptions.

**Updated System Prompt Structure:**

```python
category_descriptions = [
    # Existing categories
    "- MEDICAL_REPORT: Any medical evaluation, QME, AME, PTP, IME reports",
    "- INJURY_REPORT: Initial injury reports, incident reports",
    "- CLAIM_FORM: DWC-1, claim applications",
    "- DEPOSITION: Deposition transcripts",
    "- EXPERT_WITNESS_REPORT: Expert opinions, vocational evaluations",
    "- SETTLEMENT_AGREEMENT: Compromise & Release, Stipulations",
    "- COURT_ORDER: WCAB orders, findings, awards",
    "- INSURANCE_CORRESPONDENCE: Carrier letters, UR decisions, RFAs",
    "- WAGE_STATEMENT: Earnings records, pay stubs",
    "- VOCATIONAL_REPORT: Vocational rehabilitation reports",
    "- IME_REPORT: Independent Medical Examinations",
    "- SURVEILLANCE_REPORT: Investigation reports",
    "- SUBPOENA: Subpoenas, subpoena duces tecum",
    "- MOTION: Motions, petitions, DORs",
    "- BRIEF: Legal briefs, memoranda",
    
    # New categories
    "- PANEL_LIST: Medical evaluator panel assignment lists",
    "- QME_APPOINTMENT_NOTIFICATION: QME appointment scheduling forms",
    "- AME_REPORT: Agreed Medical Evaluator examination reports",
    "- QME_REPORT: Qualified Medical Evaluator examination reports",
    "- PTP_INITIAL_REPORT: Primary Treating Physician initial evaluation",
    "- PTP_PS_REPORT: Primary Treating Physician Permanent & Stationary report",
    "- RFA: Request for Authorization for medical treatment",
    "- UR_APPROVAL: Utilization Review approval decisions",
    "- UR_DENIAL: Utilization Review denial decisions",
    "- MODIFIED_UR: Modified Utilization Review decisions",
    "- FINDING_AND_AWARD: WCAB Finding and Award documents",
    "- FINDING_AND_ORDER: WCAB Finding & Order documents",
    "- ADVOCACY_COVER_LETTER: Advocacy letters and cover correspondence",
    "- DECLARATION_OF_READINESS: Declaration of Readiness to Proceed filings",
    "- OBJECTION_TO_DOR: Objections to Declaration of Readiness",
]
```

**Key Design Points:**
1. Each category includes a brief description to guide the AI
2. Descriptions help the AI understand when to use each category
3. The three-tier priority system remains unchanged
4. AI can still return specific type names or OTHER_[description]

### 3. Classification Dataclass (models.py)

No changes required. The Classification dataclass already supports flexible document_type strings:

```python
@dataclass
class Classification:
    """AI classification result for a document."""
    document_type: str  # Can be enum value, specific type, or OTHER_description
    confidence: float
    identifiers: dict[str, str]
    raw_response: dict
```

The helper methods `is_standard_category()` and `is_other()` will automatically work with the expanded enum.

### 4. File Manager (core/file_manager.py)

No changes required. The file manager uses `classification.document_type` directly in filenames, which works with any string value.

### 5. File Processor (core/file_processor.py)

No changes required. The file processor passes Classification objects through the pipeline without inspecting document_type values.

## Data Models

### DocumentType Enum

**Purpose:** Define all supported document categories for classification

**Structure:**
- 30 standard categories (15 existing + 15 new)
- 1 OTHER fallback category
- Total: 31 enum members

**Naming Conventions:**
- Enum names: UPPER_SNAKE_CASE (e.g., `QME_APPOINTMENT_NOTIFICATION`)
- Enum values: Title Case with spaces (e.g., `"QME Appointment Notification Form"`)
- Values match user-facing document type names

### Classification Dataclass

**No changes required.** The existing structure supports the expansion:

```python
@dataclass
class Classification:
    document_type: str  # Flexible string field
    confidence: float
    identifiers: dict[str, str]
    raw_response: dict
```

**Validation:**
- `document_type` can be any string (enum value, specific type, or OTHER_description)
- `is_standard_category()` checks if document_type matches any enum value
- `is_other()` checks if document_type starts with "OTHER_"

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Enum completeness
*For any* document type in the new categories list, that document type should exist as a DocumentType enum member
**Validates: Requirements 1.1, 2.1, 3.1, 4.1, 5.1, 6.1, 7.1, 8.1, 9.1, 10.1, 11.1, 12.1, 13.1, 14.1, 15.1, 17.1**

### Property 2: Supported types count
*For any* call to get_supported_document_types(), the returned list should contain exactly 30 document types (excluding OTHER)
**Validates: Requirements 17.1, 17.4**

### Property 3: Prompt inclusion
*For any* classification request, the system prompt should include all 30 document type categories with descriptions
**Validates: Requirements 1.3, 2.3, 3.3, 4.3, 5.3, 6.3, 7.3, 8.3, 9.3, 10.3, 11.3, 12.3, 13.3, 14.3, 15.3, 17.2**

### Property 4: Classification compatibility
*For any* new document type classification result, the Classification dataclass should successfully store and validate the document_type string
**Validates: Requirements 16.2**

### Property 5: Filename generation compatibility
*For any* new document type, the file manager should successfully generate a valid filename including the document type
**Validates: Requirements 16.3**

### Property 6: Standard category recognition
*For any* new document type enum value, the Classification.is_standard_category() method should return True when document_type matches that enum value
**Validates: Requirements 16.1, 16.2**

### Property 7: Logging compatibility
*For any* successfully processed file with a new document type, the log entry should include the document_type field
**Validates: Requirements 16.4**

### Property 8: New category classification
*For any* document matching a new supported type, the AI service should be capable of returning that document type in the classification result
**Validates: Requirements 1.2, 2.2, 3.2, 4.2, 5.2, 6.2, 7.2, 8.2, 9.2, 10.2, 11.2, 12.2, 13.2, 14.2, 15.2, 17.3**

## Error Handling

### Backward Compatibility Errors

**Scenario:** Existing code references DocumentType enum members
**Handling:** No breaking changes; all existing enum members remain unchanged

**Scenario:** Tests validate enum count
**Handling:** Update test assertions to expect 31 total enum members (30 + OTHER)

### Classification Errors

**Scenario:** AI returns a new document type that doesn't match enum exactly
**Handling:** Existing behavior continues; Classification.document_type stores the string as-is

**Scenario:** AI returns "OTHER_[description]" for unclassifiable documents
**Handling:** Existing behavior continues; Classification.is_other() returns True

### Filename Generation Errors

**Scenario:** New document type contains special characters
**Handling:** Existing file manager sanitization handles special characters

**Scenario:** New document type creates very long filenames
**Handling:** Existing file manager truncation logic applies

## Testing Strategy

### Unit Tests

**Test Coverage:**
1. **Enum Validation**
   - Verify DocumentType enum contains all 30 new categories
   - Verify enum values match expected strings
   - Verify OTHER remains as the last enum member

2. **get_supported_document_types()**
   - Verify method returns exactly 30 document types
   - Verify all new categories are included
   - Verify OTHER is excluded

3. **System Prompt Generation**
   - Verify prompt includes all 30 category descriptions
   - Verify descriptions are properly formatted
   - Verify three-tier priority structure is maintained

4. **Classification Dataclass**
   - Verify is_standard_category() returns True for new enum values
   - Verify is_other() returns False for new enum values
   - Verify document_type field accepts new category strings

5. **File Manager**
   - Verify filename generation works with new document types
   - Verify special character handling for new categories
   - Verify filename length limits are respected

### Property-Based Tests

**Configuration:**
- Minimum 100 iterations per test
- Use hypothesis library for property-based testing
- Tag format: `# Feature: document-categories-expansion, Property N: [property text]`

**Property Test 1: Enum completeness**
```python
@given(document_type=st.sampled_from([
    "Panel List",
    "QME Appointment Notification Form",
    "Agreed Medical Evaluator Report",
    "Qualified Medical Evaluator Report",
    "PTP Initial Report",
    "PTP P&S Report",
    "RFA",
    "UR Approval",
    "UR Denial",
    "Modified UR",
    "Finding and Award",
    "Finding & Order",
    "Advocacy/Cover Letter",
    "Declaration of Readiness to Proceed",
    "Objection to Declaration of Readiness to Proceed",
]))
@settings(max_examples=100)
def test_enum_completeness(document_type: str):
    """
    Feature: document-categories-expansion, Property 1: Enum completeness
    For any document type in the new categories list, that document type 
    should exist as a DocumentType enum member.
    """
    enum_values = [dt.value for dt in DocumentType]
    assert document_type in enum_values
```

**Property Test 2: Supported types count**
```python
@settings(max_examples=100)
def test_supported_types_count():
    """
    Feature: document-categories-expansion, Property 2: Supported types count
    For any call to get_supported_document_types(), the returned list should 
    contain exactly 30 document types (excluding OTHER).
    """
    ai_service = create_ai_service()  # Test fixture
    supported_types = ai_service.get_supported_document_types()
    assert len(supported_types) == 30
```

**Property Test 3: Prompt inclusion**
```python
@settings(max_examples=100)
def test_prompt_inclusion():
    """
    Feature: document-categories-expansion, Property 3: Prompt inclusion
    For any classification request, the system prompt should include all 30 
    document type categories with descriptions.
    """
    ai_service = create_ai_service()  # Test fixture
    
    # Mock the OpenAI API call to capture the prompt
    with patch.object(ai_service.client.chat.completions, 'create') as mock_create:
        mock_create.return_value = create_mock_response()
        
        # Trigger classification
        test_image = Image.new('RGB', (100, 100))
        ai_service.classify_document(test_image)
        
        # Extract system prompt from the call
        call_args = mock_create.call_args
        messages = call_args.kwargs['messages']
        system_message = next(m for m in messages if m['role'] == 'system')
        system_prompt = system_message['content']
        
        # Verify all new categories are mentioned
        new_categories = [
            "PANEL_LIST", "QME_APPOINTMENT_NOTIFICATION", "AME_REPORT",
            "QME_REPORT", "PTP_INITIAL_REPORT", "PTP_PS_REPORT",
            "RFA", "UR_APPROVAL", "UR_DENIAL", "MODIFIED_UR",
            "FINDING_AND_AWARD", "FINDING_AND_ORDER", "ADVOCACY_COVER_LETTER",
            "DECLARATION_OF_READINESS", "OBJECTION_TO_DOR"
        ]
        
        for category in new_categories:
            assert category in system_prompt
```

**Property Test 4: Classification compatibility**
```python
@given(document_type=st.sampled_from([dt.value for dt in DocumentType if dt != DocumentType.OTHER]))
@settings(max_examples=100)
def test_classification_compatibility(document_type: str):
    """
    Feature: document-categories-expansion, Property 4: Classification compatibility
    For any new document type classification result, the Classification dataclass 
    should successfully store and validate the document_type string.
    """
    classification = Classification(
        document_type=document_type,
        confidence=0.95,
        identifiers={"test": "value"},
        raw_response={}
    )
    
    assert classification.document_type == document_type
    assert classification.is_standard_category() == True
    assert classification.is_other() == False
```

**Property Test 5: Filename generation compatibility**
```python
@given(document_type=st.sampled_from([dt.value for dt in DocumentType if dt != DocumentType.OTHER]))
@settings(max_examples=100)
def test_filename_generation_compatibility(document_type: str, temp_dir):
    """
    Feature: document-categories-expansion, Property 5: Filename generation compatibility
    For any new document type, the file manager should successfully generate a 
    valid filename including the document type.
    """
    file_manager = create_file_manager(temp_dir)  # Test fixture
    
    # Create a test file
    source_file = temp_dir / "SCAN-test.pdf"
    source_file.write_text("test content")
    
    # Generate filename with document type
    current_date = datetime.now().strftime("%Y-%m-%d")
    target_name = f"{current_date}_{document_type}_TestID.pdf"
    target_path = temp_dir / target_name
    
    # Rename the file
    result = file_manager.rename_file(source_file, target_path)
    
    # Verify success and document type in filename
    assert result.exists()
    assert document_type in result.name or document_type.replace(" ", "_") in result.name
```

**Property Test 6: Standard category recognition**
```python
@given(document_type=st.sampled_from([dt.value for dt in DocumentType if dt != DocumentType.OTHER]))
@settings(max_examples=100)
def test_standard_category_recognition(document_type: str):
    """
    Feature: document-categories-expansion, Property 6: Standard category recognition
    For any new document type enum value, the Classification.is_standard_category() 
    method should return True when document_type matches that enum value.
    """
    classification = Classification(
        document_type=document_type,
        confidence=0.95,
        identifiers={},
        raw_response={}
    )
    
    assert classification.is_standard_category() == True
```

**Property Test 7: Logging compatibility**
```python
@given(document_type=st.sampled_from([dt.value for dt in DocumentType if dt != DocumentType.OTHER]))
@settings(max_examples=100)
def test_logging_compatibility(document_type: str, temp_dir):
    """
    Feature: document-categories-expansion, Property 7: Logging compatibility
    For any successfully processed file with a new document type, the log entry 
    should include the document_type field.
    """
    # Create test components
    logger = create_test_logger()  # Test fixture
    file_processor = create_file_processor(logger=logger)  # Test fixture
    
    # Mock classification result
    classification = Classification(
        document_type=document_type,
        confidence=0.95,
        identifiers={"test_id": "123"},
        raw_response={}
    )
    
    # Process a test file
    test_file = temp_dir / "SCAN-test.pdf"
    test_file.write_text("test content")
    
    with patch.object(file_processor.ai_service, 'classify_document', return_value=classification):
        result = file_processor.process_file(test_file)
    
    # Verify logging includes document_type
    log_calls = logger.info.call_args_list
    success_log = next(call for call in log_calls if "File processed successfully" in str(call))
    
    assert "document_type" in success_log.kwargs
    assert success_log.kwargs["document_type"] == document_type
```

**Property Test 8: New category classification**
```python
@given(
    document_type=st.sampled_from([
        "Panel List", "QME Appointment Notification Form",
        "Agreed Medical Evaluator Report", "Qualified Medical Evaluator Report",
        "PTP Initial Report", "PTP P&S Report", "RFA",
        "UR Approval", "UR Denial", "Modified UR",
        "Finding and Award", "Finding & Order", "Advocacy/Cover Letter",
        "Declaration of Readiness to Proceed",
        "Objection to Declaration of Readiness to Proceed"
    ]),
    confidence=st.floats(min_value=0.0, max_value=1.0)
)
@settings(max_examples=100)
def test_new_category_classification(document_type: str, confidence: float):
    """
    Feature: document-categories-expansion, Property 8: New category classification
    For any document matching a new supported type, the AI service should be 
    capable of returning that document type in the classification result.
    """
    ai_service = create_ai_service()  # Test fixture
    
    # Mock OpenAI response with the new document type
    mock_response = {
        "choices": [{
            "message": {
                "content": json.dumps({
                    "document_type": document_type,
                    "confidence": confidence,
                    "identifiers": {"test_key": "test_value"}
                })
            }
        }]
    }
    
    with patch.object(ai_service.client.chat.completions, 'create') as mock_create:
        mock_create.return_value = Mock(model_dump=lambda: mock_response)
        
        # Classify a test image
        test_image = Image.new('RGB', (100, 100))
        result = ai_service.classify_document(test_image)
        
        # Verify the new document type is returned
        assert result.document_type == document_type
        assert abs(result.confidence - confidence) < 0.01
```

### Integration Tests

**Test Coverage:**
1. **End-to-End Classification**
   - Create test PDFs representing new document types
   - Process through full pipeline
   - Verify correct classification and file naming

2. **Backward Compatibility**
   - Process existing document types
   - Verify no regression in classification accuracy
   - Verify existing tests continue to pass

3. **Mixed Document Processing**
   - Process batch of documents with old and new types
   - Verify all documents are correctly classified
   - Verify no interference between old and new categories

### Test Execution

**Commands:**
```bash
# Run all tests
pytest

# Run unit tests only
pytest -m unit

# Run property-based tests only
pytest -m property

# Run integration tests only
pytest -m integration

# Run with coverage
pytest --cov=scanner_watcher2 --cov-report=html

# Run specific test file
pytest tests/unit/test_models.py
pytest tests/property/test_ai_service_properties.py
```

**Expected Results:**
- All existing tests pass without modification (except enum count assertions)
- All new property-based tests pass with 100 iterations
- Code coverage remains above 80%
- No performance degradation in classification speed
