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
from abc import ABC, abstractmethod
from dataclasses import dataclass
from core.logging_config import get_logger
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
    threshold: float = 0.1
    memory_types: Optional[List[str]] = None
    time_range: Optional[Dict[str, str]] = None
    include_metadata: bool = True


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
        self.api_url = api_url or os.getenv('MEMORY_API_URL', 'http://backend-memory-api:5001')
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
        
        payload = {
            "user_id": entry.metadata.user_id,
            "content": entry.content,
            "context": entry.metadata.context,
            "importance": entry.metadata.importance,
            "forced": entry.metadata.explicit,
            "source": entry.metadata.source
        }
        
        response = await client.post(f"{self.api_url}/api/memory/store_explicit", json=payload)
        return response.status_code == 200
    
    @handle_memory_errors(operation_name="api_get_memories")
    async def get_memories(self, query: MemoryQuery) -> List[MemoryEntry]:
        """Retrieve memories via API."""
        client = await self._get_client()
        
        payload = {
            "user_id": query.user_id,
            "query": query.query,
            "limit": query.limit,
            "threshold": query.threshold
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
        except:
            return False


class DatabaseMemoryProvider:
    """Memory provider using direct database access."""
    
    provider_type = "database"
    
    def __init__(self):
        self.db_manager = None
    
    async def _get_db_manager(self):
        """Get database manager."""
        if self.db_manager is None:
            try:
                # Import here to avoid circular imports and config issues
                from services.database_manager import get_database_manager
                self.db_manager = await get_database_manager()
            except Exception as e:
                self.logger.warning("Database manager import failed", error=str(e), provider="database")
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
            from services.database_manager import store_user_memory
            return await store_user_memory(
                user_id=entry.metadata.user_id,
                document_text=entry.content,
                metadata=entry.metadata.__dict__
            )
        except Exception as e:
            self.logger.warning("Database memory storage failed", error=str(e), user_id=entry.metadata.user_id)
            return False
    
    @handle_memory_errors(operation_name="db_get_memories")
    async def get_memories(self, query: MemoryQuery) -> List[MemoryEntry]:
        """Retrieve memories via database."""
        try:
            # Use existing database manager methods
            from services.database_manager import retrieve_user_memory
            
            results = await retrieve_user_memory(
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
            self.logger.warning("Database memory retrieval failed", error=str(e), 
                               user_id=query.user_id, query_text=query.query)
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
            self.logger.warning("Database stats failed", error=str(e), user_id=user_id)
            return MemoryStats(user_id=user_id, total_memories=0, memory_types={})
    
    @handle_memory_errors(operation_name="db_health_check")
    async def health_check(self) -> bool:
        """Check database health."""
        try:
            db_manager = await self._get_db_manager()
            return db_manager is not None
        except Exception as e:
            self.logger.warning("Database health check failed", error=str(e))
            return False


class PipelineMemoryProvider:
    """Memory provider using pipeline/valves architecture."""
    
    provider_type = "pipeline"
    
    def __init__(self):
        self.pipeline_instance = None
        self.pipeline_module = None
        self.logger = get_logger(__name__)
    
    async def _get_pipeline(self):
        """Get or initialize the enhanced memory pipeline."""
        if self.pipeline_instance is None:
            try:
                # Import the enhanced memory pipeline
                import sys
                import os
                
                # Add pipelines directory to path
                pipelines_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "pipelines")
                if pipelines_path not in sys.path:
                    sys.path.insert(0, pipelines_path)
                
                # Import the pipeline module
                from enhanced_memory_pipeline import Pipeline as EnhancedMemoryPipeline
                
                # Initialize pipeline instance
                self.pipeline_instance = EnhancedMemoryPipeline()
                self.pipeline_module = EnhancedMemoryPipeline
                
                # Debug: log available methods
                available_methods = [method for method in dir(self.pipeline_instance) if not method.startswith('_')]
                self.logger.info("Pipeline memory provider initialized", 
                               available_methods=available_methods[:10])  # First 10 methods
                
            except Exception as e:
                self.logger.warning("Pipeline initialization failed", error=str(e))
                self.pipeline_instance = None
        
        return self.pipeline_instance
    
    @handle_memory_errors(operation_name="pipeline_store_memory") 
    async def store_memory(self, entry: MemoryEntry) -> bool:
        """Store memory via pipeline."""
        try:
            pipeline = await self._get_pipeline()
            if not pipeline:
                return False
            
            # Extract data from memory entry
            user_id = entry.metadata.user_id
            content = entry.content
            context = entry.metadata.context
            importance = entry.metadata.importance
            source = entry.metadata.source
            
            # Create memory entry data
            memory_data = {
                "user_id": user_id,
                "content": content,
                "context": context,
                "importance": importance,
                "source": source,
                "timestamp": datetime.now().isoformat()
            }
            
            # Use pipeline's memory storage functionality
            # Debug: Check what methods are available
            pipeline_methods = [method for method in dir(pipeline) if not method.startswith('_')]
            self.logger.info("Available pipeline methods", methods=pipeline_methods[:10])
            
            # Check if pipeline has direct memory methods (new enhanced pipeline)
            if hasattr(pipeline, 'store_memory'):
                self.logger.info("Using pipeline.store_memory method")
                success = await pipeline.store_memory(user_id, content, memory_data)
                if success:
                    self.logger.info("Pipeline memory stored", user_id=user_id)
                    return True
            
            # Check if pipeline has memory_manager property that returns the pipeline itself
            elif hasattr(pipeline, 'memory_manager') and pipeline.memory_manager:
                self.logger.info("Using pipeline.memory_manager.store_memory method")
                success = await pipeline.memory_manager.store_memory(user_id, content, memory_data)
                if success:
                    self.logger.info("Pipeline memory stored via memory_manager", user_id=user_id)
                    return True
            
            # Fallback: use pipeline's internal storage method if available
            elif hasattr(pipeline, '_store_user_memory'):
                self.logger.info("Using pipeline._store_user_memory fallback method")
                await pipeline._store_user_memory(user_id, content, context)
                self.logger.info("Pipeline memory stored with fallback", user_id=user_id)
                return True
            
            self.logger.warning("Pipeline memory storage method not available", 
                              available_methods=pipeline_methods[:5])
            return False
            
        except Exception as e:
            self.logger.error("Pipeline memory storage failed", error=str(e))
            return False
    
    @handle_memory_errors(operation_name="pipeline_get_memories")
    async def get_memories(self, query: MemoryQuery) -> List[MemoryEntry]:
        """Retrieve memories via pipeline."""
        try:
            pipeline = await self._get_pipeline()
            if not pipeline:
                return []
            
            # Use pipeline's memory retrieval functionality
            # Check if pipeline has direct memory methods (new enhanced pipeline)
            if hasattr(pipeline, 'get_relevant_memories'):
                memories_data = await pipeline.get_relevant_memories(
                    query.user_id, 
                    query.query, 
                    query.limit
                )
            elif hasattr(pipeline, 'memory_manager') and pipeline.memory_manager and hasattr(pipeline.memory_manager, 'get_relevant_memories'):
                memories_data = await pipeline.memory_manager.get_relevant_memories(
                    query.user_id, 
                    query.query, 
                    query.limit
                )
            elif hasattr(pipeline, '_get_relevant_memories'):
                # Fallback method
                memories_data = await pipeline._get_relevant_memories(
                    query.user_id,
                    query.query,
                    query.limit
                )
            else:
                self.logger.warning("Pipeline memory retrieval method not available")
                return []
            
            # Convert to MemoryEntry objects
            memories = []
            for memory_data in memories_data:
                if isinstance(memory_data, dict):
                    metadata = MemoryMetadata(
                        user_id=query.user_id,
                        timestamp=memory_data.get("timestamp", datetime.now().isoformat()),
                        source="pipeline",
                        importance=memory_data.get("importance", 0.5),
                        memory_type=memory_data.get("memory_type", "conversation"),
                        context=memory_data.get("context"),
                        conversation_id=memory_data.get("conversation_id"),
                        explicit=memory_data.get("explicit", False)
                    )
                    
                    memories.append(MemoryEntry(
                        content=memory_data.get("content", ""),
                        metadata=metadata,
                        similarity_score=memory_data.get("similarity_score"),
                        distance=memory_data.get("distance", 0.0)
                    ))
            
            self.logger.info("Retrieved memories from pipeline", count=len(memories), user_id=query.user_id)
            return memories
            
        except Exception as e:
            self.logger.error("Pipeline memory retrieval failed", error=str(e))
            return []
    
    @handle_memory_errors(operation_name="pipeline_delete_memory")
    async def delete_memory(self, user_id: str, memory_id: str) -> bool:
        """Delete memory via pipeline."""
        try:
            pipeline = await self._get_pipeline()
            if not pipeline:
                return False
            
            # Check if pipeline supports memory deletion
            if hasattr(pipeline, 'memory_manager') and hasattr(pipeline.memory_manager, 'delete_memory'):
                return await pipeline.memory_manager.delete_memory(user_id, memory_id)
            
            self.logger.warning("Pipeline memory deletion not supported")
            return False
            
        except Exception as e:
            self.logger.error("Pipeline memory deletion failed", error=str(e))
            return False
    
    @handle_memory_errors(operation_name="pipeline_get_stats")
    async def get_stats(self, user_id: str) -> MemoryStats:
        """Get user stats via pipeline."""
        try:
            pipeline = await self._get_pipeline()
            if not pipeline:
                return MemoryStats(user_id=user_id, total_memories=0, memory_types={})
            
            # Get memories to calculate stats
            query = MemoryQuery(user_id=user_id, query="", limit=1000)
            memories = await self.get_memories(query)
            
            # Calculate memory type counts
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
            self.logger.error("Pipeline stats failed", error=str(e))
            return MemoryStats(user_id=user_id, total_memories=0, memory_types={})
    
    @handle_memory_errors(operation_name="pipeline_health_check")
    async def health_check(self) -> bool:
        """Check pipeline health."""
        try:
            pipeline = await self._get_pipeline()
            return pipeline is not None
        except Exception as e:
            self.logger.error("Pipeline health check failed", error=str(e))
            return False
    
    async def cleanup(self):
        """Clean up pipeline resources."""
        try:
            if self.pipeline_instance:
                # Check if pipeline has async cleanup method
                if hasattr(self.pipeline_instance, 'cleanup'):
                    if asyncio.iscoroutinefunction(self.pipeline_instance.cleanup):
                        await self.pipeline_instance.cleanup()
                    else:
                        self.pipeline_instance.cleanup()
                
                # Suppress garbage collection warnings by deleting reference properly
                import warnings
                with warnings.catch_warnings():
                    warnings.filterwarnings("ignore", category=RuntimeWarning, message=".*coroutine.*never awaited.*")
                    self.pipeline_instance = None
                    self.pipeline_module = None
                    
                self.logger.info("Pipeline memory provider cleaned up")
        except Exception as e:
            self.logger.error("Pipeline cleanup failed", error=str(e))


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
                          threshold: float = 0.1) -> List[MemoryEntry]:
        """
        Retrieve memories for a user based on query.
        
        Args:
            user_id: User identifier  
            query: Search query
            limit: Maximum number of memories to return
            threshold: Similarity threshold
            
        Returns:
            List[MemoryEntry]: Retrieved memories
        """
        memory_query = MemoryQuery(
            user_id=user_id,
            query=query,
            limit=limit,
            threshold=threshold
        )
        
        return await self.provider.get_memories(memory_query)
    
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
                                  max_memories: int = 5) -> List[MemoryEntry]:
        """
        Get relevant memories for context injection.
        
        This replaces scattered memory retrieval logic across the codebase.
        
        Args:
            user_id: User identifier
            context: Current conversation context
            max_memories: Maximum memories to retrieve
            
        Returns:
            List[MemoryEntry]: Relevant memories for injection
        """
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
        
        formatted_memories = []
        for memory in memories:
            formatted_memories.append(f"- {memory.content}")
        
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
            self.logger.error("Memory service cleanup failed", error=str(e))


# Global memory service instance
_memory_service_instance: Optional[MemoryService] = None


def create_memory_service(provider_type: MemoryProviderType = MemoryProviderType.PIPELINE) -> MemoryService:
    """
    Create memory service with specified provider.
    
    Args:
        provider_type: Type of memory provider to use (defaults to PIPELINE for pipes/valves architecture)
        
    Returns:
        MemoryService: Configured memory service
    """
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
    
    return _memory_service_instance


def set_memory_service(service: MemoryService) -> None:
    """Set the global memory service instance."""
    global _memory_service_instance
    _memory_service_instance = service


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
