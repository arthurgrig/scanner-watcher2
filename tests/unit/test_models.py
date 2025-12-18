"""
Unit tests for data models.
"""

from datetime import datetime
from pathlib import Path

from scanner_watcher2.models import (
    Classification,
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
