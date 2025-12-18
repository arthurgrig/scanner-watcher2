"""
Unit tests for main application entry point.
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from scanner_watcher2.__main__ import (
    get_default_config_path,
    main,
    parse_arguments,
    run_console_mode,
)


class TestParseArguments:
    """Test command-line argument parsing."""

    def test_no_arguments(self) -> None:
        """Test parsing with no arguments."""
        with patch.object(sys, "argv", ["scanner-watcher2"]):
            args = parse_arguments()
            assert not args.install_service
            assert not args.start_service
            assert not args.stop_service
            assert not args.remove_service
            assert args.config is None
            assert args.log_level is None
            assert not args.console

    def test_install_service_argument(self) -> None:
        """Test parsing --install-service argument."""
        with patch.object(sys, "argv", ["scanner-watcher2", "--install-service"]):
            args = parse_arguments()
            assert args.install_service
            assert not args.start_service
            assert not args.stop_service
            assert not args.remove_service

    def test_config_argument(self) -> None:
        """Test parsing --config argument."""
        with patch.object(sys, "argv", ["scanner-watcher2", "--config", "/path/to/config.json"]):
            args = parse_arguments()
            assert args.config == Path("/path/to/config.json")

    def test_log_level_argument(self) -> None:
        """Test parsing --log-level argument."""
        with patch.object(sys, "argv", ["scanner-watcher2", "--log-level", "DEBUG"]):
            args = parse_arguments()
            assert args.log_level == "DEBUG"

    def test_console_argument(self) -> None:
        """Test parsing --console argument."""
        with patch.object(sys, "argv", ["scanner-watcher2", "--console"]):
            args = parse_arguments()
            assert args.console


class TestGetDefaultConfigPath:
    """Test default configuration path retrieval."""

    def test_default_config_path_with_appdata(self) -> None:
        """Test default config path when APPDATA is set."""
        with patch.dict("os.environ", {"APPDATA": "/test/appdata"}):
            path = get_default_config_path()
            assert path == Path("/test/appdata/ScannerWatcher2/config.json")

    def test_default_config_path_without_appdata(self) -> None:
        """Test default config path when APPDATA is not set."""
        with patch.dict("os.environ", {}, clear=True):
            path = get_default_config_path()
            assert path == Path("./ScannerWatcher2/config.json")


class TestRunConsoleMode:
    """Test console mode execution."""

    def test_run_console_mode_creates_default_config(self, tmp_path: Path) -> None:
        """Test that console mode creates default config if missing."""
        config_path = tmp_path / "config.json"

        with patch("scanner_watcher2.__main__.ConfigManager") as mock_config_manager:
            mock_manager = MagicMock()
            mock_config_manager.return_value = mock_manager

            with pytest.raises(SystemExit) as exc_info:
                run_console_mode(config_path)

            assert exc_info.value.code == 0
            mock_manager.create_default_config.assert_called_once_with(config_path)

    def test_run_console_mode_loads_existing_config(self, tmp_path: Path) -> None:
        """Test that console mode loads existing config."""
        config_path = tmp_path / "config.json"
        config_path.write_text('{"version": "1.0.0"}')

        watch_dir = tmp_path / "watch"
        watch_dir.mkdir()

        with patch("scanner_watcher2.__main__.ConfigManager") as mock_config_manager:
            mock_manager = MagicMock()
            mock_config_manager.return_value = mock_manager

            # Create mock config
            mock_config = MagicMock()
            mock_config.watch_directory = watch_dir
            mock_config.processing.file_prefix = "SCAN-"
            mock_config.log_level = "INFO"
            mock_config.ai.model = "gpt-4-vision-preview"
            mock_config.logging.max_file_size_mb = 10
            mock_config.logging.backup_count = 5
            mock_config.service.graceful_shutdown_timeout_seconds = 30
            mock_manager.load_config.return_value = mock_config

            with patch("scanner_watcher2.__main__.Logger"):
                with patch("scanner_watcher2.__main__.ServiceOrchestrator") as mock_orchestrator:
                    mock_orch = MagicMock()
                    mock_orchestrator.return_value = mock_orch

                    with patch("scanner_watcher2.__main__.Event") as mock_event:
                        mock_evt = MagicMock()
                        mock_event.return_value = mock_evt
                        mock_evt.wait.side_effect = KeyboardInterrupt()

                        with pytest.raises(SystemExit) as exc_info:
                            run_console_mode(config_path)

                        assert exc_info.value.code == 0
                        mock_manager.load_config.assert_called_once_with(config_path)
                        mock_orch.start.assert_called_once()
                        mock_orch.stop.assert_called_once()

    def test_run_console_mode_handles_invalid_config(self, tmp_path: Path) -> None:
        """Test that console mode handles invalid config gracefully."""
        config_path = tmp_path / "config.json"
        config_path.write_text("invalid json")

        with patch("scanner_watcher2.__main__.ConfigManager") as mock_config_manager:
            mock_manager = MagicMock()
            mock_config_manager.return_value = mock_manager
            mock_manager.load_config.side_effect = Exception("Invalid config")

            with pytest.raises(SystemExit) as exc_info:
                run_console_mode(config_path)

            assert exc_info.value.code == 1

    def test_run_console_mode_handles_missing_watch_directory(self, tmp_path: Path) -> None:
        """Test that console mode handles missing watch directory."""
        config_path = tmp_path / "config.json"
        config_path.write_text('{"version": "1.0.0"}')

        watch_dir = tmp_path / "nonexistent"

        with patch("scanner_watcher2.__main__.ConfigManager") as mock_config_manager:
            mock_manager = MagicMock()
            mock_config_manager.return_value = mock_manager

            # Create mock config with nonexistent watch directory
            mock_config = MagicMock()
            mock_config.watch_directory = watch_dir
            mock_config.processing.file_prefix = "SCAN-"
            mock_config.log_level = "INFO"
            mock_config.ai.model = "gpt-4-vision-preview"
            mock_config.logging.max_file_size_mb = 10
            mock_config.logging.backup_count = 5
            mock_manager.load_config.return_value = mock_config

            with patch("scanner_watcher2.__main__.Logger"):
                with pytest.raises(SystemExit) as exc_info:
                    run_console_mode(config_path)

                assert exc_info.value.code == 1


class TestMain:
    """Test main entry point."""

    def test_main_with_help_argument(self) -> None:
        """Test main with --help argument."""
        with patch.object(sys, "argv", ["scanner-watcher2", "--help"]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 0

    def test_main_console_mode(self, tmp_path: Path) -> None:
        """Test main in console mode."""
        config_path = tmp_path / "config.json"

        with patch.object(sys, "argv", ["scanner-watcher2", "--config", str(config_path)]):
            with patch("scanner_watcher2.__main__.run_console_mode") as mock_run:
                mock_run.side_effect = SystemExit(0)

                with pytest.raises(SystemExit):
                    main()

                mock_run.assert_called_once_with(config_path, None)

    def test_main_with_log_level_override(self, tmp_path: Path) -> None:
        """Test main with log level override."""
        config_path = tmp_path / "config.json"

        with patch.object(
            sys, "argv", ["scanner-watcher2", "--config", str(config_path), "--log-level", "DEBUG"]
        ):
            with patch("scanner_watcher2.__main__.run_console_mode") as mock_run:
                mock_run.side_effect = SystemExit(0)

                with pytest.raises(SystemExit):
                    main()

                mock_run.assert_called_once_with(config_path, "DEBUG")
