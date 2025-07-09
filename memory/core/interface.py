"""
Memory Provider Interface
========================

Abstract interface for memory providers to ensure consistency.
"""

from abc import ABC, abstractmethod
from typing import List, Optional

from .models import MemoryQuery, MemoryRecord, MemoryResponse, LearningInteraction


class IMemoryProvider(ABC):
    """Abstract interface for memory providers."""
    
    @abstractmethod
    async def retrieve_memories(self, query: MemoryQuery) -> MemoryResponse:
        """
        Retrieve memories based on query.
        
        Args:
            query: Memory query with user_id, text, and filters
            
        Returns:
            MemoryResponse with retrieved memories
        """
        pass
    
    @abstractmethod
    async def store_memory(self, memory: MemoryRecord) -> bool:
        """
        Store a single memory record.
        
        Args:
            memory: Memory record to store
            
        Returns:
            bool: Success status
        """
        pass
    
    @abstractmethod
    async def store_interaction(self, interaction: LearningInteraction) -> bool:
        """
        Store a learning interaction.
        
        Args:
            interaction: Learning interaction to store
            
        Returns:
            bool: Success status
        """
        pass
    
    @abstractmethod
    async def delete_memory(self, memory_id: str, user_id: str) -> bool:
        """
        Delete a memory record.
        
        Args:
            memory_id: ID of memory to delete
            user_id: User ID for authorization
            
        Returns:
            bool: Success status
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """
        Check if the memory provider is healthy.
        
        Returns:
            bool: Health status
        """
        pass
