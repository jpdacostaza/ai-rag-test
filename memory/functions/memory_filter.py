"""
OpenWebUI Memory Filter
======================

A memory filter for OpenWebUI that stores and retrieves conversation context.
This filter integrates with our memory API to provide persistent memory across conversations.
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
    """Filter configuration valves."""
    # Backend integration
    memory_api_url: str = "http://memory_api:8000"
    
    # Memory settings
    enable_memory: bool = True
    max_memories: int = 3
    memory_threshold: float = 0.7
    
    # Debug
    debug: bool = True


class Filter:
    def __init__(self):
        self.valves = Valves()
        self.client = httpx.Client(timeout=30.0)
    
    def log(self, message: str, level: str = "INFO"):
        """Enhanced logging with structured output."""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] [Memory Filter] {message}")
    
    async def store_memory(self, user_id: str, content: str, metadata: Optional[Dict] = None) -> bool:
        """Store memory via the memory API."""
        try:
            payload = {
                "user_id": user_id,
                "content": content,
                "metadata": metadata or {}
            }
            
            response = self.client.post(
                f"{self.valves.memory_api_url}/api/memory/store",
                json=payload
            )
            
            if response.status_code == 200:
                if self.valves.debug:
                    self.log(f"✅ Memory stored for user {user_id}")
                return True
            else:
                self.log(f"⚠️ Failed to store memory: {response.status_code} - {response.text}", "WARNING")
                return False
                
        except Exception as e:
            self.log(f"❌ Error storing memory: {e}", "ERROR")
            return False
    
    async def retrieve_memories(self, user_id: str, query: str) -> List[Dict]:
        """Retrieve relevant memories via the memory API."""
        try:
            payload = {
                "user_id": user_id,
                "query": query,
                "limit": self.valves.max_memories,
                "threshold": self.valves.memory_threshold
            }
            
            response = self.client.post(
                f"{self.valves.memory_api_url}/api/memory/search",
                json=payload
            )
            
            if response.status_code == 200:
                memories = response.json().get("memories", [])
                if self.valves.debug and memories:
                    self.log(f"📚 Retrieved {len(memories)} memories for user {user_id}")
                return memories
            else:
                self.log(f"⚠️ Failed to retrieve memories: {response.status_code} - {response.text}", "WARNING")
                return []
                
        except Exception as e:
            self.log(f"❌ Error retrieving memories: {e}", "ERROR")
            return []
    
    def inlet(self, body: dict, user: Optional[Dict] = None) -> dict:
        """
        Filter function called before sending messages to the model.
        This is where we inject relevant memories into the conversation.
        """
        if not self.valves.enable_memory:
            return body
        
        try:
            # Extract user information
            user_id = user.get("id") if user else "anonymous"
            
            # Get the current message
            messages = body.get("messages", [])
            if not messages:
                return body
            
            # Get the latest user message
            latest_message = messages[-1]
            if latest_message.get("role") != "user":
                return body
            
            user_content = latest_message.get("content", "")
            if not user_content:
                return body
            
            # Store the current message as a memory
            import asyncio
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            # Store memory asynchronously
            loop.run_until_complete(self.store_memory(
                user_id=user_id,
                content=user_content,
                metadata={
                    "timestamp": time.time(),
                    "role": "user",
                    "chat_id": body.get("chat_id")
                }
            ))
            
            # Retrieve relevant memories
            memories = loop.run_until_complete(self.retrieve_memories(user_id, user_content))
            
            # If we have relevant memories, inject them into the conversation
            if memories:
                memory_context = "Previous conversation context:\n"
                for memory in memories:
                    content = memory.get("content", "")
                    timestamp = memory.get("metadata", {}).get("timestamp")
                    if timestamp:
                        time_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp))
                        memory_context += f"[{time_str}] {content}\n"
                    else:
                        memory_context += f"- {content}\n"
                
                memory_context += "\nCurrent conversation:\n"
                
                # Find the system message or create one
                system_message_index = -1
                for i, msg in enumerate(messages):
                    if msg.get("role") == "system":
                        system_message_index = i
                        break
                
                if system_message_index >= 0:
                    # Update existing system message
                    current_system = messages[system_message_index].get("content", "")
                    messages[system_message_index]["content"] = f"{current_system}\n\n{memory_context}"
                else:
                    # Add new system message at the beginning
                    system_message = {
                        "role": "system",
                        "content": f"You are a helpful assistant with access to previous conversation context.\n\n{memory_context}"
                    }
                    messages.insert(0, system_message)
                
                if self.valves.debug:
                    self.log(f"💡 Injected {len(memories)} memories into conversation for user {user_id}")
            
            return body
            
        except Exception as e:
            self.log(f"❌ Error in inlet: {e}", "ERROR")
            return body
    
    def outlet(self, body: dict, user: Optional[Dict] = None) -> dict:
        """
        Filter function called after receiving the model's response.
        This is where we can store the assistant's response as memory.
        """
        if not self.valves.enable_memory:
            return body
        
        try:
            # Extract user information
            user_id = user.get("id") if user else "anonymous"
            
            # Get the assistant's response
            messages = body.get("messages", [])
            if not messages:
                return body
            
            # Find the latest assistant message
            latest_assistant_message = None
            for message in reversed(messages):
                if message.get("role") == "assistant":
                    latest_assistant_message = message
                    break
            
            if not latest_assistant_message:
                return body
            
            assistant_content = latest_assistant_message.get("content", "")
            if not assistant_content:
                return body
            
            # Store the assistant's response as memory
            import asyncio
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            loop.run_until_complete(self.store_memory(
                user_id=user_id,
                content=assistant_content,
                metadata={
                    "timestamp": time.time(),
                    "role": "assistant",
                    "chat_id": body.get("chat_id")
                }
            ))
            
            if self.valves.debug:
                self.log(f"📝 Stored assistant response as memory for user {user_id}")
            
            return body
            
        except Exception as e:
            self.log(f"❌ Error in outlet: {e}", "ERROR")
            return body
