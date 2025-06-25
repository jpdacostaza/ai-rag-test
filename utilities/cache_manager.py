"""Cache manager utility for memory-efficient caching."""
from typing import Generic, TypeVar, Dict, Optional, Any
from collections import OrderedDict
import time
import sys
import os
import asyncio

# Add logging import
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from human_logging import log_service_status
except ImportError:
    # Fallback if logging is not available
    def log_service_status(service: str, status: str, details: str = "") -> None:
        pass

# Alert manager integration
try:
    from utilities.alert_manager import alert_cache_performance
except ImportError:
    # Fallback if alert manager is not available
    async def alert_cache_performance(hit_rate: float, component: str = "cache"):
        pass

T = TypeVar('T')

class CacheManager(Generic[T]):
    """Thread-safe LRU cache with size limit and statistics tracking."""
    
    def __init__(self, max_size: int = 1000, alert_threshold: float = 50.0):
        """Initialize cache with maximum size and alert threshold."""
        self._cache: OrderedDict[str, T] = OrderedDict()
        self._max_size = max_size
        self._hit_count = 0
        self._miss_count = 0
        self._total_requests = 0
        self._alert_threshold = alert_threshold
        self._last_alert_time = 0
        self._alert_cooldown = 300  # 5 minutes between alerts
    
    def get(self, key: str) -> Optional[T]:
        """Get value from cache."""
        self._total_requests += 1
        if key not in self._cache:
            self._miss_count += 1
            hit_rate = (self._hit_count / self._total_requests) * 100
            log_service_status("cache", "info", f"Cache miss - key: {key}, hit_rate: {hit_rate:.1f}%")
            
            # Check performance every 100 requests
            if self._total_requests % 100 == 0:
                self._trigger_performance_check()
            
            return None
        
        # Move to end to mark as recently used
        self._cache.move_to_end(key)
        self._hit_count += 1
        hit_rate = (self._hit_count / self._total_requests) * 100
        log_service_status("cache", "info", f"Cache hit - key: {key}, hit_rate: {hit_rate:.1f}%")
        
        # Check performance every 100 requests
        if self._total_requests % 100 == 0:
            self._trigger_performance_check()
        
        return self._cache[key]
    
    def set(self, key: str, value: T) -> None:
        """Set value in cache."""
        if key in self._cache:
            # If key exists, update its value and move to end
            self._cache.move_to_end(key)
        else:
            # Remove oldest item if cache is too large
            if len(self._cache) >= self._max_size:
                lru_key, _ = self._cache.popitem(last=False)
                log_service_status("cache", "info", f"Cache eviction - removed key: {lru_key} (LRU)")
        
        self._cache[key] = value
        log_service_status("cache", "info", f"Cache set - key: {key}, cache_size: {len(self._cache)}/{self._max_size}")
    
    def remove(self, key: str) -> None:
        """Remove item from cache."""
        if key in self._cache:
            self._cache.pop(key)
            log_service_status("cache", "info", f"Cache remove - key: {key}")
    
    def clear(self) -> None:
        """Clear all items from cache."""
        cache_size = len(self._cache)
        self._cache.clear()
        self._hit_count = 0
        self._miss_count = 0
        self._total_requests = 0
        log_service_status("cache", "info", f"Cache cleared - removed {cache_size} entries")
    
    def get_size(self) -> int:
        """Get current cache size."""
        return len(self._cache)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        hit_rate = (self._hit_count / self._total_requests * 100) if self._total_requests > 0 else 0
        return {
            "size": len(self._cache),
            "max_size": self._max_size,
            "hit_count": self._hit_count,
            "miss_count": self._miss_count,
            "total_requests": self._total_requests,
            "hit_rate": f"{hit_rate:.1f}%",
            "hit_rate_numeric": hit_rate
        }

    async def _check_performance_and_alert(self):
        """Check cache performance and trigger alerts if needed."""
        if self._total_requests < 50:  # Don't alert on low sample sizes
            return
            
        hit_rate = (self._hit_count / self._total_requests * 100)
        current_time = time.time()
        
        # Only send alerts if hit rate is below threshold and cooldown has passed
        if (hit_rate < self._alert_threshold and 
            current_time - self._last_alert_time > self._alert_cooldown):
            
            try:
                await alert_cache_performance(hit_rate, "cache_manager")
                self._last_alert_time = current_time
            except Exception as e:
                log_service_status("cache", "warning", f"Failed to send cache performance alert: {e}")
    
    def _trigger_performance_check(self):
        """Trigger async performance check without blocking."""
        try:
            # Create and run the async task
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(self._check_performance_and_alert())
            else:
                asyncio.run(self._check_performance_and_alert())
        except Exception:
            # If we can't get the event loop, just skip the alert
            pass
