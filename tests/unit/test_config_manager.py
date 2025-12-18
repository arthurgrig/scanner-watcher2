"""
Unit tests for ConfigManager.
"""

import json
import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

from scanner_watcher2.config import Config
from scanner_watcher2.infrastructure.config_manager import ConfigManager


class TestConfigManager:
    """Test ConfigManager functionality."""

    def test_load_config_success(self, temp_dir: Path) -> None:
        """Verify config can be loaded from valid file."""
        manager = ConfigManager()
        config_path = temp_dir / "config.json"
        
        # Create a valid config file
        if sys.platform == "win32":
            watch_dir = "C:\\test\\watch"
        else:
            watch_dir = "/test/watch"
        
        config_data = {
            "version": "1.0.0",
            "watch_directory": watch_dir,
            "openai_api_key": "test-key-123",
            "log_level": "INFO",
        }
        
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config_data, f)
        
        # Load config
        config = manager.load_config(config_path)
        
        assert config.version == "1.0.0"
        assert config.openai_api_key == "test-key-123"
        assert config.log_level == "INFO"

    def test_load_config_file_not_found(self, temp_dir: Path) -> None:
        """Verify FileNotFoundError raised when config file doesn't exist."""
        manager = ConfigManager()
        config_path = temp_dir / "nonexistent.json"
        
        with pytest.raises(FileNotFoundError):
            manager.load_config(config_path)

    def test_load_config_invalid_json(self, temp_dir: Path) -> None:
        """Verify ValueError raised for malformed JSON."""
        manager = ConfigManager()
        config_path = temp_dir / "config.json"
        
        # Write invalid JSON
        with open(config_path, "w", encoding="utf-8") as f:
            f.write("{ invalid json }")
        
        with pytest.raises(ValueError, match="Invalid JSON"):
            manager.load_config(config_path)

    def test_load_config_invalid_data(self, temp_dir: Path) -> None:
        """Verify ValidationError raised for invalid config data."""
        manager = ConfigManager()
        config_path = temp_dir / "config.json"
        
        # Write config with missing required fields
        config_data = {
            "version": "1.0.0",
        }
        
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config_data, f)
        
        with pytest.raises(ValidationError):
            manager.load_config(config_path)

    def test_save_config_success(self, temp_dir: Path) -> None:
        """Verify config can be saved to file."""
        manager = ConfigManager()
        config_path = temp_dir / "config.json"
        
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
        
        # Save config
        manager.save_config(config, config_path)
        
        # Verify file exists
        assert config_path.exists()
        
        # Verify content
        with open(config_path, "r", encoding="utf-8") as f:
            saved_data = json.load(f)
        
        assert saved_data["version"] == "1.0.0"
        assert saved_data["log_level"] == "INFO"

    def test_save_config_creates_parent_directory(self, temp_dir: Path) -> None:
        """Verify parent directories are created if they don't exist."""
        manager = ConfigManager()
        config_path = temp_dir / "subdir" / "config.json"
        
        if sys.platform == "win32":
            watch_dir = Path("C:\\test\\watch")
        else:
            watch_dir = Path("/test/watch")
        
        config = Config(
            version="1.0.0",
            watch_directory=watch_dir,
            openai_api_key="test-key",
            log_level="INFO",
        )
        
        # Save config
        manager.save_config(config, config_path)
        
        # Verify file exists
        assert config_path.exists()

    def test_encrypt_decrypt_api_key_round_trip(self) -> None:
        """Verify API key encryption and decryption round trip."""
        manager = ConfigManager()
        original_key = "sk-test-key-12345"
        
        # Encrypt
        encrypted = manager.encrypt_api_key(original_key)
        
        # Verify encrypted is different
        assert encrypted != original_key
        
        # Decrypt
        decrypted = manager.decrypt_api_key(encrypted)
        
        # Verify round trip
        assert decrypted == original_key

    def test_encrypt_api_key_empty_raises_error(self) -> None:
        """Verify empty API key raises ValueError."""
        manager = ConfigManager()
        
        with pytest.raises(ValueError, match="API key cannot be empty"):
            manager.encrypt_api_key("")

    def test_decrypt_api_key_empty_raises_error(self) -> None:
        """Verify empty encrypted key raises ValueError."""
        manager = ConfigManager()
        
        with pytest.raises(ValueError, match="Encrypted API key cannot be empty"):
            manager.decrypt_api_key("")

    def test_decrypt_api_key_invalid_base64_raises_error(self) -> None:
        """Verify invalid base64 raises ValueError."""
        manager = ConfigManager()
        
        with pytest.raises(ValueError, match="Invalid base64 encoding"):
            manager.decrypt_api_key("not-valid-base64!!!")

    def test_reload_config_success(self, temp_dir: Path) -> None:
        """Verify config can be reloaded."""
        manager = ConfigManager()
        config_path = temp_dir / "config.json"
        
        if sys.platform == "win32":
            watch_dir = Path("C:\\test\\watch")
        else:
            watch_dir = Path("/test/watch")
        
        # Create and save initial config
        config1 = Config(
            version="1.0.0",
            watch_directory=watch_dir,
            openai_api_key="key1",
            log_level="INFO",
        )
        
        manager.save_config(config1, config_path)
        manager.load_config(config_path)
        
        # Update config file
        config2 = Config(
            version="2.0.0",
            watch_directory=watch_dir,
            openai_api_key="key2",
            log_level="DEBUG",
        )
        
        manager.save_config(config2, config_path)
        
        # Reload
        reloaded = manager.reload_config()
        
        assert reloaded is not None
        assert reloaded.version == "2.0.0"
        assert reloaded.openai_api_key == "key2"
        assert reloaded.log_level == "DEBUG"

    def test_reload_config_without_previous_load(self) -> None:
        """Verify reload returns None if no config was previously loaded."""
        manager = ConfigManager()
        
        result = manager.reload_config()
        
        assert result is None

    def test_create_default_config(self, temp_dir: Path) -> None:
        """Verify default config can be created."""
        manager = ConfigManager()
        config_path = temp_dir / "config.json"
        
        # Create default config
        config = manager.create_default_config(config_path)
        
        # Verify file exists
        assert config_path.exists()
        
        # Verify config has expected values
        assert config.version == "1.0.0"
        assert config.openai_api_key == "YOUR_API_KEY_HERE"
        assert config.log_level == "INFO"

    def test_save_and_load_preserves_api_key(self, temp_dir: Path) -> None:
        """Verify API key is encrypted on save and decrypted on load."""
        manager = ConfigManager()
        config_path = temp_dir / "config.json"
        
        if sys.platform == "win32":
            watch_dir = Path("C:\\test\\watch")
        else:
            watch_dir = Path("/test/watch")
        
        original_key = "sk-test-key-12345"
        
        config = Config(
            version="1.0.0",
            watch_directory=watch_dir,
            openai_api_key=original_key,
            log_level="INFO",
        )
        
        # Save config
        manager.save_config(config, config_path)
        
        # Read raw file
        with open(config_path, "r", encoding="utf-8") as f:
            saved_data = json.load(f)
        
        # Verify API key is encrypted in file
        assert saved_data["openai_api_key"] != original_key
        
        # Load config
        loaded_config = manager.load_config(config_path)
        
        # Verify API key is decrypted
        assert loaded_config.openai_api_key == original_key
