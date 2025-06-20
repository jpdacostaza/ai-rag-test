"""
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
    format_string: Optional[str] = None,
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
            log_file, maxBytes=10 * 1024 * 1024, backupCount=5  # 10MB
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
    return setup_logger(name=f"app.{module_name}", level="INFO", log_file="logs/application.log")


def log_service_status(logger: logging.Logger, service: str, status: str, details: str = ""):
    """
    Log service status in a standardized format.

    Args:
        logger: Logger instance
        service: Service name
        status: Status (OK, ERROR, WARNING, etc.)
        details: Additional details
    """
    status_symbols = {"OK": "✅", "ERROR": "❌", "WARNING": "⚠️", "INFO": "ℹ️"}

    symbol = status_symbols.get(status.upper(), "📝")
    message = f"{symbol} {service}: {status}"

    if details:
        message += f" - {details}"

    level_map = {
        "OK": logging.INFO,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
    }

    level = level_map.get(status.upper(), logging.INFO)
    logger.log(level, message)
