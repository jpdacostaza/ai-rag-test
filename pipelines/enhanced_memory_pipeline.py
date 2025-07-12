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

# Add the backend directory for web search tools
sys.path.insert(0, '/app')

# Import web search tools first (independent of memory system)
web_search_available = False
search_web = None
should_trigger_web_search = None
format_web_results_for_chat = None

try:
    # Try pipeline-specific web search first
    from pipeline_web_search import search_web, should_trigger_web_search, format_web_results_for_chat
    web_search_available = True
    print("[MEMORY PIPELINE INFO] Pipeline web search tools imported successfully - PRIMARY METHOD ACTIVE")
except ImportError as e:
    print(f"[MEMORY PIPELINE ERROR] Pipeline web search import failed: {e}")
    try:
        # Fallback to original web search tool
        from web_search_tool import search_web, should_trigger_web_search, format_web_results_for_chat
        web_search_available = True
        print("[MEMORY PIPELINE INFO] Original web search tools imported successfully - FALLBACK METHOD ACTIVE")
    except ImportError as e2:
        print(f"[MEMORY PIPELINE ERROR] Both web search imports failed: {e2}")
        print(f"[MEMORY PIPELINE INFO] Initializing web search FALLBACK MODE")
        
        # Only define fallback functions when both imports fail
        async def search_web(query: str, max_results: int = 3):
            print("[MEMORY PIPELINE INFO] Using web search FALLBACK - search unavailable")
            return {"results": [], "status": "fallback_unavailable"}
        
        def should_trigger_web_search(query: str, response: str):
            print("[MEMORY PIPELINE INFO] Using web search trigger FALLBACK - always returns False")
            return False
        
        def format_web_results_for_chat(results):
            print("[MEMORY PIPELINE INFO] Using web search formatter FALLBACK - returning empty")
            return ""
        
        web_search_available = False

# Now try to import memory system
memory_system_available = False
MemoryValves = None
MemoryAPIClient = None
UserAuthManager = None
MemoryProcessor = None

try:
    from memory_system.config import MemoryValves
    from memory_system.api_client import MemoryAPIClient
    from memory_system.auth import UserAuthManager
    from memory_system.processor import MemoryProcessor
    memory_system_available = True
    print("[MEMORY PIPELINE INFO] Memory system modules imported successfully - PRIMARY METHOD ACTIVE")
            
except ImportError as e:
    print(f"[MEMORY PIPELINE ERROR] Primary memory system import failed: {e}")
    print("[MEMORY PIPELINE INFO] Initializing memory system FALLBACK MODE")
    
    # Only define fallback when primary import fails
    from pydantic import BaseModel
    from typing import List
    
    class MemoryValves(BaseModel):
        model_config = {"protected_namespaces": ()}
        pipelines: List[str] = []  # Empty array initially - will be set to ["*"] in init
        priority: int = 0  # Higher priority (lower number) runs first
        backend_url: str = "http://backend-memory-api:8080"  # Correct container name and internal port
        enable_memory: bool = True
        max_memories: int = 100
        memory_threshold: float = 0.001
        quality_threshold: int = 3
        require_authenticated_user: bool = False  # Allow anonymous users for testing
        enforce_user_session_consistency: bool = True
        api_timeout: int = 10
        retry_attempts: int = 3
        debug_mode: bool = True
    
    memory_system_available = False


