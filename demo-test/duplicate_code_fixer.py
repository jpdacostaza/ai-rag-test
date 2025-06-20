#!/usr/bin/env python3
"""
Critical Duplicate Code Fixer
=============================

This script identifies and helps fix the most critical duplicate code issues
found in the codebase analysis.

Focus areas:
1. Large exact duplicates between files
2. Common utility functions that should be extracted
3. Repeated error handling patterns
"""

from pathlib import Path


def analyze_critical_duplicates():
    """Analyze and report on the most critical duplicate code issues."""

    print("🔍 CRITICAL DUPLICATE CODE ANALYSIS")
    print("=" * 50)

    # Based on our analysis, these are the most critical issues:
    critical_issues = [
        {
            "priority": "HIGH",
            "type": "Exact Duplicate",
            "description": "File validation logic duplicated",
            "files": ["comprehensive_cleanup.py", "simple_cleanup.py"],
            "lines": 15,
            "solution": "Extract to utils/file_validator.py",
        },
        {
            "priority": "HIGH",
            "type": "Similar Functions",
            "description": "Multiple logging setup patterns",
            "files": ["main.py", "cache_manager.py", "adaptive_learning.py"],
            "lines": 8,
            "solution": "Create utils/logging_setup.py",
        },
        {
            "priority": "MEDIUM",
            "type": "Repeated Patterns",
            "description": "Database connection handling",
            "files": ["main.py", "database_manager.py", "storage_manager.py"],
            "lines": 6,
            "solution": "Create utils/db_utils.py",
        },
        {
            "priority": "MEDIUM",
            "type": "Error Handling",
            "description": "Try-catch patterns with logging",
            "files": ["Multiple files"],
            "lines": 5,
            "solution": "Create decorators for common error handling",
        },
    ]

    print("CRITICAL ISSUES FOUND:")
    print("-" * 30)

    for i, issue in enumerate(critical_issues, 1):
        print(f"\n{i}. {issue['priority']} PRIORITY - {issue['type']}")
        print(f"   Description: {issue['description']}")
        print(f"   Files: {', '.join(issue['files'])}")
        print(f"   Duplicate lines: ~{issue['lines']}")
        print(f"   Recommended solution: {issue['solution']}")

    return critical_issues


def create_file_validator_utility():
    """Create a utility module for file validation."""

    utils_dir = Path("utils")
    utils_dir.mkdir(exist_ok=True)

    # Create __init__.py
    (utils_dir / "__init__.py").touch()

    # Create file_validator.py
    validator_content = '''"""
File Validation Utilities
=========================

Common file validation functions extracted from cleanup scripts.
"""

import logging
from pathlib import Path
from typing import Tuple, List


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
        exclude_dirs = ['.git', '__pycache__', '.venv', 'venv', 'node_modules']
    
    python_files = []
    directory_path = Path(directory)
    
    for path in directory_path.rglob('*.py'):
        # Check if any part of the path contains excluded directories
        if not any(excluded in path.parts for excluded in exclude_dirs):
            python_files.append(path)
    
    return sorted(python_files)
'''

    with open(utils_dir / "file_validator.py", "w", encoding="utf-8") as f:
        f.write(validator_content)

    print("✅ Created utils/file_validator.py")
    return utils_dir / "file_validator.py"


