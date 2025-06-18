"""
Error handling utilities for the FastAPI LLM backend.
Provides centralized error handling, logging, and user-friendly error responses.
"""

import logging
import traceback
from typing import Optional, Dict, Any
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

class ErrorResponse(BaseModel):
    """Standard error response model."""
    error: bool = True
    message: str
    error_type: str
    details: Optional[str] = None
    request_id: Optional[str] = None

class ErrorHandler:
    """Centralized error handling for the FastAPI backend."""
    
    @staticmethod
    def log_error(error: Exception, context: str = "", user_id: str = "", request_id: str = "") -> None:
        """Log an error with context information."""
        error_details = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context,
            "user_id": user_id,
            "request_id": request_id,
            "traceback": traceback.format_exc()
        }
        
        logging.error(f"[ERROR] {context}: {error}", extra=error_details)
    
    @staticmethod
    def get_user_friendly_message(error: Exception, context: str = "") -> str:
        """Get a user-friendly error message based on the error type."""
        error_type = type(error).__name__
        
        # Map specific error types to user-friendly messages
        error_messages = {
            "ConnectionError": "I'm having trouble connecting to external services. Please try again in a moment.",
            "TimeoutError": "The request took too long to process. Please try again.",
            "HTTPException": "There was an issue with the request. Please check your input and try again.",
            "ValidationError": "The input format is not valid. Please check your request and try again.",
            "KeyError": "Some required information is missing. Please check your request.",
            "ValueError": "Invalid input provided. Please check your data and try again.",
            "TypeError": "There was an issue processing your request. Please try again.",
            "RedisConnectionError": "Caching service is temporarily unavailable, but your request is still being processed.",
            "ChromaDBError": "Memory service is temporarily unavailable, but your request is still being processed.",
            "LLMError": "The AI service is temporarily unavailable. Please try again in a moment.",
            "ToolError": "One of the tools encountered an issue, but I'll try to help you anyway."
        }
        
        # Check for specific error patterns
        if "redis" in str(error).lower():
            return error_messages.get("RedisConnectionError", "Caching service issue.")
        elif "chroma" in str(error).lower():
            return error_messages.get("ChromaDBError", "Memory service issue.")
        elif any(keyword in str(error).lower() for keyword in ["llm", "ollama", "model", "completion"]):
            return error_messages.get("LLMError", "AI service issue.")
        elif any(keyword in str(error).lower() for keyword in ["tool", "search", "weather", "calculator"]):
            return error_messages.get("ToolError", "Tool service issue.")
        
        # Return specific message if available, otherwise generic
        return error_messages.get(error_type, "I encountered an unexpected issue. Please try again.")
    
    @staticmethod
    def create_error_response(
        error: Exception, 
        context: str = "", 
        user_id: str = "", 
        request_id: str = "",
        include_details: bool = False
    ) -> ErrorResponse:
        """Create a standardized error response."""
        
        # Log the error
        ErrorHandler.log_error(error, context, user_id, request_id)
        
        # Get user-friendly message
        user_message = ErrorHandler.get_user_friendly_message(error, context)
        
        # Create response
        response = ErrorResponse(
            message=user_message,
            error_type=type(error).__name__,
            request_id=request_id
        )
        
        # Include technical details only if requested (for debugging)
        if include_details:
            response.details = str(error)
        
        return response

class ChatErrorHandler:
    """Specialized error handler for chat endpoints."""
    
    @staticmethod
    def handle_chat_error(
        error: Exception, 
        user_id: str, 
        user_message: str = "",
        request_id: str = ""
    ) -> Dict[str, Any]:
        """Handle errors specifically in chat endpoints."""
        
        context = f"Chat endpoint for user {user_id}"
        if user_message:
            context += f" with message: '{user_message[:100]}...'" if len(user_message) > 100 else f" with message: '{user_message}'"
        
        # Log the error
        ErrorHandler.log_error(error, context, user_id, request_id)
        
        # Return a chat-specific response
        user_friendly_message = ErrorHandler.get_user_friendly_message(error, context)
        
        return {
            "response": user_friendly_message,
            "error": True,
            "error_type": type(error).__name__,
            "request_id": request_id
        }

