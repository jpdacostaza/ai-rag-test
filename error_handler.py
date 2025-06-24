"""
Error handling utilities for the FastAPI LLM backend.
Provides centralized error handling, logging, and user-friendly error responses.
"""

import logging
import traceback
from typing import Any
from typing import Dict
from typing import Optional

import redis
from fastapi import HTTPException
from pydantic import BaseModel

from human_logging import log_service_status

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
        return "I'm having trouble with my long-term memory. I can still help, but I might not remember our conversation."
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
    return error_map.get(
        error_type, "I encountered an unexpected issue. The details have been logged."
    )


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
        include_details: bool = False,
    ) -> ErrorResponse:
        """Create a standardized error response."""
        log_error(error, context, user_id, request_id)
        user_message = get_user_friendly_message(error, context)

        response = ErrorResponse(
            message=user_message, error_type=type(error).__name__, request_id=request_id
        )

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
        request_id: str = "",
    ) -> str:
        """Handle errors in tool operations and return fallback message."""
        context = f"Tool '{tool_name}' execution"
        if user_id:
            context += f" for user {user_id}"
        if input_data:
            context += (
                f" with input: '{input_data[:50]}...'"
                if len(input_data) > 50
                else f" with input: '{input_data}'"
            )

        log_error(error, context, user_id, request_id)

        tool_fallbacks = {
            "web_search": "I couldn't perform the web search right now.",
            "calculator": "I couldn't perform the calculation. Please check your input.",
        }
        return tool_fallbacks.get(tool_name, f"The {tool_name} tool encountered an issue.")


class CacheErrorHandler:
    """Specialized error handler for caching operations."""

    @staticmethod
    def handle_cache_error(
        error: Exception,
        operation: str,  # "get", "set", "delete"
        cache_key: str = "",
        user_id: str = "",
        request_id: str = "",
    ) -> None:
        """Handle cache errors gracefully without disrupting the main flow."""
        context = f"Cache {operation} operation for key: {cache_key}"
        log_error(error, context, user_id, request_id)
        logging.warning(f"[CACHE] Cache operation failed - continuing without cache: {error}")


class MemoryErrorHandler:
    """Specialized error handler for memory/ChromaDB operations."""

    @staticmethod
    def handle_memory_error(
        error: Exception,
        operation: str,
        user_id: str = "",
        request_id: str = "",  # "store", "retrieve", "index"
    ) -> None:
        """Handle memory storage errors gracefully."""
        context = f"Memory {operation} operation for user: {user_id}"
        log_error(error, context, user_id, request_id)
        logging.warning(
            f"[MEMORY] Memory operation failed - continuing without persistent memory: {error}"
        )


class RedisConnectionHandler:
    """Specialized error handler for Redis connection issues."""

    @staticmethod
    def handle_redis_error(
        error: Exception,
        operation: str,  # "connect", "get", "set", "ping"
        key: str = "",
        user_id: str = "",
        request_id: str = "",
    ) -> None:
        """Handle Redis connection errors gracefully."""
        context = "Redis {operation} operation"
        if key:
            context += " for key: {key}"

        log_error(error, context, user_id, request_id)

        if RedisConnectionHandler.is_recoverable_error(error):
            logging.warning(
                "[REDIS] Connection issue detected - system will continue with degraded caching."
            )
        else:
            logging.warning("[REDIS] Operation failed but system continues: {error}")

    @staticmethod
    def is_recoverable_error(error: Exception) -> bool:
        """Check if a Redis error is recoverable (connection-related)."""
        error_str = str(error).lower()
        recoverable_keywords = [
            "connection",
            "timeout",
            "refused",
            "unreachable",
            "broken pipe",
            "connection reset",
            "socket",
            "network",
            "errno 32",
            "connection lost",
        ]
        return any(keyword in error_str for keyword in recoverable_keywords)


# --- Utility Functions ---


def safe_execute(func, *args, fallback_value=None, error_handler=None, **kwargs):
    """
    Safely execute a function and handle errors gracefully.
    Returns function result or fallback_value if an error occurs.
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        log_service_status('ERROR_HANDLER', 'error', f'Error in safe_execute for {func.__name__}: {e}')
        if error_handler:
            error_handler(e)
        else:
            log_error(e, f"Error in safe_execute wrapper for {func.__name__}")
        return fallback_value


def with_error_handling(error_message="An error occurred"):
    """Decorator for adding basic error handling to functions."""

    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                log_service_status('ERROR_HANDLER', 'error', f'Error in decorator for {func.__name__}: {e}')
                log_error(e, f"Error in decorator for {func.__name__}")
                return error_message

        return wrapper

    return decorator
