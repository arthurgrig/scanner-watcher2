"""
Service orchestrator for coordinating all application components.
"""

import os
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
        
        # Initialize infrastructure components
        self.logger = Logger(
            log_dir=Path(os.getenv("APPDATA", ".")) / "ScannerWatcher2" / "logs",
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
        
        # Directory watcher will be initialized in start()
        self.directory_watcher: DirectoryWatcher | None = None

    def start(self) -> None:
        """Start all components."""
        self.logger.info("Starting ServiceOrchestrator")
        
        # Initialize directory watcher with callback
        self.directory_watcher = DirectoryWatcher(
            watch_path=self.config.watch_directory,
            file_prefix=self.config.processing.file_prefix,
            callback=self._process_file_callback,
        )
        
        # Start directory watcher
        self.directory_watcher.start()
        self.logger.info("Directory watcher started", watch_path=str(self.config.watch_directory))
        
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
        
        # Stop directory watcher
        if self.directory_watcher:
            self.directory_watcher.stop()
            self.logger.info("Directory watcher stopped")
        
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
        
        # Check watch directory accessibility
        watch_dir_accessible = False
        try:
            watch_dir_accessible = self.config.watch_directory.exists() and self.config.watch_directory.is_dir()
            details["watch_directory"] = str(self.config.watch_directory)
            details["watch_directory_accessible"] = watch_dir_accessible
        except Exception as e:
            details["watch_directory_error"] = str(e)
        
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
