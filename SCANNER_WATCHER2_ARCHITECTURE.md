# Scanner-Watcher2 Architecture Document
## Windows-First Legal Document Processing System

**Version:** 2.0  
**Date:** December 12, 2024  
**Status:** Architecture Design

---

## Executive Summary

Scanner-Watcher2 is a complete redesign of the legal document processing system with **Windows installability as the primary requirement**. This system monitors directories for scanned documents, uses AI to classify them, and organizes files intelligently.

### Key Design Principles
1. **Windows-First**: Native Windows service, standard Windows paths, single-click installer
2. **Zero-Dependency Installation**: Bundled Python runtime, no prerequisites
3. **Production-Ready**: Proper error handling, logging, recovery mechanisms
4. **Maintainable**: Clean architecture, comprehensive testing, clear separation of concerns

---

## Lessons Learned from Scanner-Watcher v1

### What Worked Well ✅
- **Core Processing Logic**: AI classification, PDF extraction, file management
- **Error Handling**: Comprehensive error recovery and retry mechanisms
- **Testing Strategy**: Good test coverage with unit and integration tests
- **Configuration Management**: Environment-based config with validation
- **Logging**: Detailed logging for debugging and monitoring

### What Needs Improvement ❌
- **Platform Support**: Too Unix/Linux focused (systemd, shell scripts)
- **Deployment**: Complex multi-step installation process
- **Service Management**: Manual daemon management instead of native services
- **Distribution**: Requires Python installation on target machine
- **Documentation**: Scattered across multiple files

### Reference Implementation Paths
```
Current Project Root: /Users/artgrig0/workspace/scanner-watcher

Reusable Components:
├── /Users/artgrig0/workspace/scanner-watcher/legal_document_processor/services/ai_service.py
├── /Users/artgrig0/workspace/scanner-watcher/legal_document_processor/services/pdf_processor.py
├── /Users/artgrig0/workspace/scanner-watcher/legal_document_processor/services/file_processor.py
├── /Users/artgrig0/workspace/scanner-watcher/legal_document_processor/services/directory_watcher.py
├── /Users/artgrig0/workspace/scanner-watcher/legal_document_processor/utils/file_manager.py
├── /Users/artgrig0/workspace/scanner-watcher/legal_document_processor/utils/file_validator.py
├── /Users/artgrig0/workspace/scanner-watcher/legal_document_processor/utils/error_handler.py
├── /Users/artgrig0/workspace/scanner-watcher/legal_document_processor/utils/logger.py
├── /Users/artgrig0/workspace/scanner-watcher/legal_document_processor/config/config.py
└── /Users/artgrig0/workspace/scanner-watcher/legal_document_processor/models/data_models.py

Test References:
├── /Users/artgrig0/workspace/scanner-watcher/tests/test_ai_service.py
├── /Users/artgrig0/workspace/scanner-watcher/tests/test_pdf_processor.py
├── /Users/artgrig0/workspace/scanner-watcher/tests/test_file_processor_integration.py
├── /Users/artgrig0/workspace/scanner-watcher/tests/test_directory_watcher.py
├── /Users/artgrig0/workspace/scanner-watcher/tests/test_complete_workflow_integration.py
└── /Users/artgrig0/workspace/scanner-watcher/tests/test_error_scenarios.py
```

---

## System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Windows Service Layer                     │
│  (Native Windows Service via pywin32 or NSSM wrapper)       │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│                  Application Core                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Service    │  │  Directory   │  │    File      │     │
│  │  Orchestrator│──│   Watcher    │──│  Processor   │     │
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

### Component Responsibilities

#### 1. Windows Service Layer
**Purpose**: Native Windows service integration  
**Technology**: `pywin32` (win32serviceutil) or NSSM wrapper  
**Responsibilities**:
- Start/stop/restart service via Windows Services Manager
- Run on system startup
- Handle service lifecycle events
- Integrate with Windows Event Log
- Manage service status reporting

