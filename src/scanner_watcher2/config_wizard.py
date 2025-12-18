"""
Interactive configuration wizard for Scanner-Watcher2.
"""

import os
import platform
from pathlib import Path

from scanner_watcher2.config import Config
from scanner_watcher2.infrastructure.config_manager import ConfigManager


class ConfigWizard:
    """Interactive configuration setup wizard."""

    def __init__(self) -> None:
        """Initialize configuration wizard."""
        self.config_manager = ConfigManager()

    def get_config_path(self) -> Path:
        """
        Get the default configuration path.

        Returns:
            Path to configuration file in %APPDATA%\\ScannerWatcher2\\config.json
        """
        if platform.system() == "Windows":
            appdata = os.environ.get("APPDATA", "")
            if not appdata:
                raise RuntimeError("APPDATA environment variable not set")
            config_dir = Path(appdata) / "ScannerWatcher2"
        else:
            # Fallback for non-Windows (development/testing)
            config_dir = Path.home() / ".scanner_watcher2"

        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir / "config.json"

    def prompt_watch_directory(self) -> Path:
        """
        Prompt user for watch directory path.

        Returns:
            Validated watch directory path
        """
        print("\n=== Watch Directory Configuration ===")
        print("Enter the directory path to monitor for scanned documents.")
        print("This should be an absolute path (e.g., C:\\Scans)")

        while True:
            path_str = input("\nWatch directory path: ").strip()

            if not path_str:
                print("Error: Path cannot be empty. Please try again.")
                continue

            try:
                path = Path(path_str)

                # Validate it's an absolute path
                if not path.is_absolute():
                    print("Error: Path must be absolute (e.g., C:\\Scans)")
                    continue

                # Check if directory exists, offer to create it
                if not path.exists():
                    create = input(
                        f"\nDirectory does not exist. Create it? (y/n): "
                    ).strip().lower()
                    if create == "y":
                        try:
                            path.mkdir(parents=True, exist_ok=True)
                            print(f"Created directory: {path}")
                        except Exception as e:
                            print(f"Error creating directory: {e}")
                            print("Please try a different path.")
                            continue
                    else:
                        print("Please enter an existing directory or allow creation.")
                        continue

                # Verify it's a directory
                if not path.is_dir():
                    print("Error: Path exists but is not a directory.")
                    continue

                return path

            except Exception as e:
                print(f"Error: Invalid path - {e}")
                continue

    def prompt_api_key(self) -> str:
        """
        Prompt user for OpenAI API key.

        Returns:
            OpenAI API key
        """
        print("\n=== OpenAI API Key Configuration ===")
        print("Enter your OpenAI API key.")
        print("This will be encrypted and stored securely using Windows DPAPI.")
        print("You can get an API key from: https://platform.openai.com/api-keys")

        while True:
            api_key = input("\nOpenAI API key: ").strip()

            if not api_key:
                print("Error: API key cannot be empty. Please try again.")
                continue

            # Basic validation - OpenAI keys typically start with "sk-"
            if not api_key.startswith("sk-"):
                confirm = input(
                    "\nWarning: API key doesn't start with 'sk-'. Continue anyway? (y/n): "
                ).strip().lower()
                if confirm != "y":
                    continue

            return api_key

    def prompt_file_prefix(self) -> str:
        """
        Prompt user for file prefix.

        Returns:
            File prefix for detecting scan files
        """
        print("\n=== File Prefix Configuration ===")
        print("Enter the prefix used to identify scanned documents.")
        print("Files starting with this prefix will be automatically processed.")
        print("Example: 'SCAN-' will match files like 'SCAN-document.pdf'")

        while True:
            prefix = input("\nFile prefix [default: SCAN-]: ").strip()

            # Default to SCAN-
            if not prefix:
                return "SCAN-"

            # Validate prefix is not empty
            if not prefix:
                print("Error: File prefix cannot be empty. Please try again.")
                continue

            # Check for invalid Windows filename characters
            invalid_chars = '<>:"|?*\\/\0'
            has_invalid = False
            for char in invalid_chars:
                if char in prefix:
                    print(f"Error: File prefix contains invalid character: '{char}'")
                    has_invalid = True
                    break
            
            if has_invalid:
                print("Invalid characters: < > : \" | ? * \\ / and null")
                continue

            return prefix

    def prompt_log_level(self) -> str:
        """
        Prompt user for log level.

        Returns:
            Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        print("\n=== Log Level Configuration ===")
        print("Select the logging level:")
        print("  1. DEBUG   - Detailed diagnostic information")
        print("  2. INFO    - General informational messages (recommended)")
        print("  3. WARNING - Warning messages only")
        print("  4. ERROR   - Error messages only")
        print("  5. CRITICAL - Critical errors only")

        level_map = {
            "1": "DEBUG",
            "2": "INFO",
            "3": "WARNING",
            "4": "ERROR",
            "5": "CRITICAL",
        }

        while True:
            choice = input("\nSelect log level (1-5) [default: 2]: ").strip()

            # Default to INFO
            if not choice:
                return "INFO"

            if choice in level_map:
                return level_map[choice]

            # Allow direct entry of level name
            if choice.upper() in level_map.values():
                return choice.upper()

            print("Error: Invalid choice. Please enter 1-5 or a valid log level name.")

    def validate_inputs(
        self, watch_directory: Path, api_key: str, file_prefix: str, log_level: str
    ) -> bool:
        """
        Validate all configuration inputs.

        Args:
            watch_directory: Watch directory path
            api_key: OpenAI API key
            file_prefix: File prefix for detection
            log_level: Log level

        Returns:
            True if all inputs are valid
        """
        errors = []

        # Validate watch directory
        if not watch_directory.is_absolute():
            errors.append("Watch directory must be an absolute path")
        if not watch_directory.exists():
            errors.append("Watch directory does not exist")
        if not watch_directory.is_dir():
            errors.append("Watch directory is not a directory")

        # Validate API key
        if not api_key or not api_key.strip():
            errors.append("API key cannot be empty")

        # Validate file prefix
        if not file_prefix or not file_prefix.strip():
            errors.append("File prefix cannot be empty")
        else:
            invalid_chars = '<>:"|?*\\/\0'
            for char in invalid_chars:
                if char in file_prefix:
                    errors.append(f"File prefix contains invalid character: '{char}'")
                    break

        # Validate log level
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if log_level.upper() not in valid_levels:
            errors.append(f"Log level must be one of {valid_levels}")

        if errors:
            print("\n=== Validation Errors ===")
            for error in errors:
                print(f"  - {error}")
            return False

        return True

    def display_summary(
        self, watch_directory: Path, api_key: str, file_prefix: str, log_level: str, config_path: Path
    ) -> None:
        """
        Display configuration summary.

        Args:
            watch_directory: Watch directory path
            api_key: OpenAI API key (will be masked)
            file_prefix: File prefix for detection
            log_level: Log level
            config_path: Path where configuration will be saved
        """
        print("\n" + "=" * 60)
        print("Configuration Summary")
        print("=" * 60)
        print(f"Watch Directory: {watch_directory}")
        print(f"OpenAI API Key:  {api_key[:7]}...{api_key[-4:]} (will be encrypted)")
        print(f"File Prefix:     {file_prefix}")
        print(f"Log Level:       {log_level}")
        print(f"Config File:     {config_path}")
        print("=" * 60)

    def run(self) -> bool:
        """
        Run the interactive configuration wizard.

        Returns:
            True if configuration was successfully created, False otherwise
        """
        print("\n" + "=" * 60)
        print("Scanner-Watcher2 Configuration Wizard")
        print("=" * 60)
        print("\nThis wizard will help you set up Scanner-Watcher2.")
        print("You can press Ctrl+C at any time to cancel.")

        try:
            # Get configuration path
            config_path = self.get_config_path()

            # Check if config already exists
            if config_path.exists():
                print(f"\nWarning: Configuration file already exists at:")
                print(f"  {config_path}")
                overwrite = input("\nOverwrite existing configuration? (y/n): ").strip().lower()
                if overwrite != "y":
                    print("\nConfiguration wizard cancelled.")
                    return False

            # Prompt for configuration values
            watch_directory = self.prompt_watch_directory()
            api_key = self.prompt_api_key()
            file_prefix = self.prompt_file_prefix()
            log_level = self.prompt_log_level()

            # Validate inputs
            if not self.validate_inputs(watch_directory, api_key, file_prefix, log_level):
                print("\nConfiguration validation failed. Please try again.")
                return False

            # Display summary and confirm
            self.display_summary(watch_directory, api_key, file_prefix, log_level, config_path)

            confirm = input("\nSave this configuration? (y/n): ").strip().lower()
            if confirm != "y":
                print("\nConfiguration wizard cancelled.")
                return False

            # Create configuration with custom file prefix
            from scanner_watcher2.config import ProcessingConfig
            
            config = Config(
                version="1.0.0",
                watch_directory=watch_directory,
                openai_api_key=api_key,
                log_level=log_level,
                processing=ProcessingConfig(file_prefix=file_prefix),
            )

            # Save configuration
            self.config_manager.save_config(config, config_path)

            print("\n" + "=" * 60)
            print("Configuration saved successfully!")
            print("=" * 60)
            print(f"\nConfiguration file: {config_path}")
            print("\nYou can now start Scanner-Watcher2 service.")
            print("The API key has been encrypted using Windows DPAPI.")

            return True

        except KeyboardInterrupt:
            print("\n\nConfiguration wizard cancelled by user.")
            return False
        except Exception as e:
            print(f"\n\nError during configuration: {e}")
            return False


def main() -> int:
    """
    Main entry point for configuration wizard.

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    wizard = ConfigWizard()
    success = wizard.run()
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())
