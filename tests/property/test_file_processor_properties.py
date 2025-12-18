"""
Property-based tests for file processor.
"""

import threading
import time
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest
from hypothesis import HealthCheck, given, settings, strategies as st

from scanner_watcher2.core.ai_service import AIService
from scanner_watcher2.core.file_manager import FileManager
from scanner_watcher2.core.file_processor import FileProcessor
from scanner_watcher2.core.pdf_processor import PDFProcessor
from scanner_watcher2.infrastructure.error_handler import ErrorHandler
from scanner_watcher2.infrastructure.logger import Logger
from scanner_watcher2.models import Classification


def create_test_pdf(output_path: Path, num_pages: int = 1) -> None:
    """
    Create a simple test PDF file.
    
    Args:
        output_path: Path where PDF should be saved
        num_pages: Number of pages to create
    """
    import fitz
    
    doc = fitz.open()
    
    for i in range(num_pages):
        page = doc.new_page(width=595, height=842)
        text = f"Test Page {i + 1}"
        page.insert_text((50, 50), text, fontsize=20)
    
    doc.save(str(output_path))
    doc.close()


# Feature: scanner-watcher2, Property 29: Sequential processing
@given(
    num_files=st.integers(min_value=2, max_value=5),
)
@settings(
    deadline=10000,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
    max_examples=20,  # Limit examples since this test involves threading
)
def test_sequential_processing_prevents_parallel_api_calls(
    temp_dir: Path,
    num_files: int,
) -> None:
    """
    For any queue of multiple files, the System should process them sequentially
    to avoid parallel API calls.
    
    This test verifies that:
    1. Files are processed one at a time
    2. No two API calls happen simultaneously
    3. Each file completes before the next begins
    
    Validates: Requirements 12.2
    """
    # Track API call timing to detect parallel execution
    api_call_times: list[tuple[float, float]] = []  # (start_time, end_time)
    api_call_lock = threading.Lock()
    
    # Create mock components
    pdf_processor = PDFProcessor()
    error_handler = ErrorHandler()
    
    # Create mock logger
    logger = Mock(spec=Logger)
    logger.debug = Mock()
    logger.info = Mock()
    logger.warning = Mock()
    logger.error = Mock()
    
    # Create file manager with temp directory
    file_manager = FileManager(
        error_handler=error_handler,
        logger=logger,
        temp_directory=temp_dir / "temp",
    )
    
    # Create mock AI service that tracks call timing
    def mock_classify_document(image):
        """Mock classification that records timing."""
        start_time = time.time()
        
        with api_call_lock:
            # Check if any other API call is currently in progress
            current_time = time.time()
            for call_start, call_end in api_call_times:
                # If this call overlaps with an existing call, we have parallel execution
                if call_start <= current_time <= call_end:
                    raise AssertionError(
                        f"Parallel API call detected! Current call at {current_time}, "
                        f"overlaps with call from {call_start} to {call_end}"
                    )
        
        # Simulate API call duration (small delay to make timing detectable)
        time.sleep(0.05)
        
        end_time = time.time()
        
        with api_call_lock:
            api_call_times.append((start_time, end_time))
        
        # Return mock classification
        return Classification(
            document_type="Test Document",
            confidence=0.95,
            identifiers={"test_id": "123"},
            raw_response={},
        )
    
    ai_service = Mock(spec=AIService)
    ai_service.classify_document = Mock(side_effect=mock_classify_document)
    
    # Create file processor
    file_processor = FileProcessor(
        pdf_processor=pdf_processor,
        ai_service=ai_service,
        file_manager=file_manager,
        error_handler=error_handler,
        logger=logger,
    )
    
    # Create test PDF files
    test_files = []
    for i in range(num_files):
        pdf_path = temp_dir / f"SCAN-test-{i}.pdf"
        create_test_pdf(pdf_path, num_pages=1)
        test_files.append(pdf_path)
    
    # Process files sequentially (simulating the queue processing)
    results = []
    for pdf_path in test_files:
        result = file_processor.process_file(pdf_path)
        results.append(result)
    
    # Verify all files were processed
    assert len(results) == num_files
    
    # Verify all API calls completed
    assert len(api_call_times) == num_files
    
    # Verify no overlapping API calls (sequential processing)
    sorted_calls = sorted(api_call_times, key=lambda x: x[0])
    for i in range(len(sorted_calls) - 1):
        current_end = sorted_calls[i][1]
        next_start = sorted_calls[i + 1][0]
        
        # Next call should start after current call ends
        assert next_start >= current_end, (
            f"API calls overlapped: call {i} ended at {current_end}, "
            f"but call {i+1} started at {next_start}"
        )
    
    # Verify AI service was called exactly once per file
    assert ai_service.classify_document.call_count == num_files


