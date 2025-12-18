"""
Configuration management for loading and validating configuration.
"""

import base64
import json
import platform
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from scanner_watcher2.config import Config

# Windows DPAPI is only available on Windows
if platform.system() == "Windows":
    import win32crypt  # type: ignore
else:
    win32crypt = None


class ConfigManager:
    """Load, validate, and manage application configuration."""

    def __init__(self) -> None:
        """Initialize configuration manager."""
        self._last_config: Config | None = None
        self._last_config_path: Path | None = None

    def load_config(self, config_path: Path) -> Config:
        """
        Load and validate configuration.

        Args:
            config_path: Path to configuration file

        Returns:
            Validated configuration

        Raises:
            FileNotFoundError: If configuration file does not exist
            ValidationError: If configuration is invalid
            ValueError: If configuration file is malformed
        """
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config_data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in configuration file: {e}") from e

        # Decrypt API key if it's encrypted
        if "openai_api_key" in config_data and config_data["openai_api_key"]:
            try:
                # Try to decrypt - if it fails, assume it's plain text
                config_data["openai_api_key"] = self.decrypt_api_key(
                    config_data["openai_api_key"]
                )
            except Exception:
                # If decryption fails, assume it's already plain text
                pass

        # Convert string paths to Path objects
        if "watch_directory" in config_data:
            config_data["watch_directory"] = Path(config_data["watch_directory"])

        if "processing" in config_data and "temp_directory" in config_data["processing"]:
            if config_data["processing"]["temp_directory"]:
                config_data["processing"]["temp_directory"] = Path(
                    config_data["processing"]["temp_directory"]
                )

        # Validate and create config
        config = Config(**config_data)

        # Cache for hot-reload support
        self._last_config = config
        self._last_config_path = config_path

        return config

    def save_config(self, config: Config, config_path: Path) -> None:
        """
        Save configuration to file.

        Args:
            config: Configuration to save
            config_path: Path to save configuration

        Raises:
            OSError: If unable to write configuration file
        """
        # Convert config to dict
        config_dict = config.model_dump(mode="json")

        # Encrypt API key before saving
        if "openai_api_key" in config_dict and config_dict["openai_api_key"]:
            config_dict["openai_api_key"] = self.encrypt_api_key(
                config_dict["openai_api_key"]
            )

        # Convert Path objects to strings
        if "watch_directory" in config_dict:
            config_dict["watch_directory"] = str(config_dict["watch_directory"])

        if (
            "processing" in config_dict
            and "temp_directory" in config_dict["processing"]
            and config_dict["processing"]["temp_directory"]
        ):
            config_dict["processing"]["temp_directory"] = str(
                config_dict["processing"]["temp_directory"]
            )

        # Ensure parent directory exists
        config_path.parent.mkdir(parents=True, exist_ok=True)

        # Write configuration
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config_dict, f, indent=2)

        # Update cache
        self._last_config = config
        self._last_config_path = config_path

    def reload_config(self) -> Config | None:
        """
        Reload configuration from last loaded path.

        Returns:
            Reloaded configuration, or None if no config was previously loaded

        Raises:
            FileNotFoundError: If configuration file no longer exists
            ValidationError: If configuration is invalid
            ValueError: If configuration file is malformed
        """
        if self._last_config_path is None:
            return None

        return self.load_config(self._last_config_path)

    def encrypt_api_key(self, api_key: str) -> str:
        """
        Encrypt API key using Windows DPAPI.

        On non-Windows platforms, returns base64-encoded key (not secure).

        Args:
            api_key: Plain text API key

        Returns:
            Encrypted API key (base64-encoded)

        Raises:
            ValueError: If API key is empty
        """
        if not api_key or not api_key.strip():
            raise ValueError("API key cannot be empty")

        if platform.system() == "Windows" and win32crypt is not None:
            # Use Windows DPAPI for encryption
            encrypted_bytes = win32crypt.CryptProtectData(
                api_key.encode("utf-8"),
                "ScannerWatcher2 API Key",
                None,
                None,
                None,
                0,
            )
            return base64.b64encode(encrypted_bytes).decode("ascii")
        else:
            # Fallback for non-Windows: just base64 encode (not secure)
            return base64.b64encode(api_key.encode("utf-8")).decode("ascii")

    def decrypt_api_key(self, encrypted: str) -> str:
        """
        Decrypt API key.

        On non-Windows platforms, decodes base64-encoded key.

        Args:
            encrypted: Encrypted API key (base64-encoded)

        Returns:
            Plain text API key

        Raises:
            ValueError: If encrypted key is invalid or cannot be decrypted
        """
        if not encrypted or not encrypted.strip():
            raise ValueError("Encrypted API key cannot be empty")

        try:
            encrypted_bytes = base64.b64decode(encrypted)
        except Exception as e:
            raise ValueError(f"Invalid base64 encoding: {e}") from e

        if platform.system() == "Windows" and win32crypt is not None:
            # Use Windows DPAPI for decryption
            try:
                _, decrypted_bytes = win32crypt.CryptUnprotectData(
                    encrypted_bytes, None, None, None, 0
                )
                return decrypted_bytes.decode("utf-8")
            except Exception as e:
                raise ValueError(f"Failed to decrypt API key: {e}") from e
        else:
            # Fallback for non-Windows: just base64 decode
            try:
                return encrypted_bytes.decode("utf-8")
            except Exception as e:
                raise ValueError(f"Failed to decode API key: {e}") from e

    def create_default_config(self, config_path: Path) -> Config:
        """
        Create a default configuration file with placeholder values.

        Args:
            config_path: Path where configuration should be created

        Returns:
            Default configuration

        Raises:
            OSError: If unable to write configuration file
        """
        # Create default config with placeholder values
        if platform.system() == "Windows":
            default_watch_dir = Path("C:\\Scans")
        else:
            default_watch_dir = Path("/tmp/scans")

        default_config = Config(
            version="1.0.0",
            watch_directory=default_watch_dir,
            openai_api_key="YOUR_API_KEY_HERE",
            log_level="INFO",
        )

        # Save the default config
        self.save_config(default_config, config_path)

        return default_config
