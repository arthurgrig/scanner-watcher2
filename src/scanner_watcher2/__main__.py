"""
Main application entry point for Scanner-Watcher2.

This module provides the main entry point for the application, supporting both
Windows service mode and console mode for development. It handles command-line
argument parsing, configuration loading, and component initialization.
"""

import argparse
import os
import platform
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path
from threading import Event

from scanner_watcher2.infrastructure.config_manager import ConfigManager
from scanner_watcher2.infrastructure.logger import Logger
from scanner_watcher2.service.orchestrator import ServiceOrchestrator


def get_log_dir() -> Path:
    """Get the log directory path for the current platform."""
    if platform.system() == "Windows":
        return Path(os.getenv("APPDATA", ".")) / "ScannerWatcher2" / "logs"
    return Path.home() / ".ScannerWatcher2" / "logs"


def write_crash_log(message: str) -> None:
    """
    Write to crash.log when the structured logger is unavailable.

    This is the last resort for diagnosing startup failures in windowless mode
    where print() goes nowhere and the structured logger hasn't been created yet.
    """
    try:
        log_dir = get_log_dir()
        log_dir.mkdir(parents=True, exist_ok=True)
        with open(log_dir / "crash.log", "a", encoding="utf-8") as f:
            ts = datetime.now(timezone.utc).isoformat()
            f.write(f"[{ts}] {message}\n")
    except Exception:
        pass


def parse_arguments() -> argparse.Namespace:
    """
    Parse command-line arguments.

    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(
        prog="scanner-watcher2",
        description="Windows-native legal document processing system with AI classification",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run interactive configuration wizard
  python -m scanner_watcher2 --configure

  # Run in console mode (development)
  python -m scanner_watcher2

  # Install Windows service
  python -m scanner_watcher2 --install-service

  # Start Windows service
  python -m scanner_watcher2 --start-service

  # Stop Windows service
  python -m scanner_watcher2 --stop-service

  # Remove Windows service
  python -m scanner_watcher2 --remove-service

  # Specify custom configuration file
  python -m scanner_watcher2 --config /path/to/config.json

  # Run with debug logging
  python -m scanner_watcher2 --log-level DEBUG
        """,
    )

    # Service management commands
    service_group = parser.add_mutually_exclusive_group()
    service_group.add_argument(
        "--install-service",
        action="store_true",
        help="Install as Windows service (Windows only)",
    )
    service_group.add_argument(
        "--start-service",
        action="store_true",
        help="Start Windows service (Windows only)",
    )
    service_group.add_argument(
        "--stop-service",
        action="store_true",
        help="Stop Windows service (Windows only)",
    )
    service_group.add_argument(
        "--remove-service",
        action="store_true",
        help="Remove Windows service (Windows only)",
    )
    service_group.add_argument(
        "--configure",
        action="store_true",
        help="Run interactive configuration wizard",
    )

    # Configuration options
    parser.add_argument(
        "--config",
        type=Path,
        help="Path to configuration file (default: %%APPDATA%%\\ScannerWatcher2\\config.json)",
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Override log level from configuration",
    )
    parser.add_argument(
        "--console",
        action="store_true",
        help="Run in console mode for development (default if no service commands)",
    )

    return parser.parse_args()


def get_default_config_path() -> Path:
    """
    Get default configuration file path.

    Returns:
        Default configuration path
    """
    if platform.system() == "Windows":
        appdata = os.getenv("APPDATA", ".")
        return Path(appdata) / "ScannerWatcher2" / "config.json"
    else:
        return Path.home() / ".ScannerWatcher2" / "config.json"


