"""
Database Connection Factory - Unified Connection Management

This module provides a centralized factory for creating and managing database connections
with consistent error handling, retry logic, and health monitoring.

Addresses Code Duplication Issue #3A: Database Connection Patterns
- Eliminates 8+ duplicated connection initialization patterns
- Provides unified error handling and retry logic
- Standardizes connection configuration across all services
"""

import asyncio
import os
import time
from typing import Optional, Dict, Any, Union, Protocol, cast, TYPE_CHECKING
from dataclasses import dataclass
from contextlib import asynccontextmanager

# Unified logging
from core.unified_logging import get_logger

logger = get_logger(__name__)

# Type checking imports
if TYPE_CHECKING:
    import redis.asyncio as redis_type
    import chromadb as chromadb_type
else:
    redis_type = Any
    chromadb_type = Any

# Database client imports with improved error handling
from utilities.feature_registry import feature_registry, register_import_attempt

# Register database dependencies
REDIS_AVAILABLE = register_import_attempt(
    "redis_client",
    lambda: __import__("redis.asyncio", fromlist=["Redis"]),
    "Redis async client for caching and session management"
)

CHROMADB_AVAILABLE = register_import_attempt(
    "chromadb_client", 
    lambda: __import__("chromadb"),
    "ChromaDB client for vector storage and similarity search"
)

# Import clients if available
if REDIS_AVAILABLE:
    import redis.asyncio as redis
else:
    redis = None
    
if CHROMADB_AVAILABLE:
    import chromadb
    from chromadb.config import Settings as ChromaSettings
else:
    chromadb = None
    ChromaSettings = None

from config.config_unified import Config


@dataclass
class ConnectionConfig:
    """Configuration for database connections."""
    host: str
    port: int
    timeout: float = 30.0
    max_retries: int = 3
    retry_delay: float = 2.0
    health_check_interval: float = 60.0


@dataclass
class RedisConfig(ConnectionConfig):
    """Redis-specific connection configuration."""
    db: int = 0
    password: Optional[str] = None
    decode_responses: bool = True
    retry_on_timeout: bool = True
    socket_keepalive: bool = True
    socket_keepalive_options: Dict[str, int] = None

    def __post_init__(self):
        if self.socket_keepalive_options is None:
            self.socket_keepalive_options = {1: 1, 2: 3, 3: 5}


@dataclass 
class ChromaConfig(ConnectionConfig):
    """ChromaDB-specific connection configuration."""
    collection_name: str = "default"
    persist_directory: Optional[str] = None
    anonymized_telemetry: bool = False


class ConnectionHealth:
    """Track connection health and status."""
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.is_healthy = False
        self.last_check = 0.0
        self.failure_count = 0
        self.last_error: Optional[str] = None
        self.connection_time: Optional[float] = None

    def mark_healthy(self, connection_time: float = None):
        """Mark connection as healthy."""
        self.is_healthy = True
        self.last_check = time.time()
        self.failure_count = 0
        self.last_error = None
        if connection_time:
            self.connection_time = connection_time

    def mark_unhealthy(self, error: str):
        """Mark connection as unhealthy."""
        self.is_healthy = False
        self.last_check = time.time()
        self.failure_count += 1
        self.last_error = error

    def should_retry(self, max_failures: int = 5) -> bool:
        """Check if connection should be retried."""
        return self.failure_count < max_failures


