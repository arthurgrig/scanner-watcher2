# Quick Build Guide

## Prerequisites

```bash
pip install pyinstaller
```

## Build

```bash
# Windows
build.bat

# Or manually
pyinstaller scanner_watcher2.spec
```

## Output

```
dist/scanner_watcher2.exe
```

## Quick Test

```bash
# Copy to test location
copy dist\scanner_watcher2.exe C:\Temp\

# Run in console mode
cd C:\Temp
scanner_watcher2.exe --console
```

## Files Included in Executable

- Python 3.12 runtime (embedded)
- All dependencies (pywin32, OpenAI SDK, PyMuPDF, etc.)
- config_template.json
- README.txt

## Common Issues

### PyInstaller not found
```bash
pip install pyinstaller
```

### pywin32 issues
```bash
pip install --upgrade pywin32
python Scripts/pywin32_postinstall.py -install
```

### Build fails
- Check all dependencies are installed: `pip list`
- Verify Python version: `python --version` (should be 3.12+)
- Check spec file syntax: `python -c "import ast; ast.parse(open('scanner_watcher2.spec').read())"`

## Next Steps

1. Test executable on clean Windows machine (see TESTING_CHECKLIST.md)
2. Create installer with Inno Setup (task 16)
3. Deploy to production

## Documentation

- Full build instructions: BUILD.md
- Testing checklist: TESTING_CHECKLIST.md
- User documentation: README.txt
