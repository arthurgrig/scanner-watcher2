# Design Document

## Overview

Scanner-Watcher2 is a Windows-native legal document processing system designed to automatically monitor directories, classify scanned documents using AI, and organize them with meaningful filenames. The system is built with Windows-first principles, featuring native service integration, zero-dependency installation, and production-ready error handling.

### Key Design Goals

1. **Windows-First Architecture**: Native Windows service using pywin32, standard Windows paths, and Windows Event Log integration
2. **Zero-Dependency Installation**: Single executable with embedded Python runtime via PyInstaller
3. **Production-Ready Reliability**: Comprehensive error handling with retry logic, circuit breakers, and graceful degradation
4. **Maintainability**: Clean separation of concerns, comprehensive logging, and extensive test coverage
5. **Performance**: Low resource usage (<5% CPU idle, <200MB memory), efficient file processing

### Technology Stack

- **Language**: Python 3.12+
- **Service Management**: pywin32 (win32serviceutil)
- **File Watching**: watchdog (uses Windows ReadDirectoryChangesW API)
- **PDF Processing**: PyMuPDF (fitz) with PyPDF2 fallback
- **AI Integration**: OpenAI Python SDK (GPT-4 Vision)
- **Configuration**: JSON with pydantic validation
- **Logging**: Python logging with structlog for structured JSON logs
- **Packaging**: PyInstaller for executable bundling, Inno Setup for installer
- **Testing**: pytest with pytest-mock

## Architecture

### High-Level Architecture

The system follows a layered architecture with clear separation between the Windows service layer, application core, and infrastructure:

```
┌─────────────────────────────────────────────────────────────┐
│                    Windows Service Layer                     │
│         (pywin32 - Native Windows Service)                   │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│                  Application Core                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Service    │  │  Directory   │  │    File      │     │
│  │ Orchestrator │──│   Watcher    │──│  Processor   │     │
│  └──────────────┘  └──────────────┘  └──────┬───────┘     │
│                                              │              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────▼───────┐     │
│  │     PDF      │  │      AI      │  │    File      │     │
│  │  Processor   │  │   Service    │  │   Manager    │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│              Infrastructure Layer                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Logging    │  │    Config    │  │    Error     │     │
│  │   System     │  │  Management  │  │   Handler    │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

### Architectural Patterns

1. **Service-Oriented Architecture**: Each component provides a well-defined service with clear interfaces
2. **Event-Driven Processing**: File system events trigger processing workflows
3. **Retry Pattern**: Transient errors are automatically retried with exponential backoff
4. **Circuit Breaker Pattern**: Prevents cascading failures when external services are unavailable
5. **Repository Pattern**: Abstracts file system operations for testability

## Components and Interfaces

### 1. Windows Service Layer

**Purpose**: Provides native Windows service integration

**Interface**:
```python
class ScannerWatcher2Service(win32serviceutil.ServiceFramework):
    def SvcStop(self) -> None:
        """Handle service stop request"""
        
    def SvcDoRun(self) -> None:
        """Main service entry point"""
        
    def main(self) -> None:
        """Initialize and run application"""
```

**Responsibilities**:
- Register and manage Windows service lifecycle
- Handle start/stop/restart commands from Windows Services Manager
- Integrate with Windows Event Log for service events
- Provide service status reporting
- Handle graceful shutdown with timeout

**Dependencies**: Service Orchestrator

### 2. Service Orchestrator

**Purpose**: Coordinates all application components and manages lifecycle

**Interface**:
```python
class ServiceOrchestrator:
    def __init__(self, config: Config):
        """Initialize with configuration"""
        
    def start(self) -> None:
        """Start all components"""
        
    def stop(self, timeout: int = 30) -> None:
        """Gracefully stop all components"""
        
    def run(self, stop_event: Event) -> None:
        """Main run loop with stop event"""
        
    def health_check(self) -> HealthStatus:
        """Perform system health check"""
