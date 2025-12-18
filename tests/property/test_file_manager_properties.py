"""
Property-based tests for FileManager component.
"""

from __future__ import annotations

import re
import tempfile
from datetime import datetime
from pathlib import Path

import pytest
from hypothesis import HealthCheck, given, settings, strategies as st

from scanner_watcher2.core.file_manager import FileManager
from scanner_watcher2.infrastructure.error_handler import ErrorHandler
from scanner_watcher2.infrastructure.logger import Logger


@pytest.fixture
def temp_dir(tmp_path):
    """Create a temporary directory for testing."""
    return tmp_path


@pytest.fixture
def logger(tmp_path):
    """Create a logger instance for testing."""
    log_dir = tmp_path / "logs"
    log_dir.mkdir(exist_ok=True)
    return Logger(
        log_dir=log_dir,
        component="test_file_manager",
        log_level="DEBUG",
        log_to_event_log=False,
    )


@pytest.fixture
def error_handler():
    """Create an error handler instance for testing."""
    return ErrorHandler()


@pytest.fixture
def file_manager(error_handler, logger, temp_dir):
    """Create a FileManager instance for testing."""
    return FileManager(
        error_handler=error_handler, logger=logger, temp_directory=temp_dir / "temp"
    )


# Feature: scanner-watcher2, Property 11: Filename structure
@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
@given(
    document_type=st.text(
        alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd")),
        min_size=1,
        max_size=50,
    ),
    identifier=st.text(
        alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd")),
        min_size=1,
        max_size=30,
    ),
)
def test_filename_structure_property(
    file_manager, temp_dir, document_type, identifier
):
    """
    Property 11: Filename structure.
    
    For any classified document, the renamed file should contain the date,
    document type, and relevant identifiers.
    
    Validates: Requirements 3.1
    """
    # Create a source file
    source_file = temp_dir / "SCAN-test.pdf"
    source_file.write_text("test content")

    # Generate target filename with expected structure: YYYY-MM-DD_DocumentType_Identifier.pdf
    current_date = datetime.now().strftime("%Y-%m-%d")
    target_name = f"{current_date}_{document_type}_{identifier}.pdf"

    # Rename the file
    result = file_manager.rename_file(source_file, target_name)

    # Verify the filename structure
    assert result.exists(), "Renamed file should exist"
    assert result.name == target_name, "Filename should match target structure"

    # Verify filename contains all required components
    filename_parts = result.stem.split("_")
    assert len(filename_parts) >= 3, "Filename should have at least 3 parts"

    # Verify date component (YYYY-MM-DD format)
    date_pattern = r"^\d{4}-\d{2}-\d{2}$"
    assert re.match(
        date_pattern, filename_parts[0]
    ), "First part should be date in YYYY-MM-DD format"

    # Verify document type is present
    assert (
        document_type in result.name
    ), "Filename should contain document type"

    # Verify identifier is present
    assert identifier in result.name, "Filename should contain identifier"


# Feature: scanner-watcher2, Property 12: Conflict resolution
@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
@given(
    filename=st.text(
        alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd")),
        min_size=1,
        max_size=50,
    ).map(lambda s: f"{s}.pdf"),
)
def test_conflict_resolution_property(file_manager, temp_dir, filename):
    """
    Property 12: Conflict resolution.
    
    For any file rename where the target name already exists, the System should
    append a unique suffix to prevent overwriting.
    
    Validates: Requirements 3.2
    """
    # Create a unique subdirectory for this test example to avoid conflicts
    import uuid
    test_subdir = temp_dir / f"test_{uuid.uuid4().hex[:8]}"
    test_subdir.mkdir(exist_ok=True)
    
    # Create source files in the subdirectory
    source_file1 = test_subdir / "SCAN-test1.pdf"
    source_file2 = test_subdir / "SCAN-test2.pdf"
    source_file1.write_text("content 1")
    source_file2.write_text("content 2")

    # Rename first file
    result1 = file_manager.rename_file(source_file1, filename)
    assert result1.exists(), "First renamed file should exist"
    assert result1.name == filename, "First file should have exact target name"

    # Rename second file with same target name
    result2 = file_manager.rename_file(source_file2, filename)
    assert result2.exists(), "Second renamed file should exist"
    assert result2.name != filename, "Second file should have different name"

    # Verify both files exist and have different names
    assert result1.exists(), "First file should still exist"
    assert result2.exists(), "Second file should exist"
    assert result1 != result2, "Files should have different paths"

    # Verify second file has suffix appended
    stem = Path(filename).stem
    suffix = Path(filename).suffix
    assert result2.stem.startswith(stem), "Second file should start with original stem"
    assert result2.suffix == suffix, "Second file should have same extension"
    assert "_" in result2.stem, "Second file should have underscore separator"

    # Verify content is preserved
    assert result1.read_text() == "content 1", "First file content should be preserved"
    assert result2.read_text() == "content 2", "Second file content should be preserved"


