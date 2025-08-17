"""
Memory Service Consolidation Framework
====================================

This module provides a unified memory service interface that consolidates
scattered memory logic across the codebase into a single, cohesive system.

PROBLEM ADDRESSED:
- Memory retrieval/storage logic duplicated in 6+ locations
- Inconsistent behavior between different memory systems
- Multiple memory implementations (database_manager, pipeline, api_client)
- Maintenance overhead from scattered memory logic

SOLUTION:
- Single MemoryService interface with provider pattern
- Unified memory operations across all components
- Pluggable memory backends (API, Database, Pipeline, Local)
- Consistent error handling and logging
- Backward compatibility with existing systems

USAGE:
    from services.memory_service import MemoryService, get_memory_service
    
    # Get unified memory service
    memory_service = get_memory_service()
    
    # Store memories
    await memory_service.store_memory(user_id, content, context)
    
    # Retrieve memories  
    memories = await memory_service.get_memories(user_id, query, limit)
    
    # Track conversations
    await memory_service.track_conversation(user_id, user_message, assistant_response)
"""

import asyncio
import logging
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from core.unified_logging import get_logger
from enum import Enum
from typing import List, Dict, Any, Optional, Union, Protocol
import time
import json
from datetime import datetime

# Import error handling framework
try:
    from utilities.error_patterns import handle_memory_errors, handle_service_errors
except ImportError:
    # Default if error patterns not available
    def handle_memory_errors(operation_name: str = None):
        def decorator(func):
            return func
        return decorator
    
    def handle_service_errors(*args, **kwargs):
        def decorator(func):
            return func
        return decorator


class MemoryProviderType(Enum):
    """Available memory provider types."""
    API = "api"              # Enhanced Memory API (port 8001)
    DATABASE = "database"    # Direct database access (database_manager)
    PIPELINE = "pipeline"    # Pipeline-based access
    LOCAL = "local"          # Local file-based storage


@dataclass
class MemoryMetadata:
    """Metadata for memory entries."""
    user_id: str
    timestamp: str
    source: str
    importance: float = 0.5
    memory_type: str = "conversation"
    context: Optional[str] = None
    conversation_id: Optional[str] = None
    explicit: bool = False


@dataclass
class MemoryEntry:
    """Standardized memory entry format."""
    content: str
    metadata: MemoryMetadata
    similarity_score: Optional[float] = None
    distance: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            "content": self.content,
            "metadata": {
                "user_id": self.metadata.user_id,
                "timestamp": self.metadata.timestamp,
                "source": self.metadata.source,
                "importance": self.metadata.importance,
                "memory_type": self.metadata.memory_type,
                "context": self.metadata.context,
                "conversation_id": self.metadata.conversation_id,
                "explicit": self.metadata.explicit
            },
            "similarity_score": self.similarity_score,
            "distance": self.distance
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MemoryEntry':
        """Create from dictionary format."""
        metadata_dict = data.get("metadata", {})
        metadata = MemoryMetadata(
            user_id=metadata_dict.get("user_id", ""),
            timestamp=metadata_dict.get("timestamp", datetime.now().isoformat()),
            source=metadata_dict.get("source", "unknown"),
            importance=metadata_dict.get("importance", 0.5),
            memory_type=metadata_dict.get("memory_type", "conversation"),
            context=metadata_dict.get("context"),
            conversation_id=metadata_dict.get("conversation_id"),
            explicit=metadata_dict.get("explicit", False)
        )
        
        return cls(
            content=data.get("content", ""),
            metadata=metadata,
            similarity_score=data.get("similarity_score"),
            distance=data.get("distance")
        )


@dataclass 
class MemoryQuery:
    """Memory query parameters."""
    user_id: str
    query: str
    limit: int = 10
    threshold: float = None  # Will be set from unified config
    memory_types: Optional[List[str]] = None
    time_range: Optional[Dict[str, str]] = None
    include_metadata: bool = True
    
    def __post_init__(self):
        """Set threshold from unified config if not provided."""
        if self.threshold is None:
            try:
                from config.config_unified import Config
                config = Config.get_instance()
                # self.threshold = config.memory.retrieval_threshold  # Controlled by OpenWebUI Function
                from config.memory_threshold import get_default_memory_threshold
                self.threshold = get_default_memory_threshold()  # Centralized fallback
            except ImportError:
                # Fallback if unified config not available
                from config.memory_threshold import get_default_memory_threshold
                self.threshold = get_default_memory_threshold()  # Centralized fallback


