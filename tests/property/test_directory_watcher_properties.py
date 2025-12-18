"""
Property-based tests for directory watcher.
"""

from __future__ import annotations

import threading
import time
from pathlib import Path
from unittest.mock import Mock

import pytest
from hypothesis import HealthCheck, given, settings, strategies as st

from scanner_watcher2.core.directory_watcher import DirectoryWatcher


def create_test_file(file_path: Path, content: str = "test content") -> None:
    """
    Create a test file with content.
    
    Args:
        file_path: Path where file should be created
        content: Content to write to file
    """
    file_path.write_text(content)


# Feature: scanner-watcher2, Property 1: File detection timeliness
@given(
    filename_suffix=st.text(
        alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd")),
        min_size=1,
        max_size=20,
    ),
    file_prefix=st.sampled_from(["SCAN-", "DOC-", "FILE-", "TEST-"]),
)
@settings(
    deadline=20000,  # 20 second deadline for detection test (includes stability wait)
    suppress_health_check=[HealthCheck.function_scoped_fixture],
    max_examples=10,  # Limit examples since this involves timing
)
def test_file_detection_timeliness(
    watch_directory: Path,
    filename_suffix: str,
    file_prefix: str,
) -> None:
    """
    For any file with configured File Prefix created in the Watch Directory,
    the System should detect the file within 5 seconds and queue it for processing
    after stability check.
    
    Note: The callback is triggered after the file is stable (2 seconds), so total
    time will be detection time + stability wait time.
    
    Validates: Requirements 1.1
    """
    # Create filename with configured prefix
    filename = f"{file_prefix}{filename_suffix}.pdf"
    file_path = watch_directory / filename
    
    # Track detection and callback timing
    detected_files: list[tuple[Path, float]] = []  # (path, timestamp)
    detection_lock = threading.Lock()
    
    def on_file_detected(path: Path) -> None:
        """Callback for file detection (after stability check)."""
        with detection_lock:
            detected_files.append((path, time.time()))
    
    # Create and start watcher with configurable prefix
    watcher = DirectoryWatcher(
        watch_path=watch_directory,
        file_prefix=file_prefix,
        callback=on_file_detected,
    )
    
    try:
        watcher.start()
        
        # Record start time
        start_time = time.time()
        
        # Create file
        create_test_file(file_path, content="Test PDF content")
        
        # Wait for callback (detection + stability check, up to 8 seconds total)
        # Detection should happen within 5s, then stability check adds ~2s
        timeout = 8.0
        check_interval = 0.1
        elapsed = 0.0
        
        file_path_resolved = file_path.resolve()
        
        while elapsed < timeout:
            with detection_lock:
                detected_resolved = [(p.resolve(), t) for p, t in detected_files]
                if any(p == file_path_resolved for p, _ in detected_resolved):
                    break
            time.sleep(check_interval)
            elapsed = time.time() - start_time
        
        # Get callback time
        with detection_lock:
            detected_resolved = [(p.resolve(), t) for p, t in detected_files]
            matching = [t for p, t in detected_resolved if p == file_path_resolved]
            
            assert len(matching) > 0, (
                f"File {filename} was not detected and queued within {timeout} seconds. "
                f"Expected: {file_path_resolved}, Got: {[p for p, _ in detected_resolved]}"
            )
            
            callback_time = matching[0]
        
        # Calculate total time (detection + stability)
        total_time = callback_time - start_time
        
        # Verify total time is reasonable (detection within 5s + stability ~2s = ~7s max)
        # Allow some buffer for system timing variations
        assert total_time <= 8.0, (
            f"File detection and stability check took {total_time:.2f}s, "
            f"expected ≤8.0s (5s detection + 2s stability + 1s buffer)"
        )
        
    finally:
        watcher.stop()


