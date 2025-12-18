"""
Property-based tests for ServiceOrchestrator.
"""

import os
import tempfile
import time
from pathlib import Path
from threading import Event

import pytest
from hypothesis import given, settings, strategies as st, HealthCheck

from scanner_watcher2.config import (
    AIConfig,
    Config,
    LoggingConfig,
    ProcessingConfig,
    ServiceConfig,
)
from scanner_watcher2.service.orchestrator import ServiceOrchestrator


def create_test_config(watch_dir: Path) -> Config:
    """Create a test configuration."""
    return Config(
        version="1.0.0",
        watch_directory=watch_dir,
        openai_api_key="test-key-12345",
        log_level="INFO",
        processing=ProcessingConfig(),
        ai=AIConfig(),
        logging=LoggingConfig(log_to_event_log=False),
        service=ServiceConfig(),
    )


# Feature: scanner-watcher2, Property 14: Graceful shutdown timing
@settings(max_examples=10, deadline=None)
@given(timeout=st.integers(min_value=1, max_value=10))
def test_graceful_shutdown_timing(timeout):
    """
    For any service stop request, the System should complete shutdown within the specified timeout.
    
    **Validates: Requirements 4.3**
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        watch_dir = Path(tmpdir)
        config = create_test_config(watch_dir)
        config.service.graceful_shutdown_timeout_seconds = timeout
        
        orchestrator = ServiceOrchestrator(config)
        orchestrator.start()
        
        # Measure shutdown time
        start_time = time.time()
        orchestrator.stop(timeout=timeout)
        elapsed = time.time() - start_time
        
        # Should complete within timeout (with small buffer for overhead)
        assert elapsed <= timeout + 1.0, f"Shutdown took {elapsed}s, expected <={timeout}s"



# Feature: scanner-watcher2, Property 34: Health check interval
@settings(max_examples=10, deadline=None)
@given(interval=st.integers(min_value=1, max_value=5))
def test_health_check_interval(interval):
    """
    For any 60-second period while the System is running, a health check should be performed.
    
    **Validates: Requirements 10.1**
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        watch_dir = Path(tmpdir)
        config = create_test_config(watch_dir)
        config.service.health_check_interval_seconds = interval
        
        orchestrator = ServiceOrchestrator(config)
        orchestrator.start()
        
        # Track health check calls
        original_health_check = orchestrator.health_check
        check_times = []
        
        def tracked_health_check():
            check_times.append(time.time())
            return original_health_check()
        
        orchestrator.health_check = tracked_health_check
        
        # Wait for at least 2 health checks
        time.sleep(interval * 2.5)
        
        orchestrator.stop(timeout=5)
        
        # Should have at least 2 health checks
        assert len(check_times) >= 2, f"Expected at least 2 health checks, got {len(check_times)}"
        
        # Check intervals between health checks
        for i in range(1, len(check_times)):
            actual_interval = check_times[i] - check_times[i-1]
            # Allow some tolerance for timing
            assert interval * 0.8 <= actual_interval <= interval * 1.5, \
                f"Health check interval {actual_interval}s not within expected range [{interval * 0.8}, {interval * 1.5}]"



# Feature: scanner-watcher2, Property 35: Health check completeness
@settings(max_examples=10, deadline=None)
@given(watch_dir_exists=st.booleans())
def test_health_check_completeness(watch_dir_exists):
    """
    For any health check performed, the System should verify both Watch Directory accessibility
    and Configuration File validity.
    
    **Validates: Requirements 10.2, 10.3**
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        if watch_dir_exists:
            watch_dir = Path(tmpdir) / "watch"
            watch_dir.mkdir()
        else:
            watch_dir = Path(tmpdir) / "nonexistent"
        
        config = create_test_config(watch_dir)
        orchestrator = ServiceOrchestrator(config)
        
        # Perform health check
        health_status = orchestrator.health_check()
        
        # Should check watch directory accessibility
        assert hasattr(health_status, 'watch_directory_accessible'), \
            "Health status missing watch_directory_accessible field"
        assert health_status.watch_directory_accessible == watch_dir_exists, \
            f"Expected watch_directory_accessible={watch_dir_exists}, got {health_status.watch_directory_accessible}"
        
        # Should check config validity
        assert hasattr(health_status, 'config_valid'), \
            "Health status missing config_valid field"
        assert health_status.config_valid is True, \
            "Config should be valid"
        
        # Details should contain both checks
        assert 'watch_directory_accessible' in health_status.details, \
            "Health status details missing watch_directory_accessible"
        assert 'config_valid' in health_status.details, \
            "Health status details missing config_valid"



# Feature: scanner-watcher2, Property 36: Health check failure logging
@settings(max_examples=10, deadline=None)
@given(consecutive_failures=st.integers(min_value=1, max_value=5))
def test_health_check_failure_logging(consecutive_failures):
    """
    For any failed health check, the System should log a warning with details about the failure.
    
    **Validates: Requirements 10.4**
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        # Use non-existent watch directory to trigger failure
        watch_dir = Path(tmpdir) / "nonexistent"
        config = create_test_config(watch_dir)
        
        orchestrator = ServiceOrchestrator(config)
        
        # Track warning logs
        warning_logs = []
        original_warning = orchestrator.logger.warning
        
        def tracked_warning(message, **context):
            warning_logs.append((message, context))
            return original_warning(message, **context)
        
        orchestrator.logger.warning = tracked_warning
        
        # Perform multiple health checks to trigger failures
        for _ in range(consecutive_failures):
            health_status = orchestrator.health_check()
            assert not health_status.is_healthy, "Health check should fail with non-existent directory"
        
        # Should have logged warnings for each failure
        assert len(warning_logs) >= consecutive_failures, \
            f"Expected at least {consecutive_failures} warning logs, got {len(warning_logs)}"
        
        # Each warning should contain details
        for message, context in warning_logs:
            if "Health check failed" in message:
                assert 'details' in context, "Warning log missing details"
                assert 'consecutive_failures' in context, "Warning log missing consecutive_failures"



