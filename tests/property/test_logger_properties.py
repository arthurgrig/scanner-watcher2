"""
Property-based tests for logging system.
"""

import json
import tempfile
from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from scanner_watcher2.infrastructure.logger import Logger


# Feature: scanner-watcher2, Property 22: Structured JSON logging
@given(
    message=st.text(min_size=1, max_size=200),
    component=st.text(min_size=1, max_size=50, alphabet=st.characters(blacklist_characters="\n\r\t")),
    context_key=st.text(min_size=1, max_size=20, alphabet=st.characters(min_codepoint=97, max_codepoint=122)),
    context_value=st.one_of(
        st.text(min_size=0, max_size=100),
        st.integers(),
        st.floats(allow_nan=False, allow_infinity=False),
    ),
)
@settings(max_examples=100)
@pytest.mark.property
def test_structured_json_logging(
    message: str, component: str, context_key: str, context_value: str | int | float
) -> None:
    """
    For any system operation, the System should write a structured JSON log entry to the log file.
    
    **Validates: Requirements 7.1**
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        log_dir = Path(temp_dir)
        logger = Logger(
            log_dir=log_dir,
            component=component,
            log_level="DEBUG",
            log_to_event_log=False,
        )

        try:
            # Log a message with context
            context = {context_key: context_value}
            logger.info(message, **context)

            # Read the log file
            log_file = log_dir / "scanner_watcher2.log"
            assert log_file.exists(), "Log file should be created"

            log_content = log_file.read_text(encoding="utf-8")
            assert log_content.strip(), "Log file should not be empty"

            # Parse the last log entry as JSON
            log_lines = [line for line in log_content.strip().split("\n") if line.strip()]
            assert len(log_lines) > 0, "Should have at least one log entry"

            last_log_entry = log_lines[-1]
            log_entry = json.loads(last_log_entry)

            # Verify structured JSON format
            assert isinstance(log_entry, dict), "Log entry should be a JSON object"
            assert "event" in log_entry, "Log entry should contain 'event' field"
            assert "timestamp" in log_entry, "Log entry should contain 'timestamp' field"
            assert "level" in log_entry, "Log entry should contain 'level' field"
            assert "component" in log_entry, "Log entry should contain 'component' field"

            # Verify the logged message and context
            assert log_entry["event"] == message, "Log entry should contain the message"
            assert log_entry["component"] == component, "Log entry should contain the component"
            assert context_key in log_entry, f"Log entry should contain context key '{context_key}'"
            assert log_entry[context_key] == context_value, "Log entry should contain the context value"
        finally:
            # Close logger handlers to release file locks on Windows
            if hasattr(logger, '_logger') and hasattr(logger._logger, 'handlers'):
                for handler in logger._logger.handlers[:]:
                    handler.close()
                    logger._logger.removeHandler(handler)


# Feature: scanner-watcher2, Property 23: Log rotation
@given(
    num_messages=st.integers(min_value=10, max_value=30),
    message_size=st.integers(min_value=50, max_value=150),
)
@settings(max_examples=20, deadline=5000)
@pytest.mark.property
def test_log_rotation(num_messages: int, message_size: int) -> None:
    """
    For any log file that reaches 10MB, the System should rotate the file and maintain 5 backup files.
    
    **Validates: Requirements 7.2**
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        log_dir = Path(temp_dir)
        
        # Use a very small max file size for testing (2KB instead of 10MB)
        max_file_size_kb = 2
        backup_count = 5
        
        logger = Logger(
            log_dir=log_dir,
            component="test_component",
            log_level="INFO",
            max_file_size_mb=max_file_size_kb / 1024,  # Convert KB to MB
            backup_count=backup_count,
            log_to_event_log=False,
        )

        try:
            # Generate enough log messages to trigger rotation
            large_message = "x" * message_size
            for i in range(num_messages):
                logger.info(f"Message {i}: {large_message}", iteration=i)

            # Check that log files exist
            log_file = log_dir / "scanner_watcher2.log"
            assert log_file.exists(), "Main log file should exist"

            # Count backup files
            backup_files = list(log_dir.glob("scanner_watcher2.log.*"))
            
            # Verify rotation occurred if we wrote enough data
            total_bytes_written = num_messages * (message_size + 100)  # Approximate
            max_bytes = max_file_size_kb * 1024
            
            if total_bytes_written > max_bytes:
                # Rotation should have occurred
                assert len(backup_files) > 0, "Backup files should be created when rotation occurs"
                
                # Should not exceed backup count
                assert len(backup_files) <= backup_count, (
                    f"Should not have more than {backup_count} backup files, found {len(backup_files)}"
                )
        finally:
            # Close logger handlers to release file locks on Windows
            if hasattr(logger, '_logger') and hasattr(logger._logger, 'handlers'):
                for handler in logger._logger.handlers[:]:
                    handler.close()
                    logger._logger.removeHandler(handler)


# Feature: scanner-watcher2, Property 24: Success logging completeness
@given(
    file_path=st.text(min_size=5, max_size=100),
    document_type=st.text(min_size=1, max_size=50),
    processing_time_ms=st.integers(min_value=1, max_value=60000),
    file_size_bytes=st.integers(min_value=1, max_value=10_000_000),
)
@settings(max_examples=100)
@pytest.mark.property
def test_success_logging_completeness(
    file_path: str, document_type: str, processing_time_ms: int, file_size_bytes: int
) -> None:
    """
    For any successfully processed file, the log entry should include processing time, file size, and document type.
    
    **Validates: Requirements 7.4, 15.1**
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        log_dir = Path(temp_dir)
        logger = Logger(
            log_dir=log_dir,
            component="FileProcessor",
            log_level="INFO",
            log_to_event_log=False,
        )

        try:
            # Log a successful file processing event
            logger.info(
                "File processed successfully",
                file_path=file_path,
                document_type=document_type,
                processing_time_ms=processing_time_ms,
                file_size_bytes=file_size_bytes,
            )

            # Read and parse the log file
            log_file = log_dir / "scanner_watcher2.log"
            log_content = log_file.read_text(encoding="utf-8")
            log_lines = [line for line in log_content.strip().split("\n") if line.strip()]
            
            last_log_entry = log_lines[-1]
            log_entry = json.loads(last_log_entry)

            # Verify all required fields are present
            assert "processing_time_ms" in log_entry, "Log should include processing_time_ms"
            assert "file_size_bytes" in log_entry, "Log should include file_size_bytes"
            assert "document_type" in log_entry, "Log should include document_type"
            assert "file_path" in log_entry, "Log should include file_path"

            # Verify the values match
            assert log_entry["processing_time_ms"] == processing_time_ms
            assert log_entry["file_size_bytes"] == file_size_bytes
            assert log_entry["document_type"] == document_type
            assert log_entry["file_path"] == file_path
        finally:
            # Close logger handlers to release file locks on Windows
            if hasattr(logger, '_logger') and hasattr(logger._logger, 'handlers'):
                for handler in logger._logger.handlers[:]:
                    handler.close()
                    logger._logger.removeHandler(handler)
