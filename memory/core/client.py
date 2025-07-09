"""
Memory API Client
=================

HTTP client for interacting with memory APIs.
"""

import asyncio
import uuid
from typing import List, Optional
import httpx

from .interface import IMemoryProvider
from .models import MemoryQuery, MemoryRecord, MemoryResponse, LearningInteraction, MemoryConfig


class MemoryClient(IMemoryProvider):
    """HTTP client for memory API operations."""
    
    def __init__(self, config: MemoryConfig, logger: Optional[callable] = None):
        """
        Initialize the memory client.
        
        Args:
            config: Memory configuration
            logger: Optional logging function
        """
        self.config = config
        self.log = logger or self._default_logger
        
    def _default_logger(self, message: str, level: str = "INFO") -> None:
        """Default logger that does nothing."""
        pass
    
    async def retrieve_memories(self, query: MemoryQuery) -> MemoryResponse:
        """
        Retrieve memories from the API.
        
        Args:
            query: Memory query parameters
            
        Returns:
            MemoryResponse with retrieved memories or empty response on error
        """
        try:
            async with httpx.AsyncClient(timeout=self.config.timeout) as client:
                response = await client.post(
                    f"{self.config.api_url}/api/memory/retrieve",
                    json=query.dict()
                )
                
                if response.status_code == 200:
                    data = response.json()
                    memories = [
                        MemoryRecord(**memory) for memory in data.get("memories", [])
                    ]
                    return MemoryResponse(
                        success=True,
                        memories=memories,
                        total_count=len(memories)
                    )
                else:
                    self.log(f"Memory retrieval failed: {response.status_code}", "ERROR")
                    return MemoryResponse(
                        success=False,
                        error=f"API returned status {response.status_code}"
                    )
                    
        except Exception as e:
            self.log(f"Error retrieving memories: {str(e)}", "ERROR")
            return MemoryResponse(
                success=False,
                error=f"Connection error: {str(e)}"
            )
    
    async def store_memory(self, memory: MemoryRecord) -> bool:
        """
        Store a memory record.
        
        Args:
            memory: Memory record to store
            
        Returns:
            bool: Success status
        """
        try:
            async with httpx.AsyncClient(timeout=self.config.timeout) as client:
                response = await client.post(
                    f"{self.config.api_url}/api/memory/store",
                    json=memory.dict(exclude_none=True)
                )
                
                success = response.status_code == 200
                if success:
                    self.log("Memory stored successfully")
                else:
                    self.log(f"Memory storage failed: {response.status_code}", "ERROR")
                    
                return success
                
        except Exception as e:
            self.log(f"Error storing memory: {str(e)}", "ERROR")
            return False
    
    async def store_interaction(self, interaction: LearningInteraction) -> bool:
        """
        Store a learning interaction.
        
        Args:
            interaction: Learning interaction to store
            
        Returns:
            bool: Success status
        """
        try:
            async with httpx.AsyncClient(timeout=self.config.timeout) as client:
                response = await client.post(
                    f"{self.config.api_url}/api/learning/process_interaction",
                    json=interaction.dict()
                )
                
                success = response.status_code == 200
                if success:
                    self.log("Learning interaction stored successfully")
                else:
                    self.log(f"Learning storage failed: {response.status_code}", "ERROR")
                    
                return success
                
        except Exception as e:
            self.log(f"Error storing learning interaction: {str(e)}", "ERROR")
            return False
    
    async def delete_memory(self, memory_id: str, user_id: str) -> bool:
        """
        Delete a memory record.
        
        Args:
            memory_id: ID of memory to delete
            user_id: User ID for authorization
            
        Returns:
            bool: Success status
        """
        try:
            async with httpx.AsyncClient(timeout=self.config.timeout) as client:
                response = await client.delete(
                    f"{self.config.api_url}/api/memory/{memory_id}",
                    params={"user_id": user_id}
                )
                
                success = response.status_code == 200
                if success:
                    self.log(f"Memory {memory_id} deleted successfully")
                else:
                    self.log(f"Memory deletion failed: {response.status_code}", "ERROR")
                    
                return success
                
        except Exception as e:
            self.log(f"Error deleting memory: {str(e)}", "ERROR")
            return False
    
    async def health_check(self) -> bool:
        """
        Check memory API health.
        
        Returns:
            bool: Health status
        """
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.config.api_url}/health")
                return response.status_code == 200
                
        except Exception as e:
            self.log(f"Memory API health check failed: {str(e)}", "ERROR")
            return False