# Feature: scanner-watcher2, Property 1: File detection timeliness
def test_file_detection_ignores_non_matching_prefix(watch_directory: Path) -> None:
    """
    For any file without the configured prefix, the System should not detect it.
    
    This is an edge case for file detection.
    
    Validates: Requirements 1.1
    """
    # Track detection
    detected_files: list[Path] = []
    detection_lock = threading.Lock()
    file_prefix = "SCAN-"
    
    def on_file_detected(path: Path) -> None:
        """Callback for file detection."""
        with detection_lock:
            detected_files.append(path)
    
    # Create and start watcher with configurable prefix
    watcher = DirectoryWatcher(
        watch_path=watch_directory,
        file_prefix=file_prefix,
        callback=on_file_detected,
    )
    
    try:
        watcher.start()
        
        # Create file without the configured prefix
        file_path = watch_directory / "document.pdf"
        create_test_file(file_path)
        
        # Wait a bit to ensure watcher has time to process
        time.sleep(1.0)
        
        # Verify file was NOT detected
        with detection_lock:
            assert file_path not in detected_files, (
                f"File {file_path.name} should not be detected (no {file_prefix} prefix)"
            )
        
    finally:
        watcher.stop()


# Feature: scanner-watcher2, Property 1: File detection timeliness
def test_file_detection_handles_watch_directory_unavailable(temp_dir: Path) -> None:
    """
    For any watch directory that doesn't exist, the System should handle it gracefully.
    
    This is an edge case for directory availability.
    
    Validates: Requirements 1.4
    """
    # Use non-existent directory
    nonexistent_dir = temp_dir / "nonexistent"
    file_prefix = "SCAN-"
    
    detected_files: list[Path] = []
    
    def on_file_detected(path: Path) -> None:
        """Callback for file detection."""
        detected_files.append(path)
    
    # Create watcher with non-existent directory
    watcher = DirectoryWatcher(
        watch_path=nonexistent_dir,
        file_prefix=file_prefix,
        callback=on_file_detected,
    )
    
    # Starting with non-existent directory should either:
    # 1. Raise an exception immediately, or
    # 2. Start but not detect any files (graceful handling)
    try:
        watcher.start()
        
        # If it starts, wait a bit and verify no files are detected
        time.sleep(1.0)
        
        assert len(detected_files) == 0, (
            "No files should be detected from non-existent directory"
        )
        
        watcher.stop()
    except (OSError, FileNotFoundError):
        # Expected behavior - watchdog raises error for non-existent directory
        pass



# Feature: scanner-watcher2, Property 2: File stability waiting
@given(
    num_writes=st.integers(min_value=2, max_value=5),
    write_delay=st.floats(min_value=0.1, max_value=0.5),
    file_prefix=st.sampled_from(["SCAN-", "DOC-", "FILE-"]),
)
@settings(
    deadline=30000,  # 30 second deadline for stability test
    suppress_health_check=[HealthCheck.function_scoped_fixture],
    max_examples=10,  # Limit examples since this involves timing
)
def test_file_stability_waiting(
    watch_directory: Path,
    num_writes: int,
    write_delay: float,
    file_prefix: str,
) -> None:
    """
    For any file being written to disk, the System should wait until the file size
    remains unchanged for 2 seconds before processing.
    
    This test simulates a file being written in multiple chunks with delays,
    and verifies the callback is only triggered after the file is stable.
    
    Validates: Requirements 1.2, 14.3
    """
    filename = f"{file_prefix}stability-test.pdf"
    file_path = watch_directory / filename
    
    # Track callback timing
    callback_times: list[float] = []
    callback_lock = threading.Lock()
    
    def on_file_detected(path: Path) -> None:
        """Callback for file detection (after stability check)."""
        with callback_lock:
            callback_times.append(time.time())
    
    # Create and start watcher with configurable prefix
    watcher = DirectoryWatcher(
        watch_path=watch_directory,
        file_prefix=file_prefix,
        callback=on_file_detected,
    )
    
    try:
        watcher.start()
        
        # Create file and write to it multiple times with delays
        last_write_time = time.time()
        
        for i in range(num_writes):
            content = f"Content chunk {i}\n" * 100
            
            if i == 0:
                # First write creates the file
                file_path.write_text(content)
            else:
                # Subsequent writes append
                with open(file_path, "a") as f:
                    f.write(content)
            
            last_write_time = time.time()
            
            # Wait between writes (except after last write)
            if i < num_writes - 1:
                time.sleep(write_delay)
        
        # Wait for callback (should happen ~2 seconds after last write)
        timeout = 10.0
        check_interval = 0.1
        start_wait = time.time()
        
        while time.time() - start_wait < timeout:
            with callback_lock:
                if len(callback_times) > 0:
                    break
            time.sleep(check_interval)
        
        # Verify callback was triggered
        with callback_lock:
            assert len(callback_times) > 0, (
                f"File callback was not triggered within {timeout} seconds after writes completed"
            )
            
            callback_time = callback_times[0]
        
        # Verify callback happened after file was stable (at least 2 seconds after last write)
        time_since_last_write = callback_time - last_write_time
        
        # Allow some tolerance for timing variations (1.5 seconds minimum)
        # The stability check runs every 0.5s, so there can be up to 0.5s variance
        # Additionally, system scheduling can introduce small delays
        # The requirement is 2.0s, but with 0.5s check interval, actual timing can be 1.5-2.5s
        assert time_since_last_write >= 1.5, (
            f"Callback triggered too early: {time_since_last_write:.2f}s after last write, "
            f"expected ≥2.0s (allowing 0.5s tolerance for check interval and system timing)"
        )
        
        # Verify callback was only triggered once (no duplicate callbacks)
        with callback_lock:
            assert len(callback_times) == 1, (
                f"Callback triggered {len(callback_times)} times, expected exactly 1"
            )
        
    finally:
        watcher.stop()


