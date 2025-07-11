"""
Enhanced Memory Function for OpenWebUI
=====================================

A comprehensive memory system that integrates with the backend memory API
to provide persistent conversation context and learning capabilities.

This function uses the separated memory architecture for better maintainability.

⚠️  IMPORTANT NOTE: 
This function has limitations with user identification due to OpenWebUI's function architecture.
For proper user authentication and memory isolation, use the Pipelines version instead:
- File: memory_pipeline.py  
- Setup: Run setup_complete_memory.ps1 (installs both Function + Pipeline)
- Pipeline Setup: Run setup_memory_pipelines.ps1 (Pipeline only)

OpenWebUI Functions don't receive authenticated user context, while Pipelines do.
This means all users will share the same memory space with Functions.

NOTE: This is the primary memory function file used by the system.
The file at memory/functions/memory_filter.py serves as a fallback
in case this file is not available.
"""

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

# Import our separated memory components
try:
    from memory import MemoryService, MemoryConfig
except ImportError:
    # Fallback for when memory module is not properly installed
    MemoryService = None
    MemoryConfig = None


class Valves(BaseModel):
    """Configuration valves for the memory function."""
    
    # API Configuration
    backend_api_url: str = "http://backend:3000"
    memory_api_url: str = "http://memory_api:8080"
    
    # Memory Settings
    enable_memory: bool = True
    max_memories: int = 5
    memory_threshold: float = 0.05  # Lower threshold for better memory recall
    
    # Learning Settings
    enable_learning: bool = True
    auto_store_threshold: int = 1  # Store after 1+ exchanges (immediate storage)
    
    # Debug
    debug: bool = True


