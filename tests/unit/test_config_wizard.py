"""
Unit tests for configuration wizard.
"""

import os
import platform
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from scanner_watcher2.config_wizard import ConfigWizard


class TestConfigWizard:
    """Test configuration wizard functionality."""

    def test_get_config_path_windows(self) -> None:
        """Test getting configuration path on Windows."""
        wizard = ConfigWizard()

        if platform.system() == "Windows":
            with patch.dict(os.environ, {"APPDATA": "C:\\Users\\Test\\AppData\\Roaming"}):
                config_path = wizard.get_config_path()
                assert config_path == Path("C:\\Users\\Test\\AppData\\Roaming\\ScannerWatcher2\\config.json")
                assert config_path.parent.exists()

    def test_get_config_path_no_appdata(self) -> None:
        """Test getting configuration path when APPDATA is not set."""
        wizard = ConfigWizard()

        if platform.system() == "Windows":
            with patch.dict(os.environ, {"APPDATA": ""}, clear=True):
                with pytest.raises(RuntimeError, match="APPDATA environment variable not set"):
                    wizard.get_config_path()

    def test_validate_inputs_valid(self, tmp_path: Path) -> None:
        """Test validation with valid inputs."""
        wizard = ConfigWizard()

        watch_dir = tmp_path / "scans"
        watch_dir.mkdir()

        result = wizard.validate_inputs(
            watch_directory=watch_dir,
            api_key="sk-test123456789",
            file_prefix="SCAN-",
            log_level="INFO",
        )

        assert result is True

    def test_validate_inputs_relative_path(self, tmp_path: Path) -> None:
        """Test validation fails with relative path."""
        wizard = ConfigWizard()

        result = wizard.validate_inputs(
            watch_directory=Path("relative/path"),
            api_key="sk-test123456789",
            file_prefix="SCAN-",
            log_level="INFO",
        )

        assert result is False

    def test_validate_inputs_nonexistent_directory(self) -> None:
        """Test validation fails with nonexistent directory."""
        wizard = ConfigWizard()

        result = wizard.validate_inputs(
            watch_directory=Path("/nonexistent/directory"),
            api_key="sk-test123456789",
            file_prefix="SCAN-",
            log_level="INFO",
        )

        assert result is False

    def test_validate_inputs_empty_api_key(self, tmp_path: Path) -> None:
        """Test validation fails with empty API key."""
        wizard = ConfigWizard()

        watch_dir = tmp_path / "scans"
        watch_dir.mkdir()

        result = wizard.validate_inputs(
            watch_directory=watch_dir,
            api_key="",
            file_prefix="SCAN-",
            log_level="INFO",
        )

        assert result is False

    def test_validate_inputs_invalid_log_level(self, tmp_path: Path) -> None:
        """Test validation fails with invalid log level."""
        wizard = ConfigWizard()

        watch_dir = tmp_path / "scans"
        watch_dir.mkdir()

        result = wizard.validate_inputs(
            watch_directory=watch_dir,
            api_key="sk-test123456789",
            file_prefix="SCAN-",
            log_level="INVALID",
        )

        assert result is False

    def test_validate_inputs_file_not_directory(self, tmp_path: Path) -> None:
        """Test validation fails when path is a file, not a directory."""
        wizard = ConfigWizard()

        file_path = tmp_path / "file.txt"
        file_path.write_text("test")

        result = wizard.validate_inputs(
            watch_directory=file_path,
            api_key="sk-test123456789",
            file_prefix="SCAN-",
            log_level="INFO",
        )

        assert result is False

    @patch("builtins.input")
    def test_prompt_watch_directory_valid(self, mock_input: MagicMock, tmp_path: Path) -> None:
        """Test prompting for watch directory with valid input."""
        wizard = ConfigWizard()

        watch_dir = tmp_path / "scans"
        watch_dir.mkdir()

        mock_input.return_value = str(watch_dir)

        result = wizard.prompt_watch_directory()

        assert result == watch_dir

    @patch("builtins.input")
    def test_prompt_watch_directory_create(self, mock_input: MagicMock, tmp_path: Path) -> None:
        """Test prompting for watch directory with creation."""
        wizard = ConfigWizard()

        watch_dir = tmp_path / "new_scans"

        # First input: directory path, second input: confirm creation
        mock_input.side_effect = [str(watch_dir), "y"]

        result = wizard.prompt_watch_directory()

        assert result == watch_dir
        assert watch_dir.exists()

    @patch("builtins.input")
    def test_prompt_api_key_valid(self, mock_input: MagicMock) -> None:
        """Test prompting for API key with valid input."""
        wizard = ConfigWizard()

        mock_input.return_value = "sk-test123456789"

        result = wizard.prompt_api_key()

        assert result == "sk-test123456789"

    @patch("builtins.input")
    def test_prompt_api_key_warning(self, mock_input: MagicMock) -> None:
        """Test prompting for API key with warning for non-standard format."""
        wizard = ConfigWizard()

        # First input: non-standard key, second input: confirm
        mock_input.side_effect = ["test-key-123", "y"]

        result = wizard.prompt_api_key()

        assert result == "test-key-123"

    @patch("builtins.input")
    def test_prompt_log_level_default(self, mock_input: MagicMock) -> None:
        """Test prompting for log level with default."""
        wizard = ConfigWizard()

        mock_input.return_value = ""

        result = wizard.prompt_log_level()

        assert result == "INFO"

    @patch("builtins.input")
    def test_prompt_log_level_numeric(self, mock_input: MagicMock) -> None:
        """Test prompting for log level with numeric choice."""
        wizard = ConfigWizard()

        mock_input.return_value = "1"

        result = wizard.prompt_log_level()

        assert result == "DEBUG"

    @patch("builtins.input")
    def test_prompt_log_level_name(self, mock_input: MagicMock) -> None:
        """Test prompting for log level with level name."""
        wizard = ConfigWizard()

        mock_input.return_value = "WARNING"

        result = wizard.prompt_log_level()

        assert result == "WARNING"

    @patch("builtins.input")
    def test_prompt_file_prefix_default(self, mock_input: MagicMock) -> None:
        """Test prompting for file prefix with default."""
        wizard = ConfigWizard()

        mock_input.return_value = ""

        result = wizard.prompt_file_prefix()

        assert result == "SCAN-"

    @patch("builtins.input")
    def test_prompt_file_prefix_custom(self, mock_input: MagicMock) -> None:
        """Test prompting for file prefix with custom value."""
        wizard = ConfigWizard()

        mock_input.return_value = "DOC-"

        result = wizard.prompt_file_prefix()

        assert result == "DOC-"

    @patch("builtins.input")
    def test_prompt_file_prefix_invalid_chars(self, mock_input: MagicMock) -> None:
        """Test prompting for file prefix with invalid characters."""
        wizard = ConfigWizard()

        # First input: invalid prefix with <, second input: valid prefix
        mock_input.side_effect = ["SCAN<", "SCAN-"]

        result = wizard.prompt_file_prefix()

        assert result == "SCAN-"

    def test_validate_inputs_empty_file_prefix(self, tmp_path: Path) -> None:
        """Test validation fails with empty file prefix."""
        wizard = ConfigWizard()

        watch_dir = tmp_path / "scans"
        watch_dir.mkdir()

        result = wizard.validate_inputs(
            watch_directory=watch_dir,
            api_key="sk-test123456789",
            file_prefix="",
            log_level="INFO",
        )

        assert result is False

    def test_validate_inputs_invalid_file_prefix(self, tmp_path: Path) -> None:
        """Test validation fails with invalid file prefix characters."""
        wizard = ConfigWizard()

        watch_dir = tmp_path / "scans"
        watch_dir.mkdir()

        result = wizard.validate_inputs(
            watch_directory=watch_dir,
            api_key="sk-test123456789",
            file_prefix="SCAN<",
            log_level="INFO",
        )

        assert result is False

    def test_display_summary(self, tmp_path: Path, capsys) -> None:
        """Test displaying configuration summary."""
        wizard = ConfigWizard()

        watch_dir = tmp_path / "scans"
        watch_dir.mkdir()
        config_path = tmp_path / "config.json"

        wizard.display_summary(
            watch_directory=watch_dir,
            api_key="sk-test123456789abcdef",
            file_prefix="SCAN-",
            log_level="INFO",
            config_path=config_path,
        )

        captured = capsys.readouterr()
        assert "Configuration Summary" in captured.out
        assert str(watch_dir) in captured.out
        assert "sk-test...cdef" in captured.out
        assert "SCAN-" in captured.out
        assert "INFO" in captured.out
        assert str(config_path) in captured.out

    @patch("builtins.input")
    def test_run_success(self, mock_input: MagicMock, tmp_path: Path) -> None:
        """Test running wizard successfully."""
        wizard = ConfigWizard()

        watch_dir = tmp_path / "scans"
        watch_dir.mkdir()
        config_path = tmp_path / "config.json"

        # Mock get_config_path to use temp directory
        with patch.object(wizard, "get_config_path", return_value=config_path):
            # Inputs: watch_dir, api_key, file_prefix (default), log_level (default), confirm save
            mock_input.side_effect = [
                str(watch_dir),
                "sk-test123456789",
                "",  # Default file prefix
                "",  # Default log level
                "y",  # Confirm save
            ]

            result = wizard.run()

            assert result is True
            assert config_path.exists()

    @patch("builtins.input")
    def test_run_cancel(self, mock_input: MagicMock, tmp_path: Path) -> None:
        """Test cancelling wizard."""
        wizard = ConfigWizard()

        watch_dir = tmp_path / "scans"
        watch_dir.mkdir()
        config_path = tmp_path / "config.json"

        # Mock get_config_path to use temp directory
        with patch.object(wizard, "get_config_path", return_value=config_path):
            # Inputs: watch_dir, api_key, file_prefix (default), log_level (default), cancel save
            mock_input.side_effect = [
                str(watch_dir),
                "sk-test123456789",
                "",  # Default file prefix
                "",  # Default log level
                "n",  # Cancel save
            ]

            result = wizard.run()

            assert result is False
            assert not config_path.exists()

    @patch("builtins.input")
    def test_run_overwrite_existing(self, mock_input: MagicMock, tmp_path: Path) -> None:
        """Test overwriting existing configuration."""
        wizard = ConfigWizard()

        watch_dir = tmp_path / "scans"
        watch_dir.mkdir()
        config_path = tmp_path / "config.json"
        config_path.write_text('{"version": "1.0.0"}')

        # Mock get_config_path to use temp directory
        with patch.object(wizard, "get_config_path", return_value=config_path):
            # Inputs: confirm overwrite, watch_dir, api_key, file_prefix (default), log_level (default), confirm save
            mock_input.side_effect = [
                "y",  # Confirm overwrite
                str(watch_dir),
                "sk-test123456789",
                "",  # Default file prefix
                "",  # Default log level
                "y",  # Confirm save
            ]

            result = wizard.run()

            assert result is True
            assert config_path.exists()

    @patch("builtins.input")
    def test_run_keyboard_interrupt(self, mock_input: MagicMock, tmp_path: Path) -> None:
        """Test handling keyboard interrupt."""
        wizard = ConfigWizard()

        config_path = tmp_path / "config.json"

        # Mock get_config_path to use temp directory
        with patch.object(wizard, "get_config_path", return_value=config_path):
            mock_input.side_effect = KeyboardInterrupt()

            result = wizard.run()

            assert result is False
            assert not config_path.exists()