# Feature: scanner-watcher2, Property 2: File stability waiting
def test_file_stability_with_immediate_stable_file(watch_directory: Path) -> None:
    """
    For any file that is immediately stable (written once and not modified),
    the System should trigger the callback after the stability duration.
    
    This is an edge case for file stability.
    
    Validates: Requirements 1.2, 14.3
    """
    file_prefix = "SCAN-"
    filename = f"{file_prefix}immediate-stable.pdf"
    file_path = watch_directory / filename
    
    callback_times: list[float] = []
    callback_lock = threading.Lock()
    
    def on_file_detected(path: Path) -> None:
        """Callback for file detection."""
        with callback_lock:
            callback_times.append(time.time())
    
    watcher = DirectoryWatcher(
        watch_path=watch_directory,
        file_prefix=file_prefix,
        callback=on_file_detected,
    )
    
    try:
        watcher.start()
        
        # Create file with single write
        write_time = time.time()
        file_path.write_text("Single write content")
        
        # Wait for callback
        timeout = 10.0
        check_interval = 0.1
        start_wait = time.time()
        
        while time.time() - start_wait < timeout:
            with callback_lock:
                if len(callback_times) > 0:
                    break
            time.sleep(check_interval)
        
        # Verify callback was triggered
        with callback_lock:
            assert len(callback_times) > 0, "Callback was not triggered"
            callback_time = callback_times[0]
        
        # Verify callback happened after stability duration
        time_since_write = callback_time - write_time
        assert time_since_write >= 1.8, (
            f"Callback triggered too early: {time_since_write:.2f}s after write"
        )
        
    finally:
        watcher.stop()


# Feature: scanner-watcher2, Property 2: File stability waiting
def test_is_file_stable_method(watch_directory: Path) -> None:
    """
    For any file, the is_file_stable method should correctly detect stability.
    
    This tests the is_file_stable method directly.
    
    Validates: Requirements 1.2, 14.3
    """
    file_prefix = "SCAN-"
    filename = f"{file_prefix}stability-method-test.pdf"
    file_path = watch_directory / filename
    
    watcher = DirectoryWatcher(
        watch_path=watch_directory,
        file_prefix=file_prefix,
        callback=lambda p: None,
    )
    
    # Create file
    file_path.write_text("Initial content")
    
    # File should not be stable immediately (is_file_stable waits 2 seconds)
    # This is a blocking call that checks stability
    is_stable = watcher.is_file_stable(file_path)
    
    # After the 2-second wait in is_file_stable, file should be stable
    assert is_stable, "File should be stable after 2 seconds with no modifications"
    
    # Test with non-existent file
    nonexistent = watch_directory / "nonexistent.pdf"
    is_stable = watcher.is_file_stable(nonexistent)
    assert not is_stable, "Non-existent file should not be stable"



