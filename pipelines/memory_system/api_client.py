"""
Memory API Client
=================

Handles all communication with the memory API service.
"""

import asyncio
import httpx
import json
from typing import List, Dict, Any, Optional
import time


class MemoryAPIClient:
    """Client for communicating with the memory API service."""
    
    def __init__(self, backend_url: str, timeout: int = 10, debug: bool = True):
        self.backend_url = backend_url
        self.timeout = timeout
        self.debug = debug
        self._client = None
    
    def log(self, message: str, level: str = "INFO"):
        """Log messages with consistent formatting."""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        print(f"[MEMORY API {level}] {message}")
    
    async def get_client(self):
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        return self._client
    
    async def close(self):
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None
    
    async def health_check(self) -> bool:
        """Check if memory API is healthy."""
        try:
            client = await self.get_client()
            response = await client.get(f"{self.backend_url}/health")
            
            if response.status_code == 200:
                health_data = response.json()
                if self.debug:
                    self.log(f"Memory API health: {health_data}")
                return health_data.get("status") == "healthy"
            
            return False
            
        except Exception as e:
            if self.debug:
                self.log(f"Health check failed: {e}", "ERROR")
            return False
    
    async def get_memories(self, user_id: str, query: str, max_memories: int = 20) -> List[Dict[str, Any]]:
        """Retrieve memories for a user based on query context."""
        try:
            client = await self.get_client()
            
            payload = {
                "user_id": user_id,
                "query": query,
                "max_memories": max_memories
            }
            
            if self.debug:
                self.log(f"Fetching memories for user {user_id}: {len(query)} chars query")
            
            response = await client.post(
                f"{self.backend_url}/api/memory/search",
                json=payload
            )
            
            if response.status_code == 200:
                memories = response.json()
                if self.debug:
                    self.log(f"Retrieved {len(memories)} memories for user {user_id}")
                return memories
            else:
                if self.debug:
                    self.log(f"Failed to get memories: {response.status_code} - {response.text}", "ERROR")
                return []
                
        except Exception as e:
            if self.debug:
                self.log(f"Error getting memories: {e}", "ERROR")
            return []
    
    async def store_interaction(self, user_id: str, user_message: str, assistant_message: str) -> bool:
        """Store a conversation interaction."""
        try:
            client = await self.get_client()
            
            payload = {
                "user_id": user_id,
                "user_message": user_message,
                "assistant_message": assistant_message,
                "timestamp": time.time()
            }
            
            if self.debug:
                self.log(f"Storing interaction for user {user_id}: {len(user_message)} chars user, {len(assistant_message)} chars assistant")
            
            response = await client.post(
                f"{self.backend_url}/api/learning/process_interaction",
                json=payload
            )
            
            if response.status_code == 200:
                result = response.json()
                if self.debug:
                    new_memories = result.get("new_memories", 0)
                    self.log(f"Stored interaction for user {user_id} - New memories: {new_memories}")
                return True
            else:
                if self.debug:
                    self.log(f"Failed to store interaction: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except Exception as e:
            if self.debug:
                self.log(f"Error storing interaction: {e}", "ERROR")
            return False
    
    async def get_user_stats(self, user_id: str) -> Dict[str, Any]:
        """Get memory statistics for a user."""
        try:
            client = await self.get_client()
            
            response = await client.get(f"{self.backend_url}/api/memory/stats/{user_id}")
            
            if response.status_code == 200:
                stats = response.json()
                if self.debug:
                    self.log(f"User {user_id} stats: {stats}")
                return stats
            else:
                if self.debug:
                    self.log(f"Failed to get user stats: {response.status_code}", "ERROR")
                return {}
                
        except Exception as e:
            if self.debug:
                self.log(f"Error getting user stats: {e}", "ERROR")
            return {}
