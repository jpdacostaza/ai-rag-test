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
# Support both Docker (/app) and local development paths
current_dir = os.path.dirname(os.path.abspath(__file__))
pipelines_dir = os.path.dirname(current_dir) if current_dir.endswith('pipelines') else current_dir
project_root = os.path.dirname(pipelines_dir) if not pipelines_dir.endswith('backend') else pipelines_dir

# Add both container and local paths
sys.path.insert(0, '/app/pipelines')  # Docker path
sys.path.insert(0, os.path.join(project_root, 'pipelines'))  # Local path
sys.path.insert(0, project_root)  # Project root for services imports

# Add the backend directory for web search tools
sys.path.insert(0, '/app')

# Add core modules to path
sys.path.insert(0, '/app/core')

# Zero-config auto-dependency installation with robust error handling
def install_dependencies_manually():
    """Fallback dependency installation when auto-installer fails"""
    import subprocess
    import sys
    
    packages_to_install = [
        "pydantic>=2.7.0,<3.0.0",  # Updated for LangChain compatibility
        "wikipedia>=1.4.0",
        "langchain>=0.1.0", 
        "langchain-community>=0.0.13",
        "langchain-openai>=0.0.5",
        "requests>=2.31.0",
        "RestrictedPython>=5.0"
    ]
    
    for package in packages_to_install:
        try:
            result = subprocess.run([
                sys.executable, "-m", "pip", "install", 
                package, "--quiet", "--no-warn-script-location"
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"[MEMORY PIPELINE INFO] Successfully installed: {package}")
            else:
                print(f"[MEMORY PIPELINE WARNING] Failed to install {package}: {result.stderr}")
        except Exception as e:
            print(f"[MEMORY PIPELINE WARNING] Error installing {package}: {e}")

try:
    # Try to import and use the auto-installer
    sys.path.insert(0, '/app/pipelines')
    from _auto_installer import auto_install_dependencies, fix_pydantic_compatibility
    print("[MEMORY PIPELINE INFO] Using _auto_installer for dependency management")
    fix_pydantic_compatibility()  # Fix pydantic version conflicts first
    auto_install_dependencies()
    print("[MEMORY PIPELINE INFO] Auto-installer completed successfully")
except ImportError as import_error:
    print(f"[MEMORY PIPELINE INFO] Auto-installer not available, using fallback installation")
    install_dependencies_manually()
except Exception as e:
    print(f"[MEMORY PIPELINE WARNING] Auto-installer failed, using fallback installation")
    install_dependencies_manually()

# Initialize configuration and imports with proper error handling
config = None
auth_manager = None
web_search_available = False
memory_system_available = False

# Configure and load modules
try:
    # Create a minimal config first
    config = {
        'MEMORY_API_URL': os.getenv('MEMORY_API_URL', 'http://backend-memory-api:5001'),
        'REDIS_HOST': os.getenv('REDIS_HOST', 'redis'),
        'REDIS_PORT': int(os.getenv('REDIS_PORT', '6379')),
        'OLLAMA_BASE_URL': os.getenv('OLLAMA_BASE_URL', 'http://ollama:11434'),
        'CHROMA_HOST': os.getenv('CHROMA_HOST', 'chroma'),
        'CHROMA_PORT': int(os.getenv('CHROMA_PORT', '8000')),
        'API_TIMEOUT': int(os.getenv('API_TIMEOUT', '30')),
        'WEB_SEARCH_TIMEOUT': int(os.getenv('WEB_SEARCH_TIMEOUT', '10'))
    }
    
    # Try to load enhanced config if available
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("backend_config", "/app/config/config.py")
        config_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(config_module)
        enhanced_config = config_module.get_config()
        config.update(enhanced_config)  # Merge with enhanced config
        print("[MEMORY PIPELINE INFO] Backend config loaded successfully")
    except Exception as e:
        print(f"[MEMORY PIPELINE INFO] Using basic config, enhanced config unavailable: {e}")
    
    print("[MEMORY PIPELINE INFO] Using minimal fallback config")
except Exception as e:
    print(f"[MEMORY PIPELINE ERROR] Config initialization failed: {e}")

# Import web search tools with proper fallback and auto-installation
search_web = None
should_trigger_web_search = None
format_web_results_for_chat = None

try:
    # Auto-install missing dependencies for zero-conf setup
    import subprocess
    import sys
    
    def auto_install_package(package_name):
        """Auto-install missing packages for zero-conf setup"""
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package_name, "--quiet"])
            print(f"[MEMORY PIPELINE INFO] Auto-installed missing dependency: {package_name}")
        except Exception as e:
            print(f"[MEMORY PIPELINE WARNING] Failed to auto-install {package_name}: {e}")
    
    # Check and install critical dependencies if missing
    critical_packages = {
        "wikipedia": "wikipedia>=1.4.0",
        "langchain": "langchain>=0.1.0", 
        "langchain-community": "langchain-community>=0.0.13",
        "requests": "requests>=2.31.0"
    }
    
    for package_import, package_spec in critical_packages.items():
        try:
            if package_import == "langchain-community":
                # Special handling for langchain-community import
                from langchain_community.utilities import WikipediaAPIWrapper
            else:
                __import__(package_import.replace("-", "_"))
        except ImportError:
            print(f"[MEMORY PIPELINE INFO] Installing missing dependency: {package_spec}")
            auto_install_package(package_spec)
    
    # Now try importing again after installation
    try:
        import wikipedia
        print("[MEMORY PIPELINE INFO] Wikipedia dependency available")
    except ImportError as e:
        print(f"[MEMORY PIPELINE WARNING] Wikipedia still not available: {e}")
    
    # Try LangChain dependencies (optional for basic functionality)
    langchain_available = False
    try:
        from langchain.tools import Tool
        from langchain_community.utilities import WikipediaAPIWrapper
        print("[MEMORY PIPELINE INFO] LangChain dependencies available")
        langchain_available = True
    except ImportError as e:
        print(f"[MEMORY PIPELINE INFO] LangChain dependencies not available (optional): {e}")
        langchain_available = False
    
    # Try importing web search tools
    sys.path.insert(0, '/app/utilities')
    import importlib.util
    spec = importlib.util.spec_from_file_location("web_search_tool", "/app/utilities/web_search_tool.py")
    web_search_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(web_search_module)
    
    search_web = web_search_module.search_web
    should_trigger_web_search = web_search_module.should_trigger_web_search
    format_web_results_for_chat = web_search_module.format_web_results_for_chat
    web_search_available = True
    print("[MEMORY PIPELINE INFO] Backend web search tools loaded successfully")
