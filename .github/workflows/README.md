# GitHub Actions Workflows

This directory contains GitHub Actions workflows for automated CI/CD of Scanner-Watcher2.

## Overview

Scanner-Watcher2 uses GitHub Actions to automate building, testing, and releasing the Windows application. All workflows run on Windows runners to ensure compatibility with the target platform.

## Workflows

### CI Workflow (`ci.yml`)

**Purpose**: Validates code quality on every commit and pull request

**Triggers**:
- Push to `main` branch
- Pull requests targeting `main` branch
- Manual dispatch via GitHub Actions UI

**Jobs**:

1. **Test** - Runs test suite with coverage
   - Sets up Python 3.12 on Windows
   - Installs dependencies from `pyproject.toml`
   - Runs pytest with coverage reporting
   - Uploads coverage reports as artifacts (30-day retention)
   - Fails workflow if tests fail

2. **Build** - Creates PyInstaller executable
   - Depends on test job passing
   - Sets up Python 3.12 on Windows
   - Builds standalone executable using `scanner_watcher2.spec`
   - Verifies executable was created
   - Uploads executable as artifact (30-day retention)

**Artifacts Produced**:
- `coverage-reports`: HTML and XML coverage reports
- `scanner-watcher2-executable`: Standalone Windows executable

**Duration**: ~10-15 minutes

### Release Workflow (`release.yml`)

**Purpose**: Automates creation of GitHub releases with installers

**Triggers**:
- Push of version tags matching `v*.*.*` pattern (e.g., `v1.0.0`, `v2.1.3`)
- Manual dispatch with version input

**Jobs**:

1. **Build-Release** - Creates installer and GitHub release
   - Sets up Python 3.12 on Windows
   - Builds PyInstaller executable
   - Installs Inno Setup via Chocolatey
   - Compiles Windows installer using `scanner_watcher2.iss`
   - Creates GitHub release with version tag
   - Uploads installer as release asset

**Release Assets**:
- `ScannerWatcher2Setup.exe`: Windows installer

**Duration**: ~15-20 minutes

## How to Trigger Workflows

### CI Workflow

**Automatic Triggers**:
```bash
# Push to main branch
git push origin main

# Create pull request
gh pr create --base main
```

**Manual Trigger**:
1. Go to Actions tab in GitHub
2. Select "CI" workflow
3. Click "Run workflow"
4. Select branch and click "Run workflow"

### Release Workflow

**Automatic Trigger (Recommended)**:
```bash
# Create and push version tag
git tag v1.0.0
git push origin v1.0.0
```

**Manual Trigger**:
1. Go to Actions tab in GitHub
2. Select "Release" workflow
3. Click "Run workflow"
4. Enter version tag (e.g., `v1.0.0`)
5. Click "Run workflow"

## Required Secrets and Permissions

### Secrets

**`GITHUB_TOKEN`** (Automatic)
- Automatically provided by GitHub Actions
- No configuration required
- Used for creating releases and uploading assets

**Future Secrets** (Not yet required):
- `OPENAI_API_KEY`: If integration tests need to call OpenAI API

### Configuring Secrets

If additional secrets are needed:

1. Go to repository Settings
2. Navigate to Secrets and variables → Actions
3. Click "New repository secret"
4. Add secret name and value
5. Reference in workflows as `${{ secrets.SECRET_NAME }}`

### Permissions

**CI Workflow**:
- Default permissions (read access to repository)

**Release Workflow**:
- `contents: write` - For creating releases and uploading assets
- Configured in workflow YAML

## Artifacts and Retention

### Artifact Storage

**CI Workflow Artifacts**:
- `coverage-reports`: 30-day retention
- `scanner-watcher2-executable`: 30-day retention

**Release Workflow Assets**:
- Permanent (attached to GitHub releases)

### Downloading Artifacts

**From Workflow Run**:
1. Go to Actions tab
2. Click on workflow run
3. Scroll to "Artifacts" section
4. Click artifact name to download

**From Release**:
1. Go to Releases page
2. Find desired version
3. Download `ScannerWatcher2Setup.exe`

### Storage Considerations

