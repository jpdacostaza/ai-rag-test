"""
Enhanced Memory Pipeline for OpenWebUI (Modular Version)
========================================================

A comprehensive, modular pipeline that provides memory storage and retrieval capabilities
for OpenWebUI conversations with proper user authentication context.

This modular version splits the functionality into separate modules for better:
- Code organization and maintainability
- Debugging and troubleshooting
- Feature development and testing
- Code reusability

UNIVERSAL MODEL COMPATIBILITY:
- Works with any LLM model (local or cloud-based)
- Compatible with Ollama models (llama3.2, mistral, etc.)
- Supports OpenAI-compatible APIs
- Works with older and newer model architectures
- No model-specific dependencies or requirements
- Memory instructions work via system message injection (universal approach)
"""

import sys
import os
import time
from typing import List, Optional, Dict, Any

# Add the pipelines directory to the Python path for imports
sys.path.insert(0, '/app/pipelines')

try:
    from memory_system.config import MemoryValves
    from memory_system.api_client import MemoryAPIClient
    from memory_system.auth import UserAuthManager
    from memory_system.processor import MemoryProcessor
except ImportError as e:
    print(f"[MEMORY PIPELINE ERROR] Failed to import memory system modules: {e}")
    print("[MEMORY PIPELINE ERROR] Falling back to basic implementation")
    
    # Fallback basic implementation
    from pydantic import BaseModel
    from typing import List
    
    class MemoryValves(BaseModel):
        model_config = {"protected_namespaces": ()}
        pipelines: List[str] = ["*"]
        priority: int = 0
        backend_url: str = "http://memory_api:8080"
        enable_memory: bool = True
        debug_mode: bool = True


