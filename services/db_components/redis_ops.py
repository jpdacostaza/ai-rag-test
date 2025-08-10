"""Redis operation helpers extracted from DatabaseManager.

Provides a reusable execute_redis_operation function that instruments metrics
and performs retry logic using a passed-in reinitializer callback.
"""
from __future__ import annotations
import time
from typing import Any, Awaitable, Callable, Optional
import redis.asyncio as redis
from core.unified_logging import log_service_status
from core.metrics import (
    METRICS_ENABLED,
    redis_operation_latency_seconds,
    redis_operation_errors_total,
)

RedisOperation = Callable[[redis.Redis], Awaitable[Any]]
Reinitializer = Callable[[], Awaitable[None]]

async def execute_redis_operation(
    redis_client: Optional[redis.Redis],
    lock,
    operation: RedisOperation,
    operation_name: str,
    reinitialize: Reinitializer,
) -> Any:
    """Execute a Redis operation with metrics + single retry on failure.

    Args:
        redis_client: The redis client instance or None
        lock: An asyncio.Lock guarding redis operations
        operation: Coroutine function taking redis client returning result
        operation_name: Name for metrics/ logging labels
        reinitialize: Callback to attempt redis reinitialization if needed
    Returns:
        Result of operation or None on failure
    """
    if not redis_client:
        log_service_status("redis", "error", f"Redis not available for operation: {operation_name}")
        return None
    try:
        start = time.time()
        async with lock:
            result = await operation(redis_client)
            if METRICS_ENABLED:
                redis_operation_latency_seconds.labels(operation=operation_name).observe(time.time() - start)
            return result
    except redis.RedisError as e:
        log_service_status("redis", "error", f"Redis operation '{operation_name}' failed: {e}")
        if METRICS_ENABLED:
            redis_operation_errors_total.labels(operation=operation_name).inc()
        # Retry once after reinit
        try:
            await reinitialize()
            if not redis_client:  # still None
                return None
            async with lock:
                start = time.time()
                result = await operation(redis_client)
                if METRICS_ENABLED:
                    redis_operation_latency_seconds.labels(operation=operation_name).observe(time.time() - start)
                return result
        except redis.RedisError as e2:
            log_service_status("redis", "error", f"Retry failed for '{operation_name}': {e2}")
            if METRICS_ENABLED:
                redis_operation_errors_total.labels(operation=operation_name).inc()
            return None
