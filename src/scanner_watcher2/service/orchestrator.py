"""
Service orchestrator for coordinating all application components.
"""

import os
import platform
import psutil
import time
from datetime import datetime
from pathlib import Path
from threading import Event, Thread
from typing import Callable

from scanner_watcher2.config import Config
from scanner_watcher2.core.ai_service import AIService
from scanner_watcher2.core.directory_watcher import DirectoryWatcher
from scanner_watcher2.core.file_manager import FileManager
from scanner_watcher2.core.file_processor import FileProcessor
from scanner_watcher2.core.pdf_processor import PDFProcessor
from scanner_watcher2.infrastructure.config_manager import ConfigManager
from scanner_watcher2.infrastructure.error_handler import ErrorHandler
from scanner_watcher2.infrastructure.logger import Logger
from scanner_watcher2.models import HealthStatus, ProcessingResult


class ServiceOrchestrator:
    """Coordinate all application components and manage lifecycle."""

    def __init__(self, config: Config) -> None:
        """
        Initialize with configuration.

        Args:
            config: Application configuration
        """
        self.config = config
        self._stop_event = Event()
        self._health_check_thread: Thread | None = None
        self._consecutive_health_failures = 0
        self._processing_times: list[int] = []
        self._processing_errors: int = 0
        self._processing_total: int = 0
        self._processing_files: set[Path] = set()  # Track files currently being processed
        self._processing_lock = __import__('threading').Lock()
        
        # Initialize infrastructure components
        if platform.system() == "Windows":
            log_dir = Path(os.getenv("APPDATA", ".")) / "ScannerWatcher2" / "logs"
        else:
            # Non-Windows fallback (development/testing)
            log_dir = Path.home() / ".ScannerWatcher2" / "logs"
        self.logger = Logger(
            log_dir=log_dir,
            component="ServiceOrchestrator",
            log_level=config.log_level,
            max_file_size_mb=config.logging.max_file_size_mb,
            backup_count=config.logging.backup_count,
            log_to_event_log=config.logging.log_to_event_log,
        )
        self.error_handler = ErrorHandler()
        self.config_manager = ConfigManager()
        
        # Initialize core components
        self.pdf_processor = PDFProcessor(self.logger, self.error_handler)
        self.ai_service = AIService(
            api_key=config.openai_api_key,
            model=config.ai.model,
            timeout=config.ai.timeout_seconds,
            error_handler=self.error_handler,
            logger=self.logger,
        )
        self.file_manager = FileManager(
            temp_directory=config.processing.temp_directory,
            logger=self.logger,
            error_handler=self.error_handler,
        )
        self.file_processor = FileProcessor(
            pdf_processor=self.pdf_processor,
            ai_service=self.ai_service,
            file_manager=self.file_manager,
            logger=self.logger,
            error_handler=self.error_handler,
        )
        
        # Directory watchers will be initialized in start()
        self.directory_watchers: list[DirectoryWatcher] = []

    def start(self) -> None:
        """Start all components."""
        self.logger.info("Starting ServiceOrchestrator")
        
        # Log all configured watch directories and prefixes
        self.logger.info(
            "Configuration loaded",
            watch_directories=[str(d) for d in self.config.watch_directories],
            file_prefixes=self.config.processing.file_prefixes,
        )
        
        # Check directory existence and create watchers only for existing directories
        valid_directories = []
        for watch_dir in self.config.watch_directories:
            if watch_dir.exists() and watch_dir.is_dir():
                valid_directories.append(watch_dir)
            else:
                self.logger.warning(
                    "Watch directory does not exist, skipping",
                    watch_path=str(watch_dir),
                )
        
        # Ensure at least one valid directory exists
        if not valid_directories:
            error_msg = "No valid watch directories found. At least one accessible directory is required."
            self.logger.critical(error_msg)
            raise RuntimeError(error_msg)
        
        # Create a directory watcher for each valid directory
        for watch_dir in valid_directories:
            watcher = DirectoryWatcher(
                watch_path=watch_dir,
                file_prefixes=self.config.processing.file_prefixes,
                callback=self._process_file_callback,
            )
            watcher.start()
            self.directory_watchers.append(watcher)
            self.logger.info(
                "Directory watcher started",
                watch_path=str(watch_dir),
                prefixes=self.config.processing.file_prefixes,
            )
        
        # Start health check thread
        self._health_check_thread = Thread(target=self._health_check_loop, daemon=True)
        self._health_check_thread.start()
        self.logger.info("Health check thread started")

    def stop(self, timeout: int = 30) -> None:
        """
        Gracefully stop all components.

        Args:
            timeout: Maximum time to wait for shutdown in seconds
        """
        self.logger.info("Stopping ServiceOrchestrator", timeout=timeout)
        start_time = time.time()
        
        # Signal stop
        self._stop_event.set()
        
        # Stop all directory watchers
        for watcher in self.directory_watchers:
            watcher.stop()
        
        self.logger.info("All directory watchers stopped")
        
        # Wait for health check thread to finish
        if self._health_check_thread and self._health_check_thread.is_alive():
            remaining_time = timeout - (time.time() - start_time)
            if remaining_time > 0:
                self._health_check_thread.join(timeout=remaining_time)
        
        elapsed = time.time() - start_time
        self.logger.info("ServiceOrchestrator stopped", elapsed_seconds=elapsed)

    def run(self, stop_event: Event) -> None:
        """
        Main run loop with stop event.

        Args:
            stop_event: Event to signal shutdown
        """
        self.logger.info("ServiceOrchestrator run loop started")
        
        # Wait for stop event
        stop_event.wait()
        
        # Stop with configured timeout
        self.stop(timeout=self.config.service.graceful_shutdown_timeout_seconds)

    def health_check(self) -> HealthStatus:
        """
        Perform system health check.

        Returns:
            Health status
        """
        check_time = datetime.now()
        details: dict = {}
        
        # Check all watch directories accessibility
        all_accessible = True
        directory_status = {}
        
        for watch_dir in self.config.watch_directories:
            try:
                accessible = watch_dir.exists() and watch_dir.is_dir()
                directory_status[str(watch_dir)] = accessible
                if not accessible:
                    all_accessible = False
            except Exception as e:
                directory_status[str(watch_dir)] = False
                details[f"watch_directory_error_{watch_dir}"] = str(e)
                all_accessible = False
        
        details["watch_directories"] = directory_status
        details["all_directories_accessible"] = all_accessible
        
        # For backward compatibility, also set watch_directory_accessible in details
        details["watch_directory_accessible"] = all_accessible
        watch_dir_accessible = all_accessible
        
        # Check configuration validity
        config_valid = False
        try:
            # Validate current config
            self.config.model_validate(self.config.model_dump())
            config_valid = True
            details["config_valid"] = True
        except Exception as e:
            details["config_error"] = str(e)
        
        # Log memory usage
        try:
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
            details["memory_usage_mb"] = round(memory_mb, 2)
            self.logger.info("Memory usage", memory_mb=memory_mb)
        except Exception as e:
            details["memory_error"] = str(e)
        
        # Calculate average processing time
        if self._processing_times:
            avg_time = sum(self._processing_times) / len(self._processing_times)
            details["average_processing_time_ms"] = round(avg_time, 2)
            self.logger.info("Average processing time", avg_time_ms=avg_time)
        
        # Calculate error rate
        if self._processing_total > 0:
            error_rate = (self._processing_errors / self._processing_total) * 100
            details["error_rate_percent"] = round(error_rate, 2)
            self.logger.info("Error rate", error_rate_percent=error_rate)
        
        # Determine overall health
        is_healthy = watch_dir_accessible and config_valid
        
        # Update consecutive failures
        if not is_healthy:
            self._consecutive_health_failures += 1
            self.logger.warning(
                "Health check failed",
                consecutive_failures=self._consecutive_health_failures,
                details=details,
            )
            
            # Log critical error after 3 consecutive failures
            if self._consecutive_health_failures >= 3:
                self.logger.critical(
                    "Health check failed 3 consecutive times",
                    details=details,
                )
        else:
            self._consecutive_health_failures = 0
        
        return HealthStatus(
            is_healthy=is_healthy,
            watch_directory_accessible=watch_dir_accessible,
            config_valid=config_valid,
            last_check_time=check_time,
            consecutive_failures=self._consecutive_health_failures,
            details=details,
        )

    def _health_check_loop(self) -> None:
        """Background thread for periodic health checks."""
        interval = self.config.service.health_check_interval_seconds
        
        while not self._stop_event.is_set():
            # Perform health check
            self.health_check()
            
            # Wait for next interval or stop event
            self._stop_event.wait(timeout=interval)

    def _process_file_callback(self, file_path: Path) -> None:
        """
        Callback for directory watcher to process files.

        Args:
            file_path: Path to file to process
        """
        # Check if file is already being processed
        with self._processing_lock:
            if file_path in self._processing_files:
                self.logger.debug("File already being processed, skipping", file_path=str(file_path))
                return
            self._processing_files.add(file_path)
        
        # Determine source directory and matched prefix
        source_directory = file_path.parent
        matched_prefix = None
        
        # Find which watcher detected this file to get the matched prefix
        for watcher in self.directory_watchers:
            if file_path.parent == watcher.watch_path:
                matched_prefix = watcher.get_matched_prefix(file_path)
                break
        
        # Log file detection with source directory and matched prefix
        self.logger.info(
            "File detected for processing",
            file_path=str(file_path),
            source_directory=str(source_directory),
            matched_prefix=matched_prefix,
        )
        
        try:
            result = self.file_processor.process_file(file_path)
            
            # Track metrics
            self._processing_total += 1
            if result.success:
                self._processing_times.append(result.processing_time_ms)
                # Keep only last 100 processing times for average calculation
                if len(self._processing_times) > 100:
                    self._processing_times = self._processing_times[-100:]
            else:
                self._processing_errors += 1
                
        except Exception as e:
            self._processing_total += 1
            self._processing_errors += 1
            self.logger.error("Error in file processing callback", error=str(e), file_path=str(file_path))
        finally:
            # Remove from processing set
            with self._processing_lock:
                self._processing_files.discard(file_path)
