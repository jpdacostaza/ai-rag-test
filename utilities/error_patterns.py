"""
Unified Error Handling Patterns
==============================

This module provides decorators, context managers, and utilities to standardize
error handling across the entire application, eliminating the 50+ repeated
try/catch patterns identified in the codebase.

Key Features:
- @handle_service_errors decorator for consistent error handling
- ErrorContext context manager for complex operations
- StandardizedErrorResponse for API consistency
- Service-specific error handlers (LLM, Database, Memory, etc.)
- Integration with existing logging systems
"""

import asyncio
import functools
import logging
import traceback
import uuid
from contextlib import asynccontextmanager, contextmanager
from datetime import datetime, timezone
from enum import Enum
from typing import Any, AsyncGenerator, Callable, Dict, Optional, Type, TypeVar, Union

from fastapi import HTTPException
from pydantic import BaseModel

from core.unified_logging import log_service_status


class ErrorSeverity(Enum):
    """Error severity levels for consistent classification."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ServiceType(Enum):
    """Service types for context-aware error handling."""
    API = "api"
    DATABASE = "database"
    LLM = "llm"
    MEMORY = "memory"
    CACHE = "cache"
    AUTH = "auth"
    PIPELINE = "pipeline"
    SEARCH = "search"
    VALIDATION = "validation"
    GENERAL = "general"


class ErrorAction(Enum):
    """Actions to take when errors occur."""
    RAISE = "raise"           # Re-raise the exception
    RETURN_DEFAULT = "default"  # Return a default value
    RETURN_EMPTY = "empty"    # Return empty list/dict/None
    FALLBACK = "fallback"     # Try fallback mechanism
    RETRY = "retry"           # Retry the operation
    LOG_ONLY = "log_only"     # Just log and continue


class StandardizedErrorResponse(BaseModel):
    """Standardized error response format for APIs."""
    error: bool = True
    error_type: str
    error_message: str
    error_code: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    request_id: Optional[str] = None
    timestamp: datetime
    suggestion: Optional[str] = None


T = TypeVar('T')


class ErrorHandlerConfig:
    """Configuration for error handling behavior."""
    
    def __init__(
        self,
        service_type: ServiceType = ServiceType.GENERAL,
        action: ErrorAction = ErrorAction.LOG_ONLY,
        default_value: Any = None,
        max_retries: int = 0,
        retry_delay: float = 1.0,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        log_traceback: bool = False,
        raise_on_critical: bool = True,
        fallback_function: Optional[Callable] = None
    ):
        self.service_type = service_type
        self.action = action
        self.default_value = default_value
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.severity = severity
        self.log_traceback = log_traceback
        self.raise_on_critical = raise_on_critical
        self.fallback_function = fallback_function


def handle_service_errors(
    config: Optional[ErrorHandlerConfig] = None,
    service_name: Optional[str] = None,
    operation_name: Optional[str] = None,
    user_id: Optional[str] = None,
    request_id: Optional[str] = None
):
    """
    Decorator for standardized error handling across all services.
    
    Args:
        config: Error handling configuration
        service_name: Name of the service for logging context
        operation_name: Name of the operation being performed
        user_id: User ID for context (optional)
        request_id: Request ID for tracing (optional)
    
    Example:
        @handle_service_errors(
            config=ErrorHandlerConfig(
                service_type=ServiceType.DATABASE,
                action=ErrorAction.RETURN_DEFAULT,
                default_value=[],
                max_retries=3
            ),
            service_name="DatabaseManager",
            operation_name="retrieve_user_memory"
        )
        async def retrieve_memory(user_id: str, query: str):
            # Your code here
            pass
    """
    
    if config is None:
        config = ErrorHandlerConfig()
    
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> T:
            context = {
                "service_name": service_name or func.__module__,
                "operation_name": operation_name or func.__name__,
                "user_id": user_id,
                "request_id": request_id or str(uuid.uuid4()),
                "function": f"{func.__module__}.{func.__name__}",
                "args_count": len(args),
                "kwargs_keys": list(kwargs.keys())
            }
            
            last_exception = None
            
            for attempt in range(config.max_retries + 1):
                try:
                    if asyncio.iscoroutinefunction(func):
                        result = await func(*args, **kwargs)
                    else:
                        result = func(*args, **kwargs)
                    
                    # Log successful retry if this wasn't the first attempt
                    if attempt > 0:
                        log_service_status(
                            config.service_type.value.upper(),
                            "info",
                            f"[OK] {context['operation_name']} succeeded on retry {attempt + 1}"
                        )
                    
                    return result
                    
                except Exception as e:
                    last_exception = e
                    context["error"] = str(e)
                    context["error_type"] = type(e).__name__
                    context["attempt"] = attempt + 1
                    context["max_attempts"] = config.max_retries + 1
                    
                    # Log the error with appropriate severity
                    error_message = f"[FAIL] {context['operation_name']} failed"
                    if attempt < config.max_retries:
                        error_message += f" (attempt {attempt + 1}/{config.max_retries + 1}), retrying..."
                        log_level = "warning"
                    else:
                        error_message += f" after {config.max_retries + 1} attempts"
                        log_level = "error" if config.severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL] else "warning"
                    
                    error_message += f": {str(e)}"
                    
                    log_service_status(
                        config.service_type.value.upper(),
                        log_level,
                        error_message
                    )
                    
                    # Log traceback for debugging if configured
                    if config.log_traceback:
                        logging.error(f"[{config.service_type.value.upper()}] Traceback for {context['operation_name']}: {traceback.format_exc()}")
                    
                    # If we have more retries, wait and continue
                    if attempt < config.max_retries:
                        await asyncio.sleep(config.retry_delay)
                        continue
                    
                    # Final attempt failed, handle according to configuration
                    break
            
            # All retries exhausted, handle the error
            return _handle_final_error(last_exception, config, context)
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> T:
            context = {
                "service_name": service_name or func.__module__,
                "operation_name": operation_name or func.__name__,
                "user_id": user_id,
                "request_id": request_id or str(uuid.uuid4()),
                "function": f"{func.__module__}.{func.__name__}",
                "args_count": len(args),
                "kwargs_keys": list(kwargs.keys())
            }
            
            last_exception = None
            
            for attempt in range(config.max_retries + 1):
                try:
                    result = func(*args, **kwargs)
                    
                    # Log successful retry if this wasn't the first attempt
                    if attempt > 0:
                        log_service_status(
                            config.service_type.value.upper(),
                            "info",
                            f"[OK] {context['operation_name']} succeeded on retry {attempt + 1}"
                        )
                    
                    return result
                    
                except Exception as e:
                    last_exception = e
                    context["error"] = str(e)
                    context["error_type"] = type(e).__name__
                    context["attempt"] = attempt + 1
                    context["max_attempts"] = config.max_retries + 1
                    
                    # Log the error with appropriate severity
                    error_message = f"[FAIL] {context['operation_name']} failed"
                    if attempt < config.max_retries:
                        error_message += f" (attempt {attempt + 1}/{config.max_retries + 1}), retrying..."
                        log_level = "warning"
                    else:
                        error_message += f" after {config.max_retries + 1} attempts"
                        log_level = "error" if config.severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL] else "warning"
                    
                    error_message += f": {str(e)}"
                    
                    log_service_status(
                        config.service_type.value.upper(),
                        log_level,
                        error_message
                    )
                    
                    # Log traceback for debugging if configured
                    if config.log_traceback:
                        logging.error(f"[{config.service_type.value.upper()}] Traceback for {context['operation_name']}: {traceback.format_exc()}")
                    
                    # If we have more retries, wait and continue
                    if attempt < config.max_retries:
                        import time
                        time.sleep(config.retry_delay)
                        continue
                    
                    # Final attempt failed, handle according to configuration
                    break
            
            # All retries exhausted, handle the error
            return _handle_final_error(last_exception, config, context)
        
        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def _handle_final_error(exception: Exception, config: ErrorHandlerConfig, context: Dict[str, Any]) -> Any:
    """Handle the final error after all retries are exhausted."""
    
    # Try fallback function if configured
    if config.fallback_function:
        try:
            log_service_status(
                config.service_type.value.upper(),
                "info",
                f"[SYNC] Attempting fallback for {context['operation_name']}"
            )
            return config.fallback_function()
        except Exception as fallback_error:
            log_service_status(
                config.service_type.value.upper(),
                "error",
                f"[FAIL] Fallback also failed for {context['operation_name']}: {fallback_error}"
            )
    
    # Handle based on configured action
    if config.action == ErrorAction.RAISE or (config.severity == ErrorSeverity.CRITICAL and config.raise_on_critical):
        raise exception
    elif config.action == ErrorAction.RETURN_DEFAULT:
        return config.default_value
    elif config.action == ErrorAction.RETURN_EMPTY:
        return config.default_value  # Should be [] for empty collections
    elif config.action == ErrorAction.LOG_ONLY:
        return None
    else:
        # Default: return None and log
        return None


@asynccontextmanager
async def error_context(
    service_name: str,
    operation_name: str,
    config: Optional[ErrorHandlerConfig] = None,
    **context_data
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Async context manager for error handling in complex operations.
    
    Example:
        async with error_context("DatabaseManager", "user_memory_retrieval", 
                                config=ErrorHandlerConfig(service_type=ServiceType.DATABASE)) as ctx:
            ctx["user_id"] = user_id
            # Your complex operation here
            result = await complex_database_operation()
            ctx["result_count"] = len(result)
    """
    
    if config is None:
        config = ErrorHandlerConfig()
    
    context = {
        "service_name": service_name,
        "operation_name": operation_name,
        "request_id": str(uuid.uuid4()),
        "start_time": datetime.now(timezone.utc),
        **context_data,
    }
    
    try:
        log_service_status(
            config.service_type.value.upper(),
            "info",
            f"[SYNC] Starting {operation_name}")

        yield context

        # Log successful completion
        duration = (datetime.now(timezone.utc) - context["start_time"]).total_seconds()
        log_service_status(
            config.service_type.value.upper(),
            "info",
            f"[OK] {operation_name} completed successfully in {duration:.2f}s"
        )

    except Exception as e:
        duration = (datetime.now(timezone.utc) - context["start_time"]).total_seconds()
        context.update({
            "error": str(e),
            "error_type": type(e).__name__,
            "duration": duration
        })
        
        log_service_status(
            config.service_type.value.upper(),
            "error" if config.severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL] else "warning",
            f"[FAIL] {operation_name} failed after {duration:.2f}s: {str(e)}"
        )
        
        if config.log_traceback:
            logging.error(f"[{config.service_type.value.upper()}] Traceback for {operation_name}: {traceback.format_exc()}")
        
        # Handle error according to configuration (context manager - no return values)
        if config.action == ErrorAction.RAISE or (config.severity == ErrorSeverity.CRITICAL and config.raise_on_critical):
            raise
        elif config.fallback_function:
            try:
                # Execute fallback for side effects only (context managers can't return values)
                config.fallback_function()
                log_service_status(
                    config.service_type.value.upper(),
                    "info", 
                    f"[SYNC] Executed fallback function for {operation_name}"
                )
            except Exception as fallback_error:
                log_service_status(
                    config.service_type.value.upper(),
                    "error",
                    f"[FAIL] Fallback also failed for {operation_name}: {fallback_error}"
                )
                if config.action == ErrorAction.RAISE:
                    raise


