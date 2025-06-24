"""
DatabaseManager class for FastAPI LLM backend.
Handles Redis, ChromaDB, and embedding model management with enhanced logging.
"""

from typing import Optional, Union, Any, Dict, List, TypedDict, cast, Sequence, Protocol
import os
import time
import json
import asyncio
from datetime import datetime

import chromadb
from chromadb.config import Settings
import redis
from sentence_transformers import SentenceTransformer
from numpy.typing import NDArray
import numpy as np

from error_handler import RedisConnectionHandler
from human_logging import log_service_status
from utilities.validation import DatabaseConfig, ChatMessage, validate_query_params
from utilities.memory_pool import MemoryPool
from utilities.memory_monitor import MemoryPressureMonitor
from utilities.cache_manager import CacheManager

class ChromaClientProtocol(Protocol):
    def get_or_create_collection(self, name: str, **kwargs: Any) -> 'ChromaCollectionProtocol': ...
    def list_collections(self) -> List[str]: ...
    def heartbeat(self) -> bool: ...

class ChromaCollectionProtocol(Protocol):
    def add(self, embeddings: List[List[float]], documents: List[str],
            metadatas: List[Dict[str, Any]], ids: List[str]) -> None: ...
    def query(self, query_embeddings: List[List[float]], n_results: int,
             **kwargs: Any) -> Dict[str, List[Any]]: ...

class ComponentHealth(TypedDict):
    status: str
    details: str

class DatabaseHealth(TypedDict):
    redis: ComponentHealth
    chromadb: ComponentHealth
    embeddings: ComponentHealth

class ChromaResults(TypedDict):
    documents: List[List[str]]
    metadatas: List[List[Dict[str, Any]]]
    distances: List[List[float]]
    ids: List[List[str]]

class Match(TypedDict):
    document: str
    metadata: Dict[str, Any]
    distance: float

class QueryResponse(TypedDict):
    matches: List[Match]

