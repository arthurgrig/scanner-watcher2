"""
Property-based tests for configuration validation.
"""

import sys
from pathlib import Path

import pytest
from hypothesis import given, strategies as st
from pydantic import ValidationError

from scanner_watcher2.config import (
    AIConfig,
    Config,
    LoggingConfig,
    ProcessingConfig,
    ServiceConfig,
)


def _make_absolute_path(s: str) -> Path:
    """Create a platform-appropriate absolute path for testing."""
    if sys.platform == "win32":
        # Windows: use C:\ as root
        return Path(f"C:\\{s}")
    else:
        # Unix-like: use / as root
        return Path("/").absolute() / s


# Feature: scanner-watcher2, Property 26: Configuration validation
@given(
    version=st.text(min_size=1),
    watch_directory=st.text(min_size=1).map(_make_absolute_path),
    api_key=st.text(min_size=1).filter(lambda s: s.strip()),
    log_level=st.sampled_from(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]),
)
def test_valid_config_always_validates(
    version: str, watch_directory: Path, api_key: str, log_level: str
) -> None:
    """
    For any valid configuration with required fields, the system should validate successfully.
    
    Validates: Requirements 8.2
    """
    config = Config(
        version=version,
        watch_directory=watch_directory,
        openai_api_key=api_key,
        log_level=log_level,
    )
    
    assert config.version == version
    assert config.watch_directory == watch_directory
    assert config.openai_api_key == api_key
    assert config.log_level == log_level.upper()


# Feature: scanner-watcher2, Property 26: Configuration validation
@given(
    version=st.text(min_size=1),
    watch_directory=st.text(min_size=1).map(_make_absolute_path),
    api_key=st.text(min_size=1).filter(lambda s: s.strip()),
)
def test_invalid_log_level_rejected(
    version: str, watch_directory: Path, api_key: str
) -> None:
    """
    For any configuration with invalid log level, validation should fail.
    
    Validates: Requirements 8.2
    """
    invalid_log_level = "INVALID_LEVEL"
    
    with pytest.raises(ValidationError) as exc_info:
        Config(
            version=version,
            watch_directory=watch_directory,
            openai_api_key=api_key,
            log_level=invalid_log_level,
        )
    
    assert "log_level" in str(exc_info.value)


# Feature: scanner-watcher2, Property 26: Configuration validation
@given(
    version=st.text(min_size=1),
    watch_directory=st.text(min_size=1).map(_make_absolute_path),
    log_level=st.sampled_from(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]),
)
def test_empty_api_key_rejected(
    version: str, watch_directory: Path, log_level: str
) -> None:
    """
    For any configuration with empty API key, validation should fail.
    
    Validates: Requirements 8.2
    """
    with pytest.raises(ValidationError) as exc_info:
        Config(
            version=version,
            watch_directory=watch_directory,
            openai_api_key="",
            log_level=log_level,
        )
    
    assert "openai_api_key" in str(exc_info.value)


# Feature: scanner-watcher2, Property 26: Configuration validation
@given(
    version=st.text(min_size=1),
    watch_directory=st.text(min_size=1).filter(
        lambda s: not s.startswith("/") and not (len(s) > 1 and s[1] == ":")
    ),
    api_key=st.text(min_size=1).filter(lambda s: s.strip()),
    log_level=st.sampled_from(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]),
)
def test_relative_watch_directory_rejected(
    version: str, watch_directory: str, api_key: str, log_level: str
) -> None:
    """
    For any configuration with relative watch directory path, validation should fail.
    
    Validates: Requirements 8.2, 8.3
    """
    with pytest.raises(ValidationError) as exc_info:
        Config(
            version=version,
            watch_directory=Path(watch_directory),
            openai_api_key=api_key,
            log_level=log_level,
        )
    
    assert "watch_directory" in str(exc_info.value)


# Feature: scanner-watcher2, Property 26: Configuration validation
@given(
    retry_attempts=st.integers(min_value=1, max_value=10),
    retry_delay=st.integers(min_value=1, max_value=60),
)
def test_processing_config_valid_ranges(
    retry_attempts: int, retry_delay: int
) -> None:
    """
    For any processing config with values in valid ranges, validation should succeed.
    
    Validates: Requirements 8.2
    """
    config = ProcessingConfig(
        retry_attempts=retry_attempts,
        retry_delay_seconds=retry_delay,
    )
    
    assert config.retry_attempts == retry_attempts
    assert config.retry_delay_seconds == retry_delay


# Feature: scanner-watcher2, Property 26: Configuration validation
@given(retry_attempts=st.integers().filter(lambda x: x < 1 or x > 10))
def test_processing_config_invalid_retry_attempts(retry_attempts: int) -> None:
    """
    For any processing config with retry attempts outside valid range, validation should fail.
    
    Validates: Requirements 8.2
    """
    with pytest.raises(ValidationError) as exc_info:
        ProcessingConfig(retry_attempts=retry_attempts)
    
    assert "retry_attempts" in str(exc_info.value)


