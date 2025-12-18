# Configuration Wizard Guide

The Scanner-Watcher2 configuration wizard provides an interactive way to set up the application without manually editing configuration files.

## Running the Wizard

To run the configuration wizard, use the `--configure` command-line option:

```bash
python -m scanner_watcher2 --configure
```

Or if using the installed executable:

```bash
scanner-watcher2.exe --configure
```

## What the Wizard Configures

The wizard will prompt you for the following essential settings:

### 1. Watch Directory Path

The directory that Scanner-Watcher2 will monitor for new scanned documents.

- Must be an absolute path (e.g., `C:\Scans`)
- The wizard will offer to create the directory if it doesn't exist
- The directory must be accessible and writable

**Example:**
```
Watch directory path: C:\Scans
```

### 2. File Prefix

The prefix that identifies files to be processed. Only files starting with this prefix will be detected and processed.

- Default: "SCAN-"
- Can be customized to match your scanning workflow (e.g., "DOC-", "LEGAL-", "INVOICE-")
- Must contain only valid filename characters
- Case-sensitive

**Example:**
```
File prefix [SCAN-]: LEGAL-
```

### 3. OpenAI API Key

Your OpenAI API key for document classification using GPT-4 Vision.

- Get your API key from: https://platform.openai.com/api-keys
- The key will be encrypted using Windows DPAPI before being stored
- Standard OpenAI keys start with `sk-`

**Example:**
```
OpenAI API key: sk-proj-abc123...
```

### 4. Log Level

The logging verbosity level for the application.

Options:
- **DEBUG** - Detailed diagnostic information (most verbose)
- **INFO** - General informational messages (recommended)
- **WARNING** - Warning messages only
- **ERROR** - Error messages only
- **CRITICAL** - Critical errors only (least verbose)

**Example:**
```
Select log level (1-5) [default: 2]: 2
```

## Configuration File Location

The wizard saves the configuration to:

**Windows:**
```
%APPDATA%\ScannerWatcher2\config.json
```

Typically: `C:\Users\<YourUsername>\AppData\Roaming\ScannerWatcher2\config.json`

## Example Wizard Session

```
============================================================
Scanner-Watcher2 Configuration Wizard
============================================================

This wizard will help you set up Scanner-Watcher2.
You can press Ctrl+C at any time to cancel.

=== Watch Directory Configuration ===
Enter the directory path to monitor for scanned documents.
This should be an absolute path (e.g., C:\Scans)

Watch directory path: C:\Scans

Directory does not exist. Create it? (y/n): y
Created directory: C:\Scans

=== File Prefix Configuration ===
Enter the file prefix for documents to process.
Only files starting with this prefix will be detected.
Default is "SCAN-" but you can customize it (e.g., "DOC-", "LEGAL-")

File prefix [SCAN-]: LEGAL-

=== OpenAI API Key Configuration ===
Enter your OpenAI API key.
This will be encrypted and stored securely using Windows DPAPI.
You can get an API key from: https://platform.openai.com/api-keys

OpenAI API key: sk-proj-abc123def456...

=== Log Level Configuration ===
Select the logging level:
  1. DEBUG   - Detailed diagnostic information
  2. INFO    - General informational messages (recommended)
  3. WARNING - Warning messages only
  4. ERROR   - Error messages only
  5. CRITICAL - Critical errors only

Select log level (1-5) [default: 2]: 2

============================================================
Configuration Summary
============================================================
Watch Directory: C:\Scans
File Prefix:     LEGAL-
OpenAI API Key:  sk-proj...456 (will be encrypted)
Log Level:       INFO
Config File:     C:\Users\YourName\AppData\Roaming\ScannerWatcher2\config.json
============================================================

Save this configuration? (y/n): y

============================================================
Configuration saved successfully!
============================================================

Configuration file: C:\Users\YourName\AppData\Roaming\ScannerWatcher2\config.json

You can now start Scanner-Watcher2 service.
The API key has been encrypted using Windows DPAPI.
```

## Overwriting Existing Configuration

If a configuration file already exists, the wizard will ask for confirmation before overwriting:

```
Warning: Configuration file already exists at:
  C:\Users\YourName\AppData\Roaming\ScannerWatcher2\config.json

Overwrite existing configuration? (y/n):
```

## Cancelling the Wizard

You can cancel the wizard at any time by:
- Pressing `Ctrl+C`
- Answering `n` when asked to save the configuration

## Advanced Configuration

The wizard only configures the essential settings. For advanced configuration options, you can manually edit the configuration file after running the wizard.

Advanced settings include:
- Processing configuration (pages to extract, retry attempts, delays, temp directory)
- AI configuration (model, max tokens, temperature, timeout)
- Logging configuration (file size, backup count, event log)
- Service configuration (health check interval, shutdown timeout)

**Key Advanced Options**:
- **pages_to_extract**: Number of pages to extract from each PDF for AI analysis (1-10, default: 3). More pages improve classification accuracy but increase API costs and processing time.

See the [Configuration Guide](README.md#configuration) for details on all available settings.

## Validation

The wizard validates all inputs before saving:

- **Watch Directory**: Must be an absolute path and must exist (or be created)
- **API Key**: Cannot be empty
- **Log Level**: Must be one of: DEBUG, INFO, WARNING, ERROR, CRITICAL

If validation fails, the wizard will display error messages and allow you to correct the inputs.

## Security

The OpenAI API key is encrypted using Windows Data Protection API (DPAPI) before being stored in the configuration file. This provides user-level encryption that is automatically managed by Windows.

**Important:** The encrypted key can only be decrypted by the same Windows user account on the same machine. If you move the configuration file to a different machine or user account, you will need to re-run the wizard or manually update the API key.

## Next Steps

After successfully running the configuration wizard:

1. **Install the Windows Service** (if not already installed):
   ```bash
   python -m scanner_watcher2 --install-service
   ```

2. **Start the Service**:
   ```bash
   python -m scanner_watcher2 --start-service
   ```

3. **Verify the Service is Running**:
   - Open Windows Services Manager (`services.msc`)
   - Look for "Scanner-Watcher2" service
   - Check that the status is "Running"

4. **Test Document Processing**:
   - Place a PDF file with the "SCAN-" prefix in your watch directory
   - Check the logs at: `%APPDATA%\ScannerWatcher2\logs\`
   - Verify the file is processed and renamed

## Troubleshooting

### "APPDATA environment variable not set"

This error occurs if the `APPDATA` environment variable is not set. This is unusual on Windows systems. Try:
1. Restart your command prompt or PowerShell
2. Check the environment variable: `echo %APPDATA%`
3. If still not set, manually set it: `set APPDATA=%USERPROFILE%\AppData\Roaming`

### "Watch directory does not exist"

The wizard will offer to create the directory. If creation fails:
1. Check that you have write permissions to the parent directory
2. Verify the path is valid and not too long (Windows has a 260 character path limit)
3. Try creating the directory manually first

### "Failed to decrypt API key"

This can occur if:
1. The configuration file was copied from another machine or user account
2. The Windows user profile has been corrupted

Solution: Re-run the wizard to create a new configuration with a fresh encrypted API key.

## See Also

- [Installation Guide](INSTALLER.md)
- [Configuration Reference](README.md#configuration)
- [Troubleshooting Guide](README.md#troubleshooting)
