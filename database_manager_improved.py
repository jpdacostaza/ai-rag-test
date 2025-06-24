"""
Improved Database Manager implementation with memory management and type safety.
"""

import os
import json
import asyncio
from typing import Optional, Dict, Any, List, Union
from datetime import datetime
import logging

import redis
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

from utilities.validation import DatabaseConfig, ChatMessage, validate_query_params
from utilities.memory_pool import MemoryPool
from utilities.memory_monitor import MemoryPressureMonitor
from utilities.database_types import ChromaDBClient, CacheManager
from error_handler import RedisConnectionHandler
from human_logging import log_service_status

class ImprovedDatabaseManager:
    """Enhanced database manager with memory management and type safety."""
    
    def __init__(self):
        # Initialize configuration
        self.config = self._load_config()
        
        # Initialize connections
        self.redis_pool: Optional[redis.ConnectionPool] = None
        self.chroma_db: Optional[ChromaDBClient] = None
        self.embedding_model: Optional[SentenceTransformer] = None
        
        # Initialize memory management
        self.memory_pool = MemoryPool(max_size=1000)
        self.memory_monitor = MemoryPressureMonitor()
        self.cache = CacheManager[Any](max_size=10000)
        
        # Initialize locks
        self._redis_lock = asyncio.Lock()
        self._chroma_lock = asyncio.Lock()
        self._embedding_lock = asyncio.Lock()
        
    def _load_config(self) -> DatabaseConfig:
        """Load and validate configuration."""
        return DatabaseConfig(
            redis_host=os.getenv("REDIS_HOST", "localhost"),
            redis_port=int(os.getenv("REDIS_PORT", 6379)),
            chroma_host=os.getenv("CHROMA_HOST"),
            chroma_port=int(os.getenv("CHROMA_PORT", 8000)) if os.getenv("CHROMA_PORT") else None
        )
        
    async def initialize(self):
        """Initialize all components."""
        try:
            # Start memory management
            await self.memory_pool.start()
            await self.memory_monitor.start()
            
            # Register cleanup callbacks
            self.memory_monitor.register_cleanup_callback(self._cleanup_cache)
            
            # Initialize connections
            await self._initialize_redis()
            await self._initialize_chromadb()
            await self._initialize_embedding_model()
            
            log_service_status(
                "database_manager",
                "info",
                "Successfully initialized database manager"
            )
        except Exception as e:
            log_service_status(
                "database_manager",
                "error",
                f"Failed to initialize database manager: {str(e)}"
            )
            raise
            
    async def _initialize_redis(self):
        """Initialize Redis connection."""
        async with self._redis_lock:
            try:
                self.redis_pool = redis.ConnectionPool(
                    host=self.config.redis_host,
                    port=self.config.redis_port,
                    db=0,
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=10,
                    socket_keepalive=True
                )
                
                # Test connection
                redis_client = redis.Redis(connection_pool=self.redis_pool)
                redis_client.ping()
                
                log_service_status(
                    "database_manager",
                    "info",
                    f"Connected to Redis at {self.config.redis_host}:{self.config.redis_port}"
                )
            except redis.RedisError as e:
                log_service_status(
                    "database_manager",
                    "error",
                    f"Redis connection error: {str(e)}"
                )
                raise
                
    async def _initialize_chromadb(self):
        """Initialize ChromaDB connection."""
        async with self._chroma_lock:
            try:
                settings = Settings(
                    chroma_api_impl="rest" if self.config.chroma_host else "local",
                    chroma_server_host=self.config.chroma_host,
                    chroma_server_http_port=self.config.chroma_port
                )
                
                self.chroma_db = ChromaDBClient(settings)
                if not self.chroma_db.connect():
                    raise RuntimeError("Failed to connect to ChromaDB")
                    
                log_service_status(
                    "database_manager",
                    "info",
                    "Connected to ChromaDB"
                )
            except Exception as e:
                log_service_status(
                    "database_manager",
                    "error",
                    f"ChromaDB connection error: {str(e)}"
                )
                raise
                
    async def _initialize_embedding_model(self):
        """Initialize embedding model."""
        async with self._embedding_lock:
            try:
                model_name = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
                self.embedding_model = SentenceTransformer(model_name)
                
                # Test embedding
                test_text = "Test embedding generation"
                _ = self.embedding_model.encode(test_text)
                
                log_service_status(
                    "database_manager",
                    "info",
                    f"Loaded embedding model: {model_name}"
                )
            except Exception as e:
                log_service_status(
                    "database_manager",
                    "error",
                    f"Embedding model error: {str(e)}"
                )
                raise
                
    async def _cleanup_cache(self):
        """Clean up cache when memory pressure is high."""
        self.cache.clear()
        if self.redis_pool:
            try:
                redis_client = redis.Redis(connection_pool=self.redis_pool)
                redis_client.flushdb()
            except Exception as e:
                log_service_status(
                    "database_manager",
                    "error",
                    f"Cache cleanup error: {str(e)}"
                )
                
    async def store_chat_history(
        self,
        chat_id: str,
        message: Union[str, Dict[str, Any]],
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Store chat history with memory-efficient handling."""
        try:
            # Validate input
            if isinstance(message, str):
                chat_entry = ChatMessage(
                    content=message,
                    metadata=metadata or {},
                    timestamp=datetime.now().timestamp()
                )
            else:
                chat_entry = ChatMessage(
                    content=message.get("content", ""),
                    metadata=message.get("metadata", {}) if metadata is None else metadata,
                    timestamp=message.get("timestamp", datetime.now().timestamp())
                )
            
            # Get memory object from pool
            mem_obj = await self.memory_pool.acquire()
            try:
                # Store in Redis
                redis_client = redis.Redis(connection_pool=self.redis_pool)
                chat_key = f"chat:{chat_id}"
                
                redis_client.lpush(chat_key, json.dumps(chat_entry.dict()))
                
                # Update cache
                cache_key = f"chat_history:{chat_id}"
                cached_history = self.cache.get(cache_key)
                if cached_history:
                    cached_history.append(chat_entry.dict())
                    self.cache.set(cache_key, cached_history)
                    
            finally:
                # Return memory object to pool
                await self.memory_pool.release(mem_obj)
                
        except Exception as e:
            log_service_status(
                "database_manager",
                "error",
                f"Error storing chat history: {str(e)}"
            )
            raise
            
    async def get_chat_history(
        self,
        chat_id: str,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get chat history with memory-efficient caching."""
        try:
            # Check cache first
            cache_key = f"chat_history:{chat_id}"
            cached_history = self.cache.get(cache_key)
            if cached_history:
                return cached_history[:limit] if limit else cached_history
                
            # Get from Redis
            redis_client = redis.Redis(connection_pool=self.redis_pool)
            chat_key = f"chat:{chat_id}"
            
            # Get memory object from pool
            mem_obj = await self.memory_pool.acquire()
            try:
                history = []
                entries = redis_client.lrange(chat_key, 0, limit - 1 if limit else -1)
                
                for entry_str in entries:
                    try:
                        history.append(json.loads(entry_str))
                    except json.JSONDecodeError:
                        log_service_status(
                            "database_manager",
                            "warning",
                            f"Invalid chat history entry: {entry_str}"
                        )
                        
                # Update cache
                self.cache.set(cache_key, history)
                return history
                
            finally:
                # Return memory object to pool
                await self.memory_pool.release(mem_obj)
                
        except Exception as e:
            log_service_status(
                "database_manager",
                "error",
                f"Error retrieving chat history: {str(e)}"
            )
            raise
            
    async def cleanup(self):
        """Clean up resources."""
        try:
            # Stop memory management
            await self.memory_pool.stop()
            await self.memory_monitor.stop()
            
            # Clear cache
            self.cache.clear()
            
            # Close database connections
            if self.redis_pool:
                self.redis_pool.disconnect()
                
            if self.chroma_db:
                self.chroma_db.disconnect()
                
        except Exception as e:
            log_service_status(
                "database_manager",
                "error",
                f"Cleanup error: {str(e)}"
            )
            raise