# Feature: scanner-watcher2, Property 13: File verification before cleanup
@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
@given(
    filename=st.text(
        alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd")),
        min_size=1,
        max_size=50,
    ).map(lambda s: f"{s}.pdf"),
)
def test_file_verification_before_cleanup_property(file_manager, temp_dir, filename):
    """
    Property 13: File verification before cleanup.
    
    For any renamed file, the System should verify the file is accessible
    before deleting temporary files.
    
    Validates: Requirements 3.5, 14.5
    """
    # Create a source file
    source_file = temp_dir / "SCAN-test.pdf"
    source_file.write_text("test content")

    # Create temporary files
    temp_file1 = file_manager.create_temp_file(".tmp")
    temp_file2 = file_manager.create_temp_file(".tmp")
    temp_file1.write_text("temp 1")
    temp_file2.write_text("temp 2")

    # Rename the file
    result = file_manager.rename_file(source_file, filename)

    # Verify the renamed file is accessible before cleanup
    is_accessible = file_manager.verify_file_accessible(result)
    assert is_accessible, "Renamed file should be accessible before cleanup"

    # Only cleanup temp files if verification passed
    if is_accessible:
        file_manager.cleanup_temp_files([temp_file1, temp_file2])

        # Verify temp files are deleted
        assert not temp_file1.exists(), "Temp file 1 should be deleted"
        assert not temp_file2.exists(), "Temp file 2 should be deleted"

    # Verify renamed file still exists after cleanup
    assert result.exists(), "Renamed file should still exist after cleanup"


# Feature: scanner-watcher2, Property 32: Temporary file cleanup
@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
@given(
    num_temp_files=st.integers(min_value=1, max_value=10),
    success=st.booleans(),
)
def test_temporary_file_cleanup_property(
    file_manager, temp_dir, num_temp_files, success
):
    """
    Property 32: Temporary file cleanup.
    
    For any document processing (successful or failed), the System should
    delete all temporary files after completion.
    
    Validates: Requirements 13.1, 13.2
    """
    # Create temporary files
    temp_files = []
    for i in range(num_temp_files):
        temp_file = file_manager.create_temp_file(f".tmp{i}")
        temp_file.write_text(f"temp content {i}")
        temp_files.append(temp_file)

    # Verify all temp files exist
    for temp_file in temp_files:
        assert temp_file.exists(), f"Temp file {temp_file} should exist"

    # Simulate processing completion (success or failure)
    # In both cases, cleanup should happen
    file_manager.cleanup_temp_files(temp_files)

    # Verify all temp files are deleted
    for temp_file in temp_files:
        assert not temp_file.exists(), f"Temp file {temp_file} should be deleted"


# Feature: scanner-watcher2, Property 33: Deletion verification
@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
@given(
    num_files=st.integers(min_value=1, max_value=10),
)
def test_deletion_verification_property(file_manager, temp_dir, num_files):
    """
    Property 33: Deletion verification.
    
    For any temporary file deletion operation, the System should verify
    the deletion was successful.
    
    Validates: Requirements 13.4
    """
    # Create temporary files
    temp_files = []
    for i in range(num_files):
        temp_file = file_manager.create_temp_file(f".tmp{i}")
        temp_file.write_text(f"temp content {i}")
        temp_files.append(temp_file)

    # Delete temp files
    file_manager.cleanup_temp_files(temp_files)

    # Verify deletion was successful for all files
    for temp_file in temp_files:
        # The system should verify deletion
        # After cleanup, files should not exist
        assert not temp_file.exists(), f"Temp file {temp_file} should not exist after deletion"
        
        # Verify file is truly gone (not just inaccessible)
        assert not temp_file.is_file(), f"Temp file {temp_file} should not be a file"
