"""
File manager for handling file system operations.
"""

from __future__ import annotations

import os
import shutil
import tempfile
import time
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from scanner_watcher2.infrastructure.error_handler import ErrorHandler
    from scanner_watcher2.infrastructure.logger import Logger


class FileManager:
    """Handle all file system operations with Windows file locking support."""

    def __init__(
        self,
        error_handler: ErrorHandler,
        logger: Logger,
        temp_directory: Path | None = None,
    ):
        """
        Initialize FileManager.

        Args:
            error_handler: Error handler for retry logic
            logger: Logger for operation tracking
            temp_directory: Optional custom temporary directory
        """
        self.error_handler = error_handler
        self.logger = logger
        self.temp_directory = temp_directory or Path(tempfile.gettempdir())

    def rename_file(self, source: Path, target_name: str) -> Path:
        """
        Rename file with conflict resolution and atomic operations.

        Implements Requirements 3.1, 3.2, 3.3, 3.4.

        Args:
            source: Source file path
            target_name: Target filename (without directory)

        Returns:
            Path to renamed file

        Raises:
            FileNotFoundError: If source file doesn't exist
            PermissionError: If file operations fail after retries
        """
        if not source.exists():
            raise FileNotFoundError(f"Source file not found: {source}")

        target_dir = source.parent
        target_path = target_dir / target_name

        # Handle conflict resolution - append suffix if file exists
        if target_path.exists():
            target_path = self._resolve_conflict(target_dir, target_name)

        # Perform atomic rename with retry for Windows file locking
        def _rename_operation() -> Path:
            # Use os.replace for atomic operation on Windows
            os.replace(str(source), str(target_path))
            return target_path

        try:
            result = self.error_handler.execute_with_retry(
                _rename_operation, operation_name="file_rename"
            )
            self.logger.info(
                "File renamed successfully",
                source=str(source),
                target=str(result),
            )
            return result
        except Exception as e:
            self.logger.error(
                "Failed to rename file",
                source=str(source),
                target=str(target_path),
                error=str(e),
            )
            raise

    def _resolve_conflict(self, directory: Path, filename: str) -> Path:
        """
        Resolve filename conflicts by appending unique suffix.

        Implements Requirement 3.2.

        Args:
            directory: Target directory
            filename: Desired filename

        Returns:
            Path with unique filename
        """
        stem = Path(filename).stem
        suffix = Path(filename).suffix
        counter = 1

        while True:
            new_name = f"{stem}_{counter}{suffix}"
            new_path = directory / new_name
            if not new_path.exists():
                return new_path
            counter += 1

    def create_temp_file(self, suffix: str) -> Path:
        """
        Create temporary file in configured temp directory.

        Implements Requirement 13.5.

        Args:
            suffix: File suffix/extension (e.g., '.pdf', '.png')

        Returns:
            Path to temporary file
        """
        # Ensure temp directory exists
        self.temp_directory.mkdir(parents=True, exist_ok=True)

        # Create temporary file
        fd, temp_path = tempfile.mkstemp(suffix=suffix, dir=str(self.temp_directory))
        os.close(fd)  # Close file descriptor immediately

        temp_file = Path(temp_path)
        self.logger.debug("Created temporary file", path=str(temp_file))
        return temp_file

    def cleanup_temp_files(self, file_paths: list[Path]) -> None:
        """
        Delete temporary files with verification.

        Implements Requirements 13.1, 13.2, 13.4.

        Args:
            file_paths: List of temporary file paths to delete
        """
        for file_path in file_paths:
            try:
                if file_path.exists():
                    file_path.unlink()
                    # Verify deletion was successful
                    if file_path.exists():
                        self.logger.warning(
                            "Temporary file still exists after deletion",
                            path=str(file_path),
                        )
                    else:
                        self.logger.debug(
                            "Temporary file deleted successfully", path=str(file_path)
                        )
            except Exception as e:
                self.logger.error(
                    "Failed to delete temporary file",
                    path=str(file_path),
                    error=str(e),
                )

    def is_file_locked(self, file_path: Path) -> bool:
        """
        Check if file is locked by another process.

        Implements Requirement 14.4.

        Args:
            file_path: Path to file to check

        Returns:
            True if file is locked, False otherwise
        """
        if not file_path.exists():
            return False

        try:
            # Try to open file in exclusive mode
            with open(file_path, "r+b") as f:
                # If we can open it, it's not locked
                return False
        except (PermissionError, OSError):
            # File is locked or inaccessible
            return True

    def verify_file_accessible(self, file_path: Path) -> bool:
        """
        Verify that a file exists and is accessible.

        Implements Requirements 3.5, 14.5.

        Args:
            file_path: Path to file to verify

        Returns:
            True if file is accessible, False otherwise
        """
        if not file_path.exists():
            return False

        try:
            # Try to read file metadata
            file_path.stat()
            # Try to open file for reading
            with open(file_path, "rb") as f:
                # Try to read first byte
                f.read(1)
            return True
        except Exception as e:
            self.logger.warning(
                "File verification failed", path=str(file_path), error=str(e)
            )
            return False

    def cleanup_old_temp_files(self, max_age_hours: int = 24) -> None:
        """
        Clean up old temporary files from previous sessions.

        Implements Requirement 13.3.

        Args:
            max_age_hours: Maximum age of temp files to keep (default: 24 hours)
        """
        if not self.temp_directory.exists():
            return

        current_time = time.time()
        max_age_seconds = max_age_hours * 3600

        try:
            for file_path in self.temp_directory.glob("*"):
                if file_path.is_file():
                    try:
                        file_age = current_time - file_path.stat().st_mtime
                        if file_age > max_age_seconds:
                            file_path.unlink()
                            self.logger.debug(
                                "Cleaned up old temporary file",
                                path=str(file_path),
                                age_hours=file_age / 3600,
                            )
                    except Exception as e:
                        self.logger.warning(
                            "Failed to clean up old temp file",
                            path=str(file_path),
                            error=str(e),
                        )
        except Exception as e:
            self.logger.error(
                "Failed to scan temp directory for cleanup",
                directory=str(self.temp_directory),
                error=str(e),
            )
