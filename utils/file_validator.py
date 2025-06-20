"""
File Validation Utilities
=========================

Common file validation functions extracted from cleanup scripts.
"""

import logging
from pathlib import Path
from typing import List
from typing import Tuple

logger = logging.getLogger(__name__)


def validate_python_file(file_path: str) -> Tuple[bool, str]:
    """
    Validate a Python file for syntax errors.

    Args:
        file_path: Path to the Python file

    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            compile(content, file_path, "exec")
        logger.debug(f"✅ {file_path}")
        return True, ""
    except SyntaxError as e:
        error_msg = f"❌ {file_path}: {e}"
        logger.warning(error_msg)
        return False, str(e)
    except Exception as e:
        error_msg = f"❌ {file_path}: {e}"
        logger.error(error_msg)
        return False, str(e)


def validate_python_files(file_paths: List[str]) -> Tuple[List[str], List[str]]:
    """
    Validate multiple Python files.

    Args:
        file_paths: List of file paths to validate

    Returns:
        Tuple of (valid_files, invalid_files)
    """
    valid_files = []
    invalid_files = []

    for file_path in file_paths:
        is_valid, error = validate_python_file(file_path)
        if is_valid:
            valid_files.append(file_path)
        else:
            invalid_files.append(file_path)

    return valid_files, invalid_files


def find_python_files(directory: str, exclude_dirs: List[str] = None) -> List[Path]:
    """
    Find all Python files in a directory, excluding specified directories.

    Args:
        directory: Directory to search
        exclude_dirs: List of directory names to exclude

    Returns:
        List of Python file paths
    """
    if exclude_dirs is None:
        exclude_dirs = [".git", "__pycache__", ".venv", "venv", "node_modules"]

    python_files = []
    directory_path = Path(directory)

    for path in directory_path.rglob("*.py"):
        # Check if any part of the path contains excluded directories
        if not any(excluded in path.parts for excluded in exclude_dirs):
            python_files.append(path)

    return sorted(python_files)
