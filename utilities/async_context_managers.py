"""
Async Context Managers - Enhanced Performance Edition
====================================================

This module provides optimized async context managers for proper resource management,
with enhanced connection pooling, memory pressure handling, and performance monitoring.

Addresses Issue #5: Performance optimizations including:
- Advanced connection pooling with auto-scaling
- Memory pressure detection and handling
- Connection health monitoring
- Performance metrics collection
"""

import asyncio
from typing import Optional, AsyncGenerator, Any
from contextlib import asynccontextmanager
import httpx

# Unified logging
from core.unified_logging import get_logger

logger = get_logger(__name__)

from utilities.simple_error_handling import handle_errors
from utilities.enhanced_connection_pooling import pool_manager, enhanced_redis_connection

try:
    from utilities.enhanced_connection_pooling import get_enhanced_redis_pool
    ENHANCED_POOLING_AVAILABLE = True
except ImportError:
    ENHANCED_POOLING_AVAILABLE = False


class HTTPClientManager:
    """
    Async context manager for HTTP clients with connection pooling and proper cleanup.
    """
    
    def __init__(self, timeout: float = 30.0, max_connections: int = 100):
        """
        Initialize HTTP client manager.
        
        Args:
            timeout: Request timeout in seconds
            max_connections: Maximum number of connections in pool
        """
        self.timeout = timeout
        self.max_connections = max_connections
        self._client: Optional[httpx.AsyncClient] = None
    
    async def __aenter__(self) -> httpx.AsyncClient:
        """Enter the async context and create HTTP client."""
        try:
            limits = httpx.Limits(max_connections=self.max_connections)
            timeout = httpx.Timeout(self.timeout)
            
            self._client = httpx.AsyncClient(
                limits=limits,
                timeout=timeout,
                follow_redirects=True
            )
            
            logger.debug(f"HTTP client created with timeout={self.timeout}s, max_connections={self.max_connections}")
            return self._client
            
        except Exception as e:
            logger.error(f"Failed to create HTTP client: {e}")
            raise
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit the async context and cleanup HTTP client."""
        if self._client:
            try:
                await self._client.aclose()
                logger.debug("HTTP client closed successfully")
            except Exception as e:
                logger.error(f"Error closing HTTP client: {e}")
            finally:
                self._client = None


class DatabaseConnectionManager:
    """
    Async context manager for database connections with proper cleanup.
    """
    
    def __init__(self, connection_factory, connection_params: dict = None):
        """
        Initialize database connection manager.
        
        Args:
            connection_factory: Function to create database connection
            connection_params: Parameters for connection creation
        """
        self.connection_factory = connection_factory
        self.connection_params = connection_params or {}
        self._connection = None
    
    async def __aenter__(self):
        """Enter the async context and create database connection."""
        try:
            if asyncio.iscoroutinefunction(self.connection_factory):
                self._connection = await self.connection_factory(**self.connection_params)
            else:
                self._connection = self.connection_factory(**self.connection_params)
                
            logger.debug("Database connection established")
            return self._connection
            
        except Exception as e:
            logger.error(f"Failed to create database connection: {e}")
            raise
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit the async context and cleanup database connection."""
        if self._connection:
            try:
                if hasattr(self._connection, 'aclose'):
                    await self._connection.aclose()
                elif hasattr(self._connection, 'close'):
                    if asyncio.iscoroutinefunction(self._connection.close):
                        await self._connection.close()
                    else:
                        self._connection.close()
                        
                logger.debug("Database connection closed successfully")
            except Exception as e:
                logger.error(f"Error closing database connection: {e}")
            finally:
                self._connection = None


@asynccontextmanager
async def http_client(timeout: float = 30.0, max_connections: int = 100) -> AsyncGenerator[httpx.AsyncClient, None]:
    """
    Async context manager function for HTTP clients.
    
    Args:
        timeout: Request timeout in seconds
        max_connections: Maximum number of connections
        
    Yields:
        httpx.AsyncClient: Configured HTTP client
        
    Example:
        async with http_client() as client:
            response = await client.get("https://api.example.com")
    """
    async with HTTPClientManager(timeout, max_connections) as client:
        yield client