class Pipeline:
    """Enhanced Memory Pipeline for OpenWebUI (Modular Version)."""
    
    class Valves(MemoryValves):
        """Configuration valves inherited from memory system config."""
        pass
    
    def __init__(self):
        """Initialize the modular memory pipeline."""
        self.name = "Enhanced Memory Pipeline (Modular)"
        self.valves = self.Valves()
        
        # Initialize modular components
        try:
            self.api_client = MemoryAPIClient(
                backend_url=self.valves.backend_url,
                timeout=self.valves.api_timeout,
                debug=self.valves.debug_mode
            )
            self.auth_manager = UserAuthManager(debug=self.valves.debug_mode)
            self.memory_processor = MemoryProcessor(debug=self.valves.debug_mode)
            
            self.log("Enhanced Memory Pipeline (Modular) initialized successfully")
            self.log("📁 Modular components loaded:")
            self.log("   • MemoryAPIClient - API communication")
            self.log("   • UserAuthManager - Authentication & sessions")
            self.log("   • MemoryProcessor - Memory formatting & context")
            
        except Exception as e:
            self.log(f"Error initializing modular components: {e}", "ERROR")
            # Initialize with None values for fallback
            self.api_client = None
            self.auth_manager = None
            self.memory_processor = None
    
    def log(self, message: str, level: str = "INFO"):
        """Log messages with consistent formatting."""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        print(f"[MEMORY PIPELINE {level}] {message}")
    
    async def inlet(self, body: Dict[str, Any], __user__: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Inlet filter - processes incoming requests and injects memory context.
        This runs BEFORE the request reaches the model.
        """
        try:
            # Early return if memory is disabled
            if not self.valves.enable_memory:
                return body
            
            # Check if modular components are available
            if not all([self.api_client, self.auth_manager, self.memory_processor]):
                self.log("Modular components not available, skipping memory injection", "WARNING")
                return body
            
            # Add user object to body for authentication
            if __user__:
                body["__user__"] = __user__
            
            # Authenticate user
            user_id, user_data = self.auth_manager.authenticate_user(body)
            if not user_id:
                self.log("User authentication failed, skipping memory injection", "WARNING")
                return body
            
            # Validate session consistency
            if self.valves.enforce_user_session_consistency:
                session_valid = self.auth_manager.validate_session_consistency(user_id, body)
                if session_valid:
                    self.log(f"✅ Session consistency validated for user {user_id} via explicit_id")
                else:
                    self.log(f"⚠️ Session consistency check failed for user {user_id}")
            
            # Extract query from messages
            messages = body.get("messages", [])
            if not messages:
                return body
            
            query = self.memory_processor.extract_query_from_messages(messages)
            if not query:
                self.log("No query found in messages, skipping memory retrieval")
                return body
            
            # Retrieve memories
            memories = await self.api_client.get_memories(
                user_id=user_id,
                query=query,
                max_memories=self.valves.max_memories
            )
            
            if not memories:
                # No memories found - inject new user system message
                if self.valves.debug_mode:
                    self.log(f"� No previous memories found for user {user_id} - introducing memory capabilities")
                
                # Always inject enhanced persona, regardless of memory availability
                enhanced_system_message = self.memory_processor.create_system_message("", user_id, 0)
                
                # Add system message to conversation
                if "messages" in body:
                    # Check if there's already a system message
                    existing_system = any(msg.get("role") == "system" for msg in body["messages"])
                    
                    if existing_system:
                        # Update existing system message
                        for msg in body["messages"]:
                            if msg.get("role") == "system":
                                msg["content"] = enhanced_system_message
                                if self.valves.debug_mode:
                                    self.log(f"📝 Updated system message for user {user_id} (Welcome back)")
                                break
                    else:
                        # Add new system message at the beginning
                        body["messages"].insert(0, {
                            "role": "system",
                            "content": enhanced_system_message
                        })
                        if self.valves.debug_mode:
                            self.log(f"📝 Added system message for user {user_id} (New user)")
                
                return body
            
            # Format memory context
            memory_context = self.memory_processor.format_memory_context(memories, user_id)
            memory_quality_score = self.memory_processor.calculate_memory_quality_score(memories)
            
            if self.valves.debug_mode:
                self.log(f"💭 Retrieved {len(memories)} memories for user {user_id}")
                self.log(f"📝 Memory context prepared (Quality: {memory_quality_score}/10)")
            
            # Create enhanced system message
            enhanced_system_message = self.memory_processor.create_system_message(
                memory_context, user_id, memory_quality_score
            )
            
            # Inject system message
            if "messages" in body:
                # Check if there's already a system message
                existing_system = any(msg.get("role") == "system" for msg in body["messages"])
                
                if existing_system:
                    # Update existing system message
                    for msg in body["messages"]:
                        if msg.get("role") == "system":
                            msg["content"] = enhanced_system_message
                            break
                else:
                    # Add new system message at the beginning
                    body["messages"].insert(0, {
                        "role": "system",
                        "content": enhanced_system_message
                    })
                
                # Enhance the last user message with memory context
                for msg in reversed(body["messages"]):
                    if msg.get("role") == "user":
                        original_content = msg.get("content", "")
                        enhanced_content = self.memory_processor.enhance_user_message(
                            original_content, memory_context, user_id
                        )
                        msg["content"] = enhanced_content
                        if self.valves.debug_mode:
                            self.log(f"💬 Enhanced user message with conversation context for user {user_id}")
                        break
            
            # Inject user ID for backend processing
            body["user_id"] = user_id
            if self.valves.debug_mode:
                self.log(f"🔐 User ID prepared for backend: {user_id}")
            
            return body
            
        except Exception as e:
            self.log(f"Error in inlet filter: {e}", "ERROR")
            return body
    
    async def outlet(self, body: Dict[str, Any], __user__: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Outlet filter - processes responses and stores interactions.
        This runs AFTER the model generates a response.
        """
        try:
            # Early return if memory is disabled
            if not self.valves.enable_memory:
                return body
            
            # Check if modular components are available
            if not all([self.api_client, self.auth_manager]):
                return body
            
            # Add user object to body for authentication
            if __user__:
                body["__user__"] = __user__
            
            # Authenticate user
            user_id, user_data = self.auth_manager.authenticate_user(body)
            if not user_id:
                return body
            
            if self.valves.debug_mode:
                self.log(f"💾 Saving conversation for user {user_id}")
            
            # Extract messages
            messages = body.get("messages", [])
            if len(messages) < 2:
                return body
            
            # Find the last user message and assistant response
            user_message = ""
            assistant_message = ""
            
            for msg in reversed(messages):
                if msg.get("role") == "user" and not user_message:
                    content = msg.get("content", "")
                    # Clean enhanced content back to original user message
                    if "[Previous conversation context available" in content:
                        lines = content.split("\n")
                        capturing = False
                        user_parts = []
                        for line in lines:
                            if "Current user message:" in line:
                                capturing = True
                                continue
                            if capturing:
                                user_parts.append(line)
                        user_message = "\n".join(user_parts).strip()
                    else:
                        user_message = content
                elif msg.get("role") == "assistant" and not assistant_message:
                    assistant_message = msg.get("content", "")
            
            # Validate interaction content
            if not user_message or not assistant_message:
                if self.valves.debug_mode:
                    self.log(f"⚠️ Incomplete conversation for user {user_id}: user={len(user_message)} chars, assistant={len(assistant_message)} chars")
                return body
            
            if self.valves.debug_mode:
                self.log(f"✅ Conversation validated for user {user_id}")
                self.log(f"� Saving: {len(user_message)} chars user msg, {len(assistant_message)} chars assistant msg")
            
            # Store the interaction
            success = await self.api_client.store_interaction(
                user_id=user_id,
                user_message=user_message,
                assistant_message=assistant_message
            )
            
            if success:
                if self.valves.debug_mode:
                    self.log(f"✅ Conversation saved for user {user_id}")
            else:
                self.log(f"❌ Failed to save conversation for user {user_id}", "ERROR")
            
            return body
            
        except Exception as e:
            self.log(f"Error in outlet filter: {e}", "ERROR")
            return body
    
    async def __del__(self):
        """Cleanup when pipeline is destroyed."""
        try:
            if self.api_client:
                await self.api_client.close()
        except:
            pass
