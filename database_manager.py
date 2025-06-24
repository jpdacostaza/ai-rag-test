"""
DatabaseManager class for FastAPI LLM backend.
Handles Redis, ChromaDB, and embedding model management with enhanced logging.
"""

from typing import Optional, Union, Any, Dict, List
import os
import time
import asyncio
from datetime import datetime

import chromadb
import redis
from sentence_transformers import SentenceTransformer

from error_handler import RedisConnectionHandler
from human_logging import log_service_status
from utilities.validation import DatabaseConfig, ChatMessage, validate_query_params
from utilities.database_types import (
    DatabaseClient,
    CacheManager,
    ChromaDBClient,
    DatabaseManagerTypes as Types
)
from utilities.memory_pool import MemoryPool
from utilities.memory_monitor import MemoryPressureMonitor

class DatabaseManager:
    """Central database manager for Redis and ChromaDB operations with enhanced memory management."""

    def __init__(self):
        # Configuration validation
        self.config = DatabaseConfig(
            redis_host=os.getenv("REDIS_HOST", "localhost"),
            redis_port=int(os.getenv("REDIS_PORT", 6379)),
            chroma_host=os.getenv("CHROMA_HOST"),
            chroma_port=int(os.getenv("CHROMA_PORT", 8000)) if os.getenv("CHROMA_PORT") else None
        )
        
        # Database connections
        self.redis_pool: Optional[redis.ConnectionPool] = None
        self.chroma_client: Optional[ChromaDBClient] = None
        self.chroma_collection: Optional[Types.ChromaCollection] = None
        self.embedding_model: Optional[SentenceTransformer] = None
        
        # Memory management
        self.memory_pool = MemoryPool(max_size=1000)
        self.memory_monitor = MemoryPressureMonitor(
            warning_threshold=75.0,
            critical_threshold=90.0
        )
        self.cache_manager = CacheManager[Any](max_size=10000)
        
        # Locks for thread-safe operations
        self._redis_lock = Lock()
        self._chroma_lock = Lock()
        self._embedding_lock = Lock()
        
        # Initialize everything
        self._initialize_all()
        
    async def _initialize_all(self):
        """Initialize all components with proper error handling."""
        try:
            # Start memory management
            await self.memory_pool.start()
            await self.memory_monitor.start()
            
            # Register cleanup callbacks
            self.memory_monitor.register_cleanup_callback(self._handle_memory_pressure)
            
            # Initialize databases
            await self._initialize_databases()
            
        except Exception as e:
            log_service_status(
                "database_manager",
                "error",
                f"Initialization error: {str(e)}"
            )
            raise
            
    async def _initialize_databases(self):
        """Initialize all database connections with proper error handling."""
        try:
            await self._initialize_redis()
            await self._initialize_chromadb()
            await self._initialize_embedding_model()
            log_service_status("database_manager", "info", "Successfully initialized all databases")
        except Exception as e:
            log_service_status("database_manager", "error", f"Failed to initialize databases: {str(e)}")
            raise

    async def _initialize_redis(self):
        """Initialize Redis connection pool with Docker-optimized settings."""
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
                test_client = redis.Redis(connection_pool=self.redis_pool)
                test_client.ping()
                
                log_service_status(
                    "database_manager",
                    "info",
                    f"Connected to Redis at {self.config.redis_host}:{self.config.redis_port}"
                )
            except redis.RedisError as e:
                log_service_status("database_manager", "error", f"Redis connection error: {str(e)}")
                RedisConnectionHandler.handle_redis_error(e, "connect")
                raise
            except Exception as e:
                log_service_status("database_manager", "error", f"Unexpected Redis error: {str(e)}")
                RedisConnectionHandler.handle_redis_error(e, "connect_general")
                raise
                
    async def _initialize_chromadb(self):
        """Initialize ChromaDB client with proper error handling."""
        async with self._chroma_lock:
            try:
                settings = Settings(
                    chroma_api_impl="rest" if self.config.chroma_host else "local",
                    chroma_server_host=self.config.chroma_host,
                    chroma_server_http_port=self.config.chroma_port
                )
                
                self.chroma_client = chromadb.Client(settings)
                
                # Test connection by listing collections
                self.chroma_client.list_collections()
                
                log_service_status(
                    "database_manager",
                    "info",
                    "Successfully connected to ChromaDB"
                )
            except Exception as e:
                log_service_status("database_manager", "error", f"ChromaDB initialization error: {str(e)}")
                raise
                
    async def _initialize_embedding_model(self):
        """Initialize the embedding model with proper error handling."""
        async with self._embedding_lock:
            try:
                model_name = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
                self.embedding_model = SentenceTransformer(model_name)
                
                # Test model with a simple embedding
                test_text = "Test embedding generation"
                _ = self.embedding_model.encode(test_text)
                
                log_service_status(
                    "database_manager",
                    "info",
                    f"Successfully loaded embedding model: {model_name}"
                )
            except Exception as e:
                log_service_status("database_manager", "error", f"Embedding model initialization error: {str(e)}")
                raise

    def _initialize_chroma_collection(self):
        """Set up and access the ChromaDB collection."""
        collection_name = os.getenv("CHROMA_COLLECTION", "user_memory")
        self.chroma_collection = self.chroma_client.get_or_create_collection(collection_name)
        log_service_status(
            "CHROMADB",
            "ready",
            f"Successfully connected to ChromaDB and accessed collection '{collection_name}'",
        )

    def _verify_chroma_connection(self):
        """Verify ChromaDB connection by listing collections."""
        try:
            collections = self.chroma_client.list_collections()
            log_service_status(
                "CHROMADB", "ready", f"Found {len(collections)} existing collections"
            )
        except Exception as e:
            log_service_status("CHROMADB", "degraded", f"Could not list collections: {e}")

    def get_redis_client(self):
        """Get a Redis client from the connection pool."""
        try:
            if self.redis_pool is None:
                log_service_status(
                    "REDIS",
                    "reconnecting",
                    "Redis pool not available. Attempting to re-initialize.",
                )
                self._initialize_redis()
                if self.redis_pool is None:
                    return None

            client = redis.Redis(connection_pool=self.redis_pool)
            client.ping()
            return client
        except redis.RedisError as e:
            log_service_status(
                "REDIS", "reconnecting", f"Connection issue: {e}. Attempting to re-initialize."
            )
            self._initialize_redis()
            if self.redis_pool:
                try:
                    client = redis.Redis(connection_pool=self.redis_pool)
                    client.ping()
                    return client
                except redis.RedisError:
                    log_service_status(
                        "REDIS", "failed", "Failed to get a Redis client after re-initialization."
                    )
            return None

    def is_redis_available(self):
        """Check if Redis is available."""
        return self.get_redis_client() is not None

    def is_chromadb_available(self):
        """Check if ChromaDB is available."""
        return self.chroma_client is not None and self.chroma_collection is not None

    def is_embeddings_available(self):
        """Check if embedding model is available."""
        return self.embedding_model is not None

    def get_health_status(self):
        """Get health status of all database components."""
        redis_available = self.is_redis_available()
        return {
            "redis": {
                "available": redis_available,
            },
            "chromadb": {
                "available": self.is_chromadb_available(),
                "client": self.chroma_client is not None,
                "collection": self.chroma_collection is not None,
            },
            "embeddings": {
                "available": self.is_embeddings_available(),
                "model": self.embedding_model is not None,
            },
        }

    def execute_redis_operation(self, operation_func, operation_name="redis_op", max_retries=2):
        """Execute a Redis operation with automatic retry."""
        for attempt in range(max_retries + 1):
            try:
                redis_client = self.get_redis_client()
                if redis_client:
                    return operation_func(redis_client)
                else:
                    log_service_status(
                        "REDIS",
                        "failed",
                        f"Could not get Redis client for operation: {operation_name}",
                    )
                    if attempt < max_retries:
                        time.sleep(1)  # Wait before retrying
                        continue
                    return None
            except redis.RedisError as e:
                log_service_status(
                    "REDIS",
                    "warning",
                    f"Redis operation {operation_name} failed on attempt {attempt + 1}: {e}",
                )
                if attempt >= max_retries:
                    RedisConnectionHandler.handle_redis_error(e, operation_name)
                    return None
                time.sleep(1)  # Wait before retrying
        return None

    async def _handle_memory_pressure(self):
        """Handle high memory pressure situations."""
        try:
            # Clear Redis cache if available
            if self.redis_pool:
                redis_client = redis.Redis(connection_pool=self.redis_pool)
                await redis_client.flushdb()
                
            # Clear ChromaDB cache if available
            if hasattr(self.chroma_client, 'clear_cache'):
                self.chroma_client.clear_cache()
                
        except Exception as e:
            log_service_status(
                "database_manager",
                "error",
                f"Error handling memory pressure: {str(e)}"
            )
            
    async def cleanup(self):
        """Cleanup resources."""
        try:
            # Stop memory management
            await self.memory_pool.stop()
            await self.memory_monitor.stop()
            
            # Close database connections
            if self.redis_pool:
                self.redis_pool.disconnect()
            
            if self.chroma_client:
                self.chroma_client.close()
                
        except Exception as e:
            log_service_status(
                "database_manager",
                "error",
                f"Cleanup error: {str(e)}"
            )