# Feature: scanner-watcher2, Property 29: Sequential processing
def test_sequential_processing_with_single_file(temp_dir: Path) -> None:
    """
    For a single file, processing should complete successfully.
    
    This is an edge case for sequential processing.
    
    Validates: Requirements 12.2
    """
    # Create mock components
    pdf_processor = PDFProcessor()
    error_handler = ErrorHandler()
    
    logger = Mock(spec=Logger)
    logger.debug = Mock()
    logger.info = Mock()
    logger.warning = Mock()
    logger.error = Mock()
    
    file_manager = FileManager(
        error_handler=error_handler,
        logger=logger,
        temp_directory=temp_dir / "temp",
    )
    
    ai_service = Mock(spec=AIService)
    ai_service.classify_document = Mock(
        return_value=Classification(
            document_type="Test Document",
            confidence=0.95,
            identifiers={},
            raw_response={},
        )
    )
    
    file_processor = FileProcessor(
        pdf_processor=pdf_processor,
        ai_service=ai_service,
        file_manager=file_manager,
        error_handler=error_handler,
        logger=logger,
    )
    
    # Create single test PDF
    pdf_path = temp_dir / "SCAN-test.pdf"
    create_test_pdf(pdf_path, num_pages=1)
    
    # Process file
    result = file_processor.process_file(pdf_path)
    
    # Verify success
    assert result.success is True
    assert ai_service.classify_document.call_count == 1


# Feature: scanner-watcher2, Property 29: Sequential processing
def test_file_processor_validates_file_before_processing(temp_dir: Path) -> None:
    """
    For any file, validation should occur before processing begins.
    
    Validates: Requirements 2.1, 6.4
    """
    # Create mock components
    pdf_processor = Mock(spec=PDFProcessor)
    ai_service = Mock(spec=AIService)
    error_handler = ErrorHandler()
    
    logger = Mock(spec=Logger)
    logger.debug = Mock()
    logger.info = Mock()
    logger.warning = Mock()
    logger.error = Mock()
    
    file_manager = FileManager(
        error_handler=error_handler,
        logger=logger,
        temp_directory=temp_dir / "temp",
    )
    
    file_processor = FileProcessor(
        pdf_processor=pdf_processor,
        ai_service=ai_service,
        file_manager=file_manager,
        error_handler=error_handler,
        logger=logger,
    )
    
    # Test with non-existent file
    nonexistent_path = temp_dir / "nonexistent.pdf"
    result = file_processor.process_file(nonexistent_path)
    
    # Should fail validation
    assert result.success is False
    assert "validation failed" in result.error.lower()
    
    # PDF processor and AI service should not be called
    pdf_processor.extract_first_pages.assert_not_called()
    ai_service.classify_document.assert_not_called()


# Feature: scanner-watcher2, Property 29: Sequential processing
def test_file_processor_handles_pdf_extraction_errors(temp_dir: Path) -> None:
    """
    For any file where PDF extraction fails, processing should fail gracefully
    and continue with other files.
    
    Validates: Requirements 6.4
    """
    # Create mock components
    pdf_processor = Mock(spec=PDFProcessor)
    pdf_processor.extract_first_pages = Mock(
        side_effect=ValueError("Corrupted PDF")
    )
    
    ai_service = Mock(spec=AIService)
    error_handler = ErrorHandler()
    
    logger = Mock(spec=Logger)
    logger.debug = Mock()
    logger.info = Mock()
    logger.warning = Mock()
    logger.error = Mock()
    
    file_manager = FileManager(
        error_handler=error_handler,
        logger=logger,
        temp_directory=temp_dir / "temp",
    )
    
    file_processor = FileProcessor(
        pdf_processor=pdf_processor,
        ai_service=ai_service,
        file_manager=file_manager,
        error_handler=error_handler,
        logger=logger,
    )
    
    # Create test PDF
    pdf_path = temp_dir / "test.pdf"
    create_test_pdf(pdf_path, num_pages=1)
    
    # Process file
    result = file_processor.process_file(pdf_path)
    
    # Should fail with error
    assert result.success is False
    assert "extraction failed" in result.error.lower()
    
    # AI service should not be called
    ai_service.classify_document.assert_not_called()


