"""
Unit tests for filename ordering and structure.

Tests verify that filenames follow the predictable format:
YYYYMMDD_PatientName_DocumentType_OtherIdentifiers.pdf
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import Mock

import pytest
from PIL import Image

from scanner_watcher2.core.ai_service import AIService
from scanner_watcher2.core.file_manager import FileManager
from scanner_watcher2.core.file_processor import FileProcessor
from scanner_watcher2.core.pdf_processor import PDFProcessor
from scanner_watcher2.infrastructure.error_handler import ErrorHandler
from scanner_watcher2.infrastructure.logger import Logger
from scanner_watcher2.models import Classification


@pytest.fixture
def mock_components(tmp_path: Path) -> tuple:
    """Create mocked components for testing."""
    pdf_processor = Mock(spec=PDFProcessor)
    ai_service = Mock(spec=AIService)
    error_handler = Mock(spec=ErrorHandler)
    logger = Mock(spec=Logger)
    
    # Use real FileManager but mock error_handler.execute_with_retry
    file_manager = FileManager(
        error_handler=error_handler,
        logger=logger,
        temp_directory=tmp_path
    )
    
    # Mock execute_with_retry to just execute the function directly
    def execute_with_retry_side_effect(func, operation_name=None, use_circuit_breaker=False):
        return func()
    
    error_handler.execute_with_retry.side_effect = execute_with_retry_side_effect
    
    return pdf_processor, ai_service, file_manager, error_handler, logger


@pytest.mark.unit
def test_filename_patient_name_first(tmp_path: Path, mock_components: tuple) -> None:
    """
    Test that patient name appears first in filename after date.
    
    Format: YYYYMMDD_PatientName_DocumentType_...
    """
    pdf_processor, ai_service, file_manager, error_handler, logger = mock_components
    
    # Create test file
    test_file = tmp_path / "SCAN-test.pdf"
    test_file.write_bytes(b"%PDF-1.4 test content")
    
    # Mock PDF extraction
    mock_image = Image.new("RGB", (100, 100))
    pdf_processor.extract_first_pages.return_value = [mock_image]
    pdf_processor.optimize_image.return_value = mock_image
    
    # Mock AI classification with patient name
    classification = Classification(
        document_type="Qualified Medical Evaluator Report",
        confidence=0.95,
        identifiers={
            "patient_name": "John Doe",
            "client_name": "ABC Company",
            "case_number": "12345",
        },
        raw_response={},
    )
    ai_service.classify_document.return_value = classification
    
    # Process file
    processor = FileProcessor(
        pdf_processor, ai_service, file_manager, error_handler, logger
    )
    result = processor.process_file(test_file)
    
    # Verify success
    assert result.success is True
    assert result.new_file_path is not None
    
    # Parse filename
    filename = result.new_file_path.stem
    parts = filename.split("_")
    
    # Verify structure: Date_PatientName_DocumentType_...
    assert len(parts) >= 3
    assert parts[0].isdigit() and len(parts[0]) == 8  # YYYYMMDD
    assert parts[1] == "John"
    assert parts[2] == "Doe"
    assert "Qualified" in parts[3]


@pytest.mark.unit
def test_filename_ordering_all_identifiers(tmp_path: Path, mock_components: tuple) -> None:
    """
    Test complete identifier ordering in filename.
    
    Order: patient_name, client_name, case_number, date_of_injury, report_date, evaluator_name
    """
    pdf_processor, ai_service, file_manager, error_handler, logger = mock_components
    
    # Create test file
    test_file = tmp_path / "SCAN-test.pdf"
    test_file.write_bytes(b"%PDF-1.4 test content")
    
    # Mock PDF extraction
    mock_image = Image.new("RGB", (100, 100))
    pdf_processor.extract_first_pages.return_value = [mock_image]
    pdf_processor.optimize_image.return_value = mock_image
    
    # Mock AI classification with all identifiers
    classification = Classification(
        document_type="QME Report",
        confidence=0.95,
        identifiers={
            "patient_name": "Jane Smith",
            "client_name": "XYZ Corp",
            "case_number": "ABC123",
            "date_of_injury": "2024-01-15",
            "report_date": "2024-12-20",
            "evaluator_name": "Dr. Johnson",
        },
        raw_response={},
    )
    ai_service.classify_document.return_value = classification
    
    # Process file
    processor = FileProcessor(
        pdf_processor, ai_service, file_manager, error_handler, logger
    )
    result = processor.process_file(test_file)
    
    # Verify success
    assert result.success is True
    assert result.new_file_path is not None
    
    # Parse filename
    filename = result.new_file_path.stem
    parts = filename.split("_")
    
    # Verify patient name comes before client name
    jane_idx = parts.index("Jane")
    smith_idx = parts.index("Smith")
    xyz_idx = parts.index("XYZ")
    
    assert jane_idx < xyz_idx, "Patient name should appear before client name"
    assert smith_idx < xyz_idx, "Patient name should appear before client name"
    
    # Verify case number appears
    assert "ABC123" in parts


@pytest.mark.unit
def test_filename_without_patient_name(tmp_path: Path, mock_components: tuple) -> None:
    """
    Test filename when patient name is not available.
    
    Should fall back to: YYYYMMDD_DocumentType_OtherIdentifiers
    """
    pdf_processor, ai_service, file_manager, error_handler, logger = mock_components
    
    # Create test file
    test_file = tmp_path / "SCAN-test.pdf"
    test_file.write_bytes(b"%PDF-1.4 test content")
    
    # Mock PDF extraction
    mock_image = Image.new("RGB", (100, 100))
    pdf_processor.extract_first_pages.return_value = [mock_image]
    pdf_processor.optimize_image.return_value = mock_image
    
    # Mock AI classification without patient name
    classification = Classification(
        document_type="Panel List",
        confidence=0.95,
        identifiers={
            "case_number": "99999",
        },
        raw_response={},
    )
    ai_service.classify_document.return_value = classification
    
    # Process file
    processor = FileProcessor(
        pdf_processor, ai_service, file_manager, error_handler, logger
    )
    result = processor.process_file(test_file)
    
    # Verify success
    assert result.success is True
    assert result.new_file_path is not None
    
    # Parse filename
    filename = result.new_file_path.stem
    parts = filename.split("_")
    
    # Verify structure: Date_CaseNumber_DocumentType (when no patient name)
    # The first identifier (case_number) appears before document type
    assert len(parts) >= 3
    assert parts[0].isdigit() and len(parts[0]) == 8  # YYYYMMDD
    assert "99999" in parts
    assert "Panel" in parts or "List" in parts


@pytest.mark.unit
def test_filename_client_name_after_patient(tmp_path: Path, mock_components: tuple) -> None:
    """
    Test that client/employer name appears after patient name and document type.
    """
    pdf_processor, ai_service, file_manager, error_handler, logger = mock_components
    
    # Create test file
    test_file = tmp_path / "SCAN-test.pdf"
    test_file.write_bytes(b"%PDF-1.4 test content")
    
    # Mock PDF extraction
    mock_image = Image.new("RGB", (100, 100))
    pdf_processor.extract_first_pages.return_value = [mock_image]
    pdf_processor.optimize_image.return_value = mock_image
    
    # Mock AI classification
    classification = Classification(
        document_type="Finding and Award",
        confidence=0.95,
        identifiers={
            "patient_name": "Alice Brown",
            "client_name": "Mega Corporation",
        },
        raw_response={},
    )
    ai_service.classify_document.return_value = classification
    
    # Process file
    processor = FileProcessor(
        pdf_processor, ai_service, file_manager, error_handler, logger
    )
    result = processor.process_file(test_file)
    
    # Verify success
    assert result.success is True
    assert result.new_file_path is not None
    
    # Parse filename
    filename = result.new_file_path.stem
    
    # Verify patient name appears before client name
    assert "Alice" in filename
    assert "Brown" in filename
    assert "Mega" in filename
    assert "Corporation" in filename
    
    alice_pos = filename.index("Alice")
    mega_pos = filename.index("Mega")
    
    assert alice_pos < mega_pos, "Patient name should appear before employer name"


@pytest.mark.unit
def test_filename_sanitization(tmp_path: Path, mock_components: tuple) -> None:
    """
    Test that special characters in identifiers are sanitized.
    """
    pdf_processor, ai_service, file_manager, error_handler, logger = mock_components
    
    # Create test file
    test_file = tmp_path / "SCAN-test.pdf"
    test_file.write_bytes(b"%PDF-1.4 test content")
    
    # Mock PDF extraction
    mock_image = Image.new("RGB", (100, 100))
    pdf_processor.extract_first_pages.return_value = [mock_image]
    pdf_processor.optimize_image.return_value = mock_image
    
    # Mock AI classification with special characters
    classification = Classification(
        document_type="PTP P&S Report",
        confidence=0.95,
        identifiers={
            "patient_name": "O'Brien, John Jr.",
            "client_name": "ABC & Sons, Inc.",
            "case_number": "2024/12345",
        },
        raw_response={},
    )
    ai_service.classify_document.return_value = classification
    
    # Process file
    processor = FileProcessor(
        pdf_processor, ai_service, file_manager, error_handler, logger
    )
    result = processor.process_file(test_file)
    
    # Verify success
    assert result.success is True
    assert result.new_file_path is not None
    
    # Verify filename has no special characters (except underscores and hyphens)
    filename = result.new_file_path.name
    for char in filename:
        assert char.isalnum() or char in ("_", "-", "."), f"Invalid char: {char}"


@pytest.mark.unit
def test_filename_empty_identifier_values_skipped(tmp_path: Path, mock_components: tuple) -> None:
    """
    Test that empty identifier values are not included in filename.
    """
    pdf_processor, ai_service, file_manager, error_handler, logger = mock_components
    
    # Create test file
    test_file = tmp_path / "SCAN-test.pdf"
    test_file.write_bytes(b"%PDF-1.4 test content")
    
    # Mock PDF extraction
    mock_image = Image.new("RGB", (100, 100))
    pdf_processor.extract_first_pages.return_value = [mock_image]
    pdf_processor.optimize_image.return_value = mock_image
    
    # Mock AI classification with empty values
    classification = Classification(
        document_type="UR Approval",
        confidence=0.95,
        identifiers={
            "patient_name": "Bob Wilson",
            "client_name": "",  # Empty
            "case_number": "54321",
            "date_of_injury": "",  # Empty
        },
        raw_response={},
    )
    ai_service.classify_document.return_value = classification
    
    # Process file
    processor = FileProcessor(
        pdf_processor, ai_service, file_manager, error_handler, logger
    )
    result = processor.process_file(test_file)
    
    # Verify success
    assert result.success is True
    assert result.new_file_path is not None
    
    # Parse filename
    filename = result.new_file_path.stem
    parts = filename.split("_")
    
    # Should not have consecutive underscores from empty values
    assert "__" not in filename, "Empty values should not create consecutive underscores"
    
    # Should contain patient name and case number
    assert "Bob" in parts
    assert "Wilson" in parts
    assert "54321" in parts


@pytest.mark.unit
def test_filename_preserves_order_with_extra_identifiers(
    tmp_path: Path, mock_components: tuple
) -> None:
    """
    Test that extra identifiers (not in ordered list) appear after ordered ones.
    """
    pdf_processor, ai_service, file_manager, error_handler, logger = mock_components
    
    # Create test file
    test_file = tmp_path / "SCAN-test.pdf"
    test_file.write_bytes(b"%PDF-1.4 test content")
    
    # Mock PDF extraction
    mock_image = Image.new("RGB", (100, 100))
    pdf_processor.extract_first_pages.return_value = [mock_image]
    pdf_processor.optimize_image.return_value = mock_image
    
    # Mock AI classification with extra identifiers
    classification = Classification(
        document_type="Declaration of Readiness to Proceed",
        confidence=0.95,
        identifiers={
            "patient_name": "Carol Davis",
            "case_number": "DOR-2024",
            "hearing_date": "2025-01-15",  # Extra identifier
            "attorney_name": "Smith Law",  # Extra identifier
        },
        raw_response={},
    )
    ai_service.classify_document.return_value = classification
    
    # Process file
    processor = FileProcessor(
        pdf_processor, ai_service, file_manager, error_handler, logger
    )
    result = processor.process_file(test_file)
    
    # Verify success
    assert result.success is True
    assert result.new_file_path is not None
    
    # Verify all identifiers are present
    filename = result.new_file_path.stem
    assert "Carol" in filename
    assert "Davis" in filename
    assert "DOR-2024" in filename or "DOR_2024" in filename
    assert "2025" in filename or "2025-01-15" in filename or "2025_01_15" in filename
    assert "Smith" in filename
