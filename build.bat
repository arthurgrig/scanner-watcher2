@echo off
REM Build script for Scanner-Watcher2 Windows executable
REM This script builds the single-file executable using PyInstaller

echo ========================================
echo Scanner-Watcher2 Build Script
echo ========================================
echo.

REM Check if PyInstaller is installed
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo ERROR: PyInstaller is not installed
    echo Please install it with: pip install pyinstaller
    exit /b 1
)

REM Clean previous builds
echo Cleaning previous builds...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
echo.

REM Build executable
echo Building executable with PyInstaller...
pyinstaller scanner_watcher2.spec
if errorlevel 1 (
    echo.
    echo ERROR: Build failed
    exit /b 1
)

echo.
echo ========================================
echo Build completed successfully!
echo ========================================
echo.
echo Executable location: dist\scanner_watcher2.exe
echo.
echo To test the executable:
echo   1. Copy dist\scanner_watcher2.exe to a test location
echo   2. Run: scanner_watcher2.exe --console
echo   3. Follow the prompts to configure
echo.
echo To install as Windows service:
echo   1. Run as Administrator: scanner_watcher2.exe --install-service
echo   2. Start service: scanner_watcher2.exe --start-service
echo.

pause
