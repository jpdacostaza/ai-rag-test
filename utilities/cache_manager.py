"""Cache manager utility for memory-efficient caching."""
from typing import Generic, TypeVar, Dict, Optional, Any
from collections import OrderedDict

T = TypeVar('T')

class CacheManager(Generic[T]):
    """Thread-safe LRU cache with size limit."""
    
    def __init__(self, max_size: int = 1000):
        """Initialize cache with maximum size."""
        self._cache: OrderedDict[str, T] = OrderedDict()
        self._max_size = max_size
    
    def get(self, key: str) -> Optional[T]:
        """Get value from cache."""
        if key not in self._cache:
            return None
        # Move to end to mark as recently used
        self._cache.move_to_end(key)
        return self._cache[key]
    
    def set(self, key: str, value: T) -> None:
        """Set value in cache."""
        if key in self._cache:
            # If key exists, update its value and move to end
            self._cache.move_to_end(key)
        self._cache[key] = value
        # Remove oldest item if cache is too large
        if len(self._cache) > self._max_size:
            self._cache.popitem(last=False)
    
    def remove(self, key: str) -> None:
        """Remove item from cache."""
        self._cache.pop(key, None)
    
    def clear(self) -> None:
        """Clear all items from cache."""
        self._cache.clear()
    
    def get_size(self) -> int:
        """Get current cache size."""
        return len(self._cache)
