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

try:
    import httpx
except ImportError:
    import subprocess
    import sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "httpx"])
    import httpx

class Pipeline:
    class Valves(BaseModel):
        # Backend integration settings
        backend_url: str = "http://host.docker.internal:8001"
        api_key: str = "your_openwebui_api_key_here"
        
        # Memory retrieval settings
        enable_memory_retrieval: bool = True
        max_memory_results: int = 3
        memory_relevance_threshold: float = 0.7
        context_injection_enabled: bool = True
        
        # Learning settings
        enable_adaptive_learning: bool = True
        store_interactions: bool = True
        learning_feedback_enabled: bool = True
        
        # Performance settings
        timeout_seconds: int = 5
        async_processing: bool = True
        debug_logging: bool = True
        
        # Pipeline behavior
        pipelines: List[str] = ["*"]  # Apply to all models
        priority: int = 0  # High priority filter
        
    def __init__(self):
        self.type = "filter"
        self.name = "Advanced Memory Pipeline"
        self.valves = self.Valves()
        
        # Performance tracking
        self.total_requests = 0
        self.memory_hits = 0
        self.learning_stored = 0
        self.avg_response_time = 0.0
        
        # Error tracking
        self.errors = []
        self.last_error = None
        
    async def on_startup(self):
        """Initialize the pipeline and verify backend connectivity"""
        self.log("🚀 Advanced Memory Pipeline starting up...")
        
        # Test backend connectivity
        try:
            health_check = await self.check_backend_health()
            if health_check:
                self.log("✅ Backend connectivity verified")
            else:
                self.log("⚠️ Backend health check failed - pipeline will continue with degraded functionality")
        except Exception as e:
            self.log(f"❌ Startup error: {e}")
            
        self.log("🧠 Advanced Memory Pipeline ready!")
        
    async def on_shutdown(self):
        """Cleanup and final statistics"""
        self.log("🛑 Advanced Memory Pipeline shutting down...")
        self.log(f"📊 Final stats - Requests: {self.total_requests}, Memory hits: {self.memory_hits}, Learning stored: {self.learning_stored}")
        
    async def on_valves_updated(self):
        """Handle configuration updates"""
        self.log("⚙️ Configuration updated")
        if self.valves.debug_logging:
            self.log(f"🔧 New config - Memory: {self.valves.enable_memory_retrieval}, Learning: {self.valves.enable_adaptive_learning}")
    
    def log(self, message: str):
        """Enhanced logging with timestamps"""
        if self.valves.debug_logging:
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] 🧠 {message}")
    
    async def check_backend_health(self) -> bool:
        """Check if backend is healthy and responsive"""
        try:
            async with httpx.AsyncClient(timeout=self.valves.timeout_seconds) as client:
                response = await client.get(
                    f"{self.valves.backend_url}/health",
                    headers={"Authorization": f"Bearer {self.valves.api_key}"}
                )
                return response.status_code == 200
        except Exception as e:
            self.log(f"🔴 Health check failed: {e}")
            return False
    
    async def get_user_memory(self, user_id: str, query: str) -> List[Dict[str, Any]]:
        """Retrieve relevant user memories from backend ChromaDB"""
        if not self.valves.enable_memory_retrieval:
            return []
            
        try:
            self.log(f"🔍 Retrieving memories for user {user_id}")
            
            async with httpx.AsyncClient(timeout=self.valves.timeout_seconds) as client:
                response = await client.post(
                    f"{self.valves.backend_url}/api/memory/retrieve",
                    headers={
                        "Authorization": f"Bearer {self.valves.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "user_id": user_id,
                        "query": query,
                        "limit": self.valves.max_memory_results,
                        "threshold": self.valves.memory_relevance_threshold
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    memories = result.get("memories", [])
                    self.log(f"✅ Retrieved {len(memories)} memories")
                    if memories:
                        self.memory_hits += 1
                    return memories
                else:
                    self.log(f"⚠️ Memory retrieval failed: HTTP {response.status_code}")
                    return []
                    
        except Exception as e:
            self.log(f"❌ Memory retrieval error: {e}")
            self.last_error = str(e)
            return []
    
    async def store_interaction(self, user_id: str, user_message: str, assistant_response: str, response_time: float):
        """Store interaction for adaptive learning"""
        if not self.valves.enable_adaptive_learning or not self.valves.store_interactions:
            return
            
        try:
            self.log(f"💾 Storing interaction for learning: {user_id}")
            
            if self.valves.async_processing:
                # Process in background to avoid blocking
                asyncio.create_task(self._store_interaction_async(user_id, user_message, assistant_response, response_time))
            else:
                await self._store_interaction_async(user_id, user_message, assistant_response, response_time)
                
        except Exception as e:
            self.log(f"❌ Learning storage error: {e}")
            self.last_error = str(e)
    
    async def _store_interaction_async(self, user_id: str, user_message: str, assistant_response: str, response_time: float):
        """Internal async method for storing interactions"""
        try:
            async with httpx.AsyncClient(timeout=self.valves.timeout_seconds) as client:
                response = await client.post(
                    f"{self.valves.backend_url}/api/learning/process_interaction",
                    headers={
                        "Authorization": f"Bearer {self.valves.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "user_id": user_id,
                        "conversation_id": f"pipeline_{user_id}_{int(time.time())}",
                        "user_message": user_message,
                        "assistant_response": assistant_response,
                        "response_time": response_time,
                        "tools_used": ["advanced_memory_pipeline"],
                        "source": "pipeline"
                    }
                )
                
                if response.status_code == 200:
                    self.learning_stored += 1
                    self.log(f"✅ Learning interaction stored successfully")
                else:
                    self.log(f"⚠️ Learning storage failed: HTTP {response.status_code}")
                    
        except Exception as e:
            self.log(f"❌ Async learning storage error: {e}")
    
    def format_memory_context(self, memories: List[Dict[str, Any]]) -> str:
        """Format memories into context for injection"""
        if not memories:
            return ""
            
        context_parts = []
        for i, memory in enumerate(memories[:self.valves.max_memory_results], 1):
            # Handle different memory formats from your backend
            if isinstance(memory, dict):
                text = memory.get('content', memory.get('text', memory.get('document', str(memory))))
                metadata = memory.get('metadata', {})
                source = metadata.get('source', 'previous conversation')
            else:
                text = str(memory)
                source = 'previous conversation'
            
            # Truncate very long memories
            if len(text) > 200:
                text = text[:200] + "..."
                
            context_parts.append(f"{i}. {text} (from {source})")
        
        return "\n".join(context_parts)
    
    async def inlet(self, body: dict, user: Optional[dict] = None) -> dict:
        """Pre-process user input - inject memory context"""
        start_time = time.time()
        self.total_requests += 1
        
        try:
            # Skip if memory retrieval is disabled or no user
            if not self.valves.enable_memory_retrieval or not user:
                return body
                
            user_id = user.get("id", f"anonymous_{int(time.time())}")
            
            # Get the current user message
            messages = body.get("messages", [])
            if not messages or messages[-1].get("role") != "user":
                return body
                
            user_message = messages[-1].get("content", "")
            if not user_message:
                return body
            
            self.log(f"🔄 Processing inlet for user: {user_id}")
            
            # Retrieve relevant memories
            memories = await self.get_user_memory(user_id, user_message)
            
            if memories and self.valves.context_injection_enabled:
                # Format memory context
                memory_context = self.format_memory_context(memories)
                
                if memory_context:
                    # Enhanced context injection with clear structure
                    enhanced_message = f"""Based on our previous conversations:
{memory_context}

Current question: {user_message}"""
                    
                    # Update the message with enhanced context
                    body["messages"][-1]["content"] = enhanced_message
                    
                    self.log(f"✅ Injected {len(memories)} memory items into context")
                else:
                    self.log("ℹ️ No relevant memory context to inject")
            else:
                self.log("ℹ️ No memories found or injection disabled")
                
            # Track performance
            processing_time = time.time() - start_time
            self.avg_response_time = (self.avg_response_time + processing_time) / 2
            
            return body
            
        except Exception as e:
            self.log(f"❌ Inlet processing error: {e}")
            self.last_error = str(e)
            self.errors.append({"time": datetime.now().isoformat(), "error": str(e), "stage": "inlet"})
            # Return original body on error
            return body
    
    async def outlet(self, body: dict, user: Optional[dict] = None) -> dict:
        """Post-process assistant response - store for learning"""
        try:
            # Skip if learning is disabled or no user
            if not self.valves.enable_adaptive_learning or not user:
                return body
                
            user_id = user.get("id", f"anonymous_{int(time.time())}")
            messages = body.get("messages", [])
            
            if len(messages) < 2:
                return body
            
            # Find the last user message and assistant response
            user_message = ""
            assistant_response = ""
            
            # Look for the most recent user-assistant pair
            for i in range(len(messages) - 1, -1, -1):
                msg = messages[i]
                if msg["role"] == "assistant" and not assistant_response:
                    assistant_response = msg.get("content", "")
                elif msg["role"] == "user" and not user_message and assistant_response:
                    user_message = msg.get("content", "")
                    break
            
            if user_message and assistant_response:
                self.log(f"🔄 Processing outlet for user: {user_id}")
                
                # Calculate approximate response time (from processing start)
                response_time = self.avg_response_time
                
                # Store the interaction for learning
                await self.store_interaction(user_id, user_message, assistant_response, response_time)
            else:
                self.log("ℹ️ No valid user-assistant pair found for learning")
                
        except Exception as e:
            self.log(f"❌ Outlet processing error: {e}")
            self.last_error = str(e)
            self.errors.append({"time": datetime.now().isoformat(), "error": str(e), "stage": "outlet"})
        
        return body
    
    def get_pipeline_status(self) -> dict:
        """Get current pipeline status and statistics"""
        return {
            "status": "active",
            "total_requests": self.total_requests,
            "memory_hits": self.memory_hits,
            "learning_stored": self.learning_stored,
            "avg_response_time": round(self.avg_response_time, 3),
            "memory_enabled": self.valves.enable_memory_retrieval,
            "learning_enabled": self.valves.enable_adaptive_learning,
            "last_error": self.last_error,
            "error_count": len(self.errors)
        }
