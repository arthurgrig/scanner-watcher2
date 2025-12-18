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
from pathlib import Path
from threading import Event

from scanner_watcher2.infrastructure.config_manager import ConfigManager
from scanner_watcher2.infrastructure.logger import Logger
from scanner_watcher2.service.orchestrator import ServiceOrchestrator


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
    appdata = os.getenv("APPDATA", ".")
    return Path(appdata) / "ScannerWatcher2" / "config.json"


def run_console_mode(config_path: Path, log_level_override: str | None = None) -> None:
    """
    Run application in console mode for development.

    Args:
        config_path: Path to configuration file
        log_level_override: Optional log level override
    """
    print("=" * 70)
    print("Scanner-Watcher2 - Console Mode")
    print("=" * 70)
    print()

    # Initialize configuration manager
    config_manager = ConfigManager()

    # Check if configuration exists
    if not config_path.exists():
        print(f"Configuration file not found: {config_path}")
        print("Creating default configuration...")
        try:
            config_manager.create_default_config(config_path)
            print(f"Default configuration created at: {config_path}")
            print()
            print("IMPORTANT: Please edit the configuration file to:")
            print("  1. Set your OpenAI API key")
            print("  2. Configure the watch directory path")
            print("  3. Adjust other settings as needed")
            print()
            print("Then run the application again.")
            sys.exit(0)
        except Exception as e:
            print(f"Failed to create default configuration: {e}")
            sys.exit(1)

    # Load configuration
    print(f"Loading configuration from: {config_path}")
    try:
        config = config_manager.load_config(config_path)
        print("Configuration loaded successfully")
    except Exception as e:
        print(f"Failed to load configuration: {e}")
        sys.exit(1)

    # Override log level if specified
    if log_level_override:
        config.log_level = log_level_override
        print(f"Log level overridden to: {log_level_override}")

    print()
    print("Configuration:")
    print(f"  Watch Directory: {config.watch_directory}")
    print(f"  File Prefix: {config.processing.file_prefix}")
    print(f"  Log Level: {config.log_level}")
    print(f"  AI Model: {config.ai.model}")
    print()

    # Initialize logger
    log_dir = Path(os.getenv("APPDATA", ".")) / "ScannerWatcher2" / "logs"
    logger = Logger(
        log_dir=log_dir,
        component="Main",
        log_level=config.log_level,
        max_file_size_mb=config.logging.max_file_size_mb,
        backup_count=config.logging.backup_count,
        log_to_event_log=False,  # Disable Windows Event Log in console mode
    )

    logger.info("Scanner-Watcher2 starting in console mode")
    print(f"Logs will be written to: {log_dir}")
    print()

    # Validate watch directory
    if not config.watch_directory.exists():
        logger.error("Watch directory does not exist", path=str(config.watch_directory))
        print(f"ERROR: Watch directory does not exist: {config.watch_directory}")
        print("Please create the directory or update the configuration.")
        sys.exit(1)

    # Initialize orchestrator
    print("Initializing service orchestrator...")
    try:
        orchestrator = ServiceOrchestrator(config)
        logger.info("Service orchestrator initialized")
    except Exception as e:
        logger.critical("Failed to initialize orchestrator", error=str(e))
        print(f"Failed to initialize orchestrator: {e}")
        sys.exit(1)

    # Start orchestrator
    print("Starting service orchestrator...")
    try:
        orchestrator.start()
        logger.info("Service orchestrator started")
        print()
        print("=" * 70)
        print("Scanner-Watcher2 is now running")
        print("=" * 70)
        print(f"Monitoring: {config.watch_directory}")
        print(f"Looking for files with prefix: {config.processing.file_prefix}")
        print()
        print("Press Ctrl+C to stop")
        print()
    except Exception as e:
        logger.critical("Failed to start orchestrator", error=str(e))
        print(f"Failed to start orchestrator: {e}")
        sys.exit(1)

    # Create stop event and wait for keyboard interrupt
    stop_event = Event()
    try:
        stop_event.wait()
    except KeyboardInterrupt:
        print()
        print("=" * 70)
        print("Shutdown requested...")
        print("=" * 70)
        logger.info("Shutdown requested by user")

        # Stop orchestrator
        print("Stopping service orchestrator...")
        try:
            orchestrator.stop(timeout=config.service.graceful_shutdown_timeout_seconds)
            logger.info("Service orchestrator stopped")
            print("Service orchestrator stopped successfully")
        except Exception as e:
            logger.error("Error during shutdown", error=str(e))
            print(f"Error during shutdown: {e}")

        print()
        print("Scanner-Watcher2 stopped")
        sys.exit(0)


def main() -> None:
    """Main entry point for the application."""
    args = parse_arguments()

    # Get configuration path
    config_path = args.config if args.config else get_default_config_path()

    # Handle configuration wizard
    if args.configure:
        from scanner_watcher2.config_wizard import ConfigWizard

        wizard = ConfigWizard()
        success = wizard.run()
        sys.exit(0 if success else 1)

    # Handle service management commands (Windows only)
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
        # Non-Windows platform
        if any([args.install_service, args.start_service, args.stop_service, args.remove_service]):
            print("ERROR: Service management commands are only supported on Windows")
            sys.exit(1)

    # Run in console mode (default)
    run_console_mode(config_path, args.log_level)


if __name__ == "__main__":
    main()