@contextmanager
def sync_error_context(
    service_name: str,
    operation_name: str,
    config: Optional[ErrorHandlerConfig] = None,
    **context_data
):
    """
    Synchronous context manager for error handling.
    
    Example:
        with sync_error_context("ConfigManager", "load_configuration") as ctx:
            ctx["config_file"] = "app.yaml"
            # Your operation here
            config = load_config_file()
    """
    
    if config is None:
        config = ErrorHandlerConfig()
    
    context = {
        "service_name": service_name,
        "operation_name": operation_name,
        "request_id": str(uuid.uuid4()),
        "start_time": datetime.now(timezone.utc),
        **context_data,
    }
    
    try:
        log_service_status(
            config.service_type.value.upper(),
            "info",
            f"[SYNC] Starting {operation_name}")

        yield context

        # Log successful completion
        duration = (datetime.now(timezone.utc) - context["start_time"]).total_seconds()
        log_service_status(
            config.service_type.value.upper(),
            "info",
            f"[OK] {operation_name} completed successfully in {duration:.2f}s"
        )

    except Exception as e:
        duration = (datetime.now(timezone.utc) - context["start_time"]).total_seconds()
        context.update({
            "error": str(e),
            "error_type": type(e).__name__,
            "duration": duration
        })
        
        log_service_status(
            config.service_type.value.upper(),
            "error" if config.severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL] else "warning",
            f"[FAIL] {operation_name} failed after {duration:.2f}s: {str(e)}"
        )
        
        if config.log_traceback:
            logging.error(f"[{config.service_type.value.upper()}] Traceback for {operation_name}: {traceback.format_exc()}")
        
        # Handle error according to configuration (sync context manager - no return values)
        if config.action == ErrorAction.RAISE or (config.severity == ErrorSeverity.CRITICAL and config.raise_on_critical):
            raise
        elif config.fallback_function:
            try:
                # Execute fallback for side effects only (context managers can't return values)
                config.fallback_function()
                log_service_status(
                    config.service_type.value.upper(),
                    "info",
                    f"[SYNC] Executed fallback function for {operation_name}"
                )
            except Exception as fallback_error:
                log_service_status(
                    config.service_type.value.upper(),
                    "error",
                    f"[FAIL] Fallback also failed for {operation_name}: {fallback_error}"
                )
                if config.action == ErrorAction.RAISE:
                    raise