class DatabaseConnectionFactory:
    """
    Centralized factory for creating and managing database connections.
    
    Features:
    - Unified connection creation with consistent error handling
    - Automatic retry logic with exponential backoff
    - Health monitoring and status tracking
    - Connection pooling and lifecycle management
    - Configuration-driven setup
    """
    
    def __init__(self):
        self.config = Config.get_instance()
        self._connections: Dict[str, Any] = {}
        self._health_status: Dict[str, ConnectionHealth] = {}
        self._locks: Dict[str, asyncio.Lock] = {}
        
    def _get_lock(self, service_name: str) -> asyncio.Lock:
        """Get or create lock for service."""
        if service_name not in self._locks:
            self._locks[service_name] = asyncio.Lock()
        return self._locks[service_name]

    def _get_health(self, service_name: str) -> ConnectionHealth:
        """Get or create health tracker for service."""
        if service_name not in self._health_status:
            self._health_status[service_name] = ConnectionHealth(service_name)
        return self._health_status[service_name]

    def _log_status(self, service: str, level: str, message: str):
        """Unified logging for connection status."""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] [CONNECTION_FACTORY] [{service.upper()}] {message}"
        
        if level == "info":
            logger.info(log_message)
        elif level == "warning":
            logger.warning(log_message)
        elif level == "error":
            logger.error(log_message)
        else:
            logger.debug(log_message)

    async def create_redis_connection(
        self,
        config_override: Optional[RedisConfig] = None,
        connection_name: str = "default"
    ) -> Optional[Any]:
        """
        Create Redis connection with unified error handling and retry logic.
        
        Args:
            config_override: Optional custom configuration
            connection_name: Unique name for this connection
            
        Returns:
            Redis client or None if connection fails
        """
        if redis is None:
            self._log_status("redis", "error", "Redis library not available")
            return None

        # Use provided config or create from environment
        if config_override:
            redis_config = config_override
        else:
            # Get password and convert empty string to None (Redis auth issue)
            password = getattr(self.config.database, 'redis_password', None)
            if password == '':
                password = None
                
            redis_config = RedisConfig(
                host=self.config.database.redis_host,
                port=self.config.database.redis_port,
                password=password,
                timeout=self.config.service.api_timeout,
                max_retries=3,
                retry_delay=2.0
            )

        health = self._get_health(f"redis_{connection_name}")
        
        if not health.should_retry():
            self._log_status("redis", "warning", f"Max failures reached for {connection_name}")
            return None

        async with self._get_lock(f"redis_{connection_name}"):
            for attempt in range(redis_config.max_retries):
                try:
                    start_time = time.time()
                    
                    # Create async Redis client with simplified configuration
                    client = redis.Redis(
                        host=redis_config.host,
                        port=redis_config.port,
                        db=redis_config.db,
                        password=redis_config.password,  # Already None if empty
                        decode_responses=redis_config.decode_responses,
                        socket_connect_timeout=redis_config.timeout,
                        socket_timeout=redis_config.timeout
                    )
                    
                    # Test connection
                    await client.ping()
                    
                    connection_time = time.time() - start_time
                    health.mark_healthy(connection_time)
                    
                    self._log_status(
                        "redis", 
                        "info", 
                        f"Connected successfully to {redis_config.host}:{redis_config.port} "
                        f"(connection_time: {connection_time:.3f}s)"
                    )
                    
                    # Store connection for reuse
                    self._connections[f"redis_{connection_name}"] = client
                    return client
                    
                except Exception as e:
                    error_msg = f"Connection attempt {attempt + 1}/{redis_config.max_retries} failed: {str(e)}"
                    health.mark_unhealthy(error_msg)
                    self._log_status("redis", "warning", error_msg)
                    
                    if attempt < redis_config.max_retries - 1:
                        await asyncio.sleep(redis_config.retry_delay * (2 ** attempt))  # Exponential backoff

        self._log_status("redis", "error", f"All connection attempts failed for {connection_name}")
        return None

    async def create_chroma_connection(
        self,
        config_override: Optional[ChromaConfig] = None,
        connection_name: str = "default"
    ) -> Optional[Any]:
        """
        Create ChromaDB connection with unified error handling and retry logic.
        
        Args:
            config_override: Optional custom configuration
            connection_name: Unique name for this connection
            
        Returns:
            ChromaDB client or None if connection fails
        """
        if chromadb is None:
            self._log_status("chromadb", "error", "ChromaDB library not available")
            return None

        # Use provided config or create from environment
        if config_override:
            chroma_config = config_override
        else:
            chroma_config = ChromaConfig(
                host=self.config.database.chroma_host,
                port=self.config.database.chroma_port,
                collection_name=getattr(self.config.database, 'chroma_collection', 'default'),
                persist_directory=getattr(self.config.database, 'chroma_persist_dir', None),
                timeout=self.config.service.api_timeout,
                max_retries=3,
                retry_delay=2.0
            )

        health = self._get_health(f"chroma_{connection_name}")
        
        if not health.should_retry():
            self._log_status("chromadb", "warning", f"Max failures reached for {connection_name}")
            return None

        async with self._get_lock(f"chroma_{connection_name}"):
            for attempt in range(chroma_config.max_retries):
                try:
                    start_time = time.time()
                    
                    # Create ChromaDB settings
                    if chroma_config.persist_directory:
                        settings = ChromaSettings(
                            chroma_server_host=chroma_config.host,
                            chroma_server_http_port=str(chroma_config.port),
                            persist_directory=chroma_config.persist_directory,
                            anonymized_telemetry=chroma_config.anonymized_telemetry)
                    else:
                        settings = ChromaSettings(
                            chroma_server_host=chroma_config.host,
                            chroma_server_http_port=str(chroma_config.port),
                            anonymized_telemetry=chroma_config.anonymized_telemetry)
                    
                    # Create client
                    client = chromadb.Client(settings)
                    
                    # Test connection
                    client.heartbeat()
                    
                    connection_time = time.time() - start_time
                    health.mark_healthy(connection_time)
                    
                    self._log_status(
                        "chromadb", 
                        "info", 
                        f"Connected successfully to {chroma_config.host}:{chroma_config.port} "
                        f"(connection_time: {connection_time:.3f}s)"
                    )
                    
                    # Store connection for reuse
                    self._connections[f"chroma_{connection_name}"] = client
                    return client
                    
                except Exception as e:
                    error_msg = f"Connection attempt {attempt + 1}/{chroma_config.max_retries} failed: {str(e)}"
                    health.mark_unhealthy(error_msg)
                    self._log_status("chromadb", "warning", error_msg)
                    
                    if attempt < chroma_config.max_retries - 1:
                        await asyncio.sleep(chroma_config.retry_delay * (2 ** attempt))  # Exponential backoff

        self._log_status("chromadb", "error", f"All connection attempts failed for {connection_name}")
        return None

    @asynccontextmanager
    async def get_redis_connection(self, connection_name: str = "default"):
        """
        Context manager for Redis connections with automatic cleanup.
        
        Usage:
            async with factory.get_redis_connection() as redis_client:
                await redis_client.set("key", "value")
        """
        client = None
        try:
            if f"redis_{connection_name}" in self._connections:
                client = self._connections[f"redis_{connection_name}"]
            else:
                client = await self.create_redis_connection(connection_name=connection_name)
            
            if client:
                yield client
            else:
                raise ConnectionError(f"Could not establish Redis connection: {connection_name}")
        finally:
            # Connections are pooled, so we don't close them here
            pass

    @asynccontextmanager
    async def get_chroma_connection(self, connection_name: str = "default"):
        """
        Context manager for ChromaDB connections with automatic cleanup.
        
        Usage:
            async with factory.get_chroma_connection() as chroma_client:
                collection = chroma_client.get_collection("my_collection")
        """
        client = None
        try:
            if f"chroma_{connection_name}" in self._connections:
                client = self._connections[f"chroma_{connection_name}"]
            else:
                client = await self.create_chroma_connection(connection_name=connection_name)
            
            if client:
                yield client
            else:
                raise ConnectionError(f"Could not establish ChromaDB connection: {connection_name}")
        finally:
            # Connections are managed by the factory
            pass

    def get_health_status(self) -> Dict[str, Dict[str, Any]]:
        """Get health status for all connections."""
        status = {}
        for name, health in self._health_status.items():
            status[name] = {
                "healthy": health.is_healthy,
                "last_check": health.last_check,
                "failure_count": health.failure_count,
                "last_error": health.last_error,
                "connection_time": health.connection_time
            }
        return status

    async def cleanup_connections(self):
        """Clean up all managed connections."""
        for name, connection in self._connections.items():
            try:
                if "redis" in name and hasattr(connection, 'close'):
                    await connection.close()
                elif "chroma" in name:
                    # ChromaDB connections don't need explicit cleanup
                    pass
                self._log_status("cleanup", "info", f"Cleaned up connection: {name}")
            except Exception as e:
                self._log_status("cleanup", "warning", f"Error cleaning up {name}: {e}")
        
        self._connections.clear()
        self._health_status.clear()


# Global factory instance
connection_factory = DatabaseConnectionFactory()


def get_connection_factory() -> DatabaseConnectionFactory:
    """Get the global connection factory instance."""
    return connection_factory


# Convenience functions for backward compatibility
async def create_redis_connection(connection_name: str = "default") -> Optional[Any]:
    """Create Redis connection using the factory."""
    return await connection_factory.create_redis_connection(connection_name=connection_name)


async def create_chroma_connection(connection_name: str = "default") -> Optional[Any]:
    """Create ChromaDB connection using the factory."""
    return await connection_factory.create_chroma_connection(connection_name=connection_name)


# Context managers for easy usage
get_redis = connection_factory.get_redis_connection
get_chroma = connection_factory.get_chroma_connection
