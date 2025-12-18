# Scanner-Watcher2 Troubleshooting Guide

This guide provides detailed troubleshooting steps for common issues with Scanner-Watcher2.

## Table of Contents

- [Service Issues](#service-issues)
- [File Processing Issues](#file-processing-issues)
- [API and Network Issues](#api-and-network-issues)
- [Configuration Issues](#configuration-issues)
- [Performance Issues](#performance-issues)
- [Windows-Specific Issues](#windows-specific-issues)
- [Diagnostic Tools](#diagnostic-tools)

## Service Issues

### Service Won't Start

**Symptoms**:
- Service fails to start in Services Manager
- Service starts then immediately stops
- Error in Windows Event Log

**Diagnostic Steps**:

1. **Check Windows Event Log**:
   ```
   1. Open Event Viewer (Win+R, type eventvwr.msc)
   2. Navigate to Windows Logs → Application
   3. Filter by Source: "Scanner-Watcher2"
   4. Look for error messages with timestamps matching startup attempts
   ```

2. **Check Application Logs**:
   ```bash
   type %APPDATA%\ScannerWatcher2\logs\scanner_watcher2.log
   ```
   Look for:
   - Configuration errors
   - Permission errors
   - Missing dependencies

3. **Verify Configuration File**:
   ```bash
   # Check if file exists
   dir %APPDATA%\ScannerWatcher2\config.json
   
   # Validate JSON syntax
   type %APPDATA%\ScannerWatcher2\config.json
   ```

4. **Test in Console Mode**:
   ```bash
   cd "C:\Program Files\ScannerWatcher2"
   scanner_watcher2.exe --console
   ```
   This provides immediate feedback on startup issues.

**Common Causes and Solutions**:

| Error Message | Cause | Solution |
|--------------|-------|----------|
| "Configuration file not found" | Missing config.json | Run configuration wizard or copy config_template.json |
| "Watch directory not found" | Directory doesn't exist | Create directory or update config.json |
| "Invalid API key format" | Malformed API key | Re-enter API key using configuration wizard |
| "Permission denied" | Insufficient permissions | Run as administrator or check folder permissions |
| "Port already in use" | Another instance running | Stop other instance or check for orphaned processes |

### Service Stops Unexpectedly

**Symptoms**:
- Service runs for a while then stops
- No obvious error in logs
- Intermittent failures

**Diagnostic Steps**:

1. **Check for Fatal Errors**:
   ```bash
   type %APPDATA%\ScannerWatcher2\logs\scanner_watcher2.log | findstr /i "CRITICAL FATAL"
   ```

2. **Monitor Memory Usage**:
   - Open Task Manager
   - Find "scanner_watcher2.exe" process
   - Monitor memory over time
   - Check if memory grows continuously (memory leak)

3. **Check Disk Space**:
   ```bash
   # Check available space on system drive
   wmic logicaldisk get caption,freespace,size
   ```

4. **Review Health Check Logs**:
   ```bash
   type %APPDATA%\ScannerWatcher2\logs\scanner_watcher2.log | findstr "health_check"
   ```

**Solutions**:

- **Out of Memory**: Restart service, check for large PDF files
- **Disk Full**: Free up disk space, especially in temp directory
- **Network Drive Disconnected**: Reconnect drive or use UNC path
- **API Quota Exceeded**: Wait for quota reset or upgrade API tier

### Service Won't Stop

**Symptoms**:
- Service hangs when stopping
- Takes longer than 30 seconds to stop
- Must force-kill process

**Diagnostic Steps**:

1. **Check for Stuck Operations**:
   - Look for files being processed during shutdown
   - Check for network operations in progress

2. **Review Shutdown Logs**:
   ```bash
   type %APPDATA%\ScannerWatcher2\logs\scanner_watcher2.log | findstr "shutdown"
   ```

**Solutions**:

- **Increase Timeout**: Edit config.json, increase `graceful_shutdown_timeout_seconds`
- **Force Stop**: Use Task Manager to end process
- **Restart System**: If service is completely hung

## File Processing Issues

### Files Not Being Detected

**Symptoms**:
- Files with "SCAN-" prefix are ignored
- No log entries for new files
- Files remain unprocessed

**Diagnostic Steps**:

1. **Verify File Naming**:
   - File must start with "SCAN-" (case-sensitive)
   - File must have .pdf extension
   - Example: `SCAN-document.pdf` ✓
   - Example: `scan-document.pdf` ✗ (lowercase)
   - Example: `SCAN-document.docx` ✗ (not PDF)

2. **Check Watch Directory**:
   ```bash
   # Verify directory in config
   type %APPDATA%\ScannerWatcher2\config.json | findstr watch_directory
   
   # Check if directory exists
   dir "D:\Scans"  # Replace with your path
   ```

3. **Monitor Directory Watcher**:
   ```bash
   type %APPDATA%\ScannerWatcher2\logs\scanner_watcher2.log | findstr "DirectoryWatcher"
   ```

4. **Test File Stability**:
   - System waits 2 seconds for file size to stabilize
   - Ensure file is completely written before expecting processing

**Solutions**:

- **Fix File Naming**: Rename files to start with "SCAN-"
- **Check Permissions**: Ensure service can read watch directory
- **Verify Service Running**: Check Services Manager
- **Network Drives**: Use UNC paths instead of mapped drives

### Files Detected But Not Processed

**Symptoms**:
- Files are detected (in logs)
- Processing starts but fails
- Files remain with "SCAN-" prefix

**Diagnostic Steps**:

1. **Check Processing Errors**:
   ```bash
   type %APPDATA%\ScannerWatcher2\logs\scanner_watcher2.log | findstr /i "ERROR"
   ```

2. **Verify PDF Validity**:
   - Try opening PDF in Adobe Reader
   - Check file size (not 0 bytes)
   - Verify PDF is not corrupted

3. **Check API Connectivity**:
   ```bash
   # Test OpenAI API access
   curl https://api.openai.com/v1/models -H "Authorization: Bearer YOUR_API_KEY"
   ```

4. **Review Retry Attempts**:
   ```bash
   type %APPDATA%\ScannerWatcher2\logs\scanner_watcher2.log | findstr "retry"
   ```

**Common Processing Errors**:

| Error | Cause | Solution |
|-------|-------|----------|
| "Failed to extract first page" | Corrupted PDF | Check PDF file, try re-scanning |
| "API request failed" | Network/API issue | Check internet connection, verify API key |
| "Rate limit exceeded" | Too many requests | Wait for automatic retry, upgrade API tier |
| "File locked" | PDF open elsewhere | Close PDF, wait for automatic retry |
| "Invalid classification response" | Unexpected API response | Check API model configuration |

### Files Processed But Not Renamed

**Symptoms**:
- Processing completes successfully
- Classification appears in logs
- File keeps original "SCAN-" name

**Diagnostic Steps**:

1. **Check Rename Errors**:
   ```bash
   type %APPDATA%\ScannerWatcher2\logs\scanner_watcher2.log | findstr "rename"
   ```

2. **Verify File Permissions**:
   - Check if service can write to watch directory
   - Verify file is not read-only

3. **Check for File Locks**:
   - Ensure file is not open in another application
   - Check for antivirus scanning locks

**Solutions**:

- **Permission Issues**: Grant write permissions to service account
- **File Locked**: Close applications using the file
- **Antivirus**: Add watch directory to antivirus exclusions
- **Read-Only**: Remove read-only attribute from files

## API and Network Issues

### Rate Limit Errors

**Symptoms**:
- Logs show "Rate limit exceeded"
- Processing slows down significantly
- 429 status codes in logs

**Understanding Rate Limits**:
- OpenAI enforces rate limits based on API tier
- System automatically handles rate limits with exponential backoff
- Processing resumes automatically after retry-after period

**Solutions**:

1. **Wait for Automatic Recovery**:
   - System will retry automatically
   - Check logs for retry timing

2. **Reduce Processing Volume**:
   - Process fewer files simultaneously
   - Spread processing over time

3. **Upgrade API Tier**:
   - Contact OpenAI to increase rate limits
   - Consider higher-tier API plan

4. **Monitor Rate Limit Status**:
   ```bash
   type %APPDATA%\ScannerWatcher2\logs\scanner_watcher2.log | findstr "rate_limit"
   ```

### Network Connectivity Issues

**Symptoms**:
- "Connection timeout" errors
- "Unable to reach API" messages
- Intermittent processing failures

**Diagnostic Steps**:

1. **Test Internet Connectivity**:
   ```bash
   ping api.openai.com
   curl https://api.openai.com/v1/models
   ```

2. **Check Proxy Settings**:
   - If behind corporate firewall, verify proxy configuration
   - Ensure HTTPS traffic is allowed

3. **Verify DNS Resolution**:
   ```bash
   nslookup api.openai.com
   ```

4. **Check Firewall Rules**:
   - Ensure outbound HTTPS (port 443) is allowed
   - Add scanner_watcher2.exe to firewall exceptions

**Solutions**:

- **Proxy Configuration**: Configure proxy in environment variables
- **Firewall**: Add exception for scanner_watcher2.exe
- **VPN Issues**: Ensure VPN allows OpenAI API access
- **Network Instability**: System will retry automatically

### API Authentication Errors

**Symptoms**:
- "Invalid API key" errors
- 401 Unauthorized responses
- Authentication failures

**Diagnostic Steps**:

1. **Verify API Key**:
   ```bash
   # Check encrypted key exists
   type %APPDATA%\ScannerWatcher2\config.json | findstr openai_api_key
   ```

2. **Test API Key Manually**:
   ```bash
   curl https://api.openai.com/v1/models ^
     -H "Authorization: Bearer YOUR_API_KEY"
   ```

3. **Check API Key Permissions**:
   - Verify key has GPT-4 Vision access
   - Check if key is active (not revoked)

**Solutions**:

- **Invalid Key**: Re-run configuration wizard with correct key
- **Expired Key**: Generate new key from OpenAI dashboard
- **Insufficient Permissions**: Ensure key has GPT-4 Vision access
- **Encryption Issues**: Delete config.json and reconfigure

## Configuration Issues

### Configuration Validation Errors

**Symptoms**:
- "Configuration validation failed" in logs
- Service won't start
- Invalid configuration messages

**Diagnostic Steps**:

1. **Validate JSON Syntax**:
   ```bash
   # Use online JSON validator or Python
   python -m json.tool %APPDATA%\ScannerWatcher2\config.json
   ```

2. **Check Required Fields**:
   - version
   - watch_directory
   - openai_api_key
   - log_level

3. **Verify Field Types**:
   - Paths should use double backslashes: `"D:\\Scans"`
   - Numbers should not be quoted
   - Booleans should be `true` or `false` (lowercase)

**Common Validation Errors**:

| Error | Cause | Solution |
|-------|-------|----------|
| "Invalid JSON" | Syntax error | Use JSON validator, check commas and quotes |
| "Missing required field" | Field not present | Add missing field from template |
| "Invalid path" | Path doesn't exist | Create directory or fix path |
| "Invalid log level" | Typo in level name | Use: DEBUG, INFO, WARNING, ERROR, CRITICAL |
| "Invalid retry attempts" | Out of range (1-10) | Set value between 1 and 10 |

### Configuration Not Reloading

**Symptoms**:
- Changes to config.json don't take effect
- Service uses old configuration
- Must restart service for changes

**Diagnostic Steps**:

1. **Check File Modification Time**:
   ```bash
   dir %APPDATA%\ScannerWatcher2\config.json
   ```

2. **Verify File Permissions**:
   - Ensure service can read config.json
   - Check file is not locked

3. **Review Reload Logs**:
   ```bash
   type %APPDATA%\ScannerWatcher2\logs\scanner_watcher2.log | findstr "config"
   ```

**Solutions**:

- **Watch Directory Changes**: Require service restart
- **Syntax Errors**: Fix JSON syntax, service won't reload invalid config
- **File Locked**: Close editors, save file properly
- **Manual Restart**: Stop and start service to force reload

## Performance Issues

### High CPU Usage

**Symptoms**:
- CPU usage consistently above 5% when idle
- System slowdown
- High CPU in Task Manager

**Diagnostic Steps**:

1. **Check Processing Queue**:
   ```bash
   type %APPDATA%\ScannerWatcher2\logs\scanner_watcher2.log | findstr "queue"
   ```

2. **Monitor File System Events**:
   - Excessive file system activity can cause high CPU
   - Check for applications creating many temporary files

3. **Review Performance Metrics**:
   ```bash
   type %APPDATA%\ScannerWatcher2\logs\scanner_watcher2.log | findstr "performance"
   ```

**Solutions**:

- **Large Queue**: Process files in smaller batches
- **Busy Directory**: Move watch directory to quieter location
- **Restart Service**: Clear any stuck operations
- **Reduce Monitoring**: Use more specific file prefix

### High Memory Usage

**Symptoms**:
- Memory usage grows over time
- Service uses >200MB memory
- System runs out of memory

**Diagnostic Steps**:

1. **Check for Memory Leaks**:
   - Monitor memory usage over 24 hours
   - Look for continuous growth

2. **Review Large Files**:
   ```bash
   # Find large PDFs in watch directory
   dir "D:\Scans\*.pdf" /s | findstr /r "[0-9][0-9][0-9][0-9][0-9][0-9][0-9]"
   ```

3. **Check Temporary Files**:
   ```bash
   dir %APPDATA%\ScannerWatcher2\temp
   ```

**Solutions**:

- **Large PDFs**: Split large files or increase system memory
- **Temp File Cleanup**: Delete old temporary files
- **Restart Service**: Clear memory periodically
- **Memory Limit**: Configure system to restart service if memory exceeds threshold

### Slow Processing

**Symptoms**:
- Files take minutes to process
- Processing time increases over time
- Timeout errors

**Diagnostic Steps**:

1. **Check Processing Times**:
   ```bash
   type %APPDATA%\ScannerWatcher2\logs\scanner_watcher2.log | findstr "processing_time"
   ```

2. **Identify Bottlenecks**:
   - PDF extraction time
   - API response time
   - File rename time

3. **Monitor API Latency**:
   ```bash
   type %APPDATA%\ScannerWatcher2\logs\scanner_watcher2.log | findstr "api_latency"
   ```

**Solutions**:

- **Large PDFs**: Optimize PDF file sizes before scanning
- **Slow Network**: Check internet connection speed
- **API Latency**: Normal variation, system handles automatically
- **Disk I/O**: Use faster disk for watch directory

## Windows-Specific Issues

### Service Installation Fails

**Symptoms**:
- "Access denied" during installation
- Service not appearing in Services Manager
- Installation command fails

**Solutions**:

1. **Run as Administrator**:
   ```bash
   # Right-click Command Prompt → Run as Administrator
   cd "C:\Program Files\ScannerWatcher2"
   scanner_watcher2.exe --install-service
   ```

2. **Check User Permissions**:
   - Must be in Administrators group
   - UAC must be enabled

3. **Verify Service Name**:
   - Service name: "ScannerWatcher2"
   - Display name: "Scanner-Watcher2"

### Windows Event Log Issues

**Symptoms**:
- Critical events not appearing in Event Log
- "Event Log source not found" errors
- Permission errors writing to Event Log

**Diagnostic Steps**:

1. **Check Event Log Source**:
   ```powershell
   Get-EventLog -List | Where-Object {$_.Log -eq "Application"}
   ```

2. **Verify Permissions**:
   - Service must have permission to write to Event Log
   - Usually granted during service installation

**Solutions**:

- **Reinstall Service**: Remove and reinstall to register Event Log source
- **Manual Registration**: Register Event Log source manually (requires admin)
- **Disable Event Logging**: Set `log_to_event_log: false` in config.json

### DPAPI Encryption Issues

**Symptoms**:
- "Failed to encrypt API key" errors
- "Failed to decrypt API key" errors
- API key appears as plaintext

**Understanding DPAPI**:
- Windows Data Protection API (DPAPI)
- Encrypts data per-user
- Encrypted data cannot be decrypted by other users

**Solutions**:

- **User Account Change**: Reconfigure if service user account changes
- **Profile Corruption**: Create new Windows user profile
- **Manual Encryption**: Delete config.json and reconfigure
- **Plaintext Fallback**: System will encrypt on next save

### UNC Path Issues

**Symptoms**:
- Network paths not working
- "Path not found" for \\server\share
- Intermittent access issues

**Solutions**:

1. **Use UNC Paths**:
   ```json
   {
     "watch_directory": "\\\\server\\share\\scans"
   }
   ```

2. **Verify Network Access**:
   ```bash
   dir \\server\share\scans
   ```

3. **Check Service Account**:
   - Service account must have network access
   - Local System account may not have network permissions
   - Consider using domain account for service

4. **Map Drive Alternative**:
   - Map network drive persistently
   - Use mapped drive letter in config

## Diagnostic Tools

### Log Analysis

**View Recent Errors**:
```bash
type %APPDATA%\ScannerWatcher2\logs\scanner_watcher2.log | findstr /i "ERROR CRITICAL" | more
```

**View Processing Statistics**:
```bash
type %APPDATA%\ScannerWatcher2\logs\scanner_watcher2.log | findstr "processing_time file_size"
```

**View Health Checks**:
```bash
type %APPDATA%\ScannerWatcher2\logs\scanner_watcher2.log | findstr "health_check"
```

**View API Calls**:
```bash
type %APPDATA%\ScannerWatcher2\logs\scanner_watcher2.log | findstr "api_latency"
```

### Windows Event Viewer

1. Open Event Viewer: `eventvwr.msc`
2. Navigate to: Windows Logs → Application
3. Filter by Source: "Scanner-Watcher2"
4. Look for Error and Critical events

### Service Status

**Check Service Status**:
```bash
sc query ScannerWatcher2
```

**View Service Configuration**:
```bash
sc qc ScannerWatcher2
```

**Check Service Dependencies**:
```bash
sc enumdepend ScannerWatcher2
```

### Process Monitoring

**Task Manager**:
1. Open Task Manager (Ctrl+Shift+Esc)
2. Details tab
3. Find "scanner_watcher2.exe"
4. Monitor CPU, Memory, Disk usage

**Resource Monitor**:
1. Open Resource Monitor (resmon.exe)
2. Check CPU, Memory, Disk, Network tabs
3. Filter by "scanner_watcher2.exe"

### Network Diagnostics

**Test API Connectivity**:
```bash
curl -v https://api.openai.com/v1/models
```

**Check DNS Resolution**:
```bash
nslookup api.openai.com
```

**Trace Route**:
```bash
tracert api.openai.com
```

**Test HTTPS**:
```bash
curl -v --tlsv1.2 https://api.openai.com
```

## Getting Additional Help

### Before Requesting Help

1. **Collect Information**:
   - Windows version
   - Service version
   - Error messages from logs
   - Steps to reproduce issue

2. **Gather Logs**:
   ```bash
   # Copy recent logs
   copy %APPDATA%\ScannerWatcher2\logs\scanner_watcher2.log %USERPROFILE%\Desktop\
   ```

3. **Check Event Log**:
   - Export relevant Event Log entries
   - Include timestamps

4. **Document Configuration**:
   - Copy config.json (remove API key!)
   - Note any custom settings

### Submitting Issues

When opening a GitHub issue, include:

1. **Issue Description**:
   - Clear description of problem
   - Expected vs actual behavior
   - Steps to reproduce

2. **Environment**:
   - Windows version
   - Service version
   - Installation method

3. **Logs**:
   - Relevant log excerpts
   - Error messages
   - Stack traces

4. **Configuration**:
   - Sanitized config.json
   - Custom settings

5. **Troubleshooting Attempted**:
   - Steps already tried
   - Results of diagnostic commands

### Emergency Recovery

**Complete Reset**:
```bash
# Stop service
sc stop ScannerWatcher2

# Remove service
cd "C:\Program Files\ScannerWatcher2"
scanner_watcher2.exe --remove-service

# Delete configuration
rmdir /s /q %APPDATA%\ScannerWatcher2

# Reinstall service
scanner_watcher2.exe --install-service

# Reconfigure
scanner_watcher2.exe --configure

# Start service
sc start ScannerWatcher2
```

**Backup Configuration**:
```bash
# Before making changes
copy %APPDATA%\ScannerWatcher2\config.json %APPDATA%\ScannerWatcher2\config.json.backup
```

**Restore Configuration**:
```bash
copy %APPDATA%\ScannerWatcher2\config.json.backup %APPDATA%\ScannerWatcher2\config.json
```