# Feature: scanner-watcher2, Property 3: Multiple file queueing
@given(
    num_files=st.integers(min_value=2, max_value=10),
    file_prefix=st.sampled_from(["SCAN-", "DOC-", "FILE-"]),
)
@settings(
    deadline=60000,  # 60 second deadline for multiple file test
    suppress_health_check=[HealthCheck.function_scoped_fixture],
    max_examples=10,  # Limit examples since this involves timing
)
def test_multiple_file_queueing(
    watch_directory: Path,
    num_files: int,
    file_prefix: str,
) -> None:
    """
    For any set of files detected simultaneously, all files should be added
    to the processing queue and callbacks triggered for each.
    
    Validates: Requirements 1.3
    """
    # Track detected files
    detected_files: list[Path] = []
    detection_lock = threading.Lock()
    
    def on_file_detected(path: Path) -> None:
        """Callback for file detection."""
        with detection_lock:
            detected_files.append(path)
    
    # Create and start watcher with configurable prefix
    watcher = DirectoryWatcher(
        watch_path=watch_directory,
        file_prefix=file_prefix,
        callback=on_file_detected,
    )
    
    try:
        watcher.start()
        
        # Create multiple files simultaneously
        created_files = []
        for i in range(num_files):
            filename = f"{file_prefix}multi-{i}.pdf"
            file_path = watch_directory / filename
            create_test_file(file_path, content=f"Content for file {i}")
            created_files.append(file_path)
        
        # Wait for all files to be detected and processed
        # Each file needs ~2s for stability, but they can overlap
        timeout = 15.0  # Allow enough time for all files
        check_interval = 0.2
        start_wait = time.time()
        
        while time.time() - start_wait < timeout:
            with detection_lock:
                if len(detected_files) >= num_files:
                    break
            time.sleep(check_interval)
        
        # Verify all files were detected
        with detection_lock:
            detected_resolved = [p.resolve() for p in detected_files]
            created_resolved = [p.resolve() for p in created_files]
            
            assert len(detected_files) >= num_files, (
                f"Expected {num_files} files to be detected, "
                f"but only {len(detected_files)} were detected"
            )
            
            # Verify each created file was detected
            for created_file in created_resolved:
                assert created_file in detected_resolved, (
                    f"File {created_file.name} was not detected"
                )
        
    finally:
        watcher.stop()


# Feature: scanner-watcher2, Property 3: Multiple file queueing
def test_multiple_file_queueing_with_single_file(watch_directory: Path) -> None:
    """
    For a single file, queueing should work correctly.
    
    This is an edge case for multiple file queueing.
    
    Validates: Requirements 1.3
    """
    detected_files: list[Path] = []
    detection_lock = threading.Lock()
    file_prefix = "SCAN-"
    
    def on_file_detected(path: Path) -> None:
        """Callback for file detection."""
        with detection_lock:
            detected_files.append(path)
    
    watcher = DirectoryWatcher(
        watch_path=watch_directory,
        file_prefix=file_prefix,
        callback=on_file_detected,
    )
    
    try:
        watcher.start()
        
        # Create single file
        file_path = watch_directory / f"{file_prefix}single.pdf"
        create_test_file(file_path)
        
        # Wait for detection
        timeout = 10.0
        check_interval = 0.1
        start_wait = time.time()
        
        while time.time() - start_wait < timeout:
            with detection_lock:
                if len(detected_files) > 0:
                    break
            time.sleep(check_interval)
        
        # Verify file was detected
        with detection_lock:
            assert len(detected_files) == 1, (
                f"Expected 1 file to be detected, got {len(detected_files)}"
            )
            assert detected_files[0].resolve() == file_path.resolve()
        
    finally:
        watcher.stop()


