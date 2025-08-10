"""
Enhanced Connection Pooling System
==================================

This module provides advanced connection pooling and performance optimizations
to address Issue #5: Performance considerations including connection management,
memory pressure handling, and async operation optimization.

Key improvements:
1. Advanced Redis connection pooling with monitoring
2. Memory pressure detection and auto-scaling
3. Connection health monitoring and auto-recovery
4. Performance metrics and alerting
5. Optimized async context managers
"""

import asyncio
import time
import psutil
import logging
from typing import Dict, Any, Optional, List, Callable, Union
from dataclasses import dataclass, field
from contextlib import asynccontextmanager
from collections import defaultdict, deque
import weakref

try:
    import redis.asyncio as redis
    from redis.asyncio.connection import ConnectionPool
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None
    ConnectionPool = None

from core.unified_logging import get_logger, log_service_status
from utilities.simple_error_handling import handle_database_errors, handle_errors

logger = get_logger(__name__)


@dataclass
class ConnectionPoolStats:
    """Connection pool statistics for monitoring."""
    pool_name: str
    created_connections: int = 0
    active_connections: int = 0
    idle_connections: int = 0
    max_connections: int = 20
    connection_errors: int = 0
    avg_response_time_ms: float = 0.0
    memory_usage_mb: float = 0.0
    last_cleanup: float = field(default_factory=time.time)


@dataclass
class MemoryPressureConfig:
    """Configuration for memory pressure handling."""
    warning_threshold_percent: float = 75.0
    critical_threshold_percent: float = 85.0
    cleanup_threshold_percent: float = 90.0
    min_pool_size: int = 5
    max_pool_size: int = 50
    scale_factor: float = 0.8  # Scale down by 20% under pressure