@dataclass
class MemoryStats:
    """Memory statistics for a user."""
    user_id: str
    total_memories: int
    memory_types: Dict[str, int]
    oldest_memory: Optional[str] = None
    newest_memory: Optional[str] = None
    storage_breakdown: Optional[Dict[str, int]] = None


class MemoryProvider(Protocol):
    """Protocol for memory provider implementations."""
    
    async def store_memory(self, entry: MemoryEntry) -> bool:
        """Store a memory entry."""
        ...
    
    async def get_memories(self, query: MemoryQuery) -> List[MemoryEntry]:
        """Retrieve memories based on query."""
        ...
    
    async def delete_memory(self, user_id: str, memory_id: str) -> bool:
        """Delete a specific memory."""
        ...
    
    async def get_stats(self, user_id: str) -> MemoryStats:
        """Get memory statistics for a user."""
        ...
    
    async def health_check(self) -> bool:
        """Check provider health."""
        ...


class APIMemoryProvider:
    """Memory provider using Enhanced Memory API."""
    
    provider_type = "api"
    
    def __init__(self, api_url: str = None, timeout: int = 30):
        import os
        # Prefer in-cluster Docker service name by default
        self.api_url = api_url or os.getenv('MEMORY_API_URL', 'http://memory-api:5001')
        self.timeout = timeout
        self._client = None
    
    async def _get_client(self):
        """Get HTTP client."""
        if self._client is None:
            import httpx
            self._client = httpx.AsyncClient(timeout=self.timeout)
        return self._client
    
    @handle_memory_errors(operation_name="api_store_memory")
    async def store_memory(self, entry: MemoryEntry) -> bool:
        """Store memory via API."""
        client = await self._get_client()
        
        # Build metadata dictionary for the API
        metadata = {
            "user_id": entry.metadata.user_id,
            "timestamp": entry.metadata.timestamp,
            "source": entry.metadata.source,
            "memory_type": entry.metadata.memory_type,
            "context": entry.metadata.context,
            "conversation_id": entry.metadata.conversation_id,
            "explicit": entry.metadata.explicit
        }
        
        payload = {
            "user_id": entry.metadata.user_id,
            "content": entry.content,
            "metadata": metadata,
            "importance": entry.metadata.importance,
            "memory_type": entry.metadata.memory_type
        }
        
        # Use the standard endpoint (removed explicit endpoint since API doesn't support it)
        endpoint = "/api/memory/store"
        response = await client.post(f"{self.api_url}{endpoint}", json=payload)
        return response.status_code == 200
    
    @handle_memory_errors(operation_name="api_get_memories")
    async def get_memories(self, query: MemoryQuery) -> List[MemoryEntry]:
        """Retrieve memories via API."""
        client = await self._get_client()
        
        payload = {
            "user_id": query.user_id,
            "query": query.query,
            "limit": query.limit,
            "min_score": query.threshold  # API expects min_score, not threshold
        }
        
        response = await client.post(f"{self.api_url}/api/memory/retrieve", json=payload)
        
        if response.status_code == 200:
            data = response.json()
            memories = []
            for memory_data in data.get("memories", []):
                memories.append(MemoryEntry.from_dict(memory_data))
            return memories
        
        return []
    
    @handle_memory_errors(operation_name="api_delete_memory")
    async def delete_memory(self, user_id: str, memory_id: str) -> bool:
        """Delete memory via API."""
        client = await self._get_client()
        
        response = await client.delete(f"{self.api_url}/api/memory/{user_id}/{memory_id}")
        return response.status_code == 200
    
    @handle_memory_errors(operation_name="api_get_stats")
    async def get_stats(self, user_id: str) -> MemoryStats:
        """Get user stats via API."""
        client = await self._get_client()
        
        response = await client.get(f"{self.api_url}/api/memory/stats/{user_id}")
        
        if response.status_code == 200:
            data = response.json()
            return MemoryStats(
                user_id=user_id,
                total_memories=data.get("total_memories", 0),
                memory_types=data.get("memory_types", {}),
                oldest_memory=data.get("oldest_memory"),
                newest_memory=data.get("newest_memory"),
                storage_breakdown=data.get("storage_breakdown")
            )
        
        return MemoryStats(user_id=user_id, total_memories=0, memory_types={})
    
    @handle_memory_errors(operation_name="api_health_check")
    async def health_check(self) -> bool:
        """Check API health."""
        try:
            client = await self._get_client()
            response = await client.get(f"{self.api_url}/health")
            return response.status_code == 200
        except Exception:
            return False