# Feature: scanner-watcher2, Property 29: Sequential processing
def test_file_processor_handles_ai_classification_errors(temp_dir: Path) -> None:
    """
    For any file where AI classification fails, processing should fail gracefully
    and continue with other files.
    
    Validates: Requirements 6.4
    """
    # Create mock components
    pdf_processor = PDFProcessor()
    
    ai_service = Mock(spec=AIService)
    ai_service.classify_document = Mock(
        side_effect=Exception("API error")
    )
    
    error_handler = ErrorHandler()
    
    logger = Mock(spec=Logger)
    logger.debug = Mock()
    logger.info = Mock()
    logger.warning = Mock()
    logger.error = Mock()
    
    file_manager = FileManager(
        error_handler=error_handler,
        logger=logger,
        temp_directory=temp_dir / "temp",
    )
    
    file_processor = FileProcessor(
        pdf_processor=pdf_processor,
        ai_service=ai_service,
        file_manager=file_manager,
        error_handler=error_handler,
        logger=logger,
    )
    
    # Create test PDF
    pdf_path = temp_dir / "test.pdf"
    create_test_pdf(pdf_path, num_pages=1)
    
    # Process file
    result = file_processor.process_file(pdf_path)
    
    # Should fail with error
    assert result.success is False
    assert "classification failed" in result.error.lower()


# Feature: scanner-watcher2, Property 29: Sequential processing
def test_file_processor_tracks_processing_metrics(temp_dir: Path) -> None:
    """
    For any successfully processed file, the result should include processing metrics.
    
    Validates: Requirements 15.1
    """
    # Create mock components
    pdf_processor = PDFProcessor()
    error_handler = ErrorHandler()
    
    logger = Mock(spec=Logger)
    logger.debug = Mock()
    logger.info = Mock()
    logger.warning = Mock()
    logger.error = Mock()
    
    file_manager = FileManager(
        error_handler=error_handler,
        logger=logger,
        temp_directory=temp_dir / "temp",
    )
    
    ai_service = Mock(spec=AIService)
    ai_service.classify_document = Mock(
        return_value=Classification(
            document_type="Test Document",
            confidence=0.95,
            identifiers={"case_number": "12345"},
            raw_response={},
        )
    )
    
    file_processor = FileProcessor(
        pdf_processor=pdf_processor,
        ai_service=ai_service,
        file_manager=file_manager,
        error_handler=error_handler,
        logger=logger,
    )
    
    # Create test PDF
    pdf_path = temp_dir / "SCAN-test.pdf"
    create_test_pdf(pdf_path, num_pages=1)
    
    # Process file
    result = file_processor.process_file(pdf_path)
    
    # Verify success
    assert result.success is True
    
    # Verify metrics are tracked
    assert result.processing_time_ms > 0
    assert result.correlation_id is not None
    assert len(result.correlation_id) > 0
    assert result.document_type == "Test Document"
    
    # Verify logger was called with metrics
    # Find the success log call
    success_log_calls = [
        call for call in logger.info.call_args_list
        if "processed successfully" in str(call).lower()
    ]
    assert len(success_log_calls) > 0
    
    # Verify the success log includes required metrics
    success_call = success_log_calls[0]
    call_kwargs = success_call[1] if len(success_call) > 1 else {}
    
    assert "processing_time_ms" in call_kwargs
    assert "file_size_bytes" in call_kwargs
    assert "document_type" in call_kwargs