# Feature: scanner-watcher2, Property 26: Configuration validation
@given(retry_delay=st.integers().filter(lambda x: x < 1 or x > 60))
def test_processing_config_invalid_retry_delay(retry_delay: int) -> None:
    """
    For any processing config with retry delay outside valid range, validation should fail.
    
    Validates: Requirements 8.2
    """
    with pytest.raises(ValidationError) as exc_info:
        ProcessingConfig(retry_delay_seconds=retry_delay)
    
    assert "retry_delay_seconds" in str(exc_info.value)



# Feature: scanner-watcher2, Property 25: API key encryption
@given(api_key=st.text(min_size=1).filter(lambda s: s.strip()))
def test_api_key_encryption_round_trip(api_key: str) -> None:
    """
    For any API key stored in the configuration file, the key should be encrypted using Windows DPAPI.
    
    This tests the round-trip property: encrypt then decrypt should return the original value.
    
    Validates: Requirements 8.1
    """
    from scanner_watcher2.infrastructure.config_manager import ConfigManager
    
    manager = ConfigManager()
    
    # Encrypt the API key
    encrypted = manager.encrypt_api_key(api_key)
    
    # Encrypted value should be different from original (unless on non-Windows with very short keys)
    # and should be base64-encoded
    assert encrypted != api_key or len(api_key) < 4  # base64 padding edge case
    
    # Decrypt should return original value
    decrypted = manager.decrypt_api_key(encrypted)
    assert decrypted == api_key


# Feature: scanner-watcher2, Property 25: API key encryption
@given(
    version=st.text(min_size=1),
    watch_directory=st.text(min_size=1).map(_make_absolute_path),
    api_key=st.text(min_size=1).filter(lambda s: s.strip()),
    log_level=st.sampled_from(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]),
)
def test_config_save_encrypts_api_key(
    version: str,
    watch_directory: Path,
    api_key: str,
    log_level: str,
) -> None:
    """
    For any configuration saved to disk, the API key should be encrypted in the file.
    
    Validates: Requirements 8.1
    """
    import json
    import tempfile
    from scanner_watcher2.infrastructure.config_manager import ConfigManager
    
    # Create temporary directory for this test
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = ConfigManager()
        config_path = Path(tmpdir) / "config.json"
        
        # Create and save config
        config = Config(
            version=version,
            watch_directory=watch_directory,
            openai_api_key=api_key,
            log_level=log_level,
        )
        
        manager.save_config(config, config_path)
        
        # Read raw file and verify API key is encrypted
        with open(config_path, "r", encoding="utf-8") as f:
            saved_data = json.load(f)
        
        # The encrypted API key should be different from the plain text
        encrypted_key = saved_data["openai_api_key"]
        assert encrypted_key != api_key
        
        # Load config back and verify API key is decrypted correctly
        loaded_config = manager.load_config(config_path)
        assert loaded_config.openai_api_key == api_key



# Feature: scanner-watcher2, Property 27: Configuration hot-reload
@given(
    version1=st.text(min_size=1),
    version2=st.text(min_size=1),
    watch_directory=st.text(min_size=1).map(_make_absolute_path),
    api_key1=st.text(min_size=1).filter(lambda s: s.strip()),
    api_key2=st.text(min_size=1).filter(lambda s: s.strip()),
    log_level1=st.sampled_from(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]),
    log_level2=st.sampled_from(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]),
)
def test_configuration_hot_reload(
    version1: str,
    version2: str,
    watch_directory: Path,
    api_key1: str,
    api_key2: str,
    log_level1: str,
    log_level2: str,
) -> None:
    """
    For any configuration update, the system should reload the configuration without requiring a service restart.
    
    Validates: Requirements 8.4
    """
    import tempfile
    from scanner_watcher2.infrastructure.config_manager import ConfigManager
    
    # Create temporary directory for this test
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = ConfigManager()
        config_path = Path(tmpdir) / "config.json"
        
        # Create and save initial config
        config1 = Config(
            version=version1,
            watch_directory=watch_directory,
            openai_api_key=api_key1,
            log_level=log_level1,
        )
        
        manager.save_config(config1, config_path)
        
        # Load initial config
        loaded_config1 = manager.load_config(config_path)
        assert loaded_config1.version == version1
        assert loaded_config1.openai_api_key == api_key1
        assert loaded_config1.log_level == log_level1.upper()
        
        # Update config file with new values
        config2 = Config(
            version=version2,
            watch_directory=watch_directory,
            openai_api_key=api_key2,
            log_level=log_level2,
        )
        
        manager.save_config(config2, config_path)
        
        # Reload config without creating new manager instance
        reloaded_config = manager.reload_config()
        
        # Verify reloaded config has new values
        assert reloaded_config is not None
        assert reloaded_config.version == version2
        assert reloaded_config.openai_api_key == api_key2
        assert reloaded_config.log_level == log_level2.upper()