def run_console_mode(config_path: Path, log_level_override: str | None = None) -> None:
    """
    Run application in console mode.

    Args:
        config_path: Path to configuration file
        log_level_override: Optional log level override
    """
    log_dir = get_log_dir()

    # Create logger immediately with defaults so we can log startup errors
    logger = Logger(
        log_dir=log_dir,
        component="Main",
        log_level="DEBUG",
        log_to_event_log=False,
    )

    logger.info("Scanner-Watcher2 starting", config_path=str(config_path))
    print("Scanner-Watcher2 starting...")

    config_manager = ConfigManager()

    if not config_path.exists():
        logger.info("Config not found, creating default", path=str(config_path))
        write_crash_log(f"Config not found at {config_path}, creating default")
        try:
            config_manager.create_default_config(config_path)
            logger.info("Default config created — edit API key and watch directories, then restart",
                        path=str(config_path))
            write_crash_log(f"Default config created at {config_path} — edit and restart")
        except Exception as e:
            logger.critical("Failed to create default config", error=str(e))
            write_crash_log(f"Failed to create default config: {e}")
        sys.exit(0)

    # Load configuration
    try:
        config = config_manager.load_config(config_path)
        logger.info("Configuration loaded",
                     watch_directories=[str(d) for d in config.watch_directories],
                     file_prefixes=config.processing.file_prefixes,
                     model=config.ai.model)
    except Exception as e:
        logger.critical("Failed to load configuration", error=str(e),
                        config_path=str(config_path))
        write_crash_log(f"Failed to load config from {config_path}: {e}")
        sys.exit(1)

    if log_level_override:
        config.log_level = log_level_override

    # Reconfigure logger with actual config values
    logger = Logger(
        log_dir=log_dir,
        component="Main",
        log_level=config.log_level,
        max_file_size_mb=config.logging.max_file_size_mb,
        backup_count=config.logging.backup_count,
        log_to_event_log=False,
    )

    # Log watch directory status (don't exit — orchestrator handles missing dirs gracefully)
    for watch_dir in config.watch_directories:
        if not watch_dir.exists():
            logger.warning("Watch directory does not exist, orchestrator will skip it",
                           path=str(watch_dir))

    # Initialize and start orchestrator
    try:
        orchestrator = ServiceOrchestrator(config)
        logger.info("Orchestrator initialized")
    except Exception as e:
        logger.critical("Failed to initialize orchestrator", error=str(e))
        write_crash_log(f"Failed to initialize orchestrator: {e}")
        sys.exit(1)

    try:
        orchestrator.start()
        logger.info("Scanner-Watcher2 is running",
                     watch_directories=[str(d) for d in config.watch_directories],
                     file_prefixes=config.processing.file_prefixes)
    except Exception as e:
        logger.critical("Failed to start orchestrator", error=str(e))
        write_crash_log(f"Failed to start orchestrator: {e}")
        sys.exit(1)

    # Block until interrupted
    stop_event = Event()
    try:
        stop_event.wait()
    except KeyboardInterrupt:
        logger.info("Shutdown requested by user")
        try:
            orchestrator.stop(timeout=config.service.graceful_shutdown_timeout_seconds)
            logger.info("Orchestrator stopped cleanly")
        except Exception as e:
            logger.error("Error during shutdown", error=str(e))
        sys.exit(0)


def main() -> None:
    """Main entry point for the application."""
    try:
        args = parse_arguments()

        config_path = args.config if args.config else get_default_config_path()

        if args.configure:
            from scanner_watcher2.config_wizard import ConfigWizard

            wizard = ConfigWizard()
            success = wizard.run()
            sys.exit(0 if success else 1)

        if platform.system() == "Windows":
            if args.install_service:
                from scanner_watcher2.service.windows_service import install_service

                install_service()
                return
            elif args.start_service:
                from scanner_watcher2.service.windows_service import start_service

                start_service()
                return
            elif args.stop_service:
                from scanner_watcher2.service.windows_service import stop_service

                stop_service()
                return
            elif args.remove_service:
                from scanner_watcher2.service.windows_service import remove_service

                remove_service()
                return
        else:
            if any([args.install_service, args.start_service, args.stop_service, args.remove_service]):
                print("ERROR: Service management commands are only supported on Windows")
                sys.exit(1)

        run_console_mode(config_path, args.log_level)

    except SystemExit:
        raise
    except Exception as e:
        write_crash_log(f"FATAL unhandled exception: {type(e).__name__}: {e}")
        write_crash_log(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()
