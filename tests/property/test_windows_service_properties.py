"""
Property-based tests for Windows service layer.
"""

import os
import platform
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from hypothesis import HealthCheck

from scanner_watcher2.config import (
    AIConfig,
    Config,
    LoggingConfig,
    ProcessingConfig,
    ServiceConfig,
)
from scanner_watcher2.service.windows_service import ScannerWatcher2Service


# Skip Windows service tests on non-Windows platforms
pytestmark = pytest.mark.skipif(
    platform.system() != "Windows", reason="Windows service tests require Windows platform"
)


@pytest.fixture
def temp_config_dir(tmp_path):
    """Create temporary configuration directory."""
    config_dir = tmp_path / "ScannerWatcher2"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


@pytest.fixture
def temp_log_dir(tmp_path):
    """Create temporary log directory."""
    log_dir = tmp_path / "ScannerWatcher2" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir


@pytest.fixture
def mock_config(temp_config_dir, tmp_path):
    """Create a mock configuration."""
    watch_dir = tmp_path / "watch"
    watch_dir.mkdir(exist_ok=True)

    return Config(
        version="1.0.0",
        watch_directory=watch_dir,
        openai_api_key="test-key-123",
        log_level="INFO",
        processing=ProcessingConfig(),
        ai=AIConfig(),
        logging=LoggingConfig(),
        service=ServiceConfig(),
    )


# Feature: scanner-watcher2, Property 15: Service start logging
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(service_name=st.text(min_size=1, max_size=50))
@pytest.mark.property
def test_service_start_logging(
    service_name, temp_config_dir, temp_log_dir, mock_config
):
    """
    For any service start event, the System should write an entry to Windows Event Log.

    **Validates: Requirements 4.4, 7.5**
    """
    # Mock Windows event log - patch where it's imported (inside the method)
    mock_report_event = Mock()

    # Mock the service initialization
    with patch.dict(os.environ, {"APPDATA": str(temp_config_dir.parent)}):
        with patch("scanner_watcher2.service.windows_service.ConfigManager") as mock_config_manager:
            with patch("scanner_watcher2.service.windows_service.ServiceOrchestrator") as mock_orchestrator:
                with patch("scanner_watcher2.service.windows_service.win32event") as mock_win32event:
                    # Patch win32evtlogutil where it's actually imported (inside _log_event method)
                    with patch("win32evtlogutil.ReportEvent", mock_report_event):
                        mock_win32event.EVENTLOG_INFORMATION_TYPE = 4
                        
                        # Setup mocks
                        mock_config_manager_instance = Mock()
                        mock_config_manager_instance.load_config.return_value = mock_config
                        mock_config_manager_instance.create_default_config.return_value = mock_config
                        mock_config_manager.return_value = mock_config_manager_instance

                        mock_orchestrator_instance = Mock()
                        mock_orchestrator.return_value = mock_orchestrator_instance

                        # Create service with empty args list (required by pywin32)
                        service = ScannerWatcher2Service(args=[])

                        # Mock the stop event to prevent blocking
                        if hasattr(service, "stop_event"):
                            if hasattr(service.stop_event, "set"):
                                service.stop_event.set()

                        # Call SvcDoRun which should log to event log
                        try:
                            service.SvcDoRun()
                        except Exception:
                            # Service may fail due to mocking, but we're checking the log call
                            pass

                        # Verify that ReportEvent was called for service start
                        assert mock_report_event.called, "Service start should log to Windows Event Log"

                        # Check that at least one call was made with service start message
                        calls = mock_report_event.call_args_list
                        service_start_logged = any(
                            "started" in str(call).lower() for call in calls
                        )
                        assert service_start_logged, "Service start message should be logged to Windows Event Log"


# Feature: scanner-watcher2, Property 16: Critical error logging
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(error_message=st.text(min_size=1, max_size=200))
@pytest.mark.property
def test_critical_error_logging(
    error_message, temp_config_dir, temp_log_dir
):
    """
    For any critical error encountered, the System should write an entry to Windows Event Log before stopping.

    **Validates: Requirements 4.5, 7.3**
    """
    # Mock Windows event log
    mock_report_event = Mock()

    # Mock the service initialization to raise an error
    with patch.dict(os.environ, {"APPDATA": str(temp_config_dir.parent)}):
        with patch("scanner_watcher2.service.windows_service.ConfigManager") as mock_config_manager:
            with patch("scanner_watcher2.service.windows_service.win32event") as mock_win32event:
                # Patch win32evtlogutil where it's actually imported (inside _log_event method)
                with patch("win32evtlogutil.ReportEvent", mock_report_event):
                    mock_win32event.EVENTLOG_ERROR_TYPE = 1
                    
                    # Setup mock to raise an error
                    mock_config_manager_instance = Mock()
                    mock_config_manager_instance.load_config.side_effect = Exception(error_message)
                    mock_config_manager.return_value = mock_config_manager_instance

                    # Create service with empty args list (required by pywin32)
                    service = ScannerWatcher2Service(args=[])

                    # Call SvcDoRun which should encounter error and log to event log
                    try:
                        service.SvcDoRun()
                    except Exception:
                        # Expected to fail
                        pass

                    # Verify that ReportEvent was called for critical error
                    assert mock_report_event.called, "Critical error should log to Windows Event Log"

                    # Check that at least one call was made with error event type
                    calls = mock_report_event.call_args_list
                    error_logged = any(
                        "error" in str(call).lower() or "critical" in str(call).lower()
                        for call in calls
                    )
                    assert error_logged, "Critical error message should be logged to Windows Event Log"
