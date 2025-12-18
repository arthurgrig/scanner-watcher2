"""
Property-based tests for error handler with retry logic and circuit breaker.
"""

from unittest.mock import Mock

import pytest
from hypothesis import given, settings, strategies as st

from scanner_watcher2.infrastructure.error_handler import (
    CircuitBreakerOpenError,
    CircuitBreakerState,
    ErrorHandler,
)
from scanner_watcher2.models import ErrorType


# Feature: scanner-watcher2, Property 17: Transient error retry
@given(
    max_attempts=st.integers(min_value=1, max_value=5),
    transient_error_msg=st.sampled_from([
        "Connection timeout",
        "Network error",
        "Rate limit exceeded",
        "429 Too Many Requests",
        "Sharing violation",
        "File is being used by another process",
    ]),
)
@settings(max_examples=100, deadline=None)
def test_transient_errors_are_retried(max_attempts: int, transient_error_msg: str) -> None:
    """
    For any transient error, the system should retry the operation with exponential backoff up to max attempts.
    
    Validates: Requirements 6.1, 14.1
    """
    handler = ErrorHandler(max_attempts=max_attempts, initial_delay=0.001, jitter_ms=0)
    
    # Create a mock that fails with transient error
    mock_func = Mock(side_effect=Exception(transient_error_msg))
    
    # Should retry and eventually raise
    with pytest.raises(Exception) as exc_info:
        handler.execute_with_retry(mock_func, operation_name="test_operation")
    
    # Verify it was called max_attempts times
    assert mock_func.call_count == max_attempts
    assert transient_error_msg in str(exc_info.value)


# Feature: scanner-watcher2, Property 17: Transient error retry
@given(
    max_attempts=st.integers(min_value=2, max_value=5),
    success_on_attempt=st.integers(min_value=1, max_value=4),
)
@settings(max_examples=100, deadline=None)
def test_transient_error_succeeds_on_retry(max_attempts: int, success_on_attempt: int) -> None:
    """
    For any transient error that succeeds on retry, the system should return the successful result.
    
    Validates: Requirements 6.1, 14.1
    """
    # Only test cases where success happens before max attempts
    if success_on_attempt > max_attempts:
        success_on_attempt = max_attempts
    
    handler = ErrorHandler(max_attempts=max_attempts, initial_delay=0.001, jitter_ms=0)
    
    call_count = 0
    expected_result = "success"
    
    def func_that_succeeds_eventually():
        nonlocal call_count
        call_count += 1
        if call_count < success_on_attempt:
            raise Exception("Connection timeout")
        return expected_result
    
    # Should succeed after retries
    result = handler.execute_with_retry(func_that_succeeds_eventually, operation_name="test_operation")
    
    assert result == expected_result
    assert call_count == success_on_attempt


# Feature: scanner-watcher2, Property 18: Permanent error handling
@given(
    permanent_error_msg=st.sampled_from([
        "401 Unauthorized",
        "Invalid API key",
        "Corrupted file",
        "Unsupported format",
        "Permission denied",
        "Access denied",
        "403 Forbidden",
    ]),
)
@settings(max_examples=100, deadline=None)
def test_permanent_errors_not_retried(permanent_error_msg: str) -> None:
    """
    For any permanent error, the system should skip the file and log the error without retrying.
    
    Validates: Requirements 6.2
    """
    handler = ErrorHandler(max_attempts=3, initial_delay=0.001, jitter_ms=0)
    
    # Create a mock that fails with permanent error
    mock_func = Mock(side_effect=Exception(permanent_error_msg))
    
    # Should not retry permanent errors
    with pytest.raises(Exception) as exc_info:
        handler.execute_with_retry(mock_func, operation_name="test_operation")
    
    # Verify it was called only once (no retries)
    assert mock_func.call_count == 1
    assert permanent_error_msg in str(exc_info.value)


# Feature: scanner-watcher2, Property 18: Permanent error handling
@given(
    error_msg=st.text(min_size=1),
)
@settings(max_examples=100, deadline=None)
def test_error_classification_consistency(error_msg: str) -> None:
    """
    For any error, the classification should be consistent across multiple calls.
    
    Validates: Requirements 6.2
    """
    handler = ErrorHandler()
    error = Exception(error_msg)
    
    # Classify the same error multiple times
    classification1 = handler.classify_error(error)
    classification2 = handler.classify_error(error)
    classification3 = handler.classify_error(error)
    
    # Should always return the same classification
    assert classification1 == classification2 == classification3
    assert isinstance(classification1, ErrorType)


# Feature: scanner-watcher2, Property 19: Error isolation
@given(
    num_operations=st.integers(min_value=2, max_value=10),
    failing_index=st.integers(min_value=0, max_value=9),
)
@settings(max_examples=100, deadline=None)
def test_error_isolation_between_operations(num_operations: int, failing_index: int) -> None:
    """
    For any file processing error, the system should continue processing other files in the queue.
    
    Validates: Requirements 6.4
    """
    # Adjust failing_index to be within range
    if failing_index >= num_operations:
        failing_index = num_operations - 1
    
    handler = ErrorHandler(max_attempts=1, initial_delay=0.001, jitter_ms=0)
    
    results = []
    
    # Simulate processing multiple operations
    for i in range(num_operations):
        try:
            if i == failing_index:
                # This operation fails
                handler.execute_with_retry(
                    lambda: (_ for _ in ()).throw(Exception("Processing error")),
                    operation_name=f"operation_{i}",
                )
            else:
                # This operation succeeds
                result = handler.execute_with_retry(
                    lambda idx=i: f"success_{idx}",
                    operation_name=f"operation_{i}",
                )
                results.append(result)
        except Exception:
            # Error is isolated, continue with next operation
            results.append(f"error_{i}")
    
    # All operations should have been attempted
    assert len(results) == num_operations
    
    # The failing operation should have error marker
    assert results[failing_index] == f"error_{failing_index}"
    
    # Other operations should have succeeded
    for i in range(num_operations):
        if i != failing_index:
            assert results[i] == f"success_{i}"


