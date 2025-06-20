"""
Error Handling Utilities
========================

Common error handling patterns and decorators.
"""

import functools
import logging
from typing import Any
from typing import Callable
from typing import Optional

logger = logging.getLogger(__name__)


def safe_execute(
    func: Callable,
    default_return: Any = None,
    log_errors: bool = True,
    error_message: Optional[str] = None,
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
    max_retries: int = 3, delay: float = 1.0, exceptions: tuple = (Exception,)
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
        self, operation_name: str, logger: logging.Logger = None, suppress_errors: bool = False
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
                f"❌ {self.operation_name} failed: {exc_val}", exc_info=(exc_type, exc_val, exc_tb)
            )

            if self.suppress_errors:
                return True  # Suppress the exception

        return False