except Exception as e:
    print(f"[MEMORY PIPELINE INFO] Web search tools not available: {e}")
    
    # Define fallback functions
    async def search_web(query: str, max_results: int = 3):
        return {"results": [], "status": "fallback_unavailable"}
    
    def should_trigger_web_search(query: str, response: str = ""):
        return False
    
    def format_web_results_for_chat(results):
        return ""
    
    web_search_available = False

# Import memory system components with proper fallback
MemoryValves = None
MemoryAPIClient = None
UserAuthManager = None
MemoryProcessor = None

try:
    # Try importing from the memory_system module (both Docker and local paths)
    from memory_system.config import MemoryValves
    from memory_system.api_client import MemoryAPIClient
    from memory_system.auth import UserAuthManager
    from memory_system.processor import MemoryProcessor
    memory_system_available = True
    print("[MEMORY PIPELINE INFO] Memory system modules imported successfully")
except ImportError as e:
    print(f"[MEMORY PIPELINE INFO] Memory system not available: {e}")
    print("[MEMORY PIPELINE INFO] Attempting direct import from pipeline directory")
    
    try:
        # Try direct imports from current directory structure
        import importlib.util
        
        # Get the current directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        memory_system_dir = os.path.join(current_dir, 'memory_system')
        
        # Import each module directly
        spec = importlib.util.spec_from_file_location("config", os.path.join(memory_system_dir, "config.py"))
        config_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(config_module)
        MemoryValves = config_module.MemoryValves
        
        spec = importlib.util.spec_from_file_location("api_client", os.path.join(memory_system_dir, "api_client.py"))
        api_client_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(api_client_module)
        MemoryAPIClient = api_client_module.MemoryAPIClient
        
        spec = importlib.util.spec_from_file_location("auth", os.path.join(memory_system_dir, "auth.py"))
        auth_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(auth_module)
        UserAuthManager = auth_module.UserAuthManager
        
        spec = importlib.util.spec_from_file_location("processor", os.path.join(memory_system_dir, "processor.py"))
        processor_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(processor_module)
        MemoryProcessor = processor_module.MemoryProcessor
        
        memory_system_available = True
        print("[MEMORY PIPELINE INFO] Memory system modules imported successfully via direct import")
        
    except Exception as direct_import_error:
        print(f"[MEMORY PIPELINE WARNING] Memory system components not available - pipeline running without memory features")
        print(f"[MEMORY PIPELINE DEBUG] Direct import error: {direct_import_error}")
        memory_system_available = False


