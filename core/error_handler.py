"""
Error handling utilities for the FastAPI LLM backend.
Provides centralized error handling, logging, and user-friendly error responses.
"""

import logging
import time
import traceback
from typing import Any
from typing import Dict
from typing import Optional

import redis
from fastapi import HTTPException
from pydantic import BaseModel

from core.human_logging import log_service_status
from utilities.connection_factory import DatabaseConnectionFactory
from utilities.error_patterns import handle_service_errors, handle_database_errors, ErrorHandlerConfig

# --- Standalone Functions for Global Use ---


def log_error(error: Exception, context: str = "", user_id: str = "", request_id: str = "") -> None:
    """Log an error with context information."""
    error_details = {
        "error_type": type(error).__name__,
        "error_message": str(error),
        "context": context,
        "user_id": user_id,
        "request_id": request_id,
        "traceback": traceback.format_exc(),
    }
    logging.error("[ERROR] {context}: {error}", extra=error_details)


def get_user_friendly_message(error: Exception, context: str = "") -> str:
    """Get a user-friendly error message based on the error type."""
    error_type = type(error)
    error_str = str(error).lower()

    if isinstance(error, redis.RedisError):
        return "I'm having trouble with the caching service. Your request might be slower."
    if isinstance(error, HTTPException):
        return f"Web server issue (status code: {error.status_code}). Please check your request."

    if "chroma" in error_str or "memory" in context.lower():
        return (
            "I'm having trouble with my long-term memory. I can still help, but I might not remember our conversation."
        )
    if any(keyword in error_str for keyword in ["llm", "ollama", "model", "completion"]):
        return "The AI model is currently unavailable. Please try again in a moment."
    if any(keyword in error_str for keyword in ["tool", "search", "calculator"]):
        return "One of the tools I need is not working right now. I'll do my best to answer without it."

    error_map = {
        ConnectionError: "I'm having trouble connecting to a service. Please check your network.",
        TimeoutError: "The request took too long. Please try again.",
        ValueError: "The information you provided seems to be in the wrong format.",
        KeyError: "Some required information is missing from your request.",
        TypeError: "An internal type mismatch occurred. This has been logged for review.",
    }
    return error_map.get(error_type, "I encountered an unexpected issue. The details have been logged.")


# --- Error Response Model ---


class ErrorResponse(BaseModel):
    """Standard error response model."""

    error: bool = True
    message: str
    error_type: str
    details: Optional[str] = None
    request_id: Optional[str] = None


# --- Error Handler Classes (now using standalone functions) ---


class ErrorHandler:
    """Centralized error handling for creating standardized responses."""

    @staticmethod
    def create_error_response(
        error: Exception,
        context: str = "",
        user_id: str = "",
        request_id: str = "",
        include_details: bool = False) -> ErrorResponse:
        """Create a standardized error response."""
        log_error(error, context, user_id, request_id)
        user_message = get_user_friendly_message(error, context)

        response = ErrorResponse(message=user_message, error_type=type(error).__name__, request_id=request_id)

        if include_details:
            response.details = str(error)

        return response


class ChatErrorHandler:
    """Specialized error handler for chat endpoints."""

    @staticmethod
    def handle_chat_error(
        error: Exception, user_id: str, user_message: str = "", request_id: str = ""
    ) -> Dict[str, Any]:
        """Handle errors specifically in chat endpoints."""
        context = f"Chat endpoint for user {user_id}"
        if user_message:
            context += (
                f" with message: '{user_message[:100]}...'"
                if len(user_message) > 100
                else f" with message: '{user_message}'"
            )

        log_error(error, context, user_id, request_id)
        user_friendly_message = get_user_friendly_message(error, context)

        return {
            "response": user_friendly_message,
            "error": True,
            "error_type": type(error).__name__,
            "request_id": request_id,
        }


class ToolErrorHandler:
    """Specialized error handler for tool operations."""

    @staticmethod
    def handle_tool_error(
        error: Exception,
        tool_name: str,
        user_id: str = "",
        input_data: str = "",
        request_id: str = "") -> str:
        """Handle errors in tool operations and return fallback message."""
        context = f"Tool '{tool_name}' execution"
        if user_id:
            context += f" for user {user_id}"
        if input_data:
            context += (
                f" with input: '{input_data[:50]}...'" if len(input_data) > 50 else f" with input: '{input_data}'"
            )

        log_error(error, context, user_id, request_id)

        tool_fallbacks = {
            "web_search": "I couldn't perform the web search right now.",
            "calculator": "I couldn't perform the calculation. Please check your input.",
        }
        return tool_fallbacks.get(tool_name, f"The {tool_name} tool encountered an issue.")


