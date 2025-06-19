#!/usr/bin/env python3
"""
Script to automatically fix code quality issues in all Python files
"""
import subprocess
from pathlib import Path


def run_command(cmd, description):
    """Run a command and print the results"""
    print(f"\n=== {description} ===")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(f"Error: {result.stderr}")
        return result.returncode == 0
    except Exception as e:
        print(f"Failed to run {cmd}: {e}")
        return False


def fix_python_files():
    """Fix all Python files in the current directory"""

    # Get all Python files
    py_files = list(Path(".").glob("**/*.py"))
    py_files = [f for f in py_files if "__pycache__" not in str(f)]

    print(f"Found {len(py_files)} Python files to process")

    # Process each file
    for py_file in py_files:
        print(f"\n{'='*60}")
        print(f"Processing: {py_file}")
        print(f"{'='*60}")

        # Run black formatter
        run_command(f"black --line-length=88 {py_file}", f"Black formatting {py_file}")

        # Run isort
        run_command(f"isort {py_file}", f"Import sorting {py_file}")

        # Check with flake8
        run_command(f"flake8 --max-line-length=88 {py_file}", f"Flake8 check {py_file}")

    # Final overall check
    print(f"\n{'='*60}")
    print("FINAL OVERALL CHECK")
    print(f"{'='*60}")

    run_command(
        "flake8 --statistics --count --max-line-length=88 --exclude=__pycache__, *.pyc, .git, venv, env, fix_all_files.py .",
        "Final flake8 check",
    )


if __name__ == "__main__":
    fix_python_files()