# Feature: scanner-watcher2, Property: Error file renaming
def test_file_processor_renames_with_error_prefix_on_pdf_extraction_failure(temp_dir: Path) -> None:
    """
    For any file where PDF extraction fails, the file should be renamed with ERROR prefix.
    
    Validates: Requirements 6.4, Error Handling
    """
    # Create mock components
    pdf_processor = Mock(spec=PDFProcessor)
    pdf_processor.extract_first_pages = Mock(
        side_effect=ValueError("Corrupted PDF")
    )
    
    ai_service = Mock(spec=AIService)
    error_handler = ErrorHandler()
    
    logger = Mock(spec=Logger)
    logger.debug = Mock()
    logger.info = Mock()
    logger.warning = Mock()
    logger.error = Mock()
    
    file_manager = FileManager(
        error_handler=error_handler,
        logger=logger,
        temp_directory=temp_dir / "temp",
    )
    
    file_processor = FileProcessor(
        pdf_processor=pdf_processor,
        ai_service=ai_service,
        file_manager=file_manager,
        error_handler=error_handler,
        logger=logger,
    )
    
    # Create test PDF
    pdf_path = temp_dir / "SCAN-test.pdf"
    create_test_pdf(pdf_path, num_pages=1)
    
    # Process file
    result = file_processor.process_file(pdf_path)
    
    # Should fail with error
    assert result.success is False
    assert "extraction failed" in result.error.lower()
    
    # File should be renamed with ERROR prefix
    assert result.new_file_path is not None
    assert "ERROR" in result.new_file_path.name
    assert result.new_file_path.exists()
    
    # Original file should not exist
    assert not pdf_path.exists()
    
    # AI service should not be called
    ai_service.classify_document.assert_not_called()


# Feature: scanner-watcher2, Property: Error file renaming
def test_file_processor_renames_with_unknown_prefix_on_ai_failure(temp_dir: Path) -> None:
    """
    For any file where AI classification fails, the file should be renamed with UNKNOWN prefix.
    
    Validates: Requirements 6.4, Error Handling
    """
    # Create mock components
    pdf_processor = PDFProcessor()
    
    ai_service = Mock(spec=AIService)
    ai_service.classify_document = Mock(
        side_effect=Exception("API error")
    )
    
    error_handler = ErrorHandler()
    
    logger = Mock(spec=Logger)
    logger.debug = Mock()
    logger.info = Mock()
    logger.warning = Mock()
    logger.error = Mock()
    
    file_manager = FileManager(
        error_handler=error_handler,
        logger=logger,
        temp_directory=temp_dir / "temp",
    )
    
    file_processor = FileProcessor(
        pdf_processor=pdf_processor,
        ai_service=ai_service,
        file_manager=file_manager,
        error_handler=error_handler,
        logger=logger,
    )
    
    # Create test PDF
    pdf_path = temp_dir / "SCAN-test.pdf"
    create_test_pdf(pdf_path, num_pages=1)
    
    # Process file
    result = file_processor.process_file(pdf_path)
    
    # Should fail with error
    assert result.success is False
    assert "classification failed" in result.error.lower()
    
    # File should be renamed with UNKNOWN prefix
    assert result.new_file_path is not None
    assert "UNKNOWN" in result.new_file_path.name
    assert result.new_file_path.exists()
    
    # Original file should not exist
    assert not pdf_path.exists()


# Feature: scanner-watcher2, Property: Error file renaming
def test_file_processor_error_renamed_files_include_date_and_original_name(temp_dir: Path) -> None:
    """
    For any file renamed with error prefix, the new name should include date and original name.
    
    Format: YYYYMMDD_PREFIX_OriginalName.pdf
    
    Validates: Requirements 6.4, Error Handling
    """
    from datetime import datetime
    
    # Create mock components
    pdf_processor = Mock(spec=PDFProcessor)
    pdf_processor.extract_first_pages = Mock(
        side_effect=ValueError("Corrupted PDF")
    )
    
    ai_service = Mock(spec=AIService)
    error_handler = ErrorHandler()
    
    logger = Mock(spec=Logger)
    logger.debug = Mock()
    logger.info = Mock()
    logger.warning = Mock()
    logger.error = Mock()
    
    file_manager = FileManager(
        error_handler=error_handler,
        logger=logger,
        temp_directory=temp_dir / "temp",
    )
    
    file_processor = FileProcessor(
        pdf_processor=pdf_processor,
        ai_service=ai_service,
        file_manager=file_manager,
        error_handler=error_handler,
        logger=logger,
    )
    
    # Create test PDF with specific name
    original_name = "SCAN-invoice-12345"
    pdf_path = temp_dir / f"{original_name}.pdf"
    create_test_pdf(pdf_path, num_pages=1)
    
    # Process file
    result = file_processor.process_file(pdf_path)
    
    # Should fail with error
    assert result.success is False
    
    # File should be renamed with proper format
    assert result.new_file_path is not None
    new_name = result.new_file_path.name
    
    # Check format: YYYYMMDD_ERROR_OriginalName.pdf
    today = datetime.now().strftime("%Y%m%d")
    assert new_name.startswith(today)
    assert "ERROR" in new_name
    assert original_name in new_name
    assert new_name.endswith(".pdf")