# Pre-configured error handlers for common service types

class ServiceErrorConfigs:
    """Pre-configured error handling configs for different service types."""
    
    DATABASE = ErrorHandlerConfig(
        service_type=ServiceType.DATABASE,
        action=ErrorAction.RETURN_EMPTY,
        default_value=[],
        max_retries=3,
        retry_delay=1.0,
        severity=ErrorSeverity.HIGH,
        log_traceback=True
    )
    
    LLM = ErrorHandlerConfig(
        service_type=ServiceType.LLM,
        action=ErrorAction.RETURN_DEFAULT,
        default_value="I apologize, but I'm experiencing technical difficulties. Please try again.",
        max_retries=2,
        retry_delay=2.0,
        severity=ErrorSeverity.HIGH,
        log_traceback=False
    )
    
    MEMORY = ErrorHandlerConfig(
        service_type=ServiceType.MEMORY,
        action=ErrorAction.RETURN_EMPTY,
        default_value=[],
        max_retries=2,
        retry_delay=1.0,
        severity=ErrorSeverity.MEDIUM,
        log_traceback=False
    )
    
    CACHE = ErrorHandlerConfig(
        service_type=ServiceType.CACHE,
        action=ErrorAction.LOG_ONLY,
        max_retries=1,
        retry_delay=0.5,
        severity=ErrorSeverity.LOW,
        log_traceback=False
    )
    
    API = ErrorHandlerConfig(
        service_type=ServiceType.API,
        action=ErrorAction.RAISE,
        severity=ErrorSeverity.HIGH,
        log_traceback=True
    )
    
    VALIDATION = ErrorHandlerConfig(
        service_type=ServiceType.VALIDATION,
        action=ErrorAction.RAISE,
        severity=ErrorSeverity.MEDIUM,
        log_traceback=False
    )


