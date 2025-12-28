# Task: Implement Prioritized Document Type Enum Classification

## Overview
Update the document classification system to use a prioritized enum-based approach with fallback to flexible classification.

## Current State
- System uses a fixed list of 15 specific document types
- AI must match to exact document type names
- No fallback for documents that don't fit predefined categories

## Desired State
- System uses prioritized enum of high-level document categories
- AI first attempts to map to enum categories
- If no enum match, AI provides flexible classification
- If completely unclassifiable, returns "OTHER" with suggested name

## Prioritized Document Type Enum

```python
class DocumentType(Enum):
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
    OTHER = "Other"  # Fallback category
```

## Classification Logic

### Priority 1: Enum Match
AI attempts to classify document into one of the 15 enum categories above.

**Examples:**
- QME Report → `MEDICAL_REPORT`
- AME Report → `MEDICAL_REPORT`
- PTP Report → `MEDICAL_REPORT`
- Finding and Award → `COURT_ORDER`
- Finding & Order → `COURT_ORDER`
- Declaration of Readiness → Could be `MOTION` or specific type
- UR Approval → `INSURANCE_CORRESPONDENCE`
- RFA → `INSURANCE_CORRESPONDENCE`

### Priority 2: Flexible Classification
If document doesn't clearly fit an enum category, AI provides specific document type name.

**Examples:**
- "Panel List"
- "QME Appointment Notification Form"
- "Declaration of Readiness to Proceed"
- "Utilization Review Denial"

### Priority 3: OTHER with Suggestion
If document cannot be classified, return:
- `document_type`: "OTHER_[Suggested Name]"
- Example: "OTHER_Unidentified Medical Document"

## Implementation Requirements

### 1. Update AI Service Prompt
Modify `src/scanner_watcher2/core/ai_service.py`:

```python
system_prompt = (
    "You are a legal document classifier for California Workers' Compensation cases. "
    "Classify documents using this prioritized approach:\n\n"
    "**PRIORITY 1 - Standard Categories (use if document clearly fits):**\n"
    "- MEDICAL_REPORT: Any medical evaluation, QME, AME, PTP, IME reports\n"
    "- INJURY_REPORT: Initial injury reports, incident reports\n"
    "- CLAIM_FORM: DWC-1, claim applications\n"
    "- DEPOSITION: Deposition transcripts\n"
    "- EXPERT_WITNESS_REPORT: Expert opinions, vocational evaluations\n"
    "- SETTLEMENT_AGREEMENT: Compromise & Release, Stipulations\n"
    "- COURT_ORDER: WCAB orders, findings, awards\n"
    "- INSURANCE_CORRESPONDENCE: Carrier letters, UR decisions, RFAs\n"
    "- WAGE_STATEMENT: Earnings records, pay stubs\n"
    "- VOCATIONAL_REPORT: Vocational rehabilitation reports\n"
    "- IME_REPORT: Independent Medical Examinations\n"
    "- SURVEILLANCE_REPORT: Investigation reports\n"
    "- SUBPOENA: Subpoenas, subpoena duces tecum\n"
    "- MOTION: Motions, petitions, DORs\n"
    "- BRIEF: Legal briefs, memoranda\n\n"
    "**PRIORITY 2 - Specific Type (if no standard category fits):**\n"
    "Provide the specific document type name (e.g., 'Panel List', 'QME Appointment Form')\n\n"
    "**PRIORITY 3 - Unknown (if cannot classify):**\n"
    "Return 'OTHER_[Brief Description]' (e.g., 'OTHER_Unidentified Medical Form')\n\n"
    "Return JSON with:\n"
    "- document_type: The classification (standard category, specific type, or OTHER_description)\n"
    "- confidence: 0.0-1.0\n"
    "- identifiers: Extract plaintiff_name, client_name, case_number, dates, etc.\n"
)
```

### 2. Create DocumentType Enum
Add to `src/scanner_watcher2/models.py`:

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

### 3. Update Classification Model
Modify `Classification` dataclass to handle both enum and flexible types:

```python
@dataclass
class Classification:
    """AI classification result for a document."""
    
    document_type: str  # Can be enum value, specific type, or OTHER_description
    confidence: float
    identifiers: dict[str, str]
    raw_response: dict
    
    @property
    def is_standard_category(self) -> bool:
        """Check if document_type matches a standard enum category."""
        return any(self.document_type == dt.value for dt in DocumentType)
    
    @property
    def is_other(self) -> bool:
        """Check if document_type is OTHER category."""
        return self.document_type.startswith("OTHER_")
```

### 4. Update File Naming Logic
Ensure `file_processor.py` handles all three classification types properly in filename generation.

### 5. Update Tests
- Add tests for enum category matching
- Add tests for flexible classification
- Add tests for OTHER fallback
- Update existing tests to work with new classification approach

## Benefits

1. **Flexibility**: System can handle documents outside predefined list
2. **Consistency**: Common documents grouped into standard categories
3. **Clarity**: Unknown documents clearly marked as OTHER with description
4. **Backward Compatible**: Existing specific types still work
5. **Better Organization**: Files grouped by high-level category for easier sorting

## Example Classifications

| Document | Classification | Reasoning |
|----------|---------------|-----------|
| QME Report | MEDICAL_REPORT | Fits standard category |
| AME Report | MEDICAL_REPORT | Fits standard category |
| Panel List | Panel List | Specific type, no standard category |
| Finding and Award | COURT_ORDER | Fits standard category |
| UR Denial | INSURANCE_CORRESPONDENCE | Fits standard category |
| Unknown Form | OTHER_Medical Form | Cannot classify specifically |

## Files to Modify

1. `src/scanner_watcher2/models.py` - Add DocumentType enum
2. `src/scanner_watcher2/core/ai_service.py` - Update prompt and classification logic
3. `src/scanner_watcher2/core/file_processor.py` - Ensure filename handling works
4. `tests/unit/test_ai_service.py` - Add enum classification tests
5. `tests/property/test_ai_service_properties.py` - Update property tests
6. `README.md` - Update documentation with new classification approach

## Success Criteria

- [ ] DocumentType enum created with 16 categories (15 + OTHER)
- [ ] AI prompt updated with prioritized classification logic
- [ ] System correctly maps common documents to enum categories
- [ ] System handles specific document types not in enum
- [ ] System returns OTHER_description for unclassifiable documents
- [ ] All existing tests pass
- [ ] New tests added for enum classification
- [ ] Documentation updated

## Notes

- This is a **breaking change** - existing document type names will change
- Consider migration strategy for existing classified files
- May want to add configuration option to use old vs new classification
- Should log when documents are classified as OTHER for monitoring
