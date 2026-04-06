"""
Environment validation tests for Predictive LTV Survival Pipeline

Run with: python tests/test_environment.py
"""

import os
import sys
import subprocess
from pathlib import Path


def test_python_version():
    """Verify Python 3.10+ is available."""
    version = sys.version_info
    assert version.major == 3 and version.minor >= 10, f"Python 3.10+ required, got {version.major}.{version.minor}"
    print(f"✓ Python version: {version.major}.{version.minor}.{version.micro}")


def test_required_packages():
    """Verify core packages are installed."""
    required = [
        'dbt.core',
        'dbt_databricks',
        'pyspark',
        'pandas',
        'great_expectations',
        'streamlit',
        'lifelines'
    ]
    
    for package in required:
        try:
            __import__(package)
            print(f"✓ {package} installed")
        except ImportError as e:
            print(f"✗ {package} not installed: {e}")
            raise


def test_databricks_env_vars():
    """Verify Databricks environment variables are set."""
    required_vars = [
        'DATABRICKS_HOST',
        'DATABRICKS_HTTP_PATH',
        'DATABRICKS_TOKEN'
    ]
    
    missing = []
    for var in required_vars:
        if not os.getenv(var):
            missing.append(var)
        else:
            print(f"✓ {var} is set")
    
    if missing:
        print(f"⚠ Missing environment variables: {', '.join(missing)}")
        print(f"  Run: bash scripts/setup_secrets.sh")
        print(f"  Then: source .env.local")


def test_dbt_debug():
    """Verify dbt debug succeeds."""
    try:
        result = subprocess.run(
            ['dbt', 'debug'],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            print(f"✓ dbt connection successful")
        else:
            print(f"✗ dbt debug failed:")
            print(result.stderr)
            raise RuntimeError("dbt connection failed")
    except FileNotFoundError:
        print(f"✗ dbt command not found")
        raise
    except subprocess.TimeoutExpired:
        print(f"✗ dbt debug timed out")
        raise


def test_directory_structure():
    """Verify expected directory structure."""
    required_dirs = [
        'models',
        'models/staging',
        'models/marts',
        'macros',
        'scripts',
        'data',
        'data/bronze',
        'data/silver',
        'data/gold'
    ]
    
    for dir_path in required_dirs:
        if Path(dir_path).exists():
            print(f"✓ {dir_path}/ exists")
        else:
            print(f"✗ {dir_path}/ not found")
            raise FileNotFoundError(f"Missing directory: {dir_path}")


def test_configuration_files():
    """Verify required configuration files exist."""
    required_files = [
        'dbt_project.yml',
        'profiles.yml.example',
        'requirements.txt',
        'ENVIRONMENT_SETUP.md',
        'ARCHITECTURE.md',
        'Makefile'
    ]
    
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"✓ {file_path} exists")
        else:
            print(f"✗ {file_path} not found")
            raise FileNotFoundError(f"Missing file: {file_path}")


def main():
    """Run all validation tests."""
    tests = [
        ("Python Version", test_python_version),
        ("Required Packages", test_required_packages),
        ("Databricks Environment", test_databricks_env_vars),
        ("dbt Connection", test_dbt_debug),
        ("Directory Structure", test_directory_structure),
        ("Configuration Files", test_configuration_files),
    ]
    
    print("=" * 60)
    print("Environment Validation Tests")
    print("=" * 60)
    print()
    
    passed = 0
    failed = 0
    warnings = 0
    
    for test_name, test_func in tests:
        print(f"\n[{test_name}]")
        try:
            test_func()
            passed += 1
        except Exception as e:
            if "missing" in str(e).lower() or "warning" in str(e).lower():
                warnings += 1
            else:
                failed += 1
                print(f"✗ FAILED: {e}")
    
    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed, {warnings} warnings")
    print("=" * 60)
    
    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
