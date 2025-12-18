# Building Scanner-Watcher2

This document describes how to build the Scanner-Watcher2 Windows executable using PyInstaller.

## Prerequisites

1. **Python 3.12+** installed on Windows
2. **All dependencies** installed:
   ```bash
   pip install -e ".[dev]"
   pip install pyinstaller
   ```
3. **Windows development environment** (Windows 10, 11, or Server 2019+)

## Build Process

### Option 1: Using the Build Script (Recommended)

Simply run the provided batch script:

```bash
build.bat
```

This will:
- Clean previous builds
- Run PyInstaller with the spec file
- Create a single-file executable in `dist/scanner_watcher2.exe`

### Option 2: Manual Build

Run PyInstaller directly:

```bash
pyinstaller scanner_watcher2.spec
```

## Build Output

After a successful build, you'll find:

```
dist/
└── scanner_watcher2.exe    # Single-file executable (~50-100 MB)
```

The executable includes:
- Embedded Python 3.12 runtime
- All Python dependencies (pywin32, OpenAI SDK, PyMuPDF, etc.)
- Configuration template (config_template.json)
- User documentation (README.txt)

## Testing the Executable

### 1. Basic Functionality Test

```bash
# Copy executable to test location
copy dist\scanner_watcher2.exe C:\Temp\

# Run in console mode
cd C:\Temp
scanner_watcher2.exe --console
```

This will:
- Create default configuration at `%APPDATA%\ScannerWatcher2\config.json`
- Prompt you to edit the configuration
- Exit with instructions

### 2. Configuration Test

Edit the configuration file:
```bash
notepad %APPDATA%\ScannerWatcher2\config.json
```

Set:
- `watch_directory`: A test directory (e.g., `C:\TestScans`)
- `openai_api_key`: Your OpenAI API key

Run again:
```bash
scanner_watcher2.exe --console
```

### 3. Service Installation Test (Requires Administrator)

```bash
# Install service
scanner_watcher2.exe --install-service

# Start service
scanner_watcher2.exe --start-service

# Check service status in Services Manager (services.msc)
# Look for "ScannerWatcher2"

# Stop service
scanner_watcher2.exe --stop-service

# Remove service
scanner_watcher2.exe --remove-service
```

### 4. Document Processing Test

1. Create the watch directory (e.g., `C:\TestScans`)
2. Start the service or run in console mode
3. Copy a PDF file with "SCAN-" prefix to the watch directory
4. Verify the file is processed and renamed
5. Check logs at `%APPDATA%\ScannerWatcher2\logs\`

## Testing on Clean Windows Machine

To ensure the executable works on machines without Python:

1. **Prepare a clean Windows VM or machine**:
   - Windows 10, 11, or Server 2019+
   - No Python installed
   - No development tools

2. **Copy only the executable**:
   ```
   scanner_watcher2.exe
   ```

3. **Test all functionality**:
   - Console mode
   - Service installation
   - Document processing
   - Configuration management

4. **Verify no dependencies required**:
   - Should work without any additional installations
   - Should not require Python, Visual C++ redistributables, etc.

## Common Build Issues

### Issue: PyInstaller not found

**Solution**: Install PyInstaller
```bash
pip install pyinstaller
```

### Issue: Missing pywin32 modules

**Solution**: Ensure pywin32 is installed correctly
```bash
pip install --upgrade pywin32
python Scripts/pywin32_postinstall.py -install
```

### Issue: Import errors during build

**Solution**: Add missing modules to `hiddenimports` in `scanner_watcher2.spec`

### Issue: Executable too large

**Solution**: 
- Enable UPX compression (already enabled in spec)
- Exclude unnecessary modules in `excludes` section
- Consider using `--onedir` instead of `--onefile` (requires spec modification)

### Issue: Runtime errors in executable

**Solution**:
- Test with `console=True` in spec file to see error messages
- Check for missing data files in `datas` section
- Verify all hidden imports are included

## Build Optimization

### Reducing Executable Size

1. **Enable UPX compression** (already enabled):
   ```python
   upx=True
   ```

2. **Exclude unnecessary modules**:
   ```python
   excludes=['pytest', 'hypothesis', 'tkinter', ...]
   ```

3. **Strip debug symbols** (already enabled):
   ```python
   strip=False  # Set to True on Linux/Mac
   ```

### Improving Build Speed

1. **Use build cache**:
   - PyInstaller caches analysis results
   - Subsequent builds are faster

2. **Parallel processing**:
   - PyInstaller uses multiple cores automatically

## Troubleshooting

### Build fails with "module not found"

Check that all dependencies are installed:
```bash
pip list | findstr "pywin32 openai PyMuPDF"
```

### Executable crashes on startup

Build with console enabled to see errors:
```python
# In scanner_watcher2.spec
console=True  # Change from False
```

### Service installation fails

Ensure you're running as Administrator:
```bash
# Right-click Command Prompt -> Run as Administrator
scanner_watcher2.exe --install-service
```

## Next Steps

After successful build and testing:

1. **Create installer** using Inno Setup
   - See [INSTALLER.md](INSTALLER.md) for detailed instructions
   - Run `build_installer.bat` to create the installer
2. **Sign the executable** with code signing certificate (optional)
3. **Test on multiple Windows versions** (Windows 10, 11, Server 2019+)
4. **Document deployment procedures**

## Building the Installer

Once you have successfully built the executable, you can create a professional Windows installer:

### Quick Start

```bash
# Build the installer (requires Inno Setup 6)
build_installer.bat
```

This creates: `dist\scanner-watcher2-setup-1.0.0.exe`

### What the Installer Does

- Installs to `C:\Program Files\ScannerWatcher2\`
- Creates AppData directories for configuration and logs
- Installs and configures the Windows service
- Creates Start Menu shortcuts
- Provides interactive setup for watch directory and API key
- Handles clean uninstallation

### Requirements

- Inno Setup 6: https://jrsoftware.org/isdl.php
- Built executable: `dist\scanner_watcher2.exe`

For complete installer documentation, see [INSTALLER.md](INSTALLER.md)

## Additional Resources

- [PyInstaller Documentation](https://pyinstaller.org/en/stable/)
- [PyInstaller Windows Notes](https://pyinstaller.org/en/stable/operating-mode.html#windows)
- [pywin32 Documentation](https://github.com/mhammond/pywin32)
