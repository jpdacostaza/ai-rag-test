"""
Advanced Memory Pipeline for OpenWebUI
=====================================

This pipeline integrates with the backend's adaptive learning and ChromaDB memory systems
to provide contextual memory injection and learning capabilities.

Installation:
1. Place this file in your OpenWebUI pipelines directory
2. Configure the backend API URL and key
3. Restart OpenWebUI

Features:
- Retrieves relevant user memories before processing prompts
- Injects contextual memory into user prompts
- Stores user/assistant interactions for adaptive learning
- Supports both filter and pipe modes
- Async HTTP communication with backend
"""

import asyncio
import json
import time
from typing import Dict, List, Optional, Any
from pydantic import BaseModel
from datetime import datetime

try:
    import httpx
except ImportError:
    import subprocess
    import sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "httpx"])
    import httpx

class AdvancedMemoryPipeline:
    """
    Advanced Memory Pipeline for OpenWebUI
    
    This pipeline connects to your backend's memory and adaptive learning systems
    to provide intelligent memory injection and learning capabilities.
    """
    
    class Valves(BaseModel):
        # Configuration values that can be set in the OpenWebUI admin panel
        backend_url: str = "http://localhost:8080"
        api_key: str = "your-api-key-here"
        memory_limit: int = 3
        memory_threshold: float = 0.7
        enable_learning: bool = True
        enable_memory_injection: bool = True
        max_memory_length: int = 500
        pipeline_mode: str = "filter"  # "filter" or "pipe"

    def __init__(self):
        self.valves = self.Valves()
        self.client = None
        self.pipeline_mode = "filter"  # Can be "filter" or "pipe"
        
    async def _get_client(self):
        """Get or create HTTP client"""
        if not self.client:
            self.client = httpx.AsyncClient(timeout=30.0)
        return self.client
    
    async def _call_backend(self, endpoint: str, data: dict) -> Optional[dict]:
        """Make async HTTP call to backend"""
        try:
            client = await self._get_client()
            headers = {"Content-Type": "application/json"}
            
            if self.valves.api_key and self.valves.api_key != "your-api-key-here":
                headers["Authorization"] = f"Bearer {self.valves.api_key}"
            
            url = f"{self.valves.backend_url.rstrip('/')}/{endpoint.lstrip('/')}"
            
            response = await client.post(url, json=data, headers=headers)
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            print(f"⚠️ Pipeline backend call failed: {e}")
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
            
        return []    async def _store_interaction(self, user_id: str, conversation_id: str, 
                               user_message: str, assistant_response: str, 
                               response_time: float = 1.0, tools_used: Optional[List[str]] = None) -> bool:
        """Store interaction for adaptive learning"""
        if not self.valves.enable_learning:
            return False
            
        try:
            data = {
                "user_id": user_id,
                "conversation_id": conversation_id,
                "user_message": user_message,
                "assistant_response": assistant_response,
                "response_time": response_time,
                "tools_used": tools_used or [],
                "source": "openwebui_pipeline"
            }
            
            result = await self._call_backend("api/learning/process_interaction", data)
            if result and result.get("status") == "success":
                print(f"📚 Stored learning interaction for user {user_id}")
                return True
                
        except Exception as e:
            print(f"⚠️ Learning storage failed: {e}")
            
        return False
    
    def _format_memory_context(self, memories: List[dict]) -> str:
        """Format memories into context string"""
        if not memories:
            return ""
            
        context_parts = ["[RELEVANT CONTEXT FROM PREVIOUS CONVERSATIONS]"]
        
        for i, memory in enumerate(memories[:self.valves.memory_limit]):
            # Handle different memory formats
            if isinstance(memory, dict):
                # Extract content based on available fields
                content = ""
                if "content" in memory:
                    content = memory["content"]
                elif "text" in memory:
                    content = memory["text"]
                elif "message" in memory:
                    content = memory["message"]
                else:
                    content = str(memory)
                
                # Truncate if too long
                if len(content) > self.valves.max_memory_length:
                    content = content[:self.valves.max_memory_length] + "..."
                    
                context_parts.append(f"{i+1}. {content}")
            else:
                # Handle string memories
                content = str(memory)
                if len(content) > self.valves.max_memory_length:
                    content = content[:self.valves.max_memory_length] + "..."
                context_parts.append(f"{i+1}. {content}")
        
        context_parts.append("[END CONTEXT]")
        return "\n".join(context_parts)
    
    async def _get_user_id(self, body: dict) -> str:
        """Extract user ID from request body"""
        # Try different possible user ID fields
        user_id = body.get("user", {}).get("id")
        if not user_id:
            user_id = body.get("user_id")
        if not user_id:
            user_id = body.get("userId")
        if not user_id:
            user_id = "default"
        return str(user_id)
    
    async def _get_conversation_id(self, body: dict) -> str:
        """Extract conversation ID from request body"""
        conv_id = body.get("chat_id")
        if not conv_id:
            conv_id = body.get("conversation_id")
        if not conv_id:
            conv_id = body.get("conversationId")
        if not conv_id:
            conv_id = f"pipeline_{int(time.time())}"
        return str(conv_id)

    # FILTER MODE - Modifies messages before they go to the model
    async def inlet(self, body: dict, user: Optional[dict] = None) -> dict:
        """
        Filter mode: Process incoming messages and inject memory context
        This runs before the message goes to the LLM
        """
        try:
            print(f"🔄 Advanced Memory Pipeline (Filter Mode) - Processing request")
            
            # Extract user information
            user_id = await self._get_user_id(body)
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
            print(f"👤 User query: {user_query[:100]}...")
            
            # Retrieve relevant memories
            memories = await self._retrieve_user_memory(user_id, user_query)
            
            if memories:
                # Format memory context
                memory_context = self._format_memory_context(memories)
                
                # Inject memory into the user's message
                enhanced_content = f"{memory_context}\n\n{user_query}"
                latest_message["content"] = enhanced_content
                
                print(f"💡 Enhanced message with {len(memories)} memories")
                
                # Update the message in the body
                for i, msg in enumerate(body["messages"]):
                    if msg.get("role") == "user" and msg == latest_message:
                        body["messages"][i] = latest_message
                        break
            
            return body
            
        except Exception as e:
            print(f"❌ Filter processing error: {e}")
            return body

    # PIPE MODE - Processes the complete conversation
    async def pipe(self, body: dict, user: Optional[dict] = None) -> dict:
        """
        Pipe mode: Process the complete conversation with memory and learning
        This completely handles the conversation flow
        """
        try:
            print(f"🔄 Advanced Memory Pipeline (Pipe Mode) - Processing conversation")
            
            # Extract information
            user_id = await self._get_user_id(body)
            conversation_id = await self._get_conversation_id(body)
            messages = body.get("messages", [])
            
            if not messages:
                return {"error": "No messages provided"}
            
            # Find user and assistant messages
            user_message = ""
            assistant_message = ""
            
            for msg in reversed(messages):
                if msg.get("role") == "user" and not user_message:
                    user_message = msg.get("content", "")
                elif msg.get("role") == "assistant" and not assistant_message:
                    assistant_message = msg.get("content", "")
                    
                if user_message and assistant_message:
                    break
            
            if not user_message:
                return {"error": "No user message found"}
            
            print(f"👤 User: {user_message[:100]}...")
            
            # If we have both user and assistant messages, store for learning
            if assistant_message:
                print(f"🤖 Assistant: {assistant_message[:100]}...")
                
                # Store interaction for learning
                await self._store_interaction(
                    user_id=user_id,
                    conversation_id=conversation_id,
                    user_message=user_message,
                    assistant_response=assistant_message,
                    response_time=1.0,
                    tools_used=[]
                )
            
            # Retrieve memories for current query
            memories = await self._retrieve_user_memory(user_id, user_message)
            
            # Prepare response with memory context
            response = {
                "user_id": user_id,
                "conversation_id": conversation_id,
                "memories_retrieved": len(memories),
                "message": user_message
            }
            
            if memories:
                response["memory_context"] = self._format_memory_context(memories)
                print(f"💡 Provided {len(memories)} memories as context")
            
            return response
            
        except Exception as e:
            print(f"❌ Pipe processing error: {e}")
            return {"error": str(e)}

    # OUTLET - Processes responses after the model
    async def outlet(self, body: dict, user: Optional[dict] = None) -> dict:
        """
        Process outgoing responses - store interactions for learning
        This runs after the LLM generates a response
        """
        try:
            print(f"📤 Advanced Memory Pipeline - Processing response for learning")
            
            # Extract information
            user_id = await self._get_user_id(body)
            conversation_id = await self._get_conversation_id(body)
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
                await self._store_interaction(
                    user_id=user_id,
                    conversation_id=conversation_id,
                    user_message=user_message,
                    assistant_response=assistant_message,
                    response_time=1.0,
                    tools_used=[]
                )
                
                print(f"📚 Stored conversation for adaptive learning")
            
            return body
            
        except Exception as e:
            print(f"❌ Outlet processing error: {e}")
            return body

    async def cleanup(self):
        """Cleanup resources"""
        if self.client:
            await self.client.aclose()
            self.client = None