#### 2. Service Orchestrator
**Purpose**: Main application coordinator  
**Reference**: `/Users/artgrig0/workspace/scanner-watcher/legal_document_processor/services/daemon_service.py`  
**Responsibilities**:
- Initialize all components
- Coordinate component lifecycle
- Handle graceful shutdown
- Manage component health checks
- Coordinate error recovery

#### 3. Directory Watcher
**Purpose**: Monitor filesystem for new files  
**Reference**: `/Users/artgrig0/workspace/scanner-watcher/legal_document_processor/services/directory_watcher.py`  
**Technology**: `watchdog` library (uses Windows ReadDirectoryChangesW)  
**Responsibilities**:
- Watch configured directories
- Detect files with "SCAN-" prefix
- Debounce file events (handle file still being written)
- Queue files for processing
- Handle network drive monitoring

#### 4. File Processor
**Purpose**: Coordinate document processing workflow  
**Reference**: `/Users/artgrig0/workspace/scanner-watcher/legal_document_processor/services/file_processor.py`  
**Responsibilities**:
- Validate file type and accessibility
- Coordinate PDF extraction
- Request AI classification
- Coordinate file renaming
- Clean up temporary files
- Handle processing errors

#### 5. PDF Processor
**Purpose**: Extract pages from PDF documents  
**Reference**: `/Users/artgrig0/workspace/scanner-watcher/legal_document_processor/services/pdf_processor.py`  
**Technology**: PyMuPDF (fitz) - primary, PyPDF2 - fallback  
**Responsibilities**:
- Extract first page as image
- Handle corrupted PDFs
- Support various PDF formats
- Optimize image for AI processing
- Memory-efficient processing

#### 6. AI Service
**Purpose**: Classify documents using OpenAI  
**Reference**: `/Users/artgrig0/workspace/scanner-watcher/legal_document_processor/services/ai_service.py`  
**Technology**: OpenAI API (GPT-4 Vision)  
**Responsibilities**:
- Send document images to OpenAI
- Parse classification results
- Handle API errors and rate limits
- Retry failed requests
- Cache results (optional)

#### 7. File Manager
**Purpose**: Handle file operations  
**Reference**: `/Users/artgrig0/workspace/scanner-watcher/legal_document_processor/utils/file_manager.py`  
**Responsibilities**:
- Rename files based on classification
- Handle file conflicts (duplicate names)
- Manage temporary files
- Ensure atomic file operations
- Handle Windows file locking

#### 8. Configuration Management
**Purpose**: Application configuration  
**Reference**: `/Users/artgrig0/workspace/scanner-watcher/legal_document_processor/config/config.py`  
**Storage**: 
- Primary: `%APPDATA%\ScannerWatcher2\config.json`
- Fallback: Environment variables
- Service: Windows Registry (optional)
**Responsibilities**:
- Load and validate configuration
- Provide defaults
- Support configuration updates
- Validate paths and credentials

#### 9. Logging System
**Purpose**: Application logging  
**Reference**: `/Users/artgrig0/workspace/scanner-watcher/legal_document_processor/utils/logger.py`  
**Storage**: `%APPDATA%\ScannerWatcher2\logs\`  
**Responsibilities**:
- Structured logging (JSON format)
- Log rotation (size and time-based)
- Windows Event Log integration
- Performance metrics logging
- Error tracking

#### 10. Error Handler
**Purpose**: Centralized error handling  
**Reference**: `/Users/artgrig0/workspace/scanner-watcher/legal_document_processor/utils/error_handler.py`  
**Responsibilities**:
- Retry logic with exponential backoff
- Error categorization
- Recovery strategies
- Error reporting
- Circuit breaker pattern

---

## Technology Stack

### Core Technologies

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| **Language** | Python 3.12+ | Mature ecosystem, good Windows support, easy AI integration |
| **Service Management** | pywin32 | Native Windows service integration |
| **File Watching** | watchdog | Cross-platform, uses native Windows APIs |
| **PDF Processing** | PyMuPDF (fitz) | Fast, reliable, good Windows support |
| **AI Integration** | OpenAI Python SDK | Official SDK, well-maintained |
| **Image Processing** | Pillow | Standard Python imaging library |
| **Configuration** | JSON + pydantic | Type-safe, easy to validate |
| **Logging** | Python logging + structlog | Structured logging, Windows Event Log support |

### Windows-Specific Technologies

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Service Wrapper** | pywin32 (win32serviceutil) | Native Windows service |
| **Installer** | Inno Setup | Professional Windows installer |
| **Executable Bundling** | PyInstaller | Single-file executable with embedded Python |
| **Event Logging** | win32evtlog | Windows Event Log integration |
| **Registry Access** | winreg | Optional config storage |

### Development Tools

| Tool | Purpose |
|------|---------|
| **pytest** | Testing framework |
| **pytest-mock** | Mocking for tests |
| **black** | Code formatting |
| **mypy** | Type checking |
| **ruff** | Fast linting |

---

## Windows Installation Strategy

### Distribution Package Structure

```
ScannerWatcher2-Setup.exe (Inno Setup Installer)
│
└── Extracts to: C:\Program Files\ScannerWatcher2\
    ├── scanner_watcher2.exe          # PyInstaller bundle (includes Python)
    ├── config_template.json          # Default configuration
    ├── LICENSE.txt
    ├── README.txt
    └── unins000.exe                  # Uninstaller