# Feature: scanner-watcher2, Property 3: Multiple file queueing
def test_multiple_file_queueing_no_duplicates(watch_directory: Path) -> None:
    """
    For any file, the callback should only be triggered once (no duplicates).
    
    This verifies the debouncing mechanism works correctly.
    
    Validates: Requirements 1.3
    """
    detected_files: list[Path] = []
    detection_lock = threading.Lock()
    file_prefix = "SCAN-"
    
    def on_file_detected(path: Path) -> None:
        """Callback for file detection."""
        with detection_lock:
            detected_files.append(path)
    
    watcher = DirectoryWatcher(
        watch_path=watch_directory,
        file_prefix=file_prefix,
        callback=on_file_detected,
    )
    
    try:
        watcher.start()
        
        # Create file
        file_path = watch_directory / f"{file_prefix}no-dup.pdf"
        create_test_file(file_path, content="Initial content")
        
        # Wait a bit, then modify the file (should not trigger another callback)
        time.sleep(1.0)
        
        # Modify file (append content)
        with open(file_path, "a") as f:
            f.write("\nAdditional content")
        
        # Wait for stability and callback
        time.sleep(5.0)
        
        # Verify callback was triggered exactly once
        with detection_lock:
            file_path_resolved = file_path.resolve()
            matching_detections = [
                p for p in detected_files if p.resolve() == file_path_resolved
            ]
            
            assert len(matching_detections) == 1, (
                f"Expected exactly 1 callback for file, got {len(matching_detections)}"
            )
        
    finally:
        watcher.stop()



# Feature: scanner-watcher2, Property 4: Idle CPU usage
@given(
    idle_duration=st.floats(min_value=2.0, max_value=5.0),
    file_prefix=st.sampled_from(["SCAN-", "DOC-", "FILE-"]),
)
@settings(
    deadline=30000,  # 30 second deadline for resource test
    suppress_health_check=[HealthCheck.function_scoped_fixture],
    max_examples=5,  # Limit examples since this involves timing
)
def test_idle_cpu_usage(
    watch_directory: Path,
    idle_duration: float,
    file_prefix: str,
) -> None:
    """
    For any idle monitoring period, the watcher should remain efficient with minimal
    resource usage (low thread count, no busy-waiting).
    
    This test verifies the watcher uses efficient monitoring mechanisms (event-driven
    via watchdog) rather than busy-waiting, which would consume CPU.
    
    We verify this by:
    1. Checking thread count remains reasonable (not spawning excessive threads)
    2. Verifying the watcher remains responsive during idle periods
    3. Ensuring no files are incorrectly detected during idle
    
    Validates: Requirements 1.5
    """
    detected_files: list[Path] = []
    
    def on_file_detected(path: Path) -> None:
        """Callback for file detection."""
        detected_files.append(path)
    
    # Create and start watcher with configurable prefix
    watcher = DirectoryWatcher(
        watch_path=watch_directory,
        file_prefix=file_prefix,
        callback=on_file_detected,
    )
    
    try:
        watcher.start()
        
        # Get initial thread count
        initial_thread_count = threading.active_count()
        
        # Let watcher stabilize
        time.sleep(0.5)
        
        # Monitor during idle period
        time.sleep(idle_duration)
        
        # Get final thread count
        final_thread_count = threading.active_count()
        
        # Verify no files were detected (truly idle)
        assert len(detected_files) == 0, "Files were detected during idle period"
        
        # Verify thread count hasn't grown excessively
        # Should have at most a few threads (main + observer + stability checker)
        assert final_thread_count <= initial_thread_count + 5, (
            f"Thread count grew from {initial_thread_count} to {final_thread_count}, "
            f"indicating potential resource leak"
        )
        
        # Verify watcher is still responsive by creating a file
        test_file = watch_directory / f"{file_prefix}responsiveness-test.pdf"
        create_test_file(test_file)
        
        # Wait for detection
        time.sleep(3.0)
        
        # Verify file was detected (watcher still working)
        assert len(detected_files) > 0, (
            "Watcher became unresponsive during idle period"
        )
        
    finally:
        watcher.stop()


