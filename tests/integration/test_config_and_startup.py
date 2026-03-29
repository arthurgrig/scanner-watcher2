"""
Integration tests verifying config loading and application startup.

Tests the full pipeline: JSON config file -> ConfigManager -> Config model ->
ServiceOrchestrator init -> start -> health check -> stop.
"""

import json
import sys
import time
from pathlib import Path
from unittest.mock import patch

import pytest

from scanner_watcher2.config import Config, ProcessingConfig
from scanner_watcher2.infrastructure.config_manager import ConfigManager
from scanner_watcher2.service.orchestrator import ServiceOrchestrator


def _abs_path(*parts: str) -> str:
    """Return a platform-appropriate absolute path string."""
    if sys.platform == "win32":
        return "C:\\" + "\\".join(parts)
    return "/" + "/".join(parts)


class TestConfigLoadFormats:
    """Verify various config JSON formats load into a valid Config object."""

    def test_load_new_format_with_lists(self, temp_dir: Path) -> None:
        """Config with watch_directories[] and file_prefixes[] loads correctly."""
        watch_dir = temp_dir / "scans"
        watch_dir.mkdir()

        config_path = temp_dir / "config.json"
        config_path.write_text(json.dumps({
            "version": "1.0.0",
            "watch_directories": [str(watch_dir)],
            "openai_api_key": "sk-test-key",
            "log_level": "INFO",
            "processing": {
                "file_prefixes": ["SCAN-", "DOC-"],
                "pages_to_extract": 3,
                "retry_attempts": 3,
                "retry_delay_seconds": 5,
            },
        }))

        config = ConfigManager().load_config(config_path)

        assert config.watch_directories == [watch_dir]
        assert config.processing.file_prefixes == ["SCAN-", "DOC-"]
        assert config.log_level == "INFO"

    def test_load_legacy_format_with_singular_fields(self, temp_dir: Path) -> None:
        """Config with old watch_directory and file_prefix is migrated automatically."""
        watch_dir = temp_dir / "scans"
        watch_dir.mkdir()

        config_path = temp_dir / "config.json"
        config_path.write_text(json.dumps({
            "version": "1.0.0",
            "watch_directory": str(watch_dir),
            "openai_api_key": "sk-test-key",
            "log_level": "DEBUG",
            "processing": {
                "file_prefix": "SCAN-",
            },
        }))

        config = ConfigManager().load_config(config_path)

        assert config.watch_directories == [watch_dir]
        assert config.processing.file_prefixes == ["SCAN-"]
        assert config.log_level == "DEBUG"

    def test_load_multiple_directories_and_prefixes(self, temp_dir: Path) -> None:
        """Config with multiple watch dirs and prefixes loads correctly."""
        dirs = []
        for name in ("scans_a", "scans_b", "scans_c"):
            d = temp_dir / name
            d.mkdir()
            dirs.append(d)

        config_path = temp_dir / "config.json"
        config_path.write_text(json.dumps({
            "version": "1.0.0",
            "watch_directories": [str(d) for d in dirs],
            "openai_api_key": "sk-test-key",
            "log_level": "INFO",
            "processing": {
                "file_prefixes": ["SCAN-", "DOC-", "IMG-"],
            },
        }))

        config = ConfigManager().load_config(config_path)

        assert config.watch_directories == dirs
        assert config.processing.file_prefixes == ["SCAN-", "DOC-", "IMG-"]

    def test_load_config_template_structure(self, temp_dir: Path) -> None:
        """The shipped config_template.json parses without errors (after fixing paths)."""
        template_path = Path(__file__).parents[2] / "config_template.json"
        if not template_path.exists():
            pytest.skip("config_template.json not found in repo root")

        with open(template_path, encoding="utf-8") as f:
            template_data = json.load(f)

        watch_dir = temp_dir / "template_test"
        watch_dir.mkdir()
        template_data["watch_directories"] = [str(watch_dir)]
        template_data["openai_api_key"] = "sk-template-test"

        config_path = temp_dir / "config.json"
        config_path.write_text(json.dumps(template_data))

        config = ConfigManager().load_config(config_path)

        assert len(config.watch_directories) == 1
        assert config.watch_directories[0] == watch_dir
        assert config.processing.file_prefixes == ["SCAN-", "DOC-", "IMG-"]
        assert config.ai.model == "gpt-4o"

    def test_save_and_reload_round_trip(self, temp_dir: Path) -> None:
        """Config saved via ConfigManager can be reloaded identically."""
        watch_dir = temp_dir / "scans"
        watch_dir.mkdir()

        original = Config(
            version="1.0.0",
            watch_directories=[watch_dir],
            openai_api_key="sk-round-trip-key",
            log_level="WARNING",
            processing=ProcessingConfig(
                file_prefixes=["LEGAL-", "CASE-"],
                pages_to_extract=5,
            ),
        )

        manager = ConfigManager()
        config_path = temp_dir / "config.json"
        manager.save_config(original, config_path)
        reloaded = manager.load_config(config_path)

        assert reloaded.version == original.version
        assert reloaded.watch_directories == original.watch_directories
        assert reloaded.openai_api_key == original.openai_api_key
        assert reloaded.log_level == original.log_level
        assert reloaded.processing.file_prefixes == original.processing.file_prefixes
        assert reloaded.processing.pages_to_extract == original.processing.pages_to_extract
        assert reloaded.ai.model == original.ai.model

    def test_saved_json_uses_plural_field_names(self, temp_dir: Path) -> None:
        """Verify the persisted JSON uses the new plural field names."""
        watch_dir = temp_dir / "scans"
        watch_dir.mkdir()

        config = Config(
            version="1.0.0",
            watch_directories=[watch_dir],
            openai_api_key="sk-test",
            log_level="INFO",
        )

        config_path = temp_dir / "config.json"
        ConfigManager().save_config(config, config_path)

        with open(config_path, encoding="utf-8") as f:
            raw = json.load(f)

        assert "watch_directories" in raw
        assert "watch_directory" not in raw
        assert isinstance(raw["watch_directories"], list)
        assert "file_prefixes" in raw["processing"]
        assert "file_prefix" not in raw["processing"]