```

### Installation Flow

1. **User runs installer** (`ScannerWatcher2-Setup.exe`)
2. **Installer actions**:
   - Extract files to `C:\Program Files\ScannerWatcher2\`
   - Create `%APPDATA%\ScannerWatcher2\` directory
   - Copy default config to `%APPDATA%\ScannerWatcher2\config.json`
   - Register Windows service
   - Create Start Menu shortcuts
   - Add to Windows Programs list
3. **Configuration wizard** (optional GUI or CLI):
   - Set watch directory
   - Enter OpenAI API key
   - Configure logging level
4. **Service starts automatically**

### Build Process

```bash
# 1. Build executable with PyInstaller
pyinstaller --onefile --windowed --name scanner_watcher2 \
    --add-data "config_template.json;." \
    --hidden-import win32timezone \
    src/main.py

# 2. Create installer with Inno Setup
iscc windows/installer.iss

# Output: ScannerWatcher2-Setup.exe
```

### Service Installation

```python
# Automatic during installer
# Or manual via command line:
scanner_watcher2.exe --install-service
scanner_watcher2.exe --start-service
scanner_watcher2.exe --stop-service
scanner_watcher2.exe --remove-service
```

---

## File System Layout

### Windows Paths

```
Installation:
C:\Program Files\ScannerWatcher2\
├── scanner_watcher2.exe
├── config_template.json
└── README.txt

User Data:
%APPDATA%\ScannerWatcher2\
├── config.json                    # User configuration
├── logs\
│   ├── scanner_watcher2.log      # Application logs
│   ├── scanner_watcher2.log.1    # Rotated logs
│   └── error.log                 # Error-only logs
└── temp\                         # Temporary processing files

Watch Directory (User Configured):
D:\Scans\                         # Example
├── SCAN-document1.pdf            # Files to process
└── SCAN-document2.pdf

Processed Files (Same Directory):
D:\Scans\
├── 2024-12-12_MedicalReport_JohnDoe.pdf
└── 2024-12-12_CourtOrder_JaneSmith.pdf
```

### Cross-Platform Path Handling

```python
# Use pathlib for all path operations
from pathlib import Path
import os

# Application data directory
if os.name == 'nt':  # Windows
    app_data = Path(os.environ['APPDATA']) / 'ScannerWatcher2'
else:  # macOS/Linux
    app_data = Path.home() / '.scanner_watcher2'