# Global database manager instance
db_manager = DatabaseManager()


# Convenience functions for compatibility
def get_database_health():
    """Get health status of all database components."""
    return db_manager.get_health_status()


def get_cache(db_manager_instance, cache_key: str):
    """Get value from cache with explicit hit/miss logging."""
    import logging
    try:
        redis_client = db_manager_instance.get_redis_client()
        if redis_client:
            result = redis_client.get(cache_key)
            if result is not None:
                logging.info(f"[CACHE] ✅ Cache HIT for key: {cache_key}")
                return result
            else:
                logging.info(f"[CACHE] 🟡 Cache MISS for key: {cache_key}")
                return None
        else:
            logging.warning(f"[CACHE] ❌ Redis client unavailable for key: {cache_key}")
            return None
    except Exception as e:
        logging.error(f"[CACHE] ❌ Cache retrieval error for key {cache_key}: {e}")
        return None


def set_cache(db_manager_instance, cache_key: str, value: str, expire: int = 3600):
    """Set value in cache with explicit logging."""
    import logging
    try:
        redis_client = db_manager_instance.get_redis_client()
        if redis_client:
            redis_client.setex(cache_key, expire, value)
            logging.info(f"[CACHE] 💾 Cache SET for key: {cache_key} (expires in {expire}s)")
            return True
        else:
            logging.warning(f"[CACHE] ❌ Redis client unavailable, cannot set key: {cache_key}")
            return False
    except Exception as e:
        logging.error(f"[CACHE] ❌ Cache set error for key {cache_key}: {e}")
        return False


