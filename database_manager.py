"""
DatabaseManager class for FastAPI LLM backend.
Handles Redis, chromadb, and embedding model management with enhanced logging.
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

# Alert manager integration
try:
    from utilities.alert_manager import alert_memory_pressure, alert_service_down
except ImportError:
    # Fallback if alert manager is not available
    async def alert_memory_pressure(percentage: float, component: str = "database"):
        pass
    async def alert_service_down(service_name: str, duration_seconds: float):
        pass

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
    """Database manager class for handling Redis and chromadb connections."""

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
        
        # Initialization status tracking
        self._initialized = False
        self._initialization_failed = False
        
        # Service health tracking
        self._service_start_times = {}
        self._service_downtime_alerts = {}
        
        # Don't initialize during construction - wait for proper event loop
        log_service_status("database_manager", "info", "Database manager created on module import")
        
    async def _initialize_all(self):
        """Initialize all components with proper error handling."""
        redis_success = False
        try:
            await self._initialize_redis()
            redis_success = True
        except Exception as e:
            log_service_status("database_manager", "warning", f"Redis initialization failed: {str(e)}. Continuing with other components.")
            # Don't set _initialization_failed = True or return early
            # Redis can be reconnected later, but we should still initialize embeddings and ChromaDB

        # Initialize Chroma and Embeddings independently - they are optional and will handle their own errors/retries
        await self._initialize_chroma()
        await self._initialize_embedding_model()
        
        self._initialized = True
        if redis_success:
            log_service_status("database_manager", "info", "Database components initialization process completed successfully.")
        else:
            log_service_status("database_manager", "info", "Database components initialization completed (Redis connection pending).")
            
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
                log_service_status("redis", "info", "Redis initialized successfully")
        except redis.ConnectionError as e:
            log_service_status("redis", "error", f"Redis initialization failed: {str(e)}")
            raise
            
    async def _initialize_chroma(self):
        """Initialize chromadb client with retry logic and graceful degradation."""
        from config import CHROMA_HOST, CHROMA_PORT, USE_HTTP_CHROMA
        
        chroma_host = CHROMA_HOST
        chroma_port = CHROMA_PORT
        max_retries = int(os.getenv("CHROMA_INIT_MAX_RETRIES", "3"))
        retry_delay = int(os.getenv("CHROMA_INIT_RETRY_DELAY", "5"))
        use_http_chroma = USE_HTTP_CHROMA

        log_service_status("chromadb", "info", f"Attempting ChromaDB connection to {chroma_host}:{chroma_port}")

        for attempt in range(max_retries):
            try:
                async with self._chroma_lock:
                    if use_http_chroma:
                        # Use HttpClient for connecting to remote ChromaDB service
                        self.chroma_client = cast(ChromaClientProtocol, chromadb.HttpClient(
                            host=chroma_host, 
                            port=chroma_port,
                            settings=Settings(anonymized_telemetry=False)
                        ))
                    else:
                        # Use persistent client for local/embedded ChromaDB
                        settings = Settings(
                            chroma_api_impl="rest",
                            chroma_server_host=chroma_host,
                            chroma_server_http_port=chroma_port,
                            anonymized_telemetry=False
                        )
                        self.chroma_client = cast(ChromaClientProtocol, chromadb.Client(settings))
                    
                    # Test connection
                    self.chroma_client.heartbeat()
                    
                    collection_name = os.getenv("CHROMA_COLLECTION", "default")
                    self.chroma_collection = self.chroma_client.get_or_create_collection(
                        name=collection_name,
                        metadata={"description": "Default vector store for embeddings"}
                    )
                    
                    log_service_status("chromadb", "info", f"ChromaDB initialized successfully on {chroma_host}:{chroma_port}")
                    return
            except Exception as e:
                log_service_status("chromadb", "warning", f"ChromaDB initialization attempt {attempt + 1}/{max_retries} failed: {str(e)}")
                if attempt < max_retries - 1:
                    log_service_status("chromadb", "info", f"Retrying in {retry_delay} seconds...")
                    await asyncio.sleep(retry_delay)
        
        log_service_status("chromadb", "error", "ChromaDB initialization failed after multiple retries. Service will be unavailable.")
        log_service_status("chromadb", "info", "💡 To fix: Check 'docker-compose ps' and ensure ChromaDB container is running")
        self.chroma_client = None
        self.chroma_collection = None
            
    async def _initialize_embedding_model(self):
        """Initialize the embedding model with automatic downloading if needed."""
        if os.getenv("DISABLE_EMBEDDINGS", "false").lower() == "true":
            log_service_status("embeddings", "info", "Embeddings are disabled via environment variable.")
            self.embedding_model = None
            return

        try:
            from config import EMBEDDING_MODEL, EMBEDDING_PROVIDER, SENTENCE_TRANSFORMERS_HOME, AUTO_PULL_MODELS
            
            model_name = EMBEDDING_MODEL
            provider = EMBEDDING_PROVIDER.lower()
            
            log_service_status("embeddings", "info", f"Initializing embedding model '{model_name}' with provider '{provider}'...")
            
            if provider == "huggingface":
                await self._initialize_huggingface_model(model_name)
            elif provider == "ollama":
                await self._initialize_ollama_model(model_name)
            else:
                log_service_status("embeddings", "error", f"Unknown embedding provider '{provider}'. Supported: 'huggingface', 'ollama'")
                self.embedding_model = None

        except Exception as e:
            log_service_status("embeddings", "error", f"Embedding model initialization failed: {str(e)}. Service will be unavailable.")
            self.embedding_model = None

    async def _initialize_huggingface_model(self, model_name: str):
        """Initialize a HuggingFace SentenceTransformers model."""
        try:
            from config import SENTENCE_TRANSFORMERS_HOME, AUTO_PULL_MODELS
            import os
            
            # Set the cache directory for models
            os.environ['SENTENCE_TRANSFORMERS_HOME'] = SENTENCE_TRANSFORMERS_HOME
            
            # Set the cache directory for models
            os.environ['SENTENCE_TRANSFORMERS_HOME'] = SENTENCE_TRANSFORMERS_HOME
            os.makedirs(SENTENCE_TRANSFORMERS_HOME, exist_ok=True)
            
            # SentenceTransformers handles downloading automatically if model doesn't exist
            log_service_status("embeddings", "info", f"📥 Loading/downloading model '{model_name}'...")
            
            def load_or_download_model():
                from sentence_transformers import SentenceTransformer
                try:
                    # This will download the model if it doesn't exist, or load from cache if it does
                    model = SentenceTransformer(model_name, cache_folder=SENTENCE_TRANSFORMERS_HOME)
                    return model
                except Exception as e:
                    log_service_status("embeddings", "error", f"Failed to load/download model '{model_name}': {e}")
                    return None
            
            # Load or download the model in a thread to avoid blocking the event loop
            model = await asyncio.to_thread(load_or_download_model)
            
            if model is not None:
                self.embedding_model = model
                log_service_status("embeddings", "info", f"✅ Successfully loaded model '{model_name}'")
                log_service_status("embeddings", "info", f"📊 Model dimensions: {model.get_sentence_embedding_dimension()}")
            else:
                log_service_status("embeddings", "error", f"Failed to load model '{model_name}'")
                self.embedding_model = None
                
        except ImportError:
            log_service_status("embeddings", "error", "sentence-transformers library not available. Install with: pip install sentence-transformers")
            self.embedding_model = None
        except Exception as e:
            log_service_status("embeddings", "error", f"Error initializing HuggingFace model '{model_name}': {str(e)}")
            self.embedding_model = None

    async def _initialize_ollama_model(self, model_name: str):
        """Initialize an Ollama embedding model."""
        try:
            from config import OLLAMA_BASE_URL, AUTO_PULL_MODELS
            import httpx
            
            # Test if Ollama is available and has the model
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Check if Ollama is running
                try:
                    response = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
                    if response.status_code == 200:
                        models = response.json().get("models", [])
                        model_names = [model.get("name", "").split(":")[0] for model in models]
                        
                        if model_name in model_names:
                            log_service_status("embeddings", "info", f"✅ Embedding model '{model_name}' found in Ollama")
                            self.embedding_model = model_name  # Store model name for Ollama usage
                            return
                        else:
                            log_service_status("embeddings", "info", f"Model '{model_name}' not found. Available models: {model_names}")
                            log_service_status("embeddings", "info", f"� Automatically pulling model '{model_name}'...")
                            
                            # Attempt to pull the model automatically
                            await self._pull_embedding_model(client, model_name)
                            return
                    else:
                        log_service_status("embeddings", "warning", f"Ollama returned status {response.status_code}")
                        
                except Exception as e:
                    log_service_status("embeddings", "warning", f"Cannot connect to Ollama at {OLLAMA_BASE_URL}: {e}")
                    log_service_status("embeddings", "info", "💡 To fix: Ensure Ollama is running with 'docker-compose up -d ollama'")
            
            # Fallback: mark as unavailable but don't fail startup
            log_service_status("embeddings", "error", "Ollama embedding model initialization failed. Service will be unavailable.")
            self.embedding_model = None

        except Exception as e:
            log_service_status("embeddings", "error", f"Ollama embedding model initialization failed: {str(e)}. Service will be unavailable.")
            self.embedding_model = None
            
    async def _pull_embedding_model(self, client: Any, model_name: str) -> None:
        """Pull the embedding model from Ollama."""
        try:
            from config import OLLAMA_BASE_URL
            
            # Start the pull request
            pull_response = await client.post(
                f"{OLLAMA_BASE_URL}/api/pull",
                json={"name": model_name},
                timeout=300.0  # 5 minutes timeout for model pulling
            )
            
            if pull_response.status_code == 200:
                log_service_status("embeddings", "info", f"✅ Successfully pulled model '{model_name}'")
                self.embedding_model = model_name
                
                # Verify the model is now available
                verify_response = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
                if verify_response.status_code == 200:
                    models = verify_response.json().get("models", [])
                    model_names = [model.get("name", "").split(":")[0] for model in models]
                    if model_name in model_names:
                        log_service_status("embeddings", "info", f"✅ Model '{model_name}' verified and ready")
                    else:
                        log_service_status("embeddings", "warning", f"Model '{model_name}' pull succeeded but not found in model list")
            else:
                log_service_status("embeddings", "error", f"Failed to pull model '{model_name}': HTTP {pull_response.status_code}")
                log_service_status("embeddings", "info", f"💡 Manual fix: Run 'docker exec backend-ollama ollama pull {model_name}'")
                self.embedding_model = None
                
        except Exception as e:
            log_service_status("embeddings", "error", f"Error pulling model '{model_name}': {str(e)}")
            log_service_status("embeddings", "info", f"💡 Manual fix: Run 'docker exec backend-ollama ollama pull {model_name}'")
            self.embedding_model = None

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
            f"Successfully connected to chromadb and accessed collection '{collection_name}'",
        )

    def _verify_chroma_connection(self):
        """Verify chromadb connection by listing collections."""
        if not self.chroma_client:
            log_service_status("chromadb", "error", "chromadb client not initialized")
            return
            
        try:
            collections = self.chroma_client.list_collections()
            log_service_status(
                "chromadb", "ready", f"Found {len(collections)} existing collections"
            )
        except Exception as e:
            log_service_status("chromadb", "degraded", f"Could not list collections: {e}")

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
                "status": "healthy" if chroma_available else "degraded",
                "details": "Connected and responsive" if chroma_available else "Not available"
            },
            "embeddings": {
                "status": "healthy" if embeddings_available else "degraded",
                "details": "Model loaded and ready" if embeddings_available else "Not available"
            }
        }

    async def execute_redis_operation(self, operation: Any, operation_name: str) -> Any:
        """Execute a Redis operation with proper error handling."""
        if not self.redis_client:
            log_service_status("redis", "error", f"Redis not available for operation: {operation_name}")
            return None

        try:
            async with self._redis_lock:
                result = operation(self.redis_client)
                return result
        except redis.RedisError as e:
            log_service_status("redis", "error", f"Redis operation '{operation_name}' failed: {str(e)}")
            try:
                await self._initialize_redis()
                if self.redis_client:
                    async with self._redis_lock:
                        result = operation(self.redis_client)
                        return result
            except redis.RedisError as e2:
                log_service_status("redis", "error", f"Retry failed for '{operation_name}': {str(e2)}")
            return None
            
    async def _handle_memory_pressure(self):
        """Handle high memory pressure situations."""
        try:
            # Clear Redis cache if available
            if self.redis_client:
                await self.redis_client.flushdb()
                
            # Clear cache manager
            self.cache_manager.clear()
                
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
        """Get embedding for text using the configured provider (HuggingFace or Ollama)."""
        if not self.embedding_model:
            log_service_status("embeddings", "error", "Embedding model not available")
            return None
            
        try:
            from config import EMBEDDING_PROVIDER
            provider = EMBEDDING_PROVIDER.lower()
            
            if provider == "huggingface":
                # Use SentenceTransformers model directly
                if hasattr(self.embedding_model, 'encode'):
                    # Add the query prefix for e5 models
                    if "e5-" in str(self.embedding_model).lower():
                        prefixed_text = f"query: {text}"
                    else:
                        prefixed_text = text
                    
                    # Run embedding generation in a thread to avoid blocking
                    embedding = await asyncio.to_thread(
                        self.embedding_model.encode, 
                        [prefixed_text], 
                        normalize_embeddings=True
                    )
                    return embedding[0].tolist() if len(embedding) > 0 else None
                else:
                    log_service_status("embeddings", "error", "HuggingFace model does not have encode method")
                    return None
                    
            elif provider == "ollama":
                # Use Ollama via LLM service
                from services.llm_service import llm_service
                embedding = await llm_service.get_embeddings(text, self.embedding_model)
                return embedding
            else:
                log_service_status("embeddings", "error", f"Unknown provider '{provider}'")
                return None
                
        except Exception as e:
            log_service_status("embeddings", "error", f"Error generating embedding: {str(e)}")
            return None

    async def get_chat_history(self, chat_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get chat history from Redis."""
        def get_operation(redis_client: redis.Redis) -> List[Dict[str, Any]]:
            chat_key = f"chat:{chat_id}"
            try:
                # lrange returns a list of bytes or str
                entries = redis_client.lrange(chat_key, 0, limit - 1)
                if not isinstance(entries, list):
                    log_service_status("redis", "warning", f"Cache miss - no history found for chat_id: {chat_id}")
                    return []
                
                if len(entries) == 0:
                    log_service_status("redis", "info", f"Cache miss - empty history for chat_id: {chat_id}")
                else:
                    log_service_status("redis", "info", f"Cache hit - retrieved {len(entries)} messages for chat_id: {chat_id}")
                    
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
            except redis.RedisError as e:
                log_service_status("redis", "error", f"Cache error - failed to get history for chat_id: {chat_id}, error: {str(e)}")
                return []
            
        result = await self.execute_redis_operation(get_operation, "get_chat_history")
        return result if result is not None else []
        
    async def store_chat_entry(self, chat_id: str, chat_entry: Dict[str, Any]) -> bool:
        """Store a chat entry in Redis."""
        def store_operation(redis_client: redis.Redis) -> bool:
            chat_key = f"chat:{chat_id}"
            redis_client.lpush(chat_key, json.dumps(chat_entry))
            log_service_status("redis", "info", f"Cache write - stored message for chat_id: {chat_id}, role: {chat_entry.get('role', 'unknown')}")
            return True
            
        return await self.execute_redis_operation(store_operation, "store_chat") or False
        
    async def query_chroma(self, query_text: str, n_results: int = 5) -> Optional[Dict[str, Any]]:
        """Query the chromadb collection."""
        if not self.chroma_collection or not self.embedding_model:
            log_service_status("chromadb", "error", "chromadb collection or embedding model not available")
            return None
        
        try:
            start_time = time.time()
            
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
            
            query_time = time.time() - start_time
            
            if not results or not isinstance(results, dict):
                log_service_status("memory", "warning", f"Memory miss - no results found for query: '{query_text[:50]}...'")
                return None
            
            num_results = len(results.get("documents", [[]])[0])
            if num_results == 0:
                log_service_status("memory", "info", f"Memory miss - no matches for query: '{query_text[:50]}...' (query_time: {query_time:.3f}s)")
            else:
                log_service_status("memory", "info", f"Memory hit - found {num_results} matches for query: '{query_text[:50]}...' (query_time: {query_time:.3f}s)")
                
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
            log_service_status("chromadb", "error", f"Error querying chromadb: {str(e)}")
            return None

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
            "embeddings": self._check_embeddings_health
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
            await asyncio.to_thread(self.redis_client.ping)
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
            # Try a simple encoding as a health check
            await asyncio.to_thread(self.embedding_model.encode, ["test"])
            return True
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
                "alerts": {"status": "unhealthy", "details": "Database manager not available"}
            }
    
    # Ensure initialization is complete
    await db_manager.ensure_initialized()
    health_status = cast(Dict[str, Any], await db_manager.get_health_status())
    
    # Add cache statistics
    cache_stats = db_manager.get_cache_stats()
    health_status["cache"] = {
        "status": "healthy",
        "details": f"Cache operational - {cache_stats['hit_rate']} hit rate",
        "stats": cache_stats
    }
    
    # Add alert manager statistics
    try:
        from utilities.alert_manager import get_alert_manager
        alert_manager = get_alert_manager()
        alert_stats = alert_manager.get_alert_stats()
        health_status["alerts"] = {
            "status": "healthy",
            "details": f"Alert system operational - {alert_stats['total_alerts']} total alerts",
            "stats": alert_stats
        }
    except Exception as e:
        health_status["alerts"] = {
            "status": "degraded",
            "details": f"Alert system error: {str(e)}"
        }
    
    return health_status


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
        
    # Add to chromadb
    try:
        collection = db_manager.chroma_collection
        if not collection:
            return False
            
        doc_id = str(time.time())
        collection.add(
            embeddings=[embedding],
            documents=[text],
            metadatas=[metadata],
            ids=[doc_id]
        )
        log_service_status("memory", "info", f"Memory write - stored document (id: {doc_id}, size: {len(text)} chars, user: {metadata.get('user_id', 'unknown')})")
        return True
    except Exception as e:
        log_service_status("chromadb", "error", f"Error storing vector data: {str(e)}")
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

