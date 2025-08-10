"""
Unified Logging System
=====================

This module provides a single, consolidated logging configuration that replaces all other
logging configurations in the system. It handles:
- Human-readable colored output for development/console
- Structured JSON logging for production/analysis  
- Service-specific formatters and filters
- Correlation ID tracking
- Performance logging
- API request logging
- Automatic deduplication of repeated messages

Usage:
    from core.unified_logging import get_logger, setup_logging
    
    # Initialize once at application startup
    setup_logging()
    
    # Use in any module
    logger = get_logger(__name__)
    logger.info("Message")

Environment Variables:
    LOG_LEVEL: DEBUG, INFO, WARNING, ERROR, CRITICAL (default: INFO)
    LOG_STYLE: human, json (default: human)
    LOG_DEDUP_WINDOW: Seconds to suppress duplicate messages (default: 2.0)
"""

import logging
import logging.config
import os
import sys
import json
import functools
import time
from datetime import datetime, timezone
from typing import Optional, Dict, Any, Callable, Union
from contextvars import ContextVar

# Context variable for correlation IDs
correlation_id: ContextVar[Optional[str]] = ContextVar('correlation_id', default=None)

# Global flag to prevent multiple initialization
_logging_initialized = False
_single_handler_enforced = False  # Guard to ensure we only prune duplicate handlers once

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
    "ERROR": "", "NETWORK": "", "EMBEDDINGS": "", "GATEWAY": "",
    "AUTH": "", "PIPELINE": "", "SYSTEM": "", "VECTOR": "",
    "LLM": "", "SYNC": "", "CHART": "",
}