def get_chat_history(user_id: str, limit: int = 10):
    """Get chat history for user from Redis."""
    def get_operation(redis_client):
        chat_key = f"chat_history:{user_id}"
        history_entries = redis_client.lrange(chat_key, 0, limit - 1)
        
        # Parse entries back to dict format
        history = []
        if history_entries:
            for entry_str in history_entries:
                try:
                    history.append(json.loads(entry_str))
                except json.JSONDecodeError:
                    continue
                
        return history
    
    result = db_manager.execute_redis_operation(get_operation, "get_chat_history")
    return result if result is not None else []


def store_chat_history(user_id: str, message: str, response: str):
    """Store chat history in Redis."""
    def store_operation(redis_client):
        # Create chat history entry
        chat_entry = {
            "timestamp": time.time(),
            "message": message,
            "response": response
        }
        
        # Store in Redis list for this user
        chat_key = f"chat_history:{user_id}"
        redis_client.lpush(chat_key, json.dumps(chat_entry))
        
        # Keep only last 100 messages per user
        redis_client.ltrim(chat_key, 0, 99)
        
        # Set expiration (30 days)
        redis_client.expire(chat_key, 2592000)
        
        return True
    
    return db_manager.execute_redis_operation(store_operation, "store_chat_history") is not None


def get_embedding(text: str):
    """Get embedding for text."""
    try:
        if db_manager.embedding_model:
            # Get the embedding and ensure it's a proper array
            embedding = db_manager.embedding_model.encode([text])[0]
            return embedding
        return None
    except Exception as e:
        log_service_status("EMBEDDINGS", "warning", f"Failed to generate embedding: {e}")
        return None


def index_user_document(user_id: str, content: str, metadata: Optional[dict] = None):
    """Index user document in ChromaDB."""
    try:
        if not db_manager.chroma_collection:
            log_service_status("CHROMADB", "warning", "ChromaDB collection not available")
            return False
            
        if metadata is None:
            metadata = {}
            
        # Add user_id to metadata
        metadata.update({
            "user_id": user_id,
            "timestamp": time.time(),
            "type": "user_document"
        })
        
        # Generate embedding using our embedding model
        embedding = get_embedding(content)
        if embedding is None:
            log_service_status("EMBEDDINGS", "warning", "Could not generate embedding for document")
            return False
            
        # Create unique document ID
        doc_id = f"user_{user_id}_{int(time.time())}"
        
        # Add to ChromaDB
        db_manager.chroma_collection.add(
            documents=[content],
            embeddings=[embedding.tolist()],
            metadatas=[metadata],
            ids=[doc_id]
        )
        
        log_service_status("CHROMADB", "info", f"Indexed document for user {user_id}")
        return True
        
    except Exception as e:
        log_service_status("CHROMADB", "warning", f"Failed to index document: {e}")
        return False


