# Design Document: Multi-Directory Multi-Prefix Watch

## Overview

This design extends Scanner-Watcher2's monitoring capabilities to support multiple watch directories and multiple file prefixes. The current architecture monitors a single directory for files matching a single prefix. This enhancement maintains the existing component structure while enabling parallel monitoring of multiple directories and detection of files with any configured prefix.

The design prioritizes backward compatibility, ensuring existing configurations continue to work while providing a migration path to the enhanced functionality.

## Architecture

### Component Changes

The enhancement affects three primary components:

1. **Configuration Layer** (`config.py`): Update Pydantic models to accept arrays instead of single values
2. **Directory Watcher** (`directory_watcher.py`): Modify to accept multiple prefixes
3. **Service Orchestrator** (`orchestrator.py`): Manage multiple Directory_Watcher instances

### Data Flow

```
Config File (JSON)
    ↓
Config Model (validates arrays)
    ↓
Service Orchestrator (creates N watchers)
    ↓
Directory Watcher 1, 2, ..., N (each monitors one directory)
    ↓
File Processor (processes detected files)
```

Each Directory_Watcher instance operates independently, monitoring its assigned directory for files matching any of the configured prefixes. When a file is detected, the watcher invokes the same callback used today, maintaining the existing processing pipeline.

## Components and Interfaces

### ProcessingConfig Changes

**Current Interface:**
```python
class ProcessingConfig(BaseModel):
    file_prefix: str = "SCAN-"
    # ... other fields
```

**New Interface:**
```python
class ProcessingConfig(BaseModel):
    file_prefixes: list[str] = Field(default_factory=lambda: ["SCAN-"])
    # ... other fields
    
    @field_validator("file_prefixes")
    @classmethod
    def validate_file_prefixes(cls, v: list[str]) -> list[str]:
        """Validate that all prefixes are non-empty and contain valid characters."""
        if not v:
            raise ValueError("file_prefixes cannot be empty")
        
        validated = []
        invalid_chars = '<>:"|?*\\/\0'
        
        for prefix in v:
            if not prefix or not prefix.strip():
                raise ValueError("file_prefix cannot be empty")
            
            for char in invalid_chars:
                if char in prefix:
                    raise ValueError(
                        f"file_prefix contains invalid filename character: '{char}'"
                    )
            
            validated.append(prefix.strip())
        
        return validated
    
    @model_validator(mode="before")
    @classmethod
    def convert_legacy_prefix(cls, data: dict) -> dict:
        """Convert legacy single file_prefix to file_prefixes array."""
        if isinstance(data, dict):
            if "file_prefix" in data and "file_prefixes" not in data:
                data["file_prefixes"] = [data.pop("file_prefix")]
        return data
```

### Config Changes

**Current Interface:**
```python
class Config(BaseModel):
    watch_directory: Path
    # ... other fields
```

**New Interface:**
```python
class Config(BaseModel):
    watch_directories: list[Path] = Field(min_length=1)
    # ... other fields
    
    @field_validator("watch_directories")
    @classmethod
    def validate_watch_directories(cls, v: list[Path]) -> list[Path]:
        """Validate that all watch directory paths are absolute."""
        if not v:
            raise ValueError("watch_directories cannot be empty")
        
        validated = []
        for path in v:
            if not path.is_absolute():
                raise ValueError(f"watch_directory must be an absolute path: {path}")
            validated.append(path)
        
        return validated
    
    @model_validator(mode="before")
    @classmethod
    def convert_legacy_directory(cls, data: dict) -> dict:
        """Convert legacy single watch_directory to watch_directories array."""
        if isinstance(data, dict):
            if "watch_directory" in data and "watch_directories" not in data:
                data["watch_directories"] = [data.pop("watch_directory")]
        return data
```

### DirectoryWatcher Changes

**Current Interface:**
```python
def __init__(
    self, watch_path: Path, file_prefix: str, callback: Callable[[Path], None]
) -> None:
```

**New Interface:**
```python
def __init__(
    self, watch_path: Path, file_prefixes: list[str], callback: Callable[[Path], None]
) -> None:
    """
    Initialize watcher with path and callback.

    Args:
        watch_path: Directory to monitor
        file_prefixes: List of file prefixes to detect (e.g., ["SCAN-", "DOC-"])
        callback: Function to call when file is detected
    """
    self.watch_path = watch_path
    self.file_prefixes = file_prefixes
    self.callback = callback
    # ... rest of initialization
```

The `_ScanFileEventHandler` class will be updated to check if the filename starts with ANY of the configured prefixes:

```python
def on_created(self, event: FileSystemEvent) -> None:
    """Handle file creation event."""
    if event.is_directory:
        return

    file_path = Path(event.src_path)

    # Check if file matches any prefix
    matches_prefix = any(
        file_path.name.startswith(prefix) for prefix in self.file_prefixes
    )
    
    if not matches_prefix:
        return

    # ... rest of handling logic
```

### ServiceOrchestrator Changes

