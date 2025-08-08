"""
Unified Logging Configuration
============================

This module provides a consolidated logging configuration that combines:
- Human-readable colored output for development/console
- Structured logging for production/analysis
- Single root logger configuration to prevent conflicts
- Proper handler hierarchy to avoid duplication

Based on Python logging best practices from docs.python.org/3/howto/logging-cookbook.html
"""

import logging
import logging.config
import os
import sys
import json
import functools
import time
from datetime import datetime
from typing import Optional, Dict, Any, Callable
from contextvars import ContextVar

# Context variable for correlation IDs
correlation_id: ContextVar[Optional[str]] = ContextVar('correlation_id', default=None)

# Global flag to prevent multiple initialization
_logging_initialized = False

# --- Color and Emoji Definitions ---

COLORS = {
    "DEBUG": "\033[36m",    # Cyan
    "INFO": "\033[32m",     # Green  
    "WARNING": "\033[33m",  # Yellow
    "ERROR": "\033[31m",    # Red
    "CRITICAL": "\033[35m", # Magenta
    "RESET": "\033[0m",     # Reset
    "BOLD": "\033[1m",      # Bold
    "DIM": "\033[2m",       # Dim
}

EMOJIS = {
    "DEBUG": "[SEARCH]",
    "INFO": "[OK]", 
    "WARNING": "[WARN]",
    "ERROR": "[FAIL]",
    "CRITICAL": "***",
}

SERVICE_ICONS = {
    "REDIS": "", "CHROMADB": "", "OLLAMA": "", "DATABASE": "",
    "API": "", "HEALTH": "", "MEMORY": "", "CHAT": "",
    "TOOLS": "", "WATCHDOG": "", "STARTUP": "", "CACHE": "",
    "ERROR": "", "NETWORK": "", "EMBEDDINGS": "",
}