```

**Responsibilities**:
- Initialize all application components in correct order
- Coordinate component startup and shutdown
- Manage health check scheduling
- Handle graceful shutdown with timeout
- Coordinate error recovery across components

**Dependencies**: Directory Watcher, Configuration Management, Logging System, Error Handler

### 3. Directory Watcher

**Purpose**: Monitor filesystem for new scan files

**Interface**:
```python
class DirectoryWatcher:
    def __init__(self, watch_path: Path, file_prefix: str, callback: Callable):
        """Initialize watcher with path and configurable file prefix"""
        
    def start(self) -> None:
        """Start watching directory"""
        
    def stop(self) -> None:
        """Stop watching directory"""
        
    def is_file_stable(self, file_path: Path) -> bool:
        """Check if file is done being written"""
```

**Responsibilities**:
- Monitor configured directory using watchdog library
- Detect files with configurable file prefix (default: "SCAN-")
- Debounce file events (wait for file to be stable)
- Queue files for processing via callback
- Handle network drive monitoring
- Detect when watch directory becomes unavailable

**Dependencies**: File Processor (via callback), Logging System

### 4. File Processor

**Purpose**: Coordinate the complete document processing workflow

**Interface**:
```python
class FileProcessor:
    def __init__(self, pdf_processor: PDFProcessor, ai_service: AIService, 
                 file_manager: FileManager):
        """Initialize with dependencies"""
        
    def process_file(self, file_path: Path) -> ProcessingResult:
        """Process a single file through complete workflow"""
        
    def validate_file(self, file_path: Path) -> bool:
        """Validate file type and accessibility"""
```

**Responsibilities**:
- Validate file type and accessibility
- Coordinate PDF page extraction
- Request AI classification
- Coordinate file renaming based on classification
- Clean up temporary files
- Handle processing errors and retries
- Track processing metrics

**Dependencies**: PDF Processor, AI Service, File Manager, Error Handler, Logging System

### 5. PDF Processor

**Purpose**: Extract pages from PDF documents for AI analysis

**Interface**:
```python
class PDFProcessor:
    def extract_first_pages(self, pdf_path: Path, num_pages: int = 3) -> list[Image]:
        """Extract first N pages as images (default: 3)"""
        
    def extract_page(self, pdf_path: Path, page_num: int) -> Image:
        """Extract a single page as image"""
        
    def optimize_image(self, image: Image) -> Image:
        """Optimize image for API transmission"""
        
    def validate_pdf(self, pdf_path: Path) -> bool:
        """Check if PDF is valid and readable"""
```

**Responsibilities**:
- Extract first three pages from PDF as images (or fewer if PDF has less than 3 pages)
- Try PyMuPDF first, fallback to PyPDF2
- Optimize image size for API transmission
- Handle corrupted PDFs gracefully
- Support various PDF formats
- Limit memory usage during processing
- Handle each page extraction independently to prevent single page failures from blocking the entire process

**Dependencies**: Logging System, Error Handler

### 6. AI Service

**Purpose**: Classify documents using OpenAI API

**Interface**:
```python
class AIService:
    def __init__(self, api_key: str, model: str, timeout: int):
        """Initialize with API credentials"""
        
    def classify_document(self, images: list[Image]) -> Classification:
        """Send multiple images to OpenAI and get classification"""
        
    def parse_classification(self, response: dict) -> Classification:
        """Parse OpenAI response into structured data"""
        
    def get_supported_document_types(self) -> list[str]:
        """Return list of supported document types for classification"""
```

**Supported Document Types**:
- Panel List
- QME Appointment Notification Form
- Agreed Medical Evaluator Report
- Qualified Medical Evaluator Report
- PTP Initial Report
- PTP P&S Report
- RFA (Request for Authorization)
- UR Approval
- UR Denial
- Modified UR
- Finding and Award
- Finding & Order
- Advocacy/Cover Letter
- Declaration of Readiness to Proceed
- Objection to Declaration of Readiness to Proceed

**Responsibilities**:
- Send multiple document images (up to 3 pages) to OpenAI API
- Include comprehensive list of supported document types in classification prompt
- Parse classification results with standardized document type names
- Handle API errors and rate limits
- Implement retry logic for transient failures
- Respect API timeouts
- Use HTTPS with TLS 1.2+
- Support corporate proxy configuration

**Dependencies**: Error Handler, Logging System

### 7. File Manager

**Purpose**: Handle all file system operations

**Interface**:
```python
class FileManager:
    def rename_file(self, source: Path, target_name: str) -> Path:
        """Rename file with conflict resolution"""
        
    def create_temp_file(self, suffix: str) -> Path:
        """Create temporary file"""
        
    def cleanup_temp_files(self, file_paths: List[Path]) -> None:
        """Delete temporary files"""
        
    def is_file_locked(self, file_path: Path) -> bool:
        """Check if file is locked by another process"""