def create_logging_setup_utility():
    """Create a utility module for logging setup."""

    utils_dir = Path("utils")
    utils_dir.mkdir(exist_ok=True)

    logging_content = '''"""
Logging Setup Utilities
======================

Standardized logging configuration for the application.
"""

import logging
import logging.handlers
from pathlib import Path
from typing import Optional


def setup_logger(
    name: str,
    level: str = "INFO",
    log_file: Optional[str] = None,
    format_string: Optional[str] = None
) -> logging.Logger:
    """
    Set up a standardized logger.
    
    Args:
        name: Logger name
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional file to log to
        format_string: Custom format string
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # Clear existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # Default format
    if format_string is None:
        format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    formatter = logging.Formatter(format_string)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler if specified
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def get_application_logger(module_name: str) -> logging.Logger:
    """
    Get a standardized application logger for a module.
    
    Args:
        module_name: Name of the module
        
    Returns:
        Configured logger
    """
    return setup_logger(
        name=f"app.{module_name}",
        level="INFO",
        log_file="logs/application.log"
    )


def log_service_status(logger: logging.Logger, service: str, status: str, details: str = ""):
    """
    Log service status in a standardized format.
    
    Args:
        logger: Logger instance
        service: Service name
        status: Status (OK, ERROR, WARNING, etc.)
        details: Additional details
    """
    status_symbols = {
        "OK": "✅",
        "ERROR": "❌", 
        "WARNING": "⚠️",
        "INFO": "ℹ️"
    }
    
    symbol = status_symbols.get(status.upper(), "📝")
    message = f"{symbol} {service}: {status}"
    
    if details:
        message += f" - {details}"
    
    level_map = {
        "OK": logging.INFO,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR
    }
    
    level = level_map.get(status.upper(), logging.INFO)
    logger.log(level, message)
'''

    with open(utils_dir / "logging_setup.py", "w", encoding="utf-8") as f:
        f.write(logging_content)

    print("✅ Created utils/logging_setup.py")
    return utils_dir / "logging_setup.py"


def create_error_handling_utils():
    """Create utilities for common error handling patterns."""

    utils_dir = Path("utils")
    utils_dir.mkdir(exist_ok=True)

    error_handling_content = '''"""
Error Handling Utilities
========================

Common error handling patterns and decorators.
"""

import functools
import logging
from typing import Any, Callable, Optional


logger = logging.getLogger(__name__)


def safe_execute(
    func: Callable,
    default_return: Any = None,
    log_errors: bool = True,
    error_message: Optional[str] = None
) -> Callable:
    """
    Decorator for safe function execution with error handling.
    
    Args:
        func: Function to wrap
        default_return: Value to return on error
        log_errors: Whether to log errors
        error_message: Custom error message
        
    Returns:
        Wrapped function
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            if log_errors:
                msg = error_message or f"Error in {func.__name__}: {e}"
                logger.error(msg, exc_info=True)
            return default_return
    
    return wrapper


def retry_on_failure(
    max_retries: int = 3,
    delay: float = 1.0,
    exceptions: tuple = (Exception,)
) -> Callable:
    """
    Decorator to retry function execution on failure.
    
    Args:
        max_retries: Maximum number of retries
        delay: Delay between retries in seconds
        exceptions: Tuple of exceptions to catch
        
    Returns:
        Wrapped function
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries:
                        logger.warning(
                            f"Attempt {attempt + 1} failed for {func.__name__}: {e}. "
                            f"Retrying in {delay} seconds..."
                        )
                        import time
                        time.sleep(delay)
                    else:
                        logger.error(
                            f"All {max_retries + 1} attempts failed for {func.__name__}: {e}"
                        )
            
            raise last_exception
        
        return wrapper
    return decorator


class ErrorContext:
    """Context manager for standardized error handling."""
    
    def __init__(
        self,
        operation_name: str,
        logger: logging.Logger = None,
        suppress_errors: bool = False
    ):
        self.operation_name = operation_name
        self.logger = logger or logging.getLogger(__name__)
        self.suppress_errors = suppress_errors
        self.success = False
    
    def __enter__(self):
        self.logger.info(f"Starting {self.operation_name}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.success = True
            self.logger.info(f"✅ {self.operation_name} completed successfully")
        else:
            self.logger.error(
                f"❌ {self.operation_name} failed: {exc_val}",
                exc_info=(exc_type, exc_val, exc_tb)
            )
            
            if self.suppress_errors:
                return True  # Suppress the exception
        
        return False
'''

    with open(utils_dir / "error_handling.py", "w", encoding="utf-8") as f:
        f.write(error_handling_content)

    print("✅ Created utils/error_handling.py")
    return utils_dir / "error_handling.py"


