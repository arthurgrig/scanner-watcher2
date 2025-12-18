"""
Scanner-Watcher2: Windows-native legal document processing system.

This package provides automated document monitoring, AI-powered classification,
and intelligent file organization for legal offices.
"""

__version__ = "1.0.0"
__author__ = "Scanner-Watcher2 Team"

from scanner_watcher2.models import (
    Classification,
    ErrorType,
    HealthStatus,
    ProcessingResult,
)

__all__ = [
    "Classification",
    "ErrorType",
    "HealthStatus",
    "ProcessingResult",
    "__version__",
]