async def get_cache_async() -> CacheManager[Any]:
    """Get the global cache manager instance (async)."""
    global db_manager
    if not db_manager:
        await initialize_database()
        if not db_manager:
            raise RuntimeError("Database manager not initialized")
    return db_manager.get_cache()

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
    
    def store_operation(redis_client: redis.Redis) -> bool:
        chat_key = f"chat:{chat_id}"
        # Clear existing history
        redis_client.delete(chat_key)
        # Store new history
        for message in messages:
            redis_client.lpush(chat_key, json.dumps(message))
        log_service_status("redis", "info", f"Cache write - stored {len(messages)} messages for chat_id: {chat_id}")
        return True
        
    result = await db_manager.execute_redis_operation(store_operation, "store_chat_history")
    return result if result is not None else False

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
    
    log_service_status("memory", "info", f"Memory indexing - user: {user_id}, document size: {len(document_text)} chars")
    return await store_vector_data(document_text, metadata)

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
            include=["documents", "metadatas", "distances"]
        )
        
        query_time = time.time() - start_time
        
        if not results or not isinstance(results, dict):
            log_service_status("memory", "warning", f"Memory miss - no user memories found for user: {user_id}, query: '{query[:50]}...'")
            return []
        
        memories = []
        for doc, meta, dist in zip(
            results.get("documents", [[]])[0],
            results.get("metadatas", [[{}]])[0], 
            results.get("distances", [[0.0]])[0]
        ):
            memories.append({
                "document": doc,
                "metadata": meta,
                "distance": dist
            })
        
        if len(memories) == 0:
            log_service_status("memory", "info", f"Memory miss - no matches for user: {user_id}, query: '{query[:50]}...' (query_time: {query_time:.3f}s)")
        else:
            log_service_status("memory", "info", f"Memory hit - found {len(memories)} memories for user: {user_id}, query: '{query[:50]}...' (query_time: {query_time:.3f}s)")
        
        return memories
    except Exception as e:
        log_service_status("chromadb", "error", f"Error retrieving user memory: {str(e)}")
        return []
