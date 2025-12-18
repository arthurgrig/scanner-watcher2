# Windows-Specific Requirements

This document details Windows-specific requirements, features, and considerations for Scanner-Watcher2.

## Table of Contents

- [Operating System Requirements](#operating-system-requirements)
- [Windows Service Integration](#windows-service-integration)
- [Windows Event Log](#windows-event-log)
- [Windows DPAPI Encryption](#windows-dpapi-encryption)
- [File System Considerations](#file-system-considerations)
- [Windows Paths](#windows-paths)
- [Permissions and Security](#permissions-and-security)
- [Windows-Specific APIs](#windows-specific-apis)

## Operating System Requirements

### Supported Windows Versions

- **Windows 10** (Version 1809 or later)
- **Windows 11** (All versions)
- **Windows Server 2019** or later

### Architecture

- **x64 (64-bit)**: Primary support
- **x86 (32-bit)**: Not supported

### System Requirements

**Minimum**:
- 2 GB RAM
- 500 MB disk space
- .NET Framework 4.7.2 or later (usually pre-installed)

**Recommended**:
- 4 GB RAM or more
- 1 GB disk space
- SSD for watch directory

### Windows Features

No additional Windows features need to be enabled. The application uses standard Windows APIs available in all supported versions.

## Windows Service Integration

### Service Architecture

Scanner-Watcher2 runs as a native Windows service using the pywin32 library, which provides Python bindings to Windows Service APIs.

### Service Characteristics

- **Service Name**: `ScannerWatcher2`
- **Display Name**: `Scanner-Watcher2`
- **Description**: "Monitors directories for scanned documents and organizes them using AI classification"
- **Start Type**: Automatic (starts with Windows)
- **Service Account**: Local System (default)
- **Dependencies**: None

### Service Lifecycle

1. **Installation**:
   ```bash
   scanner_watcher2.exe --install-service
   ```
   - Registers service with Windows Service Control Manager (SCM)
   - Creates service registry entries
   - Registers Windows Event Log source

2. **Starting**:
   ```bash
   sc start ScannerWatcher2
   # Or
   scanner_watcher2.exe --start-service
   # Or via Services Manager (services.msc)
   ```

3. **Stopping**:
   ```bash
   sc stop ScannerWatcher2
   # Or
   scanner_watcher2.exe --stop-service
   ```
   - Graceful shutdown with 30-second timeout
   - Completes current file processing
   - Cleans up resources

4. **Removal**:
   ```bash
   scanner_watcher2.exe --remove-service
   ```
   - Stops service if running
   - Unregisters from SCM
   - Removes registry entries

### Service Control

**Via Services Manager**:
1. Open Services (Win+R, type `services.msc`)
2. Find "Scanner-Watcher2"
3. Right-click for Start/Stop/Restart/Properties

**Via Command Line**:
```bash
# Query status
sc query ScannerWatcher2

# Start service
sc start ScannerWatcher2

# Stop service
sc stop ScannerWatcher2

# Configure startup type
sc config ScannerWatcher2 start= auto

# View configuration
sc qc ScannerWatcher2
```

**Via PowerShell**:
```powershell
# Get service status
Get-Service -Name ScannerWatcher2

# Start service
Start-Service -Name ScannerWatcher2

# Stop service
Stop-Service -Name ScannerWatcher2

# Restart service
Restart-Service -Name ScannerWatcher2
```

### Service Recovery

Configure automatic recovery in Services Manager:
1. Open Services (services.msc)
2. Right-click "Scanner-Watcher2" → Properties
3. Recovery tab
4. Configure actions for failures:
   - First failure: Restart the Service
   - Second failure: Restart the Service
   - Subsequent failures: Restart the Service
   - Reset fail count after: 1 day

### Service Account Considerations

**Local System Account** (Default):
- Full access to local system
- No network credentials
- Cannot access network drives with credentials
- Recommended for local directories only

**Custom Domain Account**:
- Required for network drive access
- Must have "Log on as a service" right
- Configure in Services Manager → Properties → Log On tab

To grant "Log on as a service":
1. Open Local Security Policy (secpol.msc)
2. Local Policies → User Rights Assignment
3. "Log on as a service"
4. Add user account

## Windows Event Log

### Event Log Integration

Scanner-Watcher2 writes critical events to the Windows Application Event Log for system-wide monitoring and alerting.

### Event Log Source

- **Source Name**: `Scanner-Watcher2`
- **Log Name**: `Application`
- **Event IDs**: Custom range (1000-1999)

### Event Types

**Information Events**:
- Service started (Event ID: 1000)
- Service stopped (Event ID: 1001)
- Configuration reloaded (Event ID: 1002)

**Warning Events**:
- Health check failed (Event ID: 2000)
- Configuration validation warning (Event ID: 2001)
- Retry limit reached (Event ID: 2002)

**Error Events**:
- Service startup failed (Event ID: 3000)
- Critical component failure (Event ID: 3001)
- Configuration error (Event ID: 3002)

**Critical Events**:
- Fatal error requiring service stop (Event ID: 4000)
- Watch directory unavailable (Event ID: 4001)
- Unable to write logs (Event ID: 4002)

### Viewing Event Log

**Event Viewer**:
1. Open Event Viewer (Win+R, type `eventvwr.msc`)
2. Navigate to Windows Logs → Application
3. Filter by Source: "Scanner-Watcher2"

**PowerShell**:
```powershell
# Get recent events
Get-EventLog -LogName Application -Source "Scanner-Watcher2" -Newest 50

# Get error events only
Get-EventLog -LogName Application -Source "Scanner-Watcher2" -EntryType Error

# Get events from last 24 hours
Get-EventLog -LogName Application -Source "Scanner-Watcher2" -After (Get-Date).AddDays(-1)
```

**Command Line**:
```bash
# Export events to file
wevtutil qe Application "/q:*[System[Provider[@Name='Scanner-Watcher2']]]" /f:text > events.txt
```

### Event Log Configuration

Control Event Log integration in config.json:
```json
{
  "logging": {
    "log_to_event_log": true
  }
}
```

Set to `false` to disable Event Log writing (file logging continues).

## Windows DPAPI Encryption

### Data Protection API (DPAPI)

Scanner-Watcher2 uses Windows DPAPI to encrypt sensitive configuration data, specifically the OpenAI API key.

### How DPAPI Works

- **User-Specific**: Encrypted data can only be decrypted by the same user on the same machine
- **Machine-Specific**: Tied to machine's encryption keys
- **Automatic Key Management**: Windows manages encryption keys
- **No Password Required**: Uses Windows login credentials

### API Key Encryption

When you configure the API key:
1. Key is encrypted using DPAPI
2. Encrypted value stored in config.json
3. Only the service account can decrypt it
4. Encrypted value looks like: `AQAAANCMnd8BFdERjHoAwE/Cl+s...`

### Security Implications

**Advantages**:
- No plaintext API keys in configuration
- Automatic key rotation with Windows
- Protected from casual file inspection

**Limitations**:
- Not protected if attacker has user credentials
- Cannot transfer encrypted config to another machine/user
- Backup/restore requires reconfiguration

### Reconfiguration Scenarios

**User Account Change**:
If service account changes, API key must be re-entered:
```bash
scanner_watcher2.exe --configure
```

**Machine Migration**:
When moving to new machine:
1. Copy config.json
2. Run configuration wizard
3. Re-enter API key (will be re-encrypted)

**Profile Corruption**:
If Windows user profile is corrupted:
1. Delete config.json
2. Run configuration wizard
3. Re-enter all settings

### Manual Encryption/Decryption

For advanced scenarios, use Python:
```python
import win32crypt

# Encrypt
plaintext = "your-api-key"
encrypted = win32crypt.CryptProtectData(plaintext.encode(), None, None, None, None, 0)

# Decrypt
decrypted = win32crypt.CryptUnprotectData(encrypted, None, None, None, 0)[1]
```

## File System Considerations

### File System Monitoring

Scanner-Watcher2 uses the watchdog library, which on Windows uses the `ReadDirectoryChangesW` API.

**Characteristics**:
- Real-time file system notifications
- Low CPU overhead
- Supports local and network drives
- Buffer size: 64KB (handles ~1000 events)

**Limitations**:
- Network drives may have delayed notifications
- Very rapid file creation may overflow buffer
- Some network file systems don't support notifications

### File Locking

Windows uses mandatory file locking, which can cause issues:

**Common Scenarios**:
- PDF open in Adobe Reader
- File being written by scanner software
- Antivirus scanning file
- Backup software accessing file

**Handling**:
- System waits 2 seconds for file stability
- Retries file operations up to 3 times
- Exponential backoff between retries
- Logs sharing violation errors

### File Stability Detection

Before processing, system verifies file is stable:
1. Check file size
2. Wait 2 seconds
3. Check file size again
4. If unchanged, file is stable
5. If changed, repeat from step 2

### Temporary Files

Temporary files are created in:
- Default: `%APPDATA%\ScannerWatcher2\temp\`
- Custom: Configured in `processing.temp_directory`

**Cleanup**:
- Automatic cleanup after processing
- Startup cleanup of orphaned files
- Verification of successful deletion

### Long Path Support

Windows has a 260-character path limit (MAX_PATH) by default.

**Enabling Long Paths**:
1. Open Registry Editor (regedit.exe)
2. Navigate to: `HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\FileSystem`
3. Set `LongPathsEnabled` to 1
4. Restart system

**Or via Group Policy**:
1. Open Group Policy Editor (gpedit.msc)
2. Computer Configuration → Administrative Templates → System → Filesystem
3. Enable "Enable Win32 long paths"

Scanner-Watcher2 supports long paths if enabled in Windows.

## Windows Paths

### Path Formats

**Absolute Paths**:
```
C:\Users\John\Documents\Scans
D:\Scans
```

**UNC Paths** (Network):
```
\\server\share\scans
\\192.168.1.100\documents\scans
```

**Relative Paths** (Not recommended):
```
.\scans
..\documents\scans
```

### Path Handling in Configuration

Use double backslashes in JSON:
```json
{
  "watch_directory": "D:\\Scans"
}
```

Or use forward slashes (converted automatically):
```json
{
  "watch_directory": "D:/Scans"
}
```

### Special Folders

**User Profile**:
- `%USERPROFILE%` → `C:\Users\John`
- `%APPDATA%` → `C:\Users\John\AppData\Roaming`
- `%LOCALAPPDATA%` → `C:\Users\John\AppData\Local`

**System**:
- `%ProgramFiles%` → `C:\Program Files`
- `%ProgramFiles(x86)%` → `C:\Program Files (x86)`
- `%SystemRoot%` → `C:\Windows`

### Network Drives

**Mapped Drives**:
```
Z:\scans  # Mapped to \\server\share
```

**Considerations**:
- Mapping must be persistent
- Service account must have access
- May disconnect/reconnect
- UNC paths more reliable

**Recommended**: Use UNC paths instead of mapped drives for services.

## Permissions and Security

### Required Permissions

**Installation**:
- Administrator privileges
- Write access to `C:\Program Files\`
- Registry write access

**Service Operation**:
- Read/write access to watch directory
- Read/write access to `%APPDATA%\ScannerWatcher2\`
- Network access for OpenAI API
- Event Log write access

### User Account Control (UAC)

**Installation**:
- Requires UAC elevation
- Installer prompts for admin rights
- Service installation requires admin

**Operation**:
- Service runs with configured account
- No UAC prompts during operation

### Antivirus Considerations

**Potential Issues**:
- Antivirus may scan PDFs, causing locks
- Real-time protection may delay file access
- Heuristic analysis may flag executable

**Recommendations**:
1. Add watch directory to antivirus exclusions
2. Add `scanner_watcher2.exe` to exclusions
3. Add `%APPDATA%\ScannerWatcher2\` to exclusions

### Firewall Configuration

**Required Access**:
- Outbound HTTPS (port 443) to api.openai.com
- DNS resolution

**Configuration**:
1. Open Windows Defender Firewall
2. Advanced Settings
3. Outbound Rules
4. New Rule → Program
5. Select `scanner_watcher2.exe`
6. Allow connection

### Network Security

**Corporate Proxies**:
Configure via environment variables:
```bash
set HTTPS_PROXY=http://proxy.company.com:8080
set HTTP_PROXY=http://proxy.company.com:8080
```

**TLS/SSL**:
- Requires TLS 1.2 or higher
- Uses Windows certificate store
- Validates OpenAI SSL certificate

## Windows-Specific APIs

### APIs Used

**pywin32 (Python for Windows Extensions)**:
- `win32service`: Service control
- `win32serviceutil`: Service utilities
- `win32event`: Event handling
- `win32evtlog`: Event Log
- `win32crypt`: DPAPI encryption

**watchdog**:
- Uses `ReadDirectoryChangesW` on Windows
- Monitors file system changes
- Handles network drives

**pathlib**:
- Cross-platform path handling
- Automatically handles Windows paths
- Supports UNC paths

### Windows API Calls

**Service Control**:
```python
import win32serviceutil
import win32service

# Install service
win32serviceutil.InstallService(
    pythonClassString,
    serviceName,
    displayName,
    startType=win32service.SERVICE_AUTO_START
)

# Start service
win32serviceutil.StartService(serviceName)

# Stop service
win32serviceutil.StopService(serviceName)
```

**Event Log**:
```python
import win32evtlog
import win32evtlogutil

# Write event
win32evtlogutil.ReportEvent(
    appName,
    eventID,
    eventType=win32evtlog.EVENTLOG_INFORMATION_TYPE,
    strings=[message]
)
```

**DPAPI**:
```python
import win32crypt

# Encrypt
encrypted = win32crypt.CryptProtectData(data, None, None, None, None, 0)

# Decrypt
decrypted = win32crypt.CryptUnprotectData(encrypted, None, None, None, 0)[1]
```

### Development Requirements

**Visual Studio Build Tools**:
Required for compiling pywin32:
- Download: https://visualstudio.microsoft.com/downloads/
- Install "Desktop development with C++" workload
- Includes MSVC compiler and Windows SDK

**Windows SDK**:
Included with Visual Studio Build Tools:
- Provides Windows API headers
- Required for pywin32 compilation

### Testing Windows Features

**Service Testing**:
```bash
# Install (requires admin)
python -m scanner_watcher2 --install-service

# Start
python -m scanner_watcher2 --start-service

# Check status
sc query ScannerWatcher2

# Stop
python -m scanner_watcher2 --stop-service

# Remove
python -m scanner_watcher2 --remove-service
```

**Event Log Testing**:
1. Run service
2. Open Event Viewer
3. Check Application log
4. Filter by "Scanner-Watcher2"

**DPAPI Testing**:
```python
from scanner_watcher2.infrastructure.config_manager import ConfigManager

manager = ConfigManager()
encrypted = manager.encrypt_api_key("test-key")
decrypted = manager.decrypt_api_key(encrypted)
assert decrypted == "test-key"
```

## Troubleshooting Windows Issues

### Service Won't Install

**Error**: "Access denied"
- **Solution**: Run as Administrator

**Error**: "Service already exists"
- **Solution**: Remove existing service first

**Error**: "The specified module could not be found"
- **Solution**: Verify executable path is correct

### Event Log Not Working

**Error**: "Event source not found"
- **Solution**: Reinstall service to register source

**Error**: "Access denied writing to Event Log"
- **Solution**: Check service account permissions

### DPAPI Errors

**Error**: "Failed to decrypt"
- **Solution**: Reconfigure with same user account

**Error**: "Invalid data"
- **Solution**: Delete config.json and reconfigure

### Path Issues

**Error**: "Path not found"
- **Solution**: Use absolute paths, check path exists

**Error**: "Invalid path format"
- **Solution**: Use double backslashes in JSON

**Error**: "Access denied"
- **Solution**: Check service account has permissions

## Additional Resources

- [Microsoft Docs: Windows Services](https://docs.microsoft.com/en-us/windows/win32/services/services)
- [Microsoft Docs: Event Logging](https://docs.microsoft.com/en-us/windows/win32/eventlog/event-logging)
- [Microsoft Docs: DPAPI](https://docs.microsoft.com/en-us/windows/win32/api/dpapi/)
- [pywin32 Documentation](https://github.com/mhammond/pywin32)
- [watchdog Documentation](https://python-watchdog.readthedocs.io/)
