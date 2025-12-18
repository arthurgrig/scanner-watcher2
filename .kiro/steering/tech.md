# Technology Stack

## Language & Runtime

- **Python 3.12+**: Primary language with type hints throughout
- **Build System**: setuptools with pyproject.toml configuration

## Core Dependencies

- **pywin32**: Native Windows service integration and Windows APIs
- **watchdog**: Filesystem monitoring using Windows ReadDirectoryChangesW
- **PyMuPDF (fitz)**: Primary PDF processing library
- **PyPDF2**: Fallback PDF processor
- **openai**: Official OpenAI Python SDK for GPT-4 Vision API
- **pydantic**: Type-safe configuration and data validation
- **structlog**: Structured JSON logging
- **Pillow**: Image processing for PDF page extraction

## Development Tools

- **pytest**: Testing framework with markers (unit, integration, property, windows)
- **pytest-cov**: Code coverage reporting
- **pytest-mock**: Mocking utilities
- **hypothesis**: Property-based testing
- **black**: Code formatting (line length: 100)
- **mypy**: Static type checking with strict mode
- **ruff**: Fast linting (pycodestyle, pyflakes, isort, flake8-bugbear)

## Code Style

- **Line Length**: 100 characters (enforced by black and ruff)
- **Type Hints**: Required on all function signatures (mypy strict mode)
- **Docstrings**: Google-style docstrings for all public APIs
- **Imports**: Sorted with isort via ruff
- **Modern Python**: Use `|` for unions, `Path` for filesystem operations

## Common Commands

```bash
# Development setup
python -m venv venv
venv\Scripts\activate  # Windows
pip install -e ".[dev]"

# Testing
pytest                                    # Run all tests
pytest --cov=scanner_watcher2            # With coverage
pytest --cov-report=html                 # HTML coverage report
pytest -m unit                           # Unit tests only
pytest -m property                       # Property-based tests only
pytest -m integration                    # Integration tests only
pytest -m windows                        # Windows-specific tests only

# Code quality
black src tests                          # Format code
ruff check src tests                     # Lint code
mypy src                                 # Type check

# Build (future)
pyinstaller scanner_watcher2.spec        # Build Windows executable
iscc windows/installer.iss               # Create installer
```

## Windows-Specific Technologies

- **Service Management**: pywin32 (win32serviceutil, win32service, win32event)
- **Event Logging**: win32evtlog for Windows Event Log integration
- **Installer**: Inno Setup for professional Windows installer
- **Executable Bundling**: PyInstaller for single-file executable with embedded Python
- **Security**: Windows DPAPI for API key encryption

## Architecture Patterns

- **Dependency Injection**: Components receive dependencies via constructor
- **Type Safety**: Pydantic models for configuration and data validation
- **Error Handling**: Centralized error handler with retry strategies
- **Logging**: Structured JSON logging with correlation IDs
- **Testing**: Comprehensive unit, integration, and property-based tests