class TestOrchestratorStartup:
    """Verify the orchestrator initializes, starts, and stops with a real config."""

    def _make_config(self, watch_dir: Path) -> Config:
        return Config(
            version="1.0.0",
            watch_directories=[watch_dir],
            openai_api_key="sk-test-startup",
            log_level="DEBUG",
            processing=ProcessingConfig(file_prefixes=["SCAN-"]),
        )

    def test_orchestrator_starts_and_stops(self, watch_directory: Path) -> None:
        """Orchestrator initializes, starts watchers, and shuts down cleanly."""
        config = self._make_config(watch_directory)
        orchestrator = ServiceOrchestrator(config)

        orchestrator.start()
        try:
            assert len(orchestrator.directory_watchers) == 1
            assert orchestrator.directory_watchers[0].watch_path == watch_directory
        finally:
            orchestrator.stop(timeout=5)

        assert orchestrator._stop_event.is_set()

    def test_orchestrator_health_check_after_start(self, watch_directory: Path) -> None:
        """Health check returns healthy status right after startup."""
        config = self._make_config(watch_directory)
        orchestrator = ServiceOrchestrator(config)

        orchestrator.start()
        try:
            health = orchestrator.health_check()
            assert health.is_healthy is True
            assert health.watch_directory_accessible is True
            assert health.config_valid is True
            assert health.consecutive_failures == 0
        finally:
            orchestrator.stop(timeout=5)

    def test_orchestrator_multiple_directories(self, temp_dir: Path) -> None:
        """Orchestrator creates a watcher per valid directory."""
        dirs = []
        for name in ("dir_a", "dir_b"):
            d = temp_dir / name
            d.mkdir()
            dirs.append(d)

        config = Config(
            version="1.0.0",
            watch_directories=dirs,
            openai_api_key="sk-test-multi",
            log_level="INFO",
            processing=ProcessingConfig(file_prefixes=["SCAN-", "DOC-"]),
        )

        orchestrator = ServiceOrchestrator(config)
        orchestrator.start()
        try:
            assert len(orchestrator.directory_watchers) == 2
            watched_paths = {w.watch_path for w in orchestrator.directory_watchers}
            assert watched_paths == set(dirs)
        finally:
            orchestrator.stop(timeout=5)

    def test_orchestrator_skips_missing_directory(self, temp_dir: Path) -> None:
        """Orchestrator skips non-existent directories but starts for valid ones."""
        valid_dir = temp_dir / "exists"
        valid_dir.mkdir()
        missing_dir = temp_dir / "does_not_exist"

        config = Config(
            version="1.0.0",
            watch_directories=[valid_dir, missing_dir],
            openai_api_key="sk-test-skip",
            log_level="INFO",
        )

        orchestrator = ServiceOrchestrator(config)
        orchestrator.start()
        try:
            assert len(orchestrator.directory_watchers) == 1
            assert orchestrator.directory_watchers[0].watch_path == valid_dir
        finally:
            orchestrator.stop(timeout=5)

    def test_orchestrator_fails_if_no_valid_directories(self, temp_dir: Path) -> None:
        """Orchestrator raises RuntimeError if all watch directories are missing."""
        config = Config(
            version="1.0.0",
            watch_directories=[temp_dir / "gone_a", temp_dir / "gone_b"],
            openai_api_key="sk-test-none",
            log_level="INFO",
        )

        orchestrator = ServiceOrchestrator(config)
        with pytest.raises(RuntimeError, match="No valid watch directories"):
            orchestrator.start()

    def test_config_to_orchestrator_end_to_end(self, temp_dir: Path) -> None:
        """Full pipeline: write JSON -> load via ConfigManager -> start orchestrator."""
        watch_dir = temp_dir / "e2e_scans"
        watch_dir.mkdir()

        config_path = temp_dir / "config.json"
        config_path.write_text(json.dumps({
            "version": "1.0.0",
            "watch_directories": [str(watch_dir)],
            "openai_api_key": "sk-e2e-key",
            "log_level": "INFO",
            "processing": {
                "file_prefixes": ["SCAN-"],
            },
        }))

        config = ConfigManager().load_config(config_path)

        assert config.watch_directories == [watch_dir]
        assert config.processing.file_prefixes == ["SCAN-"]

        orchestrator = ServiceOrchestrator(config)
        orchestrator.start()
        try:
            health = orchestrator.health_check()
            assert health.is_healthy is True
        finally:
            orchestrator.stop(timeout=5)
