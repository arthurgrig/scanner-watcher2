#!/usr/bin/env python3
"""
Workflow Validation Script

This script validates GitHub Actions workflows and build configurations
before committing changes. It performs the following checks:

1. YAML syntax validation for workflow files
2. PyInstaller spec file validation
3. Inno Setup script validation (Windows only)
4. Build command testing (Windows only)

Usage:
    python validate_workflows.py [--full]

Options:
    --full    Run full validation including build tests (Windows only)
"""

import argparse
import platform
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple


def print_header(message: str) -> None:
    """Print a formatted header."""
    print(f"\n{'=' * 70}")
    print(f"  {message}")
    print(f"{'=' * 70}\n")


def print_success(message: str) -> None:
    """Print a success message."""
    print(f"✓ {message}")


def print_error(message: str) -> None:
    """Print an error message."""
    print(f"✗ {message}", file=sys.stderr)


def print_warning(message: str) -> None:
    """Print a warning message."""
    print(f"⚠ {message}")


def check_file_exists(filepath: Path) -> bool:
    """Check if a file exists."""
    if not filepath.exists():
        print_error(f"File not found: {filepath}")
        return False
    print_success(f"Found: {filepath}")
    return True


def validate_yaml_files() -> bool:
    """Validate YAML syntax for workflow files."""
    print_header("Validating YAML Workflow Files")

    workflow_dir = Path(".github/workflows")
    if not workflow_dir.exists():
        print_error(f"Workflow directory not found: {workflow_dir}")
        return False

    yaml_files = list(workflow_dir.glob("*.yml")) + list(workflow_dir.glob("*.yaml"))
    if not yaml_files:
        print_error("No YAML workflow files found")
        return False

    print(f"Found {len(yaml_files)} workflow file(s)")

    # Check if yamllint is installed
    try:
        subprocess.run(
            ["yamllint", "--version"],
            capture_output=True,
            check=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        print_error("yamllint is not installed. Install with: pip install yamllint")
        return False

    # Validate each YAML file
    all_valid = True
    for yaml_file in yaml_files:
        try:
            result = subprocess.run(
                ["yamllint", "-c", ".yamllint", str(yaml_file)],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                print_success(f"Valid YAML: {yaml_file.name}")
            else:
                print_error(f"Invalid YAML: {yaml_file.name}")
                print(result.stdout)
                all_valid = False
        except Exception as e:
            print_error(f"Error validating {yaml_file.name}: {e}")
            all_valid = False

    return all_valid


def validate_pyinstaller_spec() -> bool:
    """Validate PyInstaller spec file exists and has correct structure."""
    print_header("Validating PyInstaller Spec File")

    spec_file = Path("scanner_watcher2.spec")
    if not check_file_exists(spec_file):
        return False

    # Read and check for required sections
    content = spec_file.read_text()
    required_sections = ["Analysis", "PYZ", "EXE"]
    missing_sections = []

    for section in required_sections:
        if section not in content:
            missing_sections.append(section)

    if missing_sections:
        print_error(f"Missing required sections: {', '.join(missing_sections)}")
        return False

    print_success("Spec file has all required sections")

    # Check for critical hidden imports
    critical_imports = ["win32service", "win32serviceutil", "openai", "fitz"]
    missing_imports = []

    for imp in critical_imports:
        if imp not in content:
            missing_imports.append(imp)

    if missing_imports:
        print_warning(f"Missing critical hidden imports: {', '.join(missing_imports)}")
        print_warning("These may need to be added to hiddenimports list")

    return True


def validate_inno_setup_script() -> bool:
    """Validate Inno Setup script exists and has correct structure."""
    print_header("Validating Inno Setup Script")

    iss_file = Path("scanner_watcher2.iss")
    if not check_file_exists(iss_file):
        return False

    # Read and check for required sections
    content = iss_file.read_text()
    required_sections = ["[Setup]", "[Files]", "[Icons]", "[Run]"]
    missing_sections = []

    for section in required_sections:
        if section not in content:
            missing_sections.append(section)

    if missing_sections:
        print_error(f"Missing required sections: {', '.join(missing_sections)}")
        return False

    print_success("Inno Setup script has all required sections")

    # Check for critical configuration
    if "AppId=" not in content:
        print_error("Missing AppId in [Setup] section")
        return False

    if "OutputDir=" not in content:
        print_warning("Missing OutputDir specification")

    return True


def test_pyinstaller_build() -> bool:
    """Test PyInstaller build command (Windows only)."""
    print_header("Testing PyInstaller Build")

    if platform.system() != "Windows":
        print_warning("PyInstaller build test skipped (Windows only)")
        print_warning("This test should be run on Windows before committing")
        return True

    # Check if PyInstaller is installed
    try:
        subprocess.run(
            ["pyinstaller", "--version"],
            capture_output=True,
            check=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        print_error("PyInstaller is not installed. Install with: pip install pyinstaller")
        return False

    # Run PyInstaller
    print("Running PyInstaller (this may take several minutes)...")
    try:
        result = subprocess.run(
            ["pyinstaller", "scanner_watcher2.spec"],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            print_error("PyInstaller build failed")
            print(result.stdout)
            print(result.stderr, file=sys.stderr)
            return False

        # Check if executable was created
        exe_path = Path("dist/scanner_watcher2.exe")
        if not exe_path.exists():
            print_error(f"Executable not found at {exe_path}")
            return False

        print_success(f"Executable created: {exe_path}")
        print(f"  Size: {exe_path.stat().st_size / (1024 * 1024):.2f} MB")
        return True

    except Exception as e:
        print_error(f"Error running PyInstaller: {e}")
        return False


def test_inno_setup_compilation() -> bool:
    """Test Inno Setup compilation (Windows only)."""
    print_header("Testing Inno Setup Compilation")

    if platform.system() != "Windows":
        print_warning("Inno Setup compilation test skipped (Windows only)")
        print_warning("This test should be run on Windows before committing")
        return True

    # Check if Inno Setup is installed
    iscc_paths = [
        Path("C:/Program Files (x86)/Inno Setup 6/ISCC.exe"),
        Path("C:/Program Files/Inno Setup 6/ISCC.exe"),
    ]

    iscc_exe = None
    for path in iscc_paths:
        if path.exists():
            iscc_exe = path
            break

    if not iscc_exe:
        print_error("Inno Setup not found. Install from: https://jrsoftware.org/isinfo.php")
        print_error("Or install via Chocolatey: choco install innosetup")
        return False

    # Check if executable exists (required for installer)
    exe_path = Path("dist/scanner_watcher2.exe")
    if not exe_path.exists():
        print_error(f"Executable not found at {exe_path}")
        print_error("Run PyInstaller build first")
        return False

    # Run Inno Setup compiler
    print("Running Inno Setup compiler...")
    try:
        result = subprocess.run(
            [str(iscc_exe), "scanner_watcher2.iss"],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            print_error("Inno Setup compilation failed")
            print(result.stdout)
            print(result.stderr, file=sys.stderr)
            return False

        # Check if installer was created
        installer_path = Path("dist/scanner-watcher2-setup-1.0.0.exe")
        if not installer_path.exists():
            # Try alternative output location
            installer_path = Path("Output/scanner-watcher2-setup-1.0.0.exe")

        if not installer_path.exists():
            print_error("Installer not found")
            return False

        print_success(f"Installer created: {installer_path}")
        print(f"  Size: {installer_path.stat().st_size / (1024 * 1024):.2f} MB")
        return True

    except Exception as e:
        print_error(f"Error running Inno Setup: {e}")
        return False


def main() -> int:
    """Main validation function."""
    parser = argparse.ArgumentParser(
        description="Validate GitHub Actions workflows and build configurations"
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="Run full validation including build tests (Windows only)",
    )
    args = parser.parse_args()

    print_header("GitHub Actions Workflow Validation")
    print(f"Platform: {platform.system()}")
    print(f"Python: {sys.version.split()[0]}")

    results: List[Tuple[str, bool]] = []

    # Always run these checks
    results.append(("YAML Validation", validate_yaml_files()))
    results.append(("PyInstaller Spec", validate_pyinstaller_spec()))
    results.append(("Inno Setup Script", validate_inno_setup_script()))

    # Run build tests if --full flag is provided
    if args.full:
        results.append(("PyInstaller Build", test_pyinstaller_build()))
        results.append(("Inno Setup Compilation", test_inno_setup_compilation()))
    else:
        print_header("Build Tests Skipped")
        print("Run with --full flag to test builds (Windows only)")
        print("  python validate_workflows.py --full")

    # Print summary
    print_header("Validation Summary")
    all_passed = True
    for name, passed in results:
        if passed:
            print_success(f"{name}: PASSED")
        else:
            print_error(f"{name}: FAILED")
            all_passed = False

    if all_passed:
        print("\n✓ All validations passed!")
        return 0
    else:
        print("\n✗ Some validations failed. Please fix the issues before committing.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
