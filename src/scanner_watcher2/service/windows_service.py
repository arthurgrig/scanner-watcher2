"""
Windows service layer for native Windows service integration.
"""

import os
import platform
import sys
from pathlib import Path
from threading import Event

from scanner_watcher2.config import Config
from scanner_watcher2.infrastructure.config_manager import ConfigManager
from scanner_watcher2.infrastructure.logger import Logger
from scanner_watcher2.service.orchestrator import ServiceOrchestrator

# Only import pywin32 on Windows
if platform.system() == "Windows":
    try:
        import win32event
        import win32service
        import win32serviceutil

        # Create base class for Windows service
        _ServiceBase = win32serviceutil.ServiceFramework
    except ImportError:
        # pywin32 not available - service functionality will be limited
        _ServiceBase = object
else:
    _ServiceBase = object


class ScannerWatcher2Service(_ServiceBase):
    """Provides native Windows service integration using pywin32."""

    # Service configuration
    _svc_name_ = "ScannerWatcher2"
    _svc_display_name_ = "Scanner Watcher 2"
    _svc_description_ = "Automated legal document processing and classification service"

    def __init__(self, args=None) -> None:
        """
        Initialize Windows service.

        Args:
            args: Service arguments (provided by Windows Service Manager)
        """
        # Initialize base class if on Windows with pywin32
        if platform.system() == "Windows" and _ServiceBase != object:
            super().__init__(args)

        # Create stop event
        if platform.system() == "Windows":
            try:
                self.stop_event = win32event.CreateEvent(None, 0, 0, None)
            except NameError:
                self.stop_event = Event()
        else:
            self.stop_event = Event()

        # Initialize components (will be set in main())
        self.logger: Logger | None = None
        self.orchestrator: ServiceOrchestrator | None = None
        self.config: Config | None = None

    def SvcStop(self) -> None:
        """Handle service stop request from Windows Service Manager."""
        if self.logger:
            self.logger.info("Service stop requested")

        # Report service is stopping
        if platform.system() == "Windows":
            try:
                self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
            except (NameError, AttributeError):
                pass

        # Signal stop event
        if platform.system() == "Windows" and hasattr(win32event, "SetEvent"):
            try:
                win32event.SetEvent(self.stop_event)
            except (NameError, AttributeError):
                pass
        else:
            if isinstance(self.stop_event, Event):
                self.stop_event.set()

        if self.logger:
            self.logger.info("Service stop signal sent")

    def SvcDoRun(self) -> None:
        """Main service entry point called by Windows Service Manager."""
        try:
            # Log service start to Windows Event Log
            if platform.system() == "Windows":
                try:
                    import win32evtlogutil

                    win32evtlogutil.ReportEvent(
                        self._svc_name_,
                        1,
                        eventType=win32event.EVENTLOG_INFORMATION_TYPE,
                        strings=["ScannerWatcher2 service started"],
                    )
                except (ImportError, NameError):
                    pass

            # Run main application
            self.main()

        except Exception as e:
            # Log critical error to Windows Event Log
            if platform.system() == "Windows":
                try:
                    import win32evtlogutil

                    win32evtlogutil.ReportEvent(
                        self._svc_name_,
                        1,
                        eventType=win32event.EVENTLOG_ERROR_TYPE,
                        strings=[f"ScannerWatcher2 service encountered critical error: {str(e)}"],
                    )
                except (ImportError, NameError):
                    pass

            if self.logger:
                self.logger.critical("Service encountered critical error", error=str(e))

            raise

    def main(self) -> None:
        """Initialize and run application."""
        try:
            # Load configuration
            config_manager = ConfigManager()
            if platform.system() == "Windows":
                config_path = Path(os.getenv("APPDATA", ".")) / "ScannerWatcher2" / "config.json"
            else:
                # Non-Windows fallback (development/testing)
                config_path = Path.home() / ".ScannerWatcher2" / "config.json"

            if not config_path.exists():
                # Create default configuration
                config_manager.create_default_config(config_path)

            self.config = config_manager.load_config(config_path)

            # Initialize logger
            if platform.system() == "Windows":
                log_dir = Path(os.getenv("APPDATA", ".")) / "ScannerWatcher2" / "logs"
            else:
                # Non-Windows fallback (development/testing)
                log_dir = Path.home() / ".ScannerWatcher2" / "logs"
            self.logger = Logger(
                log_dir=log_dir,
                component="WindowsService",
                log_level=self.config.log_level,
                max_file_size_mb=self.config.logging.max_file_size_mb,
                backup_count=self.config.logging.backup_count,
                log_to_event_log=self.config.logging.log_to_event_log,
            )

            self.logger.info("ScannerWatcher2 service starting")

            # Initialize orchestrator
            self.orchestrator = ServiceOrchestrator(self.config)

            # Start orchestrator
            self.orchestrator.start()
            self.logger.info("Service orchestrator started")

            # Run orchestrator with stop event
            if isinstance(self.stop_event, Event):
                self.orchestrator.run(self.stop_event)
            else:
                # Windows event handle - convert to threading.Event
                import threading

                threading_event = threading.Event()

                def wait_for_windows_event():
                    if platform.system() == "Windows":
                        try:
                            win32event.WaitForSingleObject(self.stop_event, win32event.INFINITE)
                            threading_event.set()
                        except (NameError, AttributeError):
                            pass

                import threading

                wait_thread = threading.Thread(target=wait_for_windows_event, daemon=True)
                wait_thread.start()
                self.orchestrator.run(threading_event)

            self.logger.info("ScannerWatcher2 service stopped")

        except Exception as e:
            if self.logger:
                self.logger.critical("Failed to initialize service", error=str(e))
            raise