class DatabaseMemoryProvider:
    """Memory provider using direct database access."""
    
    provider_type = "database"
    
    def __init__(self):
        from core.unified_logging import get_logger
        self.logger = get_logger(__name__)
        self.db_manager = None
    
    async def _get_db_manager(self):
        """Get database manager."""
        if self.db_manager is None:
            try:
                # Import the global database manager instance
                from services.database_manager import db_manager
                self.db_manager = db_manager
                # Ensure it's initialized
                if not self.db_manager.is_initialized():
                    await self.db_manager.ensure_initialized()
            except Exception as e:
                self.logger.warning(
                    "Database manager import failed",
                    extra={"error": str(e), "provider": "database"}
                )
                self.db_manager = None
        return self.db_manager
    
    @handle_memory_errors(operation_name="db_store_memory")
    async def store_memory(self, entry: MemoryEntry) -> bool:
        """Store memory via database."""
        try:
            db_manager = await self._get_db_manager()
            if not db_manager:
                return False
            
            # Use existing database manager methods
            from services.database_manager import store_vector_data
            
            # Filter out None values from metadata (ChromaDB doesn't accept None)
            metadata = {
                "user_id": entry.metadata.user_id,
                "timestamp": entry.metadata.timestamp,
                "source": entry.metadata.source,
                "importance": entry.metadata.importance,
                "memory_type": entry.metadata.memory_type,
                "explicit": entry.metadata.explicit
            }
            
            # Only add non-None optional fields
            if entry.metadata.context is not None:
                metadata["context"] = entry.metadata.context
            if entry.metadata.conversation_id is not None:
                metadata["conversation_id"] = entry.metadata.conversation_id
            
            return await store_vector_data(text=entry.content, metadata=metadata)
        except Exception as e:
            self.logger.warning(
                "Database memory storage failed",
                extra={"error": str(e), "user_id": entry.metadata.user_id}
            )
            return False
    
    @handle_memory_errors(operation_name="db_get_memories")
    async def get_memories(self, query: MemoryQuery) -> List[MemoryEntry]:
        """Retrieve memories via database."""
        try:
            # Use the global retrieve_user_memory function (async version)
            import services.database_manager as db_module
                
            results = await db_module.retrieve_user_memory(
                user_id=query.user_id,
                query=query.query,
                n_results=query.limit
            )
            
            memories = []
            for result in results:
                metadata = MemoryMetadata(
                    user_id=query.user_id,
                    timestamp=result.get("metadata", {}).get("timestamp", datetime.now().isoformat()),
                    source=result.get("metadata", {}).get("source", "database"),
                    importance=result.get("metadata", {}).get("importance", 0.5)
                )
                
                memories.append(MemoryEntry(
                    content=result.get("document", ""),
                    metadata=metadata,
                    distance=result.get("distance", 0.0)
                ))
            
            return memories
        except Exception as e:
            self.logger.warning(
                "Database memory retrieval failed",
                extra={"error": str(e), "user_id": query.user_id, "query_text": query.query}
            )
            return []
    
    @handle_memory_errors(operation_name="db_delete_memory")
    async def delete_memory(self, user_id: str, memory_id: str) -> bool:
        """Delete memory via database."""
        # Database manager doesn't currently support individual memory deletion
        self.logger.warning("Database memory deletion not supported", 
                           user_id=user_id, memory_id=memory_id)
        return False
    
    @handle_memory_errors(operation_name="db_get_stats")
    async def get_stats(self, user_id: str) -> MemoryStats:
        """Get user stats via database."""
        try:
            # Get memories to calculate stats
            query = MemoryQuery(user_id=user_id, query="", limit=1000)
            memories = await self.get_memories(query)
            
            memory_types = {}
            for memory in memories:
                mem_type = memory.metadata.memory_type
                memory_types[mem_type] = memory_types.get(mem_type, 0) + 1
            
            return MemoryStats(
                user_id=user_id,
                total_memories=len(memories),
                memory_types=memory_types
            )
        except Exception as e:
            self.logger.warning(
                "Database stats failed",
                extra={"error": str(e), "user_id": user_id}
            )
            return MemoryStats(user_id=user_id, total_memories=0, memory_types={})
    
    @handle_memory_errors(operation_name="db_health_check")
    async def health_check(self) -> bool:
        """Check database health."""
        try:
            db_manager = await self._get_db_manager()
            return db_manager is not None
        except Exception as e:
            self.logger.warning(
                "Database health check failed",
                extra={"error": str(e)}
            )
            return False


