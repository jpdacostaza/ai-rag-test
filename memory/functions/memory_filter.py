"""
OpenWebUI Memory Filter
======================

A memory filter for OpenWebUI that stores and retrieves conversation context.
This filter integrates with our memory API to provide persistent memory across conversations.

NOTE: This file serves as a fallback implementation that is only used if the primary
memory_function.py file in the root directory is not available. In most cases, the 
system will use the memory_function.py implementation instead.
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
    # Backend integration - use correct internal port for memory API  
    memory_api_url: str = "http://memory_api:8080"
    
    # Memory settings
    enable_memory: bool = True
    max_memories: int = 3
    memory_threshold: float = 0.01  # Lowered further to 0.01 for better recall
    
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
    
    def store_memory(self, user_id: str, content: str, metadata: Optional[Dict] = None) -> bool:
        """Store memory via the memory API using learning endpoint."""
        try:
            # Get conversation_id from metadata if available, or generate one
            conversation_id = metadata.get("chat_id") if metadata else None
            if not conversation_id:
                conversation_id = f"conv_{int(time.time())}"
            
            payload = {
                "user_id": user_id,
                "conversation_id": conversation_id,
                "user_message": content,
                "assistant_response": "",  # Will be filled in outlet
                "context": metadata or {}
            }
            
            response = self.client.post(
                f"{self.valves.memory_api_url}/api/learning/process_interaction",
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
    
    def retrieve_memories(self, user_id: str, query: str) -> List[Dict]:
        """Retrieve relevant memories via the memory API."""
        try:
            payload = {
                "user_id": user_id,
                "query": query,
                "limit": self.valves.max_memories,
                "threshold": self.valves.memory_threshold
            }
            
            response = self.client.post(
                f"{self.valves.memory_api_url}/api/memory/retrieve",
                json=payload
            )
            
            if response.status_code == 200:
                data = response.json()
                memories = data.get("memories", []) if isinstance(data, dict) else []
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
            # Extract user ID using comprehensive method
            user_id = self.extract_user_id(body, user)
            
            # Log for debugging
            if self.valves.debug:
                self.log(f"🔍 Processing inlet for user: {user_id}")
            
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
            self.store_memory(
                user_id=user_id,
                content=user_content,
                metadata={
                    "timestamp": time.time(),
                    "role": "user",
                    "chat_id": body.get("chat_id")
                }
            )
            
            # Retrieve relevant memories
            memories = self.retrieve_memories(user_id, user_content)
            
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
        
        IMPORTANT: We should NOT store assistant responses as user memories!
        This was causing AI responses to be extracted as "user facts".
        The inlet handles user message processing, outlet should be minimal.
        """
        if not self.valves.enable_memory:
            return body
        
        try:
            if self.valves.debug:
                user_id = self.extract_user_id(body, user)
                self.log(f"🔍 Outlet called for user: {user_id} (not processing - AI responses should not become memories)")
            
            # Just return the body without processing AI responses as memories
            return body
            
        except Exception as e:
            self.log(f"❌ Error in outlet: {e}", "ERROR")
            return body
    
    def extract_user_id(self, body: dict, user: Optional[Dict] = None) -> str:
        """Extract user ID using multiple fallback methods."""
        
        user_id = "anonymous"
        
        # Method 1: From user parameter (most reliable)
        if user and isinstance(user, dict):
            user_id = (user.get("id") or 
                      user.get("user_id") or 
                      user.get("email") or 
                      user.get("name"))
            if user_id and user_id != "anonymous":
                if self.valves.debug:
                    self.log(f"✅ User ID from user param: {user_id}")
                return str(user_id)
        
        # Method 2: From body
        if isinstance(body, dict):
            # Try various body fields
            user_candidates = [
                body.get("user"),
                body.get("user_id"), 
                body.get("userId"),
                body.get("user_email"),
                body.get("userEmail")
            ]
            
            for candidate in user_candidates:
                if candidate:
                    if isinstance(candidate, dict):
                        extracted = (candidate.get("id") or 
                                   candidate.get("email") or 
                                   candidate.get("name"))
                        if extracted:
                            if self.valves.debug:
                                self.log(f"✅ User ID from body: {extracted}")
                            return str(extracted)
                    else:
                        if self.valves.debug:
                            self.log(f"✅ User ID from body field: {candidate}")
                        return str(candidate)
            
            # Method 3: Try to extract from chat metadata
            chat_id = body.get("chat_id") or body.get("chatId")
            if chat_id:
                # Use chat_id as a user identifier (not ideal but better than anonymous)
                user_id = f"chat_{chat_id}"
                if self.valves.debug:
                    self.log(f"🔄 Using chat ID as user ID: {user_id}")
                return user_id
            
            # Method 4: Generate a session-based ID from messages if available
            messages = body.get("messages", [])
            if messages:
                # Create a pseudo-user ID based on the first message timestamp and content
                first_msg = messages[0]
                content_hash = str(hash(str(first_msg.get("content", ""))[:50]))[-8:]
                user_id = f"session_{content_hash}"
                if self.valves.debug:
                    self.log(f"🔄 Generated session user ID: {user_id}")
                return user_id
        
        if self.valves.debug:
            self.log(f"⚠️ Falling back to anonymous user")
        return "anonymous"
