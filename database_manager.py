"""
DatabaseManager class for FastAPI LLM backend.
Handles Redis, ChromaDB, and embedding model management with enhanced logging.
"""

import os
import time
from typing import Optional

import chromadb
import redis
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

from error_handler import RedisConnectionHandler
from human_logging import log_service_status


import json


class DatabaseManager:
    """Central database manager for Redis and ChromaDB operations."""

    def __init__(self):
        self.redis_pool = None
        self.chroma_client = None
        self.chroma_collection = None
        self.embedding_model = None
        self._initialize_databases()

    def _initialize_databases(self):
        """Initialize all database connections."""
        self._initialize_redis()
        self._initialize_chromadb()
        self._initialize_embedding_model()

    def _initialize_redis(self):
        """Initialize Redis connection pool with Docker-optimized settings."""
        try:
            redis_host = os.getenv("REDIS_HOST", "localhost")
            redis_port = int(os.getenv("REDIS_PORT", 6379))
            self.redis_pool = redis.ConnectionPool(
                host=redis_host,
                port=redis_port,
                db=0,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=10,
                socket_keepalive=True,
                socket_keepalive_options={},
                retry_on_timeout=True,
                retry_on_error=[redis.ConnectionError, redis.TimeoutError],
                health_check_interval=30,
                max_connections=20,
                connection_class=redis.Connection,
            )            # Test the connection
            test_client = redis.Redis(connection_pool=self.redis_pool)
            test_client.ping()
            log_service_status(
                "REDIS",
                "ready",
                f"Connected to {redis_host}:{redis_port} with Docker-optimized settings",
            )
        except redis.RedisError as e:
            RedisConnectionHandler.handle_redis_error(e, "connect")
            self.redis_pool = None
        except Exception as e:
            RedisConnectionHandler.handle_redis_error(e, "connect_general")
            self.redis_pool = None

    def _initialize_chromadb(self):
        """Initialize ChromaDB connection with performance optimizations."""
        try:
            use_http_chroma = os.getenv("USE_HTTP_CHROMA", "true").lower() == "true"

            if use_http_chroma:
                chroma_host = os.getenv("CHROMA_HOST", "localhost")
                chroma_port = int(os.getenv("CHROMA_PORT", 8000))

                try:
                    self.chroma_client = chromadb.HttpClient(host=chroma_host, port=chroma_port)
                except AttributeError:
                    self.chroma_client = chromadb.Client(
                        Settings(
                            chroma_api_impl="rest",
                            chroma_server_host=chroma_host,
                            chroma_server_http_port=chroma_port,
                        )
                    )
                log_service_status(
                    "CHROMADB",
                    "ready",
                    f"Using HTTP client connecting to http://{chroma_host}:{chroma_port}",
                )
            else:
                chroma_db_dir = os.getenv("CHROMA_DB_DIR", "./storage/chroma")
                os.makedirs(chroma_db_dir, exist_ok=True)

                self.chroma_client = chromadb.Client(
                    Settings(
                        persist_directory=chroma_db_dir,
                        anonymized_telemetry=os.getenv("CHROMA_TELEMETRY", "true").lower()
                        == "true",
                    )
                )
                log_service_status(
                    "CHROMADB", "ready", f"Using local file-based client at {chroma_db_dir}"
                )

            collection_name = os.getenv("CHROMA_COLLECTION", "user_memory")
            self.chroma_collection = self.chroma_client.get_or_create_collection(collection_name)
            log_service_status(
                "CHROMADB",
                "ready",
                f"Successfully connected to ChromaDB and accessed collection '{collection_name}'",
            )

            try:
                collections = self.chroma_client.list_collections()
                log_service_status(
                    "CHROMADB", "ready", f"Found {len(collections)} existing collections"
                )
            except Exception as e:
                log_service_status("CHROMADB", "degraded", f"Could not list collections: {e}")

        except Exception as e:
            log_service_status("CHROMADB", "failed", f"Failed to initialize: {e}")
            self.chroma_client = None
            self.chroma_collection = None

    def _initialize_embedding_model(self):
        """Initialize embedding model with robust offline support."""
        log_service_status("EMBEDDINGS", "starting", "🧠 Initializing embedding model")

        # Model loading attempts
        primary_model = os.getenv("EMBEDDING_MODEL", "Qwen/Qwen3-Embedding-0.6B")
        model_candidates = [
            primary_model,
            "sentence-transformers/all-MiniLM-L6-v2",
            "all-MiniLM-L6-v2",
            "paraphrase-MiniLM-L3-v2",
            "all-mpnet-base-v2",
        ]

        for model_name in model_candidates:
            try:
                log_service_status("EMBEDDINGS", "starting", f"Trying model: {model_name}")
                self.embedding_model = SentenceTransformer(model_name, device="cpu")
                # Test the model
                test_embedding = self.embedding_model.encode(["test"])
                if test_embedding is not None:
                    log_service_status("EMBEDDINGS", "ready", f"Successfully loaded {model_name}")
                    return
            except Exception as e:
                log_service_status("EMBEDDINGS", "warning", f"Failed to load {model_name}: {e}")
                continue

        log_service_status("EMBEDDINGS", "failed", "All embedding models failed to load")
        self.embedding_model = None

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


# Global database manager instance
db_manager = DatabaseManager()


# Convenience functions for compatibility
def get_database_health():
    """Get health status of all database components."""
    return db_manager.get_health_status()


def get_cache(db_manager_instance, cache_key: str):
    """Get value from cache."""
    try:
        redis_client = db_manager_instance.get_redis_client()
        if redis_client:
            return redis_client.get(cache_key)
        return None
    except Exception:
        return None


def set_cache(db_manager_instance, cache_key: str, value: str, expire: int = 3600):
    """Set value in cache."""
    try:
        redis_client = db_manager_instance.get_redis_client()
        if redis_client:
            redis_client.setex(cache_key, expire, value)
            return True
        return False
    except Exception:
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
            return db_manager.embedding_model.encode([text])[0]
        return None
    except Exception:
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
    try:
        if not db_manager.chroma_collection:
            log_service_status("CHROMADB", "warning", "ChromaDB collection not available")
            return []
            
        # Generate embedding for the query
        query_embedding = get_embedding(query)
        if query_embedding is None:
            log_service_status("EMBEDDINGS", "warning", "Could not generate embedding for query")
            return []
            
        # Search ChromaDB for similar documents
        results = db_manager.chroma_collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=limit,
            where={"user_id": user_id}  # Filter by user_id
        )
        
        # Format results
        memories = []
        if results and results['documents']:
            for i, doc in enumerate(results['documents'][0]):
                memory = {
                    "content": doc,
                    "metadata": results['metadatas'][0][i] if results['metadatas'] else {},
                    "similarity": 1 - results['distances'][0][i] if results['distances'] else 0.0,
                    "id": results['ids'][0][i] if results['ids'] else f"mem_{i}"
                }
                memories.append(memory)
        
        log_service_status("CHROMADB", "info", f"Retrieved {len(memories)} memories for user {user_id}")
        return memories
        
    except Exception as e:
        log_service_status("CHROMADB", "warning", f"Failed to retrieve user memory: {e}")
        return []