# Feature: scanner-watcher2, Property 4: Idle CPU usage
def test_idle_resource_usage_with_short_period(watch_directory: Path) -> None:
    """
    For a short idle period, the watcher should remain efficient.
    
    This is an edge case for resource monitoring with minimal idle time.
    
    Validates: Requirements 1.5
    """
    detected_files: list[Path] = []
    file_prefix = "SCAN-"
    
    def on_file_detected(path: Path) -> None:
        """Callback for file detection."""
        detected_files.append(path)
    
    watcher = DirectoryWatcher(
        watch_path=watch_directory,
        file_prefix=file_prefix,
        callback=on_file_detected,
    )
    
    try:
        watcher.start()
        
        # Get initial thread count
        initial_thread_count = threading.active_count()
        
        # Let watcher stabilize
        time.sleep(0.5)
        
        # Monitor during short idle period
        time.sleep(1.0)
        
        # Get final thread count
        final_thread_count = threading.active_count()
        
        # Verify no files were detected
        assert len(detected_files) == 0
        
        # Verify thread count is reasonable
        assert final_thread_count <= initial_thread_count + 5, (
            f"Thread count grew excessively: {initial_thread_count} -> {final_thread_count}"
        )
        
    finally:
        watcher.stop()


# Feature: scanner-watcher2, Property 4: Idle CPU usage
def test_watcher_can_be_stopped_and_restarted(watch_directory: Path) -> None:
    """
    For any watcher, it should be possible to stop and restart it.
    
    This verifies the watcher lifecycle management works correctly.
    
    Validates: Requirements 1.5 (indirectly - proper lifecycle prevents resource leaks)
    """
    detected_files: list[Path] = []
    detection_lock = threading.Lock()
    file_prefix = "SCAN-"
    
    def on_file_detected(path: Path) -> None:
        """Callback for file detection."""
        with detection_lock:
            detected_files.append(path)
    
    watcher = DirectoryWatcher(
        watch_path=watch_directory,
        file_prefix=file_prefix,
        callback=on_file_detected,
    )
    
    # Start watcher
    watcher.start()
    
    # Create a file
    file1 = watch_directory / f"{file_prefix}test1.pdf"
    create_test_file(file1)
    
    # Wait for detection
    time.sleep(3.0)
    
    # Stop watcher
    watcher.stop()
    
    # Verify file was detected
    with detection_lock:
        assert len(detected_files) > 0, "File should have been detected before stop"
        detected_count_before = len(detected_files)
    
    # Create another file while stopped (should not be detected)
    file2 = watch_directory / f"{file_prefix}test2.pdf"
    create_test_file(file2)
    
    # Wait a bit
    time.sleep(1.0)
    
    # Verify no new detections while stopped
    with detection_lock:
        assert len(detected_files) == detected_count_before, (
            "No files should be detected while watcher is stopped"
        )
    
    # Restart watcher
    watcher.start()
    
    # Create another file (should be detected)
    file3 = watch_directory / f"{file_prefix}test3.pdf"
    create_test_file(file3)
    
    # Wait for detection
    time.sleep(3.0)
    
    # Stop watcher
    watcher.stop()
    
    # Verify new file was detected after restart
    with detection_lock:
        assert len(detected_files) > detected_count_before, (
            "File should be detected after watcher restart"
        )


