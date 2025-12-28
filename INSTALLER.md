# Scanner-Watcher2 Installer Guide

This document describes the Inno Setup installer for Scanner-Watcher2 and how to build and test it.

## Overview

The installer (`scanner_watcher2.iss`) creates a professional Windows installation package that:

1. **Installs the application** to `C:\Program Files\ScannerWatcher2\`
2. **Creates AppData directories** at `%APPDATA%\ScannerWatcher2\` for configuration, logs, and temporary files
3. **Copies configuration template** to user's AppData directory
4. **Installs Windows service** automatically during installation
5. **Creates Start Menu shortcuts** for configuration, logs, and service management
6. **Provides interactive setup** with custom wizard pages for watch directory and API key
7. **Handles clean uninstallation** with option to preserve configuration and logs

## Prerequisites

### For Building the Installer

1. **PyInstaller executable**: Run `build.bat` first to create `dist\scanner_watcher2.exe`
2. **Inno Setup 6**: Download from https://jrsoftware.org/isdl.php
3. **Required files**:
   - `dist\scanner_watcher2.exe` (built by PyInstaller)
   - `config_template.json`
   - `README.txt`
   - `README.md`
   - `LICENSE.txt`
4. **Optional assets** (in `windows\` directory):
   - `icon.ico` - Application icon
   - `wizard-image.bmp` - Large wizard image (164x314 pixels)
   - `wizard-small-image.bmp` - Small wizard image (55x58 pixels)

### For Testing the Installer

1. **Windows 10 or Windows 11** test machine
2. **Administrator privileges** for service installation
3. **Clean test environment** (VM recommended)
4. **OpenAI API key** for functional testing

## Building the Installer

### Method 1: Using the Build Script (Recommended)

```batch
REM First, build the PyInstaller executable
build.bat

REM Then, build the installer
build_installer.bat
```

### Method 2: Manual Build

```batch
REM Build PyInstaller executable
python -m PyInstaller scanner_watcher2.spec

REM Build Inno Setup installer
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" scanner_watcher2.iss
```

Note: If Inno Setup is installed in a different location, check:
- `C:\Program Files\Inno Setup 6\ISCC.exe`
- Your Start Menu for "Inno Setup Compiler"
- Update the path in `build_installer.bat` if needed

### Output

The installer will be created at:
```
dist\scanner-watcher2-setup-1.0.0.exe
```

## Installer Features

### Installation Process

1. **Welcome Screen**: Introduces the application
2. **License Agreement**: Displays MIT license
3. **Installation Directory**: Default to `C:\Program Files\ScannerWatcher2\`
4. **Watch Directory Selection**: Custom page to select where scanner saves files
5. **API Key Configuration**: Custom page to enter OpenAI API key
6. **Ready to Install**: Summary of installation settings
7. **Installing**: Progress bar showing installation
8. **Completing**: Option to start service immediately

### Post-Installation Actions

The installer automatically:

1. Creates directory structure:
   ```
   %APPDATA%\ScannerWatcher2\
   ├── config.json (from template)
   ├── logs\
   └── temp\
   ```

2. Updates `config.json` with:
   - User-specified watch directory
   - User-provided OpenAI API key (if entered)

3. Installs Windows service:
   ```
   scanner_watcher2.exe --install-service
   ```

4. Optionally starts the service (user choice)

### Start Menu Shortcuts

The installer creates the following shortcuts in the Start Menu:

- **Scanner-Watcher2 Configuration**: Opens config.json in Notepad
- **Scanner-Watcher2 Logs**: Opens the logs directory
- **Start Scanner-Watcher2 Service**: Starts the Windows service
- **Stop Scanner-Watcher2 Service**: Stops the Windows service
- **Uninstall Scanner-Watcher2**: Runs the uninstaller

### Desktop Icon (Optional)

If user selects the desktop icon option:
- **Scanner-Watcher2 Configuration**: Desktop shortcut to edit config.json

## Uninstallation Process

### What Gets Removed

The uninstaller automatically:

1. **Stops the Windows service** (if running)
2. **Removes the Windows service** registration
3. **Deletes application files** from Program Files
4. **Removes Start Menu shortcuts**
5. **Cleans up temporary files** from AppData

### What Gets Preserved (Optional)

The uninstaller prompts the user:
> "Do you want to keep your configuration and log files?"

- **Yes**: Preserves `%APPDATA%\ScannerWatcher2\` (configuration and logs)
- **No**: Removes everything including configuration and logs

## Testing the Installer

### Test Checklist

#### Installation Testing

- [ ] **Fresh Install on Windows 10**
  - [ ] Installer runs without errors
  - [ ] All files copied to Program Files
  - [ ] AppData directories created
  - [ ] Configuration file created with user settings
  - [ ] Windows service installed successfully
  - [ ] Start Menu shortcuts created
  - [ ] Desktop icon created (if selected)

- [ ] **Fresh Install on Windows 11**
  - [ ] Same checks as Windows 10

- [ ] **Custom Configuration**
  - [ ] Watch directory path is correctly saved
  - [ ] API key is correctly saved (if provided)
  - [ ] Configuration file is valid JSON

- [ ] **Service Installation**
  - [ ] Service appears in Windows Services Manager
  - [ ] Service name: "ScannerWatcher2"
  - [ ] Display name: "Scanner-Watcher2 Document Processing Service"
  - [ ] Startup type: Automatic (Delayed Start)
  - [ ] Service can be started manually
  - [ ] Service starts automatically after reboot

#### Functional Testing

- [ ] **Service Operation**
  - [ ] Service starts successfully
  - [ ] Service processes files correctly
  - [ ] Logs are written to AppData\logs
  - [ ] Configuration changes are detected
  - [ ] Service stops gracefully

- [ ] **Start Menu Shortcuts**
  - [ ] Configuration shortcut opens config.json
  - [ ] Logs shortcut opens logs directory
  - [ ] Start service shortcut works
  - [ ] Stop service shortcut works

#### Uninstallation Testing

- [ ] **Clean Uninstall**
  - [ ] Service stops before uninstall
  - [ ] Service is removed from Services Manager
  - [ ] Program Files directory removed
  - [ ] Start Menu shortcuts removed
  - [ ] Desktop icon removed (if created)
  - [ ] User prompted about keeping config/logs

- [ ] **Preserve Configuration**
  - [ ] Selecting "Yes" preserves AppData directory
  - [ ] Configuration file remains intact
  - [ ] Log files remain intact

- [ ] **Remove Everything**
  - [ ] Selecting "No" removes AppData directory
  - [ ] All configuration removed
  - [ ] All logs removed

#### Upgrade Testing

- [ ] **Install Over Existing Version**
  - [ ] Existing configuration preserved
  - [ ] Existing logs preserved
  - [ ] Service updated correctly
  - [ ] No duplicate shortcuts created

### Test Environments

#### Minimum Test Matrix

| OS | Architecture | Test Type |
|---|---|---|
| Windows 10 21H2 | x64 | Fresh install, functional, uninstall |
| Windows 11 22H2 | x64 | Fresh install, functional, uninstall |
| Windows Server 2019 | x64 | Fresh install, service operation |

#### Recommended Test Scenarios

1. **Clean VM**: Fresh Windows installation, no development tools
2. **User Account**: Non-administrator account (should prompt for elevation)
3. **Corporate Environment**: Domain-joined machine with group policies
4. **Network Drive**: Watch directory on network share
5. **Upgrade Path**: Install v1.0.0, then install v1.0.1 over it

## Troubleshooting

### Build Issues

**Problem**: Inno Setup not found
```
Solution: Install Inno Setup 6 from https://jrsoftware.org/isdl.php
          
          Check these common installation locations:
          - C:\Program Files (x86)\Inno Setup 6\ISCC.exe
          - C:\Program Files\Inno Setup 6\ISCC.exe
          
          Or search your Start Menu for "Inno Setup Compiler"
          
          Update the INNO_SETUP variable in build_installer.bat with the correct path
