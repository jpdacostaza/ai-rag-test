"""
DatabaseManager class for FastAPI LLM backend.
Handles Redis, chromadb, and embedding model management with enhanced logging.
"""

from typing import Optional, Union, Any, Dict, List, TypedDict, cast, Sequence, Protocol
import os
import time
import json
import asyncio
from core.unified_logging import get_logger
import logging
import functools
from datetime import datetime

import chromadb
from chromadb.config import Settings
import redis.asyncio as redis
from sentence_transformers import SentenceTransformer
from numpy.typing import NDArray
import numpy as np

from core.error_handler import RedisConnectionHandler
from core.unified_logging import get_logger, log_service_status
from utilities.validation import DatabaseConfig, ChatMessage, validate_query_params
from utilities.cache_manager import CacheManager
from utilities.ai_tools import chunk_text
from utilities.connection_factory import (
    get_connection_factory,
    get_redis,
    get_chroma,
    RedisConfig,
    ChromaConfig
)
from core.metrics import (
    METRICS_ENABLED,
    chroma_operation_errors_total,  # still used for store/query error paths
)
from utilities.enhanced_connection_pooling import pool_manager, get_enhanced_redis_pool
from services.db_components.redis_ops import execute_redis_operation as redis_execute
from services.db_components.chroma_ops import query_collection as chroma_query_collection

# Use feature registry for error patterns
from utilities.feature_registry import register_import_attempt

ERROR_PATTERNS_AVAILABLE = register_import_attempt(
    'error_patterns', 
    lambda: __import__('utilities.error_patterns', fromlist=['handle_database_errors']),
    'Error handling patterns'
)
if ERROR_PATTERNS_AVAILABLE:
    from utilities.error_patterns import (
        handle_database_errors, handle_service_errors, handle_cache_errors, handle_memory_errors
    )
else:
    # Simple fallback decorators following best practices
    
    def handle_database_errors(func):
        """Handle errors in database functions."""
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                logger = get_logger(__name__)
                logger.error(
                    "Database error",
                    extra={"function": func.__name__, "error": str(e)}
                )
                return None
        return wrapper

    def handle_service_errors(func):
        """Handle errors in service functions."""
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                logger = get_logger(__name__)
                logger.error(
                    "Service error",
                    extra={"function": func.__name__, "error": str(e)}
                )
                return None
        return wrapper

    def handle_memory_errors(operation_name=None):
        """Handle errors in memory functions with optional operation name parameter."""
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    op_name = operation_name or func.__name__
                    logger = get_logger(__name__)
                    logger.error(
                        "Memory error",
                        extra={"operation": op_name, "error": str(e)}
                    )
                    return False if "index" in op_name else []
            return wrapper
        return decorator

# Alert manager integration using feature registry
ALERT_MANAGER_AVAILABLE = register_import_attempt(
    'alert_manager', 
    lambda: __import__('utilities.alert_manager', fromlist=['alert_memory_pressure']),
    'Alert management system'
)
if ALERT_MANAGER_AVAILABLE:
    from utilities.alert_manager import alert_memory_pressure, alert_service_down
else:
    # Fallback if alert manager is not available
    async def alert_memory_pressure(percentage: float, component: str = "database"):
        pass

    async def alert_service_down(service_name: str, duration_seconds: float):
        pass

# Global database manager instance - initialized at module import time
db_manager = None

# Initialize global cache manager
_cache_manager = None


def initialize_database():
    """Initialize the global database manager instance.
    
    This function ensures the database manager is instantiated only once.
    It should be called early in the application startup sequence.
    """
    global db_manager
    if db_manager is None:
        db_manager = DatabaseManager()
    return db_manager


class ChromaClientProtocol(Protocol):
    """Protocol defining the interface for ChromaDB client interactions.
    
    This protocol defines the required methods for ChromaDB client integration,
    allowing for type checking and interface consistency across the application.
    It enables testing with mock implementations and abstracts the underlying ChromaDB client.
    """

    def get_or_create_collection(self, name: str, **kwargs: Any) -> "ChromaCollectionProtocol": 
        """Get an existing collection or create a new one with the specified name.
        
        Args:
            name: The name of the collection to get or create
            **kwargs: Additional arguments to pass to the collection creation
            
        Returns:
            A ChromaCollection object that implements the ChromaCollectionProtocol
        """
        ...
        
    def list_collections(self) -> List[str]: 
        """List all available collections in the ChromaDB instance.
        
        Returns:
            A list of collection names as strings
        """
        ...
        
    def heartbeat(self) -> bool: 
        """Check if the ChromaDB service is alive and responding.
        
        Returns:
            True if the service is available, False otherwise
        """
        ...


class ChromaCollectionProtocol(Protocol):
    """Protocol defining the interface for ChromaDB collections.
    
    This protocol defines the required methods for interacting with ChromaDB collections,
    ensuring type checking and consistent interface across the application.
    It abstracts the underlying ChromaDB collection implementation and enables 
    testing with mock implementations.
    """

    def add(
        self, embeddings: List[List[float]], documents: List[str], metadatas: List[Dict[str, Any]], ids: List[str]
    ) -> None: 
        """Add documents with their embeddings and metadata to the collection.
        
        Args:
            embeddings: List of embedding vectors for the documents
            documents: List of document texts to be stored
            metadatas: List of metadata dictionaries for each document
            ids: List of unique identifiers for each document
        
        Returns:
            None
        """
        ...
        
    def query(self, query_embeddings: List[List[float]], n_results: int, **kwargs: Any) -> Dict[str, List[Any]]: 
        """Query the collection for the most similar documents to the query embeddings.
        
        Args:
            query_embeddings: List of embedding vectors to query against
            n_results: Number of top results to return
            **kwargs: Additional query parameters (e.g., where filters)
        
        Returns:
            Dictionary with keys 'documents', 'metadatas', 'distances', and 'ids'
        """
        ...


class ComponentHealth(TypedDict):
    """Type definition for health status of a database component.
    
    Used to represent the health status of individual database components
    such as Redis, ChromaDB, or the embedding model service.
    """

    status: str  # Status of the component (e.g., 'ok', 'error', 'degraded')
    details: str  # Additional details about the component's status


