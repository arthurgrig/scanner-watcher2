"""
Unit tests for ServiceOrchestrator.
"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from scanner_watcher2.config import (
    AIConfig,
    Config,
    LoggingConfig,
    ProcessingConfig,
    ServiceConfig,
)
from scanner_watcher2.service.orchestrator import ServiceOrchestrator


def create_test_config(watch_dirs: list[Path]) -> Config:
    """Create a test configuration."""
    return Config(
        version="1.0.0",
        watch_directories=watch_dirs,
        openai_api_key="test-key-12345",
        log_level="INFO",
        processing=ProcessingConfig(file_prefixes=["SCAN-", "DOC-"]),
        ai=AIConfig(),
        logging=LoggingConfig(log_to_event_log=False),
        service=ServiceConfig(),
    )


@pytest.mark.unit
def test_process_file_callback_logs_source_directory():
    """
    Test that _process_file_callback logs the source directory.
    
    Requirements: 7.3
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        watch_dir = Path(tmpdir) / "watch"
        watch_dir.mkdir()
        
        config = create_test_config([watch_dir])
        orchestrator = ServiceOrchestrator(config)
        
        # Mock the file processor to avoid actual processing
        orchestrator.file_processor.process_file = MagicMock()
        
        # Track info logs
        info_logs = []
        original_info = orchestrator.logger.info
        
        def tracked_info(message, **context):
            info_logs.append((message, context))
            return original_info(message, **context)
        
        orchestrator.logger.info = tracked_info
        
        # Start orchestrator to initialize watchers
        orchestrator.start()
        
        # Create a test file
        test_file = watch_dir / "SCAN-test.pdf"
        test_file.touch()
        
        # Call the callback directly
        orchestrator._process_file_callback(test_file)
        
        # Stop orchestrator
        orchestrator.stop(timeout=5)
        
        # Check that source directory was logged
        detection_logs = [
            (msg, ctx) for msg, ctx in info_logs 
            if "File detected for processing" in msg
        ]
        
        assert len(detection_logs) > 0, "Expected file detection to be logged"
        
        # Verify source directory is in the log
        _, context = detection_logs[0]
        assert "source_directory" in context, "Log should contain source_directory"
        assert context["source_directory"] == str(watch_dir), \
            f"Expected source_directory={watch_dir}, got {context['source_directory']}"


@pytest.mark.unit
def test_process_file_callback_logs_matched_prefix():
    """
    Test that _process_file_callback logs the matched prefix.
    
    Requirements: 7.4
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        watch_dir = Path(tmpdir) / "watch"
        watch_dir.mkdir()
        
        config = create_test_config([watch_dir])
        orchestrator = ServiceOrchestrator(config)
        
        # Mock the file processor to avoid actual processing
        orchestrator.file_processor.process_file = MagicMock()
        
        # Track info logs
        info_logs = []
        original_info = orchestrator.logger.info
        
        def tracked_info(message, **context):
            info_logs.append((message, context))
            return original_info(message, **context)
        
        orchestrator.logger.info = tracked_info
        
        # Start orchestrator to initialize watchers
        orchestrator.start()
        
        # Create a test file with DOC- prefix
        test_file = watch_dir / "DOC-test.pdf"
        test_file.touch()
        
        # Simulate the watcher detecting the file and storing the matched prefix
        for watcher in orchestrator.directory_watchers:
            if watcher.watch_path == watch_dir:
                # Manually set the matched prefix as the event handler would
                if watcher._event_handler:
                    watcher._event_handler._matched_prefixes[test_file] = "DOC-"
        
        # Call the callback directly
        orchestrator._process_file_callback(test_file)
        
        # Stop orchestrator
        orchestrator.stop(timeout=5)
        
        # Check that matched prefix was logged
        detection_logs = [
            (msg, ctx) for msg, ctx in info_logs 
            if "File detected for processing" in msg
        ]
        
        assert len(detection_logs) > 0, "Expected file detection to be logged"
        
        # Verify matched prefix is in the log
        _, context = detection_logs[0]
        assert "matched_prefix" in context, "Log should contain matched_prefix"
        assert context["matched_prefix"] == "DOC-", \
            f"Expected matched_prefix=DOC-, got {context['matched_prefix']}"


@pytest.mark.unit
def test_process_file_callback_logs_both_directory_and_prefix():
    """
    Test that _process_file_callback logs both source directory and matched prefix.
    
    Requirements: 7.3, 7.4
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        watch_dir = Path(tmpdir) / "watch"
        watch_dir.mkdir()
        
        config = create_test_config([watch_dir])
        orchestrator = ServiceOrchestrator(config)
        
        # Mock the file processor to avoid actual processing
        orchestrator.file_processor.process_file = MagicMock()
        
        # Track info logs
        info_logs = []
        original_info = orchestrator.logger.info
        
        def tracked_info(message, **context):
            info_logs.append((message, context))
            return original_info(message, **context)
        
        orchestrator.logger.info = tracked_info
        
        # Start orchestrator to initialize watchers
        orchestrator.start()
        
        # Create a test file
        test_file = watch_dir / "SCAN-test.pdf"
        test_file.touch()
        
        # Simulate the watcher detecting the file and storing the matched prefix
        for watcher in orchestrator.directory_watchers:
            if watcher.watch_path == watch_dir:
                # Manually set the matched prefix as the event handler would
                if watcher._event_handler:
                    watcher._event_handler._matched_prefixes[test_file] = "SCAN-"
        
        # Call the callback directly
        orchestrator._process_file_callback(test_file)
        
        # Stop orchestrator
        orchestrator.stop(timeout=5)
        
        # Check that both were logged
        detection_logs = [
            (msg, ctx) for msg, ctx in info_logs 
            if "File detected for processing" in msg
        ]
        
        assert len(detection_logs) > 0, "Expected file detection to be logged"
        
        # Verify both are in the log
        _, context = detection_logs[0]
        assert "source_directory" in context, "Log should contain source_directory"
        assert "matched_prefix" in context, "Log should contain matched_prefix"
        assert context["source_directory"] == str(watch_dir)
        assert context["matched_prefix"] == "SCAN-"