**Current Implementation:**
```python
def start(self) -> None:
    """Start all components."""
    self.directory_watcher = DirectoryWatcher(
        watch_path=self.config.watch_directory,
        file_prefix=self.config.processing.file_prefix,
        callback=self._process_file_callback,
    )
    self.directory_watcher.start()
```

**New Implementation:**
```python
def __init__(self, config: Config) -> None:
    """Initialize with configuration."""
    # ... existing initialization
    self.directory_watchers: list[DirectoryWatcher] = []

def start(self) -> None:
    """Start all components."""
    self.logger.info("Starting ServiceOrchestrator")
    
    # Create a directory watcher for each configured directory
    for watch_dir in self.config.watch_directories:
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

def stop(self, timeout: int = 30) -> None:
    """Gracefully stop all components."""
    self.logger.info("Stopping ServiceOrchestrator", timeout=timeout)
    start_time = time.time()
    
    # Signal stop
    self._stop_event.set()
    
    # Stop all directory watchers
    for watcher in self.directory_watchers:
        watcher.stop()
    
    self.logger.info("All directory watchers stopped")
    
    # ... rest of shutdown logic
```

### Health Check Updates

The health check will be enhanced to validate all watch directories:

```python
def health_check(self) -> HealthStatus:
    """Perform system health check."""
    check_time = datetime.now()
    details: dict = {}
    
    # Check all watch directories
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
    
    # ... rest of health check logic
    
    is_healthy = all_accessible and config_valid
    
    return HealthStatus(
        is_healthy=is_healthy,
        watch_directory_accessible=all_accessible,
        config_valid=config_valid,
        last_check_time=check_time,
        consecutive_failures=self._consecutive_health_failures,
        details=details,
    )
```

## Data Models

### Configuration JSON Format

**Legacy Format (still supported):**
```json
{
  "version": "1.0.0",
  "watch_directory": "C:\\Scans",
  "processing": {
    "file_prefix": "SCAN-"
  }
}
```

**New Format:**
```json
{
  "version": "1.0.0",
  "watch_directories": [
    "C:\\Scans",
    "C:\\Documents\\Incoming",
    "D:\\SharedScans"
  ],
  "processing": {
    "file_prefixes": ["SCAN-", "DOC-", "IMG-"]
  }
}
```

### Migration Strategy

The design uses Pydantic's `model_validator` with `mode="before"` to automatically convert legacy configurations:

1. If `watch_directory` exists and `watch_directories` doesn't, convert to single-element array
2. If `file_prefix` exists and `file_prefixes` doesn't, convert to single-element array
3. If both old and new formats exist, prefer the new format

This ensures zero-downtime upgrades for existing users.


## Correctness Properties

A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.

### Property 1: Configuration accepts list of file prefixes

*For any* valid list of non-empty strings containing only valid filename characters, the Processing_Config should accept it as file_prefixes.

**Validates: Requirements 1.1**

### Property 2: File detection matches any configured prefix

*For any* filename and any list of prefixes, if the filename starts with at least one prefix from the list, the Directory_Watcher should detect it.

**Validates: Requirements 1.2**

### Property 3: Invalid prefix characters are rejected

