# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller specification file for Scanner-Watcher2.

This spec file configures PyInstaller to create a single-file executable
for Windows with all dependencies bundled, including:
- Embedded Python runtime
- All Python dependencies
- Configuration template and documentation
- Hidden imports for pywin32 modules

Usage:
    pyinstaller scanner_watcher2.spec

Output:
    dist/scanner_watcher2.exe - Single-file executable
"""

block_cipher = None

a = Analysis(
    ['src/scanner_watcher2/__main__.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('config_template.json', '.'),
        ('README.txt', '.'),
    ],
    hiddenimports=[
        # pywin32 modules that may not be auto-detected
        'win32timezone',
        'win32service',
        'win32serviceutil',
        'win32event',
        'win32evtlog',
        'win32evtlogutil',
        'servicemanager',
        'pywintypes',
        'win32api',
        'win32con',
        'win32file',
        # OpenAI SDK dependencies
        'openai',
        'openai.types',
        'openai.resources',
        # PDF processing
        'fitz',
        'PyPDF2',
        'PIL',
        'PIL.Image',
        # Logging
        'structlog',
        'structlog.processors',
        # Pydantic
        'pydantic',
        'pydantic.fields',
        'pydantic_core',
        # Watchdog
        'watchdog',
        'watchdog.observers',
        'watchdog.events',
        # Other dependencies
        'psutil',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude test modules
        'pytest',
        'hypothesis',
        'unittest',
        # Exclude development tools
        'black',
        'mypy',
        'ruff',
        # Exclude unnecessary standard library modules
        'tkinter',
        'test',
        'distutils',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='scanner_watcher2',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # No console window for Windows service
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # TODO: Add icon file when available (e.g., 'windows/icon.ico')
)