class DatabaseHealth(TypedDict):
    """Type definition for overall database health status.
    
    Aggregates the health status of all database components (Redis, ChromaDB, embeddings)
    for system monitoring and health checks.
    """

    redis: ComponentHealth      # Health status of Redis
    chromadb: ComponentHealth   # Health status of ChromaDB
    embeddings: ComponentHealth # Health status of embedding model


class ChromaResults(TypedDict):
    """Type definition for raw results returned from ChromaDB queries.
    
    Represents the structure of results returned directly from ChromaDB's
    query method, before any additional processing.
    """

    documents: List[List[str]]               # Nested list of document contents
    metadatas: List[List[Dict[str, Any]]]    # Nested list of metadata dictionaries
    distances: List[List[float]]             # Nested list of distance scores
    ids: List[List[str]]                     # Nested list of document IDs


class Match(TypedDict):
    """Type definition for a single document match from a memory query.
    
    Represents a processed result from a ChromaDB query, containing
    the document content, metadata, and distance score.
    """

    document: str               # The document content
    metadata: Dict[str, Any]    # Metadata associated with the document
    distance: float             # Distance/similarity score


class QueryResponse(TypedDict):
    """Type definition for the response to a memory query.
    
    Used as the standardized format for returning memory query results
    to the application, containing a list of matched documents.
    """

    matches: List[Match]  # List of matched documents with metadata and scores