def create_api_error_response(
    error: Exception,
    error_code: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
    request_id: Optional[str] = None,
    suggestion: Optional[str] = None
) -> StandardizedErrorResponse:
    """Create a standardized API error response."""
    
    return StandardizedErrorResponse(
        error_type=type(error).__name__,
        error_message=str(error),
        error_code=error_code,
        request_id=request_id or str(uuid.uuid4()),
    timestamp=datetime.now(timezone.utc),
        suggestion=suggestion
    )


def handle_api_error(error: Exception, status_code: int = 500) -> HTTPException:
    """Convert any exception to a standardized HTTP exception."""
    
    error_response = create_api_error_response(error)
    
    raise HTTPException(
        status_code=status_code,
        detail=error_response.dict()
    )


# Convenience decorators for common patterns

def handle_database_errors(operation_name: str = None, default_value: Any = None):
    """Convenience decorator for database operations."""
    config = ServiceErrorConfigs.DATABASE
    if default_value is not None:
        config = ErrorHandlerConfig(
            service_type=config.service_type,
            action=config.action,
            default_value=default_value,
            max_retries=config.max_retries,
            retry_delay=config.retry_delay,
            severity=config.severity,
            log_traceback=config.log_traceback,
            raise_on_critical=config.raise_on_critical,
            fallback_function=config.fallback_function
        )
    
    return handle_service_errors(
        config=config,
        service_name="Database",
        operation_name=operation_name
    )


def handle_llm_errors(operation_name: str = None, fallback_message: str = None):
    """Convenience decorator for LLM operations."""
    config = ServiceErrorConfigs.LLM
    if fallback_message:
        config = ErrorHandlerConfig(
            service_type=config.service_type,
            action=config.action,
            default_value=fallback_message,
            max_retries=config.max_retries,
            retry_delay=config.retry_delay,
            severity=config.severity,
            log_traceback=config.log_traceback,
            raise_on_critical=config.raise_on_critical,
            fallback_function=config.fallback_function
        )
    
    return handle_service_errors(
        config=config,
        service_name="LLM",
        operation_name=operation_name
    )


def handle_memory_errors(operation_name: str = None):
    """Convenience decorator for memory operations."""
    return handle_service_errors(
        config=ServiceErrorConfigs.MEMORY,
        service_name="Memory",
        operation_name=operation_name
    )


def handle_cache_errors(operation_name: str = None):
    """Convenience decorator for cache operations."""
    return handle_service_errors(
        config=ServiceErrorConfigs.CACHE,
        service_name="Cache",
        operation_name=operation_name
    )


def handle_api_errors(operation_name: str = None):
    """Convenience decorator for API operations."""
    return handle_service_errors(
        config=ServiceErrorConfigs.API,
        service_name="API",
        operation_name=operation_name
    )
