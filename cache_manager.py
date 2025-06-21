"""
Cache Management Utility for FastAPI LLM Backend
Provides cache versioning, invalidation, and migration tools to prevent format conflicts.
"""

import hashlib
import json
from datetime import datetime
from typing import Any
from typing import Dict
from typing import Optional

from human_logging import log_service_status


class CacheManager:
    """Advanced cache management with versioning and format validation."""

    CACHE_VERSION = "v2.0.0"  # Increment when system prompt or response format changes
    VERSION_KEY = "cache:version"
    SYSTEM_PROMPT_HASH_KEY = "cache:system_prompt_hash"

    def __init__(self, redis_client):
        self.redis_client = redis_client
        self._check_cache_version()

    def _check_cache_version(self):
        """Check cache version and invalidate if outdated."""
        try:
            stored_version = self.redis_client.get(self.VERSION_KEY)
            if stored_version != self.CACHE_VERSION:
                log_service_status(
                    "CACHE",
                    "upgrading",
                    f"Cache version mismatch. Upgrading from {stored_version} to {self.CACHE_VERSION}",
                )
                self.invalidate_all_cache()
                self.redis_client.set(self.VERSION_KEY, self.CACHE_VERSION)
                log_service_status(
                    "CACHE", "ready", f"Cache upgraded to version {self.CACHE_VERSION}"                )
        except Exception as e:
            log_service_status("CACHE", "warning", f"Cache version check failed: {e}")

    def _get_system_prompt_hash(self, system_prompt: str) -> str:
        """Generate hash of system prompt for change detection."""
        return hashlib.sha256(system_prompt.encode()).hexdigest()[:16]

    def check_system_prompt_change(self, current_system_prompt: str):
        """Check if system prompt has changed and invalidate cache if needed."""
        try:
            current_hash = self._get_system_prompt_hash(current_system_prompt)
            stored_hash = self.redis_client.get(self.SYSTEM_PROMPT_HASH_KEY)

            if stored_hash != current_hash:
                log_service_status(
                    "CACHE", "updating", "System prompt changed, invalidating chat cache"
                )
                self.invalidate_chat_cache()
                self.redis_client.set(self.SYSTEM_PROMPT_HASH_KEY, current_hash)
                log_service_status(
                    "CACHE", "ready", "Chat cache invalidated due to system prompt change"                )
        except Exception as e:
            log_service_status("CACHE", "warning", f"System prompt check failed: {e}")

    def invalidate_chat_cache(self):
        """Invalidate all chat-related cache entries."""
        try:
            # Find all chat cache keys
            chat_keys = []
            cursor = 0
            while True:
                cursor, keys = self.redis_client.scan(cursor, match="chat:*", count=1000)
                chat_keys.extend(keys)
                if cursor == 0:
                    break

            if chat_keys:
                deleted = self.redis_client.delete(*chat_keys)
                log_service_status("CACHE", "ready", f"Invalidated {deleted} chat cache entries")
            else:                log_service_status("CACHE", "ready", "No chat cache entries to invalidate")
        except Exception as e:
            log_service_status("CACHE", "error", f"Failed to invalidate chat cache: {e}")

    def invalidate_all_cache(self):
        """Invalidate all cache entries (nuclear option)."""
        try:
            # Get all keys except version and system prompt hash
            all_keys = []
            cursor = 0
            while True:
                cursor, keys = self.redis_client.scan(cursor, count=1000)
                # Exclude version control keys
                filtered_keys = [
                    k for k in keys if k not in [self.VERSION_KEY, self.SYSTEM_PROMPT_HASH_KEY]
                ]
                all_keys.extend(filtered_keys)
                if cursor == 0:
                    break

            if all_keys:
                self.redis_client.delete(*all_keys)
                log_service_status(
                    "CACHE", "ready", "Invalidated all cache: {deleted} entries deleted"
                )
            else:                log_service_status("CACHE", "ready", "No cache entries to invalidate")
        except Exception as e:
            log_service_status("CACHE", "error", f"Failed to invalidate all cache: {e}")

    def validate_response_format(self, response: str) -> bool:
        """Validate that response is plain text, not JSON."""
        if not response:
            return True

        # Check if response looks like JSON
        response_trimmed = response.strip()
        if response_trimmed.startswith("{") and response_trimmed.endswith("}"):
            try:
                json.loads(response_trimmed)
                # If it parses as JSON, it's invalid for our plain text
                # requirement
                log_service_status(
                    "CACHE", "warning", "Detected JSON response format - invalidating"
                )
                return False
            except json.JSONDecodeError:
                # Not valid JSON, so it's fine
                return True

        return True

    def set_with_validation(self, key: str, value: str, ttl: int = 600) -> bool:
        """Set cache with response format validation."""
        try:
            if not self.validate_response_format(value):
                log_service_status(
                    "CACHE", "warning", f"Skipping cache for key {key} - invalid format"
                )
                return False

            # Add metadata to cached value
            cache_data = {
                "value": value,
                "cached_at": datetime.utcnow().isoformat(),
                "version": self.CACHE_VERSION,
                "format": "plain_text",
            }

            self.redis_client.setex(key, ttl, json.dumps(cache_data))
            return True
        except Exception as e:
            log_service_status("CACHE", "error", f"Failed to set cache for key {key}: {e}")
            return False

    def get_with_validation(self, key: str) -> Optional[str]:
        """Get cache with format validation."""
        try:
            cached_data = self.redis_client.get(key)
            if not cached_data:
                return None

            # Try to parse as new format with metadata
            try:
                data = json.loads(cached_data)
                if isinstance(data, dict) and "value" in data:
                    # Validate format
                    if not self.validate_response_format(data["value"]):
                        log_service_status(
                            "CACHE", "warning", "Invalidating cache key {key} - bad format"
                        )
                        self.redis_client.delete(key)
                        return None
                    return data["value"]
                else:
                    # Old format, validate and migrate or invalidate
                    if not self.validate_response_format(cached_data):
                        log_service_status(
                            "CACHE", "warning", f"Invalidating old format cache key {key}"
                        )
                        self.redis_client.delete(key)
                        return None
                    return cached_data
            except json.JSONDecodeError:
                # Plain string, validate format
                if not self.validate_response_format(cached_data):
                    log_service_status(
                        "CACHE", "warning", "Invalidating cache key {key} - bad format"
                    )
                    self.redis_client.delete(key)
                    return None
                return cached_data
        except Exception as e:
            log_service_status("CACHE", "error", f"Failed to get cache for key {key}: {e}")
            return None

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics and health info."""
        try:
            info = self.redis_client.info()

            # Count different types of cache entries
            cache_counts = {"chat": 0, "history": 0, "other": 0}

            cursor = 0
            while True:
                cursor, keys = self.redis_client.scan(cursor, count=1000)
                for key in keys:
                    if key.startswith("chat:"):
                        cache_counts["chat"] += 1
                    elif key.startswith("chat_history:"):
                        cache_counts["history"] += 1
                    else:
                        cache_counts["other"] += 1
                if cursor == 0:
                    break

            return {
                "version": self.redis_client.get(self.VERSION_KEY) or "unknown",
                "cache_counts": cache_counts,
                "memory_usage": info.get("used_memory_human", "unknown"),
                "connected_clients": info.get("connected_clients", 0),
                "total_keys": sum(cache_counts.values()),
            }
        except Exception as e:
            log_service_status("CACHE", "error", f"Failed to get cache stats: {e}")
            return {"error": str(e)}