class UnifiedFormatter(logging.Formatter):
    """
    Unified formatter that supports both human-readable and structured output.
    Uses environment variables to determine output style.
    """
    
    def __init__(self, style='human', *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.style = style
        self.use_colors = sys.stdout.isatty() and style == 'human'
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record based on configured style."""
        if self.style == 'json':
            return self._format_json(record)
        else:
            return self._format_human(record)
    
    def _format_json(self, record: logging.LogRecord) -> str:
        """Format as structured JSON."""
        log_entry = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
            'service': 'opt-backend',
        }
        
        # Add correlation ID if available
        if hasattr(record, 'correlation_id'):
            log_entry['correlation_id'] = record.correlation_id
        elif correlation_id.get():
            log_entry['correlation_id'] = correlation_id.get()
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_entry, ensure_ascii=False)
    
    def _format_human(self, record: logging.LogRecord) -> str:
        """Format as human-readable colored output."""
        level_name = record.levelname
        message = record.getMessage()
        
        if self.use_colors:
            level_color = COLORS.get(level_name, "")
            reset, bold, dim = COLORS["RESET"], COLORS["BOLD"], COLORS["DIM"]
        else:
            level_color = reset = bold = dim = ""
        
        emoji = EMOJIS.get(level_name, "")
        timestamp = datetime.fromtimestamp(record.created).strftime("%H:%M:%S")
        
        # Extract service icon from message (e.g., "[REDIS]")
        service_icon = ""
        for service, icon in SERVICE_ICONS.items():
            if f"[{service}]" in message:
                message = message.replace(f"[{service}]", "").strip()
                service_icon = f"{icon} "
                break
        
        # Format based on log level
        if level_name in ["ERROR", "CRITICAL"]:
            return f"{emoji} {bold}{level_color}{timestamp}{reset}  {level_color}{bold}{level_name:<8}{reset}  {service_icon}{bold}{message}{reset}"
        elif level_name == "WARNING":
            return f"{emoji} {level_color}{timestamp}{reset}  {level_color}{level_name:<8}{reset}  {service_icon}{message}"
        elif level_name == "INFO":
            return f"{emoji} {timestamp}  {level_color}{level_name:<8}{reset}  {service_icon}{message}"
        else:  # DEBUG
            return f"{emoji} {dim}{timestamp}  {level_color}{level_name:<8}{reset}  {service_icon}{message}{reset}"


def setup_logging(
    level: str = None,
    style: str = None,
    disable_existing: bool = True
) -> None:
    """
    Set up unified logging configuration using dictConfig approach.
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        style: Output style ('human' for colored console, 'json' for structured)
        disable_existing: Whether to disable existing loggers to prevent conflicts
    """
    global _logging_initialized
    
    if _logging_initialized:
        return
    
    # Determine configuration from environment
    log_level = (level or os.getenv("LOG_LEVEL", "INFO")).upper()
    log_style = style or os.getenv("LOG_STYLE", "human")  # 'human' or 'json'
    
    # Create unified logging configuration
    config = {
        'version': 1,
        'disable_existing_loggers': disable_existing,
        'formatters': {
            'unified': {
                '()': UnifiedFormatter,
                'style': log_style,
            },
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'stream': 'ext://sys.stdout',
                'formatter': 'unified',
                'level': log_level,
            },
        },
        'root': {
            'level': log_level,
            'handlers': ['console'],
        },
        # Configure specific loggers to use NullHandler (library best practice)
        'loggers': {
            'urllib3': {'handlers': ['console'], 'level': 'WARNING', 'propagate': False},
            'requests': {'handlers': ['console'], 'level': 'WARNING', 'propagate': False},
            'uvicorn': {'handlers': ['console'], 'level': 'INFO', 'propagate': False},
            'uvicorn.access': {'handlers': ['console'], 'level': 'WARNING', 'propagate': False},
        }
    }
    
    # Apply the configuration
    logging.config.dictConfig(config)
    
    # Set the initialization flag
    _logging_initialized = True
    
    # Log successful initialization
    logger = logging.getLogger(__name__)
    logger.info(f"[STARTUP]  Unified logging initialized: level={log_level}, style={log_style}")


def get_logger(name: str = None) -> logging.Logger:
    """
    Get a logger instance with proper configuration.
    
    Args:
        name: Logger name (defaults to caller's module)
    
    Returns:
        Configured logger instance
    """
    # Ensure logging is initialized
    if not _logging_initialized:
        setup_logging()
    
    return logging.getLogger(name)


def set_correlation_id(request_id: str) -> None:
    """Set correlation ID for request tracking."""
    correlation_id.set(request_id)


def get_correlation_id() -> Optional[str]:
    """Get current correlation ID."""
    return correlation_id.get()


# --- Convenience Functions ---

def log_service_status(service: str, status: str, details: str = ""):
    """Log service status in a consistent, structured format."""
    logger = get_logger("service_status")
    
    status_icons = {
        "starting": "",
        "ready": "[OK]", 
        "degraded": "[WARN]",
        "failed": "[FAIL]",
        "connecting": "",
        "reconnecting": "[SYNC]",
        "debug": "[SEARCH]",
    }
    icon = status_icons.get(status.lower(), "")
    message = f"[{service.upper()}] {icon} {status.title()}{' - ' + details if details else ''}"

    # Properly map status to log level, including debug
    if status.lower() == "failed":
        log_level = "error"
    elif status.lower() == "degraded":
        log_level = "warning"
    elif status.lower() == "debug":
        log_level = "debug"
    else:
        log_level = "info"
    
    getattr(logger, log_level)(message)


def log_api_request(method: str, endpoint: str, status_code: int, response_time_ms: float):
    """Log API requests with color-coded status and timing."""
    logger = get_logger("api_requests")
    
    if status_code < 400:
        status_emoji = "[OK]"
    elif 400 <= status_code < 500:
        status_emoji = "[WARN]"
    else:
        status_emoji = "[FAIL]"
    logger.info(f"[API] {status_emoji} {method} {endpoint} -> {status_code} ({response_time_ms:.2f}ms)")


def log_chat_interaction(
    user_id: str, message_len: int, response_len: int, 
    tools_used: Optional[list] = None, request_id: Optional[str] = None
):
    """Log chat interaction details."""
    logger = get_logger()
    tools_info = f" (tools: {', '.join(tools_used)})" if tools_used else ""
    req_id_info = f" [ReqID: {request_id}]" if request_id else ""
    logger.info(f"[CHAT]  User {user_id}: {message_len} chars -> {response_len} chars{tools_info}{req_id_info}")


def log_function_call(func: Callable) -> Callable:
    """
    Decorator to log function calls with parameters and execution time.
    
    Args:
        func: The function to wrap
        
    Returns:
        Wrapped function with logging
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        start_time = time.time()
        
        # Log function entry
        logger.debug(f" Calling {func.__name__} with args={args[:3]}{'...' if len(args) > 3 else ''}, kwargs={list(kwargs.keys())}")
        
        try:
            result = func(*args, **kwargs)
            execution_time = (time.time() - start_time) * 1000
            logger.debug(f"[OK] {func.__name__} completed in {execution_time:.2f}ms")
            return result
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            logger.error(f"[FAIL] {func.__name__} failed after {execution_time:.2f}ms: {e}")
            raise
    
    return wrapper


def log_performance(operation: str, start_time: float, metadata: Dict[str, Any] = None):
    """
    Log performance metrics for an operation.
    
    Args:
        operation: Name of the operation
        start_time: Start time (from time.time())
        metadata: Additional metadata to log
    """
    logger = get_logger("performance")
    execution_time = (time.time() - start_time) * 1000
    
    log_data = {
        "operation": operation,
        "execution_time_ms": round(execution_time, 2),
        "timestamp": datetime.utcnow().isoformat(),
    }
    
    if metadata:
        log_data.update(metadata)
    
    if execution_time > 1000:  # > 1 second
        logger.warning(f"[WARN] Slow operation: {operation} took {execution_time:.2f}ms", extra=log_data)
    else:
        logger.info(f"[CHART] {operation} completed in {execution_time:.2f}ms", extra=log_data)


# Initialize logging when module is imported
setup_logging()