class MemoryAPIClient:
    """Client for interacting with the Memory API."""

    def __init__(self, base_url: str, timeout: float = 10.0, debug_log: callable = None):
        self.base_url = base_url
        self.timeout = timeout
        self.log = debug_log if debug_log else lambda msg, level: None

    async def retrieve_memories(self, user_id: str, query: str, limit: int, threshold: float) -> List[dict]:
        """Retrieve relevant memories from the memory API."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/api/memory/retrieve",
                    json={
                        "user_id": user_id,
                        "query": query,
                        "limit": limit,
                        "threshold": threshold
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

    async def store_interaction(self, user_id: str, messages: List[dict]) -> bool:
        """Store learning interaction in the memory system."""
        try:
            user_message, assistant_response = self._extract_interaction(messages)
            
            if user_message and assistant_response:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(
                        f"{self.base_url}/api/learning/process_interaction",
                        json={
                            "user_id": user_id,
                            "conversation_id": str(uuid.uuid4()),
                            "user_message": user_message,
                            "assistant_response": assistant_response,
                            "timestamp": str(int(time.time())),
                            "source": "openwebui_function"
                        }
                    )
                    
                    if response.status_code == 200:
                        self.log("Learning interaction stored successfully")
                        return True
                    else:
                        self.log(f"Learning storage failed: {response.status_code}", "ERROR")
                        
        except Exception as e:
            self.log(f"Error storing learning interaction: {str(e)}", "ERROR")
        
        return False

    def _extract_interaction(self, messages: List[dict]) -> tuple[str, str]:
        """Extract user and assistant messages from a list of messages."""
        user_message = ""
        assistant_response = ""
        for msg in reversed(messages):
            if msg.get("role") == "user" and not user_message:
                user_message = msg.get("content", "")
            elif msg.get("role") == "assistant" and not assistant_response:
                assistant_response = msg.get("content", "")
        return user_message, assistant_response


class Filter:
    """Enhanced Memory Filter for OpenWebUI using separated memory architecture."""
    
    def __init__(self):
        self.valves = Valves()
        self.conversation_count = {}  # Legacy fallback support
        
        # Initialize memory service with proper separation of concerns
        if MemoryService and MemoryConfig:
            config = MemoryConfig(
                api_url=self.valves.memory_api_url,
                timeout=10.0,
                max_memories=self.valves.max_memories,
                relevance_threshold=self.valves.memory_threshold,
                auto_store_enabled=self.valves.enable_learning,
                auto_store_threshold=self.valves.auto_store_threshold,
                debug_enabled=self.valves.debug
            )
            self.memory_service = MemoryService(config, self.log)
        else:
            # Fallback to legacy implementation
            self.memory_service = None
            self.memory_client = MemoryAPIClient(
                base_url=self.valves.memory_api_url, 
                debug_log=self.log
            )
        
    def log(self, message: str, level: str = "INFO"):
        """Log messages with timestamp."""
        if self.valves.debug:
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            print(f"[{timestamp}] [{level}] [Memory] {message}")
    
    async def inlet(self, body: dict, user: Optional[dict] = None) -> dict:
        """Process incoming messages to inject relevant memories."""
        self.log("INLET: Function called", "DEBUG")
        self.log(f"INLET: Full body received: {body}", "DEBUG")
        self.log(f"INLET: User object received: {user}", "DEBUG")
        
        if not self.valves.enable_memory:
            self.log("INLET: Memory disabled, skipping", "DEBUG")
            return body
            
        try:
            user_id = self._get_user_id(user, body)
            messages = body.get("messages", [])
            
            latest_message = self._get_latest_user_message(messages)
            if not latest_message:
                self.log("INLET: No user message found", "DEBUG")
                return body
                
            self.log(f"INLET: Processing message for user {user_id}: {latest_message[:100]}...")
            
            # Use new memory service if available, otherwise fallback
            if self.memory_service:
                self.log("INLET: Using new memory service", "DEBUG")
                memories = await self.memory_service.get_relevant_memories(
                    user_id=user_id,
                    query_text=latest_message
                )
                
                if memories:
                    memory_context = self.memory_service.format_memories_for_injection(memories)
                    body = self.memory_service.inject_memory_context(body, memory_context)
                    self.log(f"INLET: Injected {len(memories)} memories into conversation")
                else:
                    self.log("INLET: No memories found with new service", "DEBUG")
            else:
                # Legacy fallback
                self.log("INLET: Using legacy memory client", "DEBUG")
                memories = await self.memory_client.retrieve_memories(
                    user_id=user_id,
                    query=latest_message,
                    limit=self.valves.max_memories,
                    threshold=self.valves.memory_threshold
                )
                
                if memories:
                    memory_context = self._format_memories(memories)
                    body = self._inject_memory_context(body, memory_context)
                    self.log(f"INLET: Injected {len(memories)} memories into conversation")
                else:
                    self.log("INLET: No memories found with legacy client", "DEBUG")
            
        except Exception as e:
            self.log(f"INLET: Error - {str(e)}", "ERROR")
            
        return body
    
    async def outlet(self, body: dict, user: Optional[dict] = None) -> dict:
        """Process outgoing messages to store learning data."""
        self.log("OUTLET: Function called", "DEBUG")
        self.log(f"OUTLET: Full body received: {body}", "DEBUG") 
        self.log(f"OUTLET: User object received: {user}", "DEBUG")
        
        if not self.valves.enable_learning:
            self.log("OUTLET: Learning disabled, skipping", "DEBUG")
            return body
            
        try:
            user_id = self._get_user_id(user, body)
            messages = body.get("messages", [])
            
            self.log(f"OUTLET: Processing for user {user_id}, messages count: {len(messages)}")
            
            # Use new memory service if available, otherwise fallback  
            if self.memory_service:
                self.log("OUTLET: Using new memory service", "DEBUG")
                stored = await self.memory_service.track_conversation_and_store(user_id, messages)
                self.log(f"OUTLET: Memory service returned: {stored}")
            else:
                # Legacy fallback
                self.log("OUTLET: Using legacy memory client", "DEBUG")
                self.conversation_count[user_id] = self.conversation_count.get(user_id, 0) + 1
                self.log(f"OUTLET: Conversation count for {user_id}: {self.conversation_count[user_id]}/{self.valves.auto_store_threshold}")
                
                if self.conversation_count[user_id] >= self.valves.auto_store_threshold:
                    self.log(f"OUTLET: Threshold reached, storing interaction for {user_id}")
                    stored = await self.memory_client.store_interaction(user_id, messages)
                    self.log(f"OUTLET: Store result: {stored}")
                    self.conversation_count[user_id] = 0
                else:
                    self.log(f"OUTLET: Threshold not reached yet for {user_id}")
                
        except Exception as e:
            self.log(f"OUTLET: Error - {str(e)}", "ERROR")
            
        return body
    
    def _get_user_id(self, user: Optional[dict], body: Optional[dict] = None) -> str:
        """Extract user ID from user object with fallback options."""
        self.log(f"DEBUG: Raw user object received: {user}", "DEBUG")
        self.log(f"DEBUG: Body keys available: {list(body.keys()) if body else 'None'}", "DEBUG")
        
        # First, try to get user info from the user object
        if user and isinstance(user, dict):
            # Try multiple possible user ID fields in order of preference
            user_id = (
                user.get("id") or 
                user.get("user_id") or 
                user.get("email") or 
                user.get("username") or
                user.get("sub") or  # JWT subject
                None
            )
            if user_id:
                self.log(f"DEBUG: Extracted user_id '{user_id}' from user object", "DEBUG")
                return str(user_id)
        
        # Try to extract user info from the request body
        if body and isinstance(body, dict):
            # Check for user info in various places in the body
            user_from_body = (
                body.get("user") or
                body.get("user_id") or 
                body.get("metadata", {}).get("user_id") or
                body.get("chat_id") or  # Sometimes chat ID contains user info
                None
            )
            if user_from_body:
                self.log(f"DEBUG: Found user info in body: '{user_from_body}'", "DEBUG")
                if isinstance(user_from_body, dict):
                    extracted_id = (
                        user_from_body.get("id") or
                        user_from_body.get("email") or
                        user_from_body.get("username") or
                        str(user_from_body)
                    )
                    if extracted_id:
                        self.log(f"DEBUG: Extracted user_id '{extracted_id}' from body", "DEBUG")
                        return str(extracted_id)
                else:
                    self.log(f"DEBUG: Using user_id '{user_from_body}' from body", "DEBUG")
                    return str(user_from_body)
        
        # For OpenWebUI, if no user context is provided, try to create a consistent
        # session-based ID rather than using "anonymous" which fragments memory
        session_id = "openwebui_default_user"  # Consistent default for OpenWebUI
        self.log(f"DEBUG: No user identification found, using session-based user_id '{session_id}'", "DEBUG")
        return session_id
    
    def _get_latest_user_message(self, messages: List[dict]) -> Optional[str]:
        """Get the content of the latest user message."""
        for msg in reversed(messages):
            if msg.get("role") == "user":
                return msg.get("content")
        return None
    
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
