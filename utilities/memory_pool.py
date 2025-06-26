"""
Memory pool implementation for efficient object reuse.
"""

import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
from collections import deque
import weakref


class MemoryObject:
    """Base class for pooled memory objects."""

    def __init__(self):
        """TODO: Add proper docstring for __init__."""
        self.content: Any = None
        self.metadata: Dict[str, Any] = {}
        self.last_access: datetime = datetime.now()
        self.access_count: int = 0

    def clear(self):
        """Reset the object for reuse."""
        self.content = None
        self.metadata.clear()
        self.last_access = datetime.now()
        self.access_count = 0


class MemoryPool:
    """Thread-safe memory pool for object reuse."""

    def __init__(self, max_size: int = 1000, cleanup_interval: int = 300):
        """TODO: Add proper docstring for __init__."""
        self.max_size = max_size
        self.cleanup_interval = cleanup_interval
        self.pools: Dict[str, deque] = {}
        self.active_objects: Dict[str, weakref.WeakSet] = {}
        self._lock = asyncio.Lock()
        self._cleanup_task: Optional[asyncio.Task] = None
        self.stats = {"hits": 0, "misses": 0, "created": 0, "released": 0}

    async def start(self):
        """Start the pool with cleanup task."""
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())

    async def stop(self):
        """Stop the pool and cleanup."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

    async def acquire(self, pool_name: str) -> MemoryObject:
        """Get an object from the pool."""
        async with self._lock:
            if pool_name not in self.pools:
                self.pools[pool_name] = deque(maxlen=self.max_size)
                self.active_objects[pool_name] = weakref.WeakSet()

            if self.pools[pool_name]:
                obj = self.pools[pool_name].popleft()
                self.stats["hits"] += 1
            else:
                obj = MemoryObject()
                self.stats["misses"] += 1
                self.stats["created"] += 1

            self.active_objects[pool_name].add(obj)
            obj.last_access = datetime.now()
            obj.access_count += 1
            return obj

    async def release(self, pool_name: str, obj: MemoryObject):
        """Return an object to the pool."""
        async with self._lock:
            if pool_name not in self.pools:
                return

            if len(self.pools[pool_name]) < self.max_size:
                obj.clear()
                self.pools[pool_name].append(obj)
                self.stats["released"] += 1

            if obj in self.active_objects[pool_name]:
                self.active_objects[pool_name].remove(obj)

    async def _cleanup_loop(self):
        """Periodically cleanup unused objects."""
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval)
                await self._cleanup_old_objects()
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error in cleanup loop: {e}")

    async def _cleanup_old_objects(self):
        """Remove old objects from pools."""
        async with self._lock:
            now = datetime.now()
            for pool_name, pool in self.pools.items():
                # Remove objects not accessed in the last hour
                active_count = len(self.active_objects[pool_name])
                if active_count < self.max_size * 0.8:  # Keep more objects if usage is high
                    continue

                to_remove = []
                for obj in pool:
                    if (now - obj.last_access).total_seconds() > 3600:  # 1 hour
                        to_remove.append(obj)

                for obj in to_remove:
                    pool.remove(obj)

    def get_stats(self) -> Dict[str, Any]:
        """Get pool statistics."""
        stats = self.stats.copy()
        stats.update(
            {
                "pools": {
                    name: {"size": len(pool), "active": len(self.active_objects[name])}
                    for name, pool in self.pools.items()
                }
            }
        )
        return stats