# Feature: scanner-watcher2, Property 20: Error context logging
@given(
    error_msg=st.text(min_size=1),
)
@settings(max_examples=100, deadline=None)
def test_error_classification_includes_context(error_msg: str) -> None:
    """
    For any error logged, the classification should provide context about the error type.
    
    Validates: Requirements 6.5
    """
    handler = ErrorHandler()
    error = Exception(error_msg)
    
    # Classify error
    error_type = handler.classify_error(error)
    
    # Error type should be one of the valid types
    assert error_type in [
        ErrorType.TRANSIENT,
        ErrorType.PERMANENT,
        ErrorType.CRITICAL,
        ErrorType.FATAL,
    ]
    
    # Error type should have a string representation for logging
    assert isinstance(error_type.value, str)
    assert len(error_type.value) > 0


# Feature: scanner-watcher2, Property 21: Sharing violation classification
@given(
    sharing_violation_msg=st.sampled_from([
        "Sharing violation",
        "File is being used by another process",
        "Cannot access the file because it is being used",
        "The process cannot access the file",
    ]),
)
@settings(max_examples=100, deadline=None)
def test_sharing_violation_classified_as_transient(sharing_violation_msg: str) -> None:
    """
    For any file operation that fails with a sharing violation, the system should classify it as a transient error.
    
    Validates: Requirements 14.4
    """
    handler = ErrorHandler()
    error = Exception(sharing_violation_msg)
    
    # Classify the sharing violation error
    error_type = handler.classify_error(error)
    
    # Should be classified as transient
    assert error_type == ErrorType.TRANSIENT


# Feature: scanner-watcher2, Property 17: Transient error retry
@given(
    attempt=st.integers(min_value=1, max_value=10),
)
@settings(max_examples=100, deadline=None)
def test_exponential_backoff_increases(attempt: int) -> None:
    """
    For any retry attempt, the backoff delay should increase exponentially.
    
    Validates: Requirements 6.1
    """
    handler = ErrorHandler(
        initial_delay=1.0,
        exponential_base=2.0,
        max_delay=60.0,
        jitter_ms=0,  # No jitter for predictable testing
    )
    
    # Calculate backoff for this attempt
    delay = handler.calculate_backoff(attempt)
    
    # Delay should be at least initial_delay for attempt 1
    if attempt == 1:
        assert delay >= handler.initial_delay
    
    # Delay should not exceed max_delay
    assert delay <= handler.max_delay
    
    # For attempts > 1, delay should be greater than or equal to previous attempt
    if attempt > 1:
        previous_delay = handler.calculate_backoff(attempt - 1)
        # Allow for some floating point imprecision
        assert delay >= previous_delay * 0.99


# Additional circuit breaker tests
@given(
    threshold=st.integers(min_value=2, max_value=10),
)
@settings(max_examples=100, deadline=None)
def test_circuit_breaker_opens_after_threshold(threshold: int) -> None:
    """
    For any circuit breaker, it should open after reaching the failure threshold.
    
    Validates: Requirements 6.3
    """
    handler = ErrorHandler(
        max_attempts=1,
        circuit_breaker_threshold=threshold,
        circuit_breaker_window=60,
        initial_delay=0.001,
        jitter_ms=0,
    )
    
    # Fail threshold times
    for _ in range(threshold):
        try:
            handler.execute_with_retry(
                lambda: (_ for _ in ()).throw(Exception("Connection timeout")),
                operation_name="test_operation",
                use_circuit_breaker=True,
            )
        except Exception:
            pass
    
    # Circuit breaker should now be open
    assert handler.get_circuit_breaker_state() == CircuitBreakerState.OPEN
    
    # Next call should fail immediately with CircuitBreakerOpenError
    with pytest.raises(CircuitBreakerOpenError):
        handler.execute_with_retry(
            lambda: "success",
            operation_name="test_operation",
            use_circuit_breaker=True,
        )


@given(
    threshold=st.integers(min_value=2, max_value=10),
)
@settings(max_examples=100, deadline=None)
def test_circuit_breaker_closes_on_success(threshold: int) -> None:
    """
    For any circuit breaker in half-open state, it should close on successful operation.
    
    Validates: Requirements 6.3
    """
    handler = ErrorHandler(
        max_attempts=1,
        circuit_breaker_threshold=threshold,
        circuit_breaker_timeout=0,  # Immediate transition to half-open
        circuit_breaker_window=60,
        initial_delay=0.001,
        jitter_ms=0,
    )
    
    # Open the circuit breaker
    for _ in range(threshold):
        try:
            handler.execute_with_retry(
                lambda: (_ for _ in ()).throw(Exception("Connection timeout")),
                operation_name="test_operation",
                use_circuit_breaker=True,
            )
        except Exception:
            pass
    
    assert handler.get_circuit_breaker_state() == CircuitBreakerState.OPEN
    
    # Wait for transition to half-open (timeout is 0, so it should transition immediately)
    import time
    time.sleep(0.01)
    
    # Successful operation should close the circuit
    result = handler.execute_with_retry(
        lambda: "success",
        operation_name="test_operation",
        use_circuit_breaker=True,
    )
    
    assert result == "success"
    assert handler.get_circuit_breaker_state() == CircuitBreakerState.CLOSED
