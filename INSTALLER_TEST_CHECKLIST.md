# Scanner-Watcher2 Installer Testing Checklist

Use this checklist to verify the installer works correctly on Windows 10 and Windows 11.

## Pre-Testing Setup

- [ ] Build the PyInstaller executable: `build.bat`
- [ ] Build the installer: `build_installer.bat`
- [ ] Verify installer exists: `dist\scanner-watcher2-setup-1.0.0.exe`
- [ ] Prepare test VMs or clean Windows machines
- [ ] Have OpenAI API key ready for testing

## Test Environment 1: Windows 10 (Clean Install)

### System Information
- OS Version: Windows 10 _________
- Architecture: x64
- Python Installed: No
- Previous Version: None

### Installation Testing

#### Installer Launch
- [ ] Double-click installer runs without errors
- [ ] UAC prompt appears (if not admin)
- [ ] Welcome screen displays correctly
- [ ] Application description is clear

#### License Agreement
- [ ] License text displays (MIT License)
- [ ] "I accept the agreement" checkbox works
- [ ] Cannot proceed without accepting

#### Installation Directory
- [ ] Default directory is `C:\Program Files\ScannerWatcher2\`
- [ ] Can change directory if desired
- [ ] Directory validation works

#### Watch Directory Selection (Custom Page)
- [ ] Custom page appears
- [ ] Default is `C:\Scans`
- [ ] Can browse and select different directory
- [ ] Validation prevents empty directory

#### API Key Entry (Custom Page)
- [ ] Custom page appears
- [ ] Can enter API key
- [ ] Can skip (with warning)
- [ ] Validation checks key length
- [ ] Warning appears if key is too short

#### Installation Progress
- [ ] Progress bar shows installation
- [ ] Status messages are clear
- [ ] No errors during file copy
- [ ] Service installation succeeds

#### Completion
- [ ] Completion screen displays
- [ ] Option to start service is available
- [ ] Finish button works

### Post-Installation Verification

#### Files and Directories
- [ ] Program Files directory exists: `C:\Program Files\ScannerWatcher2\`
- [ ] Executable exists: `C:\Program Files\ScannerWatcher2\scanner_watcher2.exe`
- [ ] Config template exists: `C:\Program Files\ScannerWatcher2\config_template.json`
- [ ] README exists: `C:\Program Files\ScannerWatcher2\README.txt`
- [ ] LICENSE exists: `C:\Program Files\ScannerWatcher2\LICENSE.txt`

#### AppData Structure
- [ ] AppData directory exists: `%APPDATA%\ScannerWatcher2\`
- [ ] Config file exists: `%APPDATA%\ScannerWatcher2\config.json`
- [ ] Logs directory exists: `%APPDATA%\ScannerWatcher2\logs\`
- [ ] Temp directory exists: `%APPDATA%\ScannerWatcher2\temp\`

#### Configuration File
- [ ] Config file is valid JSON
- [ ] Watch directory matches user selection
- [ ] API key matches user entry (if provided)
- [ ] All required fields present
- [ ] Default values are correct

#### Windows Service
- [ ] Service appears in Services Manager (services.msc)
- [ ] Service name: "ScannerWatcher2"
- [ ] Display name: "Scanner-Watcher2 Document Processing Service"
- [ ] Startup type: Automatic (Delayed Start)
- [ ] Service status: Stopped (or Running if user selected start)

#### Start Menu Shortcuts
- [ ] Start Menu folder exists: "Scanner-Watcher2"
- [ ] "Scanner-Watcher2 Configuration" shortcut exists
- [ ] "Scanner-Watcher2 Logs" shortcut exists
- [ ] "Start Scanner-Watcher2 Service" shortcut exists
- [ ] "Stop Scanner-Watcher2 Service" shortcut exists
- [ ] "Uninstall Scanner-Watcher2" shortcut exists

#### Desktop Icon (if selected)
- [ ] Desktop shortcut exists (if option was selected)
- [ ] Desktop shortcut opens configuration file

### Functional Testing

#### Configuration Shortcut
- [ ] Click "Scanner-Watcher2 Configuration" in Start Menu
- [ ] Notepad opens with config.json
- [ ] Can edit and save configuration

#### Logs Shortcut
- [ ] Click "Scanner-Watcher2 Logs" in Start Menu
- [ ] Explorer opens logs directory
- [ ] Directory is accessible

#### Start Service Shortcut
- [ ] Click "Start Scanner-Watcher2 Service" in Start Menu
- [ ] Service starts successfully
- [ ] No error messages
- [ ] Service status changes to "Running" in Services Manager

#### Service Operation
- [ ] Create watch directory (if it doesn't exist)
- [ ] Copy a test PDF with "SCAN-" prefix to watch directory
- [ ] Wait 5-10 seconds
- [ ] Verify file is processed (renamed or error logged)
- [ ] Check logs directory for log files
- [ ] Verify log entries are created

#### Stop Service Shortcut
- [ ] Click "Stop Scanner-Watcher2 Service" in Start Menu
- [ ] Service stops successfully
- [ ] Service status changes to "Stopped" in Services Manager

#### Service Auto-Start
- [ ] Reboot the machine
- [ ] After reboot, check Services Manager
- [ ] Service should start automatically (Delayed Start)
- [ ] Verify service is running after ~2 minutes

### Uninstallation Testing

#### Uninstall Process
- [ ] Click "Uninstall Scanner-Watcher2" in Start Menu
- [ ] Uninstaller launches
- [ ] Prompt asks about keeping config/logs
- [ ] Select "Yes" to keep config/logs
- [ ] Uninstallation completes without errors

#### Post-Uninstall Verification (Keep Config)
- [ ] Program Files directory removed
- [ ] Start Menu shortcuts removed
- [ ] Desktop icon removed (if it existed)
- [ ] Service removed from Services Manager
- [ ] AppData directory still exists
- [ ] Config file still exists
- [ ] Logs still exist

#### Reinstall and Uninstall (Remove Everything)
- [ ] Reinstall the application
- [ ] Verify installation works
- [ ] Run uninstaller again
- [ ] Select "No" to remove everything
- [ ] AppData directory removed
- [ ] Config file removed
- [ ] Logs removed

---

## Test Environment 2: Windows 11 (Clean Install)

### System Information
- OS Version: Windows 11 _________
- Architecture: x64
- Python Installed: No
- Previous Version: None

### Repeat All Tests from Windows 10

- [ ] Installer Launch
- [ ] License Agreement
- [ ] Installation Directory
- [ ] Watch Directory Selection
- [ ] API Key Entry
- [ ] Installation Progress
- [ ] Completion
- [ ] Files and Directories
- [ ] AppData Structure
- [ ] Configuration File
- [ ] Windows Service
- [ ] Start Menu Shortcuts
- [ ] Desktop Icon
- [ ] Configuration Shortcut
- [ ] Logs Shortcut
- [ ] Start Service Shortcut
- [ ] Service Operation
- [ ] Stop Service Shortcut
- [ ] Service Auto-Start
- [ ] Uninstall Process
- [ ] Post-Uninstall Verification

### Windows 11 Specific Tests

- [ ] Installer UI renders correctly with Windows 11 theme
- [ ] Start Menu integration works with Windows 11 layout
- [ ] Service works with Windows 11 security features
- [ ] No compatibility warnings or issues

---

## Test Environment 3: Upgrade Scenario

### System Information
- OS Version: Windows 10/11 _________
- Previous Version: 1.0.0 (installed)
- Upgrade To: 1.0.0 (same version)

### Upgrade Testing

#### Pre-Upgrade State
- [ ] Install version 1.0.0
- [ ] Configure with custom settings
- [ ] Process some test files
- [ ] Verify logs are created
- [ ] Note current configuration

#### Upgrade Installation
- [ ] Run installer for same version
- [ ] Installer detects existing installation
- [ ] Installation proceeds
- [ ] No errors during upgrade

#### Post-Upgrade Verification
- [ ] Configuration file preserved
- [ ] Custom settings intact
- [ ] Logs preserved
- [ ] Service updated correctly
- [ ] No duplicate shortcuts
- [ ] Service still works
- [ ] Can process files

---

## Test Environment 4: Non-Administrator User

### System Information
- OS Version: Windows 10/11 _________
- User Account: Standard User (not admin)

### Installation with Standard User

- [ ] Run installer as standard user
- [ ] UAC prompt appears requesting elevation
- [ ] Enter admin credentials
- [ ] Installation proceeds normally
- [ ] All features work after installation

---

## Test Environment 5: Corporate/Domain Environment

### System Information
- OS Version: Windows 10/11 _________
- Domain: Joined to Active Directory
- Group Policies: Applied

### Corporate Environment Testing

- [ ] Installer runs on domain-joined machine
- [ ] Service installs correctly
- [ ] Service runs under correct account
- [ ] Network drive can be used as watch directory
- [ ] Proxy settings work (if configured)
- [ ] No conflicts with group policies

---

## Test Environment 6: Network Drive Scenario

### System Information
- OS Version: Windows 10/11 _________
- Watch Directory: Network share (e.g., `\\server\scans`)

### Network Drive Testing

- [ ] Configure watch directory as network path
- [ ] Service starts successfully
- [ ] Service can access network directory
- [ ] Files on network share are detected
- [ ] Files on network share are processed
- [ ] Network disconnection handled gracefully
- [ ] Service recovers when network returns

---

## Edge Cases and Error Scenarios

### Invalid Configuration

- [ ] Install with invalid API key
- [ ] Service fails to start (expected)
- [ ] Error logged to Windows Event Log
- [ ] Error message is clear

### Missing Watch Directory

- [ ] Install with non-existent watch directory
- [ ] Service starts but logs warning
- [ ] Health check detects missing directory
- [ ] Service continues running

### Disk Space Issues

- [ ] Install with low disk space
- [ ] Installer handles gracefully
- [ ] Clear error message if installation fails

### Corrupted Installation

- [ ] Delete executable after installation
- [ ] Service fails to start (expected)
- [ ] Uninstaller still works
- [ ] Can reinstall to fix

---

## Performance Testing

### Installation Performance

- [ ] Installation completes in < 2 minutes
- [ ] No excessive disk I/O
- [ ] No excessive CPU usage

### Service Performance

- [ ] Service starts in < 10 seconds
- [ ] Idle CPU usage < 5%
- [ ] Idle memory usage < 200 MB
- [ ] File processing works efficiently

---

## Documentation Verification

### Installer Messages

- [ ] Welcome message is clear and accurate
- [ ] License text is correct
- [ ] Completion message provides next steps
- [ ] Error messages are helpful

### Included Documentation

- [ ] README.txt is accurate
- [ ] README.txt provides clear instructions
- [ ] Configuration examples are correct
- [ ] Troubleshooting section is helpful

---

## Final Checklist

### Before Release

- [ ] All tests passed on Windows 10
- [ ] All tests passed on Windows 11
- [ ] Upgrade scenario tested
- [ ] Network drive scenario tested
- [ ] Documentation reviewed and accurate
- [ ] Known issues documented
- [ ] Support contact information correct

### Optional (Recommended)

- [ ] Code sign the installer
- [ ] Generate SHA256 checksum
- [ ] Create release notes
- [ ] Prepare support documentation

---

## Test Results Summary

### Windows 10 Test Results
- Date: ___________
- Tester: ___________
- Result: PASS / FAIL
- Notes: ___________

### Windows 11 Test Results
- Date: ___________
- Tester: ___________
- Result: PASS / FAIL
- Notes: ___________

### Issues Found
1. ___________
2. ___________
3. ___________

### Recommendations
1. ___________
2. ___________
3. ___________

---

## Sign-Off

- [ ] All critical tests passed
- [ ] All issues documented
- [ ] Installer ready for distribution

Tested by: ___________
Date: ___________
Signature: ___________
