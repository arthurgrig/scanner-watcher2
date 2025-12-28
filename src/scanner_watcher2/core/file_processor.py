"""
File processor workflow coordinator for complete document processing pipeline.
"""

from __future__ import annotations

import time
import uuid
from pathlib import Path

from scanner_watcher2.core.ai_service import AIService
from scanner_watcher2.core.file_manager import FileManager
from scanner_watcher2.core.pdf_processor import PDFProcessor
from scanner_watcher2.infrastructure.error_handler import ErrorHandler
from scanner_watcher2.infrastructure.logger import Logger
from scanner_watcher2.models import ProcessingResult


class FileProcessor:
    """
    Coordinate the complete document processing workflow.
    
    Provides:
    - File validation
    - PDF extraction coordination
    - AI classification coordination
    - File renaming coordination
    - Error handling with proper classification
    - Processing metrics tracking
    - Sequential processing to avoid parallel API calls
    """

    def __init__(
        self,
        pdf_processor: PDFProcessor,
        ai_service: AIService,
        file_manager: FileManager,
        error_handler: ErrorHandler,
        logger: Logger,
    ) -> None:
        """
        Initialize file processor with dependencies.

        Args:
            pdf_processor: PDF processor for page extraction
            ai_service: AI service for document classification
            file_manager: File manager for file operations
            error_handler: Error handler for retry logic
            logger: Logger for operation tracking
        """
        self.pdf_processor = pdf_processor
        self.ai_service = ai_service
        self.file_manager = file_manager
        self.error_handler = error_handler
        self.logger = logger

    def validate_file(self, file_path: Path) -> bool:
        """
        Validate file type and accessibility.

        Implements Requirements 2.1, 6.4.

        Args:
            file_path: Path to file to validate

        Returns:
            True if file is valid and accessible, False otherwise
        """
        # Check if file exists
        if not file_path.exists():
            self.logger.warning("File does not exist", file_path=str(file_path))
            return False

        # Check if it's a file (not a directory)
        if not file_path.is_file():
            self.logger.warning("Path is not a file", file_path=str(file_path))
            return False

        # Check if it's a PDF
        if file_path.suffix.lower() != ".pdf":
            self.logger.warning(
                "File is not a PDF",
                file_path=str(file_path),
                suffix=file_path.suffix,
            )
            return False

        # Check if file is accessible
        if not self.file_manager.verify_file_accessible(file_path):
            self.logger.warning("File is not accessible", file_path=str(file_path))
            return False

        return True

    def process_file(self, file_path: Path) -> ProcessingResult:
        """
        Process a single file through complete workflow.

        Implements Requirements 2.1, 2.2, 2.3, 3.1, 6.4, 12.2, 15.1.

        Workflow:
        1. Validate file
        2. Extract first page from PDF
        3. Optimize image for API transmission
        4. Classify document using AI
        5. Rename file based on classification
        6. Clean up temporary files
        7. Track processing metrics

        Args:
            file_path: Path to file to process

        Returns:
            ProcessingResult with success status and details
        """
        # Generate correlation ID for tracking
        correlation_id = str(uuid.uuid4())
        start_time = time.time()

        self.logger.info(
            "Starting file processing",
            file_path=str(file_path),
            correlation_id=correlation_id,
        )

        temp_files: list[Path] = []
        document_type: str | None = None
        new_file_path: Path | None = None
        error_message: str | None = None

        try:
            # Step 1: Validate file
            if not self.validate_file(file_path):
                error_message = "File validation failed"
                self.logger.error(
                    error_message,
                    file_path=str(file_path),
                    correlation_id=correlation_id,
                )
                return ProcessingResult(
                    success=False,
                    file_path=file_path,
                    document_type=None,
                    new_file_path=None,
                    processing_time_ms=int((time.time() - start_time) * 1000),
                    error=error_message,
                    correlation_id=correlation_id,
                )

            # Get file size for metrics
            file_size_bytes = file_path.stat().st_size

            # Step 2: Extract first pages from PDF (default: 3 pages)
            self.logger.debug(
                "Extracting pages from PDF",
                file_path=str(file_path),
                correlation_id=correlation_id,
            )

            try:
                # Extract multiple pages (default 3, or fewer if PDF has less)
                page_images = self.pdf_processor.extract_first_pages(file_path, num_pages=3)
                
                self.logger.debug(
                    "Pages extracted successfully",
                    num_pages=len(page_images),
                    correlation_id=correlation_id,
                )
            except Exception as e:
                error_type = self.error_handler.classify_error(e)
                error_message = f"PDF extraction failed: {str(e)}"
                
                self.logger.error(
                    error_message,
                    file_path=str(file_path),
                    error_type=error_type.value,
                    correlation_id=correlation_id,
                )
                
                # Rename file with ERROR prefix
                new_file_path = self._rename_with_error_prefix(file_path, "ERROR")
                
                return ProcessingResult(
                    success=False,
                    file_path=file_path,
                    document_type=None,
                    new_file_path=new_file_path,
                    processing_time_ms=int((time.time() - start_time) * 1000),
                    error=error_message,
                    correlation_id=correlation_id,
                )

            # Step 3: Optimize images for API transmission
            self.logger.debug(
                "Optimizing images for API transmission",
                num_images=len(page_images),
                correlation_id=correlation_id,
            )

            try:
                optimized_images = [
                    self.pdf_processor.optimize_image(img) for img in page_images
                ]
            except Exception as e:
                error_message = f"Image optimization failed: {str(e)}"
                
                self.logger.error(
                    error_message,
                    file_path=str(file_path),
                    correlation_id=correlation_id,
                )
                
                # Rename file with ERROR prefix
                new_file_path = self._rename_with_error_prefix(file_path, "ERROR")
                
                return ProcessingResult(
                    success=False,
                    file_path=file_path,
                    document_type=None,
                    new_file_path=new_file_path,
                    processing_time_ms=int((time.time() - start_time) * 1000),
                    error=error_message,
                    correlation_id=correlation_id,
                )

            # Step 4: Classify document using AI with all pages
            self.logger.debug(
                "Classifying document with AI",
                num_images=len(optimized_images),
                correlation_id=correlation_id,
            )

            try:
                classification = self.ai_service.classify_document(optimized_images)
                document_type = classification.document_type
                
                self.logger.info(
                    "Document classified successfully",
                    document_type=document_type,
                    confidence=classification.confidence,
                    correlation_id=correlation_id,
                )
            except Exception as e:
                error_type = self.error_handler.classify_error(e)
                error_message = f"AI classification failed: {str(e)}"
                
                self.logger.error(
                    error_message,
                    file_path=str(file_path),
                    error_type=error_type.value,
                    correlation_id=correlation_id,
                )
                
                # Rename file with UNKNOWN prefix (AI couldn't categorize)
                new_file_path = self._rename_with_error_prefix(file_path, "UNKNOWN")
                
                return ProcessingResult(
                    success=False,
                    file_path=file_path,
                    document_type=None,
                    new_file_path=new_file_path,
                    processing_time_ms=int((time.time() - start_time) * 1000),
                    error=error_message,
                    correlation_id=correlation_id,
                )

            # Step 5: Rename file based on classification
            self.logger.debug(
                "Renaming file based on classification",
                document_type=document_type,
                correlation_id=correlation_id,
            )

            try:
                # Build new filename with structured ordering
                from datetime import datetime
                
                date_str = datetime.now().strftime("%Y%m%d")
                
                # Sanitize document type for filename
                safe_doc_type = "".join(
                    c if c.isalnum() or c in ("-", "_") else "_"
                    for c in document_type
                )
                
                # Define predictable ordering for identifiers
                # Format: YYYYMMDD_PlaintiffName_DocumentType_RemainingIdentifiers.pdf
                ordered_keys = [
                    "plaintiff_name",    # Plaintiff (lawyer's client) - HIGHEST PRIORITY
                    "plaintiff",         # Alternative key for plaintiff
                    "patient_name",      # Injured worker (same as plaintiff)
                    "client_name",       # Employer/company name (defendant)
                    "case_number",
                    "date_of_injury",
                    "report_date",
                    "evaluator_name",
                ]
                
                def sanitize_value(value: str) -> str:
                    """Sanitize identifier value for filename."""
                    return "".join(
                        c if c.isalnum() or c in ("-", "_") else "_"
                        for c in str(value)
                    )
                
                # Extract identifiers in predictable order
                identifier_parts = []
                processed_keys = set()
                
                # Add identifiers in defined order
                for key in ordered_keys:
                    if key in classification.identifiers:
                        value = classification.identifiers[key]
                        if value:  # Only add non-empty values
                            identifier_parts.append(sanitize_value(value))
                            processed_keys.add(key)
                
                # Add any remaining identifiers not in ordered list
                for key, value in classification.identifiers.items():
                    if key not in processed_keys and value:
                        identifier_parts.append(sanitize_value(value))
                
                # Build filename: YYYYMMDD_PlaintiffName_DocumentType_OtherIdentifiers.pdf
                # Plaintiff name is first identifier (if present), then document type, then rest
                filename_parts = [date_str]
                
                if identifier_parts:
                    # First identifier should be plaintiff_name (lawyer's client)
                    filename_parts.append(identifier_parts[0])
                    filename_parts.append(safe_doc_type)
                    filename_parts.extend(identifier_parts[1:])
                else:
                    # No identifiers, just date and document type
                    filename_parts.append(safe_doc_type)
                
                new_filename = "_".join(filename_parts) + ".pdf"
                
                new_file_path = self.file_manager.rename_file(file_path, new_filename)
                
                self.logger.info(
                    "File renamed successfully",
                    old_path=str(file_path),
                    new_path=str(new_file_path),
                    correlation_id=correlation_id,
                )
            except Exception as e:
                error_type = self.error_handler.classify_error(e)
                error_message = f"File rename failed: {str(e)}"
                
                self.logger.error(
                    error_message,
                    file_path=str(file_path),
                    error_type=error_type.value,
                    correlation_id=correlation_id,
                )
                
                return ProcessingResult(
                    success=False,
                    file_path=file_path,
                    document_type=document_type,
                    new_file_path=None,
                    processing_time_ms=int((time.time() - start_time) * 1000),
                    error=error_message,
                    correlation_id=correlation_id,
                )

            # Step 6: Verify renamed file is accessible before cleanup
            if new_file_path and not self.file_manager.verify_file_accessible(new_file_path):
                error_message = "Renamed file verification failed"
                
                self.logger.error(
                    error_message,
                    new_path=str(new_file_path),
                    correlation_id=correlation_id,
                )
                
                return ProcessingResult(
                    success=False,
                    file_path=file_path,
                    document_type=document_type,
                    new_file_path=new_file_path,
                    processing_time_ms=int((time.time() - start_time) * 1000),
                    error=error_message,
                    correlation_id=correlation_id,
                )

            # Step 7: Clean up temporary files
            if temp_files:
                self.logger.debug(
                    "Cleaning up temporary files",
                    temp_file_count=len(temp_files),
                    correlation_id=correlation_id,
                )
                self.file_manager.cleanup_temp_files(temp_files)

            # Calculate processing metrics
            processing_time_ms = int((time.time() - start_time) * 1000)

            # Log success with metrics (Requirement 7.4, 15.1)
            self.logger.info(
                "File processed successfully",
                file_path=str(file_path),
                new_path=str(new_file_path),
                document_type=document_type,
                processing_time_ms=processing_time_ms,
                file_size_bytes=file_size_bytes,
                correlation_id=correlation_id,
            )

            return ProcessingResult(
                success=True,
                file_path=file_path,
                document_type=document_type,
                new_file_path=new_file_path,
                processing_time_ms=processing_time_ms,
                error=None,
                correlation_id=correlation_id,
            )

        except Exception as e:
            # Catch-all for unexpected errors
            error_type = self.error_handler.classify_error(e)
            error_message = f"Unexpected error during processing: {str(e)}"
            
            self.logger.error(
                error_message,
                file_path=str(file_path),
                error_type=error_type.value,
                correlation_id=correlation_id,
            )

            # Clean up temporary files even on error
            if temp_files:
                self.file_manager.cleanup_temp_files(temp_files)

            return ProcessingResult(
                success=False,
                file_path=file_path,
                document_type=document_type,
                new_file_path=new_file_path,
                processing_time_ms=int((time.time() - start_time) * 1000),
                error=error_message,
                correlation_id=correlation_id,
            )

    def _rename_with_error_prefix(self, file_path: Path, prefix: str) -> Path:
        """
        Rename file with ERROR or UNKNOWN prefix when processing fails.

        Args:
            file_path: Original file path
            prefix: Prefix to add (ERROR or UNKNOWN)

        Returns:
            New file path after renaming
        """
        from datetime import datetime
        
        date_str = datetime.now().strftime("%Y%m%d")
        original_name = file_path.stem  # Filename without extension
        
        # Build new filename: YYYYMMDD_PREFIX_OriginalName.pdf
        new_filename = f"{date_str}_{prefix}_{original_name}.pdf"
        
        try:
            new_file_path = self.file_manager.rename_file(file_path, new_filename)
            self.logger.info(
                f"File renamed with {prefix} prefix",
                original_path=str(file_path),
                new_path=str(new_file_path),
            )
            return new_file_path
        except Exception as e:
            self.logger.error(
                f"Failed to rename file with {prefix} prefix",
                file_path=str(file_path),
                error=str(e),
            )
            return file_path  # Return original path if rename fails