class EnhancedConnectionPool:
    """
    Enhanced connection pool with performance monitoring and auto-scaling.
    """
    
    def __init__(
        self,
        pool_name: str,
        connection_factory: Callable,
        initial_size: int = 10,
        max_size: int = 50,
        min_size: int = 5,
        cleanup_interval: float = 300.0,  # 5 minutes
        health_check_interval: float = 60.0,  # 1 minute
        memory_config: Optional[MemoryPressureConfig] = None
    ):
        self.pool_name = pool_name
        self.connection_factory = connection_factory
        self.initial_size = initial_size
        self.max_size = max_size
        self.min_size = min_size
        self.cleanup_interval = cleanup_interval
        self.health_check_interval = health_check_interval
        self.memory_config = memory_config or MemoryPressureConfig()
        
        # Pool management
        self._available_connections: asyncio.Queue = asyncio.Queue()
        self._in_use_connections: weakref.WeakSet = weakref.WeakSet()
        self._connection_count = 0
        self._lock = asyncio.Lock()
        
        # Performance monitoring
        self.stats = ConnectionPoolStats(pool_name=pool_name, max_connections=max_size)
        self._response_times = deque(maxlen=100)
        self._cleanup_task: Optional[asyncio.Task] = None
        self._health_check_task: Optional[asyncio.Task] = None
        
        # Memory pressure tracking
        self._memory_pressure_callbacks: List[Callable] = []
        self._last_memory_check = 0.0
        
        logger.info(f"Enhanced connection pool '{pool_name}' initialized: "
                   f"initial={initial_size}, max={max_size}, min={min_size}")

    async def initialize(self):
        """Initialize the connection pool with initial connections."""
        try:
            # Create initial connections
            for _ in range(self.initial_size):
                connection = await self._create_connection()
                if connection:
                    await self._available_connections.put(connection)
            
            # Start background tasks
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
            self._health_check_task = asyncio.create_task(self._health_check_loop())
            
            log_service_status("connection_pool", "info", 
                             f"Pool '{self.pool_name}' initialized with {self._connection_count} connections")
            
        except Exception as e:
            log_service_status("connection_pool", "error", 
                             f"Failed to initialize pool '{self.pool_name}': {e}")
            raise

    @handle_database_errors(operation="create_connection", default_value=None)
    async def _create_connection(self):
        """Create a new connection using the factory."""
        try:
            connection = await self.connection_factory()
            if connection:
                self._connection_count += 1
                self.stats.created_connections += 1
                logger.debug(f"Created new connection for pool '{self.pool_name}' "
                           f"(total: {self._connection_count})")
            return connection
        except Exception as e:
            self.stats.connection_errors += 1
            raise

    @asynccontextmanager
    async def get_connection(self):
        """Get a connection from the pool with automatic return."""
        connection = None
        start_time = time.time()
        
        try:
            connection = await self._acquire_connection()
            
            if connection:
                self.stats.active_connections += 1
                self._in_use_connections.add(connection)
                yield connection
            else:
                raise RuntimeError(f"Could not acquire connection from pool '{self.pool_name}'")
                
        finally:
            if connection:
                await self._release_connection(connection)
                self.stats.active_connections -= 1
                
                # Record response time
                response_time = (time.time() - start_time) * 1000
                self._response_times.append(response_time)
                self.stats.avg_response_time_ms = sum(self._response_times) / len(self._response_times)

    async def _acquire_connection(self):
        """Acquire a connection from the pool."""
        async with self._lock:
            # Check memory pressure before creating new connections
            await self._check_memory_pressure()
            
            # Try to get existing connection
            try:
                connection = self._available_connections.get_nowait()
                if await self._validate_connection(connection):
                    return connection
                else:
                    # Connection is stale, create a new one
                    self._connection_count -= 1
            except asyncio.QueueEmpty:
                pass
            
            # Create new connection if under limit
            if self._connection_count < self.max_size:
                return await self._create_connection()
            
            # Wait for available connection
            try:
                connection = await asyncio.wait_for(
                    self._available_connections.get(), 
                    timeout=5.0
                )
                if await self._validate_connection(connection):
                    return connection
            except asyncio.TimeoutError:
                log_service_status("connection_pool", "warning", 
                                 f"Connection timeout for pool '{self.pool_name}'")
                
        return None

    async def _release_connection(self, connection):
        """Release a connection back to the pool."""
        if connection and await self._validate_connection(connection):
            try:
                self._available_connections.put_nowait(connection)
                self._in_use_connections.discard(connection)
            except asyncio.QueueFull:
                # Pool is full, close the connection
                await self._close_connection(connection)

    @handle_errors("validate_connection", default_value=False)
    async def _validate_connection(self, connection) -> bool:
        """Validate that a connection is still healthy."""
        if not connection:
            return False
            
        try:
            # For Redis connections
            if hasattr(connection, 'ping'):
                await connection.ping()
                return True
            # For other connection types, add specific validation
            return True
        except Exception:
            return False

    async def _close_connection(self, connection):
        """Safely close a connection."""
        try:
            if hasattr(connection, 'aclose'):
                await connection.aclose()
            elif hasattr(connection, 'close'):
                if asyncio.iscoroutinefunction(connection.close):
                    await connection.close()
                else:
                    connection.close()
            self._connection_count -= 1
        except Exception as e:
            logger.warning(f"Error closing connection: {e}")

    async def _check_memory_pressure(self):
        """Check system memory pressure and adjust pool size accordingly."""
        current_time = time.time()
        if current_time - self._last_memory_check < 30.0:  # Check every 30 seconds
            return
            
        self._last_memory_check = current_time
        
        try:
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            self.stats.memory_usage_mb = memory.used / (1024 * 1024)
            
            if memory_percent > self.memory_config.critical_threshold_percent:
                # Critical memory pressure - scale down aggressively
                target_size = max(self.min_size, int(self.max_size * 0.5))
                await self._scale_pool(target_size)
                
                # Trigger memory pressure callbacks
                for callback in self._memory_pressure_callbacks:
                    try:
                        await callback(memory_percent, "critical")
                    except Exception as e:
                        logger.error(f"Memory pressure callback failed: {e}")
                        
            elif memory_percent > self.memory_config.warning_threshold_percent:
                # Warning level - scale down moderately
                target_size = max(self.min_size, int(self.max_size * self.memory_config.scale_factor))
                await self._scale_pool(target_size)
                
        except Exception as e:
            logger.error(f"Error checking memory pressure: {e}")

    async def _scale_pool(self, target_size: int):
        """Scale the pool size based on memory pressure."""
        async with self._lock:
            current_size = self._connection_count
            
            if target_size < current_size:
                # Scale down - close excess connections
                connections_to_close = current_size - target_size
                closed_count = 0
                
                while closed_count < connections_to_close and not self._available_connections.empty():
                    try:
                        connection = self._available_connections.get_nowait()
                        await self._close_connection(connection)
                        closed_count += 1
                    except asyncio.QueueEmpty:
                        break
                
                log_service_status("connection_pool", "info", 
                                 f"Scaled down pool '{self.pool_name}' from {current_size} to {self._connection_count}")

    async def _cleanup_loop(self):
        """Background cleanup task for stale connections."""
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval)
                await self._cleanup_stale_connections()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop for pool '{self.pool_name}': {e}")

    async def _health_check_loop(self):
        """Background health check task for connections."""
        while True:
            try:
                await asyncio.sleep(self.health_check_interval)
                await self._health_check_connections()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in health check loop for pool '{self.pool_name}': {e}")

    async def _cleanup_stale_connections(self):
        """Remove stale connections from the pool."""
        async with self._lock:
            current_time = time.time()
            stale_connections = []
            
            # Check available connections
            temp_queue = asyncio.Queue()
            while not self._available_connections.empty():
                try:
                    connection = self._available_connections.get_nowait()
                    if await self._validate_connection(connection):
                        await temp_queue.put(connection)
                    else:
                        stale_connections.append(connection)
                except asyncio.QueueEmpty:
                    break
            
            # Put valid connections back
            self._available_connections = temp_queue
            
            # Close stale connections
            for connection in stale_connections:
                await self._close_connection(connection)
            
            if stale_connections:
                log_service_status("connection_pool", "info", 
                                 f"Cleaned up {len(stale_connections)} stale connections from pool '{self.pool_name}'")
            
            self.stats.last_cleanup = current_time

    async def _health_check_connections(self):
        """Perform health checks on active connections."""
        unhealthy_count = 0
        
        # Check in-use connections (weak references)
        for connection in list(self._in_use_connections):
            if not await self._validate_connection(connection):
                unhealthy_count += 1
        
        if unhealthy_count > 0:
            log_service_status("connection_pool", "warning", 
                             f"Found {unhealthy_count} unhealthy connections in pool '{self.pool_name}'")

    def add_memory_pressure_callback(self, callback: Callable):
        """Add a callback to be triggered during memory pressure."""
        self._memory_pressure_callbacks.append(callback)

    def get_stats(self) -> Dict[str, Any]:
        """Get current pool statistics."""
        return {
            "pool_name": self.stats.pool_name,
            "created_connections": self.stats.created_connections,
            "active_connections": self.stats.active_connections,
            "idle_connections": self._available_connections.qsize(),
            "total_connections": self._connection_count,
            "max_connections": self.max_size,
            "connection_errors": self.stats.connection_errors,
            "avg_response_time_ms": round(self.stats.avg_response_time_ms, 2),
            "memory_usage_mb": round(self.stats.memory_usage_mb, 2),
            "last_cleanup": self.stats.last_cleanup,
        }

    async def cleanup(self):
        """Cleanup the pool and close all connections."""
        # Cancel background tasks
        if self._cleanup_task:
            self._cleanup_task.cancel()
        if self._health_check_task:
            self._health_check_task.cancel()
        
        # Close all connections
        async with self._lock:
            # Close available connections
            while not self._available_connections.empty():
                try:
                    connection = self._available_connections.get_nowait()
                    await self._close_connection(connection)
                except asyncio.QueueEmpty:
                    break
            
            # Close in-use connections
            for connection in list(self._in_use_connections):
                await self._close_connection(connection)
        
        log_service_status("connection_pool", "info", f"Cleaned up pool '{self.pool_name}'")


