"""
Advanced Prompt Caching Service
==============================

Implements industry best practices for prompt caching:
- Anthropic-style prompt caching with cache_control markers
- Semantic caching for similar queries
- Multi-tier caching (memory + Redis + LLM provider level)
- Cache metrics and monitoring
- Smart cache invalidation strategies

Based on research from:
- Anthropic prompt caching documentation
- LangChain caching patterns
- Industry best practices for LLM optimization
"""

import asyncio
import hashlib
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum

# Core imports
from core.unified_logging import get_logger, log_service_status
from utilities.cache_manager import CacheManager

logger = get_logger(__name__)


class CacheLevel(Enum):
    """Cache level types for multi-tier caching strategy."""
    MEMORY = "memory"
    REDIS = "redis" 
    LLM_PROVIDER = "llm_provider"


class CacheTTL(Enum):
    """Cache TTL configurations based on use case."""
    SYSTEM_PROMPT = 3600  # 1 hour - system prompts rarely change
    USER_CONTEXT = 300    # 5 minutes - user context changes frequently
    CONVERSATION = 1800   # 30 minutes - conversation context
    TOOL_DEFINITIONS = 7200  # 2 hours - tools change infrequently
    SEMANTIC = 900        # 15 minutes - semantic similarity cache


@dataclass
class CacheEntry:
    """Cache entry with metadata for advanced caching strategies."""
    content: str
    cache_type: str
    created_at: datetime
    last_accessed: datetime
    access_count: int
    ttl_seconds: int
    cache_control: Optional[Dict[str, Any]] = None
    semantic_hash: Optional[str] = None
    token_count: Optional[int] = None