- Artifacts count against repository storage quota
- 30-day retention balances storage costs with debugging needs
- Release assets don't count against artifact storage

## Troubleshooting

### Common Issues

#### Tests Fail on Windows Runner

**Symptom**: Tests pass locally but fail in CI

**Possible Causes**:
- Path separator differences (use `pathlib.Path`)
- Line ending differences (configure `.gitattributes`)
- Missing Windows-specific dependencies
- Timing issues in filesystem operations

**Solutions**:
```python
# Use pathlib for cross-platform paths
from pathlib import Path
config_path = Path("config") / "settings.json"

# Add delays for filesystem operations
import time
time.sleep(0.1)  # Allow filesystem to settle
```

#### PyInstaller Build Fails

**Symptom**: Executable not created or missing dependencies

**Possible Causes**:
- Missing hidden imports in `.spec` file
- Data files not included
- Version conflicts in dependencies

**Solutions**:
1. Check PyInstaller output for missing modules
2. Add hidden imports to `scanner_watcher2.spec`:
   ```python
   hiddenimports=['missing_module']
   ```
3. Include data files:
   ```python
   datas=[('src/data', 'data')]
   ```

#### Inno Setup Compilation Fails

**Symptom**: Installer not created

**Possible Causes**:
- Syntax errors in `.iss` file
- Missing files referenced in installer script
- Incorrect paths in installer configuration

**Solutions**:
1. Validate `.iss` file syntax locally
2. Ensure all files exist before compilation
3. Use absolute paths or verify working directory
4. Check Inno Setup compiler output in logs

#### Release Creation Fails

**Symptom**: GitHub release not created or assets not uploaded

**Possible Causes**:
- Insufficient permissions
- Duplicate tag/release
- Network issues
- Invalid tag format

**Solutions**:
1. Verify `contents: write` permission in workflow
2. Delete existing tag/release if recreating:
   ```bash
   git tag -d v1.0.0
   git push origin :refs/tags/v1.0.0
   gh release delete v1.0.0
   ```
3. Ensure tag matches `v*.*.*` pattern
4. Re-run workflow if transient failure

#### Dependency Installation Fails

**Symptom**: pip install fails

**Possible Causes**:
- PyPI network issues
- Version conflicts
- Missing system dependencies

**Solutions**:
1. Re-run workflow (often resolves transient issues)
2. Check dependency versions in `pyproject.toml`
3. Review pip error messages in logs
4. Consider pinning problematic dependency versions

#### Workflow Doesn't Trigger

**Symptom**: Push/PR doesn't start workflow

**Possible Causes**:
- YAML syntax errors
- Incorrect trigger configuration
- Workflow disabled

**Solutions**:
1. Validate YAML syntax:
   ```bash
   # Use yamllint or GitHub's validator
   yamllint .github/workflows/
   ```
2. Check workflow is enabled in Actions tab
3. Verify branch names match trigger configuration
4. Check GitHub Actions status page for outages

### Debugging Workflows

**View Detailed Logs**:
1. Go to Actions tab
2. Click on failed workflow run
3. Click on failed job
4. Expand failed step to see detailed output

**Enable Debug Logging**:
1. Go to repository Settings
2. Navigate to Secrets and variables → Actions
3. Add secret: `ACTIONS_STEP_DEBUG` = `true`
4. Re-run workflow to see verbose output

**Download Logs**:
1. Go to workflow run
2. Click "..." menu in top right
3. Select "Download log archive"

**Test Locally** (Limited):
```bash
# Install act (GitHub Actions local runner)
# Note: Windows support is limited
choco install act-cli

# Run workflow locally
act -j test
```

### Getting Help