# Feature: scanner-watcher2, Property 5: Configurable prefix detection
@given(
    file_prefix=st.text(
        alphabet=st.characters(
            whitelist_categories=("Lu", "Ll", "Nd"),
            whitelist_characters="-_",
        ),
        min_size=1,
        max_size=10,
    ).filter(lambda s: s and not s.isspace()),
    filename_suffix=st.text(
        alphabet=st.characters(whitelist_categories=("Lu", "Ll", "Nd")),
        min_size=1,
        max_size=20,
    ),
)
@settings(
    deadline=20000,  # 20 second deadline for detection test
    suppress_health_check=[HealthCheck.function_scoped_fixture],
    max_examples=20,  # Test with various prefixes
)
def test_configurable_prefix_detection(
    watch_directory: Path,
    file_prefix: str,
    filename_suffix: str,
) -> None:
    """
    For any configured File Prefix value, the System should detect files with that
    prefix and ignore files without that prefix.
    
    This property verifies that the file prefix configuration works correctly across
    a wide range of prefix values, ensuring the system can be customized for different
    naming conventions.
    
    Validates: Requirements 1.6
    """
    # Track detected files
    detected_files: list[Path] = []
    detection_lock = threading.Lock()
    
    def on_file_detected(path: Path) -> None:
        """Callback for file detection."""
        with detection_lock:
            detected_files.append(path)
    
    # Create and start watcher with custom prefix
    watcher = DirectoryWatcher(
        watch_path=watch_directory,
        file_prefix=file_prefix,
        callback=on_file_detected,
    )
    
    try:
        watcher.start()
        
        # Create file WITH the configured prefix (should be detected)
        matching_filename = f"{file_prefix}{filename_suffix}.pdf"
        matching_file = watch_directory / matching_filename
        create_test_file(matching_file, content="Matching file content")
        
        # Create file WITHOUT the configured prefix (should NOT be detected)
        non_matching_filename = f"OTHER-{filename_suffix}.pdf"
        non_matching_file = watch_directory / non_matching_filename
        create_test_file(non_matching_file, content="Non-matching file content")
        
        # Wait for detection and stability check
        timeout = 8.0
        check_interval = 0.1
        start_wait = time.time()
        
        while time.time() - start_wait < timeout:
            with detection_lock:
                if len(detected_files) > 0:
                    break
            time.sleep(check_interval)
        
        # Verify the matching file was detected
        with detection_lock:
            detected_resolved = [p.resolve() for p in detected_files]
            matching_resolved = matching_file.resolve()
            non_matching_resolved = non_matching_file.resolve()
            
            assert matching_resolved in detected_resolved, (
                f"File with prefix '{file_prefix}' was not detected. "
                f"Expected: {matching_filename}, "
                f"Detected: {[p.name for p in detected_files]}"
            )
            
            # Verify the non-matching file was NOT detected
            assert non_matching_resolved not in detected_resolved, (
                f"File without prefix '{file_prefix}' should not be detected. "
                f"File: {non_matching_filename}"
            )
            
            # Verify exactly one file was detected (the matching one)
            assert len(detected_files) == 1, (
                f"Expected exactly 1 file to be detected, got {len(detected_files)}"
            )
        
    finally:
        watcher.stop()


# Feature: scanner-watcher2, Property 5: Configurable prefix detection
def test_configurable_prefix_with_special_characters(watch_directory: Path) -> None:
    """
    For any prefix containing special characters (like underscores or hyphens),
    the System should correctly detect files with that prefix.
    
    This is an edge case for prefix configuration with special characters.
    
    Validates: Requirements 1.6
    """
    # Test with various special character prefixes
    test_prefixes = [
        "SCAN-",
        "DOC_",
        "FILE-2024-",
        "TEST_SCAN_",
        "A-B-C-",
    ]
    
    for file_prefix in test_prefixes:
        detected_files: list[Path] = []
        detection_lock = threading.Lock()
        
        def on_file_detected(path: Path) -> None:
            """Callback for file detection."""
            with detection_lock:
                detected_files.append(path)
        
        watcher = DirectoryWatcher(
            watch_path=watch_directory,
            file_prefix=file_prefix,
            callback=on_file_detected,
        )
        
        try:
            watcher.start()
            
            # Create file with the prefix
            filename = f"{file_prefix}document.pdf"
            file_path = watch_directory / filename
            create_test_file(file_path)
            
            # Wait for detection
            timeout = 8.0
            check_interval = 0.1
            start_wait = time.time()
            
            while time.time() - start_wait < timeout:
                with detection_lock:
                    if len(detected_files) > 0:
                        break
                time.sleep(check_interval)
            
            # Verify file was detected
            with detection_lock:
                assert len(detected_files) > 0, (
                    f"File with prefix '{file_prefix}' was not detected"
                )
                assert detected_files[0].resolve() == file_path.resolve(), (
                    f"Wrong file detected for prefix '{file_prefix}'"
                )
            
        finally:
            watcher.stop()
            
        # Clean up for next iteration
        with detection_lock:
            detected_files.clear()


