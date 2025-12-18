# Scanner-Watcher2 Executable Testing Checklist

This checklist should be used to verify the PyInstaller executable works correctly on a clean Windows machine.

## Pre-Testing Setup

- [ ] Clean Windows 10, 11, or Server 2019+ machine (VM recommended)
- [ ] No Python installed
- [ ] No development tools installed
- [ ] Administrator access available
- [ ] Internet connection available (for OpenAI API)
- [ ] Valid OpenAI API key for testing

## File Verification

- [ ] `scanner_watcher2.exe` exists in `dist/` folder
- [ ] Executable size is reasonable (50-100 MB expected)
- [ ] File properties show correct version information (if configured)

## Basic Functionality Tests

### 1. Console Mode - First Run

- [ ] Copy `scanner_watcher2.exe` to test location (e.g., `C:\Temp`)
- [ ] Run: `scanner_watcher2.exe --console`
- [ ] Verify default configuration is created at `%APPDATA%\ScannerWatcher2\config.json`
- [ ] Verify application exits with instructions to edit configuration
- [ ] Verify no Python-related errors appear

### 2. Configuration Setup

- [ ] Open configuration file: `%APPDATA%\ScannerWatcher2\config.json`
- [ ] Verify file contains all expected sections (version, watch_directory, openai_api_key, etc.)
- [ ] Edit configuration:
  - [ ] Set `watch_directory` to test directory (e.g., `C:\TestScans`)
  - [ ] Set `openai_api_key` to valid API key
  - [ ] Set `log_level` to `DEBUG` for testing
- [ ] Save configuration file

### 3. Console Mode - With Configuration

- [ ] Create watch directory (e.g., `C:\TestScans`)
- [ ] Run: `scanner_watcher2.exe --console`
- [ ] Verify application starts without errors
- [ ] Verify console shows:
  - [ ] Configuration loaded successfully
  - [ ] Watch directory path
  - [ ] File prefix
  - [ ] Log level
  - [ ] AI model
