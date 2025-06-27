"""
Simple Working Memory Pipeline for OpenWebUI
===========================================

A minimal memory pipeline that works with the current pipelines server.
This pipeline integrates with our memory API to provide basic memory functionality.
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


class Pipeline:
    """Simple memory pipeline for OpenWebUI integration."""

    class Valves(BaseModel):
        """Pipeline configuration valves."""
        # Backend integration
        memory_api_url: str = "http://memory_api:8000"
        
        # Memory settings
        enable_memory: bool = True
        max_memories: int = 3
        memory_threshold: float = 0.7
        
        # Debug
        debug: bool = True
        
        # Pipeline targets
        pipelines: List[str] = ["*"]

        class Config:
            """Pydantic config for compatibility."""
            # This ensures compatibility with both Pydantic v1 and v2
            pass

    def __init__(self):
        """Initialize the pipeline."""
        self.type = "filter"
        self.name = "Simple Memory Pipeline"
        self.valves = self.Valves()
        self.client = httpx.AsyncClient(timeout=10.0)

    def log(self, message: str):
        """Simple logging function."""
        if self.valves.debug:
            print(f"[MEMORY_PIPELINE] {message}")

    async def on_startup(self):
        """Pipeline startup."""
        self.log("🚀 Simple Memory Pipeline starting...")
        
        # Test memory API connection
        try:
            response = await self.client.get(f"{self.valves.memory_api_url}/health")
            if response.status_code == 200:
                self.log("✅ Memory API connected")
            else:
                self.log(f"⚠️ Memory API health check failed: {response.status_code}")
        except Exception as e:
            self.log(f"❌ Memory API connection failed: {e}")
        
        self.log("🧠 Simple Memory Pipeline ready!")

    async def on_shutdown(self):
        """Pipeline shutdown."""
        self.log("🛑 Simple Memory Pipeline shutting down...")
        await self.client.aclose()

    async def inlet(self, body: dict, user: Optional[dict] = None) -> dict:
        """
        Process incoming messages and inject memory context.
        This is called before the message goes to the LLM.
        """
        try:
            self.log("📥 Processing inlet...")
            
            if not self.valves.enable_memory:
                return body
            
            # Extract user information with multiple fallback methods
            user_id = "default_user"  # Default fallback
            
            if user:
                if user.get("id"):
                    user_id = str(user["id"])
                elif user.get("email"):
                    user_id = user["email"]
                elif user.get("name"):
                    user_id = user["name"]
            
            # Try to extract from body as well
            if user_id == "default_user" and body:
                if body.get("user_id"):
                    user_id = str(body["user_id"])
                elif body.get("user"):
                    if isinstance(body["user"], dict):
                        user_id = str(body["user"].get("id", body["user"].get("email", "default_user")))
                    else:
                        user_id = str(body["user"])
            
            self.log(f"👤 Identified user: {user_id}")
            
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
            
            self.log(f"👤 User: {user_id}, Message: {user_message[:50]}...")
            
            # Retrieve relevant memories
            memories = await self.retrieve_memories(user_id, user_message)
            
            if memories:
                self.log(f"🧠 Found {len(memories)} relevant memories")
                
                # Create memory context
                memory_context = self.format_memory_context(memories)
                
                # Inject memory context into the system message
                self.inject_memory_context(messages, memory_context)
                
                # Update the body with modified messages
                body["messages"] = messages
            else:
                self.log("🔍 No relevant memories found")
            
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
            
            # Extract user information with multiple fallback methods
            user_id = "default_user"  # Default fallback
            
            if user:
                if user.get("id"):
                    user_id = str(user["id"])
                elif user.get("email"):
                    user_id = user["email"]
                elif user.get("name"):
                    user_id = user["name"]
            
            # Try to extract from body as well
            if user_id == "default_user" and body:
                if body.get("user_id"):
                    user_id = str(body["user_id"])
                elif body.get("user"):
                    if isinstance(body["user"], dict):
                        user_id = str(body["user"].get("id", body["user"].get("email", "default_user")))
                    else:
                        user_id = str(body["user"])
            
            self.log(f"👤 Storing for user: {user_id}")
            
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
                # Store the interaction for learning
                await self.store_interaction(user_id, user_message, assistant_response)
            
            return body
            
        except Exception as e:
            self.log(f"❌ Outlet error: {e}")
            return body

    async def retrieve_memories(self, user_id: str, query: str) -> List[Dict[str, Any]]:
        """Retrieve relevant memories for the user query."""
        try:
            response = await self.client.post(
                f"{self.valves.memory_api_url}/api/memory/retrieve",
                json={
                    "user_id": user_id,
                    "query": query,
                    "limit": self.valves.max_memories,
                    "threshold": self.valves.memory_threshold
                },
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("memories", [])
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
                    "context": {"source": "simple_pipeline"},
                    "source": "pipeline"
                },
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                self.log(f"💾 Interaction stored (Total memories: {result.get('memories_count', 0)})")
            else:
                self.log(f"Interaction storage failed: {response.status_code}")
                
        except Exception as e:
            self.log(f"Interaction storage error: {e}")

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
