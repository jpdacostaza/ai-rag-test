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
            # Convert query_text to query for API compatibility
            api_request = {
                "user_id": query.user_id,
                "query": query.query_text,  # API expects 'query' not 'query_text'
                "limit": query.limit,
                "threshold": query.threshold
            }
            
            async with httpx.AsyncClient(timeout=self.config.timeout) as client:
                response = await client.post(
                    f"{self.config.api_url}/api/memory/retrieve",
                    json=api_request
                )
                
                if response.status_code == 200:
                    data = response.json()
                    memories = []
                    for memory in data.get("memories", []):
                        # Add user_id to each memory record since API doesn't include it
                        memory_data = memory.copy()
                        memory_data["user_id"] = query.user_id
                        memories.append(MemoryRecord(**memory_data))
                    
                    return MemoryResponse(
                        success=True,
                        memories=memories,
                        total_count=len(memories)
                    )
                else:
                    error_details = f"Status: {response.status_code}"
                    try:
                        error_data = response.json()
                        error_details += f", Response: {error_data}"
                    except:
                        error_details += f", Text: {response.text}"
                    self.log(f"Memory retrieval failed: {error_details}", "ERROR")
                    return MemoryResponse(
                        success=False,
                        error=f"API returned status {response.status_code}: {error_details}"
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
            # Convert MemoryRecord to MemorySaveRequest format expected by API
            api_request = {
                "user_id": memory.user_id,
                "content": memory.content,
                "metadata": memory.metadata or {},
                "category": memory.metadata.get("category", "explicit") if memory.metadata else "explicit"
            }
            
            async with httpx.AsyncClient(timeout=self.config.timeout) as client:
                response = await client.post(
                    f"{self.config.api_url}/api/memory/save",  # API uses 'save' not 'store'
                    json=api_request
                )
                
                success = response.status_code == 200
                if success:
                    self.log("Memory stored successfully")
                else:
                    error_details = f"Status: {response.status_code}"
                    try:
                        error_data = response.json()
                        error_details += f", Response: {error_data}"
                    except:
                        error_details += f", Text: {response.text}"
                    self.log(f"Memory storage failed: {error_details}", "ERROR")
                    
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
            # Convert interaction to API format
            api_request = {
                "user_id": interaction.user_id,
                "conversation_id": interaction.conversation_id,
                "user_message": interaction.user_message,
                "assistant_response": interaction.assistant_response or "",
                "response_time": 1.0,  # Default value
                "tools_used": [],  # Default empty list
                "context": interaction.metadata or {},  # Use metadata as context
                "timestamp": str(int(interaction.timestamp)) if interaction.timestamp else None,
                "source": interaction.source or "openwebui"
            }
            
            async with httpx.AsyncClient(timeout=self.config.timeout) as client:
                response = await client.post(
                    f"{self.config.api_url}/api/learning/process_interaction",
                    json={k: v for k, v in api_request.items() if v is not None}
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