class Pipeline:
    """Enhanced Memory Pipeline for OpenWebUI (Modular Version)."""
    
    # Class-level configuration for auto-registration
    type = "filter"  # Explicitly define as filter pipeline
    id = "enhanced_memory_pipeline"
    name = "Enhanced Memory Pipeline"
    
    class Valves(MemoryValves):
        """Configuration valves inherited from memory system config."""
        pass
    
    def __init__(self):
        """Initialize the modular memory pipeline."""
        # Set the type and identifiers following best practices
        self.type = "filter"
        self.name = "Enhanced Memory Pipeline"
        
        # Initialize valves with proper configuration
        self.valves = self.Valves(
            **{
                "pipelines": ["*"],  # Connect to all pipelines
                "priority": 0,       # Highest priority
                "backend_url": "http://backend-memory-api:8080",  # Correct container name
                "enable_memory": True,
                "debug_mode": True,
            }
        )
        
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
            # LOG EVERY REQUEST that comes through the pipeline
            self.log("🔥 INLET CALLED - Pipeline is processing a request")
            if self.valves.debug_mode:
                messages = body.get("messages", [])
                for i, msg in enumerate(messages):
                    if msg.get("role") == "user":
                        content = msg.get("content", "")[:100]  # First 100 chars
                        self.log(f"📨 User message {i}: {content}...")
            
            # Early return if memory is disabled
            if not self.valves.enable_memory:
                self.log("⚠️ Memory disabled, returning body unchanged")
                return body
            
            # Extract query from messages for web search (do this early, before auth)
            query = ""
            for msg in body.get("messages", []):
                if msg.get("role") == "user":
                    query = msg.get("content", "")
                    break
            
            # WEB SEARCH PROCESSING (Independent of authentication)
            # This ensures web search works even if memory system fails
            if query and web_search_available:
                self.log(f"🔍 Checking web search trigger for query: '{query[:50]}...'")
                if should_trigger_web_search(query, ""):
                    self.log(f"✅ WEB SEARCH TRIGGERED for query: {query}")
                    
                    # Perform web search
                    search_results = await search_web(query, max_results=3)
                    
                    if search_results.get("results"):
                        # Add web search results to system message
                        web_context = format_web_results_for_chat(search_results)
                        
                        # Find existing system message or create one
                        system_msg_found = False
                        for msg in body["messages"]:
                            if msg.get("role") == "system":
                                msg["content"] += f"\n\nCurrent web search results for '{query}':{web_context}"
                                system_msg_found = True
                                break
                        
                        # If no system message exists, create one
                        if not system_msg_found:
                            body["messages"].insert(0, {
                                "role": "system",
                                "content": f"You are a helpful assistant with web search capabilities.\n\nCurrent web search results for '{query}':{web_context}"
                            })
                        
                        self.log(f"🌐 Added web search results to context")
                    elif search_results.get("status") == "fallback_unavailable":
                        self.log(f"⚠️ Web search triggered but using FALLBACK MODE - no results available")
                else:
                    self.log(f"❌ Web search NOT triggered for query: '{query[:50]}...'")
            elif query and not web_search_available:
                # Web search not available - check if user was asking for search
                if should_trigger_web_search(query, ""):
                    self.log(f"⚠️ User requested web search but web search is in FALLBACK MODE")
                    self.log(f"⚠️ Query would have triggered search: {query}")
                else:
                    self.log(f"ℹ️ Query would not have triggered web search: '{query[:50]}...'")
            else:
                self.log(f"ℹ️ No query found or web search unavailable")
            
            # MEMORY SYSTEM PROCESSING (Requires authentication)
            # Check if modular components are available
            if not all([self.api_client, self.auth_manager, self.memory_processor]):
                self.log("Modular components not available, skipping memory injection", "WARNING")
                return body
            
            # Add user object to body for authentication
            if __user__:
                body["__user__"] = __user__
            
            # Authenticate user - be more flexible with user ID formats
            user_id, user_data = self.auth_manager.authenticate_user(body)
            
            # If no user_id found but __user__ has an id, use it directly
            if not user_id and __user__ and __user__.get("id"):
                user_id = str(__user__.get("id"))
                user_data = __user__
                if self.valves.debug_mode:
                    self.log(f"✅ Using fallback user ID from __user__: {user_id}")
            
            # If still no user_id, create a temporary one for this session
            if not user_id:
                user_id = "anonymous-user"
                user_data = {"id": user_id, "name": "Anonymous User"}
                if self.valves.debug_mode:
                    self.log(f"⚠️ No user authentication found, using anonymous session: {user_id}")
            
            if self.valves.debug_mode:
                self.log(f"🔐 Proceeding with user: {user_id}")
            
            # Validate session consistency
            if self.valves.enforce_user_session_consistency:
                session_valid = self.auth_manager.validate_session_consistency(user_id, body)
                if session_valid:
                    self.log(f"✅ Session consistency validated for user {user_id} via explicit_id")
                else:
                    self.log(f"⚠️ Session consistency check failed for user {user_id}")
            
            # Extract query from messages (again, for memory processing)
            query = ""
            for msg in body.get("messages", []):
                if msg.get("role") == "user":
                    query = msg.get("content", "")
                    break
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
            
            # Inject memory context silently into system message (no robotic formatting)
            if "messages" in body and memory_context:
                # Add clarification about Swift (financial company vs programming language)
                swift_clarification = ""
                if "swift" in query.lower() and any("apple" in mem.lower() or "programming" in mem.lower() for mem in memory_context.lower().split()):
                    swift_clarification = "\n\nIMPORTANT: The user works at SWIFT (Society for Worldwide Interbank Financial Telecommunication) - the global financial messaging company at https://www.swift.com/ - NOT Apple's Swift programming language."
                
                # Create a natural, invisible system message with memory context
                natural_system_message = f"""You are a helpful AI assistant with real-time web search capabilities. Here's some relevant context from previous conversations:

{memory_context}{swift_clarification}

CRITICAL INSTRUCTIONS:
- You have access to current web information through search capabilities
- When you don't have current, specific, or factual information, you should search the web rather than guessing
- For questions about current events, company information, recent developments, or real-time data, use web search
- Be honest about knowledge limitations and search when uncertain
- Integrate web search results naturally into responses
- Never hallucinate facts - search for current information when needed

Respond naturally without mentioning this context directly. Use it to inform your responses in a human-like way."""
                
                # Check if there's already a system message
                existing_system = any(msg.get("role") == "system" for msg in body["messages"])
                
                if existing_system:
                    # Update existing system message with memory context
                    for msg in body["messages"]:
                        if msg.get("role") == "system":
                            # Append memory context to existing system message
                            original_content = msg.get("content", "")
                            msg["content"] = f"{original_content}\n\n{natural_system_message}"
                            break
                else:
                    # Add new system message at the beginning
                    body["messages"].insert(0, {
                        "role": "system",
                        "content": natural_system_message
                    })
                
                if self.valves.debug_mode:
                    self.log(f"🧠 Memory context injected invisibly for user {user_id}")
                    if swift_clarification:
                        self.log(f"🏢 Added Swift company clarification")
            
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