```

**Responsibilities**:
- Rename files based on classification
- Handle file name conflicts (append suffix)
- Ensure atomic file operations
- Handle Windows file locking
- Manage temporary files
- Verify file operations succeeded
- Clean up temporary files

**Dependencies**: Error Handler, Logging System

### 8. Configuration Management

**Purpose**: Load, validate, and manage application configuration

**Interface**:
```python
class ConfigManager:
    def load_config(self, config_path: Path) -> Config:
        """Load and validate configuration"""
        
    def save_config(self, config: Config, config_path: Path) -> None:
        """Save configuration to file"""
        
    def encrypt_api_key(self, api_key: str) -> str:
        """Encrypt API key using Windows DPAPI"""
        
    def decrypt_api_key(self, encrypted: str) -> str:
        """Decrypt API key"""
```

**Configuration Schema**:
```python
class ProcessingConfig(BaseModel):
    file_prefix: str = "SCAN-"  # Configurable prefix for file detection
    pages_to_extract: int = Field(ge=1, le=10, default=3)  # Number of pages to extract
    retry_attempts: int = Field(ge=1, le=10, default=3)
    retry_delay_seconds: int = Field(ge=1, le=60, default=5)
    temp_directory: Optional[Path] = None

class AIConfig(BaseModel):
    model: str = "gpt-4-vision-preview"
    max_tokens: int = 500
    temperature: float = 0.1
    timeout_seconds: int = 30

class LoggingConfig(BaseModel):
    max_file_size_mb: int = 10
    backup_count: int = 5
    log_to_event_log: bool = True

class ServiceConfig(BaseModel):
    health_check_interval_seconds: int = 60
    graceful_shutdown_timeout_seconds: int = 30

class Config(BaseModel):
    version: str
    watch_directory: Path
    openai_api_key: str
    log_level: str = "INFO"
    processing: ProcessingConfig
    ai: AIConfig
    logging: LoggingConfig
    service: ServiceConfig
```

**Responsibilities**:
- Load configuration from %APPDATA%\ScannerWatcher2\config.json
- Validate all configuration fields
- Provide sensible defaults
- Encrypt/decrypt sensitive data (API keys) using Windows DPAPI
- Support configuration reload without restart
- Create default configuration if missing

**Dependencies**: Logging System

### 9. Logging System

**Purpose**: Provide comprehensive structured logging

**Interface**:
```python
class Logger:
    def debug(self, message: str, **context) -> None:
        """Log debug message with context"""
        
    def info(self, message: str, **context) -> None:
        """Log info message with context"""
        
    def warning(self, message: str, **context) -> None:
        """Log warning message with context"""
        
    def error(self, message: str, **context) -> None:
        """Log error message with context"""
        
    def critical(self, message: str, **context) -> None:
        """Log critical message and write to Event Log"""
```

**Log Format**:
```json
{
  "timestamp": "2024-12-12T10:30:45.123Z",
  "level": "INFO",
  "component": "FileProcessor",
  "message": "File processed successfully",
  "context": {
    "file_path": "D:\\Scans\\SCAN-document.pdf",
    "document_type": "Medical Report",
    "processing_time_ms": 1234,
    "file_size_bytes": 524288
  },
  "correlation_id": "abc123"
}
```

**Responsibilities**:
- Write structured JSON logs to %APPDATA%\ScannerWatcher2\logs\
- Rotate logs at 10MB, keep 5 backups
- Write critical events to Windows Event Log
- Include context information (file paths, timings, errors)
- Generate correlation IDs for request tracking
- Support multiple log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)

**Dependencies**: None (infrastructure component)

### 10. Error Handler

**Purpose**: Centralized error handling and retry logic

**Interface**:
```python
class ErrorHandler:
    def classify_error(self, error: Exception) -> ErrorType:
        """Classify error as transient, permanent, or critical"""
        
    def should_retry(self, error: Exception, attempt: int) -> bool:
        """Determine if operation should be retried"""
        
    def calculate_backoff(self, attempt: int) -> float:
        """Calculate exponential backoff delay"""
        
    def execute_with_retry(self, func: Callable, max_attempts: int) -> Any:
        """Execute function with retry logic"""