class ToolErrorHandler:
    """Specialized error handler for tool operations."""
    
    @staticmethod
    def handle_tool_error(
        error: Exception,
        tool_name: str,
        user_id: str = "",
        input_data: str = "",
        request_id: str = ""
    ) -> str:
        """Handle errors in tool operations and return fallback message."""
        
        context = f"Tool '{tool_name}' execution"
        if user_id:
            context += f" for user {user_id}"
        if input_data:
            context += f" with input: '{input_data[:50]}...'" if len(input_data) > 50 else f" with input: '{input_data}'"
        
        # Log the error
        ErrorHandler.log_error(error, context, user_id, request_id)
        
        # Tool-specific fallback messages
        tool_fallbacks = {
            "weather": "I couldn't fetch the weather information right now. Please try again later.",
            "web_search": "I couldn't perform the web search right now. Please try again later.",
            "calculator": "I couldn't perform the calculation right now. Please check your input and try again.",
            "unit_conversion": "I couldn't perform the unit conversion right now. Please check your input and try again.",
            "time": "I couldn't get the current time right now. Please try again later.",
            "news": "I couldn't fetch the latest news right now. Please try again later.",
            "exchange_rate": "I couldn't get the exchange rate right now. Please try again later.",
            "system_info": "I couldn't get the system information right now. Please try again later.",
            "python_code_execution": "I couldn't execute the Python code right now. Please check your code and try again.",
            "wikipedia": "I couldn't search Wikipedia right now. Please try again later.",
            "geo_timezone": "I couldn't get the timezone information right now. Please try again later."
        }
        
        return tool_fallbacks.get(tool_name, f"The {tool_name} tool encountered an issue. Please try again later.")

class CacheErrorHandler:
    """Specialized error handler for caching operations."""
    
    @staticmethod
    def handle_cache_error(
        error: Exception,
        operation: str,  # "get", "set", "delete"
        cache_key: str = "",
        user_id: str = "",
        request_id: str = ""
    ) -> None:
        """Handle cache errors gracefully without disrupting the main flow."""
        
        context = f"Cache {operation} operation"
        if cache_key:
            context += f" for key: {cache_key}"
        if user_id:
            context += f" (user: {user_id})"
        
        # Log but don't raise - cache errors should not break the main functionality
        ErrorHandler.log_error(error, context, user_id, request_id)
        
        # Log a warning that the cache is degraded
        logging.warning(f"[CACHE] Cache operation failed - continuing without cache: {error}")

class MemoryErrorHandler:
    """Specialized error handler for memory/ChromaDB operations."""
    
    @staticmethod
    def handle_memory_error(
        error: Exception,
        operation: str,  # "store", "retrieve", "index"
        user_id: str = "",
        request_id: str = ""
    ) -> None:
        """Handle memory storage errors gracefully."""
        
        context = f"Memory {operation} operation"
        if user_id:
            context += f" for user: {user_id}"
        
        # Log but don't raise - memory errors should not break the main functionality
        ErrorHandler.log_error(error, context, user_id, request_id)
        
        # Log a warning that memory is degraded
        logging.warning(f"[MEMORY] Memory operation failed - continuing without persistent memory: {error}")

class RedisConnectionHandler:
    """Specialized error handler for Redis connection issues."""
    
    @staticmethod
    def handle_redis_error(
        error: Exception,
        operation: str,  # "connect", "get", "set", "ping"
        key: str = "",
        user_id: str = "",
        request_id: str = ""
    ) -> None:
        """Handle Redis connection errors gracefully."""
        
        context = f"Redis {operation} operation"
        if key:
            context += f" for key: {key}"
        if user_id:
            context += f" (user: {user_id})"
        
        # Log the Redis-specific error
        ErrorHandler.log_error(error, context, user_id, request_id)
        
        # Check if it's a connection-related error that might be recoverable
        error_str = str(error).lower()
        is_connection_error = any(keyword in error_str for keyword in [
            "connection", "timeout", "refused", "unreachable", "broken pipe", 
            "connection reset", "socket", "network", "errno 32"
        ])
        
        if is_connection_error:
            if "broken pipe" in error_str or "errno 32" in error_str:
                logging.warning("[REDIS] Broken pipe detected - connection lost, automatic reconnection will be attempted")
            else:
                logging.warning("[REDIS] Connection issue detected - system will continue with degraded caching")
        else:
            logging.warning(f"[REDIS] Operation failed but system continues: {error}")
    
    @staticmethod
    def is_recoverable_error(error: Exception) -> bool:
        """Check if a Redis error is recoverable (connection-related)."""
        error_str = str(error).lower()
        recoverable_keywords = [
            "connection", "timeout", "refused", "unreachable", "broken pipe",
            "connection reset", "socket", "network", "errno 32", "connection lost"
        ]
        return any(keyword in error_str for keyword in recoverable_keywords)

# Utility functions for common error scenarios
def safe_execute(func, *args, fallback_value=None, error_handler=None, **kwargs):
    """
    Safely execute a function and handle errors gracefully.
    
    Args:
        func: Function to execute
        *args: Arguments for the function
        fallback_value: Value to return if function fails
        error_handler: Custom error handler function
        **kwargs: Keyword arguments for the function
    
    Returns:
        Function result or fallback_value if error occurs
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        if error_handler:
            error_handler(e)
        else:
            logging.error(f"[SAFE_EXECUTE] Error in {func.__name__}: {e}")
        return fallback_value

def with_error_handling(error_message="An error occurred"):
    """
    Decorator for adding error handling to functions.
    
    Args:
        error_message: Default error message to return
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logging.error(f"[ERROR_DECORATOR] Error in {func.__name__}: {e}")
                return error_message
        return wrapper
    return decorator
