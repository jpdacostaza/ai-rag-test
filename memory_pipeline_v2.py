"""
title: Memory Pipeline
author: Backend Team  
description: Advanced memory and learning pipeline for OpenWebUI
requirements: httpx
version: 1.0.0
"""

import asyncio
import json
import time
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel

try:
    import httpx
except ImportError:
    import subprocess
    import sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "httpx"])
    import httpx


class Pipeline:
    class Valves(BaseModel):
        backend_url: str = "http://host.docker.internal:8001"
        api_key: str = "f2b985dd-219f-45b1-a90e-170962cc7082"
        memory_limit: int = 3
        memory_threshold: float = 0.7
        enable_learning: bool = True
        enable_memory_injection: bool = True
        max_memory_length: int = 500

    def __init__(self):
        self.name = "Memory Pipeline"
        self.valves = self.Valves()
        self.client = None
        
    async def on_startup(self):
        """Called when the pipeline starts"""
        print(f"🚀 {self.name} started successfully!")
        
    async def on_shutdown(self):
        """Called when the pipeline shuts down"""
        if self.client:
            await self.client.aclose()
        print(f"🛑 {self.name} shut down")
        
    async def _get_client(self):
        """Get or create HTTP client"""
        if not self.client:
            self.client = httpx.AsyncClient(timeout=30.0)
        return self.client
    
    async def _call_backend(self, endpoint: str, data: dict) -> Optional[dict]:
        """Make async HTTP call to backend"""
        try:
            client = await self._get_client()
            url = f"{self.valves.backend_url}/{endpoint.lstrip('/')}"
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.valves.api_key}"
            }
            
            print(f"🔗 Memory Pipeline: Calling {url}")
            
            response = await client.post(url, json=data, headers=headers)
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"⚠️ Backend call failed: HTTP {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Backend call error: {e}")
            return None
    
    async def _retrieve_user_memory(self, user_id: str, query: str) -> List[dict]:
        """Retrieve user memory from backend"""
        if not self.valves.enable_memory_injection:
            return []
            
        try:
            data = {
                "user_id": user_id,
                "query": query,
                "limit": self.valves.memory_limit,
                "threshold": self.valves.memory_threshold
            }
            
            result = await self._call_backend("api/memory/retrieve", data)
            if result and "memories" in result:
                print(f"💭 Retrieved {len(result['memories'])} memories for user {user_id}")
                return result["memories"]
                
        except Exception as e:
            print(f"⚠️ Memory retrieval failed: {e}")
            
        return []
    
    def _format_memory_context(self, memories: List[dict]) -> str:
        """Format memories into context string"""
        if not memories:
            return ""
        
        context_parts = ["[MEMORY CONTEXT] Based on our previous conversations:"]
        
        for i, memory in enumerate(memories, 1):
            content = memory.get("content", memory.get("text", ""))
            if len(content) > self.valves.max_memory_length:
                content = content[:self.valves.max_memory_length] + "..."
            
            context_parts.append(f"{i}. {content}")
        
        context_parts.append("[END MEMORY CONTEXT]")
        return "\n".join(context_parts)
    
    async def _get_user_id(self, body: dict, user: Optional[dict] = None) -> str:
        """Extract user ID from request"""
        if user and "id" in user:
            return str(user["id"])
        return body.get("user_id", body.get("user", "default_user"))
    
    async def _store_interaction(self, user_id: str, user_message: str, assistant_response: str) -> bool:
        """Store interaction for learning"""
        if not self.valves.enable_learning:
            return False
            
        try:
            data = {
                "user_id": user_id,
                "conversation_id": f"conv_{int(time.time())}",
                "user_message": user_message,
                "assistant_response": assistant_response,
                "source": "openwebui_pipeline"
            }
            
            result = await self._call_backend("api/learning/process_interaction", data)
            if result and result.get("status") == "success":
                print(f"📚 Stored learning interaction for user {user_id}")
                return True
                
        except Exception as e:
            print(f"⚠️ Learning storage failed: {e}")
            
        return False

    async def inlet(self, body: dict, user: Optional[dict] = None) -> dict:
        """Process incoming messages and inject memory context"""
        try:
            print(f"🔄 Memory Pipeline: Processing inlet request")
            
            # Extract user information
            user_id = await self._get_user_id(body, user)
            messages = body.get("messages", [])
            
            if not messages:
                return body
                
            # Get the latest user message
            latest_message = None
            for msg in reversed(messages):
                if msg.get("role") == "user":
                    latest_message = msg
                    break
            
            if not latest_message or not latest_message.get("content"):
                return body
            
            user_query = latest_message["content"]
            print(f"👤 User ({user_id}): {user_query[:100]}...")
            
            # Retrieve relevant memories
            memories = await self._retrieve_user_memory(user_id, user_query)
            
            if memories:
                # Format memory context
                memory_context = self._format_memory_context(memories)
                
                # Inject memory into the user's message
                enhanced_content = f"{memory_context}\n\n{user_query}"
                latest_message["content"] = enhanced_content
                
                print(f"💡 Enhanced message with {len(memories)} memories")
            
            return body
            
        except Exception as e:
            print(f"❌ Inlet processing error: {e}")
            return body

    async def outlet(self, body: dict, user: Optional[dict] = None) -> dict:
        """Process outgoing responses for learning"""
        try:
            print(f"📤 Memory Pipeline: Processing outlet response")
            
            # Extract information
            user_id = await self._get_user_id(body, user)
            messages = body.get("messages", [])
            
            if len(messages) < 2:
                return body
            
            # Find the latest user and assistant messages
            user_message = ""
            assistant_message = ""
            
            for msg in reversed(messages):
                if msg.get("role") == "assistant" and not assistant_message:
                    assistant_message = msg.get("content", "")
                elif msg.get("role") == "user" and not user_message:
                    user_message = msg.get("content", "")
                    
                if user_message and assistant_message:
                    break
            
            if user_message and assistant_message:
                # Store the interaction for learning
                await self._store_interaction(user_id, user_message, assistant_message)
            
            return body
            
        except Exception as e:
            print(f"❌ Outlet processing error: {e}")
            return body
