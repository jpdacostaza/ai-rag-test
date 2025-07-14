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
import logging
from typing import List, Optional, Dict, Any

# Configure pipeline logger to avoid duplicates
def setup_pipeline_logging():
    logger = logging.getLogger("enhanced_memory_pipeline")
    if logger.hasHandlers():
        logger.handlers.clear()
    
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        "[MEMORY PIPELINE %(levelname)s] %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False  # Prevent duplicate logs
    return logger

# Initialize pipeline logger
pipeline_logger = setup_pipeline_logging()

# Add the pipelines directory to the Python path for imports
sys.path.insert(0, '/app/pipelines')

# Add the backend directory for web search tools
sys.path.insert(0, '/app')

# Add core modules to path
sys.path.insert(0, '/app/core')

# Import centralized configuration and security
try:
    # Try to import from the main backend if available
    sys.path.insert(0, '/app')
    from config.config import get_config
    pipeline_logger.info("Backend config modules loaded successfully")
    config = get_config()
    auth_manager = None
except ImportError as e:
    pipeline_logger.info(f"Backend config not available, using pipeline fallback: {e}")
    # Fallback to pipeline configuration
    try:
        sys.path.insert(0, '/app/pipelines')
        from config.config import get_config
        pipeline_logger.info("Pipeline config loaded successfully")
        config = get_config()
        auth_manager = None
    except ImportError as fallback_e:
        pipeline_logger.info(f"Pipeline config also failed, using minimal fallback: {fallback_e}")
        config = None
        auth_manager = None

# Import web search tools (using correct paths)
web_search_available = False
search_web = None
should_trigger_web_search = None
format_web_results_for_chat = None

try:
    # Try pipeline-specific web search from failed directory (available in container)
    from failed.pipeline_web_search import search_web, should_trigger_web_search, format_web_results_for_chat
    web_search_available = True
    pipeline_logger.info("Pipeline web search tools imported successfully - FALLBACK METHOD ACTIVE")
except ImportError as e:
    pipeline_logger.info(f"Pipeline web search not available: {e}")
    try:
        # Try importing from the main backend web search tool (not available in container)
        sys.path.insert(0, '/app')
        from utilities.web_search_tool import search_web, should_trigger_web_search, format_web_results_for_chat
        web_search_available = True
        pipeline_logger.info("Backend web search tools imported successfully - PRIMARY METHOD ACTIVE")
    except ImportError as e2:
        pipeline_logger.info(f"Backend web search also not available: {e2}")
        pipeline_logger.info("Initializing web search FALLBACK MODE")
        
        # Define fallback functions when both imports fail
        async def search_web(query: str, max_results: int = 3):
            pipeline_logger.info("Using web search FALLBACK - search unavailable")
            return {"results": [], "status": "fallback_unavailable"}
        
        def should_trigger_web_search(query: str, response: str = ""):
            pipeline_logger.info("Using web search trigger FALLBACK - always returns False")
            return False
        
        def format_web_results_for_chat(results):
            pipeline_logger.info("Using web search formatter FALLBACK - returning empty")
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
    pipeline_logger.info("Memory system modules imported successfully - PRIMARY METHOD ACTIVE")
            