def install_service() -> None:
    """Install the Windows service."""
    if platform.system() != "Windows":
        print("Service installation is only supported on Windows")
        return

    try:
        win32serviceutil.HandleCommandLine(
            ScannerWatcher2Service,
            argv=["", "install"],
        )
        print(f"Service '{ScannerWatcher2Service._svc_display_name_}' installed successfully")
    except Exception as e:
        print(f"Failed to install service: {e}")
        sys.exit(1)


def start_service() -> None:
    """Start the Windows service."""
    if platform.system() != "Windows":
        print("Service management is only supported on Windows")
        return

    try:
        win32serviceutil.HandleCommandLine(
            ScannerWatcher2Service,
            argv=["", "start"],
        )
        print(f"Service '{ScannerWatcher2Service._svc_display_name_}' started successfully")
    except Exception as e:
        print(f"Failed to start service: {e}")
        sys.exit(1)


def stop_service() -> None:
    """Stop the Windows service."""
    if platform.system() != "Windows":
        print("Service management is only supported on Windows")
        return

    try:
        win32serviceutil.HandleCommandLine(
            ScannerWatcher2Service,
            argv=["", "stop"],
        )
        print(f"Service '{ScannerWatcher2Service._svc_display_name_}' stopped successfully")
    except Exception as e:
        print(f"Failed to stop service: {e}")
        sys.exit(1)


def remove_service() -> None:
    """Remove the Windows service."""
    if platform.system() != "Windows":
        print("Service removal is only supported on Windows")
        return

    try:
        win32serviceutil.HandleCommandLine(
            ScannerWatcher2Service,
            argv=["", "remove"],
        )
        print(f"Service '{ScannerWatcher2Service._svc_display_name_}' removed successfully")
    except Exception as e:
        print(f"Failed to remove service: {e}")
        sys.exit(1)


def main() -> None:
    """
    Main entry point for service management.

    Supports command-line arguments:
    - --install-service: Install the Windows service
    - --start-service: Start the Windows service
    - --stop-service: Stop the Windows service
    - --remove-service: Remove the Windows service
    - (no args): Run as console application for development
    """
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower()

        if arg == "--install-service":
            install_service()
        elif arg == "--start-service":
            start_service()
        elif arg == "--stop-service":
            stop_service()
        elif arg == "--remove-service":
            remove_service()
        elif platform.system() == "Windows":
            # Let pywin32 handle service-related commands
            try:
                win32serviceutil.HandleCommandLine(ScannerWatcher2Service)
            except NameError:
                print("pywin32 not available - service functionality disabled")
                sys.exit(1)
        else:
            print("Unknown argument or Windows-only command on non-Windows platform")
            sys.exit(1)
    else:
        # Run as console application for development
        print("Running in console mode (development)")
        service = ScannerWatcher2Service()
        try:
            service.main()
        except KeyboardInterrupt:
            print("\nShutting down...")
            service.SvcStop()


if __name__ == "__main__":
    main()