class Pipeline:
    """Enhanced Memory Pipeline for OpenWebUI (Modular Version)."""
    
    # Class-level configuration for auto-registration
    type = "filter"  # Explicitly define as filter pipeline
    id = "enhanced_memory_pipeline"
    name = "Enhanced Memory Pipeline"
    
    # Create a simple fallback valve class if MemoryValves is not available
    if MemoryValves is None:
        from pydantic import BaseModel
        from typing import List
        
        class Valves(BaseModel):
            """Fallback configuration valves when memory system is not available."""
            model_config = {"protected_namespaces": ()}
            pipelines: List[str] = ["*"]
            priority: int = 0
            backend_url: str = config.get('MEMORY_API_URL', 'http://backend-memory-api:5001') if config else os.getenv('MEMORY_API_URL', 'http://backend-memory-api:5001')
            enable_memory: bool = False  # Disable memory when components not available
            max_memories: int = 100
            memory_threshold: float = 0.001
            quality_threshold: int = 3
            require_authenticated_user: bool = False
            enforce_user_session_consistency: bool = True
            api_timeout: int = config.get('API_TIMEOUT', 30) if config else int(os.getenv('API_TIMEOUT', '30'))
            retry_attempts: int = 3
            debug_mode: bool = True
    else:
        class Valves(MemoryValves):
            """Configuration valves inherited from memory system config."""
            pass
    
    def __init__(self):
        """Initialize the modular memory pipeline."""
        # Set the type and identifiers following best practices
        self.type = "filter"
        self.name = "Enhanced Memory Pipeline"
        
        # Initialize valves with proper configuration
        if memory_system_available and config:
            # Use config values if available
            backend_url = config.get('MEMORY_API_URL', 'http://backend-memory-api:5001')
            api_timeout = config.get('API_TIMEOUT', 30)
        else:
            # Use environment variables as fallback
            backend_url = os.getenv('MEMORY_API_URL', 'http://backend-memory-api:5001')
            api_timeout = int(os.getenv('API_TIMEOUT', '30'))
            
        if memory_system_available:
            self.valves = self.Valves(
                **{
                    "pipelines": ["*"],  # Connect to all pipelines
                    "priority": 0,       # Highest priority
                    "backend_url": backend_url,  # Use config or env variable
                    "enable_memory": True,
                    "api_timeout": api_timeout,  # Use config timeout
                    "debug_mode": True,
                }
            )
        else:
            self.valves = self.Valves(
                **{
                    "pipelines": ["*"],  # Connect to all pipelines
                    "priority": 0,       # Highest priority
                    "backend_url": backend_url,  # Use fallback URL
                    "enable_memory": False,  # Disable memory when components not available
                    "api_timeout": api_timeout,  # Use fallback timeout
                    "debug_mode": True,
                }
            )
        
        # Initialize modular components only if available
        if memory_system_available and all([MemoryAPIClient, UserAuthManager, MemoryProcessor]):
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
        else:
            # Memory system not available - set components to None
            self.api_client = None
            self.auth_manager = None
            self.memory_processor = None
            self.log("Memory system components not available - pipeline running without memory features", "WARNING")
    
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
    
    # Memory service compatibility methods
    # These methods are expected by the memory service for pipeline integration
    
    @property
    def memory_manager(self):
        """Property to provide memory manager compatibility with memory service."""
        return self if memory_system_available and hasattr(self, 'api_client') else None
    
    async def get_relevant_memories(self, user_id: str, query: str = "", limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get relevant memories for a user - memory service compatibility method.
        
        Args:
            user_id: The user ID to get memories for
            query: Optional query to filter memories  
            limit: Maximum number of memories to return
            
        Returns:
            List of memory dictionaries
        """
        try:
            if not memory_system_available or not hasattr(self, 'api_client'):
                self.log("Memory system not available for memory retrieval", "WARNING")
                return []
            
            if not self.valves.enable_memory:
                self.log("Memory disabled, returning empty memories", "WARNING")
                return []
            
            # Use the API client to retrieve memories
            memories = await self.api_client.get_memories(
                user_id=user_id,
                query=query,
                max_memories=limit
            )
            
            if memories:
                self.log(f"Retrieved {len(memories)} memories for user {user_id[:8]}...")
                return memories
            else:
                self.log(f"No memories found for user {user_id[:8]}...")
                return []
                
        except Exception as e:
            self.log(f"Error retrieving memories for user {user_id[:8]}...: {str(e)}", "ERROR")
            return []
    
    async def _get_relevant_memories(self, user_id: str, query: str = "", limit: int = 10) -> List[Dict[str, Any]]:
        """
        Fallback method for memory retrieval - memory service compatibility.
        This is the fallback method that memory service looks for.
        """
        return await self.get_relevant_memories(user_id, query, limit)
    
    async def store_memory(self, user_id: str, content: str, metadata: Dict[str, Any] = None) -> bool:
        """
        Store a memory - memory service compatibility method.
        
        Args:
            user_id: The user ID to store memory for
            content: The memory content
            metadata: Optional metadata dictionary
            
        Returns:
            True if storage was successful, False otherwise
        """
        try:
            if not memory_system_available or not hasattr(self, 'api_client'):
                self.log("Memory system not available for memory storage", "WARNING")
                return False
            
            if not self.valves.enable_memory:
                self.log("Memory disabled, skipping memory storage", "WARNING")
                return False
            
            # Prepare memory data
            memory_data = {
                "user_id": user_id,
                "content": content,
                "metadata": metadata or {}
            }
            
            # Use the API client to store memory
            success = await self.api_client.store_memory(memory_data)
            
            if success:
                self.log(f"Successfully stored memory for user {user_id[:8]}...")
            else:
                self.log(f"Failed to store memory for user {user_id[:8]}...", "ERROR")
            
            return success
            
        except Exception as e:
            self.log(f"Error storing memory for user {user_id[:8]}...: {str(e)}", "ERROR")
            return False

    async def __del__(self):
        """Cleanup when pipeline is destroyed."""
        try:
            if hasattr(self, 'api_client') and self.api_client:
                await self.api_client.close()
                self.log("Pipeline cleanup completed", "INFO")
        except Exception as cleanup_error:
            print(f"[MEMORY PIPELINE ERROR] Cleanup failed: {cleanup_error}")  # Use print since log may not be available
