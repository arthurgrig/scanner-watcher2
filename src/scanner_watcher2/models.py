"""
Data models and core types for Scanner-Watcher2.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any


class ErrorType(Enum):
    """Classification of error types for handling strategy."""

    TRANSIENT = "transient"
    PERMANENT = "permanent"
    CRITICAL = "critical"
    FATAL = "fatal"


class DocumentType(Enum):
    """
    Standard document type categories for classification.
    
    Provides high-level categories for common legal documents with fallback
    to flexible classification for documents outside predefined categories.
    """

    MEDICAL_REPORT = "Medical Report"
    INJURY_REPORT = "Injury Report"
    CLAIM_FORM = "Claim Form"
    DEPOSITION = "Deposition"
    EXPERT_WITNESS_REPORT = "Expert Witness Report"
    SETTLEMENT_AGREEMENT = "Settlement Agreement"
    COURT_ORDER = "Court Order"
    INSURANCE_CORRESPONDENCE = "Insurance Correspondence"
    WAGE_STATEMENT = "Wage Statement"
    VOCATIONAL_REPORT = "Vocational Report"
    IME_REPORT = "IME Report"
    SURVEILLANCE_REPORT = "Surveillance Report"
    SUBPOENA = "Subpoena"
    MOTION = "Motion"
    BRIEF = "Brief"
    OTHER = "Other"


@dataclass
class ProcessingResult:
    """Result of processing a single document."""

    success: bool
    file_path: Path
    document_type: str | None
    new_file_path: Path | None
    processing_time_ms: int
    error: str | None
    correlation_id: str


@dataclass
class Classification:
    """
    AI classification result for a document.
    
    Supports three-tier classification:
    1. Standard enum categories (e.g., "Medical Report")
    2. Specific document types (e.g., "Panel List")
    3. OTHER fallback (e.g., "OTHER_Unidentified Medical Form")
    """

    document_type: str  # Can be enum value, specific type, or OTHER_description
    confidence: float
    identifiers: dict[str, str]  # e.g., {"patient_name": "John Doe"}
    raw_response: dict

    @property
    def is_standard_category(self) -> bool:
        """
        Check if document_type matches a standard enum category.
        
        Returns:
            True if document_type is one of the DocumentType enum values
        """
        return any(self.document_type == dt.value for dt in DocumentType)

    @property
    def is_other(self) -> bool:
        """
        Check if document_type is OTHER category.
        
        Returns:
            True if document_type starts with "OTHER_"
        """
        return self.document_type.startswith("OTHER_")


@dataclass
class HealthStatus:
    """System health check status."""

    is_healthy: bool
    watch_directory_accessible: bool
    config_valid: bool
    last_check_time: datetime
    consecutive_failures: int
    details: dict[str, Any]
