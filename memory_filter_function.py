"""
OpenWebUI Memory Filter Function
================================

A memory filter function that adds context from previous conversations.
This should be imported as a Function in OpenWebUI, then applied as a Filter to models.

Instructions:
1. Copy this entire code
2. In OpenWebUI: Admin → Functions → Import Function
3. Paste this code
4. Set ID: "memory_filter"
5. Set Name: "Memory Filter"
6. Set Type: "filter" 
7. Enable the function
8. Go to Models → llama3.2:3b → Filters → Add this filter
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


class Filter:
    """Memory filter for OpenWebUI - adds context from previous conversations."""

    class Valves(BaseModel):
        """Filter configuration valves."""
        # Backend integration
        memory_api_url: str = "http://memory_api:8000"
        
        # Memory settings
        enable_memory: bool = True
        max_memories: int = 3
        memory_threshold: float = 0.3
        
        # Debug
        debug: bool = True

    def __init__(self):
        """Initialize the filter."""
        self.valves = self.Valves()
        self.client = httpx.AsyncClient(timeout=10.0)

    def log(self, message: str):
        """Simple logging function."""
        if self.valves.debug:
            print(f"[MEMORY_FILTER] {message}")

    async def inlet(self, body: dict, user: Optional[dict] = None) -> dict:
        """
        Process incoming messages and inject memory context.
        This is called before the message goes to the LLM.
        """
        try:
            self.log("📥 Processing inlet...")
            
            if not self.valves.enable_memory:
                return body
            
            # Extract user information
            user_id = "default_user"
            if user and user.get("id"):
                user_id = str(user["id"])
            elif user and user.get("email"):
                user_id = user["email"]
            
            self.log(f"👤 User: {user_id}")
            
            # Get the user's message
            messages = body.get("messages", [])
            if not messages:
                return body
            
            user_message = ""
            for msg in reversed(messages):
                if msg.get("role") == "user":
                    user_message = msg.get("content", "")
                    break
            
            if not user_message.strip():
                return body
            
            self.log(f"💬 Message: {user_message[:50]}...")
            
            # Retrieve relevant memories
            memories = await self.retrieve_memories(user_id, user_message)
            
            if memories:
                self.log(f"🧠 Found {len(memories)} memories")
                
                # Create memory context
                memory_context = self.format_memory_context(memories)
                
                # Inject memory context into the system message
                self.inject_memory_context(messages, memory_context)
                body["messages"] = messages
            else:
                self.log("🔍 No memories found")
            
            return body
            
        except Exception as e:
            self.log(f"❌ Inlet error: {e}")
            return body

    async def outlet(self, body: dict, user: Optional[dict] = None) -> dict:
        """
        Process outgoing responses and store interactions for learning.
        This is called after the LLM generates a response.
        """
        try:
            self.log("📤 Processing outlet...")
            
            if not self.valves.enable_memory:
                return body
            
            # Extract user information
            user_id = "default_user"
            if user and user.get("id"):
                user_id = str(user["id"])
            elif user and user.get("email"):
                user_id = user["email"]
            
            # Extract messages
            messages = body.get("messages", [])
            if len(messages) < 2:
                return body
            
            # Get the user's message and assistant's response
            user_message = ""
            assistant_response = ""
            
            for msg in reversed(messages):
                if msg.get("role") == "assistant" and not assistant_response:
                    assistant_response = msg.get("content", "")
                elif msg.get("role") == "user" and not user_message:
                    user_message = msg.get("content", "")
                
                if user_message and assistant_response:
                    break
            
            if user_message and assistant_response:
                await self.store_interaction(user_id, user_message, assistant_response)
            
            return body
            
        except Exception as e:
            self.log(f"❌ Outlet error: {e}")
            return body

    async def retrieve_memories(self, user_id: str, query: str) -> List[Dict[str, Any]]:
        """Retrieve relevant memories for the user query."""
        try:
            request_data = {
                "user_id": user_id,
                "query": query,
                "limit": self.valves.max_memories,
                "threshold": self.valves.memory_threshold
            }
            
            self.log(f"🔍 Retrieving memories with: {request_data}")
            
            response = await self.client.post(
                f"{self.valves.memory_api_url}/api/memory/retrieve",
                json=request_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                memories = result.get("memories", [])
                self.log(f"📊 API returned {len(memories)} memories")
                
                # If no memories found with the specific query, try a fallback approach
                if not memories and result.get("sources", {}).get("long_term", 0) > 0:
                    self.log("🔄 No memories found with query, trying fallback with empty query")
                    
                    # Try with empty query and lower threshold
                    fallback_request = {
                        "user_id": user_id,
                        "query": "",
                        "limit": self.valves.max_memories,
                        "threshold": 0.0  # Get any memories
                    }
                    
                    fallback_response = await self.client.post(
                        f"{self.valves.memory_api_url}/api/memory/retrieve",
                        json=fallback_request,
                        headers={"Content-Type": "application/json"}
                    )
                    
                    if fallback_response.status_code == 200:
                        fallback_result = fallback_response.json()
                        memories = fallback_result.get("memories", [])
                        self.log(f"🔄 Fallback returned {len(memories)} memories")
                
                return memories
            else:
                self.log(f"Memory retrieval failed: {response.status_code}")
                return []
                
        except Exception as e:
            self.log(f"Memory retrieval error: {e}")
            return []

    async def store_interaction(self, user_id: str, user_message: str, assistant_response: str):
        """Store user interaction for learning."""
        try:
            conversation_id = f"chat_{user_id}_{int(time.time())}"
            
            response = await self.client.post(
                f"{self.valves.memory_api_url}/api/learning/process_interaction",
                json={
                    "user_id": user_id,
                    "conversation_id": conversation_id,
                    "user_message": user_message,
                    "assistant_response": assistant_response,
                    "response_time": 1.0,
                    "context": {"source": "memory_filter"},
                    "source": "filter"
                },
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                total_memories = result.get('total_memories', {}).get('total', 0) or result.get('memories_count', 0)
                self.log(f"💾 Stored interaction (Total: {total_memories})")
            else:
                self.log(f"Storage failed: {response.status_code}")
                
        except Exception as e:
            self.log(f"Storage error: {e}")

    def format_memory_context(self, memories: List[Dict[str, Any]]) -> str:
        """Format memories into context string."""
        if not memories:
            return ""
        
        context_parts = ["[MEMORY CONTEXT - Previous conversation context:]"]
        
        for i, memory in enumerate(memories, 1):
            content = memory.get("content", "")
            score = memory.get("relevance_score", 0)
            context_parts.append(f"{i}. {content} (relevance: {score:.2f})")
        
        context_parts.append("[END MEMORY CONTEXT]")
        return "\n".join(context_parts)

    def inject_memory_context(self, messages: List[Dict[str, Any]], memory_context: str):
        """Inject memory context into the messages."""
        if not memory_context:
            return
        
        # Find or create system message
        system_message = None
        for msg in messages:
            if msg.get("role") == "system":
                system_message = msg
                break
        
        if system_message:
            # Append to existing system message
            original_content = system_message.get("content", "")
            system_message["content"] = f"{original_content}\n\n{memory_context}"
        else:
            # Create new system message at the beginning
            system_message = {
                "role": "system",
                "content": f"You are a helpful AI assistant.\n\n{memory_context}"
            }
            messages.insert(0, system_message)
