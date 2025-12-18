Scanner-Watcher2 - Legal Document Processing System
====================================================

Version: 1.0.0

OVERVIEW
--------
Scanner-Watcher2 is a Windows-native legal document processing system that 
automatically monitors directories for scanned documents, uses AI to classify 
them, and organizes files with meaningful names.

QUICK START
-----------
1. Install Scanner-Watcher2 using the installer
2. Edit the configuration file at:
   %APPDATA%\ScannerWatcher2\config.json
3. Set your OpenAI API key
4. Configure the watch directory path
5. Start the Windows service from Services Manager or run:
   scanner-watcher2 --start-service

CONFIGURATION
-------------
The configuration file is located at:
%APPDATA%\ScannerWatcher2\config.json

Required Settings:
- watch_directory: Directory to monitor for scanned documents
- openai_api_key: Your OpenAI API key (get from https://platform.openai.com)

Optional Settings:
- log_level: Logging verbosity (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- processing.file_prefix: Prefix for files to process (default: "SCAN-")
- processing.retry_attempts: Number of retry attempts for transient errors
- ai.model: OpenAI model to use (default: "gpt-4-vision-preview")
- ai.timeout_seconds: API timeout in seconds (default: 30)
- logging.max_file_size_mb: Maximum log file size before rotation (default: 10)
- logging.backup_count: Number of backup log files to keep (default: 5)
- service.health_check_interval_seconds: Health check interval (default: 60)

USAGE
-----
The application runs as a Windows service and starts automatically with Windows.

Service Management:
- Install service:  scanner-watcher2 --install-service
- Start service:    scanner-watcher2 --start-service
- Stop service:     scanner-watcher2 --stop-service
- Remove service:   scanner-watcher2 --remove-service

Console Mode (Development):
- Run in console:   scanner-watcher2 --console
- Custom config:    scanner-watcher2 --config path\to\config.json
- Debug logging:    scanner-watcher2 --log-level DEBUG

LOGS
----
Logs are written to:
%APPDATA%\ScannerWatcher2\logs\

Critical events are also logged to Windows Event Log under:
Application and Services Logs > ScannerWatcher2

TROUBLESHOOTING
---------------
1. Service won't start:
   - Check Windows Event Log for error messages
   - Verify configuration file is valid JSON
   - Ensure watch directory exists and is accessible
   - Verify OpenAI API key is valid

2. Files not being processed:
   - Ensure files have "SCAN-" prefix (or configured prefix)
   - Check that files are PDFs
   - Verify watch directory is correct in configuration
   - Check logs for error messages

3. API errors:
   - Verify OpenAI API key is valid and has credits
   - Check internet connectivity
   - Review API rate limits in OpenAI dashboard
   - Check logs for specific error messages

4. Permission errors:
   - Ensure service account has read/write access to watch directory
   - Verify %APPDATA%\ScannerWatcher2 directory is accessible
   - Check Windows Event Log for permission-related errors

SYSTEM REQUIREMENTS
-------------------
- Windows 10, Windows 11, or Windows Server 2019+
- Internet connection for OpenAI API access
- Sufficient disk space for logs and temporary files
- Read/write permissions for watch directory

SUPPORT
-------
For issues, questions, or feature requests, please contact your system administrator.

LICENSE
-------
Copyright (c) 2024 Scanner-Watcher2 Team
Licensed under the MIT License

SECURITY
--------
- API keys are encrypted using Windows DPAPI
- All API communication uses HTTPS with TLS 1.2+
- Logs may contain file paths and document metadata
- Temporary files are automatically cleaned up after processing

PRIVACY
-------
- Document images are sent to OpenAI API for classification
- OpenAI's data usage policy applies to processed documents
- Review OpenAI's privacy policy at: https://openai.com/privacy
- No document data is stored by Scanner-Watcher2 beyond logs
