# Scanner-Watcher2

Windows-native legal document processing system that monitors directories for scanned documents, uses AI to classify them, and organizes files intelligently.

## Features

- **Automatic Document Detection**: Monitors directories for new scanned documents with configurable file prefix (default: "SCAN-")
- **AI-Powered Classification**: Uses OpenAI GPT-4 Vision with flexible three-tier classification system (standard categories, specific types, and OTHER fallback) to handle any legal document
- **Multi-Page Analysis**: Extracts and analyzes up to 3 pages from each document for improved classification accuracy
- **Intelligent File Organization**: Renames files with meaningful names including date, document type, and identifiers
- **Windows Service Integration**: Runs as a native Windows service with automatic startup and lifecycle management
- **Production-Ready**: Comprehensive error handling, retry logic with exponential backoff, and circuit breakers
- **Secure Configuration**: API keys encrypted using Windows DPAPI
- **Comprehensive Logging**: Structured JSON logs with Windows Event Log integration for critical events
- **Zero-Dependency Installation**: Single executable with embedded Python runtime - no prerequisites required

## Requirements

### For End Users
- Windows 10, Windows 11, or Windows Server 2019+
- OpenAI API key (with GPT-4 Vision access)
- Administrator privileges for service installation

### For Developers
- Windows 10, Windows 11, or Windows Server 2019+
- Python 3.12 or higher
- OpenAI API key
- Visual Studio Build Tools (for pywin32 compilation)

## Quick Start

### For End Users

1. **Download and Install**
   - Download `ScannerWatcher2Setup.exe` from the releases page
   - Run the installer with administrator privileges
   - Follow the installation wizard
   - The service will be installed to `C:\Program Files\ScannerWatcher2\`

2. **Configure the Application**
   - Run the configuration wizard from the Start Menu: "Scanner-Watcher2 Configuration"
   - Or run: `scanner_watcher2.exe --configure`
   - Provide:
     - Watch directory path (e.g., `D:\Scans`)
     - OpenAI API key
     - Log level (INFO recommended)

3. **Start the Service**
   - The service starts automatically after installation
   - Or manually: Open Services (services.msc), find "Scanner-Watcher2", and click Start
   - Or from command line: `sc start ScannerWatcher2`

4. **Verify Operation**
   - Place a PDF file with your configured file prefix (default: "SCAN-") in your watch directory
   - Check logs at `%APPDATA%\ScannerWatcher2\logs\scanner_watcher2.log`
   - The file should be renamed within seconds based on its classification

For detailed installation instructions, see [INSTALLER.md](INSTALLER.md).

### For Developers

1. **Clone and Setup**
   ```bash
   git clone <repository-url>
   cd scanner-watcher2
   python -m venv venv
   venv\Scripts\activate
   pip install -e ".[dev]"
   ```

2. **Configure for Development**
   ```bash
   # Create configuration directory
   mkdir %APPDATA%\ScannerWatcher2
   
   # Copy template and edit
   copy config_template.json %APPDATA%\ScannerWatcher2\config.json
   notepad %APPDATA%\ScannerWatcher2\config.json
   ```

3. **Run in Console Mode**
   ```bash
   python -m scanner_watcher2 --console
   ```

For detailed developer setup, see the [Developer Setup Guide](#developer-setup-guide) section below.

## Development

### Project Structure

```
scanner-watcher2/
├── src/
│   └── scanner_watcher2/
│       ├── core/              # Core application components
│       ├── infrastructure/    # Infrastructure layer
│       ├── service/           # Service layer
│       ├── config.py          # Configuration models
│       └── models.py          # Data models
├── tests/
│   ├── unit/                  # Unit tests
│   ├── integration/           # Integration tests
│   ├── property/              # Property-based tests
│   └── fixtures/              # Test fixtures
└── pyproject.toml             # Project configuration
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=scanner_watcher2 --cov-report=html

# Run only unit tests
pytest -m unit

# Run only property tests
pytest -m property

# Run Windows-specific tests
pytest -m windows
```

### Code Quality

```bash
# Format code
black src tests

# Lint code
ruff check src tests

# Type check
mypy src
```

### Building Executable

To build the Windows executable:

```bash
# Install PyInstaller
pip install pyinstaller

# Build using the spec file
pyinstaller scanner_watcher2.spec

