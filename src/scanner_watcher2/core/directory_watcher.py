"""
Directory watcher for monitoring filesystem changes.
"""

from __future__ import annotations

import threading
import time
from collections.abc import Callable
from pathlib import Path

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer


class DirectoryWatcher:
    """Monitor filesystem for new scan files."""

    def __init__(
        self, watch_path: Path, file_prefix: str, callback: Callable[[Path], None]
    ) -> None:
        """
        Initialize watcher with path and callback.

        Args:
            watch_path: Directory to monitor
            file_prefix: File prefix to detect (e.g., "SCAN-")
            callback: Function to call when file is detected
        """
        self.watch_path = watch_path
        self.file_prefix = file_prefix
        self.callback = callback
        self._observer: Observer | None = None
        self._event_handler: _ScanFileEventHandler | None = None
        self._pending_files: dict[Path, float] = {}  # file_path -> last_modified_time
        self._pending_lock = threading.Lock()
        self._stability_check_interval = 0.5  # Check every 500ms
        self._stability_duration = 2.0  # File must be stable for 2 seconds
        self._stop_event = threading.Event()
        self._stability_thread: threading.Thread | None = None

    def start(self) -> None:
        """Start watching directory."""
        if self._observer is not None:
            raise RuntimeError("DirectoryWatcher is already running")

        # Create event handler
        self._event_handler = _ScanFileEventHandler(
            file_prefix=self.file_prefix,
            on_file_detected=self._on_file_detected,
        )

        # Create and start observer
        self._observer = Observer()
        self._observer.schedule(
            self._event_handler, str(self.watch_path), recursive=False
        )
        self._observer.start()

        # Start stability checking thread
        self._stop_event.clear()
        self._stability_thread = threading.Thread(
            target=self._stability_check_loop, daemon=True
        )
        self._stability_thread.start()

    def stop(self) -> None:
        """Stop watching directory."""
        if self._observer is None:
            return

        # Signal stop to stability thread
        self._stop_event.set()

        # Stop observer
        self._observer.stop()
        self._observer.join(timeout=5.0)
        self._observer = None

        # Wait for stability thread to finish
        if self._stability_thread is not None:
            self._stability_thread.join(timeout=2.0)
            self._stability_thread = None

        # Clear pending files
        with self._pending_lock:
            self._pending_files.clear()

    def is_file_stable(self, file_path: Path) -> bool:
        """
        Check if file is done being written.

        Args:
            file_path: Path to file to check

        Returns:
            True if file is stable (size unchanged for 2 seconds)
        """
        if not file_path.exists():
            return False

        try:
            # Get current file size
            current_size = file_path.stat().st_size
            current_mtime = file_path.stat().st_mtime

            # Wait for stability duration
            time.sleep(self._stability_duration)

            # Check if file still exists and size hasn't changed
            if not file_path.exists():
                return False

            new_size = file_path.stat().st_size
            new_mtime = file_path.stat().st_mtime

            # File is stable if size and mtime haven't changed
            return current_size == new_size and current_mtime == new_mtime

        except (OSError, PermissionError):
            return False

    def _on_file_detected(self, file_path: Path) -> None:
        """
        Handle file detection event.

        Args:
            file_path: Path to detected file
        """
        # Add to pending files for stability checking
        with self._pending_lock:
            self._pending_files[file_path] = time.time()

    def _stability_check_loop(self) -> None:
        """Background thread that checks file stability and triggers callbacks."""
        while not self._stop_event.is_set():
            # Sleep for check interval
            time.sleep(self._stability_check_interval)

            # Get snapshot of pending files
            with self._pending_lock:
                files_to_check = list(self._pending_files.items())

            # Check each pending file
            for file_path, detection_time in files_to_check:
                # Skip if file doesn't exist
                if not file_path.exists():
                    with self._pending_lock:
                        self._pending_files.pop(file_path, None)
                    continue

                try:
                    # Get current file size and mtime
                    current_size = file_path.stat().st_size
                    current_mtime = file_path.stat().st_mtime

                    # Check if we have a previous size recorded
                    file_key = f"{file_path}_size"
                    previous_size = getattr(self, file_key, None)
                    file_mtime_key = f"{file_path}_mtime"
                    previous_mtime = getattr(self, file_mtime_key, None)

                    # If this is the first check, just record the size
                    if previous_size is None:
                        setattr(self, file_key, current_size)
                        setattr(self, file_mtime_key, current_mtime)
                        continue

                    # Check if file has been stable for required duration
                    time_since_detection = time.time() - detection_time

                    # File is stable if:
                    # 1. Size hasn't changed since last check
                    # 2. Mtime hasn't changed since last check
                    # 3. At least stability_duration has passed since detection
                    if (
                        current_size == previous_size
                        and current_mtime == previous_mtime
                        and time_since_detection >= self._stability_duration
                    ):
                        # File is stable, trigger callback
                        with self._pending_lock:
                            self._pending_files.pop(file_path, None)

                        # Clean up stored attributes
                        delattr(self, file_key)
                        delattr(self, file_mtime_key)

                        # Trigger callback
                        try:
                            self.callback(file_path)
                        except Exception:
                            # Ignore callback errors to prevent watcher from stopping
                            pass
                    else:
                        # File changed, update stored size and reset detection time
                        if current_size != previous_size or current_mtime != previous_mtime:
                            setattr(self, file_key, current_size)
                            setattr(self, file_mtime_key, current_mtime)
                            with self._pending_lock:
                                self._pending_files[file_path] = time.time()

                except (OSError, PermissionError):
                    # File access error, remove from pending
                    with self._pending_lock:
                        self._pending_files.pop(file_path, None)


class _ScanFileEventHandler(FileSystemEventHandler):
    """Event handler for scan file detection."""

    def __init__(
        self, file_prefix: str, on_file_detected: Callable[[Path], None]
    ) -> None:
        """
        Initialize event handler.

        Args:
            file_prefix: File prefix to detect
            on_file_detected: Callback for detected files
        """
        super().__init__()
        self.file_prefix = file_prefix
        self.on_file_detected = on_file_detected
        self._seen_files: set[Path] = set()

    def on_created(self, event: FileSystemEvent) -> None:
        """
        Handle file creation event.

        Args:
            event: File system event
        """
        if event.is_directory:
            return

        file_path = Path(event.src_path)

        # Check if file matches prefix
        if not file_path.name.startswith(self.file_prefix):
            return

        # Debounce: only process each file once
        if file_path in self._seen_files:
            return

        self._seen_files.add(file_path)

        # Trigger detection callback
        self.on_file_detected(file_path)

    def on_modified(self, event: FileSystemEvent) -> None:
        """
        Handle file modification event.

        Args:
            event: File system event
        """
        if event.is_directory:
            return

        file_path = Path(event.src_path)

        # Check if file matches prefix
        if not file_path.name.startswith(self.file_prefix):
            return

        # If we haven't seen this file yet, treat it as a new file
        if file_path not in self._seen_files:
            self._seen_files.add(file_path)
            self.on_file_detected(file_path)
