"""
Service layer for Windows service integration.
"""

from scanner_watcher2.service.orchestrator import ServiceOrchestrator
from scanner_watcher2.service.windows_service import ScannerWatcher2Service

__all__ = [
    "ScannerWatcher2Service",
    "ServiceOrchestrator",
]
