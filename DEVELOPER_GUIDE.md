# Scanner-Watcher2 Developer Guide

Comprehensive guide for developers working on Scanner-Watcher2.

## Table of Contents

- [Getting Started](#getting-started)
- [Architecture Overview](#architecture-overview)
- [Development Workflow](#development-workflow)
- [Testing Strategy](#testing-strategy)
- [Code Style and Standards](#code-style-and-standards)
- [Component Details](#component-details)
- [Building and Packaging](#building-and-packaging)
- [Debugging](#debugging)
- [Contributing](#contributing)

## Getting Started

### Prerequisites

1. **Python 3.12 or Higher**
   ```bash
   python --version  # Must be 3.12+
   ```
   Download from: https://www.python.org/downloads/

2. **Visual Studio Build Tools**
   - Required for compiling pywin32
   - Download: https://visualstudio.microsoft.com/downloads/
   - Install "Desktop development with C++" workload

3. **Git**
   ```bash
   git --version
   ```

4. **Optional Tools**:
   - VS Code with Python extension
   - Windows Terminal
   - Inno Setup (for building installer)

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

3. **Install Development Dependencies**
   ```bash
   pip install -e ".[dev]"
   ```

4. **Verify Installation**
   ```bash
   pytest --version
   black --version
   mypy --version
   ruff --version
   hypothesis --version
   ```

5. **Setup Configuration**
   ```bash
   # Create directories
   mkdir %APPDATA%\ScannerWatcher2
   mkdir %APPDATA%\ScannerWatcher2\logs
   mkdir %APPDATA%\ScannerWatcher2\temp
   
   # Copy template
   copy config_template.json %APPDATA%\ScannerWatcher2\config.json
   
   # Edit configuration
   notepad %APPDATA%\ScannerWatcher2\config.json
   ```
   
   Update with:
   - Valid watch directory path
   - Your OpenAI API key
   - Log level: DEBUG (for development)

6. **Run Tests**
   ```bash
   pytest
   ```

## Architecture Overview

### Layered Architecture

Scanner-Watcher2 follows a clean layered architecture:

```
┌─────────────────────────────────────────┐
│      Windows Service Layer              │
│      (pywin32 integration)              │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│      Service Layer                      │
│  - Orchestrator (lifecycle)             │
│  - Windows Service (wrapper)            │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│      Core Layer                         │
│  - Directory Watcher                    │
│  - File Processor                       │
│  - PDF Processor                        │
│  - AI Service                           │
│  - File Manager                         │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│      Infrastructure Layer               │
│  - Logger                               │
│  - Config Manager                       │
│  - Error Handler                        │
└─────────────────────────────────────────┘
```

### Design Principles

1. **Dependency Injection**: Components receive dependencies via constructor
2. **Single Responsibility**: Each component has one clear purpose
3. **Interface Segregation**: Small, focused interfaces
4. **Dependency Inversion**: Depend on abstractions, not concretions
5. **Type Safety**: Full type hints with mypy strict mode

### Key Patterns

- **Service Orchestrator Pattern**: Central coordinator for component lifecycle
- **Retry Pattern**: Exponential backoff for transient errors
- **Circuit Breaker Pattern**: Prevent cascading failures
- **Observer Pattern**: File system event handling
- **Strategy Pattern**: Multiple PDF extraction strategies

## Development Workflow

### Daily Development

1. **Activate Virtual Environment**
   ```bash
   venv\Scripts\activate
   ```

2. **Pull Latest Changes**
   ```bash
   git pull origin main
   ```

3. **Create Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

4. **Run in Console Mode**
   ```bash
   python -m scanner_watcher2 --console
   ```

5. **Make Changes**
   - Write tests first (TDD)
   - Implement feature
   - Run tests frequently

6. **Run Tests**
   ```bash
   pytest -v
   ```

7. **Check Code Quality**
   ```bash
   black src tests
   ruff check src tests
   mypy src
   ```

8. **Commit Changes**
   ```bash
   git add .
   git commit -m "feat: add feature description"
   ```

### Running the Application

**Console Mode** (Development):
```bash
python -m scanner_watcher2 --console
```

**Service Mode** (Testing):
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

**Configuration Wizard**:
```bash
python -m scanner_watcher2 --configure
```

### Common Development Tasks

#### Adding a New Configuration Option

1. **Update Config Model** (`src/scanner_watcher2/config.py`):
   ```python
   class ProcessingConfig(BaseModel):
       # Add new field
       new_option: int = Field(ge=1, le=100, default=10)
   ```

2. **Update Template** (`config_template.json`):
   ```json
   {
     "processing": {
       "new_option": 10
     }
   }
   ```

3. **Add Validation** (if needed):
   ```python
   @field_validator("new_option")
   @classmethod
   def validate_new_option(cls, v: int) -> int:
       if v < 1 or v > 100:
           raise ValueError("new_option must be between 1 and 100")
       return v
   ```

4. **Update Documentation**:
   - README.md configuration section
   - CONFIGURATION_WIZARD.md

5. **Add Tests**:
   ```python
   def test_new_option_validation():
       # Test valid values
       # Test invalid values
       # Test default value
   ```

#### Adding a New Component

1. **Create Component File**:
   ```python
   # src/scanner_watcher2/core/new_component.py
   from __future__ import annotations
   from typing import Protocol
   
   class NewComponent:
       """Component description."""
       
       def __init__(self, dependency: SomeDependency):
           self._dependency = dependency
       
       def do_something(self, param: str) -> Result:
           """Method description."""
           pass
   ```

2. **Add Type Hints**:
   - Use `from __future__ import annotations`
   - Add type hints to all parameters and return values
   - Use Protocol for interfaces

3. **Add Logging**:
   ```python
   from scanner_watcher2.infrastructure.logger import Logger
   
   class NewComponent:
       def __init__(self, logger: Logger):
           self._logger = logger
       
       def do_something(self):
           self._logger.info("Doing something", component="NewComponent")
   ```

4. **Add Error Handling**:
   ```python
   from scanner_watcher2.infrastructure.error_handler import ErrorHandler
   
   def do_something(self):
       try:
           # Operation
           pass
       except Exception as e:
           self._error_handler.handle_error(e, context={"operation": "do_something"})
   ```

5. **Wire in Orchestrator**:
   ```python
   # src/scanner_watcher2/service/orchestrator.py
   def __init__(self, config: Config):
       self._new_component = NewComponent(dependency)
   ```

6. **Add Tests**:
   - Unit tests in `tests/unit/test_new_component.py`
   - Property tests in `tests/property/test_new_component_properties.py`
   - Integration tests if needed

#### Adding a New Error Type

1. **Update ErrorType Enum** (`src/scanner_watcher2/models.py`):
   ```python
   class ErrorType(Enum):
       TRANSIENT = "transient"
       PERMANENT = "permanent"
       CRITICAL = "critical"
       FATAL = "fatal"
       NEW_TYPE = "new_type"  # Add new type
   ```

2. **Update Error Classification** (`src/scanner_watcher2/infrastructure/error_handler.py`):
   ```python
   def classify_error(self, error: Exception) -> ErrorType:
       if isinstance(error, NewErrorClass):
           return ErrorType.NEW_TYPE
       # ... existing classification
   ```

3. **Add Handling Logic**:
   ```python
   def should_retry(self, error: Exception, attempt: int) -> bool:
       error_type = self.classify_error(error)
       if error_type == ErrorType.NEW_TYPE:
           return attempt < self._max_attempts
       # ... existing logic
   ```

4. **Add Tests**:
   ```python
   def test_new_error_type_classification():
       handler = ErrorHandler()
       error = NewErrorClass("test")
       assert handler.classify_error(error) == ErrorType.NEW_TYPE
   ```

## Testing Strategy

### Test Categories

1. **Unit Tests** (`tests/unit/`):
   - Fast, isolated tests
   - Mock external dependencies
   - Test individual functions/methods
   - Run frequently during development

2. **Property-Based Tests** (`tests/property/`):
   - Use Hypothesis framework
   - Test universal properties
   - Generate random test cases
   - Catch edge cases

3. **Integration Tests** (`tests/integration/`):
   - Test component interactions
   - Use real filesystem
   - Mock only external APIs
   - Test complete workflows

4. **Windows-Specific Tests**:
   - Service installation/removal
   - Event Log integration
   - DPAPI encryption
   - Windows path handling

### Running Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=scanner_watcher2 --cov-report=html

# Specific category
pytest -m unit
pytest -m property
pytest -m integration
pytest -m windows

# Specific file
pytest tests/unit/test_config.py

# Specific test
pytest tests/unit/test_config.py::test_load_config

# Verbose output
pytest -v

# Stop on first failure
pytest -x

# Run last failed tests
pytest --lf

# Show print statements
pytest -s
```

### Writing Tests

#### Unit Test Example

```python
# tests/unit/test_file_manager.py
import pytest
from pathlib import Path
from scanner_watcher2.core.file_manager import FileManager

def test_rename_file_success(tmp_path):
    """Test successful file rename."""
    # Arrange
    source = tmp_path / "source.pdf"
    source.write_text("content")
    manager = FileManager()
    
    # Act
    result = manager.rename_file(source, "target.pdf")
    
    # Assert
    assert result.exists()
    assert result.name == "target.pdf"
    assert not source.exists()

def test_rename_file_conflict(tmp_path):
    """Test rename with existing target file."""
    # Arrange
    source = tmp_path / "source.pdf"
    target = tmp_path / "target.pdf"
    source.write_text("source content")
    target.write_text("target content")
    manager = FileManager()
    
    # Act
    result = manager.rename_file(source, "target.pdf")
    
    # Assert
    assert result.exists()
    assert result.name.startswith("target")
    assert result.name.endswith(".pdf")
    assert result.name != "target.pdf"  # Should have suffix
```

#### Property Test Example

```python
# tests/property/test_file_manager_properties.py
from hypothesis import given, strategies as st
from pathlib import Path
from scanner_watcher2.core.file_manager import FileManager

# Feature: scanner-watcher2, Property 12: Conflict resolution
@given(filename=st.text(min_size=1, max_size=50).filter(lambda s: s.isalnum()))
def test_conflict_resolution_property(tmp_path, filename):
    """For any filename, if target exists, system appends unique suffix."""
    # Arrange
    manager = FileManager()
    source = tmp_path / f"source_{filename}.pdf"
    target = tmp_path / f"{filename}.pdf"
    source.write_text("source")
    target.write_text("existing")
    
    # Act
    result = manager.rename_file(source, f"{filename}.pdf")
    
    # Assert
    assert result.exists()
    assert result != target  # Different file
    assert target.exists()  # Original unchanged
    assert result.name.startswith(filename)
```

### Test Fixtures

Common fixtures in `tests/conftest.py`:

```python
import pytest
from pathlib import Path

@pytest.fixture
def temp_dir(tmp_path):
    """Temporary directory for tests."""
    return tmp_path

@pytest.fixture
def watch_directory(tmp_path):
    """Mock watch directory."""
    watch_dir = tmp_path / "watch"
    watch_dir.mkdir()
    return watch_dir

@pytest.fixture
def config_dir(tmp_path):
    """Configuration directory."""
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    return config_dir

@pytest.fixture
def sample_pdf(tmp_path):
    """Create sample PDF file."""
    pdf_path = tmp_path / "sample.pdf"
    # Create minimal valid PDF
    pdf_path.write_bytes(b"%PDF-1.4\n...")
    return pdf_path
```

### Coverage Goals

- **Overall**: >90%
- **Critical Paths**: 100%
- **Error Handling**: >95%
- **Core Components**: >95%

View coverage report:
```bash
pytest --cov=scanner_watcher2 --cov-report=html
start htmlcov\index.html
```

## Code Style and Standards

### Python Style

- **Line Length**: 100 characters (enforced by black)
- **Indentation**: 4 spaces
- **Quotes**: Double quotes for strings
- **Imports**: Sorted by ruff/isort

### Type Hints

Required on all function signatures:

```python
from __future__ import annotations
from pathlib import Path
from typing import Optional

def process_file(file_path: Path, timeout: int = 30) -> Optional[str]:
    """Process a file with optional timeout."""
    pass
```

Use modern Python type syntax:
- `str | None` instead of `Optional[str]`
- `list[str]` instead of `List[str]`
- `dict[str, int]` instead of `Dict[str, int]`

### Docstrings

Use Google-style docstrings:

```python
def process_file(file_path: Path, timeout: int = 30) -> ProcessingResult:
    """Process a PDF file through the complete workflow.
    
    Args:
        file_path: Path to the PDF file to process
        timeout: Maximum processing time in seconds
        
    Returns:
        ProcessingResult containing success status and details
        
    Raises:
        FileNotFoundError: If file_path doesn't exist
        ProcessingError: If processing fails
        
    Example:
        >>> result = process_file(Path("scan.pdf"))
        >>> print(result.success)
        True
    """
    pass
```

### Error Handling

Always use specific exception types:

```python
# Good
try:
    file_path.read_text()
except FileNotFoundError:
    logger.error("File not found", file_path=str(file_path))
except PermissionError:
    logger.error("Permission denied", file_path=str(file_path))

# Bad
try:
    file_path.read_text()
except Exception as e:
    logger.error("Error", error=str(e))
```

### Logging

Use structured logging with context:

```python
# Good
self._logger.info(
    "File processed successfully",
    file_path=str(file_path),
    processing_time_ms=elapsed_ms,
    document_type=classification.document_type
)

# Bad
self._logger.info(f"Processed {file_path} in {elapsed_ms}ms")
```

### Code Quality Tools

```bash
# Format code (auto-fix)
black src tests

# Lint code (report issues)
ruff check src tests

# Fix auto-fixable issues
ruff check --fix src tests

# Type check
mypy src

# Run all checks
black src tests && ruff check src tests && mypy src
```

### Pre-commit Checklist

Before committing:
- [ ] All tests pass
- [ ] Code formatted with black
- [ ] No ruff warnings
- [ ] No mypy errors
- [ ] Docstrings added/updated
- [ ] Tests added for new code
- [ ] Documentation updated

## Component Details

### Core Layer

#### Directory Watcher
- **File**: `src/scanner_watcher2/core/directory_watcher.py`
- **Purpose**: Monitor filesystem for new files
- **Key Methods**:
  - `start()`: Begin monitoring
  - `stop()`: Stop monitoring
  - `is_file_stable()`: Check if file is done writing
- **Dependencies**: watchdog library
- **Testing**: Mock filesystem events

#### File Processor
- **File**: `src/scanner_watcher2/core/file_processor.py`
- **Purpose**: Coordinate complete processing workflow
- **Key Methods**:
  - `process_file()`: Main workflow coordinator
  - `validate_file()`: Check file validity
- **Dependencies**: PDF Processor, AI Service, File Manager
- **Testing**: Integration tests with real files

#### PDF Processor
- **File**: `src/scanner_watcher2/core/pdf_processor.py`
- **Purpose**: Extract pages from PDFs
- **Key Methods**:
  - `extract_first_page()`: Get first page as image
  - `optimize_image()`: Reduce image size
  - `validate_pdf()`: Check PDF validity
- **Dependencies**: PyMuPDF, PyPDF2, Pillow
- **Testing**: Use fixture PDFs

#### AI Service
- **File**: `src/scanner_watcher2/core/ai_service.py`
- **Purpose**: Classify documents via OpenAI API
- **Key Methods**:
  - `classify_document()`: Send image to API
  - `parse_classification()`: Parse response
- **Dependencies**: OpenAI SDK
- **Testing**: Mock API responses

#### File Manager
- **File**: `src/scanner_watcher2/core/file_manager.py`
- **Purpose**: Handle file operations
- **Key Methods**:
  - `rename_file()`: Rename with conflict resolution
  - `create_temp_file()`: Create temporary file
  - `cleanup_temp_files()`: Delete temporary files
- **Dependencies**: None (uses pathlib)
- **Testing**: Use tmp_path fixture

### Infrastructure Layer

#### Logger
- **File**: `src/scanner_watcher2/infrastructure/logger.py`
- **Purpose**: Structured logging
- **Key Methods**:
  - `info()`, `warning()`, `error()`, `critical()`
  - `_write_to_event_log()`: Windows Event Log
- **Dependencies**: structlog, pywin32
- **Testing**: Capture log output

#### Config Manager
- **File**: `src/scanner_watcher2/infrastructure/config_manager.py`
- **Purpose**: Configuration management
- **Key Methods**:
  - `load_config()`: Load and validate
  - `save_config()`: Save configuration
  - `encrypt_api_key()`: DPAPI encryption
- **Dependencies**: pydantic, pywin32
- **Testing**: Use temporary config files

#### Error Handler
- **File**: `src/scanner_watcher2/infrastructure/error_handler.py`
- **Purpose**: Centralized error handling
- **Key Methods**:
  - `classify_error()`: Determine error type
  - `should_retry()`: Retry decision
  - `execute_with_retry()`: Retry wrapper
- **Dependencies**: None
- **Testing**: Test all error types

### Service Layer

#### Orchestrator
- **File**: `src/scanner_watcher2/service/orchestrator.py`
- **Purpose**: Component lifecycle management
- **Key Methods**:
  - `start()`: Initialize all components
  - `stop()`: Graceful shutdown
  - `health_check()`: System health check
- **Dependencies**: All core and infrastructure components
- **Testing**: Integration tests

#### Windows Service
- **File**: `src/scanner_watcher2/service/windows_service.py`
- **Purpose**: Windows service wrapper
- **Key Methods**:
  - `SvcDoRun()`: Service main loop
  - `SvcStop()`: Handle stop request
- **Dependencies**: pywin32, Orchestrator
- **Testing**: Windows-specific tests

## Building and Packaging

### Building Executable

1. **Install PyInstaller**:
   ```bash
   pip install pyinstaller
   ```

2. **Build Using Spec File**:
   ```bash
   pyinstaller scanner_watcher2.spec
   ```

3. **Or Use Build Script**:
   ```bash
   build.bat
   ```

4. **Output**:
   - Executable: `dist/scanner_watcher2.exe`
   - Size: ~50-60 MB (includes Python runtime)

### Building Installer

1. **Install Inno Setup**:
   - Download from: https://jrsoftware.org/isdl.php
   - Install to default location

2. **Build Installer**:
   ```bash
   build_installer.bat
   ```

3. **Or Manual Build**:
   ```bash
   "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" scanner_watcher2.iss
   ```

4. **Output**:
   - Installer: `Output/ScannerWatcher2Setup.exe`
   - Size: ~50-60 MB

### Testing Build

See [TESTING_CHECKLIST.md](TESTING_CHECKLIST.md) for comprehensive testing procedures.

Quick test:
```bash
# Run executable
dist\scanner_watcher2.exe --console

# Install service
dist\scanner_watcher2.exe --install-service

# Test configuration
dist\scanner_watcher2.exe --configure
```

## Debugging

### Console Mode Debugging

Run with detailed logging:
```bash
python -m scanner_watcher2 --console
```

Set log level to DEBUG in config.json:
```json
{
  "log_level": "DEBUG"
}
```

### Python Debugger

Add breakpoint:
```python
import pdb; pdb.set_trace()
```

Or use built-in breakpoint():
```python
breakpoint()  # Python 3.7+
```

### VS Code Debugging

Create `.vscode/launch.json`:
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
      "console": "integratedTerminal",
      "justMyCode": false
    },
    {
      "name": "Scanner-Watcher2 Tests",
      "type": "python",
      "request": "launch",
      "module": "pytest",
      "args": ["-v"],
      "console": "integratedTerminal",
      "justMyCode": false
    }
  ]
}
```

### Logging Debug Information

Add debug logging:
```python
self._logger.debug(
    "Processing file",
    file_path=str(file_path),
    file_size=file_path.stat().st_size,
    file_mtime=file_path.stat().st_mtime
)
```

### Windows Event Log

View service events:
1. Open Event Viewer (eventvwr.msc)
2. Windows Logs → Application
3. Filter by Source: "Scanner-Watcher2"

### Performance Profiling

Use cProfile:
```python
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()

# Code to profile
process_file(file_path)

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(20)
```

## Contributing

### Contribution Workflow

1. **Fork Repository**
2. **Create Feature Branch**:
   ```bash
   git checkout -b feature/your-feature
   ```

3. **Make Changes**:
   - Follow code style guidelines
   - Write tests
   - Update documentation

4. **Run Tests**:
   ```bash
   pytest
   black src tests
   ruff check src tests
   mypy src
   ```

5. **Commit Changes**:
   ```bash
   git add .
   git commit -m "feat: add feature description"
   ```

6. **Push Branch**:
   ```bash
   git push origin feature/your-feature
   ```

7. **Create Pull Request**

### Commit Message Format

Follow conventional commits:

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `test:` Test changes
- `refactor:` Code refactoring
- `style:` Code style changes
- `chore:` Build/tooling changes

Examples:
```
feat: add support for custom file prefixes
fix: handle corrupted PDF files gracefully
docs: update configuration guide
test: add property tests for file manager
refactor: simplify error handling logic
```

### Pull Request Guidelines

- Clear description of changes
- Reference related issues
- Include tests for new features
- Update documentation
- Ensure CI passes
- Request review from maintainers

### Code Review Checklist

- [ ] Code follows style guidelines
- [ ] Tests added and passing
- [ ] Documentation updated
- [ ] No breaking changes (or documented)
- [ ] Performance impact considered
- [ ] Security implications reviewed
- [ ] Error handling appropriate
- [ ] Logging added where needed

## Additional Resources

- [README.md](README.md) - Project overview
- [BUILD.md](BUILD.md) - Build instructions
- [INSTALLER.md](INSTALLER.md) - Installer guide
- [CONFIGURATION_WIZARD.md](CONFIGURATION_WIZARD.md) - Configuration details
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Troubleshooting guide
- [TESTING_CHECKLIST.md](TESTING_CHECKLIST.md) - Testing procedures
- [.kiro/specs/scanner-watcher2/](/.kiro/specs/scanner-watcher2/) - Feature specifications
