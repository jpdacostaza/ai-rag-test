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
    
    def __init__(self, api_url: str = "http://localhost:8001", timeout: int = 30):
        self.api_url = api_url
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
                print(f"⚠️ Database manager import failed: {e}")
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
            print(f"⚠️ Database memory storage failed: {e}")
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
            print(f"⚠️ Database memory retrieval failed: {e}")
            return []
    
    @handle_memory_errors(operation_name="db_delete_memory")
    async def delete_memory(self, user_id: str, memory_id: str) -> bool:
        """Delete memory via database."""
        # Database manager doesn't currently support individual memory deletion
        print(f"⚠️ Database memory deletion not supported")
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
            print(f"⚠️ Database stats failed: {e}")
            return MemoryStats(user_id=user_id, total_memories=0, memory_types={})
    
    @handle_memory_errors(operation_name="db_health_check")
    async def health_check(self) -> bool:
        """Check database health."""
        try:
            db_manager = await self._get_db_manager()
            return db_manager is not None
        except Exception as e:
            print(f"⚠️ Database health check failed: {e}")
            return False


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
        self.logger = logging.getLogger(__name__)
    
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
        return await self.get_memories(user_id, context, max_memories)
    
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
    async def track_conversation_and_store(self, user_id: str, user_message: str,
                                         assistant_response: str) -> bool:
        """
        Track and store conversation (compatibility method).
        
        This replaces main.py memory service calls.
        """
        return await self.track_conversation(user_id, user_message, assistant_response)
    
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


# Global memory service instance
_memory_service_instance: Optional[MemoryService] = None


def create_memory_service(provider_type: MemoryProviderType = MemoryProviderType.API) -> MemoryService:
    """
    Create memory service with specified provider.
    
    Args:
        provider_type: Type of memory provider to use
        
    Returns:
        MemoryService: Configured memory service
    """
    if provider_type == MemoryProviderType.API:
        provider = APIMemoryProvider()
    elif provider_type == MemoryProviderType.DATABASE:
        provider = DatabaseMemoryProvider()
    else:
        # Default to API provider
        provider = APIMemoryProvider()
    
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
