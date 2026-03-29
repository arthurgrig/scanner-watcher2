"""
Unit tests for data models.
"""

from datetime import datetime
from pathlib import Path

from scanner_watcher2.models import (
    Classification,
    DocumentType,
    ErrorType,
    HealthStatus,
    ProcessingResult,
)


class TestErrorType:
    """Test ErrorType enum."""

    def test_error_types_exist(self) -> None:
        """Verify all error types are defined."""
        assert ErrorType.TRANSIENT.value == "transient"
        assert ErrorType.PERMANENT.value == "permanent"
        assert ErrorType.CRITICAL.value == "critical"
        assert ErrorType.FATAL.value == "fatal"


class TestProcessingResult:
    """Test ProcessingResult dataclass."""

    def test_processing_result_creation(self) -> None:
        """Verify ProcessingResult can be created."""
        result = ProcessingResult(
            success=True,
            file_path=Path("/test/file.pdf"),
            document_type="Medical Report",
            new_file_path=Path("/test/2024-01-01_Medical_Report.pdf"),
            processing_time_ms=1234,
            error=None,
            correlation_id="test-123",
        )
        assert result.success is True
        assert result.document_type == "Medical Report"
        assert result.processing_time_ms == 1234


class TestClassification:
    """Test Classification dataclass."""

    def test_classification_creation(self) -> None:
        """Verify Classification can be created."""
        classification = Classification(
            document_type="Medical Report",
            confidence=0.95,
            identifiers={"patient_name": "John Doe"},
            raw_response={"type": "medical"},
        )
        assert classification.document_type == "Medical Report"
        assert classification.confidence == 0.95
        assert classification.identifiers["patient_name"] == "John Doe"


class TestHealthStatus:
    """Test HealthStatus dataclass."""

    def test_health_status_creation(self) -> None:
        """Verify HealthStatus can be created."""
        now = datetime.now()
        status = HealthStatus(
            is_healthy=True,
            watch_directory_accessible=True,
            config_valid=True,
            last_check_time=now,
            consecutive_failures=0,
            details={"memory_mb": 150},
        )
        assert status.is_healthy is True
        assert status.consecutive_failures == 0
        assert status.details["memory_mb"] == 150


class TestDocumentType:
    """Test DocumentType enum."""

    def test_document_type_enum_values(self) -> None:
        """Verify all document type enum values are defined."""
        # Existing categories
        assert DocumentType.MEDICAL_REPORT.value == "Medical Report"
        assert DocumentType.INJURY_REPORT.value == "Injury Report"
        assert DocumentType.CLAIM_FORM.value == "Claim Form"
        assert DocumentType.DEPOSITION.value == "Deposition"
        assert DocumentType.EXPERT_WITNESS_REPORT.value == "Expert Witness Report"
        assert DocumentType.SETTLEMENT_AGREEMENT.value == "Settlement Agreement"
        assert DocumentType.COURT_ORDER.value == "Court Order"
        assert DocumentType.INSURANCE_CORRESPONDENCE.value == "Insurance Correspondence"
        assert DocumentType.WAGE_STATEMENT.value == "Wage Statement"
        assert DocumentType.VOCATIONAL_REPORT.value == "Vocational Report"
        assert DocumentType.IME_REPORT.value == "IME Report"
        assert DocumentType.SURVEILLANCE_REPORT.value == "Surveillance Report"
        assert DocumentType.SUBPOENA.value == "Subpoena"
        assert DocumentType.MOTION.value == "Motion"
        assert DocumentType.BRIEF.value == "Brief"
        
        # New categories
        assert DocumentType.PANEL_LIST.value == "Panel List"
        assert DocumentType.QME_APPOINTMENT_NOTIFICATION.value == "QME Appointment Notification Form"
        assert DocumentType.AME_REPORT.value == "Agreed Medical Evaluator Report"
        assert DocumentType.QME_REPORT.value == "Qualified Medical Evaluator Report"
        assert DocumentType.PTP_INITIAL_REPORT.value == "PTP Initial Report"
        assert DocumentType.PTP_PS_REPORT.value == "PTP P&S Report"
        assert DocumentType.RFA.value == "RFA"
        assert DocumentType.UR_APPROVAL.value == "UR Approval"
        assert DocumentType.UR_DENIAL.value == "UR Denial"
        assert DocumentType.MODIFIED_UR.value == "Modified UR"
        assert DocumentType.FINDING_AND_AWARD.value == "Finding and Award"
        assert DocumentType.FINDING_AND_ORDER.value == "Finding & Order"
        assert DocumentType.ADVOCACY_COVER_LETTER.value == "Advocacy/Cover Letter"
        assert DocumentType.DECLARATION_OF_READINESS.value == "Declaration of Readiness to Proceed"
        assert DocumentType.OBJECTION_TO_DOR.value == "Objection to Declaration of Readiness to Proceed"
        
        assert DocumentType.OTHER.value == "Other"

    def test_document_type_enum_count(self) -> None:
        """Verify we have exactly 31 document type categories (30 + OTHER)."""
        assert len(DocumentType) == 31


class TestClassificationHelperMethods:
    """Test Classification helper methods for enum-based classification."""

    def test_is_standard_category_for_enum_value(self) -> None:
        """Verify is_standard_category returns True for enum values."""
        classification = Classification(
            document_type="Medical Report",
            confidence=0.95,
            identifiers={},
            raw_response={},
        )
        assert classification.is_standard_category is True

    def test_is_standard_category_for_specific_type(self) -> None:
        """Verify is_standard_category returns False for specific types not in enum."""
        classification = Classification(
            document_type="Custom Document Type",
            confidence=0.90,
            identifiers={},
            raw_response={},
        )
        assert classification.is_standard_category is False

    def test_is_other_for_other_prefix(self) -> None:
        """Verify is_other returns True for OTHER_ prefix."""
        classification = Classification(
            document_type="OTHER_Unidentified Medical Form",
            confidence=0.50,
            identifiers={},
            raw_response={},
        )
        assert classification.is_other is True

    def test_is_other_for_standard_category(self) -> None:
        """Verify is_other returns False for standard categories."""
        classification = Classification(
            document_type="Medical Report",
            confidence=0.95,
            identifiers={},
            raw_response={},
        )
        assert classification.is_other is False

    def test_is_other_for_specific_type(self) -> None:
        """Verify is_other returns False for specific types not in enum."""
        classification = Classification(
            document_type="Custom Document Type",
            confidence=0.90,
            identifiers={},
            raw_response={},
        )
        assert classification.is_other is False

    def test_all_enum_categories_recognized_as_standard(self) -> None:
        """Verify all enum values are recognized as standard categories."""
        for doc_type in DocumentType:
            if doc_type != DocumentType.OTHER:
                classification = Classification(
                    document_type=doc_type.value,
                    confidence=0.95,
                    identifiers={},
                    raw_response={},
                )
                assert classification.is_standard_category is True, \
                    f"{doc_type.value} should be recognized as standard category"
