"""
Simplified Error Handling
========================

This module provides simple, easy-to-use error handling decorators
that replace the over-engineered error_patterns.py system.

Key principles:
- Simple to use and understand
- Consistent error logging
- Graceful degradation
- No complex configuration objects
"""

import functools
import logging
from typing import Any, Callable, Optional, TypeVar

from fastapi import HTTPException

# Type variable for decorated functions
F = TypeVar('F', bound=Callable[..., Any])

logger = logging.getLogger(__name__)


def handle_errors(operation: str, default_value: Any = None, raise_http: bool = False):
    """
    Simple error handling decorator for any function or method.
    
    Args:
        operation: Name of the operation being performed (for logging)
        default_value: Value to return if function fails (None by default)
        raise_http: Whether to raise HTTPException for API endpoints
    
    Example:
        @handle_errors("get_user_memories", default_value=[])
        async def get_user_memories(user_id: str) -> List[Memory]:
            # Function implementation
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                logger.error(f"{operation} failed: {e}", exc_info=True)
                if raise_http:
                    raise HTTPException(status_code=500, detail=f"{operation} failed: {str(e)}")
                return default_value
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(f"{operation} failed: {e}", exc_info=True)
                if raise_http:
                    raise HTTPException(status_code=500, detail=f"{operation} failed: {str(e)}")
                return default_value
        
        # Return appropriate wrapper based on whether function is async
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def handle_api_errors(operation: str):
    """
    Simple error handling decorator specifically for API endpoints.
    Automatically raises HTTPException with appropriate status codes.
    
    Args:
        operation: Name of the API operation (for logging and error messages)
    
    Example:
        @handle_api_errors("chat_endpoint")
        async def chat_endpoint(request: ChatRequest) -> ChatResponse:
            # API implementation
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except HTTPException:
                # Re-raise HTTP exceptions as-is
                raise
            except ValueError as e:
                logger.error(f"{operation} validation error: {e}", exc_info=True)
                raise HTTPException(status_code=400, detail=str(e))
            except Exception as e:
                logger.error(f"{operation} failed: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=f"Internal server error in {operation}")
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except HTTPException:
                # Re-raise HTTP exceptions as-is
                raise
            except ValueError as e:
                logger.error(f"{operation} validation error: {e}", exc_info=True)
                raise HTTPException(status_code=400, detail=str(e))
            except Exception as e:
                logger.error(f"{operation} failed: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=f"Internal server error in {operation}")
        
        # Return appropriate wrapper based on whether function is async
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


# Convenience decorators for common patterns
def handle_database_errors(operation: str = "database_operation", default_value: Any = None):
    """Convenience decorator for database operations."""
    return handle_errors(f"Database {operation}", default_value=default_value)


def handle_llm_errors(operation: str = "llm_operation", fallback_message: str = "I'm having trouble processing your request right now."):
    """Convenience decorator for LLM operations."""
    return handle_errors(f"LLM {operation}", default_value=fallback_message)


def handle_memory_errors(operation: str = "memory_operation"):
    """Convenience decorator for memory operations."""
    return handle_errors(f"Memory {operation}", default_value=[])


def handle_cache_errors(operation: str = "cache_operation"):
    """Convenience decorator for cache operations."""
    return handle_errors(f"Cache {operation}", default_value=None)


# Add asyncio import
import asyncio