```

**Error Classification**:
- **Transient Errors**: Network timeouts, API rate limits, file locked, temporary disk full
- **Permanent Errors**: Invalid API key, corrupted PDF, unsupported format, permission denied
- **Critical Errors**: Watch directory disappeared, disk full, OpenAI API down
- **Fatal Errors**: Configuration corrupted, unable to write logs, out of memory

**Retry Strategy**:
- Max attempts: 3
- Initial delay: 1 second
- Exponential base: 2.0
- Max delay: 60 seconds
- Jitter: Random 0-500ms added to prevent thundering herd

**Circuit Breaker**:
- Threshold: 5 failures within 60 seconds
- Open duration: 5 minutes
- Half-open: Allow 1 test request after timeout

**Responsibilities**:
- Classify errors into categories
- Implement retry logic with exponential backoff
- Implement circuit breaker pattern for external services
- Provide recovery strategies
- Track error rates and patterns

**Dependencies**: Logging System

## Data Models

### ProcessingResult

```python
@dataclass
class ProcessingResult:
    success: bool
    file_path: Path
    document_type: Optional[str]
    new_file_path: Optional[Path]
    processing_time_ms: int
    error: Optional[str]
    correlation_id: str
```

### Classification

```python
@dataclass
class Classification:
    document_type: str
    confidence: float
    identifiers: Dict[str, str]  # e.g., {"patient_name": "John Doe"}
    raw_response: dict
```

### HealthStatus

```python
@dataclass
class HealthStatus:
    is_healthy: bool
    watch_directory_accessible: bool
    config_valid: bool
    last_check_time: datetime
    consecutive_failures: int
    details: Dict[str, Any]
```

### ErrorType

```python
class ErrorType(Enum):
    TRANSIENT = "transient"
    PERMANENT = "permanent"
    CRITICAL = "critical"
    FATAL = "fatal"
