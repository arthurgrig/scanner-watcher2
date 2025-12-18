# Project Structure

## Directory Layout

```
scanner-watcher2/
├── src/scanner_watcher2/          # Main application package
│   ├── core/                      # Core business logic components
│   ├── infrastructure/            # Infrastructure layer (logging, config, errors)
│   ├── service/                   # Service layer (orchestration, Windows service)
│   ├── config.py                  # Configuration models (Pydantic)
│   └── models.py                  # Data models and enums
├── tests/                         # Test suite
│   ├── unit/                      # Unit tests (fast, isolated, mocked)
│   ├── integration/               # Integration tests (component interactions)
│   ├── property/                  # Property-based tests (hypothesis)
│   ├── fixtures/                  # Test fixtures and sample data
│   └── conftest.py                # Shared pytest fixtures
├── pyproject.toml                 # Project configuration and dependencies
└── README.md                      # Project documentation
```

## Layer Responsibilities

### Core Layer (`src/scanner_watcher2/core/`)

Business logic components that implement document processing workflow:

- **ai_service.py**: OpenAI API integration for document classification
- **pdf_processor.py**: PDF extraction and image processing
- **file_processor.py**: Workflow coordinator for complete processing pipeline
- **file_manager.py**: File operations (rename, move, cleanup)
- **directory_watcher.py**: Filesystem monitoring for new documents

### Infrastructure Layer (`src/scanner_watcher2/infrastructure/`)

Cross-cutting concerns and foundational services:

- **logger.py**: Structured JSON logging with Windows Event Log integration
- **config_manager.py**: Configuration loading, validation, and management
- **error_handler.py**: Centralized error handling with retry logic and circuit breakers

### Service Layer (`src/scanner_watcher2/service/`)

Application orchestration and Windows service integration:

- **orchestrator.py**: Main application coordinator, component lifecycle management
- **windows_service.py**: Native Windows service wrapper using pywin32

### Configuration & Models

- **config.py**: Pydantic models for type-safe configuration (Config, ProcessingConfig, AIConfig, LoggingConfig, ServiceConfig)
- **models.py**: Core data types (ProcessingResult, Classification, HealthStatus, ErrorType enum)

## Test Organization

### Test Markers

Use pytest markers to categorize tests:

- `@pytest.mark.unit`: Fast, isolated tests with mocked dependencies
- `@pytest.mark.integration`: Tests with real filesystem and component interactions
- `@pytest.mark.property`: Property-based tests using hypothesis
- `@pytest.mark.windows`: Windows-specific functionality tests

### Fixture Conventions

Common fixtures in `conftest.py`:

- `temp_dir`: Temporary directory for test isolation
- `watch_directory`: Mock watch directory
- `config_dir`: Configuration directory for tests
- `temp_files_dir`: Temporary files directory

## Naming Conventions

### Files & Modules

- Use snake_case for all Python files
- Test files: `test_<module_name>.py`
- One class per file for major components
- Group related utilities in single files

### Classes & Functions

- Classes: PascalCase (e.g., `FileProcessor`, `AIService`)
- Functions/methods: snake_case (e.g., `process_file`, `validate_config`)
- Private methods: prefix with underscore (e.g., `_build_context`)
- Type hints: Required on all public APIs

### Constants & Enums

- Constants: UPPER_SNAKE_CASE
- Enums: PascalCase class, UPPER_SNAKE_CASE values

## Import Organization

Imports sorted by ruff/isort in this order:

1. Standard library imports
2. Third-party imports
3. Local application imports

Use `from __future__ import annotations` for forward references and cleaner type hints.

## Path Handling

- Always use `pathlib.Path` for filesystem operations
- Never use string concatenation for paths
- Use absolute paths in configuration
- Handle Windows path separators automatically via Path

## Windows-Specific Considerations

### File Paths

- Configuration: `%APPDATA%\ScannerWatcher2\config.json`
- Logs: `%APPDATA%\ScannerWatcher2\logs\`
- Installation: `C:\Program Files\ScannerWatcher2\`

### Platform Detection

```python
import platform
if platform.system() == "Windows":
    # Windows-specific code
```

### Service Integration

Windows service components use pywin32 and follow Windows service lifecycle patterns (SvcStop, SvcDoRun).