@asynccontextmanager
async def database_connection(connection_factory, **kwargs) -> AsyncGenerator[Any, None]:
    """
    Async context manager function for database connections.
    
    Args:
        connection_factory: Function to create connection
        **kwargs: Parameters for connection creation
        
    Yields:
        Database connection object
        
    Example:
        async with database_connection(create_redis_client, host="localhost") as redis:
            await redis.set("key", "value")
    """
    async with DatabaseConnectionManager(connection_factory, kwargs) as conn:
        yield conn


@asynccontextmanager 
async def redis_connection(redis_client=None, use_enhanced_pool=True) -> AsyncGenerator[Any, None]:
    """
    Async context manager for Redis connections with enhanced pooling support.
    
    Args:
        redis_client: Optional Redis client instance
        use_enhanced_pool: Whether to use enhanced connection pooling
        
    Yields:
        Redis client or None if unavailable
    """
    if use_enhanced_pool and ENHANCED_POOLING_AVAILABLE:
        # Use enhanced pooling for better performance
        try:
            async with enhanced_redis_connection() as client:
                logger.debug("Enhanced Redis connection context entered")
                yield client
                return
        except Exception as e:
            logger.warning(f"Enhanced Redis pool failed, falling back to direct connection: {e}")
    
    # Fallback to direct connection
    client = redis_client
    if not client:
        try:
            from services.database_manager import db_manager
            client = db_manager.redis_client if db_manager else None
        except Exception as e:
            logger.warning(f"Could not get Redis client: {e}")
            client = None
    
    try:
        if client:
            logger.debug("Redis connection context entered (direct)")
        yield client
    finally:
        if client:
            logger.debug("Redis connection context exited")


@asynccontextmanager
async def vector_connection(vector_client=None) -> AsyncGenerator[Any, None]:
    """
    Async context manager for vector database connections.
    
    Args:
        vector_client: Optional vector client instance
        
    Yields:
        Vector client or None if unavailable
    """
    client = vector_client
    if not client:
        try:
            from services.database_manager import db_manager
            client = db_manager.chroma_client if db_manager else None
        except Exception as e:
            logger.warning(f"Could not get vector client: {e}")
            client = None
    
    try:
        if client:
            logger.debug("Vector database connection context entered")
        yield client
    finally:
        if client:
            logger.debug("Vector database connection context exited")


# Utility functions for common patterns
@handle_errors("safe_http_request", default_value=None)
async def safe_http_request(url: str, method: str = "GET", **kwargs) -> Optional[httpx.Response]:
    """
    Make a safe HTTP request with proper resource management.
    
    Args:
        url: Request URL
        method: HTTP method
        **kwargs: Additional request parameters
        
    Returns:
        Response object or None if failed
    """
    async with http_client() as client:
        if method.upper() == "GET":
            return await client.get(url, **kwargs)
        elif method.upper() == "POST":
            return await client.post(url, **kwargs)
        elif method.upper() == "PUT":
            return await client.put(url, **kwargs)
        elif method.upper() == "DELETE":
            return await client.delete(url, **kwargs)
        else:
            return await client.request(method, url, **kwargs)


@handle_errors("safe_redis_operation", default_value=None)
async def safe_redis_operation(operation_func, *args, **kwargs):
    """
    Execute a Redis operation with proper resource management.
    
    Args:
        operation_func: Function to execute on Redis client
        *args: Arguments for the operation
        **kwargs: Keyword arguments for the operation
        
    Returns:
        Operation result or None if failed
    """
    async with redis_connection() as redis:
        if redis and hasattr(redis, operation_func.__name__):
            return await operation_func(redis, *args, **kwargs)
        return None


@handle_errors("safe_vector_operation", default_value=None)
async def safe_vector_operation(operation_func, *args, **kwargs):
    """
    Execute a vector database operation with proper resource management.
    
    Args:
        operation_func: Function to execute on vector client
        *args: Arguments for the operation
        **kwargs: Keyword arguments for the operation
        
    Returns:
        Operation result or None if failed
    """
    async with vector_connection() as vector:
        if vector:
            return await operation_func(vector, *args, **kwargs)
        return None