def generate_refactoring_plan():
    """Generate a detailed refactoring plan."""

    plan_content = """# Duplicate Code Refactoring Plan

## Phase 1: Immediate Fixes (High Priority)

### 1. Extract File Validation Logic
**Files affected**: `comprehensive_cleanup.py`, `simple_cleanup.py`
**Action**: Replace duplicate validation code with utility function

```python
# Before (in both files):
invalid_files = []
for py_file in python_files:
    try:
        with open(py_file, "r", encoding="utf-8") as f:
            content = f.read()
            compile(content, py_file, "exec")
        logger.debug(f"✅ {py_file}")
    except SyntaxError as e:
        logger.warning(f"❌ {py_file}: {e}")
        invalid_files.append(py_file)

# After:
from utils.file_validator import validate_python_files
valid_files, invalid_files = validate_python_files(python_files)
```

### 2. Standardize Logging Setup
**Files affected**: Multiple files
**Action**: Replace various logging setups with utility function

```python
# Before (various patterns):
logger = logging.getLogger(__name__)
# ... various setup code ...

# After:
from utils.logging_setup import get_application_logger
logger = get_application_logger(__name__)
```

### 3. Common Error Handling
**Files affected**: All modules with try-catch blocks
**Action**: Use error handling decorators and context managers

```python
# Before:
try:
    result = some_operation()
    logger.info("Operation successful")
except Exception as e:
    logger.error(f"Operation failed: {e}")
    return None

# After:
from utils.error_handling import safe_execute, ErrorContext

@safe_execute(default_return=None)
def perform_operation():
    return some_operation()

# Or using context manager:
with ErrorContext("some operation", logger):
    result = some_operation()
```

## Phase 2: Structural Improvements (Medium Priority)

### 1. Database Connection Utilities
Create `utils/db_utils.py` for common database operations.

### 2. Configuration Management
Extract common configuration patterns to `utils/config.py`.

### 3. API Response Handling
Create standardized response handlers in `utils/api_utils.py`.

## Phase 3: Advanced Refactoring (Lower Priority)

### 1. Base Classes
Create base classes for similar functionality.

### 2. Design Patterns
Implement Factory and Strategy patterns where appropriate.

### 3. Plugin Architecture
Consider plugin architecture for extensible functionality.

## Implementation Steps

1. **Create utility modules** (use the created utilities)
2. **Update imports** in existing files
3. **Remove duplicate code** and replace with utility calls
4. **Test thoroughly** to ensure functionality is preserved
5. **Update documentation** to reflect new structure

## Testing Strategy

- Run all existing tests after each change
- Add tests for new utility functions
- Verify that behavior is identical before/after refactoring

## Success Metrics

- Reduce duplicate code by 70%+
- Decrease file-specific error handling by 80%+
- Improve code maintainability scores
- Reduce time to implement similar features

---

*Generated by duplicate code analysis tools*
"""

    with open("readme/REFACTORING_PLAN.md", "w", encoding="utf-8") as f:
        f.write(plan_content)

    print("✅ Created readme/REFACTORING_PLAN.md")


def main():
    """Main function to analyze and create utilities for duplicate code."""

    # Analyze critical issues
    analyze_critical_duplicates()

    print("\n" + "=" * 50)
    print("CREATING UTILITY MODULES")
    print("=" * 50)

    # Create utility modules to address the issues
    create_file_validator_utility()
    create_logging_setup_utility()
    create_error_handling_utils()
    generate_refactoring_plan()

    print("\n" + "=" * 50)
    print("NEXT STEPS")
    print("=" * 50)

    print("\n1. Review the created utility modules in the utils/ directory")
    print("2. Follow the refactoring plan in readme/REFACTORING_PLAN.md")
    print("3. Update existing code to use the new utilities")
    print("4. Test thoroughly after each change")
    print("5. Run duplicate detection again to measure improvement")

    print("\n📊 Expected Results:")
    print("   - 70%+ reduction in duplicate code")
    print("   - Improved maintainability")
    print("   - Standardized error handling")
    print("   - Consistent logging across modules")

    print("\n✨ The utility modules are ready for integration!")


if __name__ == "__main__":
    main()