def retrieve_user_memory(user_id: str, query: str, limit: int = 5):
    """Retrieve user memory from ChromaDB based on semantic similarity."""
    log_service_status("DATABASE_MANAGER", "info", f"retrieve_user_memory called with user_id={user_id}, query='{query[:50]}...', limit={limit}")
    
    try:
        if not db_manager.chroma_collection:
            log_service_status("CHROMADB", "warning", "ChromaDB collection not available")
            return []
            
        # Generate and validate embedding
        query_embedding = _get_validated_embedding(query)
        if query_embedding is None:
            return []
            
        # Search ChromaDB for similar documents
        results = _query_chromadb(query_embedding, user_id, limit)
        
        # Format and return results
        memories = _format_memory_results(results)
        log_service_status("CHROMADB", "info", f"Retrieved {len(memories)} memories for user {user_id}")
        return memories
        
    except Exception as e:
        log_service_status("CHROMADB", "warning", f"Failed to retrieve user memory: {e}")
        return []


def _get_validated_embedding(query: str):
    """Generate and validate embedding for the query."""
    query_embedding = get_embedding(query)
    if query_embedding is None:
        log_service_status("DATABASE_MANAGER", "error", "Failed to generate embedding - got None")
        return None
    
    # Check if embedding is valid - avoid NumPy array truth value errors
    embedding_valid = _validate_embedding(query_embedding)
    
    if not embedding_valid:
        log_service_status("EMBEDDINGS", "warning", f"Could not generate embedding for query: '{query[:50]}...'")
        return None
        
    # Convert embedding to list format for ChromaDB
    return _convert_embedding_to_list(query_embedding)


def _validate_embedding(embedding):
    """Validate that the embedding is properly formatted."""
    if embedding is None:
        return False
    
    if hasattr(embedding, 'size'):
        # For NumPy arrays, check size safely
        try:
            return embedding.size > 0
        except ValueError:
            # Handle NumPy array truth value error
            return False
    elif hasattr(embedding, '__len__'):
        return len(embedding) > 0
    else:
        return False


def _convert_embedding_to_list(embedding):
    """Convert embedding to list format for ChromaDB."""
    if embedding is None:
        log_service_status("EMBEDDINGS", "warning", "Query embedding is None")
        return None
        
    try:
        if hasattr(embedding, 'tolist'):
            return embedding.tolist()
        elif hasattr(embedding, '__iter__'):
            return list(embedding)
        else:
            log_service_status("EMBEDDINGS", "warning", "Embedding format not supported")
            return None
    except Exception as e:
        log_service_status("EMBEDDINGS", "warning", f"Failed to convert embedding to list: {e}")
        return None


def _query_chromadb(embedding_list, user_id: str, limit: int):
    """Query ChromaDB for similar documents."""
    log_service_status("DATABASE_MANAGER", "debug", f"Querying ChromaDB with user_id filter: {user_id}")
    
    try:
        results = db_manager.chroma_collection.query(
            query_embeddings=[embedding_list],
            n_results=limit,
            where={"user_id": user_id}  # Filter by user_id
        )
        log_service_status("DATABASE_MANAGER", "debug", "ChromaDB query completed successfully")
        return results
    except Exception as query_error:
        log_service_status("DATABASE_MANAGER", "error", f"ChromaDB query failed: {type(query_error).__name__}: {query_error}")
        import traceback
        log_service_status("DATABASE_MANAGER", "error", f"Full traceback: {traceback.format_exc()}")
        raise query_error


def _format_memory_results(results):
    """Format ChromaDB results into memory objects."""
    memories = []
    if not results or not results.get('documents'):
        return memories
        
    documents_list = results.get('documents')
    if not documents_list or len(documents_list) == 0:
        return memories
        
    documents = documents_list[0]
    metadatas_list = results.get('metadatas')
    metadatas = metadatas_list[0] if metadatas_list and len(metadatas_list) > 0 else []
    distances_list = results.get('distances')
    distances = distances_list[0] if distances_list and len(distances_list) > 0 else []
    ids_list = results.get('ids')
    ids = ids_list[0] if ids_list and len(ids_list) > 0 else []
    
    for i, doc in enumerate(documents):
        memory = {
            "content": doc,
            "metadata": metadatas[i] if i < len(metadatas) else {},
            "similarity": 1 - distances[i] if i < len(distances) else 0.0,
            "id": ids[i] if i < len(ids) else f"mem_{i}"
        }
        memories.append(memory)
    
    return memories