class PoolManager:
    """
    Manager for multiple connection pools with global optimization.
    """
    
    def __init__(self):
        self.pools: Dict[str, EnhancedConnectionPool] = {}
        self._memory_monitor_task: Optional[asyncio.Task] = None
        self._started = False

    async def create_pool(
        self,
        name: str,
        connection_factory: Callable,
        initial_size: int = 10,
        max_size: int = 50,
        min_size: int = 5,
        **kwargs
    ) -> EnhancedConnectionPool:
        """Create and register a new connection pool."""
        if name in self.pools:
            logger.warning(f"Pool '{name}' already exists, returning existing pool")
            return self.pools[name]
        
        pool = EnhancedConnectionPool(
            pool_name=name,
            connection_factory=connection_factory,
            initial_size=initial_size,
            max_size=max_size,
            min_size=min_size,
            **kwargs
        )
        
        await pool.initialize()
        self.pools[name] = pool
        
        # Add memory pressure callback
        pool.add_memory_pressure_callback(self._global_memory_pressure_handler)
        
        if not self._started:
            await self.start_monitoring()
        
        return pool

    async def get_pool(self, name: str) -> Optional[EnhancedConnectionPool]:
        """Get a pool by name."""
        return self.pools.get(name)

    @asynccontextmanager
    async def get_connection(self, pool_name: str):
        """Get a connection from a specific pool."""
        pool = self.pools.get(pool_name)
        if not pool:
            raise RuntimeError(f"Pool '{pool_name}' not found")
        
        async with pool.get_connection() as connection:
            yield connection

    async def _global_memory_pressure_handler(self, memory_percent: float, severity: str):
        """Handle memory pressure across all pools."""
        if severity == "critical":
            log_service_status("pool_manager", "warning", 
                             f"Critical memory pressure: {memory_percent:.1f}% - scaling down all pools")
            
            # Trigger cleanup on all pools
            for pool in self.pools.values():
                try:
                    await pool._cleanup_stale_connections()
                except Exception as e:
                    logger.error(f"Error during emergency cleanup: {e}")

    async def start_monitoring(self):
        """Start global monitoring tasks."""
        if not self._started:
            self._memory_monitor_task = asyncio.create_task(self._global_memory_monitor())
            self._started = True

    async def _global_memory_monitor(self):
        """Global memory monitoring task."""
        while True:
            try:
                await asyncio.sleep(60.0)  # Check every minute
                
                memory = psutil.virtual_memory()
                if memory.percent > 90.0:
                    await self._global_memory_pressure_handler(memory.percent, "critical")
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in global memory monitor: {e}")

    def get_all_stats(self) -> Dict[str, Any]:
        """Get statistics for all pools."""
        stats = {}
        total_connections = 0
        total_errors = 0
        
        for name, pool in self.pools.items():
            pool_stats = pool.get_stats()
            stats[name] = pool_stats
            total_connections += pool_stats["total_connections"]
            total_errors += pool_stats["connection_errors"]
        
        stats["global"] = {
            "total_pools": len(self.pools),
            "total_connections": total_connections,
            "total_errors": total_errors,
            "memory_usage_mb": psutil.virtual_memory().used / (1024 * 1024)
        }
        
        return stats

    async def cleanup(self):
        """Cleanup all pools and monitoring tasks."""
        if self._memory_monitor_task:
            self._memory_monitor_task.cancel()
        
        for pool in self.pools.values():
            await pool.cleanup()
        
        self.pools.clear()
        self._started = False


# Global pool manager instance
pool_manager = PoolManager()


async def get_enhanced_redis_pool(
    pool_name: str = "default",
    max_size: int = 50,
    min_size: int = 5
) -> EnhancedConnectionPool:
    """Get or create an enhanced Redis connection pool."""
    pool = await pool_manager.get_pool(pool_name)
    if pool:
        return pool
    
    # Create Redis connection factory
    async def redis_factory():
        if not REDIS_AVAILABLE:
            raise RuntimeError("Redis not available")
        
        import os
        return await redis.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", "6379")),
            db=int(os.getenv("REDIS_DB", "0")),
            decode_responses=True,
            socket_keepalive=True,
            socket_keepalive_options={},
            health_check_interval=30
        )
    
    return await pool_manager.create_pool(
        name=pool_name,
        connection_factory=redis_factory,
        max_size=max_size,
        min_size=min_size
    )


@asynccontextmanager
async def enhanced_redis_connection(pool_name: str = "default"):
    """Context manager for enhanced Redis connections."""
    async with pool_manager.get_connection(pool_name) as connection:
        yield connection