# Always use forward slashes in code, pathlib handles conversion
config_path = app_data / 'config.json'
log_path = app_data / 'logs' / 'app.log'
```

---

## Configuration Management

### Configuration File Format

**Location**: `%APPDATA%\ScannerWatcher2\config.json`

```json
{
  "version": "2.0",
  "watch_directory": "D:\\Scans",
  "openai_api_key": "sk-...",
  "log_level": "INFO",
  "processing": {
    "file_prefix": "SCAN-",
    "retry_attempts": 3,
    "retry_delay_seconds": 5,
    "temp_directory": null
  },
  "ai": {
    "model": "gpt-4-vision-preview",
    "max_tokens": 500,
    "temperature": 0.1,
    "timeout_seconds": 30
  },
  "logging": {
    "max_file_size_mb": 10,
    "backup_count": 5,
    "log_to_event_log": true
  },
  "service": {
    "health_check_interval_seconds": 60,
    "graceful_shutdown_timeout_seconds": 30
  }
}
```

### Configuration Validation

```python
from pydantic import BaseModel, Field, validator
from pathlib import Path

class ProcessingConfig(BaseModel):
    file_prefix: str = "SCAN-"
    retry_attempts: int = Field(ge=1, le=10, default=3)
    retry_delay_seconds: int = Field(ge=1, le=60, default=5)
    temp_directory: Optional[Path] = None

class Config(BaseModel):
    version: str
    watch_directory: Path
    openai_api_key: str
    log_level: str = "INFO"
    processing: ProcessingConfig
    # ... other sections

    @validator('watch_directory')
    def validate_watch_directory(cls, v):
        if not v.exists():
            raise ValueError(f"Watch directory does not exist: {v}")
        if not v.is_dir():
            raise ValueError(f"Watch directory is not a directory: {v}")
        return v
```

---

## Error Handling Strategy

### Error Categories

1. **Transient Errors** (Retry)
   - Network timeouts
   - API rate limits
   - File locked by another process
   - Temporary disk full

2. **Permanent Errors** (Skip and Log)
   - Invalid API key
   - Corrupted PDF
   - Unsupported file format
   - Permission denied

3. **Critical Errors** (Alert and Continue)
   - Watch directory disappeared
   - Disk full
   - OpenAI API down

4. **Fatal Errors** (Stop Service)
   - Configuration file corrupted
   - Unable to write logs
   - Out of memory

### Retry Strategy

**Reference**: `/Users/artgrig0/workspace/scanner-watcher/legal_document_processor/utils/error_handler.py`

```python
class RetryConfig:
    max_attempts: int = 3
    initial_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True

# Exponential backoff with jitter
# Attempt 1: 1s + jitter
# Attempt 2: 2s + jitter
# Attempt 3: 4s + jitter
```

### Circuit Breaker Pattern

```python
# If OpenAI API fails 5 times in 60 seconds, open circuit
# Wait 5 minutes before trying again
# Prevents hammering failed services
```

---

## Logging Strategy

### Log Levels

- **DEBUG**: Detailed diagnostic information
- **INFO**: General informational messages (file processed, service started)
- **WARNING**: Warning messages (retry attempt, slow processing)
- **ERROR**: Error messages (processing failed, API error)
- **CRITICAL**: Critical errors (service stopping, configuration invalid)

### Log Destinations

1. **File Logs**: `%APPDATA%\ScannerWatcher2\logs\scanner_watcher2.log`
   - Rotated at 10MB
   - Keep 5 backup files
   - JSON format for structured logging

2. **Windows Event Log**: Application log
   - Service start/stop events
   - Critical errors
   - Configuration changes

3. **Console**: During development and manual runs
   - Human-readable format
   - Color-coded by level

### Log Format

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

---

## Testing Strategy

### Test Categories

**Reference Tests**: `/Users/artgrig0/workspace/scanner-watcher/tests/`

1. **Unit Tests** (Fast, Isolated)
   - Test individual components
   - Mock external dependencies
   - Reference: `test_ai_service.py`, `test_pdf_processor.py`

2. **Integration Tests** (Medium, Real Dependencies)
   - Test component interactions
   - Use real file system
   - Mock only external APIs
   - Reference: `test_file_processor_integration.py`, `test_complete_workflow_integration.py`

3. **End-to-End Tests** (Slow, Full System)
   - Test complete workflows
   - Real files, real processing
   - Mock only OpenAI API
   - Reference: `test_complete_workflow_integration.py`

4. **Windows-Specific Tests**
   - Service installation/removal
   - Windows path handling
   - Event log integration
   - Long path support (>260 characters)

### Test Structure

```
tests/
├── unit/
│   ├── test_ai_service.py
│   ├── test_pdf_processor.py
│   ├── test_file_manager.py
│   └── test_config.py
├── integration/
│   ├── test_file_processing_workflow.py
│   ├── test_directory_watcher.py
│   └── test_error_recovery.py
├── e2e/
│   └── test_complete_workflow.py
├── windows/
│   ├── test_service_installation.py
│   ├── test_windows_paths.py
│   └── test_event_log.py
└── fixtures/
    ├── sample_pdfs/
    └── mock_responses/
