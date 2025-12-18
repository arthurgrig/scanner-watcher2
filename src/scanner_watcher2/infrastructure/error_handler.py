"""
Error handler with retry logic, exponential backoff, and circuit breaker pattern.
"""

import random
import time
from collections import deque
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, TypeVar

from scanner_watcher2.models import ErrorType


class CircuitBreakerState(Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Service failing, fail fast
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open."""

    pass


class ErrorHandler:
    """
    Centralized error handling with retry logic and circuit breaker pattern.
    
    Provides:
    - Error classification (transient, permanent, critical, fatal)
    - Exponential backoff with jitter for retries
    - Circuit breaker pattern for external services
    - Retry execution wrapper
    """

    def __init__(
        self,
        max_attempts: int = 3,
        initial_delay: float = 1.0,
        exponential_base: float = 2.0,
        max_delay: float = 60.0,
        jitter_ms: int = 500,
        circuit_breaker_threshold: int = 5,
        circuit_breaker_timeout: int = 300,  # 5 minutes
        circuit_breaker_window: int = 60,  # 60 seconds
    ) -> None:
        """
        Initialize error handler with retry and circuit breaker configuration.

        Args:
            max_attempts: Maximum retry attempts for transient errors
            initial_delay: Initial delay in seconds for exponential backoff
            exponential_base: Base for exponential backoff calculation
            max_delay: Maximum delay in seconds between retries
            jitter_ms: Maximum random jitter in milliseconds to add to delays
            circuit_breaker_threshold: Number of failures to open circuit breaker
            circuit_breaker_timeout: Seconds to wait before testing service recovery
            circuit_breaker_window: Time window in seconds for counting failures
        """
        self.max_attempts = max_attempts
        self.initial_delay = initial_delay
        self.exponential_base = exponential_base
        self.max_delay = max_delay
        self.jitter_ms = jitter_ms

        # Circuit breaker configuration
        self.circuit_breaker_threshold = circuit_breaker_threshold
        self.circuit_breaker_timeout = circuit_breaker_timeout
        self.circuit_breaker_window = circuit_breaker_window

        # Circuit breaker state
        self._circuit_state = CircuitBreakerState.CLOSED
        self._circuit_opened_at: datetime | None = None
        self._failure_times: deque[datetime] = deque()

    def classify_error(self, error: Exception) -> ErrorType:
        """
        Classify error as transient, permanent, critical, or fatal.

        Args:
            error: Exception to classify

        Returns:
            ErrorType classification
        """
        error_str = str(error).lower()
        error_type_name = type(error).__name__.lower()

        # Transient errors - can be retried
        transient_indicators = [
            "timeout",
            "timed out",
            "connection",
            "network",
            "rate limit",
            "429",
            "503",
            "sharing violation",
            "file is being used",
            "cannot access",
            "temporarily unavailable",
        ]

        for indicator in transient_indicators:
            if indicator in error_str or indicator in error_type_name:
                return ErrorType.TRANSIENT

        # Fatal errors - stop service
        fatal_indicators = [
            "out of memory",
            "memory error",
            "cannot write log",
            "permission denied on log",
        ]

        for indicator in fatal_indicators:
            if indicator in error_str:
                return ErrorType.FATAL

        # Critical errors - alert but continue
        critical_indicators = [
            "directory not found",
            "disk full",
            "no space left",
            "api down",
            "service unavailable",
        ]

        for indicator in critical_indicators:
            if indicator in error_str:
                return ErrorType.CRITICAL

        # Permanent errors - skip and log
        permanent_indicators = [
            "401",
            "403",
            "invalid api key",
            "unauthorized",
            "forbidden",
            "corrupted",
            "invalid format",
            "unsupported",
            "permission denied",
            "access denied",
        ]

        for indicator in permanent_indicators:
            if indicator in error_str or indicator in error_type_name:
                return ErrorType.PERMANENT

        # Default to permanent if we can't classify
        return ErrorType.PERMANENT

    def should_retry(self, error: Exception, attempt: int) -> bool:
        """
        Determine if operation should be retried based on error type and attempt count.

        Args:
            error: Exception that occurred
            attempt: Current attempt number (1-indexed)

        Returns:
            True if should retry, False otherwise
        """
        if attempt >= self.max_attempts:
            return False

        error_type = self.classify_error(error)
        return error_type == ErrorType.TRANSIENT

    def calculate_backoff(self, attempt: int) -> float:
        """
        Calculate exponential backoff delay with jitter.

        Args:
            attempt: Current attempt number (1-indexed)

        Returns:
            Delay in seconds
        """
        # Calculate exponential delay: initial_delay * (base ^ attempt)
        delay = self.initial_delay * (self.exponential_base ** (attempt - 1))

        # Cap at max_delay
        delay = min(delay, self.max_delay)

        # Add random jitter (0 to jitter_ms milliseconds)
        jitter = random.uniform(0, self.jitter_ms / 1000.0)
        delay += jitter

        return delay

    def _record_failure(self) -> None:
        """Record a failure for circuit breaker tracking."""
        now = datetime.now()
        self._failure_times.append(now)

        # Remove failures outside the time window
        cutoff = now - timedelta(seconds=self.circuit_breaker_window)
        while self._failure_times and self._failure_times[0] < cutoff:
            self._failure_times.popleft()

    def _get_failure_count(self) -> int:
        """Get number of failures within the time window."""
        now = datetime.now()
        cutoff = now - timedelta(seconds=self.circuit_breaker_window)

        # Remove old failures
        while self._failure_times and self._failure_times[0] < cutoff:
            self._failure_times.popleft()

        return len(self._failure_times)

    def _check_circuit_breaker(self) -> None:
        """
        Check circuit breaker state and update if necessary.

        Raises:
            CircuitBreakerOpenError: If circuit breaker is open
        """
        if self._circuit_state == CircuitBreakerState.OPEN:
            # Check if timeout has elapsed
            if self._circuit_opened_at:
                elapsed = (datetime.now() - self._circuit_opened_at).total_seconds()
                if elapsed >= self.circuit_breaker_timeout:
                    # Move to half-open state to test recovery
                    self._circuit_state = CircuitBreakerState.HALF_OPEN
                    return

            # Circuit is still open
            raise CircuitBreakerOpenError("Circuit breaker is open")

    def _update_circuit_breaker(self, success: bool) -> None:
        """
        Update circuit breaker state based on operation result.

        Args:
            success: Whether the operation succeeded
        """
        if success:
            if self._circuit_state == CircuitBreakerState.HALF_OPEN:
                # Success in half-open state, close the circuit
                self._circuit_state = CircuitBreakerState.CLOSED
                self._failure_times.clear()
                self._circuit_opened_at = None
        else:
            self._record_failure()

            if self._circuit_state == CircuitBreakerState.HALF_OPEN:
                # Failure in half-open state, reopen the circuit
                self._circuit_state = CircuitBreakerState.OPEN
                self._circuit_opened_at = datetime.now()
            elif self._circuit_state == CircuitBreakerState.CLOSED:
                # Check if we should open the circuit
                if self._get_failure_count() >= self.circuit_breaker_threshold:
                    self._circuit_state = CircuitBreakerState.OPEN
                    self._circuit_opened_at = datetime.now()

    T = TypeVar("T")

    def execute_with_retry(
        self,
        func: Callable[[], T],
        operation_name: str = "operation",
        use_circuit_breaker: bool = False,
    ) -> T:
        """
        Execute function with retry logic for transient errors.

        Args:
            func: Function to execute
            operation_name: Name of operation for logging
            use_circuit_breaker: Whether to use circuit breaker pattern

        Returns:
            Result of function execution

        Raises:
            Exception: Last exception if all retries fail
            CircuitBreakerOpenError: If circuit breaker is open
        """
        last_exception: Exception | None = None

        for attempt in range(1, self.max_attempts + 1):
            try:
                # Check circuit breaker if enabled
                if use_circuit_breaker:
                    self._check_circuit_breaker()

                # Execute the function
                result = func()

                # Update circuit breaker on success
                if use_circuit_breaker:
                    self._update_circuit_breaker(success=True)

                return result

            except CircuitBreakerOpenError:
                # Don't retry if circuit breaker is open
                raise

            except Exception as e:
                last_exception = e

                # Update circuit breaker on failure
                if use_circuit_breaker:
                    self._update_circuit_breaker(success=False)

                # Check if we should retry
                if not self.should_retry(e, attempt):
                    raise

                # Don't sleep after the last attempt
                if attempt < self.max_attempts:
                    delay = self.calculate_backoff(attempt)
                    time.sleep(delay)

        # All retries exhausted
        if last_exception:
            raise last_exception
        else:
            raise RuntimeError(f"{operation_name} failed after {self.max_attempts} attempts")

    def get_circuit_breaker_state(self) -> CircuitBreakerState:
        """
        Get current circuit breaker state.

        Returns:
            Current circuit breaker state
        """
        return self._circuit_state

    def reset_circuit_breaker(self) -> None:
        """Reset circuit breaker to closed state."""
        self._circuit_state = CircuitBreakerState.CLOSED
        self._circuit_opened_at = None
        self._failure_times.clear()