except ImportError as e:
    pipeline_logger.error(f"Primary memory system import failed: {e}")
    pipeline_logger.info("Initializing memory system FALLBACK MODE")
    
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
            
            pipeline_logger.info("Enhanced Memory Pipeline (Modular) initialized successfully")
            pipeline_logger.info("📁 Modular components loaded:")
            pipeline_logger.info("   • MemoryAPIClient - API communication")
            pipeline_logger.info("   • UserAuthManager - Authentication & sessions")
            pipeline_logger.info("   • MemoryProcessor - Memory formatting & context")
            
        except Exception as e:
            pipeline_logger.error(f"Error initializing modular components: {e}")
            # Initialize with None values for fallback
            self.api_client = None
            self.auth_manager = None
            self.memory_processor = None
    
    def log(self, message: str, level: str = "INFO"):
        """Log messages with consistent formatting using proper logging."""
        log_method = getattr(pipeline_logger, level.lower(), pipeline_logger.info)
        log_method(message)
    
    async def inlet(self, body: Dict[str, Any], __user__: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Inlet filter - processes incoming requests and injects memory context.
        This runs BEFORE the request reaches the model.
        """
        try:
            # LOG EVERY REQUEST that comes through the pipeline
            self.log("🔥 INLET CALLED - Pipeline is processing a request")
            
            # Enhanced debugging for persona/model changes
            if self.valves.debug_mode:
                messages = body.get("messages", [])
                model_info = body.get("model", "unknown")
                self.log(f"📊 Request details: model={model_info}, {len(messages)} messages")
                
                for i, msg in enumerate(messages):
                    if msg.get("role") == "user":
                        content = msg.get("content", "")[:100]  # First 100 chars
                        self.log(f"📨 User message {i}: {content}...")
                        
                        # Check for persona-related commands
                        if "/persona" in content.lower() or "persona" in content.lower():
                            self.log(f"🎭 PERSONA CHANGE DETECTED in message: {content[:200]}")
            
            # Early return if memory is disabled
            if not self.valves.enable_memory:
                self.log("⚠️ Memory disabled, returning body unchanged")
                return body
            
            # Extract messages and query early for both web search and memory processing
            messages = body.get("messages", [])
            if not messages:
                self.log("No messages found in request, returning unchanged")
                return body
            
            # Extract the latest user query
            query = ""
            for msg in reversed(messages):  # Start from most recent
                if msg.get("role") == "user":
                    query = msg.get("content", "")
                    break
            
            # WEB SEARCH PROCESSING (Independent of authentication)
            # This ensures web search works even if memory system fails
            if query and web_search_available:
                try:
                    self.log(f"🔍 Checking web search trigger for query: '{query[:50]}...'")
                    if should_trigger_web_search(query, ""):
                        self.log(f"✅ WEB SEARCH TRIGGERED for query: {query}")
                        
                        # Perform web search with timeout protection
                        try:
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
                        except Exception as search_error:
                            self.log(f"❌ Web search failed: {search_error}", "ERROR")
                    else:
                        self.log(f"❌ Web search NOT triggered for query: '{query[:50]}...'")
                except Exception as trigger_error:
                    self.log(f"❌ Web search trigger check failed: {trigger_error}", "ERROR")
            elif query and not web_search_available:
                # Web search not available - check if user was asking for search
                try:
                    if should_trigger_web_search(query, ""):
                        self.log(f"⚠️ User requested web search but web search is in FALLBACK MODE")
                        self.log(f"⚠️ Query would have triggered search: {query}")
                    else:
                        self.log(f"ℹ️ Query would not have triggered web search: '{query[:50]}...'")
                except Exception as fallback_error:
                    self.log(f"❌ Web search fallback check failed: {fallback_error}", "ERROR")
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
                    self.log(f"✅ Session consistency validated for user {user_id}")
                else:
                    self.log(f"⚠️ Session consistency check failed for user {user_id}")
            
            # Use query already extracted above - no need to re-extract
            if not query:
                self.log("No query found in messages, skipping memory retrieval")
                return body
            
            # Retrieve memories with error handling
            try:
                memories = await self.api_client.get_memories(
                    user_id=user_id,
                    query=query,
                    max_memories=self.valves.max_memories
                )
            except Exception as memory_error:
                self.log(f"❌ Failed to retrieve memories for user {user_id}: {memory_error}", "ERROR")
                memories = []  # Continue with empty memories on error
            
            if not memories:
                # No memories found - inject new user system message
                if self.valves.debug_mode:
                    self.log(f"� No previous memories found for user {user_id} - introducing memory capabilities")
                
                # Always inject enhanced persona, regardless of memory availability
                enhanced_system_message = self.memory_processor.create_system_message("", user_id, 0, body)
                
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
                
                # Enhanced debugging for memory content
                if memories:
                    self.log(f"🔍 First few memories preview:")
                    for i, mem in enumerate(memories[:3]):
                        content_preview = str(mem.get('content', mem.get('text', 'No content')))[:80]
                        self.log(f"   Memory {i+1}: {content_preview}...")
                else:
                    self.log(f"⚠️ NO MEMORIES FOUND for user {user_id} with query: {query[:50]}...")
            
            # Inject memory context silently into system message (no robotic formatting)
            if "messages" in body and memory_context:
                # Add clarification about Swift (financial company vs programming language)
                swift_clarification = ""
                if "swift" in query.lower() and any("apple" in mem.lower() or "programming" in mem.lower() for mem in memory_context.lower().split()):
                    swift_clarification = "\n\nIMPORTANT: The user works at SWIFT (Society for Worldwide Interbank Financial Telecommunication) - the global financial messaging company at https://www.swift.com/ - NOT Apple's Swift programming language."
                
                # Create optimized system message with memory context for model size
                natural_system_message = self.memory_processor.create_system_message(memory_context, user_id, memory_quality_score, body)
                
                # Check if there's already a system message
                existing_system = any(msg.get("role") == "system" for msg in body["messages"])
                
                if existing_system:
                    # Update existing system message with memory context
                    for msg in body["messages"]:
                        if msg.get("role") == "system":
                            # Replace with optimized system message
                            msg["content"] = natural_system_message + swift_clarification
                            break
                else:
                    # Add new system message at the beginning
                    body["messages"].insert(0, {
                        "role": "system",
                        "content": natural_system_message + swift_clarification
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
            
            # Store the interaction with error handling
            try:
                success = await self.api_client.store_interaction(
                    user_id=user_id,
                    user_message=user_message,
                    assistant_message=assistant_message
                )
                
                if success:
                    if self.valves.debug_mode:
                        self.log(f"✅ Conversation saved for user {user_id}")
                else:
                    self.log(f"❌ Failed to save conversation for user {user_id}", "WARNING")
            except Exception as store_error:
                self.log(f"❌ Error storing conversation for user {user_id}: {store_error}", "ERROR")
            
            return body
            
        except Exception as e:
            self.log(f"Error in outlet filter: {e}", "ERROR")
            return body
    
    async def __del__(self):
        """Cleanup when pipeline is destroyed."""
        try:
            if hasattr(self, 'api_client') and self.api_client:
                await self.api_client.close()
                self.log("Pipeline cleanup completed", "INFO")
        except Exception as cleanup_error:
            pipeline_logger.error(f"Cleanup failed: {cleanup_error}")  # Use pipeline logger instead of print
