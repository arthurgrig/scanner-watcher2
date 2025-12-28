# Filename Structure

## Overview

Scanner-Watcher2 uses a structured, predictable filename format to ensure consistent file organization and easy sorting.

## Format

```
YYYYMMDD_PlaintiffName_DocumentType_AdditionalIdentifiers.pdf
```

## Components (in order)

1. **Date** (YYYYMMDD): Processing date in ISO format for chronological sorting
2. **Plaintiff Name**: Plaintiff/injured worker name - the lawyer's client (first identifier)
3. **Document Type**: Classified document type (e.g., "Qualified_Medical_Evaluator_Report")
4. **Additional Identifiers**: Remaining identifiers in predictable order

## Identifier Ordering

Identifiers are extracted and ordered as follows:

1. `plaintiff_name` - Plaintiff/injured worker name (lawyer's client) - **HIGHEST PRIORITY**
2. `plaintiff` - Alternative key for plaintiff
3. `patient_name` - Alternative for injured worker (same as plaintiff)
4. `client_name` - Employer/defendant company name
5. `case_number` - Case, claim, or file number
6. `date_of_injury` - Date of injury
7. `report_date` - Date of the report/document
8. `evaluator_name` - Name of doctor/evaluator
9. Any additional identifiers not in the above list

## Examples

### With All Identifiers
```
20251227_Anna_Free_Qualified_Medical_Evaluator_Report_Industrial_Staffing_Services_Inc_PZC50004284_9_9_2024_February_20_2025_Jeffrey_M_Karls.pdf
```

### With Minimal Identifiers
```
20251227_John_Doe_Finding_and_Award_ABC_Company.pdf
```

### Without Employer Name
```
20251227_Jane_Smith_Panel_List_12345.pdf
```

## Benefits

- **Chronological Sorting**: Date-first format ensures files sort by processing date
- **Plaintiff Grouping**: Plaintiff name as second component groups files by plaintiff (lawyer's client) when sorted
- **Predictable Structure**: Consistent ordering makes files easy to find and organize
- **Human Readable**: Underscores separate components for readability
- **Machine Parseable**: Structured format allows automated processing
- **Plaintiff Attorney Focused**: Prioritizes the plaintiff/injured worker name for easy case management

## AI Service Configuration

The AI service is configured to extract identifiers using standardized key names:
- `plaintiff_name` for plaintiff/injured worker (lawyer's client) - **HIGHEST PRIORITY**
- `plaintiff` as alternative key for plaintiff
- `patient_name` as alternative for injured worker
- `client_name` for employer/defendant company information
- `case_number` for case/claim identifiers
- And other standardized keys

This ensures consistent filename generation across all document types, with the plaintiff name always appearing first after the date.