# Feature: scanner-watcher2, Property: Error file renaming
def test_file_processor_handles_rename_failure_gracefully(temp_dir: Path) -> None:
    """
    For any file where error renaming fails, the processor should handle it gracefully.
    
    Validates: Requirements 6.4, Error Handling
    """
    # Create mock components
    pdf_processor = Mock(spec=PDFProcessor)
    pdf_processor.extract_first_pages = Mock(
        side_effect=ValueError("Corrupted PDF")
    )
    
    ai_service = Mock(spec=AIService)
    error_handler = ErrorHandler()
    
    logger = Mock(spec=Logger)
    logger.debug = Mock()
    logger.info = Mock()
    logger.warning = Mock()
    logger.error = Mock()
    
    # Create file manager that fails on rename
    file_manager = Mock(spec=FileManager)
    file_manager.rename_file = Mock(
        side_effect=OSError("Permission denied")
    )
    
    file_processor = FileProcessor(
        pdf_processor=pdf_processor,
        ai_service=ai_service,
        file_manager=file_manager,
        error_handler=error_handler,
        logger=logger,
    )
    
    # Create test PDF
    pdf_path = temp_dir / "SCAN-test.pdf"
    create_test_pdf(pdf_path, num_pages=1)
    
    # Process file
    result = file_processor.process_file(pdf_path)
    
    # Should fail with error
    assert result.success is False
    
    # new_file_path should be the original path (rename failed)
    assert result.new_file_path == pdf_path
    
    # Logger should have logged the rename failure
    error_calls = [call for call in logger.error.call_args_list]
    rename_error_logged = any(
        "rename" in str(call).lower() for call in error_calls
    )
    assert rename_error_logged


# Feature: scanner-watcher2, Property: Error file renaming
@given(
    error_type=st.sampled_from(["pdf_extraction", "image_optimization", "ai_classification"]),
)
@settings(
    deadline=5000,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
    max_examples=10,
)
def test_file_processor_always_renames_on_any_error(
    temp_dir: Path,
    error_type: str,
) -> None:
    """
    For any type of processing error, the file should always be renamed with appropriate prefix.
    
    Validates: Requirements 6.4, Error Handling
    """
    # Create mock components based on error type
    pdf_processor = Mock(spec=PDFProcessor) if error_type != "pdf_extraction" else PDFProcessor()
    ai_service = Mock(spec=AIService)
    error_handler = ErrorHandler()
    
    logger = Mock(spec=Logger)
    logger.debug = Mock()
    logger.info = Mock()
    logger.warning = Mock()
    logger.error = Mock()
    
    file_manager = FileManager(
        error_handler=error_handler,
        logger=logger,
        temp_directory=temp_dir / "temp",
    )
    
    # Configure mocks based on error type
    if error_type == "pdf_extraction":
        pdf_processor = Mock(spec=PDFProcessor)
        pdf_processor.extract_first_pages = Mock(side_effect=ValueError("PDF error"))
        expected_prefix = "ERROR"
    elif error_type == "image_optimization":
        from PIL import Image
        pdf_processor.extract_first_pages = Mock(return_value=[Image.new("RGB", (100, 100))])
        pdf_processor.optimize_image = Mock(side_effect=ValueError("Optimization error"))
        expected_prefix = "ERROR"
    else:  # ai_classification
        from PIL import Image
        pdf_processor.extract_first_pages = Mock(return_value=[Image.new("RGB", (100, 100))])
        pdf_processor.optimize_image = Mock(return_value=Image.new("RGB", (100, 100)))
        ai_service.classify_document = Mock(side_effect=Exception("AI error"))
        expected_prefix = "UNKNOWN"
    
    file_processor = FileProcessor(
        pdf_processor=pdf_processor,
        ai_service=ai_service,
        file_manager=file_manager,
        error_handler=error_handler,
        logger=logger,
    )
    
    # Create test PDF
    pdf_path = temp_dir / f"SCAN-test-{error_type}.pdf"
    create_test_pdf(pdf_path, num_pages=1)
    
    # Process file
    result = file_processor.process_file(pdf_path)
    
    # Should fail
    assert result.success is False
    
    # File should be renamed with appropriate prefix
    assert result.new_file_path is not None
    assert expected_prefix in result.new_file_path.name
    assert result.new_file_path.exists()
    
    # Original file should not exist
    assert not pdf_path.exists()