# Feature: scanner-watcher2, Property 38: Memory usage logging
@settings(max_examples=10, deadline=None)
@given(seed=st.integers(min_value=1, max_value=100))
def test_memory_usage_logging(seed):
    """
    For any health check performed, the System should log current memory usage.
    
    **Validates: Requirements 15.3**
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        watch_dir = Path(tmpdir)
        config = create_test_config(watch_dir)
        
        orchestrator = ServiceOrchestrator(config)
        
        # Track info logs
        info_logs = []
        original_info = orchestrator.logger.info
        
        def tracked_info(message, **context):
            info_logs.append((message, context))
            return original_info(message, **context)
        
        orchestrator.logger.info = tracked_info
        
        # Perform health check
        health_status = orchestrator.health_check()
        
        # Should have logged memory usage
        memory_logs = [
            (msg, ctx) for msg, ctx in info_logs 
            if "Memory usage" in msg or "memory_mb" in ctx
        ]
        
        assert len(memory_logs) > 0, "Expected memory usage to be logged during health check"
        
        # Memory usage should be in details
        assert 'memory_usage_mb' in health_status.details, \
            "Health status details missing memory_usage_mb"
        
        # Memory usage should be a positive number
        memory_mb = health_status.details['memory_usage_mb']
        assert isinstance(memory_mb, (int, float)), \
            f"Memory usage should be numeric, got {type(memory_mb)}"
        assert memory_mb > 0, f"Memory usage should be positive, got {memory_mb}"



# Feature: scanner-watcher2, Property 39: Average processing time calculation
@settings(max_examples=10, deadline=None)
@given(processing_times=st.lists(st.integers(min_value=100, max_value=5000), min_size=1, max_size=10))
def test_average_processing_time_calculation(processing_times):
    """
    For any hour of operation, the System should calculate and log the average processing time per file.
    
    **Validates: Requirements 15.4**
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        watch_dir = Path(tmpdir)
        config = create_test_config(watch_dir)
        
        orchestrator = ServiceOrchestrator(config)
        
        # Simulate processing times
        orchestrator._processing_times = processing_times.copy()
        
        # Track info logs
        info_logs = []
        original_info = orchestrator.logger.info
        
        def tracked_info(message, **context):
            info_logs.append((message, context))
            return original_info(message, **context)
        
        orchestrator.logger.info = tracked_info
        
        # Perform health check
        health_status = orchestrator.health_check()
        
        # Calculate expected average
        expected_avg = sum(processing_times) / len(processing_times)
        
        # Should have logged average processing time
        avg_logs = [
            (msg, ctx) for msg, ctx in info_logs 
            if "Average processing time" in msg or "avg_time_ms" in ctx
        ]
        
        assert len(avg_logs) > 0, "Expected average processing time to be logged during health check"
        
        # Average should be in details
        assert 'average_processing_time_ms' in health_status.details, \
            "Health status details missing average_processing_time_ms"
        
        actual_avg = health_status.details['average_processing_time_ms']
        assert abs(actual_avg - expected_avg) < 0.1, \
            f"Expected average {expected_avg}ms, got {actual_avg}ms"



# Feature: scanner-watcher2, Property 40: Error rate calculation
@settings(max_examples=10, deadline=None)
@given(
    total_files=st.integers(min_value=1, max_value=100),
    error_count=st.integers(min_value=0, max_value=50)
)
def test_error_rate_calculation(total_files, error_count):
    """
    For any set of processed files, the System should calculate and log the error rate as a percentage.
    
    **Validates: Requirements 15.5**
    """
    # Ensure error count doesn't exceed total
    error_count = min(error_count, total_files)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        watch_dir = Path(tmpdir)
        config = create_test_config(watch_dir)
        
        orchestrator = ServiceOrchestrator(config)
        
        # Simulate processing statistics
        orchestrator._processing_total = total_files
        orchestrator._processing_errors = error_count
        
        # Track info logs
        info_logs = []
        original_info = orchestrator.logger.info
        
        def tracked_info(message, **context):
            info_logs.append((message, context))
            return original_info(message, **context)
        
        orchestrator.logger.info = tracked_info
        
        # Perform health check
        health_status = orchestrator.health_check()
        
        # Calculate expected error rate
        expected_rate = (error_count / total_files) * 100
        
        # Should have logged error rate
        error_rate_logs = [
            (msg, ctx) for msg, ctx in info_logs 
            if "Error rate" in msg or "error_rate_percent" in ctx
        ]
        
        assert len(error_rate_logs) > 0, "Expected error rate to be logged during health check"
        
        # Error rate should be in details
        assert 'error_rate_percent' in health_status.details, \
            "Health status details missing error_rate_percent"
        
        actual_rate = health_status.details['error_rate_percent']
        assert abs(actual_rate - expected_rate) < 0.1, \
            f"Expected error rate {expected_rate}%, got {actual_rate}%"