class DatabaseManager:
    """Database manager class for handling Redis and ChromaDB connections."""

    def __init__(self):
        """Initialize database manager."""
        # Database clients
        self.redis_client: Optional[redis.Redis] = None
        self.chroma_client: Optional[ChromaClientProtocol] = None
        self.chroma_collection: Optional[ChromaCollectionProtocol] = None
        self.embedding_model: Optional[SentenceTransformer] = None
        
        # Memory management
        self.memory_pool = MemoryPool(max_size=1000)
        self.memory_monitor = MemoryPressureMonitor(
            warning_threshold=75.0,
            critical_threshold=90.0
        )
        self.cache_manager = CacheManager[Any](max_size=10000)
        
        # Locks for thread-safe operations
        self._redis_lock = asyncio.Lock()
        self._chroma_lock = asyncio.Lock()
        self._embedding_lock = asyncio.Lock()
        
        # Initialize everything
        asyncio.create_task(self._initialize_all())
        
    async def _initialize_all(self):
        """Initialize all components with proper error handling."""
        try:
            await self._initialize_redis()
            await self._initialize_chroma()
            await self._initialize_embedding_model()
            log_service_status("All database components initialized successfully", "info")
        except Exception as e:
            log_service_status(f"Error during initialization: {str(e)}", "error")
            raise
            
    async def _initialize_redis(self):
        """Initialize Redis client with proper error handling."""
        try:
            redis_host = os.getenv("REDIS_HOST", "localhost")
            redis_port = int(os.getenv("REDIS_PORT", "6379"))
            redis_db = int(os.getenv("REDIS_DB", "0"))
            
            async with self._redis_lock:
                self.redis_client = redis.Redis(
                    host=redis_host,
                    port=redis_port,
                    db=redis_db,
                    decode_responses=True
                )
                
                # Test connection
                self.redis_client.ping()
                log_service_status("Redis initialized successfully", "info")
        except redis.ConnectionError as e:
            log_service_status(f"Redis initialization failed: {str(e)}", "error")
            raise
            
    async def _initialize_chroma(self):
        """Initialize ChromaDB client with proper error handling."""
        try:
            settings = Settings(
                chroma_api_impl="rest",
                chroma_server_host=os.getenv("CHROMA_HOST", "localhost"),
                chroma_server_http_port=int(os.getenv("CHROMA_PORT", "8000")),
            )
            
            async with self._chroma_lock:
                self.chroma_client = cast(ChromaClientProtocol, chromadb.Client(settings))
                
                # Test connection by getting collections
                try:
                    _ = self.chroma_client.list_collections()
                except Exception:
                    log_service_status("ChromaDB connection test failed", "error")
                    raise
                
                collection_name = os.getenv("CHROMA_COLLECTION", "default")
                self.chroma_collection = self.chroma_client.get_or_create_collection(
                    name=collection_name,
                    metadata={"description": "Default vector store for embeddings"}
                )
                
                log_service_status("ChromaDB initialized successfully", "info")
        except Exception as e:
            log_service_status(f"ChromaDB initialization failed: {str(e)}", "error")
            raise
            
    async def _initialize_embedding_model(self):
        """Initialize the embedding model with proper error handling."""
        try:
            model_name = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
            self.embedding_model = SentenceTransformer(model_name)
            log_service_status(f"Embedding model {model_name} loaded successfully", "info")
        except Exception as e:
            log_service_status(f"Embedding model initialization failed: {str(e)}", "error")
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

    async def get_redis_client(self):
        """Get a Redis client from the connection pool."""
        try:
            if self.redis_client is None:
                log_service_status(
                    "REDIS",
                    "reconnecting",
                    "Redis client not available. Attempting to re-initialize.",
                )
                await self._initialize_redis()
                if self.redis_client is None:
                    return None
            
            self.redis_client.ping()
            return self.redis_client
        except redis.RedisError as e:
            log_service_status(
                "REDIS", "reconnecting", f"Connection issue: {e}. Attempting to re-initialize."
            )
            await self._initialize_redis()
            if self.redis_client:
                try:
                    self.redis_client.ping()
                    return self.redis_client
                except redis.RedisError:
                    log_service_status(
                        "REDIS", "failed", "Failed to get a Redis client after re-initialization."
                    )
            return None

    async def is_redis_available(self):
        """Check if Redis is available."""
        client = await self.get_redis_client()
        return client is not None

    async def is_chromadb_available(self):
        """Check if ChromaDB is available."""
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
        """Get health status of all database components."""
        redis_available = await self.is_redis_available()
        chroma_available = await self.is_chromadb_available()
        embeddings_available = self.is_embeddings_available()
        
        return {
            "redis": {
                "status": "healthy" if redis_available else "unhealthy",
                "details": "Connected and responsive" if redis_available else "Not available"
            },
            "chromadb": {
                "status": "healthy" if chroma_available else "unhealthy",
                "details": "Connected and responsive" if chroma_available else "Not available"
            },
            "embeddings": {
                "status": "healthy" if embeddings_available else "unhealthy",
                "details": "Model loaded and ready" if embeddings_available else "Not available"
            }
        }

    async def execute_redis_operation(self, operation: Any, operation_name: str) -> Any:
        """Execute a Redis operation with proper error handling."""
        if not self.redis_client:
            log_service_status(f"Redis not available for operation: {operation_name}", "error")
            return None

        try:
            async with self._redis_lock:
                result = operation(self.redis_client)
                return result
        except redis.RedisError as e:
            log_service_status(f"Redis operation '{operation_name}' failed: {str(e)}", "error")
            try:
                await self._initialize_redis()
                if self.redis_client:
                    async with self._redis_lock:
                        result = operation(self.redis_client)
                        return result
            except redis.RedisError as e2:
                log_service_status(f"Retry failed for '{operation_name}': {str(e2)}", "error")
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
        """Clean up database connections."""
        try:
            if self.redis_client:
                await self._redis_lock.acquire()
                try:
                    self.redis_client.close()
                finally:
                    self._redis_lock.release()
            
            if self.chroma_client:
                await self._chroma_lock.acquire()
                try:
                    # Free up resources, actual cleanup will be handled by the ChromaDB server
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
            
            log_service_status("Database connections cleaned up successfully", "info")
        except Exception as e:
            log_service_status(f"Error during cleanup: {str(e)}", "error")
            raise

    async def get_embedding(self, text: str) -> Optional[List[float]]:
        """Get embedding for text using the current model."""
        if not self.embedding_model:
            log_service_status("Embedding model not available", "error")
            return None
            
        try:
            embedding = self.embedding_model.encode(text)
            return embedding.tolist()
        except Exception as e:
            log_service_status(f"Error generating embedding: {str(e)}", "error")
            return None

    async def get_chat_history(self, chat_id: str) -> List[Dict[str, Any]]:
        """Get chat history from Redis."""
        def get_operation(redis_client: redis.Redis) -> List[Dict[str, Any]]:
            chat_key = f"chat:{chat_id}"
            try:
                # lrange returns a list of bytes or str
                entries = redis_client.lrange(chat_key, 0, -1)
                if not isinstance(entries, list):
                    return []
                    
                history = []
                for entry in entries:
                    try:
                        if isinstance(entry, bytes):
                            entry_str = entry.decode('utf-8')
                        else:
                            entry_str = entry
                        history.append(json.loads(entry_str))
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        continue
                return history
            except redis.RedisError:
                return []
            
        result = await self.execute_redis_operation(get_operation, "get_chat_history")
        return result if result is not None else []
        
    async def store_chat_entry(self, chat_id: str, chat_entry: Dict[str, Any]) -> bool:
        """Store a chat entry in Redis."""
        def store_operation(redis_client: redis.Redis) -> bool:
            chat_key = f"chat:{chat_id}"
            redis_client.lpush(chat_key, json.dumps(chat_entry))
            return True
            
        return await self.execute_redis_operation(store_operation, "store_chat") or False
        
    async def query_chroma(self, query_text: str, n_results: int = 5) -> Optional[Dict[str, Any]]:
        """Query the ChromaDB collection."""
        if not self.chroma_collection or not self.embedding_model:
            log_service_status("ChromaDB collection or embedding model not available", "error")
            return None
        
        try:
            # Get embedding for query
            query_embedding = await self.get_embedding(query_text)
            if query_embedding is None:
                return None
            
            # Query collection
            results = self.chroma_collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                include=["documents", "metadatas", "distances"]
            )
            
            if not results or not isinstance(results, dict):
                return None
                
            return {
                "matches": [
                    {
                        "document": doc,
                        "metadata": meta,
                        "distance": dist
                    }
                    for doc, meta, dist in zip(
                        results.get("documents", [[]])[0],
                        results.get("metadatas", [[{}]])[0],
                        results.get("distances", [[0.0]])[0]
                    )
                ] if results.get("documents") else []
            }
        except Exception as e:
            log_service_status(f"Error querying ChromaDB: {str(e)}", "error")
            return None


