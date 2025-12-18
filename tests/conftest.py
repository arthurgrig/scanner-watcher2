"""
Pytest configuration and shared fixtures.
"""

import tempfile
from collections.abc import Generator
from pathlib import Path

import pytest


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def watch_directory(temp_dir: Path) -> Path:
    """Create a watch directory for testing."""
    watch_dir = temp_dir / "watch"
    watch_dir.mkdir()
    return watch_dir


@pytest.fixture
def temp_files_dir(temp_dir: Path) -> Path:
    """Create a temporary files directory for testing."""
    temp_files = temp_dir / "temp"
    temp_files.mkdir()
    return temp_files


@pytest.fixture
def config_dir(temp_dir: Path) -> Path:
    """Create a configuration directory for testing."""
    config = temp_dir / "config"
    config.mkdir()
    return config