**Resources**:
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [PyInstaller Documentation](https://pyinstaller.org/en/stable/)
- [Inno Setup Documentation](https://jrsoftware.org/ishelp/)
- Repository Issues: Report workflow problems

**Workflow Status**:
- Check Actions tab for real-time status
- Status badges appear on pull requests
- Email notifications for workflow failures (if enabled)

## Maintenance

### Updating Action Versions

Regularly update action versions for security and features:

```yaml
# Check for updates
- uses: actions/checkout@v4  # Update to v5 when available
- uses: actions/setup-python@v5
- uses: actions/upload-artifact@v4
```

### Monitoring Runner Updates

GitHub updates runner images regularly:
- Monitor [runner image releases](https://github.com/actions/runner-images/releases)
- Test workflows after major runner updates
- Pin to specific runner version if needed: `runs-on: windows-2022`

### Optimizing Workflow Performance

**Caching**:
- Pip cache is enabled in both workflows
- Cache key based on `pyproject.toml` hash
- Reduces dependency installation time by ~50%

**Parallelization**:
- Test and build jobs run sequentially (build depends on test)
- Consider parallel test execution for large test suites

**Artifact Size**:
- Compress large artifacts before upload
- Clean up unnecessary files before artifact creation
- Monitor storage usage in repository settings

## Future Enhancements

Potential workflow improvements:

1. **Code Quality Checks**
   - Add linting (ruff, black, mypy)
   - Fail on formatting issues

2. **Security Scanning**
   - Add dependency vulnerability scanning
   - Scan for accidentally committed secrets

3. **Multi-Version Testing**
   - Test on Windows 2019, 2022
   - Test with Python 3.12, 3.13

4. **Automated Changelog**
   - Generate from commit messages
   - Include in release notes

5. **Notification Integration**
   - Slack/email notifications
   - Custom failure alerts

## Testing the Release Workflow

Before using the release workflow for production releases, it's important to validate that it works correctly. This section provides a complete guide for testing the release workflow with test tags.

### Why Test the Release Workflow?

Testing the release workflow ensures:
- The workflow triggers correctly on version tags
- PyInstaller builds the executable successfully
- Inno Setup compiles the installer without errors
- GitHub release is created with correct metadata
- Installer is attached as a downloadable asset
- The installer downloads and installs correctly

### Testing Process Overview

1. Create a test version tag
2. Push the tag to trigger the release workflow
3. Monitor the workflow execution
4. Verify the release and installer
5. Test the installer download and installation
6. Clean up test artifacts

### Step-by-Step Testing Guide

#### Step 1: Create a Test Tag

Create a test version tag that follows the `v*.*.*` pattern but is clearly marked as a test:

```bash
# Use a test version number (e.g., v0.0.1-test, v0.0.2-test)
git tag v0.0.1-test

# Or use a pre-release version
git tag v1.0.0-alpha.1
git tag v1.0.0-beta.1
git tag v1.0.0-rc.1
```

**Best Practices**:
- Use `v0.0.x-test` for pure testing (clearly not a real release)
- Use pre-release suffixes (`-alpha`, `-beta`, `-rc`) for release candidates
- Avoid using version numbers you plan to use for real releases
- Document test tags in commit messages or PR descriptions

#### Step 2: Push the Test Tag

Push the tag to GitHub to trigger the release workflow:

```bash
# Push the test tag
git push origin v0.0.1-test

# Verify the tag was pushed
git ls-remote --tags origin
```

**What Happens Next**:
- GitHub Actions detects the tag push
- Release workflow is triggered automatically
- Workflow appears in the Actions tab
- You'll receive notifications (if enabled)

#### Step 3: Monitor Workflow Execution

Watch the workflow run in real-time:

**Via GitHub UI**:
1. Go to the Actions tab in your repository
2. Look for the "Release" workflow run
3. Click on the run to see detailed progress
4. Monitor each step as it executes

**Via GitHub CLI**:
```bash
# List recent workflow runs
gh run list --workflow=release.yml

# Watch a specific run (replace <run-id>)
gh run watch <run-id>

# View run details
gh run view <run-id>
```

**Expected Duration**: 15-20 minutes

**Key Steps to Monitor**:
- ✓ Checkout code
- ✓ Setup Python 3.12
- ✓ Install dependencies
- ✓ Build PyInstaller executable
- ✓ Install Inno Setup
- ✓ Compile installer
- ✓ Create GitHub release
- ✓ Upload installer asset

#### Step 4: Verify the Release

Once the workflow completes, verify the release was created correctly:

**Via GitHub UI**:
1. Go to the Releases page (Code tab → Releases)
2. Find your test release (e.g., `v0.0.1-test`)
3. Verify the release includes:
   - Correct version tag
   - Release title
   - Installer asset (`ScannerWatcher2Setup.exe`)
   - Asset size (should be several MB)

**Via GitHub CLI**:
```bash
# List releases
gh release list

# View specific release
gh release view v0.0.1-test

# Check release assets
gh release view v0.0.1-test --json assets
```

**Verification Checklist**:
- [ ] Release exists with correct tag name
- [ ] Release is marked as "Pre-release" (if using pre-release tag)
- [ ] Installer asset is attached
- [ ] Asset name follows convention: `ScannerWatcher2Setup.exe`
- [ ] Asset size is reasonable (typically 20-50 MB)
- [ ] Release timestamp matches workflow completion time

#### Step 5: Test Installer Download and Installation

Download and test the installer to ensure it works correctly:

**Download the Installer**:

Via GitHub UI:
1. Go to the release page
2. Click on `ScannerWatcher2Setup.exe` to download

Via GitHub CLI:
```bash
# Download release assets
gh release download v0.0.1-test

# Or download to specific directory
gh release download v0.0.1-test --dir ./test-installer
```

Via Direct URL:
```bash
# Download using curl or wget
curl -L -O https://github.com/YOUR-USERNAME/scanner-watcher2/releases/download/v0.0.1-test/ScannerWatcher2Setup.exe
```

**Test the Installer**:

1. **Verify File Integrity**:
   ```powershell
   # Check file size
   Get-Item ScannerWatcher2Setup.exe | Select-Object Name, Length
   
   # Verify it's a valid executable
   Get-AuthenticodeSignature ScannerWatcher2Setup.exe
   ```

2. **Run the Installer** (in a test environment):
   ```powershell
   # Run installer in silent mode for testing
   .\ScannerWatcher2Setup.exe /VERYSILENT /SUPPRESSMSGBOXES /LOG="install.log"
   
   # Check installation log
   Get-Content install.log
   ```

3. **Verify Installation**:
   ```powershell
   # Check installation directory
   Test-Path "C:\Program Files\ScannerWatcher2\scanner_watcher2.exe"
   
   # Check Start Menu shortcuts
   Test-Path "$env:ProgramData\Microsoft\Windows\Start Menu\Programs\ScannerWatcher2"
   ```

4. **Test the Application**:
   ```powershell
   # Run the application
   & "C:\Program Files\ScannerWatcher2\scanner_watcher2.exe" --help
   
   # Or test the configuration wizard
   & "C:\Program Files\ScannerWatcher2\scanner_watcher2.exe" --configure
   ```

5. **Test Uninstallation**:
   ```powershell
   # Uninstall silently
   & "C:\Program Files\ScannerWatcher2\unins000.exe" /VERYSILENT /SUPPRESSMSGBOXES
   
   # Verify uninstallation
   Test-Path "C:\Program Files\ScannerWatcher2" # Should return False
   ```

**Installation Testing Checklist**:
- [ ] Installer downloads without errors
- [ ] Installer file size is correct
- [ ] Installer runs without errors
- [ ] Application files are installed correctly
- [ ] Start Menu shortcuts are created
- [ ] Application launches successfully
- [ ] Configuration wizard works
- [ ] Uninstaller removes all files
- [ ] No errors in installation log

#### Step 6: Clean Up Test Artifacts

After testing, clean up the test release and tag:

**Delete the GitHub Release**:

Via GitHub UI:
1. Go to the Releases page
2. Click on the test release
3. Click "Delete" button
4. Confirm deletion

Via GitHub CLI:
```bash
# Delete the release
gh release delete v0.0.1-test --yes

# Verify deletion
gh release list
```

**Delete the Git Tag**:

```bash
# Delete local tag
git tag -d v0.0.1-test

# Delete remote tag
git push origin :refs/tags/v0.0.1-test

# Or use the delete syntax
git push origin --delete v0.0.1-test

# Verify tag is deleted
git ls-remote --tags origin
```

**Verify Cleanup**:
```bash
# Check no local tags remain
git tag | grep test

# Check no remote tags remain
git ls-remote --tags origin | grep test

# Check no releases remain
gh release list | grep test
```

### Troubleshooting Test Releases

#### Workflow Doesn't Trigger

**Problem**: Tag pushed but workflow doesn't start

**Solutions**:
- Verify tag matches `v*.*.*` pattern (must start with `v`)
- Check workflow file is on the branch where tag was created
- Ensure workflow is enabled in Actions settings
- Check GitHub Actions status page for outages

#### Release Creation Fails

**Problem**: Workflow runs but release isn't created

**Solutions**:
- Check workflow has `contents: write` permission
- Verify `GITHUB_TOKEN` has necessary permissions
- Ensure tag doesn't already exist (delete old tag first)
- Review workflow logs for specific error messages

#### Installer Not Attached

**Problem**: Release created but installer asset is missing

**Solutions**:
- Check Inno Setup compilation step succeeded
- Verify installer file path in workflow matches actual output
- Check file size limits (GitHub has 2GB asset limit)
- Review upload step logs for errors

#### Installer Won't Run

**Problem**: Downloaded installer fails to execute

**Solutions**:
- Check Windows SmartScreen settings
- Verify file wasn't corrupted during download (check size)
- Try running as administrator
- Check Windows Event Viewer for error details
- Review installation log file

### Best Practices for Release Testing

1. **Test Before Production**: Always test with a test tag before creating real releases
2. **Use Consistent Naming**: Use `v0.0.x-test` pattern for test releases
3. **Document Tests**: Keep notes on what you tested and results
4. **Test Full Cycle**: Don't skip installation testing - download and install the actual artifact
5. **Clean Up Promptly**: Delete test releases and tags after testing
6. **Test on Clean System**: Use a VM or clean Windows installation for installer testing
7. **Verify Uninstall**: Always test that uninstallation works correctly
8. **Check Logs**: Review workflow logs even for successful runs
9. **Test Edge Cases**: Try canceling workflow, re-running failed jobs, etc.
10. **Automate When Possible**: Consider scripting repetitive testing steps

### Testing Checklist

Use this checklist when testing the release workflow:

**Pre-Test**:
- [ ] Workflows validated locally with `validate_workflows.py`
- [ ] All CI tests passing on main branch
- [ ] Test tag name chosen (e.g., `v0.0.1-test`)

**Workflow Execution**:
- [ ] Test tag created and pushed
- [ ] Release workflow triggered automatically
- [ ] All workflow steps completed successfully
- [ ] No errors or warnings in workflow logs
- [ ] Workflow completed in reasonable time (~15-20 min)

**Release Verification**:
- [ ] GitHub release created with correct tag
- [ ] Release marked as pre-release (if applicable)
- [ ] Installer asset attached to release
- [ ] Asset size is reasonable (20-50 MB)
- [ ] Asset name follows convention

**Installer Testing**:
- [ ] Installer downloaded successfully
- [ ] File integrity verified (size, signature)
- [ ] Installer runs without errors
- [ ] Application installed to correct location
- [ ] Start Menu shortcuts created
- [ ] Application launches successfully
- [ ] Configuration wizard works
- [ ] Uninstaller removes all files cleanly

**Cleanup**:
- [ ] Test release deleted from GitHub
- [ ] Local test tag deleted
- [ ] Remote test tag deleted
- [ ] No test artifacts remain

**Documentation**:
- [ ] Test results documented
- [ ] Any issues noted for future reference
- [ ] Workflow improvements identified

### Example Test Session

Here's a complete example of testing the release workflow:

```bash
# 1. Create test tag
git tag v0.0.1-test
git push origin v0.0.1-test

# 2. Monitor workflow
gh run watch --workflow=release.yml

# 3. Verify release
gh release view v0.0.1-test

# 4. Download installer
gh release download v0.0.1-test --dir ./test-installer
cd test-installer

# 5. Test installer (PowerShell)
.\ScannerWatcher2Setup.exe /VERYSILENT /LOG="install.log"
Get-Content install.log
Test-Path "C:\Program Files\ScannerWatcher2\scanner_watcher2.exe"

# 6. Test application
& "C:\Program Files\ScannerWatcher2\scanner_watcher2.exe" --help

# 7. Uninstall
& "C:\Program Files\ScannerWatcher2\unins000.exe" /VERYSILENT

# 8. Clean up
cd ..
gh release delete v0.0.1-test --yes
git tag -d v0.0.1-test
git push origin :refs/tags/v0.0.1-test
```

### When to Re-Test

Re-test the release workflow when:
- Workflow files are modified
- PyInstaller spec file changes
- Inno Setup script changes
- Dependencies are updated significantly
- Python version is upgraded
- GitHub Actions runner images are updated
- After long periods of inactivity (3+ months)

## Local Validation

Before committing workflow changes, validate them locally to catch issues early.

### Validation Script

A validation script is provided to check workflows and build configurations:

```bash
# Basic validation (YAML syntax, spec files)
python validate_workflows.py

# Full validation including builds (Windows only)
python validate_workflows.py --full
```

### What Gets Validated

**Basic Validation** (All platforms):
- YAML syntax for all workflow files
- PyInstaller spec file structure
- Inno Setup script structure
- Required sections and configurations

**Full Validation** (Windows only):
- PyInstaller executable build
- Inno Setup installer compilation
- Output file verification

### Manual Validation Steps

If you prefer to validate manually:

**1. Install yamllint**:
```bash
pip install yamllint
```

**2. Validate YAML files**:
```bash
yamllint -c .yamllint .github/workflows/*.yml
```

**3. Test PyInstaller build** (Windows only):
```bash
# Install dependencies
pip install -e ".[dev]"

# Build executable
pyinstaller scanner_watcher2.spec

# Verify output
dir dist\scanner_watcher2.exe
```

**4. Test Inno Setup compilation** (Windows only):
```bash
# Install Inno Setup
choco install innosetup -y

# Compile installer
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" scanner_watcher2.iss

# Verify output
dir Output\scanner-watcher2-setup-*.exe
```

### Validation Checklist

Before committing workflow changes:

- [ ] YAML files pass yamllint validation
- [ ] PyInstaller spec file has all required sections
- [ ] Inno Setup script has all required sections
- [ ] (Windows) PyInstaller build completes successfully
- [ ] (Windows) Inno Setup compilation completes successfully
- [ ] (Windows) Executable runs without errors
- [ ] (Windows) Installer installs and uninstalls cleanly

### CI/CD Validation

After pushing changes:

- [ ] CI workflow runs successfully on GitHub Actions
- [ ] All tests pass on Windows runner
- [ ] Executable artifact is created and downloadable
- [ ] (For releases) Installer is created and attached to release
- [ ] Workflow logs show no warnings or errors

## Workflow Best Practices

1. **Always validate locally first** - Use the validation script before pushing
2. **Test on Windows** - Run full validation on Windows before committing build changes
3. **Use semantic versioning** - Follow `v{major}.{minor}.{patch}` for release tags
4. **Review workflow logs** - Check logs even for successful runs to catch warnings
5. **Keep workflows simple** - Complex workflows are harder to debug and maintain
6. **Document changes** - Update this README when modifying workflows
7. **Test with PRs** - Use pull requests to validate workflow changes before merging
8. **Monitor storage** - Clean up old artifacts to manage storage quota
9. **Pin critical versions** - Pin action versions for stability, update deliberately

## Quick Reference

### Common Commands

```bash
# Create release
git tag v1.0.0
git push origin v1.0.0

# Delete release (if needed)
gh release delete v1.0.0
git tag -d v1.0.0
git push origin :refs/tags/v1.0.0

# View workflow runs
gh run list

# View specific run
gh run view <run-id>

# Re-run failed workflow
gh run rerun <run-id>

# Download artifacts
gh run download <run-id>
```

### Workflow Files

- `ci.yml`: Continuous integration (test + build)
- `release.yml`: Release automation (installer + GitHub release)

### Key Paths

- Workflows: `.github/workflows/`
- Build spec: `scanner_watcher2.spec`
- Installer script: `scanner_watcher2.iss`
- Dependencies: `pyproject.toml`