# Global database manager instance
db_manager = DatabaseManager()


# Convenience functions for compatibility
async def get_database_health() -> Dict[str, Any]:
    """Get health status of the database components."""
    global db_manager
    if not db_manager:
        return {
            "status": "unavailable",
            "message": "Database manager not initialized"
        }
    return cast(Dict[str, Any], await db_manager.get_health_status())

async def initialize_database():
    """Initialize the global database manager."""
    global db_manager
    if not db_manager:
        db_manager = DatabaseManager()
        # Wait for initialization
        await asyncio.sleep(1)
        health = await get_database_health()
        status = cast(DatabaseHealth, health)
        if (status["redis"]["status"] == "unhealthy" or 
            status["chromadb"]["status"] == "unhealthy"):
            raise RuntimeError("Database initialization failed")
    return db_manager

# Initialize global database manager
db_manager = None
asyncio.create_task(initialize_database())


async def get_chat_history(chat_id: str) -> List[Dict[str, Any]]:
    """Get chat history from Redis."""
    global db_manager
    if not db_manager:
        await initialize_database()
        if not db_manager:
            return []
    return await db_manager.get_chat_history(chat_id)

async def store_chat_entry(chat_id: str, chat_entry: Dict[str, Any]) -> bool:
    """Store a chat entry in Redis."""
    global db_manager
    if not db_manager:
        await initialize_database()
        if not db_manager:
            return False
    return await db_manager.store_chat_entry(chat_id, chat_entry)

async def get_embedding(text: str) -> Optional[List[float]]:
    """Get embedding for text."""
    global db_manager
    if not db_manager:
        await initialize_database()
        if not db_manager:
            return None
    return await db_manager.get_embedding(text)

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
        
    # Add to ChromaDB
    try:
        collection = db_manager.chroma_collection
        if not collection:
            return False
            
        collection.add(
            embeddings=[embedding],
            documents=[text],
            metadatas=[metadata],
            ids=[str(time.time())]
        )
        return True
    except Exception as e:
        log_service_status(f"Error storing vector data: {str(e)}", "error")
        return False

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
            chroma_results["documents"][0],
            chroma_results["metadatas"][0],
            chroma_results["distances"][0]
        ):
            matches.append({
                "document": doc,
                "metadata": meta,
                "distance": dist
            })
        return {"matches": matches}
    except (IndexError, TypeError):
        return {"matches": []}