```

### Test Coverage Goals

- **Unit Tests**: >90% coverage
- **Integration Tests**: All critical paths
- **E2E Tests**: Happy path + major error scenarios
- **Windows Tests**: All Windows-specific features

---

## Security Considerations

### API Key Management

1. **Storage**: Encrypted in config file (Windows DPAPI)
2. **Access**: Only service account can read
3. **Transmission**: HTTPS only
4. **Rotation**: Support key rotation without service restart

### File System Security

1. **Permissions**: Service runs as LocalSystem or dedicated service account
2. **Validation**: Validate all file paths (prevent directory traversal)
3. **Sandboxing**: Process files in isolated temp directory
4. **Cleanup**: Securely delete temporary files

### Network Security

1. **TLS**: All API calls use TLS 1.2+
2. **Timeouts**: Prevent hanging connections
3. **Rate Limiting**: Respect OpenAI rate limits
4. **Proxy Support**: Support corporate proxies

---

## Performance Considerations

### Resource Limits

- **Memory**: Target <200MB idle, <500MB processing
- **CPU**: Target <5% idle, <25% processing
- **Disk I/O**: Minimize reads/writes, use buffering
- **Network**: Batch API calls when possible

### Optimization Strategies

1. **Lazy Loading**: Load components only when needed
2. **Connection Pooling**: Reuse HTTP connections
3. **Image Optimization**: Compress images before sending to API
4. **Async Processing**: Process multiple files concurrently (with limits)
5. **Caching**: Cache AI responses for identical documents (optional)

### Monitoring Metrics

- Files processed per hour
- Average processing time
- Error rate
- API call latency
- Memory usage
- Disk space available

---

## Deployment Checklist

### Pre-Build

- [ ] All tests passing
- [ ] Version number updated
- [ ] CHANGELOG updated
- [ ] Documentation updated

### Build

- [ ] PyInstaller build successful
- [ ] Executable runs on clean Windows machine
- [ ] All dependencies bundled
- [ ] File size reasonable (<100MB)

### Installer

- [ ] Inno Setup script configured
- [ ] Installer creates all directories
- [ ] Service registers correctly
- [ ] Uninstaller removes all files
- [ ] Start Menu shortcuts work

### Testing

- [ ] Install on Windows 10
- [ ] Install on Windows 11
- [ ] Install on Windows Server 2019+
- [ ] Service starts automatically
- [ ] Configuration wizard works
- [ ] Process test document successfully
- [ ] Logs written correctly
- [ ] Uninstall removes everything

### Release

- [ ] Create GitHub release
- [ ] Upload installer
- [ ] Update documentation
- [ ] Notify users

---

## Migration Path from v1

### For Developers

1. **Copy reusable components** from reference paths
2. **Adapt for Windows**: Remove Unix-specific code
3. **Add Windows service wrapper**
4. **Update configuration** to use Windows paths
5. **Add PyInstaller spec**
6. **Create Inno Setup script**
7. **Update tests** for Windows

### For Users

1. **Export configuration** from v1
2. **Uninstall v1** (if applicable)
3. **Install v2** using new installer
4. **Import configuration** via wizard
5. **Verify service** is running
6. **Test with sample document**

---

## Future Enhancements

### Phase 2 (Post-Launch)

- [ ] Configuration GUI (Windows Forms or web-based)
- [ ] System tray icon with status
- [ ] Email notifications for errors
- [ ] Support for multiple watch directories
- [ ] Document preview before processing
- [ ] Batch processing mode
- [ ] Performance dashboard

### Phase 3 (Advanced)

- [ ] OCR for scanned images (not just PDFs)
- [ ] Custom classification rules
- [ ] Integration with document management systems
- [ ] Multi-language support
- [ ] Cloud backup integration
- [ ] Mobile app for monitoring

---

## Appendix A: Windows Service Implementation

### Service Entry Point

```python
import win32serviceutil
import win32service
import win32event
import servicemanager