*For any* string containing Windows invalid filename characters (<>:"|?*\\/\0), the Processing_Config should reject it as a file prefix.

**Validates: Requirements 1.3**

### Property 4: Duplicate prefixes are accepted

*For any* list of prefixes containing duplicates, the Processing_Config should accept the configuration without error.

**Validates: Requirements 1.5**

### Property 5: Configuration accepts list of watch directories

*For any* valid list of absolute paths, the Config should accept it as watch_directories.

**Validates: Requirements 2.1**

### Property 6: Watcher count equals directory count

*For any* configuration with N watch directories, the Service_Orchestrator should create exactly N Directory_Watcher instances.

**Validates: Requirements 2.2, 6.1**

### Property 7: Only absolute paths are accepted

*For any* path that is not absolute, the Config should reject it as a watch directory.

**Validates: Requirements 2.3**

### Property 8: Non-existent directories don't prevent startup

*For any* configuration where some watch directories don't exist, the Service_Orchestrator should start successfully and monitor the directories that do exist.

**Validates: Requirements 2.5**

### Property 9: All watchers use same processing pipeline

*For any* file detected in any watch directory, the System should invoke the same file processing callback.

**Validates: Requirements 2.6, 6.3**

### Property 10: Legacy single-value format is converted

*For any* configuration using legacy single watch_directory or file_prefix fields, the Config should convert them to single-element arrays.

**Validates: Requirements 3.3, 4.1, 4.2**

### Property 11: New array format is preserved

*For any* configuration using the new array format for watch_directories and file_prefixes, the Config should load them without modification.

**Validates: Requirements 4.3**

### Property 12: Health check validates all directories

*For any* configuration with N watch directories, the health check should verify accessibility of all N directories.

**Validates: Requirements 5.1**

### Property 13: Inaccessible directory causes unhealthy status

*For any* configuration where at least one watch directory is inaccessible, the Health_Status should report is_healthy as False.

**Validates: Requirements 5.2**

### Property 14: Health check details include all directories

*For any* health check result, the details dictionary should contain accessibility status for each configured watch directory.

**Validates: Requirements 5.3**

### Property 15: All accessible directories yield healthy status

*For any* configuration where all watch directories are accessible, the Health_Status should report is_healthy as True (assuming other health criteria are met).

**Validates: Requirements 5.4**

### Property 16: All watchers are stopped on shutdown

*For any* Service_Orchestrator with N running Directory_Watchers, calling stop() should stop all N watchers.

**Validates: Requirements 6.2**

### Property 17: Concurrent file detection is thread-safe

*For any* set of files detected simultaneously across different directories, the System should process all files without race conditions or data corruption.

**Validates: Requirements 6.4**

### Property 18: Startup logs all directories

*For any* configuration with N watch directories, the startup logs should contain entries for all N directories.

**Validates: Requirements 7.1**

### Property 19: Startup logs all prefixes

*For any* configuration with M file prefixes, the startup logs should contain entries showing all M prefixes.

**Validates: Requirements 7.2**

### Property 20: Detection logs include source directory

*For any* file detected by a Directory_Watcher, the log entry should include which watch directory the file was found in.

**Validates: Requirements 7.3**

### Property 21: Detection logs include matched prefix

*For any* file detected by a Directory_Watcher, the log entry should include which prefix matched the filename.

**Validates: Requirements 7.4**

## Error Handling

### Configuration Validation Errors

**Empty Lists:**
- Empty `watch_directories` list → Pydantic ValidationError with clear message
- Empty `file_prefixes` list → Pydantic ValidationError with clear message

**Invalid Paths:**
- Relative path in `watch_directories` → ValidationError: "watch_directory must be an absolute path"
- Invalid characters in prefix → ValidationError: "file_prefix contains invalid filename character"

**Backward Compatibility:**
- Missing both old and new fields → ValidationError
- Both old and new fields present → Prefer new format, ignore old

### Runtime Errors

**Directory Inaccessibility:**
- Non-existent directory at startup → Log warning, continue with other directories
- Directory becomes inaccessible during runtime → Health check reports unhealthy, continue monitoring other directories
- All directories inaccessible → Health check reports critical failure

**Watcher Failures:**
- Individual watcher fails to start → Log error, continue with other watchers
- Watcher crashes during operation → Error handler logs exception, other watchers continue
- Callback exception → Log error, watcher continues monitoring

### Recovery Strategies

**Graceful Degradation:**
- If some directories are inaccessible, monitor the accessible ones
- If a watcher fails, other watchers continue independently
- Health checks identify degraded state for administrator intervention

**Retry Logic:**
- Directory watcher uses existing file stability checking (2-second stability window)
- No automatic retry for directory creation (administrator must fix configuration)
- Existing error handler retry logic applies to file processing

## Testing Strategy

### Unit Tests

Unit tests will verify specific examples and edge cases:

- Empty list validation (watch_directories and file_prefixes)
- Single-element list handling
- Invalid character detection in prefixes
- Relative vs absolute path validation
- Legacy format conversion with specific examples
- Health check status calculation with specific directory states

### Property-Based Tests

Property-based tests will verify universal properties across all inputs using Hypothesis (minimum 100 iterations per test):

**Configuration Properties:**
- Property 1: Valid prefix lists are accepted
- Property 3: Invalid characters are rejected
- Property 4: Duplicate prefixes are accepted
- Property 5: Valid directory lists are accepted
- Property 7: Relative paths are rejected
- Property 10: Legacy format conversion
- Property 11: New format preservation

**Runtime Properties:**
- Property 2: File detection with any matching prefix
- Property 6: Watcher count equals directory count
- Property 8: Non-existent directories don't prevent startup
- Property 9: All watchers use same callback
- Property 12: Health check validates all directories
- Property 13: Inaccessible directory causes unhealthy status
- Property 14: Health check details include all directories
- Property 15: All accessible directories yield healthy status
- Property 16: All watchers stopped on shutdown
- Property 17: Concurrent detection is thread-safe
- Property 18-21: Logging properties

**Test Configuration:**
- Each property test runs minimum 100 iterations
- Tests use Hypothesis strategies for generating:
  - Valid/invalid file prefixes
  - Absolute/relative paths
  - Directory lists of varying sizes
  - Filename patterns
- Tests are tagged with: **Feature: multi-directory-multi-prefix-watch, Property N: [property text]**

### Integration Tests

Integration tests will verify component interactions:

- Multiple watchers detecting files simultaneously
- Health check with mixed accessible/inaccessible directories
- Full startup/shutdown cycle with multiple watchers
- Legacy configuration migration in real config files
- File processing from multiple directories

### Test Organization

Tests will be organized following the existing structure:
- `tests/unit/test_config.py` - Configuration validation tests
- `tests/unit/test_directory_watcher.py` - Watcher behavior tests
- `tests/unit/test_orchestrator.py` - Orchestrator lifecycle tests
- `tests/property/test_config_properties.py` - Configuration property tests
- `tests/property/test_directory_watcher_properties.py` - Watcher property tests
- `tests/property/test_orchestrator_properties.py` - Orchestrator property tests
- `tests/integration/test_multi_directory_watch.py` - End-to-end integration tests
