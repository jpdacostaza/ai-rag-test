"""
Function-level caching utilities for performance optimization.
"""

import functools
import hashlib
import json
import time
from typing import Any, Dict, Optional, Callable
from core.unified_logging import get_logger

logger = get_logger(__name__)

def cache_with_ttl(ttl_seconds: int = 300, max_size: int = 128):
    """
    Decorator for function-level caching with TTL.
    
    Args:
        ttl_seconds: Time to live for cached results
        max_size: Maximum number of cached results
    """
    def decorator(func: Callable) -> Callable:
        cache: Dict[str, Dict[str, Any]] = {}
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = _generate_cache_key(func.__name__, args, kwargs)
            
            # Check if cached result exists and is still valid
            if cache_key in cache:
                cached_entry = cache[cache_key]
                if time.time() - cached_entry['timestamp'] < ttl_seconds:
                    logger.debug(f"Cache hit for {func.__name__}: {cache_key[:12]}...")
                    return cached_entry['result']
                else:
                    # Remove expired entry
                    del cache[cache_key]
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            
            # Implement simple LRU if cache is full
            if len(cache) >= max_size:
                oldest_key = min(cache.keys(), key=lambda k: cache[k]['timestamp'])
                del cache[oldest_key]
            
            cache[cache_key] = {
                'result': result,
                'timestamp': time.time()
            }
            
            logger.debug(f"Cached result for {func.__name__}: {cache_key[:12]}...")
            return result
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = _generate_cache_key(func.__name__, args, kwargs)
            
            # Check if cached result exists and is still valid
            if cache_key in cache:
                cached_entry = cache[cache_key]
                if time.time() - cached_entry['timestamp'] < ttl_seconds:
                    logger.debug(f"Cache hit for {func.__name__}: {cache_key[:12]}...")
                    return cached_entry['result']
                else:
                    # Remove expired entry
                    del cache[cache_key]
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            
            # Implement simple LRU if cache is full
            if len(cache) >= max_size:
                oldest_key = min(cache.keys(), key=lambda k: cache[k]['timestamp'])
                del cache[oldest_key]
            
            cache[cache_key] = {
                'result': result,
                'timestamp': time.time()
            }
            
            logger.debug(f"Cached result for {func.__name__}: {cache_key[:12]}...")
            return result
        
        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator

def _generate_cache_key(func_name: str, args: tuple, kwargs: dict) -> str:
    """Generate deterministic cache key from function arguments."""
    # Create a deterministic representation of arguments
    key_data = {
        'function': func_name,
        'args': str(args),
        'kwargs': sorted(kwargs.items()) if kwargs else []
    }
    
    key_string = json.dumps(key_data, sort_keys=True, default=str)
    return hashlib.sha256(key_string.encode()).hexdigest()[:16]

# Import asyncio at the bottom to avoid circular imports
import asyncio
