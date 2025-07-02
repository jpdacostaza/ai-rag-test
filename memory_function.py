"""
Enhanced Memory Function for OpenWebUI
=====================================

A comprehensive memory system that integrates with the backend memory API
to provide persistent conversation context and learning capabilities.

NOTE: This is the primary memory function file used by the system.
The file at memory/functions/memory_filter.py serves as a fallback
in case this file is not available.
"""

import json
import time
import uuid
from typing import Dict, List, Optional, Any
from pydantic import BaseModel

try:
    import httpx
except ImportError:
    import subprocess
    import sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "httpx"])
    import httpx


class Valves(BaseModel):
    """Configuration valves for the memory function."""
    
    # API Configuration
    backend_api_url: str = "http://backend:3000"
    memory_api_url: str = "http://memory_api:8080"
    
    # Memory Settings
    enable_memory: bool = True
    max_memories: int = 5
    memory_threshold: float = 0.1
    
    # Learning Settings
    enable_learning: bool = True
    auto_store_threshold: int = 3  # Store after 3+ exchanges
    
    # Debug
    debug: bool = False


class Filter:
    """Enhanced Memory Filter for OpenWebUI."""
    
    def __init__(self):
        self.valves = Valves()
        self.conversation_count = {}
        
    def log(self, message: str, level: str = "INFO"):
        """Log messages with timestamp."""
        if self.valves.debug:
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            print(f"[{timestamp}] [{level}] [Memory] {message}")
    
    async def inlet(self, body: dict, user: Optional[dict] = None) -> dict:
        """Process incoming messages to inject relevant memories."""
        if not self.valves.enable_memory:
            return body
            
        try:
            # Extract user information
            user_id = self._get_user_id(user)
            messages = body.get("messages", [])
            
            if not messages:
                return body
                
            # Get the latest user message
            latest_message = None
            for msg in reversed(messages):
                if msg.get("role") == "user":
                    latest_message = msg.get("content", "")
                    break
                    
            if not latest_message:
                return body
                
            self.log(f"Processing message for user {user_id}: {latest_message[:100]}...")
            
            # Retrieve relevant memories
            memories = await self._retrieve_memories(user_id, latest_message)
            
            if memories:
                # Inject memories into the conversation
                memory_context = self._format_memories(memories)
                body = self._inject_memory_context(body, memory_context)
                self.log(f"Injected {len(memories)} memories into conversation")
            
        except Exception as e:
            self.log(f"Error in inlet: {str(e)}", "ERROR")
            
        return body
    
    async def outlet(self, body: dict, user: Optional[dict] = None) -> dict:
        """Process outgoing messages to store learning data."""
        if not self.valves.enable_learning:
            return body
            
        try:
            user_id = self._get_user_id(user)
            messages = body.get("messages", [])
            
            # Track conversation count for auto-storage
            self.conversation_count[user_id] = self.conversation_count.get(user_id, 0) + 1
            
            # Store learning data if threshold met
            if self.conversation_count[user_id] >= self.valves.auto_store_threshold:
                await self._store_learning_interaction(user_id, messages)
                self.conversation_count[user_id] = 0  # Reset counter
                
        except Exception as e:
            self.log(f"Error in outlet: {str(e)}", "ERROR")
            
        return body
    
    def _get_user_id(self, user: Optional[dict]) -> str:
        """Extract user ID from user object."""
        if user and isinstance(user, dict):
            return user.get("id", user.get("user_id", "anonymous"))
        return "anonymous"
    
    async def _retrieve_memories(self, user_id: str, query: str) -> List[dict]:
        """Retrieve relevant memories from the memory API."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{self.valves.memory_api_url}/api/memory/retrieve",
                    json={
                        "user_id": user_id,
                        "query": query,
                        "limit": self.valves.max_memories,
                        "threshold": self.valves.memory_threshold
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data.get("memories", [])
                else:
                    self.log(f"Memory retrieval failed: {response.status_code}", "ERROR")
                    
        except Exception as e:
            self.log(f"Error retrieving memories: {str(e)}", "ERROR")
            
        return []
    
    async def _store_learning_interaction(self, user_id: str, messages: List[dict]):
        """Store learning interaction in the memory system."""
        try:
            # Extract user and assistant messages
            user_message = ""
            assistant_response = ""
            
            for msg in reversed(messages):
                if msg.get("role") == "user" and not user_message:
                    user_message = msg.get("content", "")
                elif msg.get("role") == "assistant" and not assistant_response:
                    assistant_response = msg.get("content", "")
                    
            if user_message and assistant_response:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.post(
                        f"{self.valves.memory_api_url}/api/learning/process_interaction",
                        json={
                            "user_id": user_id,
                            "conversation_id": str(uuid.uuid4()),
                            "user_message": user_message,
                            "assistant_response": assistant_response,
                            "timestamp": time.time(),
                            "source": "openwebui_function"
                        }
                    )
                    
                    if response.status_code == 200:
                        self.log("Learning interaction stored successfully")
                    else:
                        self.log(f"Learning storage failed: {response.status_code}", "ERROR")
                        
        except Exception as e:
            self.log(f"Error storing learning interaction: {str(e)}", "ERROR")
    
    def _format_memories(self, memories: List[dict]) -> str:
        """Format memories for injection into conversation."""
        if not memories:
            return ""
            
        formatted = "## Relevant Context from Previous Conversations:\n\n"
        
        for i, memory in enumerate(memories, 1):
            content = memory.get("content", "")
            relevance = memory.get("relevance_score", 0)
            
            formatted += f"**Context {i}** (relevance: {relevance:.2f}):\n"
            formatted += f"{content}\n\n"
            
        formatted += "---\n\n"
        return formatted
    
    def _inject_memory_context(self, body: dict, memory_context: str) -> dict:
        """Inject memory context into the conversation."""
        messages = body.get("messages", [])
        
        if not messages or not memory_context:
            return body
            
        # Find the last user message and inject context before it
        for i in range(len(messages) - 1, -1, -1):
            if messages[i].get("role") == "user":
                original_content = messages[i].get("content", "")
                
                # Inject memory context
                enhanced_content = f"{memory_context}{original_content}"
                messages[i]["content"] = enhanced_content
                break
                
        body["messages"] = messages
        return body


# Required for OpenWebUI
def filter_function():
    """Factory function for OpenWebUI."""
    return Filter()