class CacheErrorHandler:
    """
    DEPRECATED: Use @handle_cache_errors decorator from utilities.error_patterns instead.
    
    This class is maintained for backward compatibility only.
    For new code, use: @handle_cache_errors or @handle_service_errors
    """

    @staticmethod
    def handle_cache_error(
        error: Exception,
        operation: str,  # "get", "set", "delete"
        cache_key: str = "",
        user_id: str = "",
        request_id: str = "") -> None:
        """Handle cache errors gracefully without disrupting the main flow."""
        context = f"Cache {operation} operation for key: {cache_key}"
        logging.warning(f"[CACHE] Cache operation failed - continuing without cache: {error}")
        # Simple logging without decorator to avoid parameter conflicts


class MemoryErrorHandler:
    """
    DEPRECATED: Use @handle_memory_errors decorator from utilities.error_patterns instead.
    
    This class is maintained for backward compatibility only.
    For new code, use: @handle_memory_errors or @handle_service_errors
    """

    @staticmethod
    @handle_service_errors(
        operation_name="memory_operation",
        config=ErrorHandlerConfig(
            max_retries=1,
            log_traceback=True
        )
    )
    def handle_memory_error(
        error: Exception,
        operation: str,
        user_id: str = "",
        request_id: str = "") -> None:
        """Handle memory storage errors gracefully."""
        context = f"Memory {operation} operation for user: {user_id}"
        logging.warning(f"[MEMORY] Memory operation failed - continuing without persistent memory: {error}")
        # Error logging handled by decorator


class RedisConnectionHandler:
    """Handle Redis connection errors and retries using DatabaseConnectionFactory."""

    def __init__(self, max_retries: int = 3):
        self.max_retries = max_retries
        self.connection_factory = DatabaseConnectionFactory()

    def handle_connection_error(self, error: Exception) -> bool:
        """Handle Redis connection errors."""
        log_error(error, "Redis connection failed")
        return False

    async def retry_operation(self, operation, *args, **kwargs):
        """Retry Redis operations with exponential backoff using DatabaseConnectionFactory."""
        for attempt in range(self.max_retries):
            try:
                # Use DatabaseConnectionFactory for Redis connections
                redis_client = await self.connection_factory.create_redis_connection(connection_name=f"error_handler_retry_{attempt}")
                
                if not redis_client:
                    raise redis.RedisError("Failed to create Redis connection via DatabaseConnectionFactory")
                
                # Execute the operation with the factory-managed connection
                if callable(operation):
                    return await operation(redis_client, *args, **kwargs)
                else:
                    return redis_client
                    
            except redis.RedisError as e:
                if attempt == self.max_retries - 1:
                    log_service_status("ERROR_HANDLER", "error", f"Redis operation failed after {self.max_retries} attempts via DatabaseConnectionFactory: {e}")
                    raise e
                log_service_status("ERROR_HANDLER", "warning", f"Redis operation attempt {attempt + 1} failed, retrying: {e}")
                time.sleep(2 ** attempt)
        return None

    @handle_database_errors(
        operation_name="get_redis_connection"
    )
    async def get_redis_connection(self):
        """Get a Redis connection using DatabaseConnectionFactory."""
        redis_client = await self.connection_factory.create_redis_connection(connection_name="error_handler_connection")
        if redis_client:
            log_service_status("ERROR_HANDLER", "info", "Redis connection established via DatabaseConnectionFactory")
            return redis_client
        else:
            log_service_status("ERROR_HANDLER", "warning", "Failed to establish Redis connection via DatabaseConnectionFactory")
            return None


# --- Utility Functions ---


def safe_execute(func, *args, fallback_value=None, error_handler=None, **kwargs):
    """
    DEPRECATED: Use @handle_service_errors decorator from utilities.error_patterns instead.
    
    This function is maintained for backward compatibility only.
    For new code, use the standardized error handling decorators:
    - @handle_service_errors for general operations
    - @handle_database_errors for database operations  
    - @handle_api_errors for API operations
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        log_service_status("ERROR_HANDLER", "warning", f"DEPRECATED safe_execute used for {func.__name__}: {e}")
        if error_handler:
            error_handler(e)
        else:
            log_error(e, f"Error in deprecated safe_execute wrapper for {func.__name__}")
        return fallback_value


def with_error_handling(error_message="An error occurred"):
    """
    DEPRECATED: Use specific error decorators from utilities.error_patterns instead.
    
    This decorator is maintained for backward compatibility only.
    For new code, use the appropriate decorator:
    - @handle_service_errors for general operations
    - @handle_database_errors for database operations
    - @handle_api_errors for API operations
    - @handle_llm_errors for LLM operations
    """

    def decorator(func):
        """Wrapper decorator with deprecation notice."""
        def wrapper(*args, **kwargs):
            """Legacy wrapper with error handling."""
            try:
                return func(*args, **kwargs)
            except Exception as e:
                log_service_status("ERROR_HANDLER", "warning", f"DEPRECATED with_error_handling used for {func.__name__}: {e}")
                log_error(e, f"Error in deprecated decorator for {func.__name__}")
                return error_message
        return wrapper
    return decorator