class ScannerWatcher2Service(win32serviceutil.ServiceFramework):
    _svc_name_ = "ScannerWatcher2"
    _svc_display_name_ = "Scanner Watcher 2"
    _svc_description_ = "Monitors directories and processes legal documents with AI"

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.stop_event = win32event.CreateEvent(None, 0, 0, None)
        self.is_running = True

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.stop_event)
        self.is_running = False

    def SvcDoRun(self):
        servicemanager.LogMsg(
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            servicemanager.PYS_SERVICE_STARTED,
            (self._svc_name_, '')
        )
        self.main()

    def main(self):
        # Initialize and run application
        from scanner_watcher2.core import Application
        app = Application()
        app.run(stop_event=self.stop_event)

if __name__ == '__main__':
    win32serviceutil.HandleCommandLine(ScannerWatcher2Service)
```

---

## Appendix B: PyInstaller Spec

```python
# scanner_watcher2.spec
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['src/main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('config_template.json', '.'),
        ('README.txt', '.'),
    ],
    hiddenimports=[
        'win32timezone',
        'win32service',
        'win32serviceutil',
        'win32event',
        'servicemanager',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='scanner_watcher2',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # No console window
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='windows/icon.ico',
)
```

---

## Appendix C: Inno Setup Script

```ini
; scanner_watcher2.iss
[Setup]
AppName=Scanner Watcher 2
AppVersion=2.0.0
AppPublisher=Your Company
DefaultDirName={pf}\ScannerWatcher2
DefaultGroupName=Scanner Watcher 2
OutputDir=dist
OutputBaseFilename=ScannerWatcher2-Setup
Compression=lzma2
SolidCompression=yes
PrivilegesRequired=admin
UninstallDisplayIcon={app}\scanner_watcher2.exe

[Files]
Source: "dist\scanner_watcher2.exe"; DestDir: "{app}"
Source: "config_template.json"; DestDir: "{app}"
Source: "README.txt"; DestDir: "{app}"
Source: "LICENSE.txt"; DestDir: "{app}"

[Icons]
Name: "{group}\Scanner Watcher 2 Config"; Filename: "{app}\scanner_watcher2.exe"; Parameters: "--configure"
Name: "{group}\Uninstall Scanner Watcher 2"; Filename: "{uninstallexe}"

[Run]
Filename: "{app}\scanner_watcher2.exe"; Parameters: "--install-service"; StatusMsg: "Installing Windows service..."
Filename: "{app}\scanner_watcher2.exe"; Parameters: "--configure"; Description: "Configure Scanner Watcher 2"; Flags: postinstall nowait skipifsilent

[UninstallRun]
Filename: "{app}\scanner_watcher2.exe"; Parameters: "--stop-service"
Filename: "{app}\scanner_watcher2.exe"; Parameters: "--remove-service"

[Code]
procedure CurStepChanged(CurStep: TSetupStep);
var
  AppDataDir: String;
begin
  if CurStep = ssPostInstall then
  begin
    AppDataDir := ExpandConstant('{userappdata}\ScannerWatcher2');
    if not DirExists(AppDataDir) then
      CreateDir(AppDataDir);
    CreateDir(AppDataDir + '\logs');
    CreateDir(AppDataDir + '\temp');
    FileCopy(ExpandConstant('{app}\config_template.json'), 
             AppDataDir + '\config.json', False);
  end;
end;
```

---

## Document Control

**Author**: Architecture Team  
**Reviewers**: Development Team, Operations Team  
**Approval**: Project Lead  
**Next Review**: After Phase 1 Implementation

**Change History**:
- 2024-12-12: Initial version based on v1 lessons learned
