"""
Structured Logging Configuration
===============================

This module provides centralized structured logging configuration using structlog,
replacing print statements and improving log analysis capabilities.
"""

import logging
import structlog
import sys
from typing import Dict, Any, Optional
from datetime import datetime
import uuid
from contextvars import ContextVar

# Context variable for correlation IDs
correlation_id: ContextVar[Optional[str]] = ContextVar('correlation_id', default=None)


def get_correlation_id() -> str:
    """Get or generate a correlation ID for request tracking."""
    current_id = correlation_id.get()
    if current_id is None:
        current_id = str(uuid.uuid4())[:8]
        correlation_id.set(current_id)
    return current_id


def set_correlation_id(request_id: str) -> None:
    """Set a correlation ID for request tracking."""
    correlation_id.set(request_id)


def add_correlation_id(logger, method_name, event_dict):
    """Add correlation ID to log entries."""
    event_dict['correlation_id'] = get_correlation_id()
    return event_dict


def add_timestamp(logger, method_name, event_dict):
    """Add timestamp to log entries."""
    event_dict['timestamp'] = datetime.utcnow().isoformat()
    return event_dict


def add_service_info(logger, method_name, event_dict):
    """Add service information to log entries."""
    event_dict['service'] = 'opt-backend'
    event_dict['version'] = '1.0.0'
    return event_dict


def configure_structured_logging(
    log_level: str = "INFO",
    log_format: str = "json",
    log_file: Optional[str] = None
) -> None:
    """
    Configure structured logging for the application.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: Format type ("json", "console", "human")
        log_file: Optional file path for log output
    """
    
    # Convert log level string to logging constant
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Configure processors based on format
    processors = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        add_correlation_id,
        add_timestamp,
        add_service_info,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]
    
    if log_format.lower() == "json":
        processors.append(structlog.processors.JSONRenderer())
    elif log_format.lower() == "console":
        processors.extend([
            structlog.dev.ConsoleRenderer(colors=True),
        ])
    else:  # human-readable format
        processors.extend([
            structlog.processors.TimeStamper(fmt="ISO"),
            structlog.dev.ConsoleRenderer(colors=True),
        ])
    
    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # Configure standard logging
    handlers = []
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    handlers.append(console_handler)
    
    # File handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(numeric_level)
        handlers.append(file_handler)
    
    # DO NOT configure root logger - let human_logging handle that
    # This prevents conflicts with human-readable logging
    pass


def get_structured_logger(name: str) -> structlog.BoundLogger:
    """
    Get a structured logger instance.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Configured structured logger
    """
    return structlog.get_logger(name)


class LoggerMixin:
    """Mixin class to add structured logging to any class."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = get_structured_logger(self.__class__.__module__)
    
    def log_info(self, message: str, **kwargs):
        """Log info message with context."""
        self.logger.info(message, **kwargs)
    
    def log_warning(self, message: str, **kwargs):
        """Log warning message with context."""
        self.logger.warning(message, **kwargs)
    
    def log_error(self, message: str, **kwargs):
        """Log error message with context."""
        self.logger.error(message, **kwargs)
    
    def log_debug(self, message: str, **kwargs):
        """Log debug message with context."""
        self.logger.debug(message, **kwargs)


def log_function_call(func_name: str, args: dict = None, kwargs: dict = None):
    """Log function call with parameters."""
    logger = get_structured_logger(__name__)
    logger.info(
        "Function called",
        function=func_name,
        args=args or {},
        kwargs=kwargs or {}
    )


def log_performance(operation: str, duration_ms: float, **kwargs):
    """Log performance metrics."""
    logger = get_structured_logger(__name__)
    logger.info(
        "Performance metric",
        operation=operation,
        duration_ms=duration_ms,
        **kwargs
    )


def log_request_start(request_id: str, method: str, path: str, **kwargs):
    """Log request start."""
    set_correlation_id(request_id)
    logger = get_structured_logger(__name__)
    logger.info(
        "Request started",
        request_id=request_id,
        method=method,
        path=path,
        **kwargs
    )


def log_request_end(request_id: str, status_code: int, duration_ms: float, **kwargs):
    """Log request completion."""
    logger = get_structured_logger(__name__)
    logger.info(
        "Request completed",
        request_id=request_id,
        status_code=status_code,
        duration_ms=duration_ms,
        **kwargs
    )


def log_error_with_context(error: Exception, context: dict = None, **kwargs):
    """Log error with additional context."""
    logger = get_structured_logger(__name__)
    logger.error(
        "Error occurred",
        error_type=type(error).__name__,
        error_message=str(error),
        context=context or {},
        **kwargs
    )


def log_service_health(service: str, status: str, metrics: dict = None, **kwargs):
    """Log service health status."""
    logger = get_structured_logger(__name__)
    logger.info(
        "Service health check",
        service=service,
        status=status,
        metrics=metrics or {},
        **kwargs
    )


# DO NOT initialize on import - let human_logging take precedence
# Structured logging is available on-demand for specific use cases

# Export commonly used functions
__all__ = [
    'configure_structured_logging',
    'get_structured_logger',
    'LoggerMixin',
    'get_correlation_id',
    'set_correlation_id',
    'log_function_call',
    'log_performance',
    'log_request_start',
    'log_request_end',
    'log_error_with_context',
    'log_service_health'
]
