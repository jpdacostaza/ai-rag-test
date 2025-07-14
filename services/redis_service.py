"""
Redis Service
============

Focused service class for Redis operations, replacing direct db_manager usage.
"""

import json
import logging
from typing import Any, Dict, List, Optional, Union
import time

from utilities.simple_error_handling import handle_errors


class RedisService:
    """
    Service class for Redis operations with proper error handling and logging.
    """
    
    def __init__(self, redis_client=None):
        """
        Initialize Redis service.
        
        Args:
            redis_client: Redis client instance, falls back to db_manager if None
        """
        self.redis_client = redis_client
        if not self.redis_client:
            # Fallback to global db_manager for gradual migration
            try:
                from services.database_manager import db_manager
                self.redis_client = db_manager.redis_client if db_manager else None
            except Exception as e:
                logging.warning(f"Could not get Redis client from db_manager: {e}")
                self.redis_client = None

    @handle_errors("redis_set", default_value=False)
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Set a value in Redis with optional TTL.
        
        Args:
            key: Redis key
            value: Value to store (will be JSON serialized if not string)
            ttl: Time to live in seconds
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.redis_client:
            return False
            
        try:
            # Serialize complex objects to JSON
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            elif not isinstance(value, (str, bytes, int, float)):
                value = str(value)
                
            if ttl:
                result = await self.redis_client.setex(key, ttl, value)
            else:
                result = await self.redis_client.set(key, value)
                
            return bool(result)
            
        except Exception as e:
            logging.error(f"Redis set failed for key {key}: {e}")
            return False

    @handle_errors("redis_get", default_value=None)
    async def get(self, key: str) -> Optional[Any]:
        """
        Get a value from Redis.
        
        Args:
            key: Redis key
            
        Returns:
            The value if found, None otherwise
        """
        if not self.redis_client:
            return None
            
        try:
            value = await self.redis_client.get(key)
            if value is None:
                return None
                
            # Try to decode as JSON first
            if isinstance(value, bytes):
                value = value.decode('utf-8')
                
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value
                
        except Exception as e:
            logging.error(f"Redis get failed for key {key}: {e}")
            return None

    @handle_errors("redis_delete", default_value=False)
    async def delete(self, key: str) -> bool:
        """
        Delete a key from Redis.
        
        Args:
            key: Redis key to delete
            
        Returns:
            bool: True if key was deleted, False otherwise
        """
        if not self.redis_client:
            return False
            
        try:
            result = await self.redis_client.delete(key)
            return result > 0
        except Exception as e:
            logging.error(f"Redis delete failed for key {key}: {e}")
            return False

    @handle_errors("redis_exists", default_value=False)
    async def exists(self, key: str) -> bool:
        """
        Check if a key exists in Redis.
        
        Args:
            key: Redis key to check
            
        Returns:
            bool: True if key exists, False otherwise
        """
        if not self.redis_client:
            return False
            
        try:
            return bool(await self.redis_client.exists(key))
        except Exception as e:
            logging.error(f"Redis exists check failed for key {key}: {e}")
            return False

    @handle_errors("redis_list_push", default_value=False)
    async def list_push(self, key: str, *values: Any) -> bool:
        """
        Push values to a Redis list.
        
        Args:
            key: Redis list key
            values: Values to push
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.redis_client:
            return False
            
        try:
            # Serialize complex objects
            serialized_values = []
            for value in values:
                if isinstance(value, (dict, list)):
                    serialized_values.append(json.dumps(value))
                else:
                    serialized_values.append(str(value))
                    
            result = await self.redis_client.lpush(key, *serialized_values)
            return result > 0
            
        except Exception as e:
            logging.error(f"Redis list push failed for key {key}: {e}")
            return False

    @handle_errors("redis_list_get", default_value=[])
    async def list_get(self, key: str, start: int = 0, end: int = -1) -> List[Any]:
        """
        Get values from a Redis list.
        
        Args:
            key: Redis list key
            start: Start index (default: 0)
            end: End index (default: -1 for all)
            
        Returns:
            List of values
        """
        if not self.redis_client:
            return []
            
        try:
            values = await self.redis_client.lrange(key, start, end)
            result = []
            
            for value in values:
                if isinstance(value, bytes):
                    value = value.decode('utf-8')
                    
                try:
                    result.append(json.loads(value))
                except (json.JSONDecodeError, TypeError):
                    result.append(value)
                    
            return result
            
        except Exception as e:
            logging.error(f"Redis list get failed for key {key}: {e}")
            return []

    async def get_stats(self) -> Dict[str, Any]:
        """
        Get Redis connection and usage statistics.
        
        Returns:
            Dict with Redis stats
        """
        if not self.redis_client:
            return {"status": "unavailable", "connected": False}
            
        try:
            info = await self.redis_client.info()
            
            # Handle different possible return types from info()
            if hasattr(info, 'get'):
                # It's a dict-like object
                return {
                    "status": "connected",
                    "connected": True,
                    "used_memory": info.get("used_memory_human", "unknown"),
                    "connected_clients": info.get("connected_clients", 0),
                    "total_commands_processed": info.get("total_commands_processed", 0),
                    "uptime_in_seconds": info.get("uptime_in_seconds", 0)
                }
            else:
                # It might be a different type, return basic info
                return {
                    "status": "connected", 
                    "connected": True,
                    "info_type": str(type(info)),
                    "raw_info": str(info)[:200]  # First 200 chars for debugging
                }
        except Exception as e:
            logging.error(f"Redis stats failed: {e}")
            return {"status": "error", "connected": False, "error": str(e)}

    @handle_errors("redis_health_check", default_value=False)
    async def health_check(self) -> bool:
        """
        Check Redis health by doing a simple ping.
        
        Returns:
            bool: True if Redis is healthy, False otherwise
        """
        if not self.redis_client:
            return False
            
        try:
            response = await self.redis_client.ping()
            return response is True
        except Exception as e:
            logging.error(f"Redis health check failed: {e}")
            return False