class PipelineMemoryProvider:
    """Memory provider using pipeline/valves architecture via HTTP API."""
    
    provider_type = "pipeline"
    
    def __init__(self):
        self.pipeline_service_url = os.getenv('PIPELINES_HOST', 'backend-pipelines')
        self.pipeline_service_port = int(os.getenv('PIPELINES_PORT', '9099'))
        self.base_url = f"http://{self.pipeline_service_url}:{self.pipeline_service_port}"
        self.logger = get_logger(__name__)
        self._client = None
        self.pipeline_available = None
    
    async def _get_http_client(self):
        """Get HTTP client for pipeline service communication."""
        if self._client is None:
            import httpx
            self._client = httpx.AsyncClient(timeout=30.0)
        return self._client
    
    async def _check_pipeline_health(self):
        """Check if pipeline service is available."""
        if self.pipeline_available is None:
            try:
                client = await self._get_http_client()
                response = await client.get(f"{self.base_url}/")
                self.pipeline_available = response.status_code == 200
                if self.pipeline_available:
                    self.logger.info(
                        "Pipeline service connection established",
                        extra={"service_url": self.base_url}
                    )
                else:
                    self.logger.warning(
                        "Pipeline service not responding correctly",
                        extra={"status_code": response.status_code, "service_url": self.base_url}
                    )
            except Exception as e:
                self.pipeline_available = False
                self.logger.warning(
                    "Pipeline service connection failed",
                    extra={"error": str(e), "service_url": self.base_url}
                )
        
        return self.pipeline_available
    
    @handle_memory_errors(operation_name="pipeline_store_memory") 
    async def store_memory(self, entry: MemoryEntry) -> bool:
        """Store memory via pipeline HTTP API."""
        try:
            # Check if pipeline service is available
            if not await self._check_pipeline_health():
                self.logger.warning("Pipeline service not available for memory storage")
                return False
            
            # For now, fall back to the memory API since OpenWebUI pipelines 
            # are designed for chat flow processing, not direct memory API calls
            # The pipeline processes memories through the chat inlet/outlet flow
            memory_api_url = os.getenv('MEMORY_API_URL', 'http://memory-api:5001')
            
            client = await self._get_http_client()
            
            # Build proper metadata for API
            api_metadata = {
                "user_id": entry.metadata.user_id,
                "timestamp": entry.metadata.timestamp,
                "source": entry.metadata.source,
                "memory_type": entry.metadata.memory_type,
                "context": entry.metadata.context,
                "conversation_id": entry.metadata.conversation_id,
                "explicit": entry.metadata.explicit
            }
            
            memory_data = {
                "user_id": entry.metadata.user_id,
                "content": entry.content,
                "metadata": api_metadata,
                "importance": entry.metadata.importance,
                "memory_type": entry.metadata.memory_type
            }
            
            response = await client.post(
                f"{memory_api_url}/api/memory/store",
                json=memory_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                self.logger.info("Pipeline memory stored via API")
                return True
            else:
                self.logger.warning(
                    "Memory storage failed",
                    extra={"status_code": response.status_code, "response": response.text}
                )
                return False
                
        except Exception as e:
            self.logger.error(
                "Pipeline memory storage error",
                extra={"error": str(e)}
            )
            return False

    @handle_memory_errors(operation_name="pipeline_get_memories")
    async def get_memories(self, query: MemoryQuery) -> List[MemoryEntry]:
        """Retrieve memories via pipeline HTTP API."""
        try:
            # Check if pipeline service is available
            if not await self._check_pipeline_health():
                self.logger.warning("Pipeline service not available for memory retrieval")
                return []
            
            # For now, fall back to the memory API since OpenWebUI pipelines 
            # are designed for chat flow processing, not direct memory API calls
            memory_api_url = os.getenv('MEMORY_API_URL', 'http://memory-api:5001')
            
            client = await self._get_http_client()
            request_data = {
                "user_id": query.user_id,
                "query": query.query,
                "limit": query.limit
            }
            
            response = await client.post(
                f"{memory_api_url}/api/memory/retrieve",
                json=request_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                memories_data = response.json()
                # Convert to MemoryEntry objects
                memories = []
                for mem_data in memories_data.get("memories", []):
                    metadata = MemoryMetadata(
                        user_id=mem_data.get("user_id"),
                        context=mem_data.get("context", {}),
                        importance=mem_data.get("importance", 1.0),
                        source=mem_data.get("source", "pipeline")
                    )
                    memory = MemoryEntry(
                        content=mem_data.get("content", ""),
                        metadata=metadata
                    )
                    memories.append(memory)
                
                self.logger.info(
                    "Retrieved memories via pipeline API",
                    extra={"count": len(memories)}
                )
                return memories
            else:
                self.logger.warning(
                    "Memory retrieval failed",
                    extra={"status_code": response.status_code, "response": response.text}
                )
                return []
                
        except Exception as e:
            self.logger.error(
                "Pipeline memory retrieval error",
                extra={"error": str(e)}
            )
            return []

    @handle_memory_errors(operation_name="pipeline_delete_memory")
    async def delete_memory(self, user_id: str, memory_id: str) -> bool:
        """Delete memory via pipeline HTTP API."""
        try:
            # Check if pipeline service is available
            if not await self._check_pipeline_health():
                self.logger.warning("Pipeline service not available for memory deletion")
                return False
            
            # For now, fall back to the memory API since OpenWebUI pipelines 
            # are designed for chat flow processing, not direct memory API calls
            memory_api_url = os.getenv('MEMORY_API_URL', 'http://memory-api:5001')
            
            client = await self._get_http_client()
            response = await client.delete(
                f"{memory_api_url}/api/memory/{user_id}/{memory_id}",
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                self.logger.info("Pipeline memory deleted via API")
                return True
            else:
                self.logger.warning(
                    "Memory deletion failed",
                    extra={"status_code": response.status_code, "response": response.text}
                )
                return False
                
        except Exception as e:
            self.logger.error(
                "Pipeline memory deletion error",
                extra={"error": str(e)}
            )
            return False

    @handle_memory_errors(operation_name="pipeline_get_stats")
    async def get_stats(self, user_id: str) -> MemoryStats:
        """Get user stats via pipeline HTTP API."""
        try:
            # Check if pipeline service is available
            if not await self._check_pipeline_health():
                self.logger.warning("Pipeline service not available for stats")
                return MemoryStats(user_id=user_id, total_memories=0, memory_types={})
            
            # For now, fall back to the memory API since OpenWebUI pipelines 
            # are designed for chat flow processing, not direct memory API calls
            memory_api_url = os.getenv('MEMORY_API_URL', 'http://memory-api:5001')
            
            client = await self._get_http_client()
            response = await client.get(
                f"{memory_api_url}/api/memory/stats/{user_id}",
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                stats_data = response.json()
                return MemoryStats(
                    user_id=user_id,
                    total_memories=stats_data.get("total_memories", 0),
                    memory_types=stats_data.get("memory_types", {})
                )
            else:
                self.logger.warning(
                    "Stats retrieval failed",
                    extra={"status_code": response.status_code, "response": response.text}
                )
                return MemoryStats(user_id=user_id, total_memories=0, memory_types={})
                
        except Exception as e:
            self.logger.error(
                "Pipeline stats error",
                extra={"error": str(e)}
            )
            return MemoryStats(user_id=user_id, total_memories=0, memory_types={})

    @handle_memory_errors(operation_name="pipeline_health_check")
    async def health_check(self) -> bool:
        """Check pipeline health."""
        try:
            return await self._check_pipeline_health()
        except Exception as e:
            self.logger.error(
                "Pipeline health check failed",
                extra={"error": str(e)}
            )
            return False
    
    async def cleanup(self):
        """Clean up pipeline resources."""
        try:
            if self._client:
                await self._client.aclose()
                self._client = None
                
            self.pipeline_available = None
            self.logger.info("Pipeline memory provider cleaned up")
        except Exception as e:
            self.logger.error(
                "Pipeline cleanup failed",
                extra={"error": str(e)}
            )


class MemoryService:
    """
    Unified Memory Service - Single interface for all memory operations.
    
    This service consolidates scattered memory logic from:
    - database_manager.py (retrieve_user_memory)
    - Enhanced Memory Pipeline
    - Memory API Client
    - Main application integration
    - Route dependencies
    
    Provides:
    - Single memory interface across all components
    - Pluggable memory providers (API, Database, Pipeline, Local)
    - Consistent error handling and logging
    - Backward compatibility
    - Performance optimization
    """
    
    def __init__(self, provider: MemoryProvider):
        self.provider = provider
        self.logger = get_logger(__name__)
    
    @property
    def provider_type(self) -> str:
        """Get the type of the current memory provider."""
        if hasattr(self.provider, 'provider_type'):
            return self.provider.provider_type
        else:
            return type(self.provider).__name__.replace('MemoryProvider', '').lower()
    
    @handle_memory_errors(operation_name="store_memory")
    async def store_memory(self, user_id: str, content: str, context: Optional[str] = None,
                          importance: float = 0.5, explicit: bool = False, 
                          source: str = "memory_service") -> bool:
        """
        Store a memory entry.
        
        Args:
            user_id: User identifier
            content: Memory content
            context: Optional context information
            importance: Memory importance (0.0-1.0)
            explicit: Whether this is an explicit memory command
            source: Source of the memory
            
        Returns:
            bool: True if stored successfully
        """
        metadata = MemoryMetadata(
            user_id=user_id,
            timestamp=datetime.now().isoformat(),
            source=source,
            importance=importance,
            context=context,
            explicit=explicit
        )
        
        entry = MemoryEntry(content=content, metadata=metadata)
        return await self.provider.store_memory(entry)
    
    @handle_memory_errors(operation_name="get_memories")
    async def get_memories(self, user_id: str, query: str, limit: int = 10,
                          threshold: float = None) -> List[MemoryEntry]:
        """
        Retrieve memories for a user based on query.
        
        Args:
            user_id: User identifier  
            query: Search query
            limit: Maximum memories to return
            threshold: Similarity threshold (will use unified config if None)
        
        Returns:
            List[MemoryEntry]: Retrieved memories
        """
        # Use unified config threshold if not provided
        if threshold is None:
            try:
                from config.config_unified import Config
                config = Config.get_instance()
                # threshold = config.memory.retrieval_threshold  # Controlled by OpenWebUI Function
                from config.memory_threshold import get_default_memory_threshold
                threshold = get_default_memory_threshold()  # Centralized fallback
            except ImportError:
                from config.memory_threshold import get_default_memory_threshold
                threshold = get_default_memory_threshold()  # Centralized fallback
        
        memory_query = MemoryQuery(
            user_id=user_id,
            query=query,
            limit=limit,
            threshold=threshold
        )
        
        # Metrics instrumentation (lazy import to avoid cycles)
        start_time = time.time()
        memories: List[MemoryEntry] = []
        provider_label = getattr(self.provider, 'provider_type', 'unknown')
        try:
            memories = await self.provider.get_memories(memory_query)
            return memories
        finally:
            try:
                from core.metrics import (
                    METRICS_ENABLED,
                    memory_retrieval_latency_seconds,
                    memory_hits_total,
                    memory_misses_total,
                )
                if METRICS_ENABLED:
                    latency = time.time() - start_time
                    memory_retrieval_latency_seconds.labels(provider_label).observe(latency)
                    if memories:
                        memory_hits_total.labels(provider_label).inc()
                    else:
                        memory_misses_total.labels(provider_label).inc()
            except Exception:
                # Metrics are non-critical; swallow errors
                pass
    
    @handle_memory_errors(operation_name="track_conversation")
    async def track_conversation(self, user_id: str, user_message: str, 
                               assistant_response: str, conversation_id: Optional[str] = None) -> bool:
        """
        Track a conversation interaction for memory storage.
        
        Args:
            user_id: User identifier
            user_message: User's message
            assistant_response: Assistant's response
            conversation_id: Optional conversation identifier
            
        Returns:
            bool: True if tracked successfully
        """
        # Extract important information from the conversation
        content = f"User: {user_message}\nAssistant: {assistant_response}"
        
        metadata = MemoryMetadata(
            user_id=user_id,
            timestamp=datetime.now().isoformat(),
            source="conversation_tracking",
            memory_type="conversation",
            conversation_id=conversation_id
        )
        
        entry = MemoryEntry(content=content, metadata=metadata)
        return await self.provider.store_memory(entry)
    
    @handle_memory_errors(operation_name="get_relevant_memories")
    async def get_relevant_memories(self, user_id: str, context: str, 
                                  max_memories: int = 5, limit: int = None) -> List[MemoryEntry]:
        """
        Get relevant memories for context injection.
        
        This replaces scattered memory retrieval logic across the codebase.
        
        Args:
            user_id: User identifier
            context: Current conversation context
            max_memories: Maximum memories to retrieve
            limit: Alternative parameter name for max_memories (for compatibility)
            
        Returns:
            List[MemoryEntry]: Relevant memories for injection
        """
        # Support both parameter names for compatibility
        if limit is not None:
            max_memories = limit
            
        return await self.get_memories(user_id, query=context, limit=max_memories)
    
    @handle_memory_errors(operation_name="format_memories_for_injection")
    def format_memories_for_injection(self, memories: List[MemoryEntry]) -> str:
        """
        Format memories for context injection.
        
        Args:
            memories: List of memory entries
            
        Returns:
            str: Formatted memory context
        """
        if not memories:
            return ""
        
        # Lazy import to avoid circular dependency
        try:
            from core.security import InputSanitizer
            sanitize = InputSanitizer.sanitize_text
        except Exception:  # pragma: no cover
            def sanitize(x: str) -> str:
                return x.replace('\n', ' ').strip()

        formatted_memories = []
        for memory in memories:
            raw = sanitize(memory.content)
            # Additional hardening: remove any (now escaped) script blocks and obvious JS function calls like alert()
            # We operate on the escaped text (e.g. &lt;script&gt;) produced by sanitizer; strip those segments entirely.
            try:
                import re
                cleaned = re.sub(r"&lt;script&gt;.*?&lt;/script&gt;", "", raw, flags=re.IGNORECASE | re.DOTALL)
                cleaned = re.sub(r"\balert\s*\([^)]*\)", "", cleaned, flags=re.IGNORECASE)
                # Remove lone occurrences of the word 'script' (escaped tag names) if any remain
                cleaned = re.sub(r"\bscript\b", "", cleaned, flags=re.IGNORECASE)
            except Exception:  # pragma: no cover - fallback if re import somehow fails
                cleaned = raw
            # Collapse excessive whitespace created by removals
            cleaned = " ".join(cleaned.split())
            if not cleaned:
                continue  # skip empty remnants
            safe_content = cleaned[:500]  # truncate overly long memory lines
            formatted_memories.append(f"- {safe_content}")
        
        return f"Previous conversations and context:\n" + "\n".join(formatted_memories)
    
    @handle_memory_errors(operation_name="track_conversation_and_store")
    async def track_conversation_and_store(self, user_id: str, user_message: str = None,
                                         assistant_response: str = None, messages: List[Dict[str, Any]] = None) -> bool:
        """
        Track and store conversation (compatibility method).
        
        This replaces main.py memory service calls and supports both calling patterns:
        1. track_conversation_and_store(user_id, user_message, assistant_response)
        2. track_conversation_and_store(user_id, messages=conversation_messages)
        """
        # Handle new calling pattern with messages parameter
        if messages:
            user_msg = ""
            assistant_msg = ""
            
            for msg in messages:
                if msg.get("role") == "user":
                    user_msg = msg.get("content", "")
                elif msg.get("role") == "assistant":
                    assistant_msg = msg.get("content", "")
            
            return await self.track_conversation(user_id, user_msg, assistant_msg)
        
        # Handle legacy calling pattern
        elif user_message and assistant_response:
            return await self.track_conversation(user_id, user_message, assistant_response)
        
        else:
            self.logger.warning("track_conversation_and_store called without proper parameters")
            return False
    
    @handle_memory_errors(operation_name="delete_memory")
    async def delete_memory(self, user_id: str, memory_id: str) -> bool:
        """Delete a specific memory."""
        return await self.provider.delete_memory(user_id, memory_id)
    
    @handle_memory_errors(operation_name="get_user_stats")
    async def get_stats(self, user_id: str) -> MemoryStats:
        """Get memory statistics for a user."""
        return await self.provider.get_stats(user_id)
    
    async def get_memory_stats(self, user_id: str) -> MemoryStats:
        """Alias for get_stats for backward compatibility."""
        return await self.get_stats(user_id)
    
    @handle_memory_errors(operation_name="health_check")
    async def health_check(self) -> bool:
        """Check memory service health."""
        return await self.provider.health_check()
    
    async def cleanup(self):
        """Clean up memory service resources."""
        try:
            if hasattr(self.provider, 'cleanup'):
                await self.provider.cleanup()
            self.logger.info("Memory service cleaned up")
        except Exception as e:
            self.logger.error(
                "Memory service cleanup failed",
                extra={"error": str(e)}
            )


# Global memory service instance
_memory_service_instance: Optional[MemoryService] = None


def create_memory_service(provider_type: MemoryProviderType = MemoryProviderType.PIPELINE) -> MemoryService:
    """Create memory service with specified provider.

    Provider precedence/selection logic (documented for transparency):
    1. Explicit argument (internal callers/tests may pass)
    2. Environment variable MEMORY_PROVIDER (api|database|pipeline|local, case-insensitive)
       - Invalid values fall back to pipeline
    3. Default: PIPELINE (optimized pipes/valves architecture)

    Environment variable allows container runtime override without code change.

    Args:
        provider_type: Preferred provider passed by caller (rarely used externally)
    Returns:
        MemoryService: Configured memory service
    """
    # Environment override
    try:
        env_provider = os.getenv("MEMORY_PROVIDER", "").strip().lower()
        if env_provider:
            mapping = {
                "api": MemoryProviderType.API,
                "database": MemoryProviderType.DATABASE,
                "pipeline": MemoryProviderType.PIPELINE,
                "local": MemoryProviderType.LOCAL,
            }
            provider_type = mapping.get(env_provider, provider_type)
    except Exception:
        pass
    if provider_type == MemoryProviderType.API:
        provider = APIMemoryProvider()
    elif provider_type == MemoryProviderType.DATABASE:
        provider = DatabaseMemoryProvider()
    elif provider_type == MemoryProviderType.PIPELINE:
        provider = PipelineMemoryProvider()
    else:
        # Default to Pipeline provider for pipes/valves architecture
        provider = PipelineMemoryProvider()
    
    return MemoryService(provider)


def get_memory_service() -> MemoryService:
    """
    Get or create the global memory service instance.
    
    This replaces:
    - get_memory_service_or_legacy() in main.py
    - Memory service dependencies in routes
    - Direct database_manager memory calls
    - Pipeline memory access
    
    Returns:
        MemoryService: Global memory service
    """
    global _memory_service_instance
    
    if _memory_service_instance is None:
        _memory_service_instance = create_memory_service()
        try:  # Emit active provider metric once
            from core.metrics import METRICS_ENABLED, memory_provider_active
            if METRICS_ENABLED:
                memory_provider_active.labels(_memory_service_instance.provider_type).inc()
        except Exception:
            pass
    
    return _memory_service_instance


def set_memory_service(service: MemoryService) -> None:
    """Set the global memory service instance."""
    global _memory_service_instance
    _memory_service_instance = service


async def record_memory_provider_health() -> None:
    """Perform a lightweight health check and increment success/failure metric.

    Intended for readiness checks or periodic tasks.
    """
    try:
        service = get_memory_service()
        provider = service.provider_type
        ok = False
        if hasattr(service.provider, 'health_check'):
            try:
                ok = await service.provider.health_check()
            except Exception:
                ok = False
        from core.metrics import METRICS_ENABLED, memory_provider_health
        if METRICS_ENABLED:
            memory_provider_health.labels(provider, 'success' if ok else 'failure').inc()
    except Exception:
        # Swallow all errors; metrics non-critical
        pass


# Backward compatibility functions
async def get_relevant_memories(user_id: str, context: str, max_memories: int = 5) -> List[Dict[str, Any]]:
    """Backward compatibility function for existing code."""
    service = get_memory_service()
    memories = await service.get_relevant_memories(user_id, context, max_memories)
    return [memory.to_dict() for memory in memories]


async def store_user_memory_unified(user_id: str, content: str, context: Optional[str] = None) -> bool:
    """Backward compatibility function for memory storage."""
    service = get_memory_service()
    return await service.store_memory(user_id, content, context)


async def track_conversation_unified(user_id: str, user_message: str, assistant_response: str) -> bool:
    """Backward compatibility function for conversation tracking."""
    service = get_memory_service()
    return await service.track_conversation(user_id, user_message, assistant_response)