```

**Problem**: scanner_watcher2.exe not found
```
Solution: Run build.bat first to create the PyInstaller executable
```

**Problem**: Icon files not found
```
Solution: Either create the icon files in windows\ directory
          Or comment out the icon lines in scanner_watcher2.iss:
          ; SetupIconFile=windows\icon.ico
          ; WizardImageFile=windows\wizard-image.bmp
          ; WizardSmallImageFile=windows\wizard-small-image.bmp
```

### Installation Issues

**Problem**: Service installation fails
```
Solution: Ensure installer is run with administrator privileges
          Check Windows Event Log for error details
```

**Problem**: Configuration not updated with user values
```
Solution: Check that config_template.json exists in app directory
          Verify JSON syntax is valid
```

**Problem**: Shortcuts don't work
```
Solution: Verify paths in shortcuts are correct
          Check that AppData directory was created
```

### Runtime Issues

**Problem**: Service won't start after installation
```
Solution: Check configuration file is valid
          Verify OpenAI API key is correct
          Ensure watch directory exists
          Review Windows Event Log
```

## Customization

### Branding

To customize the installer appearance:

1. **Application Icon**: Replace `windows\icon.ico`
2. **Wizard Images**: Replace `windows\wizard-image.bmp` and `windows\wizard-small-image.bmp`
3. **Company Name**: Update `MyAppPublisher` in scanner_watcher2.iss
4. **Product URL**: Update `MyAppURL` in scanner_watcher2.iss

### Installation Options

To modify installation behavior, edit scanner_watcher2.iss:

- **Default install directory**: Change `DefaultDirName`
- **Require admin**: Change `PrivilegesRequired`
- **Compression**: Change `Compression` (lzma, zip, bzip)
- **Minimum Windows version**: Change `MinVersion`

### Custom Wizard Pages

The installer includes custom wizard pages for:
- Watch directory selection
- OpenAI API key entry

To add more custom pages, modify the `[Code]` section in scanner_watcher2.iss.

## Distribution

### Signing the Installer (Recommended)

For production distribution, sign the installer with a code signing certificate:

```batch
signtool sign /f certificate.pfx /p password /t http://timestamp.digicert.com dist\scanner-watcher2-setup-1.0.0.exe
```

### Checksums

Generate checksums for verification:

```batch
certutil -hashfile dist\scanner-watcher2-setup-1.0.0.exe SHA256
```

### Distribution Checklist

- [ ] Installer built successfully
- [ ] Tested on Windows 10 and Windows 11
- [ ] Code signed (if applicable)
- [ ] Checksums generated
- [ ] Release notes prepared
- [ ] Documentation updated
- [ ] Support contact information verified

## Version Updates

When releasing a new version:

1. Update version in `scanner_watcher2.iss`:
   ```
   #define MyAppVersion "1.0.1"
   ```

2. Update version in `pyproject.toml`

3. Update version in `config_template.json`

4. Rebuild both executable and installer

5. Test upgrade path from previous version

## Support

For issues with the installer:
1. Check Windows Event Log (Application)
2. Review installer log at `%TEMP%\Setup Log YYYY-MM-DD #NNN.txt`
3. Test in clean VM environment
4. Contact development team with log files

## References

- Inno Setup Documentation: https://jrsoftware.org/ishelp/
- Inno Setup Examples: https://jrsoftware.org/isinfo.php
- Windows Installer Best Practices: https://docs.microsoft.com/en-us/windows/win32/msi/windows-installer-best-practices
