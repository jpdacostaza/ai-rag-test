"""
OpenWebUI Memory Function
========================

A memory function for OpenWebUI that stores and retrieves conversation context.
This function integrates with our memory API to provide persistent memory across conversations.
"""

import json
import time
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
    """Function configuration valves."""
    # Backend integration
    memory_api_url: str = "http://memory_api:8000"
    
    # Memory settings
    enable_memory: bool = True
    max_memories: int = 3
    memory_threshold: float = 0.7
    
    # Debug
    debug: bool = True


class Tools:
    def __init__(self):
        self.valves = Valves()
        self.client = httpx.Client(timeout=30.0)
    
    def log(self, message: str, level: str = "INFO"):
        """Enhanced logging with structured output."""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] [Memory Function] {message}")
    
    async def store_memory(self, user_id: str, content: str, metadata: Optional[Dict] = None) -> bool:
        """Store memory via the memory API."""
        try:
            payload = {
                "content": content,
                "metadata": metadata or {}
            }
            
            response = self.client.post(
                f"{self.valves.memory_api_url}/api/memory/{user_id}",
                json=payload
            )
            
            if response.status_code == 200:
                self.log(f"Memory stored successfully for user {user_id}")
                return True
            else:
                self.log(f"Failed to store memory: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"Error storing memory: {str(e)}", "ERROR")
            return False
    
    async def retrieve_memories(self, user_id: str, query: str, limit: int = 3) -> List[Dict]:
        """Retrieve relevant memories via the memory API."""
        try:
            response = self.client.get(
                f"{self.valves.memory_api_url}/api/memory/{user_id}",
                params={"query": query, "limit": limit}
            )
            
            if response.status_code == 200:
                memories = response.json()
                self.log(f"Retrieved {len(memories)} memories for user {user_id}")
                return memories
            else:
                self.log(f"Failed to retrieve memories: {response.status_code} - {response.text}", "ERROR")
                return []
                
        except Exception as e:
            self.log(f"Error retrieving memories: {str(e)}", "ERROR")
            return []


def inlet(body: dict, user: Optional[dict] = None) -> dict:
    """
    Process incoming messages and inject memory context.
    This function is called before the message is sent to the LLM.
    """
    tools = Tools()
    
    if not tools.valves.enable_memory:
        return body
    
    try:
        user_id = user.get("id", "anonymous") if user else "anonymous"
        
        # Get the current message
        messages = body.get("messages", [])
        if not messages:
            return body
        
        current_message = messages[-1].get("content", "")
        
        # Retrieve relevant memories
        memories = tools.retrieve_memories(user_id, current_message, tools.valves.max_memories)
        
        if memories:
            # Format memory context
            memory_context = "Previous conversation context:\n"
            for i, memory in enumerate(memories, 1):
                memory_context += f"{i}. {memory.get('content', '')}\n"
            
            # Inject memory into the system message or create one
            system_message = None
            for msg in messages:
                if msg.get("role") == "system":
                    system_message = msg
                    break
            
            if system_message:
                # Append to existing system message
                system_message["content"] = f"{system_message['content']}\n\n{memory_context}"
            else:
                # Create new system message
                system_message = {
                    "role": "system",
                    "content": memory_context
                }
                messages.insert(0, system_message)
            
            tools.log(f"Injected {len(memories)} memories into conversation for user {user_id}")
        
        return body
        
    except Exception as e:
        tools.log(f"Error in inlet: {str(e)}", "ERROR")
        return body


def outlet(body: dict, user: Optional[dict] = None) -> dict:
    """
    Process outgoing responses and store them as memories.
    This function is called after the LLM generates a response.
    """
    tools = Tools()
    
    if not tools.valves.enable_memory:
        return body
    
    try:
        user_id = user.get("id", "anonymous") if user else "anonymous"
        
        # Get the generated response
        messages = body.get("messages", [])
        if not messages:
            return body
        
        # Find the assistant's response
        assistant_message = None
        for msg in reversed(messages):
            if msg.get("role") == "assistant":
                assistant_message = msg
                break
        
        if assistant_message:
            content = assistant_message.get("content", "")
            if content:
                # Store the conversation exchange
                metadata = {
                    "timestamp": time.time(),
                    "conversation_id": body.get("chat_id", "unknown"),
                    "model": body.get("model", "unknown")
                }
                
                # Store both user input and assistant response
                if len(messages) >= 2:
                    user_message = messages[-2].get("content", "") if messages[-2].get("role") == "user" else ""
                    if user_message:
                        exchange_content = f"User: {user_message}\nAssistant: {content}"
                        tools.store_memory(user_id, exchange_content, metadata)
                        tools.log(f"Stored conversation exchange for user {user_id}")
        
        return body
        
    except Exception as e:
        tools.log(f"Error in outlet: {str(e)}", "ERROR")
        return body


# OpenWebUI Function Metadata
metadata = {
    "name": "Memory Function",
    "description": "Provides persistent memory functionality for conversations",
    "author": "OpenWebUI Memory System",
    "version": "1.0.0",
    "required": False
}
