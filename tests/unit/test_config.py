"""
Unit tests for configuration models.
"""

import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

from scanner_watcher2.config import (
    AIConfig,
    Config,
    LoggingConfig,
    ProcessingConfig,
    ServiceConfig,
)


class TestProcessingConfig:
    """Test ProcessingConfig model."""

    def test_default_values(self) -> None:
        """Verify default configuration values."""
        config = ProcessingConfig()
        assert config.file_prefix == "SCAN-"
        assert config.pages_to_extract == 3
        assert config.retry_attempts == 3
        assert config.retry_delay_seconds == 5
        assert config.temp_directory is None

    def test_valid_retry_attempts(self) -> None:
        """Verify valid retry attempts are accepted."""
        config = ProcessingConfig(retry_attempts=5)
        assert config.retry_attempts == 5

    def test_invalid_retry_attempts_too_low(self) -> None:
        """Verify retry attempts below 1 are rejected."""
        with pytest.raises(ValidationError):
            ProcessingConfig(retry_attempts=0)

    def test_invalid_retry_attempts_too_high(self) -> None:
        """Verify retry attempts above 10 are rejected."""
        with pytest.raises(ValidationError):
            ProcessingConfig(retry_attempts=11)

    def test_valid_file_prefix(self) -> None:
        """Verify valid file prefix is accepted."""
        config = ProcessingConfig(file_prefix="DOC-")
        assert config.file_prefix == "DOC-"

    def test_empty_file_prefix_rejected(self) -> None:
        """Verify empty file prefix is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ProcessingConfig(file_prefix="")
        assert "file_prefix" in str(exc_info.value)

    def test_whitespace_file_prefix_rejected(self) -> None:
        """Verify whitespace-only file prefix is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ProcessingConfig(file_prefix="   ")
        assert "file_prefix" in str(exc_info.value)

    def test_file_prefix_with_invalid_chars_rejected(self) -> None:
        """Verify file prefix with invalid filename characters is rejected."""
        invalid_prefixes = [
            "SCAN<",
            "SCAN>",
            "SCAN:",
            'SCAN"',
            "SCAN|",
            "SCAN?",
            "SCAN*",
            "SCAN\\",
            "SCAN/",
        ]
        for prefix in invalid_prefixes:
            with pytest.raises(ValidationError) as exc_info:
                ProcessingConfig(file_prefix=prefix)
            assert "file_prefix" in str(exc_info.value)

    def test_file_prefix_strips_whitespace(self) -> None:
        """Verify file prefix strips leading/trailing whitespace."""
        config = ProcessingConfig(file_prefix="  SCAN-  ")
        assert config.file_prefix == "SCAN-"

    def test_valid_pages_to_extract(self) -> None:
        """Verify valid pages_to_extract values are accepted."""
        config = ProcessingConfig(pages_to_extract=5)
        assert config.pages_to_extract == 5

    def test_invalid_pages_to_extract_too_low(self) -> None:
        """Verify pages_to_extract below 1 is rejected."""
        with pytest.raises(ValidationError):
            ProcessingConfig(pages_to_extract=0)

    def test_invalid_pages_to_extract_too_high(self) -> None:
        """Verify pages_to_extract above 10 is rejected."""
        with pytest.raises(ValidationError):
            ProcessingConfig(pages_to_extract=11)


class TestConfig:
    """Test main Config model."""

    def test_valid_config_creation(self) -> None:
        """Verify valid configuration can be created."""
        # Use platform-appropriate absolute path
        if sys.platform == "win32":
            watch_dir = Path("C:\\test\\watch")
        else:
            watch_dir = Path("/test/watch")
        
        config = Config(
            version="1.0.0",
            watch_directory=watch_dir,
            openai_api_key="test-key-123",
            log_level="INFO",
        )
        
        assert config.version == "1.0.0"
        assert config.watch_directory == watch_dir
        assert config.openai_api_key == "test-key-123"
        assert config.log_level == "INFO"

    def test_log_level_normalized_to_uppercase(self) -> None:
        """Verify log level is normalized to uppercase."""
        if sys.platform == "win32":
            watch_dir = Path("C:\\test\\watch")
        else:
            watch_dir = Path("/test/watch")
        
        config = Config(
            version="1.0.0",
            watch_directory=watch_dir,
            openai_api_key="test-key",
            log_level="debug",
        )
        
        assert config.log_level == "DEBUG"

    def test_invalid_log_level_rejected(self) -> None:
        """Verify invalid log level is rejected."""
        if sys.platform == "win32":
            watch_dir = Path("C:\\test\\watch")
        else:
            watch_dir = Path("/test/watch")
        
        with pytest.raises(ValidationError) as exc_info:
            Config(
                version="1.0.0",
                watch_directory=watch_dir,
                openai_api_key="test-key",
                log_level="INVALID",
            )
        
        assert "log_level" in str(exc_info.value)

    def test_empty_api_key_rejected(self) -> None:
        """Verify empty API key is rejected."""
        if sys.platform == "win32":
            watch_dir = Path("C:\\test\\watch")
        else:
            watch_dir = Path("/test/watch")
        
        with pytest.raises(ValidationError) as exc_info:
            Config(
                version="1.0.0",
                watch_directory=watch_dir,
                openai_api_key="",
                log_level="INFO",
            )
        
        assert "openai_api_key" in str(exc_info.value)

    def test_whitespace_api_key_rejected(self) -> None:
        """Verify whitespace-only API key is rejected."""
        if sys.platform == "win32":
            watch_dir = Path("C:\\test\\watch")
        else:
            watch_dir = Path("/test/watch")
        
        with pytest.raises(ValidationError) as exc_info:
            Config(
                version="1.0.0",
                watch_directory=watch_dir,
                openai_api_key="   ",
                log_level="INFO",
            )
        
        assert "openai_api_key" in str(exc_info.value)

    def test_relative_watch_directory_rejected(self) -> None:
        """Verify relative watch directory path is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            Config(
                version="1.0.0",
                watch_directory=Path("relative/path"),
                openai_api_key="test-key",
                log_level="INFO",
            )
        
        assert "watch_directory" in str(exc_info.value)

    def test_default_nested_configs(self) -> None:
        """Verify nested configs use default factories."""
        if sys.platform == "win32":
            watch_dir = Path("C:\\test\\watch")
        else:
            watch_dir = Path("/test/watch")
        
        config = Config(
            version="1.0.0",
            watch_directory=watch_dir,
            openai_api_key="test-key",
        )
        
        assert isinstance(config.processing, ProcessingConfig)
        assert isinstance(config.ai, AIConfig)
        assert isinstance(config.logging, LoggingConfig)
        assert isinstance(config.service, ServiceConfig)