```


## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### File Detection and Monitoring Properties

**Property 1: File detection timeliness**
*For any* file with the configured File Prefix created in the Watch Directory, the System should detect the file within 5 seconds
**Validates: Requirements 1.1**

**Property 2: File stability waiting**
*For any* file being written to disk, the System should wait until the file size remains unchanged for 2 seconds before processing
**Validates: Requirements 1.2, 14.3**

**Property 3: Multiple file queueing**
*For any* set of files detected simultaneously, all files should be added to the processing queue
**Validates: Requirements 1.3**

**Property 4: Idle CPU usage**
*For any* idle monitoring period, CPU usage should remain below 5%
**Validates: Requirements 1.5**

**Property 5: Configurable prefix detection**
*For any* configured File Prefix value, the System should detect files with that prefix
**Validates: Requirements 1.6**

### PDF Processing Properties

**Property 6: First three pages extraction**
*For any* valid PDF file with at least three pages, the System should successfully extract the first three pages as images
**Validates: Requirements 2.1**

**Property 7: Partial page extraction**
*For any* valid PDF file with fewer than three pages, the System should extract all available pages
**Validates: Requirements 2.4**

**Property 8: Extraction fallback**
*For any* PDF where PyMuPDF extraction fails, the System should attempt extraction using PyPDF2
**Validates: Requirements 9.1, 9.2**

**Property 9: Image optimization**
*For any* extracted page image, the System should optimize the image size before API transmission
**Validates: Requirements 9.3**

**Property 10: Independent page extraction**
*For any* multi-page extraction, each page should be extracted independently so single page failures don't block the entire process
**Validates: Requirements 9.6**

### AI Classification Properties

**Property 11: Multiple images to API transmission**
*For any* set of extracted images, the System should send all images to OpenAI API for classification
**Validates: Requirements 2.2**

**Property 12: Response parsing**
*For any* valid OpenAI classification response, the System should successfully parse the document type
**Validates: Requirements 2.3**

**Property 13: Response validation**
*For any* classification response received, the System should validate the response format before processing
**Validates: Requirements 2.6**

**Property 14: Document type support**
*For any* document matching a supported type, the System should return the standardized document type name
**Validates: Requirements 16.1-16.15, 16.17**

**Property 15: Comprehensive prompt inclusion**
*For any* classification request, the System should include all supported document types in the AI prompt
**Validates: Requirements 16.16**

### File Renaming Properties

**Property 16: Filename structure**
*For any* classified document, the renamed file should contain the date, document type, and relevant identifiers
**Validates: Requirements 3.1**

**Property 17: Conflict resolution**
*For any* file rename where the target name already exists, the System should append a unique suffix to prevent overwriting
**Validates: Requirements 3.2**

**Property 18: File verification before cleanup**
*For any* renamed file, the System should verify the file is accessible before deleting temporary files
**Validates: Requirements 3.5, 14.5**

### Service Lifecycle Properties

**Property 19: Graceful shutdown timing**
*For any* service stop request, the System should complete shutdown within 30 seconds
**Validates: Requirements 4.3**

**Property 20: Service start logging**
*For any* service start event, the System should write an entry to Windows Event Log
**Validates: Requirements 4.4, 7.5**

**Property 21: Critical error logging**
*For any* critical error encountered, the System should write an entry to Windows Event Log before stopping
**Validates: Requirements 4.5, 7.3**

### Error Handling Properties

**Property 22: Transient error retry**
*For any* transient error, the System should retry the operation with exponential backoff up to 3 attempts
**Validates: Requirements 6.1, 14.1**

**Property 23: Permanent error handling**
*For any* permanent error, the System should skip the file and log the error without retrying
**Validates: Requirements 6.2**

**Property 24: Error isolation**
*For any* file processing error, the System should continue processing other files in the queue
**Validates: Requirements 6.4**

**Property 25: Error context logging**
*For any* error logged, the log entry should include file path, error type, and correlation ID
**Validates: Requirements 6.5**

**Property 26: Sharing violation classification**
*For any* file operation that fails with a sharing violation, the System should classify it as a transient error
**Validates: Requirements 14.4**

### Logging Properties

**Property 27: Structured JSON logging**
*For any* system operation, the System should write a structured JSON log entry to the log file
**Validates: Requirements 7.1**

**Property 28: Log rotation**
*For any* log file that reaches 10MB, the System should rotate the file and maintain 5 backup files
**Validates: Requirements 7.2**

**Property 29: Success logging completeness**
*For any* successfully processed file, the log entry should include processing time, file size, and document type
**Validates: Requirements 7.4, 15.1**

### Configuration Properties

**Property 30: API key encryption**
*For any* API key stored in the configuration file, the key should be encrypted using Windows DPAPI
**Validates: Requirements 8.1**

**Property 31: Configuration validation**
*For any* configuration file loaded, the System should validate all required fields are present
**Validates: Requirements 8.2**

**Property 32: Configuration hot-reload**
*For any* configuration update, the System should reload the configuration without requiring a service restart
**Validates: Requirements 8.4**

### API Management Properties

**Property 33: Rate limit handling**
*For any* OpenAI API rate limit error, the System should wait the specified retry-after duration before retrying
**Validates: Requirements 12.1**

**Property 34: Sequential processing**
*For any* queue of multiple files, the System should process them sequentially to avoid parallel API calls
**Validates: Requirements 12.2**

**Property 35: Timeout handling**
*For any* API call that times out after 30 seconds, the System should log the timeout and retry according to the retry policy
**Validates: Requirements 12.3**

**Property 36: TLS security**
*For any* API call made, the System should use HTTPS with TLS 1.2 or higher
**Validates: Requirements 12.4**

### Resource Cleanup Properties

**Property 37: Temporary file cleanup**
*For any* document processing (successful or failed), the System should delete all temporary files after completion
**Validates: Requirements 13.1, 13.2**

**Property 38: Deletion verification**
*For any* temporary file deletion operation, the System should verify the deletion was successful
**Validates: Requirements 13.4**

### Health Check Properties

**Property 39: Health check interval**
*For any* 60-second period while the System is running, a health check should be performed
**Validates: Requirements 10.1**

**Property 40: Health check completeness**
*For any* health check performed, the System should verify both Watch Directory accessibility and Configuration File validity
**Validates: Requirements 10.2, 10.3**

**Property 41: Health check failure logging**
*For any* failed health check, the System should log a warning with details about the failure
**Validates: Requirements 10.4**

### Performance Metrics Properties

**Property 42: API latency logging**
*For any* API call made, the System should log the response latency
**Validates: Requirements 15.2**

**Property 43: Memory usage logging**
*For any* health check performed, the System should log current memory usage
**Validates: Requirements 15.3**

**Property 44: Average processing time calculation**
*For any* hour of operation, the System should calculate and log the average processing time per file
**Validates: Requirements 15.4**

**Property 45: Error rate calculation**
*For any* set of processed files, the System should calculate and log the error rate as a percentage
**Validates: Requirements 15.5**

## Error Handling

### Error Classification Strategy

The system categorizes all errors into four types to determine appropriate handling:

1. **Transient Errors** (Retry with backoff)
   - Network timeouts
   - API rate limits (429 status)
   - File locked by another process (sharing violation)
   - Temporary disk full
   - Temporary network unavailability

2. **Permanent Errors** (Skip and log)
   - Invalid API key (401 status)
   - Corrupted PDF (cannot be parsed)
   - Unsupported file format
   - Permission denied (access denied)
   - Invalid file path

3. **Critical Errors** (Alert and continue)
   - Watch directory disappeared
   - Disk full (persistent)
   - OpenAI API down (circuit breaker opens)
   - Configuration file corrupted

4. **Fatal Errors** (Stop service)
   - Unable to write logs
   - Out of memory
   - Unable to load configuration
   - Service account permissions revoked

### Retry Mechanism

**Exponential Backoff Configuration**:
- Maximum attempts: 3
- Initial delay: 1.0 seconds
- Exponential base: 2.0
- Maximum delay: 60.0 seconds
- Jitter: Random 0-500ms added to each delay

**Retry Calculation**:
```
delay = min(initial_delay * (exponential_base ^ attempt), max_delay) + random(0, 500ms)
```

**Example Retry Sequence**:
- Attempt 1: 1.0s + jitter
- Attempt 2: 2.0s + jitter
- Attempt 3: 4.0s + jitter

### Circuit Breaker Pattern

**Purpose**: Prevent cascading failures when external services (OpenAI API) are unavailable

**Configuration**:
- Failure threshold: 5 failures within 60 seconds
- Open duration: 5 minutes
- Half-open test: Allow 1 request after timeout

**States**:
1. **Closed**: Normal operation, all requests pass through
2. **Open**: Service is failing, all requests fail fast without calling API
3. **Half-Open**: Testing if service recovered, allow 1 test request

**Behavior**:
- When in Open state, return cached error response immediately
- Log circuit breaker state changes to Windows Event Log
- Reset failure count after successful request in Half-Open state

### Recovery Strategies

**File Processing Failures**:
1. Classify error type
2. If transient, retry with backoff
3. If permanent, move to error directory (optional) or skip
4. Log detailed error information
5. Continue processing next file

**API Failures**:
1. Check circuit breaker state
2. If open, fail fast
3. If closed, attempt request
4. On failure, increment circuit breaker counter
5. Apply retry logic for transient errors

**Configuration Failures**:
1. Attempt to reload from backup
2. If backup invalid, use last known good configuration
3. If no valid configuration, stop service with fatal error
4. Log to Windows Event Log

**Watch Directory Failures**:
1. Log critical error
2. Attempt to reconnect every 60 seconds
3. Continue service operation (health checks will detect issue)
4. Resume monitoring when directory becomes available

## Testing Strategy

### Testing Approach

The system uses a dual testing approach combining unit tests and property-based tests to ensure comprehensive coverage:

- **Unit tests** verify specific examples, edge cases, and error conditions
- **Property-based tests** verify universal properties that should hold across all inputs
- Together they provide comprehensive coverage: unit tests catch concrete bugs, property tests verify general correctness

### Property-Based Testing

**Framework**: Hypothesis (Python property-based testing library)

**Configuration**:
- Minimum iterations per property: 100
- Maximum examples: 1000
- Deadline per test: 60 seconds
- Shrinking enabled for minimal failing examples

**Property Test Requirements**:
- Each property-based test MUST be tagged with a comment referencing the correctness property
- Tag format: `# Feature: scanner-watcher2, Property {number}: {property_text}`
- Each correctness property MUST be implemented by a SINGLE property-based test
- Tests should use smart generators that constrain to valid input spaces