@dataclass
class CacheMetrics:
    """Cache performance metrics tracking."""
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    cache_creation_tokens: int = 0
    cache_read_tokens: int = 0
    total_cost_saved: float = 0.0
    
    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate percentage."""
        total = self.hits + self.misses
        return (self.hits / total * 100) if total > 0 else 0.0


class PromptCacheService:
    """
    Advanced prompt caching service implementing industry best practices.
    
    Features:
    - Multi-tier caching strategy (memory -> Redis -> LLM provider)
    - Semantic similarity caching for related queries
    - Anthropic-style cache_control markers
    - Intelligent cache invalidation
    - Comprehensive metrics tracking
    - Cost optimization strategies
    """
    
    def __init__(self, redis_client=None, max_memory_cache_size: int = 1000):
        """Initialize prompt cache service with multi-tier strategy."""
        self.logger = logger
        self.redis_client = redis_client
        
        # Memory cache for fastest access
        self.memory_cache = CacheManager[CacheEntry](max_size=max_memory_cache_size)
        
        # Cache metrics tracking
        self.metrics = CacheMetrics()
        
        # Semantic similarity threshold (0.0 - 1.0)
        self.semantic_threshold = 0.85
        
        # Cache configuration
        self.config = {
            "enable_semantic_caching": True,
            "enable_anthropic_caching": True,
            "enable_multi_tier": True,
            "max_cache_size": max_memory_cache_size,
            "default_ttl": CacheTTL.CONVERSATION.value
        }
        
        self._init_redis_connection()
        
    def _init_redis_connection(self):
        """Initialize Redis connection if not provided."""
        if not self.redis_client:
            try:
                import redis
                self.redis_client = redis.Redis(
                    host='localhost', 
                    port=6379, 
                    db=1,  # Use separate DB for prompt cache
                    decode_responses=True
                )
                # Test connection
                self.redis_client.ping()
                log_service_status("PROMPT_CACHE", "ready", "Redis connection established")
            except Exception as e:
                log_service_status("PROMPT_CACHE", "warning", f"Redis unavailable: {e}")
                self.redis_client = None
    
    def _generate_cache_key(self, prompt: str, model: str = "", cache_type: str = "general") -> str:
        """Generate deterministic cache key for prompt."""
        content = f"{cache_type}:{model}:{prompt}"
        return f"prompt_cache:{hashlib.sha256(content.encode()).hexdigest()[:16]}"
    
    def _generate_semantic_hash(self, prompt: str) -> str:
        """Generate semantic hash for similarity matching."""
        # Simple semantic hash - could be enhanced with embeddings
        words = prompt.lower().split()
        # Remove common words for better semantic matching
        stop_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by"}
        semantic_words = [w for w in words if w not in stop_words and len(w) > 2]
        semantic_content = " ".join(sorted(semantic_words))
        return hashlib.md5(semantic_content.encode()).hexdigest()[:12]
    
    def _estimate_token_count(self, text: str) -> int:
        """Estimate token count for cost calculations."""
        # Rough estimation: ~4 characters per token
        return len(text) // 4
    
    async def get_cached_prompt(
        self, 
        prompt: str, 
        model: str = "", 
        cache_type: str = "general"
    ) -> Optional[CacheEntry]:
        """
        Retrieve cached prompt with multi-tier fallback strategy.
        
        Search order:
        1. Memory cache (fastest)
        2. Redis cache (persistent)
        3. Semantic similarity cache (flexible)
        """
        cache_key = self._generate_cache_key(prompt, model, cache_type)
        
        # Level 1: Memory cache
        memory_entry = self.memory_cache.get(cache_key)
        if memory_entry and self._is_cache_valid(memory_entry):
            memory_entry.last_accessed = datetime.utcnow()
            memory_entry.access_count += 1
            self.metrics.hits += 1
            log_service_status("PROMPT_CACHE", "info", f"✅ Memory cache HIT: {cache_key[:12]}... (type: {cache_type}, tokens: {memory_entry.token_count})")
            return memory_entry
        
        # Level 2: Redis cache
        if self.redis_client:
            try:
                redis_data = self.redis_client.get(cache_key)
                if redis_data:
                    entry_dict = json.loads(redis_data)
                    # Convert ISO strings back to datetime objects
                    entry_dict['created_at'] = datetime.fromisoformat(entry_dict['created_at'])
                    entry_dict['last_accessed'] = datetime.fromisoformat(entry_dict['last_accessed'])
                    entry = CacheEntry(**entry_dict)
                    if self._is_cache_valid(entry):
                        # Promote to memory cache
                        self.memory_cache.set(cache_key, entry)
                        entry.last_accessed = datetime.utcnow()
                        entry.access_count += 1
                        self.metrics.hits += 1
                        log_service_status("PROMPT_CACHE", "info", f"✅ Redis cache HIT: {cache_key[:12]}... (type: {cache_type}, tokens: {entry.token_count})")
                        return entry
            except Exception as e:
                log_service_status("PROMPT_CACHE", "warning", f"Redis cache read error: {e}")
        
        # Level 3: Semantic similarity cache
        if self.config["enable_semantic_caching"]:
            semantic_entry = await self._find_semantic_match(prompt, model, cache_type)
            if semantic_entry:
                # Store exact match for future use
                await self.cache_prompt(prompt, semantic_entry.content, model, cache_type, semantic_entry.ttl_seconds)
                self.metrics.hits += 1
                log_service_status("PROMPT_CACHE", "info", f"✅ Semantic cache HIT: {cache_key[:12]}... (type: {cache_type}, similarity match)")
                return semantic_entry
        
        # Cache miss
        self.metrics.misses += 1
        log_service_status("PROMPT_CACHE", "info", f"❌ Cache MISS: {cache_key[:12]}... (type: {cache_type})")
        return None
    
    async def cache_prompt(
        self, 
        prompt: str, 
        response: str, 
        model: str = "", 
        cache_type: str = "general",
        ttl_seconds: Optional[int] = None
    ) -> bool:
        """
        Cache prompt with response using multi-tier strategy.
        
        Stores in:
        1. Memory cache (for speed)
        2. Redis cache (for persistence)
        3. Semantic index (for similarity matching)
        """
        if not response or not response.strip():
            return False
        
        cache_key = self._generate_cache_key(prompt, model, cache_type)
        
        # Use appropriate TTL based on cache type
        if ttl_seconds is None:
            ttl_seconds = self._get_default_ttl(cache_type)
        
        # Create cache entry
        entry = CacheEntry(
            content=response,
            cache_type=cache_type,
            created_at=datetime.utcnow(),
            last_accessed=datetime.utcnow(),
            access_count=0,
            ttl_seconds=ttl_seconds,
            semantic_hash=self._generate_semantic_hash(prompt),
            token_count=self._estimate_token_count(response)
        )
        
        try:
            # Store in memory cache
            self.memory_cache.set(cache_key, entry)
            
            # Store in Redis cache
            if self.redis_client:
                entry_dict = asdict(entry)
                # Convert datetime objects to ISO strings for JSON serialization
                entry_dict['created_at'] = entry.created_at.isoformat()
                entry_dict['last_accessed'] = entry.last_accessed.isoformat()
                
                self.redis_client.setex(
                    cache_key, 
                    ttl_seconds, 
                    json.dumps(entry_dict, default=str)
                )
            
            # Update metrics
            if entry.token_count:
                self.metrics.cache_creation_tokens += entry.token_count
            
            log_service_status("PROMPT_CACHE", "info", f"💾 Response CACHED: {cache_key[:12]}... (type: {cache_type}, tokens: {entry.token_count}, TTL: {ttl_seconds}s)")
            return True
            
        except Exception as e:
            log_service_status("PROMPT_CACHE", "error", f"Cache storage failed: {e}")
            return False
    
    async def _find_semantic_match(
        self, 
        prompt: str, 
        model: str, 
        cache_type: str
    ) -> Optional[CacheEntry]:
        """Find semantically similar cached prompts."""
        if not self.config["enable_semantic_caching"]:
            return None
        
        semantic_hash = self._generate_semantic_hash(prompt)
        
        # Search memory cache for semantic matches
        for cache_key, entry in self.memory_cache._cache.items():
            if (entry.cache_type == cache_type and 
                entry.semantic_hash == semantic_hash and
                self._is_cache_valid(entry)):
                return entry
        
        # Search Redis cache for semantic matches
        if self.redis_client:
            try:
                # Use Redis SCAN to find semantic matches
                pattern = f"prompt_cache:*"
                for key in self.redis_client.scan_iter(match=pattern):
                    try:
                        data = self.redis_client.get(key)
                        if data:
                            entry_dict = json.loads(data)
                            if (entry_dict.get('cache_type') == cache_type and
                                entry_dict.get('semantic_hash') == semantic_hash):
                                entry = CacheEntry(**entry_dict)
                                if self._is_cache_valid(entry):
                                    return entry
                    except Exception:
                        continue
            except Exception as e:
                log_service_status("PROMPT_CACHE", "warning", f"Semantic search error: {e}")
        
        return None
    
    def _is_cache_valid(self, entry: CacheEntry) -> bool:
        """Check if cache entry is still valid based on TTL."""
        age = datetime.utcnow() - entry.created_at
        return age.total_seconds() < entry.ttl_seconds
    
    def _get_default_ttl(self, cache_type: str) -> int:
        """Get default TTL based on cache type."""
        ttl_mapping = {
            "system_prompt": CacheTTL.SYSTEM_PROMPT.value,
            "user_context": CacheTTL.USER_CONTEXT.value,
            "conversation": CacheTTL.CONVERSATION.value,
            "tool_definitions": CacheTTL.TOOL_DEFINITIONS.value,
            "semantic": CacheTTL.SEMANTIC.value,
        }
        return ttl_mapping.get(cache_type, self.config["default_ttl"])
    
    def create_anthropic_cache_control(
        self, 
        cache_type: str = "ephemeral",
        ttl: str = "5m"
    ) -> Dict[str, Any]:
        """
        Create Anthropic-style cache_control marker.
        
        Args:
            cache_type: Type of cache (ephemeral)
            ttl: Time to live ("5m" or "1h")
        """
        return {
            "type": cache_type,
            "ttl": ttl
        }
    
    def enhance_prompt_with_caching(
        self, 
        messages: List[Dict[str, Any]], 
        system_prompt: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Enhance prompt structure with cache_control markers for optimal caching.
        
        Following Anthropic best practices:
        1. Tools first (cached with 1h TTL - change infrequently)
        2. System prompt (cached with 1h TTL - stable content)  
        3. Messages (not cached - dynamic content)
        """
        enhanced_request = {}
        
        # Add tools with caching (if provided)
        if tools and self.config["enable_anthropic_caching"]:
            enhanced_tools = []
            for i, tool in enumerate(tools):
                enhanced_tool = tool.copy()
                # Cache tool definitions (they change infrequently)
                if i == len(tools) - 1:  # Last tool gets cache marker
                    enhanced_tool["cache_control"] = self.create_anthropic_cache_control("ephemeral", "1h")
                enhanced_tools.append(enhanced_tool)
            enhanced_request["tools"] = enhanced_tools
        elif tools:
            enhanced_request["tools"] = tools
        
        # Add system prompt with caching (if provided)
        if system_prompt and self.config["enable_anthropic_caching"]:
            enhanced_request["system"] = [{
                "type": "text",
                "text": system_prompt,
                "cache_control": self.create_anthropic_cache_control("ephemeral", "1h")
            }]
        elif system_prompt:
            enhanced_request["system"] = [{"type": "text", "text": system_prompt}]
        
        # Add messages (not cached - dynamic content)
        enhanced_request["messages"] = messages
        
        return enhanced_request
    
    async def clear_cache(self, cache_type: Optional[str] = None) -> int:
        """Clear cache entries, optionally filtered by type."""
        cleared_count = 0
        
        # Clear memory cache
        if cache_type:
            # Filter by cache type
            keys_to_remove = []
            for key, entry in self.memory_cache._cache.items():
                if entry.cache_type == cache_type:
                    keys_to_remove.append(key)
            for key in keys_to_remove:
                self.memory_cache.remove(key)
                cleared_count += 1
        else:
            # Clear all
            cleared_count = len(self.memory_cache._cache)
            self.memory_cache.clear()
        
        # Clear Redis cache
        if self.redis_client:
            try:
                pattern = f"prompt_cache:*"
                keys = list(self.redis_client.scan_iter(match=pattern))
                if keys:
                    deleted = self.redis_client.delete(*keys)
                    cleared_count += deleted
            except Exception as e:
                log_service_status("PROMPT_CACHE", "warning", f"Redis cache clear error: {e}")
        
        log_service_status("PROMPT_CACHE", "info", f"Cleared {cleared_count} cache entries")
        return cleared_count
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics."""
        memory_size = len(self.memory_cache._cache)
        redis_size = 0
        
        if self.redis_client:
            try:
                pattern = f"prompt_cache:*"
                redis_size = len(list(self.redis_client.scan_iter(match=pattern)))
            except Exception:
                redis_size = -1  # Error indicator
        
        return {
            "memory_cache_size": memory_size,
            "redis_cache_size": redis_size,
            "hit_rate": self.metrics.hit_rate,
            "total_hits": self.metrics.hits,
            "total_misses": self.metrics.misses,
            "cache_creation_tokens": self.metrics.cache_creation_tokens,
            "cache_read_tokens": self.metrics.cache_read_tokens,
            "estimated_cost_saved": self.metrics.total_cost_saved,
            "config": self.config
        }
    
    async def optimize_cache_performance(self):
        """Perform cache optimization and cleanup."""
        try:
            # Remove expired entries from memory cache
            expired_keys = []
            for key, entry in self.memory_cache._cache.items():
                if not self._is_cache_valid(entry):
                    expired_keys.append(key)
            
            for key in expired_keys:
                self.memory_cache.remove(key)
                self.metrics.evictions += 1
            
            # Log optimization results
            if expired_keys:
                log_service_status("PROMPT_CACHE", "info", f"Optimized cache: removed {len(expired_keys)} expired entries")
            
        except Exception as e:
            log_service_status("PROMPT_CACHE", "error", f"Cache optimization failed: {e}")


# Global instance for easy access
prompt_cache_service = PromptCacheService()


# Backwards compatibility and convenience functions
async def get_cached_response(prompt: str, model: str = "") -> Optional[str]:
    """Convenience function to get cached response."""
    entry = await prompt_cache_service.get_cached_prompt(prompt, model)
    return entry.content if entry else None


async def cache_response(prompt: str, response: str, model: str = "") -> bool:
    """Convenience function to cache response."""
    return await prompt_cache_service.cache_prompt(prompt, response, model)


def create_cache_control(ttl: str = "5m") -> Dict[str, Any]:
    """Convenience function to create cache control marker."""
    return prompt_cache_service.create_anthropic_cache_control("ephemeral", ttl)