# Or use the build script
build.bat
```

The executable will be created in `dist/scanner_watcher2.exe`.

For detailed build instructions, see [BUILD.md](BUILD.md).

For testing the executable, see [TESTING_CHECKLIST.md](TESTING_CHECKLIST.md).

## Configuration

Configuration is stored in `%APPDATA%\ScannerWatcher2\config.json`. The configuration wizard will help you create this file, or you can edit it manually.

### Configuration Options

```json
{
  "version": "1.0.0",
  "watch_directory": "D:\\Scans",
  "openai_api_key": "<encrypted>",
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

### Configuration Fields

#### Core Settings
- **version**: Configuration version (currently "1.0.0")
- **watch_directory**: Directory to monitor for scanned documents (must exist)
- **openai_api_key**: OpenAI API key (automatically encrypted using Windows DPAPI)
- **log_level**: Logging verbosity - DEBUG, INFO, WARNING, ERROR, or CRITICAL

#### Processing Settings
- **file_prefix**: Prefix for files to process (default: "SCAN-"). Files must start with this prefix to be detected and processed. Can be customized to match your scanning workflow (e.g., "DOC-", "LEGAL-")
- **pages_to_extract**: Number of pages to extract from each PDF for AI analysis (1-10, default: 3). More pages provide better classification accuracy but increase API costs
- **retry_attempts**: Number of retry attempts for transient errors (1-10, default: 3)
- **retry_delay_seconds**: Initial delay between retries (1-60 seconds, default: 5)
- **temp_directory**: Custom temporary directory (default: `%APPDATA%\ScannerWatcher2\temp\`)

#### AI Settings
- **model**: OpenAI model to use (default: "gpt-4-vision-preview")
- **max_tokens**: Maximum tokens in API response (default: 500)
- **temperature**: AI creativity level (0.0-1.0, default: 0.1 for consistency)
- **timeout_seconds**: API request timeout (default: 30)

#### Logging Settings
- **max_file_size_mb**: Maximum log file size before rotation (default: 10 MB)
- **backup_count**: Number of rotated log files to keep (default: 5)
- **log_to_event_log**: Write critical events to Windows Event Log (default: true)

#### Service Settings
- **health_check_interval_seconds**: Interval between health checks (default: 60)
- **graceful_shutdown_timeout_seconds**: Maximum time for graceful shutdown (default: 30)

### Supported Document Types

Scanner-Watcher2 uses a flexible three-tier classification system to identify and organize legal documents:

#### Tier 1: Standard Categories (Enum-Based)

The system first attempts to classify documents into high-level standard categories:

- **Medical Report**: QME reports, AME reports, PTP reports, IME reports, medical evaluations
- **Injury Report**: Initial injury reports, incident reports
- **Claim Form**: DWC-1, claim applications
- **Deposition**: Deposition transcripts
- **Expert Witness Report**: Expert opinions, vocational evaluations
- **Settlement Agreement**: Compromise & Release, Stipulations
- **Court Order**: WCAB orders, findings, awards
- **Insurance Correspondence**: Carrier letters, UR decisions, RFAs
- **Wage Statement**: Earnings records, pay stubs
- **Vocational Report**: Vocational rehabilitation reports
- **IME Report**: Independent Medical Examinations
- **Surveillance Report**: Investigation reports
- **Subpoena**: Subpoenas, subpoena duces tecum
- **Motion**: Motions, petitions, DORs
- **Brief**: Legal briefs, memoranda

#### Tier 2: Specific Document Types

If a document doesn't clearly fit a standard category, the AI provides a specific document type name:

- Panel List
- QME Appointment Notification Form
- Declaration of Readiness to Proceed
- Objection to Declaration of Readiness to Proceed
- Finding and Award
- Finding & Order
- And other specific legal document types

#### Tier 3: OTHER Fallback

For documents that cannot be classified, the system returns:
- `OTHER_[Brief Description]` (e.g., "OTHER_Unidentified Medical Form")

This allows the system to handle any document while clearly marking unclassifiable ones.

#### Classification Benefits

- **Flexibility**: Handles documents outside predefined lists
- **Consistency**: Groups similar documents into standard categories
- **Clarity**: Unknown documents clearly marked with OTHER prefix
- **Better Organization**: Files grouped by high-level category for easier sorting

The AI analyzes up to 3 pages from each document to accurately identify the document type, even when documents have similar formatting or content. You can adjust the number of pages analyzed using the `pages_to_extract` configuration option.

### Updating Configuration

The service automatically reloads configuration when the file changes - no restart required. However, changes to `watch_directory` or `file_prefix` require a service restart.

For detailed configuration instructions, see [CONFIGURATION_WIZARD.md](CONFIGURATION_WIZARD.md).

## Troubleshooting

### Service Won't Start

**Symptom**: Service fails to start or stops immediately

**Solutions**:
1. Check Windows Event Log for error messages:
   - Open Event Viewer (eventvwr.msc)
   - Navigate to Windows Logs → Application
   - Look for "Scanner-Watcher2" source entries

2. Verify configuration file exists and is valid:
   ```bash
   type %APPDATA%\ScannerWatcher2\config.json
   ```

3. Check watch directory exists and is accessible:
   - Ensure the path in config.json exists
   - Verify the service account has read/write permissions

4. Review application logs:
   ```bash
   type %APPDATA%\ScannerWatcher2\logs\scanner_watcher2.log
   ```

5. Try running in console mode for detailed output:
   ```bash
   cd "C:\Program Files\ScannerWatcher2"
   scanner_watcher2.exe --console
   ```

### Files Not Being Processed

**Symptom**: Files with configured prefix are not being renamed

**Solutions**:
1. Verify file naming:
   - Files must start with your configured file prefix (default: "SCAN-", case-sensitive)
   - Files must be PDF format
   - Example with default prefix: `SCAN-document.pdf` ✓
   - Example with custom prefix "DOC-": `DOC-document.pdf` ✓

2. Check file stability:
   - System waits 2 seconds for file size to stabilize
   - Ensure file is not locked by another process

3. Review logs for processing errors:
   ```bash
   type %APPDATA%\ScannerWatcher2\logs\scanner_watcher2.log | findstr ERROR
   ```

4. Verify OpenAI API key is valid:
   - Check API key has GPT-4 Vision access
   - Verify API quota is not exceeded

5. Check network connectivity:
   - Ensure system can reach api.openai.com
   - Verify proxy settings if behind corporate firewall

6. Check multi-page extraction:
   - System extracts up to 3 pages by default for analysis
   - For PDFs with fewer pages, all available pages are extracted
   - If extraction fails on any page, check logs for specific errors
   - Large PDFs may take longer to process due to multi-page extraction

### API Rate Limit Errors

**Symptom**: Logs show "Rate limit exceeded" errors

**Solutions**:
1. The system automatically handles rate limits with exponential backoff
2. Processing will resume automatically after the retry-after period
3. Consider upgrading OpenAI API tier for higher rate limits
4. Reduce processing volume during peak times

### High Memory Usage

**Symptom**: Service consumes excessive memory

**Solutions**:
1. Check for very large PDF files (>100MB)
   - Multi-page extraction (default: 3 pages) increases memory usage
   - Consider reducing `pages_to_extract` in config.json for large PDFs
2. Review `temp_directory` for leftover temporary files
3. Adjust pages_to_extract setting:
   ```json
   {
     "processing": {
       "pages_to_extract": 1
     }
   }
   ```
   - Reducing from 3 to 1 page decreases memory usage but may reduce classification accuracy
4. Restart the service to clear memory:
   ```bash
   sc stop ScannerWatcher2
   sc start ScannerWatcher2
   ```

### Configuration Changes Not Taking Effect

**Symptom**: Configuration updates are ignored

**Solutions**:
1. Verify JSON syntax is valid (use a JSON validator)
2. Check file permissions - service must be able to read config.json
3. For `watch_directory` changes, restart the service:
   ```bash
   sc stop ScannerWatcher2
   sc start ScannerWatcher2
   ```

### Network Drive Monitoring Issues

**Symptom**: Files on network drives are not detected

**Solutions**:
1. Ensure network drive is mapped and accessible
2. Use UNC paths instead of mapped drives: `\\server\share\folder`
3. Verify service account has network access permissions
4. Check network drive remains connected (health checks monitor this)

### Permission Denied Errors

**Symptom**: Logs show "Access denied" or "Permission denied"

**Solutions**:
1. Verify service account has permissions:
   - Read/write access to watch directory
   - Read/write access to `%APPDATA%\ScannerWatcher2\`
   - Read access to `C:\Program Files\ScannerWatcher2\`

2. Check file-level permissions on specific PDFs
3. Ensure antivirus is not blocking file operations

### Logs Not Appearing

**Symptom**: No log files in `%APPDATA%\ScannerWatcher2\logs\`

**Solutions**:
1. Verify directory exists and is writable
2. Check service account permissions
3. Review Windows Event Log for startup errors
4. Try running in console mode to see output

### Common Error Messages

| Error Message | Cause | Solution |
|--------------|-------|----------|
| "Watch directory not found" | Configured directory doesn't exist | Create directory or update config.json |
| "Invalid API key" | OpenAI API key is incorrect | Update API key in config.json |
| "Circuit breaker open" | Too many API failures | Wait 5 minutes for automatic recovery |
| "File locked by another process" | PDF is open in another application | Close the file or wait for automatic retry |
| "Corrupted PDF" | PDF file is damaged | Check PDF file integrity |
| "Configuration validation failed" | Invalid config.json | Review config.json syntax and values |

### Getting Help

1. **Check Logs**: Always review logs first at `%APPDATA%\ScannerWatcher2\logs\`
2. **Windows Event Log**: Check for critical errors in Event Viewer
3. **Console Mode**: Run with `--console` flag for detailed output
4. **GitHub Issues**: Open an issue with log excerpts and error messages
5. **Documentation**: Review [CONFIGURATION_WIZARD.md](CONFIGURATION_WIZARD.md) and [INSTALLER.md](INSTALLER.md)

## Developer Setup Guide

### Prerequisites

1. **Python 3.12+**
   ```bash
   python --version  # Should be 3.12 or higher
   ```

2. **Visual Studio Build Tools** (for pywin32)
   - Download from: https://visualstudio.microsoft.com/downloads/
   - Install "Desktop development with C++" workload

3. **Git**
   ```bash
   git --version
   ```

### Initial Setup

1. **Clone Repository**
   ```bash
   git clone <repository-url>
   cd scanner-watcher2
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   # Install package in editable mode with dev dependencies
   pip install -e ".[dev]"
   ```

4. **Verify Installation**
   ```bash
   pytest --version
   black --version
   mypy --version
   ruff --version
   ```

### Development Workflow

1. **Create Configuration**
   ```bash
   # Create config directory
   mkdir %APPDATA%\ScannerWatcher2
   mkdir %APPDATA%\ScannerWatcher2\logs
   mkdir %APPDATA%\ScannerWatcher2\temp
   
   # Copy and edit configuration
   copy config_template.json %APPDATA%\ScannerWatcher2\config.json
   notepad %APPDATA%\ScannerWatcher2\config.json
   ```
   
   Update the configuration with:
   - Valid watch directory path
   - Your OpenAI API key
   - Desired log level (DEBUG for development)

2. **Run in Console Mode**
   ```bash
   python -m scanner_watcher2 --console
   ```

3. **Run Tests**
   ```bash
   # Run all tests
   pytest
   
   # Run with coverage
   pytest --cov=scanner_watcher2 --cov-report=html
   
   # Run specific test categories
   pytest -m unit           # Unit tests only
   pytest -m property       # Property-based tests only
   pytest -m integration    # Integration tests only
   pytest -m windows        # Windows-specific tests only
   
   # Run specific test file
   pytest tests/unit/test_config.py
   
   # Run with verbose output
   pytest -v
   ```

4. **Code Quality Checks**
   ```bash
   # Format code (automatically fixes issues)
   black src tests
   
   # Lint code (reports issues)
   ruff check src tests
   
   # Fix auto-fixable lint issues
   ruff check --fix src tests
   
   # Type check
   mypy src
   ```

5. **Build Executable**
   ```bash
   # Build using spec file
   pyinstaller scanner_watcher2.spec
   
   # Or use build script
   build.bat
   
   # Executable will be in dist/scanner_watcher2.exe
   ```

6. **Build Installer**
   ```bash
   # Requires Inno Setup installed
   build_installer.bat
   
   # Installer will be in Output/ScannerWatcher2Setup.exe
   ```

### Project Structure

```
scanner-watcher2/
├── src/scanner_watcher2/          # Main application package
│   ├── core/                      # Core business logic
│   │   ├── ai_service.py          # OpenAI API integration
│   │   ├── pdf_processor.py      # PDF extraction
│   │   ├── file_processor.py     # Workflow coordinator
│   │   ├── file_manager.py       # File operations
│   │   └── directory_watcher.py  # Filesystem monitoring
│   ├── infrastructure/            # Infrastructure layer
│   │   ├── logger.py              # Structured logging
│   │   ├── config_manager.py     # Configuration management
│   │   └── error_handler.py      # Error handling & retry
│   ├── service/                   # Service layer
│   │   ├── orchestrator.py       # Application coordinator
│   │   └── windows_service.py    # Windows service wrapper
│   ├── config.py                  # Configuration models
│   ├── models.py                  # Data models
│   ├── config_wizard.py           # Interactive configuration
│   └── __main__.py                # Entry point
├── tests/                         # Test suite
│   ├── unit/                      # Unit tests
│   ├── integration/               # Integration tests
│   ├── property/                  # Property-based tests
│   ├── fixtures/                  # Test fixtures
│   └── conftest.py                # Shared fixtures
├── .kiro/                         # Kiro specs
│   └── specs/scanner-watcher2/   # Feature specifications
├── pyproject.toml                 # Project configuration
├── scanner_watcher2.spec          # PyInstaller spec
├── scanner_watcher2.iss           # Inno Setup script
└── README.md                      # This file
```

### Testing Guidelines

1. **Write Tests First**: Follow TDD when adding new features
2. **Test Categories**:
   - Unit tests: Fast, isolated, mocked dependencies
   - Property tests: Hypothesis-based, test universal properties
   - Integration tests: Real filesystem, component interactions
   - Windows tests: Service installation, Event Log, DPAPI

3. **Coverage Goals**:
   - Overall: >90%
   - Critical paths: 100%
   - Error handling: >95%

4. **Running Specific Tests**:
   ```bash
   # Test specific component
   pytest tests/unit/test_config_manager.py
   
   # Test specific function
   pytest tests/unit/test_config_manager.py::test_load_config
   
   # Run tests matching pattern
   pytest -k "test_retry"
   ```

### Debugging

1. **Console Mode**: Run with detailed logging
   ```bash
   python -m scanner_watcher2 --console
   ```

2. **Debug Logging**: Set log level to DEBUG in config.json
   ```json
   {
     "log_level": "DEBUG"
   }
   ```

3. **Python Debugger**: Use pdb for interactive debugging
   ```python
   import pdb; pdb.set_trace()
   ```

4. **VS Code**: Use launch.json configuration
   ```json
   {
     "version": "0.2.0",
     "configurations": [
       {
         "name": "Scanner-Watcher2 Console",
         "type": "python",
         "request": "launch",
         "module": "scanner_watcher2",
         "args": ["--console"],
         "console": "integratedTerminal"
       }
     ]
   }
   ```

### Contributing

1. **Create Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make Changes**
   - Write tests first
   - Implement feature
   - Ensure all tests pass
   - Run code quality checks

3. **Commit Changes**
   ```bash
   git add .
   git commit -m "Add feature: description"
   ```

4. **Push and Create PR**
   ```bash
   git push origin feature/your-feature-name
   ```

### Common Development Tasks

**Add New Configuration Option**:
1. Update `Config` model in `src/scanner_watcher2/config.py`
2. Update `config_template.json`
3. Add validation in `ConfigManager`
4. Update documentation
5. Add tests

**Add New Error Type**:
1. Update `ErrorType` enum in `src/scanner_watcher2/models.py`
2. Update error classification in `ErrorHandler`
3. Add tests for new error handling

**Add New Component**:
1. Create component file in appropriate layer (core/infrastructure/service)
2. Define interface with type hints
3. Implement component logic
4. Add unit tests
5. Add property-based tests
6. Update orchestrator to wire component

### Windows-Specific Development

**Service Testing**:
```bash
# Install service (requires admin)
python -m scanner_watcher2 --install-service

# Start service
python -m scanner_watcher2 --start-service

# Stop service
python -m scanner_watcher2 --stop-service

# Remove service
python -m scanner_watcher2 --remove-service
```

**Event Log Testing**:
- Open Event Viewer (eventvwr.msc)
- Navigate to Windows Logs → Application
- Filter by source: "Scanner-Watcher2"

**DPAPI Testing**:
- API key encryption is user-specific
- Test with different Windows user accounts
- Encrypted keys cannot be decrypted by other users

### Additional Resources

- [BUILD.md](BUILD.md) - Detailed build instructions
- [INSTALLER.md](INSTALLER.md) - Installer creation guide
- [CONFIGURATION_WIZARD.md](CONFIGURATION_WIZARD.md) - Configuration wizard details
- [TESTING_CHECKLIST.md](TESTING_CHECKLIST.md) - Testing procedures
- [.kiro/specs/scanner-watcher2/](/.kiro/specs/scanner-watcher2/) - Feature specifications

## License

MIT License - See LICENSE.txt file for details

## Support

For issues and questions:
- **GitHub Issues**: Open an issue with detailed description and logs
- **Documentation**: Review troubleshooting section above
- **Logs**: Always include relevant log excerpts from `%APPDATA%\ScannerWatcher2\logs\`