**Example Property Test Structure**:
```python
from hypothesis import given, strategies as st

# Feature: scanner-watcher2, Property 1: File detection timeliness
@given(filename=st.text(min_size=1).map(lambda s: f"SCAN-{s}.pdf"))
def test_file_detection_timeliness(filename, watch_directory):
    """For any file with SCAN- prefix, system detects within 5 seconds"""
    file_path = watch_directory / filename
    start_time = time.time()
    
    # Create file
    file_path.write_text("test content")
    
    # Wait for detection
    detected = wait_for_detection(file_path, timeout=5)
    elapsed = time.time() - start_time
    
    assert detected, f"File {filename} not detected"
    assert elapsed <= 5.0, f"Detection took {elapsed}s, expected ≤5s"
```

### Unit Testing

**Framework**: pytest with pytest-mock

**Coverage Goals**:
- Overall code coverage: >90%
- Critical paths: 100%
- Error handling paths: >95%

**Unit Test Categories**:

1. **Component Tests**: Test individual components in isolation
   - PDF Processor: extraction, optimization, error handling
   - AI Service: API calls, response parsing, error handling
   - File Manager: renaming, conflict resolution, cleanup
   - Configuration Manager: loading, validation, encryption

2. **Integration Tests**: Test component interactions
   - File processing workflow: detection → extraction → classification → renaming
   - Error recovery: retry logic, circuit breaker, error propagation
   - Service lifecycle: startup → monitoring → shutdown