class DatabaseManager:
    """Database manager class for handling Redis and chromadb connections."""

    def __init__(self):
        """Initialize database manager."""
        # Database clients
        self.redis_client: Optional[redis.Redis] = None
        self.chroma_client: Optional[ChromaClientProtocol] = None
        self.chroma_collection: Optional[ChromaCollectionProtocol] = None
        self.embedding_model: Optional[SentenceTransformer] = None

        # Connection factory for centralized connection management
        self.connection_factory = get_connection_factory()

        # Cache management
        self.cache_manager = CacheManager[Any](max_size=10000)

        # Locks for thread-safe operations
        self._redis_lock = asyncio.Lock()
        self._chroma_lock = asyncio.Lock()
        self._embedding_lock = asyncio.Lock()

        # Initialization status tracking
        self._initialized = False
        self._initialization_failed = False

        # Service health tracking
        self._service_start_times = {}
        self._service_downtime_alerts = {}

        # Enhanced connection pooling
        self._enhanced_redis_pool = None
        self._use_enhanced_pooling = os.getenv("USE_ENHANCED_POOLING", "true").lower() == "true"
        log_service_status("database_manager", "info", "Database manager created on module import")

    async def _initialize_all(self):
        """Initialize all components with proper error handling."""
        redis_success = False
        try:
            await self._initialize_redis()
            redis_success = True
        except Exception as e:
            log_service_status(
                "database_manager",
                "warning",
                f"Redis initialization failed: {str(e)}. Continuing with other components.")
            # Don't set _initialization_failed = True or return early
            # Redis can be reconnected later, but we should still initialize embeddings and ChromaDB

        # Initialize Chroma and Embeddings independently - they are optional and will handle their own errors/retries
        await self._initialize_chroma()
        await self._initialize_embedding_model()

        self._initialized = True
        if redis_success:
            log_service_status(
                "database_manager", "info", "Database components initialization process completed successfully."
            )
        else:
            log_service_status(
                "database_manager", "info", "Database components initialization completed (Redis connection pending)."
            )

    async def _initialize_redis(self):
        """Initialize Redis client using ConnectionFactory or enhanced pooling."""
        log_service_status("database_manager", "info", "Initializing Redis connection...")
        
        # Try enhanced pooling first if enabled
        if self._use_enhanced_pooling:
            try:
                self._enhanced_redis_pool = await get_enhanced_redis_pool(
                    pool_name="database_manager",
                    max_size=int(os.getenv("REDIS_MAX_CONNECTIONS", "50")),
                    min_size=int(os.getenv("REDIS_MIN_CONNECTIONS", "5"))
                )
                log_service_status("redis", "info", "Enhanced Redis pooling initialized successfully")
                return
            except Exception as e:
                log_service_status("redis", "warning", f"Enhanced pooling failed, falling back to ConnectionFactory: {e}")
        
        # Fallback to ConnectionFactory
        try:
            # Use ConnectionFactory for Redis connection
            self.redis_client = await self.connection_factory.create_redis_connection(connection_name="database_manager")
            
            if self.redis_client:
                log_service_status("redis", "info", "Redis initialized successfully via ConnectionFactory")
            else:
                log_service_status("redis", "warning", "Redis initialization failed - check ConnectionFactory logs")
                # Don't raise exception to allow other components to initialize
                
        except Exception as e:
            log_service_status("redis", "error", f"Redis ConnectionFactory initialization error: {str(e)}")
            # Allow initialization to continue without Redis

    async def _initialize_chroma(self):
        """Initialize ChromaDB client using ConnectionFactory."""
        log_service_status("database_manager", "info", "Initializing ChromaDB connection via ConnectionFactory...")
        
        try:
            # Use ConnectionFactory for ChromaDB connection
            self.chroma_client = await self.connection_factory.create_chroma_connection(connection_name="database_manager")
            
            if self.chroma_client:
                # Initialize collection
                collection_name = os.getenv("CHROMA_COLLECTION", "default")
                self.chroma_collection = self.chroma_client.get_or_create_collection(
                    name=collection_name, 
                    metadata={"description": "Default vector store for embeddings"}
                )
                log_service_status("chromadb", "info", "ChromaDB initialized successfully via ConnectionFactory")
            else:
                log_service_status("chromadb", "warning", "ChromaDB initialization failed - check ConnectionFactory logs")
                self.chroma_client = None
                self.chroma_collection = None
                
        except Exception as e:
            log_service_status("chromadb", "error", f"ChromaDB ConnectionFactory initialization error: {str(e)}")
            self.chroma_client = None
            self.chroma_collection = None

    async def _initialize_embedding_model(self):
        """Initialize the embedding model with automatic downloading if needed."""
        if os.getenv("DISABLE_EMBEDDINGS", "false").lower() == "true":
            log_service_status("embeddings", "info", "Embeddings are disabled via environment variable.")
            self.embedding_model = None
            return
        # Delegate to dedicated component for embedding initialization
        try:
            from config.config_unified import EMBEDDING_MODEL, EMBEDDING_PROVIDER
            from services.db_components.embeddings_init import initialize_embedding
            model_name = EMBEDDING_MODEL
            provider = EMBEDDING_PROVIDER
            log_service_status(
                "embeddings",
                "info",
                f"Initializing embedding model '{model_name}' via embeddings_init component (provider={provider})"
            )
            self.embedding_model = await initialize_embedding(model_name, provider)
            if self.embedding_model is None:
                log_service_status(
                    "embeddings",
                    "warning",
                    f"Embedding model '{model_name}' unavailable after initialization attempt (provider={provider})"
                )
        except Exception as e:  # pragma: no cover
            log_service_status("embeddings", "error", f"Embedding init component failure: {e}")
            self.embedding_model = None

    # Legacy embedding initialization helper methods removed; logic moved to services/db_components/embeddings_init.py

    def _initialize_chroma_collection(self):
        """Set up and access the chromadb collection."""
        if not self.chroma_client:
            log_service_status("chromadb", "error", "chromadb client not initialized")
            return

        collection_name = os.getenv("CHROMA_COLLECTION", "user_memory")
        self.chroma_collection = self.chroma_client.get_or_create_collection(collection_name)
        log_service_status(
            "chromadb",
            "ready",
            f"Successfully connected to chromadb and accessed collection '{collection_name}'")

    def _verify_chroma_connection(self):
        """Verify chromadb connection by listing collections."""
        if not self.chroma_client:
            log_service_status("chromadb", "error", "chromadb client not initialized")
            return

        try:
            collections = self.chroma_client.list_collections()
            log_service_status("chromadb", "ready", f"Found {len(collections)} existing collections")
        except Exception as e:
            log_service_status("chromadb", "degraded", f"Could not list collections: {e}")

    async def get_redis_client(self):
        """Get a Redis client from the connection pool (legacy interface)."""
        try:
            if self.redis_client is None:
                log_service_status(
                    "REDIS",
                    "reconnecting",
                    "Redis client not available. Attempting to re-initialize via ConnectionFactory.")
                await self._initialize_redis()
                if self.redis_client is None:
                    return None

            # Test connection
            await self.redis_client.ping()
            return self.redis_client
        except Exception as e:
            log_service_status("REDIS", "reconnecting", f"Connection issue: {e}. Attempting to re-initialize.")
            await self._initialize_redis()
            if self.redis_client:
                try:
                    await self.redis_client.ping()
                    return self.redis_client
                except Exception:
                    log_service_status("REDIS", "failed", "Failed to get a Redis client after re-initialization.")
            return None

    def get_redis_context(self):
        """Get Redis context manager for modern usage."""
        return get_redis("database_manager")

    async def is_redis_available(self):
        """Check if Redis is available (enhanced pooling or legacy)."""
        # Check enhanced pooling first
        if self._enhanced_redis_pool:
            try:
                async with self._enhanced_redis_pool.get_connection() as redis_client:
                    await redis_client.ping()
                    return True
            except Exception:
                return False
        
        # Fallback to legacy client check
        client = await self.get_redis_client()
        return client is not None

    async def is_chromadb_available(self):
        """Check if chromadb is available."""
        try:
            if self.chroma_client is None or self.chroma_collection is None:
                return False
            self.chroma_client.heartbeat()
            return True
        except Exception:
            return False

    def is_embeddings_available(self):
        """Check if embedding model is available."""
        return self.embedding_model is not None

    async def get_health_status(self):
        """Get health status of all database components with enhanced metrics."""
        redis_available = await self.is_redis_available()
        chroma_available = await self.is_chromadb_available()
        embeddings_available = self.is_embeddings_available()

        # Enhanced Redis status with pool metrics
        redis_status = {
            "status": "healthy" if redis_available else "unhealthy",
            "details": "Connected and responsive" if redis_available else "Not available",
        }
        
        # Add pool statistics if using enhanced pooling
        if self._enhanced_redis_pool:
            try:
                pool_stats = self._enhanced_redis_pool.get_stats()
                redis_status["pool_stats"] = pool_stats
                redis_status["pooling"] = "enhanced"
            except Exception as e:
                redis_status["pool_error"] = str(e)
        else:
            redis_status["pooling"] = "legacy"

        return {
            "redis": redis_status,
            "chromadb": {
                "status": "healthy" if chroma_available else "degraded",
                "details": "Connected and responsive" if chroma_available else "Not available",
            },
            "embeddings": {
                "status": "healthy" if embeddings_available else "degraded",
                "details": "Model loaded and ready" if embeddings_available else "Not available",
            },
            "connection_factory": {
                "status": "active",
                "connections": self.connection_factory.get_health_status()
            }
        }

    async def execute_redis_operation(self, operation: Any, operation_name: str) -> Any:
        """Execute Redis operation using enhanced pooling or fallback to legacy method."""
        if self._enhanced_redis_pool:
            # Use enhanced connection pooling
            try:
                async with self._enhanced_redis_pool.get_connection() as redis_client:
                    result = await operation(redis_client)
                    return result
            except Exception as e:
                log_service_status("redis", "error", f"Enhanced pool operation '{operation_name}' failed: {e}")
                # Only fall back if it's a connection-related issue, not a Redis operation error
                if "connection" in str(e).lower() or "pool" in str(e).lower():
                    log_service_status("redis", "warning", f"Falling back to legacy method for '{operation_name}'")
                else:
                    # Re-raise non-connection errors to avoid duplicate execution
                    raise
        
        # Fallback to legacy method (only for connection issues or when enhanced pooling not available)
        async def reinit():
            await self._initialize_redis()
        return await redis_execute(self.redis_client, self._redis_lock, operation, operation_name, reinit)

    async def _handle_memory_pressure(self):
        """Enhanced memory pressure handling with connection pool optimization."""
        try:
            # If using enhanced pooling, let the pool manager handle it
            if self._enhanced_redis_pool:
                # Get current memory usage
                import psutil
                memory = psutil.virtual_memory()
                
                if memory.percent > 90.0:
                    log_service_status("database_manager", "warning", 
                                     f"Critical memory pressure: {memory.percent:.1f}% - triggering emergency cleanup")
                    
                    # Trigger pool cleanup
                    await self._enhanced_redis_pool._cleanup_stale_connections()
                    
                    # Clear local caches
                    self.cache_manager.clear()
                    
                    return
            
            # Legacy memory pressure handling
            # Clear Redis cache if available
            if self.redis_client:
                await self.redis_client.flushdb()

            # Clear cache manager
            self.cache_manager.clear()

        except Exception as e:
            log_service_status("database_manager", "error", f"Error handling memory pressure: {str(e)}")

    async def cleanup(self):
        """Clean up database connections including enhanced pools."""
        try:
            # Cleanup enhanced Redis pool first
            if self._enhanced_redis_pool:
                await self._enhanced_redis_pool.cleanup()
                self._enhanced_redis_pool = None
                log_service_status("database_manager", "info", "Enhanced Redis pool cleaned up")

            # Legacy Redis cleanup
            if self.redis_client:
                await self._redis_lock.acquire()
                try:
                    await self.redis_client.aclose()
                finally:
                    self._redis_lock.release()

            if self.chroma_client:
                await self._chroma_lock.acquire()
                try:
                    # Free up resources, actual cleanup will be handled by the chromadb server
                    self.chroma_client = None
                    self.chroma_collection = None
                finally:
                    self._chroma_lock.release()

            if self.embedding_model:
                await self._embedding_lock.acquire()
                try:
                    # Clear any GPU memory if applicable
                    del self.embedding_model
                    self.embedding_model = None
                finally:
                    self._embedding_lock.release()

            log_service_status("database_manager", "info", "Database connections cleaned up successfully")
        except Exception as e:
            log_service_status("database_manager", "error", f"Error during cleanup: {str(e)}")
            raise

    async def get_embedding(self, text: str) -> Optional[List[float]]:
        """Get embedding using embedding provider abstraction."""
        try:
            from services.embedding_provider import get_embedding_provider
            provider = get_embedding_provider()
            embedding = await provider.embed_text(text)
            if embedding is None:
                log_service_status("EMBEDDINGS", "warning", "Embedding provider returned None")
            return embedding
        except Exception as e:  # pragma: no cover
            log_service_status("EMBEDDINGS", "error", f"Embedding retrieval failed: {e}")
            return None

    async def get_chat_history(self, chat_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get chat history from Redis."""

        async def get_operation(redis_client: redis.Redis) -> List[Dict[str, Any]]:
            """
            Inner operation function to retrieve chat history from Redis.
            
            Args:
                redis_client (redis.Redis): Redis client instance
                
            Returns:
                List[Dict[str, Any]]: List of chat history entries
            """
            chat_key = f"chat:{chat_id}"
            try:
                # lrange returns a list of bytes or str
                entries = await redis_client.lrange(chat_key, 0, limit - 1)
                if not isinstance(entries, list):
                    log_service_status("redis", "warning", f"Cache miss - no history found for chat_id: {chat_id}")
                    return []

                if len(entries) == 0:
                    log_service_status("redis", "info", f"Cache miss - empty history for chat_id: {chat_id}")
                else:
                    log_service_status(
                        "redis", "info", f"Cache hit - retrieved {len(entries)} messages for chat_id: {chat_id}"
                    )

                history = []
                for entry in entries:
                    try:
                        if isinstance(entry, bytes):
                            entry_str = entry.decode("utf-8")
                        else:
                            entry_str = entry
                        history.append(json.loads(entry_str))
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        continue
                return history
            except redis.RedisError as e:
                log_service_status(
                    "redis",
                    "error",
                    f"Cache error - failed to get history for chat_id: {chat_id}, error: {str(e)}"
                )
                return []

        result = await self.execute_redis_operation(get_operation, "get_chat_history")
        return result if result is not None else []

    async def store_chat_entry(self, chat_id: str, chat_entry: Dict[str, Any]) -> bool:
        """Store a chat entry in Redis."""

        async def store_operation(redis_client: redis.Redis) -> bool:
            """
            Inner operation function to store a chat entry in Redis.
            
            Args:
                redis_client (redis.Redis): Redis client instance
                
            Returns:
                bool: True if operation completed successfully
            """
            chat_key = f"chat:{chat_id}"
            await redis_client.lpush(chat_key, json.dumps(chat_entry))
            log_service_status(
                "redis",
                "info",
                f"Cache write - stored message for chat_id: {chat_id}, role: {chat_entry.get('role', 'unknown')}")
            return True

        return await self.execute_redis_operation(store_operation, "store_chat") or False

    async def store_vector_data(self, text: str, metadata: Dict[str, Any]) -> bool:
        """Store text and metadata in vector database."""
        if not self.chroma_collection:
            log_service_status("chromadb", "error", "ChromaDB collection not available for vector storage")
            return False

        # Get embedding
        embedding = await self.get_embedding(text)
        if not embedding:
            log_service_status("chromadb", "error", "Failed to generate embedding for text")
            return False

        # Add to chromadb
        try:
            doc_id = str(int(time.time() * 1000000))  # Use microsecond timestamp for unique ID
            self.chroma_collection.add(
                embeddings=[embedding], 
                documents=[text], 
                metadatas=[metadata], 
                ids=[doc_id]
            )
            log_service_status(
                "memory",
                "info",
                f"Vector data stored successfully - doc_id: {doc_id}, metadata: {metadata}"
            )
            return True
        except Exception as e:
            log_service_status("chromadb", "error", f"Failed to store vector data: {str(e)}")
            return False

    async def query_chroma(self, query_text: str, n_results: int = 5) -> Optional[Dict[str, Any]]:
        """Query Chroma using extracted chroma_ops helper with metrics."""
        if not self.chroma_collection or not self.embedding_model:
            log_service_status("chromadb", "error", "chromadb collection or embedding model not available")
            return None
        results = await chroma_query_collection(self.chroma_collection, self.get_embedding, query_text, n_results)
        if not results or not isinstance(results, dict):
            log_service_status("memory", "warning", f"Memory miss - no results found for query: '{query_text[:50]}...'")
            return None
        try:
            num_results = len(results.get("documents", [[]])[0])
        except Exception:
            num_results = 0
        if num_results == 0:
            log_service_status("memory", "info", f"Memory miss - no matches for query: '{query_text[:50]}...'")
        else:
            log_service_status("memory", "info", f"Memory hit - found {num_results} matches for query: '{query_text[:50]}...'")
        return {
            "matches": (
                [
                    {"document": doc, "metadata": meta, "distance": dist}
                    for doc, meta, dist in zip(
                        results.get("documents", [[]])[0],
                        results.get("metadatas", [[{}]])[0],
                        results.get("distances", [[0.0]])[0])
                ]
                if results.get("documents")
                else []
            )
        }

    def get_cache(self) -> CacheManager[Any]:
        """Get the cache manager instance."""
        return self.cache_manager

    def clear_cache(self) -> None:
        """Clear the cache manager."""
        log_service_status("cache", "info", "Cache cleared - all entries removed")
        self.cache_manager.clear()

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return self.cache_manager.get_stats()

    async def monitor_service_health(self) -> None:
        """Monitor service health and trigger alerts for downtime."""
        services_to_check = {
            "redis": self._check_redis_health,
            "chromadb": self._check_chromadb_health,
            "embeddings": self._check_embeddings_health,
        }

        current_time = time.time()

        for service_name, health_check in services_to_check.items():
            try:
                is_healthy = await health_check()

                if is_healthy:
                    # Service is healthy - reset any tracking
                    if service_name in self._service_start_times:
                        del self._service_start_times[service_name]
                    if service_name in self._service_downtime_alerts:
                        del self._service_downtime_alerts[service_name]
                else:
                    # Service is down - track downtime
                    if service_name not in self._service_start_times:
                        self._service_start_times[service_name] = current_time

                    downtime_duration = current_time - self._service_start_times[service_name]

                    # Check if we should send alert (don't spam alerts)
                    last_alert_time = self._service_downtime_alerts.get(service_name, 0)
                    if current_time - last_alert_time > 300:  # 5 minutes between alerts
                        await alert_service_down(service_name, downtime_duration)
                        self._service_downtime_alerts[service_name] = current_time

            except Exception as e:
                log_service_status("health_monitor", "error", f"Error checking {service_name} health: {e}")

    async def _check_redis_health(self) -> bool:
        """Check Redis health."""
        try:
            if not self.redis_client:
                return False
            await self.redis_client.ping()
            return True
        except Exception:
            return False

    async def _check_chromadb_health(self) -> bool:
        """Check ChromaDB health."""
        try:
            if not self.chroma_client:
                return False
            # Try to list collections as a health check
            await asyncio.to_thread(self.chroma_client.list_collections)
            return True
        except Exception:
            return False

    async def _check_embeddings_health(self) -> bool:
        """Check embeddings model health."""
        try:
            if not self.embedding_model:
                return False
            # Try a simple embedding generation as a health check
            embedding = await self.get_embedding("test")
            return embedding is not None
        except Exception:
            return False

    def is_initialized(self) -> bool:
        """Check if the database manager is fully initialized."""
        return self._initialized

    def initialization_failed(self) -> bool:
        """Check if initialization failed."""
        return self._initialization_failed

    async def ensure_initialized(self) -> bool:
        """Ensure the database manager is initialized, retry if needed."""
        if self._initialized:
            return True

        if self._initialization_failed:
            # Try to reinitialize
            self._initialization_failed = False
            try:
                await self._initialize_all()
                return self._initialized
            except Exception as e:
                log_service_status("database_manager", "error", f"Reinitialization failed: {str(e)}")
                return False

        # If not initialized and initialization hasn't failed, try to initialize
        if not self._initialized:
            try:
                await self._initialize_all()
                return self._initialized
            except Exception as e:
                log_service_status("database_manager", "error", f"Initial initialization failed: {str(e)}")
                self._initialization_failed = True
                return False

        return self._initialized


# Global database manager instance
db_manager: Optional[DatabaseManager] = None


def create_db_manager() -> DatabaseManager:
    """Create database manager instance synchronously."""
    try:
        return DatabaseManager()
    except Exception as e:
        log_service_status("database_manager", "error", f"Failed to create database manager: {str(e)}")
        raise


async def initialize_database() -> Optional[DatabaseManager]:
    """Initialize the global database manager."""
    global db_manager
    if db_manager is None:
        try:
            db_manager = create_db_manager()
            # Wait for async initialization to complete
            await db_manager.ensure_initialized()
        except Exception as e:
            log_service_status("database_manager", "error", f"Failed to initialize database manager: {str(e)}")
            db_manager = None
    elif not db_manager.is_initialized():
        # Try to ensure initialization completes
        await db_manager.ensure_initialized()
    return db_manager


# Initialize on module import with better error handling
try:
    db_manager = create_db_manager()
    log_service_status("database_manager", "info", "Database manager created on module import")
except Exception as e:
    log_service_status("database_manager", "error", f"Failed to create database manager: {str(e)}")
    db_manager = None


# Convenience functions for compatibility
async def get_database_health() -> Dict[str, Any]:
    """Get health status of the database components."""
    global db_manager
    if not db_manager:
        db_manager = await initialize_database()
        if not db_manager:
            return {
                "status": "unavailable",
                "message": "Database manager not initialized",
                "redis": {"status": "unhealthy", "details": "Database manager not available"},
                "chromadb": {"status": "unhealthy", "details": "Database manager not available"},
                "embeddings": {"status": "unhealthy", "details": "Database manager not available"},
                "cache": {"status": "unhealthy", "details": "Database manager not available"},
                "alerts": {"status": "unhealthy", "details": "Database manager not available"},
            }

    # Ensure initialization is complete
    await db_manager.ensure_initialized()
    health_status = cast(Dict[str, Any], await db_manager.get_health_status())

    # Add cache statistics
    cache_stats = db_manager.get_cache_stats()
    health_status["cache"] = {
        "status": "healthy",
        "details": f"Cache operational - {cache_stats['hit_rate']} hit rate",
        "stats": cache_stats,
    }

    # Add alert manager statistics using feature registry
    if ALERT_MANAGER_AVAILABLE:
        try:
            from utilities.alert_manager import get_alert_manager

            alert_manager = get_alert_manager()
            alert_stats = alert_manager.get_alert_stats()
            health_status["alerts"] = {
                "status": "healthy",
                "details": f"Alert system operational - {alert_stats['total_alerts']} total alerts",
                "stats": alert_stats,
            }
        except Exception as e:
            health_status["alerts"] = {"status": "degraded", "details": f"Alert system error: {str(e)}"}
    else:
        health_status["alerts"] = {"status": "unavailable", "details": "Alert manager not available"}
    return health_status


@handle_database_errors()
async def get_chat_history(chat_id: str, limit: int = 100) -> List[Dict[str, Any]]:
    """Get chat history from Redis."""
    global db_manager
    if not db_manager:
        db_manager = await initialize_database()
        if not db_manager:
            log_service_status("redis", "error", "Cannot get chat history: Database manager not available")
            return []

    # Ensure initialization is complete
    await db_manager.ensure_initialized()
    return await db_manager.get_chat_history(chat_id, limit)


@handle_database_errors()
async def store_chat_entry(chat_id: str, chat_entry: Dict[str, Any]) -> bool:
    """Store a chat entry in Redis."""
    global db_manager
    if not db_manager:
        await initialize_database()
        if not db_manager:
            return False
    return await db_manager.store_chat_entry(chat_id, chat_entry)


@handle_database_errors()
async def get_embedding(text: str) -> Optional[List[float]]:
    """Get embedding for text."""
    global db_manager
    if not db_manager:
        await initialize_database()
        if not db_manager:
            return None
    return await db_manager.get_embedding(text)


@handle_database_errors()
async def store_vector_data(text: str, metadata: Dict[str, Any]) -> bool:
    """Store text and metadata in vector database."""
    global db_manager
    if not db_manager:
        await initialize_database()
        if not db_manager:
            return False

    # Get embedding
    embedding = await get_embedding(text)
    if not embedding:
        return False

    # Add to chromadb
    try:
        collection = db_manager.chroma_collection
        if not collection:
            return False

        doc_id = str(time.time())
        collection.add(embeddings=[embedding], documents=[text], metadatas=[metadata], ids=[doc_id])
        log_service_status(
            "memory",
            "info",
            f"Memory write - stored document (id: {doc_id}, size: {len(text)} chars, user: {metadata.get('user_id', 'unknown')})")
        return True
    except Exception as e:
        log_service_status("chromadb", "error", f"Error storing vector data: {str(e)}")
        return False


@handle_database_errors()
async def query_similar(query_text: str, n_results: int = 5) -> QueryResponse:
    """Query for similar texts in vector database."""
    global db_manager
    if not db_manager:
        await initialize_database()
        if not db_manager:
            return {"matches": []}

    results = await db_manager.query_chroma(query_text, n_results)
    if not results or not isinstance(results, dict):
        return {"matches": []}

    chroma_results = cast(ChromaResults, results)

    if not all(key in chroma_results for key in ["documents", "metadatas", "distances"]):
        return {"matches": []}

    try:
        matches = []
        for doc, meta, dist in zip(
            chroma_results["documents"][0], chroma_results["metadatas"][0], chroma_results["distances"][0]
        ):
            matches.append({"document": doc, "metadata": meta, "distance": dist})
        return {"matches": matches}
    except (IndexError, TypeError):
        return {"matches": []}


@handle_cache_errors("get_cache")
def get_cache() -> CacheManager[Any]:
    """Get the global cache manager instance (synchronous)."""
    global db_manager
    if not db_manager:
        try:
            db_manager = create_db_manager()
        except Exception:
            # Return a dummy cache manager if initialization fails
            log_service_status("cache", "warning", "Cache unavailable - using fallback cache manager")
            return CacheManager[Any](max_size=100)
    return db_manager.get_cache()


def set_cache(key: str, value: Any, ttl: Optional[int] = None) -> bool:
    """Set a value in the global cache manager (synchronous)."""
    try:
        cache = get_cache()
        cache.set(key, value)
        log_service_status("cache", "info", f"Cache write - key: {key}, ttl: {ttl if ttl else 'none'}")
        return True
    except Exception as e:
        log_service_status("cache", "error", f"Cache write failed - key: {key}, error: {str(e)}")
        return False


@handle_cache_errors("get_cache_async")
async def get_cache_async() -> CacheManager[Any]:
    """Get the global cache manager instance (async)."""
    global db_manager
    if not db_manager:
        await initialize_database()
        if not db_manager:
            raise RuntimeError("Database manager not initialized")
    return db_manager.get_cache()


@handle_cache_errors("set_cache_async")
async def set_cache_async(key: str, value: Any, ttl: Optional[int] = None) -> bool:
    """Set a value in the global cache manager (async)."""
    global db_manager
    if not db_manager:
        await initialize_database()
        if not db_manager:
            return False

    cache = db_manager.get_cache()
    cache.set(key, value)
    return True


@handle_database_errors()
async def store_chat_history(chat_id: str, messages: List[Dict[str, Any]]) -> bool:
    """Store complete chat history in Redis."""
    global db_manager
    if not db_manager:
        db_manager = await initialize_database()
        if not db_manager:
            log_service_status("redis", "error", "Cannot store chat history: Database manager not available")
            return False

    # Ensure initialization is complete
    await db_manager.ensure_initialized()

    async def store_operation(redis_client: redis.Redis) -> bool:
        """Store chat history messages in Redis.
        
        Stores the complete chat history for a given chat ID in Redis,
        clearing any existing history first.
        
        Args:
            redis_client: Redis client instance for operations
            
        Returns:
            bool: True if storage was successful, False otherwise
        """
        chat_key = f"chat:{chat_id}"
        # Clear existing history
        await redis_client.delete(chat_key)
        # Store new history
        for message in messages:
            await redis_client.lpush(chat_key, json.dumps(message))
        log_service_status("redis", "info", f"Cache write - stored {len(messages)} messages for chat_id: {chat_id}")
        return True

    result = await db_manager.execute_redis_operation(store_operation, "store_chat_history")
    return result if result is not None else False


@handle_database_errors()
async def index_user_document(user_id: str, document_text: str, metadata: Dict[str, Any]) -> bool:
    """Index a user document in the vector database."""
    global db_manager
    if not db_manager:
        await initialize_database()
        if not db_manager:
            return False

    # Add user_id to metadata
    metadata["user_id"] = user_id
    metadata["timestamp"] = datetime.now().isoformat()

    log_service_status(
        "memory", "info", f"Memory indexing - user: {user_id}, document size: {len(document_text)} chars"
    )
    return await store_vector_data(document_text, metadata)


@handle_database_errors()
async def retrieve_user_memory(user_id: str, query: str, n_results: int = 5) -> List[Dict[str, Any]]:
    """Retrieve user-specific memory from the vector database."""
    global db_manager
    if not db_manager:
        await initialize_database()
        if not db_manager:
            return []

    try:
        start_time = time.time()

        # Query chromadb with user filter
        if not db_manager.chroma_collection or not db_manager.embedding_model:
            return []

        query_embedding = await db_manager.get_embedding(query)
        if not query_embedding:
            return []

        results = db_manager.chroma_collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where={"user_id": user_id},
            include=["documents", "metadatas", "distances"])

        query_time = time.time() - start_time

        if not results or not isinstance(results, dict):
            log_service_status(
                "memory",
                "warning",
                f"Memory miss - no user memories found for user: {user_id}, query: '{query[:50]}...'")
            return []

        memories = []
        for doc, meta, dist in zip(
            results.get("documents", [[]])[0], results.get("metadatas", [[{}]])[0], results.get("distances", [[0.0]])[0]
        ):
            memories.append({"document": doc, "metadata": meta, "distance": dist})

        if len(memories) == 0:
            log_service_status(
                "memory",
                "info",
                f"Memory miss - no matches for user: {user_id}, query: '{query[:50]}...' (query_time: {query_time:.3f}s)")
        else:
            log_service_status(
                "memory",
                "info",
                f"Memory hit - found {len(memories)} memories for user: {user_id}, query: '{query[:50]}...' (query_time: {query_time:.3f}s)")

        return memories
    except Exception as e:
        log_service_status("chromadb", "error", f"Error retrieving user memory: {str(e)}")
        return []


@handle_database_errors()
async def index_document_chunks(user_id: str, doc_id: str, name: str, chunks: List[str]) -> bool:
    """Index pre-chunked document content in the vector database."""
    global db_manager
    if not db_manager:
        await initialize_database()
        if not db_manager:
            return False

    # Ensure initialization is complete
    await db_manager.ensure_initialized()

    try:
        if not await db_manager.is_chromadb_available() or not db_manager.is_embeddings_available():
            log_service_status("memory", "warning", "ChromaDB or embeddings not available for document indexing")
            return False

        # Generate embeddings for all chunks
        embeddings = []
        for chunk in chunks:
            embedding = await db_manager.get_embedding(chunk)
            if embedding:
                embeddings.append(embedding)
            else:
                log_service_status("memory", "error", f"Failed to generate embedding for chunk in doc_id={doc_id}")
                return False

        # Create IDs and metadata for chunks
        chunk_ids = [f"chunk:{doc_id}:{i}" for i in range(len(chunks))]
        metadatas = [
            {"user_id": user_id, "doc_id": doc_id, "source": name, "chunk_index": i, "timestamp": datetime.now().isoformat()}
            for i in range(len(chunks))
        ]

        # Add to ChromaDB
        collection = db_manager.chroma_collection
        if not collection:
            return False

        collection.add(embeddings=embeddings, documents=chunks, metadatas=metadatas, ids=chunk_ids)
        log_service_status(
            "memory", "info", f"Successfully indexed {len(chunks)} chunks for doc_id={doc_id}, user_id={user_id}"
        )
        return True

    except Exception as e:
        log_service_status("memory", "error", f"Failed to index document chunks for doc_id={doc_id}: {str(e)}")
        return False


@handle_memory_errors("index_document_chunks")
def index_document_chunks(db_manager, user_id, doc_id, name, chunks, request_id=""):
    """Embed and index a list of pre-chunked text documents for a user in chromadb.
    
    Args:
        db_manager: The database manager instance
        user_id: The ID of the user who owns the document
        doc_id: Unique identifier for the document
        name: Name or title of the document
        chunks: List of text chunks to index
        request_id: Optional request ID for tracking
        
    Returns:
        True if indexing was successful, False otherwise
    """
    def _index_op():
        """Index document chunks in ChromaDB.
        
        Embeds and stores document chunks in ChromaDB for the specified user,
        with appropriate metadata for retrieval. Handles embedding generation
        and ChromaDB storage operations with proper error handling.
        
        Returns:
            bool: True if indexing was successful, False otherwise
        """
        if not db_manager.is_chromadb_available():
            logging.warning("[CHROMADB] chromadb not available, skipping document indexing")
            return False

        if not db_manager.is_embeddings_available():
            logging.warning("[EMBEDDINGS] Embedding model not available, skipping document indexing")
            return False

        try:
            # Set show_progress_bar to False for cleaner logs
            embeddings = db_manager.embedding_model.encode(chunks, show_progress_bar=False).tolist()
            logging.info(f"Generated embeddings for {len(chunks)} chunks for doc_id={doc_id}")
        except Exception as e:
            logging.error(f"Failed to generate embeddings for doc_id={doc_id}: {e}")
            raise e

        chunk_ids = [f"chunk:{doc_id}:{i}" for i in range(len(chunks))]
        metadatas = [
            {"user_id": user_id, "doc_id": doc_id, "source": name, "chunk_index": i} for i in range(len(chunks))
        ]

        try:
            db_manager.chroma_collection.add(
                embeddings=embeddings, ids=chunk_ids, metadatas=metadatas, documents=chunks
            )
            logging.info(f"Successfully indexed {len(chunks)} chunks for doc_id={doc_id}, user_id={user_id}")
            return True
        except Exception as e:
            logging.error(f"Failed to store chunks in chromadb for doc_id={doc_id}: {e}")
            raise e

    return _index_op()


def index_user_document(db_manager, user_id, doc_id, name, text, chunk_size=1000, chunk_overlap=200, request_id=""):
    """Chunk, embed, and index a document for a specific user in chromadb.
    
    Args:
        db_manager: The database manager instance
        user_id: The ID of the user who owns the document
        doc_id: Unique identifier for the document
        name: Name or title of the document
        text: The document text to index
        chunk_size: Size of each text chunk (default: 1000)
        chunk_overlap: Overlap between adjacent chunks (default: 200)
        request_id: Optional request ID for tracking
        
    Returns:
        True if indexing was successful, False otherwise
    
    Note: 
        This is a convenience wrapper. For pre-chunked data, use index_document_chunks.
    """
    chunks = chunk_text(text, chunk_size, chunk_overlap)
    if not chunks:
        logging.warning(f"No chunks created for doc_id={doc_id}, user_id={user_id}")
        return False

    return index_document_chunks(db_manager, user_id, doc_id, name, chunks, request_id)


@handle_memory_errors("retrieve_user_memory")
def retrieve_user_memory(db_manager, user_id, query_embedding, n_results=5, request_id=""):
    """Retrieve relevant memory chunks for a user from chromadb.
    
    Args:
        db_manager: The database manager instance
        user_id: The ID of the user whose memory to search
        query_embedding: The embedding vector to search for similar documents
        n_results: Number of results to return (default: 5)
        request_id: Optional request ID for tracking
        
    Returns:
        List of memory chunks with metadata and similarity scores
    """
    # Add logging for memory retrieval
    logging.debug(f"retrieve_user_memory called with user_id={user_id}")

    def _retrieve_memory():
        """Retrieve relevant memory chunks for a user from ChromaDB.
        
        Searches for memory chunks relevant to the specified query embedding
        and formats the results for use in the application. Includes user
        profile information when available and handles various embedding
        formats properly.
        
        Returns:
            List[Dict]: List of formatted memory results with documents, 
                       metadata, and similarity scores
        """
        try:
            # Synchronous check for ChromaDB availability
            if db_manager.chroma_client is None or db_manager.chroma_collection is None:
                logging.warning("[CHROMADB] chromadb not available, returning empty memory")
                return []
        except Exception as e:
            logging.warning(f"[CHROMADB] Error checking availability: {str(e)}, returning empty memory")
            return []

        # Enhanced logging for debugging
        logging.info(f"[MEMORY] [SEARCH] Starting memory retrieval for user_id={user_id}, n_results={n_results}")

        # Ensure query_embedding is properly formatted
        logging.debug(f"[MEMORY] [CHART] Query embedding type: {type(query_embedding)}")

        if query_embedding is None:
            logging.error("[MEMORY] [FAIL] Query embedding is None")
            return []
        elif hasattr(query_embedding, "tolist"):
            embedding_list = query_embedding.tolist()
            logging.debug(
                f"[MEMORY] [CHART] Converted numpy array to list, shape: {query_embedding.shape if hasattr(query_embedding, 'shape') else 'unknown'}"
            )
        elif hasattr(query_embedding, "__iter__") and not isinstance(query_embedding, str):
            embedding_list = list(query_embedding)
            logging.debug(f"[MEMORY] [CHART] Converted iterable to list, length: {len(embedding_list)}")
        else:
            logging.error(f"[MEMORY] [FAIL] Invalid embedding format: {type(query_embedding)}")
            return []

        logging.debug(f"[MEMORY]  Query embedding dimension: {len(embedding_list)}")

        results = db_manager.chroma_collection.query(
            query_embeddings=[embedding_list],
            n_results=n_results,
            where={"user_id": user_id},
            include=["documents", "metadatas", "distances"])

        logging.info(f"[MEMORY] [CHART] chromadb query results: {results}")

        docs = results.get("documents", [[]])[0] if results else []
        metadatas = results.get("metadatas", [[]])[0] if results else []
        distances = results.get("distances", [[]])[0] if results else []

        logging.info(f"[MEMORY] [OK] Retrieved {len(docs)} memory chunks for user_id={user_id}")

        # Use len() check instead of boolean check to avoid numpy array truth value error
        if len(docs) > 0:
            for i, (doc, metadata, distance) in enumerate(zip(docs, metadatas, distances)):
                similarity = 1 - distance if distance is not None else 0.0
                logging.info(f"[MEMORY]  Chunk {i+1}: similarity={similarity:.4f}, metadata={metadata}")
                logging.debug(f"[MEMORY]  Content: {doc[:100]}...")
        else:
            logging.warning(f"[MEMORY] [WARN] No relevant memory found for user_id={user_id}")

        # Return formatted results for semantic search
        formatted_results = []

        # Add user profile as highest priority context
        try:
            from services.user_profiles import user_profile_manager

            user_profile = user_profile_manager.get_user_info(user_id)
            if user_profile:
                profile_context = user_profile_manager.build_context_for_llm(user_id)
                if profile_context:
                    formatted_results.append(
                        {
                            "document": f"User Profile: {profile_context}",
                            "metadata": {"type": "user_profile", "user_id": user_id},
                            "distance": 0.0,  # Highest relevance
                        }
                    )
                    logging.info(f"[MEMORY]  Added user profile context for {user_id}")
        except ImportError:
            logging.debug("[MEMORY] User profile system not available")
        except Exception as e:
            logging.warning(f"[MEMORY] Error adding user profile: {e}")

        for i, (doc, metadata, distance) in enumerate(zip(docs, metadatas, distances)):
            similarity = 1 - distance if distance is not None else 0.0
            formatted_results.append(
                {"content": doc, "metadata": metadata, "similarity": similarity, "distance": distance, "rank": i + 1}
            )

        logging.info(f"[MEMORY]  Returning {len(formatted_results)} formatted results")
        return formatted_results

    return _retrieve_memory()


def get_embedding_sync(db_manager, text, request_id=""):
    """Get embedding vector for text using the embedding model (synchronous version).
    
    Args:
        db_manager: The database manager instance
        text: The text to generate an embedding for
        request_id: Optional request ID for tracking
        
    Returns:
        The embedding vector if successful, None otherwise
    """
    logging.critical(f"[SEARCH] [DATABASE] get_embedding called with text: '{text[:50]}...'")

    def _get_embedding():
        """Generate an embedding vector for the given text using the embedding model.
        
        Converts text to a numerical embedding vector using the available
        embedding model in the database manager. Handles different embedding
        model types and formats properly.
        
        Returns:
            Union[List[float], NDArray, None]: A numerical embedding vector 
                                             if successful, None otherwise
        """
        if not db_manager.is_embeddings_available():
            logging.warning("[EMBEDDINGS] Embedding model not available")
            logging.critical(f"[FAIL] [DATABASE] Embedding model not available")
            return None

        logging.critical(f"[SEARCH] [DATABASE] Generating embedding using model: {type(db_manager.embedding_model)}")
        # Get the embedding and return the first element (single text input)
        embedding = db_manager.embedding_model.encode([text])
        logging.critical(f"[SEARCH] [DATABASE] Raw embedding result: type={type(embedding)}, shape={getattr(embedding, 'shape', 'no shape')}")
        
        if embedding is not None:
            if hasattr(embedding, "__len__") and len(embedding) > 0:
                result = embedding[0]
                logging.critical(f"[SEARCH] [DATABASE] Returning embedding[0]: type={type(result)}, shape={getattr(result, 'shape', 'no shape')}")
                return result
            
        logging.critical(f"[FAIL] [DATABASE] Embedding invalid or empty")
        return None

    # Execute synchronously in the current thread
    return _get_embedding()


# Initialize the global database manager instance at module import time
db_manager = DatabaseManager()