class UnifiedFormatter(logging.Formatter):
    """
    Unified formatter that supports both human-readable and structured output.
    Automatically detects TTY for color support and formats messages with service icons.
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
        """Format as structured JSON for production logging."""
        log_entry = {
            'timestamp': datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
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
        
        # Add extra fields if present
        if hasattr(record, 'extra'):
            log_entry.update(record.extra)
        
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_entry, ensure_ascii=False, separators=(',', ':'))
    
    def _format_human(self, record: logging.LogRecord) -> str:
        """Format as human-readable colored output with service icons."""
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
                service_icon = f"{icon} " if icon else ""
                break
        
        # Format based on log level with consistent width
        if level_name in ["ERROR", "CRITICAL"]:
            return f"{emoji} {bold}{level_color}{timestamp}{reset}  {level_color}{bold}{level_name:<8}{reset}  {service_icon}{bold}{message}{reset}"
        elif level_name == "WARNING":
            return f"{emoji} {level_color}{timestamp}{reset}  {level_color}{level_name:<8}{reset}  {service_icon}{message}"
        elif level_name == "INFO":
            return f"{emoji} {timestamp}  {level_color}{level_name:<8}{reset}  {service_icon}{message}"
        else:  # DEBUG
            return f"{emoji} {dim}{timestamp}  {level_color}{level_name:<8}{reset}  {service_icon}{message}{reset}"


class DedupFilter(logging.Filter):
    """Suppress duplicate log messages within a time window.

    Enhancements:
      * Collapses multi-line startup summaries into a single canonical key so
        repeated emission (due to duplicate startup invocation) is suppressed.
      * Normalizes whitespace for comparison stability.
      * Uses class-level shared state to ensure deduplication works across all instances.
      * More aggressive deduplication with longer window for startup messages.
    """
    # Class-level shared state to ensure deduplication across all instances
    _shared_last_messages = {}  # Dictionary to track multiple recent messages
    _shared_window = None
    
    def __init__(self, window_seconds: float = None):
        super().__init__()
        if DedupFilter._shared_window is None:
            DedupFilter._shared_window = float(os.getenv("LOG_DEDUP_WINDOW", window_seconds or 2.0))

    def _canonicalize(self, msg: str) -> str:
        # Ultra-aggressive canonicalization: strip all variable parts
        import re
        
        # Remove trace IDs, execution timestamps, and other variable parts
        msg = re.sub(r'\[TRACE:[a-f0-9]+\]', '', msg)
        msg = re.sub(r'\[EXEC:\d+\.\d+\]', '', msg)
        msg = re.sub(r'in \d+\.\d+s', 'in X.Xs', msg)
        msg = re.sub(r'Model \w+[\d\.:b]+', 'Model XXX', msg)
        
        # Service status block patterns
        if "SERVICE STATUS SUMMARY" in msg or ("Redis:" in msg and "ChromaDB:" in msg):
            return "STARTUP_SUMMARY_BLOCK"
        if "Model" in msg and ("available" in msg or "Ready" in msg):
            return "MODEL_AVAILABLE_GENERIC"
        if "Model preloading disabled" in msg:
            return "MODEL_PRELOAD_DISABLED"
        if "Model initialization" in msg and ("starting" in msg or "completed" in msg):
            return "MODEL_INITIALIZATION_GENERIC"
        if "Cache management system initialized" in msg:
            return "CACHE_INITIALIZED"
        if "Background systems initialized" in msg:
            return "BACKGROUND_INITIALIZED"
        if "Watchdog service skipped" in msg:
            return "WATCHDOG_SKIPPED"
        if "FastAPI LLM Backend startup completed" in msg:
            return "STARTUP_COMPLETED"
        if "Memory service initialized successfully" in msg:
            return "MEMORY_INITIALIZED"
        if "Application startup completed successfully" in msg:
            return "APP_STARTUP_COMPLETED"
        if "startup_event called" in msg:
            return "STARTUP_EVENT_CALLED"
        if "Phase" in msg and ("Background services" in msg or "Model and cache" in msg):
            return "STARTUP_PHASE_GENERIC"
            
        # Collapse whitespace and normalize
        return " ".join(msg.split()).strip()

    def filter(self, record: logging.LogRecord) -> bool:  # type: ignore
        msg = record.getMessage()
        key = (record.levelno, self._canonicalize(msg))
        now = record.created
        
        # Use much longer window for startup-related messages (30s vs 6s)
        is_startup_msg = any(x in msg for x in ["Model", "Cache", "Background", "SERVICE STATUS", "startup", "Phase", "TRACE:", "Ready", "initialization"])
        window = self._shared_window * 15 if is_startup_msg else self._shared_window
        
        # Check if this message was seen recently
        if key in DedupFilter._shared_last_messages:
            last_time = DedupFilter._shared_last_messages[key]
            if (now - last_time) < window:
                return False
        
        # Clean old entries periodically (every 100 messages)
        if len(DedupFilter._shared_last_messages) % 100 == 0:
            cutoff = now - (window * 2)
            DedupFilter._shared_last_messages = {k: v for k, v in DedupFilter._shared_last_messages.items() if v > cutoff}
        
        # Record this message
        DedupFilter._shared_last_messages[key] = now
        return True


def setup_logging(
    level: str = None,
    style: str = None,
    disable_existing: bool = True,
    force_reinit: bool = False
) -> None:
    """
    Set up unified logging configuration for the entire application.
    This should be called once at application startup.
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        style: Output style ('human' for colored console, 'json' for structured)
        disable_existing: Whether to disable existing loggers to prevent conflicts
        force_reinit: Force re-initialization even if already configured
    """
    global _logging_initialized
    
    if _logging_initialized and not force_reinit:
        return
    
    # Clear any existing handlers to prevent duplication and detect external interference
    root_logger = logging.getLogger()
    if root_logger.handlers:
        print(f"[LOGGING] Removing {len(root_logger.handlers)} existing handlers to prevent duplication", flush=True)
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
    
    # Disable Python's default logging.basicConfig to prevent external interference
    logging.basicConfig = lambda *args, **kwargs: None
    
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
        'filters': {
            'dedup': {'()': DedupFilter}
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'stream': 'ext://sys.stdout',
                'formatter': 'unified',
                'level': log_level,
                'filters': ['dedup']
            },
        },
        'root': {
            'level': log_level,
            'handlers': ['console'],
        },
        # Configure problematic third-party loggers
        'loggers': {
            'urllib3': {'level': 'WARNING', 'propagate': True},
            'requests': {'level': 'WARNING', 'propagate': True},
            'uvicorn': {'level': 'INFO', 'propagate': True},
            'uvicorn.access': {'level': 'WARNING', 'propagate': True},
            'uvicorn.error': {'level': 'INFO', 'propagate': True},
            'httpx': {'level': 'WARNING', 'propagate': True},
            'chromadb': {'level': 'WARNING', 'propagate': True},
            'sentence_transformers': {'level': 'WARNING', 'propagate': True},
        }
    }
    
    # Apply the configuration
    logging.config.dictConfig(config)
    
    # Validate single handler setup
    root_handlers = logging.getLogger().handlers
    if len(root_handlers) != 1:
        print(f"[LOGGING] WARNING: Expected 1 handler, found {len(root_handlers)}. This may cause duplicates.", flush=True)
    
    # Set the initialization flag
    _logging_initialized = True
    
    # Log successful initialization once
    logger = logging.getLogger(__name__)
    logger.info(f"Unified logging initialized: level={log_level}, style={log_style}")
    # Diagnostic: report handler count (helps detect external basicConfig usage later)
    logger.debug(f"Root logger handler count after init: {len(root_handlers)} -> {[type(h).__name__ for h in root_handlers]}")


def get_logger(name: str = None) -> logging.Logger:
    """
    Get a logger instance with proper unified configuration.
    
    Args:
        name: Logger name (defaults to caller's module name)
    
    Returns:
        Configured logger instance
    
    Note: If setup_logging() hasn't been called yet, returns a basic logger
    that will be properly configured once setup_logging() is called.
    """
    logger = logging.getLogger(name)
    
    # If unified logging hasn't been initialized yet, don't add fallback handlers
    # to avoid duplicate logging - let the main setup_logging() handle it
    if not _logging_initialized:
        return logger  # Will be configured later
    # Enforce single console handler if some third-party added another StreamHandler
    global _single_handler_enforced
    if (not _single_handler_enforced) and os.getenv("LOG_ENFORCE_SINGLE_HANDLER", "true").lower() == "true":
        root_logger = logging.getLogger()
        stream_handlers = [h for h in root_logger.handlers if isinstance(h, logging.StreamHandler)]
        if len(stream_handlers) > 1:
            for h in stream_handlers[1:]:
                root_logger.removeHandler(h)
            for h in root_logger.handlers:
                has_dedup = any(isinstance(f, DedupFilter) for f in getattr(h, 'filters', []))
                if not has_dedup:
                    h.addFilter(DedupFilter())
            _single_handler_enforced = True
            if root_logger.isEnabledFor(logging.DEBUG):
                root_logger.debug("Duplicate console handlers pruned to prevent log duplication")
    return logger


def set_correlation_id(request_id: str) -> None:
    """Set correlation ID for request tracking across log messages."""
    correlation_id.set(request_id)


def get_correlation_id() -> Optional[str]:
    """Get current correlation ID if set."""
    return correlation_id.get()


def reset_logging() -> None:
    """Reset logging configuration. Useful for testing."""
    global _logging_initialized
    _logging_initialized = False
    logging.getLogger().handlers.clear()


# --- Convenience Logging Functions ---

def log_service_status(service: str, status: str, details: str = "") -> None:
    """Log service status with lightweight rapid duplicate suppression.

    Suppresses identical (service,status,details) tuples logged within a short window
    to further reduce any residual duplication beyond DedupFilter (belt & suspenders).
    """
    logger = get_logger("service_status")

    # Localized suppression cache stored as function attribute
    now = time.time()
    window = float(os.getenv("SERVICE_STATUS_SUPPRESS_WINDOW", "2.0"))  # seconds
    try:
        cache: Dict[Tuple[str,str,str], float] = getattr(log_service_status, "_recent", {})  # type: ignore
    except Exception:  # pragma: no cover
        cache = {}

    key = (service.lower(), status.lower(), details.strip())
    last = cache.get(key)
    if last and (now - last) < window:
        return  # Suppress rapid duplicate
    cache[key] = now
    # Periodic cleanup to keep cache small
    if len(cache) > 256:
        cutoff = now - window
        for k in list(cache.keys()):
            if cache[k] < cutoff:
                del cache[k]
    setattr(log_service_status, "_recent", cache)  # type: ignore

    status_icons = {
        "starting": "",
        "ready": "[OK]",
        "degraded": "[WARN]",
        "failed": "[FAIL]",
        "connecting": "",
        "reconnecting": "[SYNC]",
        "debug": "[SEARCH]",
        "healthy": "[OK]",
        "unhealthy": "[FAIL]",
        "warning": "[WARN]",
    }

    icon = status_icons.get(status.lower(), "")
    message = f"[{service.upper()}] {icon} {status.title()}{' - ' + details if details else ''}"

    lvl = status.lower()
    if lvl in ("failed", "unhealthy"):
        logger.error(message)
    elif lvl in ("degraded", "warning"):
        logger.warning(message)
    elif lvl == "debug":
        logger.debug(message)
    else:
        logger.info(message)


def log_api_request(method: str, endpoint: str, status_code: int, response_time_ms: float) -> None:
    """
    Log API requests with status-appropriate formatting.
    
    Args:
        method: HTTP method (GET, POST, etc.)
        endpoint: API endpoint path
        status_code: HTTP status code
        response_time_ms: Response time in milliseconds
    """
    logger = get_logger("api_requests")
    
    if status_code < 400:
        status_emoji = "[OK]"
        log_func = logger.info
    elif 400 <= status_code < 500:
        status_emoji = "[WARN]"
        log_func = logger.warning
    else:
        status_emoji = "[FAIL]"
        log_func = logger.error
    
    log_func(f"[API] {status_emoji} {method} {endpoint} -> {status_code} ({response_time_ms:.2f}ms)")


def log_chat_interaction(
    user_id: str, 
    message_len: int, 
    response_len: int, 
    tools_used: Optional[list] = None, 
    request_id: Optional[str] = None
) -> None:
    """
    Log chat interaction details in a structured format.
    
    Args:
        user_id: User identifier
        message_len: Length of user message in characters
        response_len: Length of response in characters
        tools_used: List of tools/functions used (optional)
        request_id: Request correlation ID (optional)
    """
    logger = get_logger("chat")
    tools_info = f" (tools: {', '.join(tools_used)})" if tools_used else ""
    req_id_info = f" [ReqID: {request_id}]" if request_id else ""
    logger.info(f"[CHAT]  User {user_id}: {message_len} chars -> {response_len} chars{tools_info}{req_id_info}")


def log_function_call(func: Callable) -> Callable:
    """
    Decorator to log function calls with parameters and execution time.
    Useful for debugging and performance monitoring.
    
    Args:
        func: The function to wrap
        
    Returns:
        Wrapped function with logging
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        start_time = time.time()
        
        # Log function entry (only in debug mode)
        logger.debug(f" Calling {func.__name__} with args={args[:3]}{'...' if len(args) > 3 else ''}, kwargs={list(kwargs.keys())}")
        
        try:
            result = func(*args, **kwargs)
            execution_time = (time.time() - start_time) * 1000
            if execution_time > 100:  # Only log slow operations
                logger.debug(f"[OK] {func.__name__} completed in {execution_time:.2f}ms")
            return result
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            logger.error(f"[FAIL] {func.__name__} failed after {execution_time:.2f}ms: {e}")
            raise
    
    return wrapper


def log_performance(operation: str, start_time: float, metadata: Dict[str, Any] = None) -> None:
    """
    Log performance metrics for an operation.
    
    Args:
        operation: Name of the operation
        start_time: Start time (from time.time())
        metadata: Additional metadata to include in log
    """
    logger = get_logger("performance")
    execution_time = (time.time() - start_time) * 1000
    
    # Add extra metadata as record extra
    extra = metadata or {}
    extra.update({
        "operation": operation,
        "execution_time_ms": round(execution_time, 2),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })
    
    if execution_time > 1000:  # > 1 second
        logger.warning(f"[WARN] Slow operation: {operation} took {execution_time:.2f}ms", extra=extra)
    else:
        logger.info(f"[CHART] {operation} completed in {execution_time:.2f}ms", extra=extra)


def log_memory_operation(operation: str, user_id: str, collection: str, details: str = "") -> None:
    """Log memory system operations."""
    logger = get_logger("memory")
    details_str = f" - {details}" if details else ""
    logger.info(f"[MEMORY]  {operation} for user {user_id} in {collection}{details_str}")


def log_error_context(error: Exception, context: Dict[str, Any] = None) -> None:
    """Log error with additional context information."""
    logger = get_logger("errors")
    context_str = f" Context: {context}" if context else ""
    logger.error(f"[ERROR]  {type(error).__name__}: {error}{context_str}", exc_info=True)


# Compatibility functions for gradual migration
def setup_human_logging(level: str = "INFO") -> None:
    """Compatibility function - redirects to setup_logging with human style."""
    setup_logging(level=level, style='human')


# Export commonly used functions
__all__ = [
    'setup_logging', 'get_logger', 'log_service_status', 'log_api_request',
    'log_chat_interaction', 'log_function_call', 'log_performance',
    'log_memory_operation', 'log_error_context', 'set_correlation_id', 
    'get_correlation_id', 'reset_logging', 'setup_human_logging'
]