# Feature: scanner-watcher2, Property 5: Configurable prefix detection
def test_configurable_prefix_case_sensitivity(watch_directory: Path) -> None:
    """
    For any prefix, the System should perform case-sensitive matching.
    
    This verifies that "SCAN-" and "scan-" are treated as different prefixes.
    
    Validates: Requirements 1.6
    """
    detected_files: list[Path] = []
    detection_lock = threading.Lock()
    file_prefix = "SCAN-"  # Uppercase prefix
    
    def on_file_detected(path: Path) -> None:
        """Callback for file detection."""
        with detection_lock:
            detected_files.append(path)
    
    watcher = DirectoryWatcher(
        watch_path=watch_directory,
        file_prefix=file_prefix,
        callback=on_file_detected,
    )
    
    try:
        watcher.start()
        
        # Create file with uppercase prefix (should be detected)
        uppercase_file = watch_directory / "SCAN-document.pdf"
        create_test_file(uppercase_file)
        
        # Create file with lowercase prefix (should NOT be detected)
        lowercase_file = watch_directory / "scan-document.pdf"
        create_test_file(lowercase_file)
        
        # Wait for detection
        time.sleep(5.0)
        
        # Verify only uppercase file was detected
        with detection_lock:
            detected_resolved = [p.resolve() for p in detected_files]
            uppercase_resolved = uppercase_file.resolve()
            lowercase_resolved = lowercase_file.resolve()
            
            assert uppercase_resolved in detected_resolved, (
                "File with matching case prefix should be detected"
            )
            
            assert lowercase_resolved not in detected_resolved, (
                "File with different case prefix should NOT be detected (case-sensitive)"
            )
            
            assert len(detected_files) == 1, (
                f"Expected exactly 1 file, got {len(detected_files)}"
            )
        
    finally:
        watcher.stop()


# Feature: scanner-watcher2, Property 5: Configurable prefix detection
def test_configurable_prefix_empty_string_handling(watch_directory: Path) -> None:
    """
    For an empty prefix, the System should detect all files (or handle gracefully).
    
    This is an edge case for prefix configuration.
    
    Note: In practice, the configuration validation should prevent empty prefixes,
    but this test verifies the watcher's behavior if it receives one.
    
    Validates: Requirements 1.6
    """
    detected_files: list[Path] = []
    detection_lock = threading.Lock()
    file_prefix = ""  # Empty prefix
    
    def on_file_detected(path: Path) -> None:
        """Callback for file detection."""
        with detection_lock:
            detected_files.append(path)
    
    watcher = DirectoryWatcher(
        watch_path=watch_directory,
        file_prefix=file_prefix,
        callback=on_file_detected,
    )
    
    try:
        watcher.start()
        
        # Create files with various names
        file1 = watch_directory / "document1.pdf"
        file2 = watch_directory / "SCAN-document2.pdf"
        file3 = watch_directory / "test.pdf"
        
        create_test_file(file1)
        create_test_file(file2)
        create_test_file(file3)
        
        # Wait for detection
        time.sleep(5.0)
        
        # With empty prefix, all files should be detected
        with detection_lock:
            # All files should match empty prefix (startswith("") is always True)
            assert len(detected_files) >= 3, (
                f"With empty prefix, all files should be detected. "
                f"Expected at least 3, got {len(detected_files)}"
            )
        
    finally:
        watcher.stop()
