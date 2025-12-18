@echo off
REM Build script for Scanner-Watcher2 installer
REM This script builds the PyInstaller executable and then creates the Inno Setup installer

echo ========================================
echo Scanner-Watcher2 Installer Build Script
echo ========================================
echo.

REM Check if PyInstaller executable exists
if not exist "dist\scanner_watcher2.exe" (
    echo ERROR: scanner_watcher2.exe not found in dist\ directory
    echo Please run build.bat first to create the executable
    echo.
    pause
    exit /b 1
)

REM Check if Inno Setup is installed
set INNO_SETUP="C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if not exist %INNO_SETUP% (
    echo ERROR: Inno Setup not found at %INNO_SETUP%
    echo Please install Inno Setup 6 from https://jrsoftware.org/isdl.php
    echo.
    pause
    exit /b 1
)

echo Building installer with Inno Setup...
echo.

REM Build the installer
%INNO_SETUP% scanner_watcher2.iss

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo Installer built successfully!
    echo ========================================
    echo.
    echo Output: dist\scanner-watcher2-setup-1.0.0.exe
    echo.
    echo You can now distribute this installer to end users.
    echo.
) else (
    echo.
    echo ========================================
    echo ERROR: Installer build failed
    echo ========================================
    echo.
    echo Check the output above for error messages.
    echo.
)

pause
