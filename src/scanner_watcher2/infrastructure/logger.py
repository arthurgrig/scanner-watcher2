"""
Logging system with structured JSON logging and Windows Event Log integration.
"""

import json
import logging
import logging.handlers
import platform
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import structlog


class Logger:
    """Provide comprehensive structured logging with JSON format and Windows Event Log integration."""

    def __init__(
        self,
        log_dir: Path,
        component: str,
        log_level: str = "INFO",
        max_file_size_mb: int = 10,
        backup_count: int = 5,
        log_to_event_log: bool = True,
    ) -> None:
        """
        Initialize logger with structured JSON logging and rotation.

        Args:
            log_dir: Directory for log files
            component: Component name for log context
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            max_file_size_mb: Maximum log file size in MB before rotation
            backup_count: Number of backup log files to keep
            log_to_event_log: Whether to log critical events to Windows Event Log
        """
        self.component = component
        self.log_to_event_log = log_to_event_log
        self._correlation_id: str | None = None

        # Create log directory if it doesn't exist
        log_dir.mkdir(parents=True, exist_ok=True)

        # Set up standard Python logger with rotation
        log_file = log_dir / "scanner_watcher2.log"
        max_bytes = max_file_size_mb * 1024 * 1024

        # Create rotating file handler
        file_handler = logging.handlers.RotatingFileHandler(
            filename=str(log_file),
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8",
        )

        # Configure structlog for JSON output
        structlog.configure(
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.TimeStamper(fmt="iso", utc=True),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.UnicodeDecoder(),
                structlog.processors.JSONRenderer(),
            ],
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            cache_logger_on_first_use=True,
        )

        # Set up Python logging
        self._python_logger = logging.getLogger(f"scanner_watcher2.{component}")
        self._python_logger.setLevel(getattr(logging, log_level.upper()))
        self._python_logger.addHandler(file_handler)
        self._python_logger.propagate = False

        # Get structlog logger
        self._logger = structlog.get_logger(f"scanner_watcher2.{component}")

        # Set up Windows Event Log if enabled and on Windows
        self._event_log_available = False
        if log_to_event_log and platform.system() == "Windows":
            try:
                import win32evtlog
                import win32evtlogutil

                self._win32evtlog = win32evtlog
                self._win32evtlogutil = win32evtlogutil
                self._event_log_available = True
            except ImportError:
                # Windows Event Log not available (e.g., in tests or non-Windows)
                pass

    def generate_correlation_id(self) -> str:
        """
        Generate a new correlation ID for request tracking.

        Returns:
            New correlation ID
        """
        self._correlation_id = str(uuid.uuid4())
        return self._correlation_id

    def set_correlation_id(self, correlation_id: str) -> None:
        """
        Set the correlation ID for subsequent log entries.

        Args:
            correlation_id: Correlation ID to use
        """
        self._correlation_id = correlation_id

    def get_correlation_id(self) -> str | None:
        """
        Get the current correlation ID.

        Returns:
            Current correlation ID or None
        """
        return self._correlation_id

    def _build_context(self, **context: Any) -> dict[str, Any]:
        """
        Build log context with component and correlation ID.

        Args:
            **context: Additional context fields

        Returns:
            Complete context dictionary
        """
        log_context = {
            "component": self.component,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        if self._correlation_id:
            log_context["correlation_id"] = self._correlation_id

        log_context.update(context)
        return log_context

    def _write_to_event_log(self, message: str, level: str, context: dict[str, Any]) -> None:
        """
        Write log entry to Windows Event Log.

        Args:
            message: Log message
            level: Log level
            context: Log context
        """
        if not self._event_log_available:
            return

        try:
            # Format message with context
            full_message = f"{message}\n\nContext: {json.dumps(context, indent=2)}"

            # Map log level to Windows event type
            event_type = self._win32evtlog.EVENTLOG_INFORMATION_TYPE
            if level in ("ERROR", "CRITICAL"):
                event_type = self._win32evtlog.EVENTLOG_ERROR_TYPE
            elif level == "WARNING":
                event_type = self._win32evtlog.EVENTLOG_WARNING_TYPE

            # Write to event log
            self._win32evtlogutil.ReportEvent(
                "ScannerWatcher2",
                1,  # Event ID
                eventType=event_type,
                strings=[full_message],
            )
        except Exception:
            # Silently fail if event log writing fails
            pass

    def debug(self, message: str, **context: Any) -> None:
        """
        Log debug message with context.

        Args:
            message: Log message
            **context: Additional context fields
        """
        log_context = self._build_context(**context)
        self._logger.debug(message, **log_context)

    def info(self, message: str, **context: Any) -> None:
        """
        Log info message with context.

        Args:
            message: Log message
            **context: Additional context fields
        """
        log_context = self._build_context(**context)
        self._logger.info(message, **log_context)

    def warning(self, message: str, **context: Any) -> None:
        """
        Log warning message with context.

        Args:
            message: Log message
            **context: Additional context fields
        """
        log_context = self._build_context(**context)
        self._logger.warning(message, **log_context)

    def error(self, message: str, **context: Any) -> None:
        """
        Log error message with context.

        Args:
            message: Log message
            **context: Additional context fields
        """
        log_context = self._build_context(**context)
        self._logger.error(message, **log_context)

    def critical(self, message: str, **context: Any) -> None:
        """
        Log critical message and write to Windows Event Log.

        Args:
            message: Log message
            **context: Additional context fields
        """
        log_context = self._build_context(**context)
        self._logger.critical(message, **log_context)

        # Write critical events to Windows Event Log
        self._write_to_event_log(message, "CRITICAL", log_context)