# Create the pipeline instance
advanced_memory_pipeline = AdvancedMemoryPipeline()

# Export the required functions for OpenWebUI
async def inlet(body: dict, user: Optional[dict] = None) -> dict:
    """Filter mode entry point"""
    return await advanced_memory_pipeline.inlet(body, user)

async def pipe(body: dict, user: Optional[dict] = None) -> dict:
    """Pipe mode entry point"""
    return await advanced_memory_pipeline.pipe(body, user)

async def outlet(body: dict, user: Optional[dict] = None) -> dict:
    """Outlet processing entry point"""
    return await advanced_memory_pipeline.outlet(body, user)

def on_startup():
    """Called when pipeline starts"""
    print("🚀 Advanced Memory Pipeline started")
    print("📋 Configuration:")
    print(f"   Backend URL: {advanced_memory_pipeline.valves.backend_url}")
    print(f"   Memory injection: {advanced_memory_pipeline.valves.enable_memory_injection}")
    print(f"   Learning enabled: {advanced_memory_pipeline.valves.enable_learning}")
    print(f"   Memory limit: {advanced_memory_pipeline.valves.memory_limit}")

def on_shutdown():
    """Called when pipeline shuts down"""
    print("🛑 Advanced Memory Pipeline shutting down")
    # Note: async cleanup would need to be handled differently in a real OpenWebUI environment