3. **Windows-Specific Tests**: Test Windows integration
   - Service installation and removal
   - Windows path handling (long paths, UNC paths, network drives)
   - Windows Event Log integration
   - DPAPI encryption/decryption

4. **Edge Case Tests**: Test boundary conditions
   - Empty PDFs (no pages)
   - Corrupted PDFs
   - Very large files (>100MB)
   - Invalid configuration
   - Locked files
   - Network drive disconnection

### Test Fixtures and Mocking

**Mocking Strategy**:
- Mock only external APIs (OpenAI)
- Use real filesystem operations with temporary directories
- Use real PDF files for testing (sample fixtures)
- Mock Windows Event Log for unit tests (use real for integration tests)

**Test Fixtures**:
```
tests/fixtures/
├── pdfs/
│   ├── valid_single_page.pdf
│   ├── valid_multi_page.pdf
│   ├── corrupted.pdf
│   ├── empty.pdf
│   └── large_file.pdf
├── configs/
│   ├── valid_config.json
│   ├── invalid_config.json
│   └── minimal_config.json
└── mock_responses/
    ├── openai_success.json
    ├── openai_rate_limit.json
    └── openai_error.json
```

### Test Execution

**Local Development**:
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=scanner_watcher2 --cov-report=html

# Run only property tests
pytest -m property

# Run only unit tests
pytest -m unit

# Run Windows-specific tests (Windows only)
pytest -m windows
```

**CI/CD Pipeline**:
1. Run unit tests on every commit
2. Run integration tests on pull requests
3. Run full test suite including Windows tests on Windows agents
4. Generate coverage reports
5. Fail build if coverage drops below 90%

### Performance Testing

**Metrics to Monitor**:
- File detection latency (target: <5 seconds)
- Processing time per file (target: <30 seconds average)
- Memory usage (target: <200MB idle, <500MB processing)
- CPU usage (target: <5% idle, <25% processing)

**Load Testing**:
- Process 100 files sequentially
- Monitor resource usage throughout
- Verify no memory leaks
- Verify error handling under load