@pytest.mark.unit
def test_start_with_all_directories_existing():
    """
    Test startup with all directories existing.
    
    Requirements: 2.5
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        watch_dir1 = Path(tmpdir) / "watch1"
        watch_dir2 = Path(tmpdir) / "watch2"
        watch_dir1.mkdir()
        watch_dir2.mkdir()
        
        config = create_test_config([watch_dir1, watch_dir2])
        orchestrator = ServiceOrchestrator(config)
        
        # Start orchestrator
        orchestrator.start()
        
        # Verify that 2 watchers were created
        assert len(orchestrator.directory_watchers) == 2, \
            f"Expected 2 watchers, got {len(orchestrator.directory_watchers)}"
        
        # Stop orchestrator
        orchestrator.stop(timeout=5)


@pytest.mark.unit
def test_start_with_some_directories_missing():
    """
    Test startup with some directories missing.
    
    Requirements: 2.5
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        watch_dir1 = Path(tmpdir) / "watch1"
        watch_dir2 = Path(tmpdir) / "watch2"  # This one won't be created
        watch_dir1.mkdir()
        # watch_dir2 intentionally not created
        
        config = create_test_config([watch_dir1, watch_dir2])
        orchestrator = ServiceOrchestrator(config)
        
        # Track warning logs
        warning_logs = []
        original_warning = orchestrator.logger.warning
        
        def tracked_warning(message, **context):
            warning_logs.append((message, context))
            return original_warning(message, **context)
        
        orchestrator.logger.warning = tracked_warning
        
        # Start orchestrator - should succeed with only 1 watcher
        orchestrator.start()
        
        # Verify that only 1 watcher was created (for the existing directory)
        assert len(orchestrator.directory_watchers) == 1, \
            f"Expected 1 watcher, got {len(orchestrator.directory_watchers)}"
        
        # Verify that a warning was logged for the missing directory
        missing_dir_warnings = [
            (msg, ctx) for msg, ctx in warning_logs 
            if "does not exist" in msg
        ]
        assert len(missing_dir_warnings) > 0, "Expected warning for missing directory"
        
        # Stop orchestrator
        orchestrator.stop(timeout=5)


@pytest.mark.unit
def test_start_with_all_directories_missing():
    """
    Test startup with all directories missing (should fail).
    
    Requirements: 2.5
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        watch_dir1 = Path(tmpdir) / "watch1"  # Not created
        watch_dir2 = Path(tmpdir) / "watch2"  # Not created
        # Neither directory created
        
        config = create_test_config([watch_dir1, watch_dir2])
        orchestrator = ServiceOrchestrator(config)
        
        # Start should raise RuntimeError
        with pytest.raises(RuntimeError) as exc_info:
            orchestrator.start()
        
        assert "No valid watch directories found" in str(exc_info.value), \
            f"Expected error about no valid directories, got: {exc_info.value}"
