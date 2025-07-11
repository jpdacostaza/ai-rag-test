"""
title: Enhanced Memory Pipeline
author: open-webui
date: 2025-01-10
version: 1.0.0
license: MIT
description: A pipeline filter that provides memory persistence with proper user identification
requirements: httpx
"""

import json
import httpx
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
import os
import uuid
import time


class Pipeline:
    class Valves(BaseModel):
        pipelines: List[str] = []
        priority: int = 0
        backend_url: str = "http://memory_api:8080"
        memory_threshold: float = 0.05
        max_memories: int = 10
        debug: bool = True

    def __init__(self):
        self.type = "filter"
        self.name = "Enhanced Memory Pipeline"
        
        self.valves = self.Valves(
            **{
                "pipelines": ["*"],  # Apply to all models
                "backend_url": os.getenv("BACKEND_URL", "http://memory_api:8080"),
                "memory_threshold": float(os.getenv("MEMORY_THRESHOLD", "0.05")),
                "max_memories": int(os.getenv("MAX_MEMORIES", "10")),
                "debug": os.getenv("DEBUG_MODE", "true").lower() == "true",
            }
        )

    def log(self, message: str):
        if self.valves.debug:
            print(f"[MEMORY DEBUG] {message}")

    async def on_startup(self):
        self.log(f"Memory pipeline started for {__name__}")

    async def on_shutdown(self):
        self.log(f"Memory pipeline stopped for {__name__}")

    def _get_user_id(self, user: Optional[dict]) -> str:
        """Extract user ID with proper authentication context"""
        if not user:
            self.log("No user object provided")
            return "anonymous"
        
        # Log full user object for debugging
        self.log(f"User object received: {json.dumps(user, indent=2)}")
        
        # Try different user identification strategies
        user_id = None
        
        # Strategy 1: Use email (most specific)
        if "email" in user and user["email"]:
            user_id = user["email"]
            self.log(f"Using email as user_id: {user_id}")
        
        # Strategy 2: Use user ID
        elif "id" in user and user["id"]:
            user_id = user["id"]
            self.log(f"Using id as user_id: {user_id}")
        
        # Strategy 3: Use username
        elif "username" in user and user["username"]:
            user_id = user["username"]
            self.log(f"Using username as user_id: {user_id}")
        
        # Strategy 4: Use name
        elif "name" in user and user["name"]:
            user_id = user["name"]
            self.log(f"Using name as user_id: {user_id}")
        
        # Fallback
        else:
            user_id = "authenticated_user"
            self.log(f"Using fallback user_id: {user_id}")
        
        return user_id

    async def _retrieve_memories(self, user_id: str, conversation_id: str, query: str) -> List[Dict[str, Any]]:
        """Retrieve relevant memories from backend"""
        try:
            url = f"{self.valves.backend_url}/api/memory/retrieve"
            data = {
                "user_id": user_id,
                "query": query,
                "threshold": self.valves.memory_threshold,
                "limit": self.valves.max_memories
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=data, timeout=30.0)
                
            if response.status_code == 200:
                result = response.json()
                memories = result.get("memories", [])
                self.log(f"Retrieved {len(memories)} memories for user {user_id}")
                return memories
            else:
                self.log(f"Memory retrieval failed: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            self.log(f"Error retrieving memories: {str(e)}")
            return []

    async def _store_memory(self, user_id: str, conversation_id: str, user_message: str, assistant_message: str) -> bool:
        """Store learning interaction in backend"""
        try:
            url = f"{self.valves.backend_url}/api/learning/process_interaction"
            data = {
                "user_id": user_id,
                "conversation_id": conversation_id,
                "user_message": user_message,
                "assistant_response": assistant_message,
                "timestamp": str(int(time.time())),
                "source": "pipeline"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=data, timeout=30.0)
                
            if response.status_code == 200:
                self.log(f"Successfully stored interaction for user {user_id}")
                return True
            else:
                self.log(f"Memory storage failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log(f"Error storing memory: {str(e)}")
            return False

    async def inlet(self, body: dict, user: Optional[dict] = None) -> dict:
        """Process incoming requests - inject memories"""
        self.log("=== INLET: Processing incoming request ===")
        
        # Extract user identification
        user_id = self._get_user_id(user)
        
        # Get conversation context
        metadata = body.get("metadata", {})
        conversation_id = metadata.get("chat_id", str(uuid.uuid4()))
        
        # Handle temporary chats
        if conversation_id == "local":
            session_id = metadata.get("session_id")
            conversation_id = f"temporary-session-{session_id}"
        
        self.log(f"Processing for user: {user_id}, conversation: {conversation_id}")
        
        # Get the latest user message for memory retrieval
        messages = body.get("messages", [])
        if messages:
            latest_message = messages[-1]
            if latest_message.get("role") == "user":
                query = latest_message.get("content", "")
                
                # Retrieve relevant memories
                memories = await self._retrieve_memories(user_id, conversation_id, query)
                
                if memories:
                    # Inject memories into the conversation
                    memory_context = "\n".join([
                        f"[Memory {i+1}]: {memory.get('content', '')}"
                        for i, memory in enumerate(memories)
                    ])
                    
                    # Add memory context as a system message
                    memory_message = {
                        "role": "system",
                        "content": f"Previous conversation context and memories:\n{memory_context}\n\nUse this context to provide more personalized and coherent responses."
                    }
                    
                    # Insert memory context before the latest user message
                    messages.insert(-1, memory_message)
                    body["messages"] = messages
                    
                    self.log(f"Injected {len(memories)} memories into conversation")
        
        return body

    async def outlet(self, body: dict, user: Optional[dict] = None) -> dict:
        """Process outgoing responses - store memories"""
        self.log("=== OUTLET: Processing outgoing response ===")
        
        try:
            # Debug: Log the body structure
            self.log(f"Outlet body keys: {list(body.keys()) if body else 'None'}")
            
            # Extract user identification
            user_id = self._get_user_id(user)
            
            # Get conversation context from body metadata or try different approaches
            chat_id = body.get("chat_id")
            if not chat_id:
                metadata = body.get("metadata", {}) if body else {}
                chat_id = metadata.get("chat_id")
            
            # Handle temporary chats
            if chat_id == "local":
                session_id = body.get("session_id") or body.get("metadata", {}).get("session_id")
                chat_id = f"temporary-session-{session_id}"
            
            if not chat_id:
                chat_id = str(uuid.uuid4())
            
            self.log(f"Storing memory for user: {user_id}, conversation: {chat_id}")
            
            # Extract conversation content for storage - try multiple approaches
            messages = body.get("messages", []) if body else []
            self.log(f"Found {len(messages)} messages in outlet")
            
            if len(messages) >= 2:
                # Get the last user message and assistant response
                user_message = None
                assistant_message = None
                
                # Look for the most recent user and assistant messages
                for message in reversed(messages):
                    if message.get("role") == "assistant" and not assistant_message:
                        assistant_message = message.get("content", "")
                    elif message.get("role") == "user" and not user_message:
                        user_message = message.get("content", "")
                    
                    if user_message and assistant_message:
                        break
                
                if user_message and assistant_message:
                    # Store the interaction using the correct method signature
                    success = await self._store_memory(user_id, chat_id, user_message, assistant_message)
                    if success:
                        self.log(f"Successfully stored conversation for user {user_id}")
                    else:
                        self.log(f"Failed to store conversation for user {user_id}")
                else:
                    self.log(f"Missing user_message ({bool(user_message)}) or assistant_message ({bool(assistant_message)})")
            else:
                self.log(f"Insufficient messages for storage: {len(messages)}")
            
            return body
            
        except Exception as e:
            self.log(f"Error in outlet: {str(e)}")
            import traceback
            self.log(f"Traceback: {traceback.format_exc()}")
            return body

    def health(self):
        """Health check endpoint for OpenWebUI pipeline monitoring"""
        return {"status": "healthy", "type": "filter", "memory_enabled": True}
