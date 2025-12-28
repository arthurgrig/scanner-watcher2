# Workflow Validation Guide

This guide explains how to validate GitHub Actions workflows and build configurations locally before committing changes.

## Quick Start

### Automated Validation (Recommended)

```bash
# Install validation dependencies
pip install yamllint

# Run validation script
python validate_workflows.py

# On Windows, run full validation including builds
python validate_workflows.py --full
```

## Validation Levels

### Basic Validation (All Platforms)

Validates configuration files without building:

- ✓ YAML syntax for workflow files
- ✓ PyInstaller spec file structure
- ✓ Inno Setup script structure

**Command**: `python validate_workflows.py`

**Time**: ~5 seconds

### Full Validation (Windows Only)

Includes actual build testing:

- ✓ All basic validations
- ✓ PyInstaller executable build
- ✓ Inno Setup installer compilation
- ✓ Output file verification

**Command**: `python validate_workflows.py --full`

**Time**: ~5-10 minutes

**Requirements**:
- Windows 10 or later
- Python 3.12+
- All dependencies installed: `pip install -e ".[dev]"`
- Inno Setup installed: `choco install innosetup`

## Manual Validation Steps

If you prefer to validate manually or need to debug specific issues:

### 1. YAML Syntax Validation

```bash
# Install yamllint
pip install yamllint

# Validate all workflow files
yamllint -c .yamllint .github/workflows/*.yml
```

**Expected Output**: No errors (exit code 0)

### 2. PyInstaller Spec Validation

```bash
# Check spec file exists
ls scanner_watcher2.spec

# Verify required sections (manual inspection)
# - Analysis
# - PYZ
# - EXE
# - hiddenimports list
```

### 3. Inno Setup Script Validation

```bash
# Check script exists
ls scanner_watcher2.iss

# Verify required sections (manual inspection)
# - [Setup]
# - [Files]
# - [Icons]
# - [Run]
# - [UninstallRun]
```

### 4. PyInstaller Build Test (Windows Only)

```bash
# Install dependencies
pip install -e ".[dev]"

# Build executable
pyinstaller scanner_watcher2.spec

# Verify output
dir dist\scanner_watcher2.exe

# Check executable size (should be ~50-100 MB)
```

**Common Issues**:
- Missing dependencies: Check `pyproject.toml` and install all packages
- Hidden import errors: Add missing modules to `hiddenimports` in spec file
- File not found: Ensure `config_template.json` and `README.txt` exist

### 5. Inno Setup Compilation Test (Windows Only)

```bash
# Install Inno Setup (if not already installed)
choco install innosetup -y

# Compile installer
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" scanner_watcher2.iss

# Verify output
dir Output\scanner-watcher2-setup-*.exe

# Check installer size (should be ~50-100 MB)
```

**Common Issues**:
- Executable not found: Run PyInstaller build first
- Path errors: Ensure all file paths in `.iss` are correct
- Missing files: Check that all referenced files exist

## Validation Checklist

Use this checklist before committing workflow changes:

### Pre-Commit Checklist

- [ ] Run `python validate_workflows.py` - all checks pass
- [ ] YAML files have no syntax errors
- [ ] Spec file has all required sections
- [ ] Inno Setup script has all required sections

### Windows Pre-Commit Checklist (Additional)

- [ ] Run `python validate_workflows.py --full` - all checks pass
- [ ] PyInstaller build completes successfully
- [ ] Executable file is created in `dist/`
- [ ] Inno Setup compilation completes successfully
- [ ] Installer file is created in `Output/`
- [ ] Executable runs without immediate errors
- [ ] Installer installs without errors
- [ ] Installer uninstalls cleanly

### Post-Push Checklist

- [ ] CI workflow runs successfully on GitHub Actions
- [ ] All tests pass on Windows runner
- [ ] Build job completes successfully
- [ ] Executable artifact is created and downloadable
- [ ] No warnings or errors in workflow logs

### Release Checklist (Additional)

- [ ] Release workflow triggers on tag push
- [ ] Installer is compiled successfully
- [ ] GitHub release is created
- [ ] Installer is attached to release
- [ ] Release notes are generated
- [ ] Installer downloads and installs correctly

## Troubleshooting

### Validation Script Issues

**Problem**: `yamllint: command not found`

**Solution**:
```bash
pip install yamllint
```

**Problem**: `ModuleNotFoundError` when running validation script

**Solution**:
```bash
# Ensure you're in the virtual environment
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

# Install dependencies
pip install -e ".[dev]"
```

### YAML Validation Issues

**Problem**: Trailing spaces errors

**Solution**:
```bash
# Remove trailing spaces (macOS/Linux)
sed -i 's/[[:space:]]*$//' .github/workflows/*.yml

# Remove trailing spaces (Windows PowerShell)
(Get-Content file.yml) | ForEach-Object { $_.TrimEnd() } | Set-Content file.yml
```

**Problem**: Line too long errors

**Solution**: Break long lines or adjust `.yamllint` configuration

### PyInstaller Build Issues

**Problem**: Missing module errors

**Solution**: Add missing modules to `hiddenimports` in `scanner_watcher2.spec`

**Problem**: File not found errors

**Solution**: Ensure all files in `datas` list exist and paths are correct

**Problem**: Build succeeds but executable crashes

**Solution**:
1. Run executable from command line to see error messages
2. Check for missing DLLs or dependencies
3. Add missing imports to `hiddenimports`
4. Verify all data files are included

### Inno Setup Compilation Issues

**Problem**: Inno Setup not found

**Solution**:
```bash
# Install via Chocolatey
choco install innosetup -y

# Or download from https://jrsoftware.org/isinfo.php
```

**Problem**: File not found during compilation

**Solution**: Verify all file paths in `scanner_watcher2.iss` are correct

**Problem**: Syntax errors in script

**Solution**: Use Inno Setup IDE to validate script syntax

## Platform-Specific Notes

### macOS / Linux

- Basic validation works on all platforms
- Full validation (builds) requires Windows
- Use validation script to catch configuration issues early
- Test actual builds on Windows before committing

### Windows

- Full validation is available
- Run `validate_workflows.py --full` before committing build changes
- Ensure Inno Setup is installed for installer testing
- Test both executable and installer before pushing

## Integration with Development Workflow

### Recommended Workflow

1. **Make changes** to workflows or build configurations
2. **Run basic validation**: `python validate_workflows.py`
3. **Fix any issues** identified by validation
4. **On Windows, run full validation**: `python validate_workflows.py --full`
5. **Test executable and installer** manually
6. **Commit changes** if all validations pass
7. **Push to GitHub** and monitor CI workflow
8. **Verify artifacts** are created correctly

### Git Hooks (Optional)

You can set up a pre-commit hook to automatically validate workflows:

```bash
# Create .git/hooks/pre-commit
cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash
echo "Running workflow validation..."
python validate_workflows.py
if [ $? -ne 0 ]; then
    echo "Validation failed. Commit aborted."
    exit 1
fi
EOF

# Make executable
chmod +x .git/hooks/pre-commit
```

## Additional Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [PyInstaller Documentation](https://pyinstaller.org/en/stable/)
- [Inno Setup Documentation](https://jrsoftware.org/ishelp/)
- [yamllint Documentation](https://yamllint.readthedocs.io/)

## Getting Help

If you encounter issues not covered in this guide:

1. Check workflow logs in GitHub Actions tab
2. Review error messages from validation script
3. Consult the troubleshooting section above
4. Open an issue with validation output and error messages