- [ ] Verify logs directory created at `%APPDATA%\ScannerWatcher2\logs\`
- [ ] Verify log file is created and contains startup messages
- [ ] Press Ctrl+C to stop
- [ ] Verify graceful shutdown message appears
- [ ] Verify no errors during shutdown

### 4. Command-Line Arguments

- [ ] Test help: `scanner_watcher2.exe --help`
- [ ] Verify help text displays correctly
- [ ] Test custom config: `scanner_watcher2.exe --config C:\custom\config.json`
- [ ] Test log level override: `scanner_watcher2.exe --log-level DEBUG`

## Service Installation Tests (Requires Administrator)

### 5. Service Installation

- [ ] Open Command Prompt as Administrator
- [ ] Run: `scanner_watcher2.exe --install-service`
- [ ] Verify success message appears
- [ ] Open Services Manager (`services.msc`)
- [ ] Verify "ScannerWatcher2" service is listed
- [ ] Verify service properties:
  - [ ] Startup type is "Automatic"
  - [ ] Service description is present
  - [ ] Log on as "Local System" (or configured account)

### 6. Service Start

- [ ] Run: `scanner_watcher2.exe --start-service`
- [ ] Verify success message appears
- [ ] In Services Manager, verify service status is "Running"
- [ ] Check Windows Event Log:
  - [ ] Open Event Viewer
  - [ ] Navigate to Application and Services Logs
  - [ ] Look for "ScannerWatcher2" source
  - [ ] Verify service start event is logged
- [ ] Check application logs at `%APPDATA%\ScannerWatcher2\logs\`
- [ ] Verify service startup messages in log file

### 7. Service Operation

- [ ] Verify service is running in Services Manager
- [ ] Create test PDF file with "SCAN-" prefix
- [ ] Copy test file to watch directory
- [ ] Wait 5-10 seconds
- [ ] Verify file is processed:
  - [ ] File is renamed with date and document type
  - [ ] Original "SCAN-" file is gone
  - [ ] New file exists in same directory
- [ ] Check logs for processing messages:
  - [ ] File detection logged
  - [ ] PDF extraction logged
  - [ ] AI classification logged
  - [ ] File rename logged
  - [ ] Processing time logged

### 8. Service Stop

- [ ] Run: `scanner_watcher2.exe --stop-service`
- [ ] Verify success message appears
- [ ] In Services Manager, verify service status is "Stopped"
- [ ] Check Windows Event Log for service stop event
- [ ] Check application logs for graceful shutdown messages

### 9. Service Removal

- [ ] Run: `scanner_watcher2.exe --remove-service`
- [ ] Verify success message appears
- [ ] In Services Manager, verify "ScannerWatcher2" service is no longer listed
- [ ] Verify no errors in Windows Event Log

## Document Processing Tests

### 10. Single File Processing

- [ ] Start service or run in console mode
- [ ] Create test PDF with "SCAN-" prefix
- [ ] Copy to watch directory
- [ ] Verify file is processed within 5 seconds
- [ ] Verify file is renamed correctly
- [ ] Check logs for complete processing workflow

### 11. Multiple File Processing

- [ ] Start service or run in console mode
- [ ] Copy 3-5 test PDFs with "SCAN-" prefix to watch directory
- [ ] Verify all files are processed
- [ ] Verify files are processed sequentially (check timestamps in logs)
- [ ] Verify no files are skipped

### 12. Error Handling

- [ ] Test with corrupted PDF:
  - [ ] Create invalid PDF file with "SCAN-" prefix
  - [ ] Copy to watch directory
  - [ ] Verify error is logged
  - [ ] Verify service continues running
  - [ ] Verify other files can still be processed

- [ ] Test with locked file:
  - [ ] Create PDF with "SCAN-" prefix
  - [ ] Open file in another application (lock it)
  - [ ] Copy to watch directory
  - [ ] Verify retry attempts are logged
  - [ ] Verify file is processed after unlocking

- [ ] Test with invalid API key:
  - [ ] Set invalid API key in configuration
  - [ ] Restart service
  - [ ] Copy test PDF to watch directory
  - [ ] Verify API error is logged
  - [ ] Verify error is classified as permanent
  - [ ] Verify file is skipped

## Configuration Tests

### 13. Configuration Hot-Reload

- [ ] Start service
- [ ] Edit configuration file (change log level)
- [ ] Wait for next health check (60 seconds)
- [ ] Verify new configuration is loaded (check logs)
- [ ] Verify service continues running

### 14. Invalid Configuration

- [ ] Stop service
- [ ] Edit configuration file with invalid JSON
- [ ] Try to start service
- [ ] Verify service fails to start with clear error message
- [ ] Check Windows Event Log for error details

### 15. Missing Configuration

- [ ] Stop service
- [ ] Delete configuration file
- [ ] Try to start service
- [ ] Verify default configuration is created
- [ ] Verify service prompts for configuration

## Health Check Tests

### 16. Health Check Execution

- [ ] Start service with DEBUG logging
- [ ] Wait 60 seconds (health check interval)
- [ ] Check logs for health check messages
- [ ] Verify health check includes:
  - [ ] Watch directory accessibility check
  - [ ] Configuration validation check
  - [ ] Memory usage logging

### 17. Health Check Failure

- [ ] Start service
- [ ] Rename or delete watch directory
- [ ] Wait for health check
- [ ] Verify health check failure is logged
- [ ] Verify warning appears in logs
- [ ] Verify service continues running

## Performance Tests

### 18. Resource Usage

- [ ] Start service
- [ ] Monitor CPU usage (Task Manager)
- [ ] Verify idle CPU usage < 5%
- [ ] Monitor memory usage
- [ ] Verify memory usage < 200 MB
- [ ] Process several files
- [ ] Verify memory doesn't grow unbounded

### 19. Processing Speed

- [ ] Process single file
- [ ] Check logs for processing time
- [ ] Verify processing completes in reasonable time (< 30 seconds typical)
- [ ] Verify API latency is logged

## Security Tests

### 20. API Key Encryption

- [ ] Open configuration file
- [ ] Verify API key is encrypted (not plain text)
- [ ] Verify encryption uses Windows DPAPI
- [ ] Verify encrypted key can be decrypted by service

### 21. TLS Security

- [ ] Enable network monitoring (optional)
- [ ] Process a file
- [ ] Verify API calls use HTTPS
- [ ] Verify TLS 1.2 or higher is used

## Logging Tests

### 22. Log File Creation

- [ ] Verify logs directory exists: `%APPDATA%\ScannerWatcher2\logs\`
- [ ] Verify log file is created
- [ ] Verify log file contains JSON-formatted entries

### 23. Log Rotation

- [ ] Configure small log file size (e.g., 1 MB) for testing
- [ ] Process many files to generate logs
- [ ] Verify log file rotates at configured size
- [ ] Verify backup log files are created
- [ ] Verify only configured number of backups are kept

### 24. Windows Event Log

- [ ] Start service
- [ ] Open Event Viewer
- [ ] Navigate to Application and Services Logs
- [ ] Verify "ScannerWatcher2" source exists
- [ ] Verify service start event is logged
- [ ] Stop service
- [ ] Verify service stop event is logged
- [ ] Trigger critical error (e.g., delete watch directory)
- [ ] Verify critical error is logged to Event Log

## Clean Machine Test

### 25. Fresh Windows Installation

- [ ] Use completely fresh Windows VM or machine
- [ ] Verify no Python installed: `python --version` should fail
- [ ] Verify no Visual C++ redistributables needed
- [ ] Copy only `scanner_watcher2.exe` to machine
- [ ] Run through all tests above
- [ ] Verify everything works without any additional installations

## Final Verification

- [ ] All tests passed
- [ ] No Python-related errors encountered
- [ ] No missing DLL errors
- [ ] Service installs and runs correctly
- [ ] Document processing works end-to-end
- [ ] Logs are created and rotated correctly
- [ ] Windows Event Log integration works
- [ ] Configuration management works
- [ ] Error handling works correctly
- [ ] Performance is acceptable

## Issues Found

Document any issues found during testing:

| Issue # | Description | Severity | Status |
|---------|-------------|----------|--------|
| 1       |             |          |        |
| 2       |             |          |        |
| 3       |             |          |        |

## Test Environment Details

- Windows Version: _______________
- Test Date: _______________
- Tester: _______________
- Executable Version: _______________
- Notes: _______________

## Sign-Off

- [ ] All critical tests passed
- [ ] All issues documented
- [ ] Ready for deployment

Tester Signature: _______________ Date: _______________
