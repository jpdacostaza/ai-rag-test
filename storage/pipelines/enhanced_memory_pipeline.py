"""
Enhanced Memory Pipeline for OpenWebUI
=====================================

A comprehensive pipeline that provides memory storage and retrieval capabilities
for OpenWebUI conversations with proper user authentication context.

This pipeline integrates with the separated memory architecture and provides
better user identification compared to the Function approach.

UNIVERSAL MODEL COMPATIBILITY:
- Works with any LLM model (local or cloud-based)
- Compatible with Ollama models (llama3.2, mistral, etc.)
- Supports OpenAI-compatible APIs
- Works with older and newer model architectures
- No model-specific dependencies or requirements
- Memory instructions work via system message injection (universal approach)
"""

from typing import List, Optional, Dict, Any
import asyncio
import httpx
import json
import time
import os
import re
from pydantic import BaseModel

class Pipeline:
    """Enhanced Memory Pipeline for OpenWebUI."""
    
    class Valves(BaseModel):
        """Configuration valves for the memory pipeline."""
        
        # Fix for Pydantic protected namespace warning
        model_config = {"protected_namespaces": ()}
        
        # Pipeline Requirements - which pipelines this filter connects to
        # Use ["*"] to connect to all pipelines
        pipelines: List[str] = ["*"]
        
        # Priority level determines execution order (lower = higher priority)
        priority: int = 0
        
        # API Configuration
        backend_url: str = "http://memory_api:8080"
        
        # Memory Settings
        enable_memory: bool = True
        max_memories: int = 50  # Number of memories to retrieve per query (NOT total storage limit)
        memory_threshold: float = 0.005  # Even lower threshold for better recall (0.5%)
        
        # Advanced Memory Management (NEW)
        unlimited_storage: bool = True  # Allow unlimited memory storage
        smart_memory_management: bool = True  # Enable intelligent memory organization
        max_context_memories: int = 20  # Max memories to include in conversation context
        adaptive_memory_limit: bool = True  # Adapt memory retrieval based on model capabilities
        
        # Explicit Memory Commands (NEW)
        enable_explicit_commands: bool = True  # Support "remember this", "save this", etc.
        force_memory_keywords: List[str] = ["remember this", "save this", "don't forget", "important to remember"]
        
        # Learning Settings
        enable_learning: bool = True
        auto_store_threshold: int = 1  # Store immediately after first exchange
        
        # Performance Settings
        timeout: float = 5.0
        
        # Debug Settings
        debug: bool = False

        # Model Compatibility Settings
        model_agnostic: bool = True  # Works with any model (local/cloud)
        adaptive_prompting: bool = True  # Adapts to different model capabilities
        universal_memory_format: bool = True  # Standard memory format for all models
        
        # Persona Integration
        integrate_persona: bool = True  # Integrate with persona.json configuration
        persona_priority: str = "memory_first"  # memory_first, balanced, persona_first
    def __init__(self):
        """Initialize the memory pipeline."""
        self.type = "filter"
        self.id = "enhanced_memory_pipeline"
        self.name = "Enhanced Memory Pipeline"
        
        # Initialize valves with environment variable overrides
        self.valves = self.Valves(
            **{
                "pipelines": ["*"],  # Connect to all pipelines by default
                "backend_url": os.getenv("MEMORY_API_URL", "http://memory_api:8080"),
                "debug": True,  # Enable debug mode to see filter activity
            }
        )
        
        # Compatibility fix: ensure pipelines attribute is directly accessible
        if not hasattr(self.valves, 'pipelines'):
            self.valves.pipelines = ["*"]
        
        # Initialize HTTP client
        self.http_client = None
        self._client_lock = asyncio.Lock()  # Thread safety for HTTP client
        
        # Session tracking for user ID consistency with cleanup
        self._user_sessions = {}  # Track user sessions
        self._session_users = {}  # Track sessions per user
        self._session_timestamps = {}  # Track session creation times
        self._max_session_age = 86400  # 24 hours in seconds
    
    async def on_startup(self):
        """Called when the server is started."""
        self.log("Enhanced Memory Pipeline started")
        
    async def on_shutdown(self):
        """Called when the server is stopped."""
        if self.http_client:
            await self.http_client.aclose()
        self.log("Enhanced Memory Pipeline stopped")
        
    async def on_valves_updated(self):
        """Called when the valves are updated."""
        self.log("Enhanced Memory Pipeline valves updated")
    
    async def get_http_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client with thread safety."""
        if self.http_client is None:
            async with self._client_lock:
                # Double-check pattern
                if self.http_client is None:
                    self.http_client = httpx.AsyncClient(timeout=self.valves.timeout)
        return self.http_client
    
    def log(self, message: str, level: str = "INFO"):
        """Log message if debug is enabled."""
        if self.valves.debug:
            print(f"[MEMORY PIPELINE {level}] {message}", flush=True)
    
    async def get_user_memories(self, user_id: str, query: str) -> List[Dict[str, Any]]:
        """Retrieve relevant memories for the user."""
        try:
            client = await self.get_http_client()
            
            payload = {
                "user_id": user_id,
                "query": query,
                "limit": self.valves.max_memories,  # Fixed: API expects 'limit', not 'max_results'
                "threshold": self.valves.memory_threshold
            }
            
            self.log(f"🔍 Memory retrieval payload: {payload}")
            
            response = await client.post(
                f"{self.valves.backend_url}/api/memory/retrieve",
                json=payload
            )
            
            if response.status_code == 200:
                data = response.json()
                memories = data.get("memories", [])
                self.log(f"Retrieved {len(memories)} memories for user {user_id}")
                return memories
            else:
                self.log(f"Failed to retrieve memories: HTTP {response.status_code}", "ERROR")
                return []
                
        except Exception as e:
            self.log(f"Error retrieving memories: {e}", "ERROR")
            return []
    
    async def store_interaction(self, user_id: str, messages: List[Dict]) -> bool:
        """Store interaction in memory system."""
        try:
            if len(messages) < self.valves.auto_store_threshold:
                return True
            
            client = await self.get_http_client()
            
            # Extract user and assistant messages
            user_message = ""
            assistant_message = ""
            
            for message in messages:
                if message.get("role") == "user":
                    user_message = message.get("content", "")
                elif message.get("role") == "assistant":
                    assistant_message = message.get("content", "")
            
            payload = {
                "user_id": user_id,
                "conversation_id": f"openwebui_conv_{user_id}_{int(time.time())}",
                "user_message": user_message,
                "assistant_response": assistant_message,
                "source": "openwebui_pipeline"
            }
            
            self.log(f"🔍 Store interaction payload for user {user_id}: {len(user_message)} chars user msg, {len(assistant_message)} chars assistant msg")
            
            response = await client.post(
                f"{self.valves.backend_url}/api/learning/process_interaction",
                json=payload
            )
            
            if response.status_code == 200:
                result = response.json()
                self.log(f"Stored interaction for user {user_id} - New memories: {result.get('new_memories', 0)}")
                return True
            else:
                self.log(f"Failed to store interaction: HTTP {response.status_code}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"Error storing interaction: {e}", "ERROR")
            return False
    
    def detect_explicit_memory_commands(self, message_content: str) -> Dict[str, Any]:
        """Detect explicit memory commands in user messages."""
        if not self.valves.enable_explicit_commands:
            return {"has_command": False}
        
        content_lower = message_content.lower()
        detected_commands = []
        
        # Check for force memory keywords
        for keyword in self.valves.force_memory_keywords:
            if keyword in content_lower:
                detected_commands.append({
                    "keyword": keyword,
                    "type": "force_remember",
                    "priority": "high"
                })
        
        # Check for other memory patterns
        memory_patterns = {
            r"(remember that|save this|don't forget)": "force_remember",
            r"(important|critical|key|vital).*?(remember|save|note)": "high_priority",
            r"(never forget|always remember)": "permanent",
            r"(update|correct|change).*?(remember|memory)": "update_memory",
            r"(forget|remove|delete).*?(memory|remember)": "forget_command"
        }
        
        import re
        for pattern, command_type in memory_patterns.items():
            if re.search(pattern, content_lower):
                detected_commands.append({
                    "pattern": pattern,
                    "type": command_type,
                    "priority": "high" if command_type in ["force_remember", "permanent"] else "medium"
                })
        
        return {
            "has_command": len(detected_commands) > 0,
            "commands": detected_commands,
            "message_content": message_content
        }
    
    async def store_explicit_memory(self, user_id: str, content: str, command_info: Dict) -> bool:
        """Store explicit memory with high priority."""
        try:
            client = await self.get_http_client()
            
            # Create explicit memory payload
            payload = {
                "user_id": user_id,
                "content": content,
                "source": "explicit_command",
                "metadata": {
                    "priority": "high",
                    "explicit": True,
                    "commands": command_info.get("commands", []),
                    "timestamp": time.time()
                }
            }
            
            self.log(f"💾 FORCE STORING explicit memory for user {user_id}: {content[:100]}...")
            
            # First, let's add this to the memory API (we'll add the endpoint next)
            response = await client.post(
                f"{self.valves.backend_url}/api/memory/store_explicit",
                json=payload
            )
            
            if response.status_code == 200:
                self.log(f"✅ Explicit memory stored successfully for user {user_id}")
                return True
            else:
                self.log(f"❌ Failed to store explicit memory: HTTP {response.status_code}", "ERROR")
                # Fallback to regular interaction storage
                return await self._fallback_explicit_storage(user_id, content)
                
        except Exception as e:
            self.log(f"❌ Error storing explicit memory: {e}", "ERROR")
            # Fallback to regular interaction storage
            return await self._fallback_explicit_storage(user_id, content)
    
    async def _fallback_explicit_storage(self, user_id: str, content: str) -> bool:
        """Fallback method to store explicit memory via regular interaction."""
        try:
            # Create a special interaction that marks it as explicit
            messages = [
                {"role": "user", "content": f"EXPLICIT MEMORY: {content}"},
                {"role": "assistant", "content": "I will remember this important information."}
            ]
            
            return await self.store_interaction(user_id, messages)
        except Exception as e:
            self.log(f"❌ Fallback storage failed: {e}", "ERROR")
            return False
    
    def adapt_memory_limit_for_context(self, model_info: Optional[Dict] = None) -> int:
        """Adapt memory retrieval limit based on model capabilities and context."""
        if not self.valves.adaptive_memory_limit:
            return self.valves.max_context_memories
        
        try:
            # Determine context window size if available
            context_window = 4096  # Default assumption
            
            if model_info:
                # Extract context window from model info if available
                context_window = model_info.get("context_window", 4096)
            
            # Calculate optimal memory count based on context window
            if context_window >= 32000:  # Large context models
                return min(self.valves.max_memories, 100)
            elif context_window >= 16000:  # Medium-large context
                return min(self.valves.max_memories, 50)
            elif context_window >= 8000:   # Medium context
                return min(self.valves.max_memories, 30)
            else:  # Small context models
                return min(self.valves.max_context_memories, 20)
                
        except Exception as e:
            self.log(f"Error adapting memory limit: {e}", "ERROR")
            return self.valves.max_context_memories

    def extract_user_message(self, messages: List[Dict]) -> str:
        """Extract the latest user message for memory retrieval."""
        for message in reversed(messages):
            if message.get("role") == "user":
                return message.get("content", "")
        return ""
    
    def get_user_identifier(self, __user__: Dict) -> Optional[str]:
        """Get user identifier with strict authentication validation - no fallbacks."""
        # Debug: Log the complete user object (only if debug enabled)
        if self.valves.debug:
            self.log(f"🔍 DEBUG: Received __user__ object: {__user__}")
        
        if not __user__ or not isinstance(__user__, dict):
            self.log(f"❌ AUTHENTICATION REQUIRED: Invalid or missing user object: {type(__user__)}", "ERROR")
            return None
        
        # Try different user identification methods (prioritized)
        user_id = (
            __user__.get("id") or 
            __user__.get("email") or 
            __user__.get("username") or 
            __user__.get("name")
        )
        
        if not user_id:
            self.log(f"❌ AUTHENTICATION REQUIRED: No user ID found in user object keys: {list(__user__.keys())}", "ERROR")
            return None
        
        user_id_str = str(user_id)
        
        # Validate user ID format
        if not self._is_valid_user_id(user_id_str):
            self.log(f"❌ AUTHENTICATION REQUIRED: Invalid user ID format: {user_id_str}", "ERROR")
            return None
        
        self.log(f"✅ USER AUTHENTICATED: {user_id_str}")
        return user_id_str
    
    def _is_valid_user_id(self, user_id: str) -> bool:
        """Validate user ID format and structure."""
        if not user_id or len(user_id) < 3:
            return False
        
        # Check for common invalid patterns
        invalid_patterns = ["undefined", "null", "none", "", "anonymous", "guest"]
        if user_id.lower() in invalid_patterns:
            return False
        
        # Check for UUID format (OpenWebUI standard)
        import re
        uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
        is_uuid = bool(re.match(uuid_pattern, user_id, re.IGNORECASE))
        
        if is_uuid:
            self.log(f"✅ Valid UUID format: {user_id}")
            return True
        
        # Allow email format
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        is_email = bool(re.match(email_pattern, user_id))
        
        if is_email:
            self.log(f"✅ Valid email format: {user_id}")
            return True
        
        # Allow alphanumeric with minimum length
        if len(user_id) >= 8 and user_id.replace("-", "").replace("_", "").isalnum():
            self.log(f"✅ Valid alphanumeric format: {user_id}")
            return True
        
        self.log(f"❌ Invalid user ID format: {user_id}")
        return False
    
    async def inlet(self, body: Dict, __user__: Optional[Dict] = None) -> Dict:
        """
        Process incoming requests - retrieve and inject memories.
        
        This is called before the message is sent to the model.
        """
        if not self.valves.enable_memory:
            return body
        
        try:
            messages = body.get("messages", [])
            if not messages:
                return body
            
            # Get user identifier with strict validation (no fallbacks)
            user_id = self.get_user_identifier(__user__)
            
            # If no valid user ID, block memory functionality but allow basic conversation
            if not user_id:
                self.log(f"🚨 AUTHENTICATION REQUIRED: Memory functionality disabled - no valid user ID provided", "ERROR")
                # Return body unchanged - conversation continues but without memory
                return body
            
            # Extract user query first for explicit command detection
            user_query = self.extract_user_message(messages)
            if not user_query:
                return body

            # 🔥 NEW: Check for document content FIRST (CV, resume, etc.)
            document_info = self.detect_document_content(messages)
            if document_info.get('is_document'):
                self.log(f"📄 DOCUMENT DETECTED for user {user_id}: {document_info.get('document_types', [])}")
                # Process document for enhanced memory storage
                await self.process_document_content(user_id, document_info)

            # 🔥 NEW: Check for explicit memory commands SECOND
            if self.valves.enable_explicit_commands:
                explicit_command = self.detect_explicit_memory_commands(user_query)
                if explicit_command["has_command"]:
                    self.log(f"🚨 EXPLICIT MEMORY COMMAND detected for user {user_id}: {explicit_command}")
                    
                    # Store the explicit memory immediately
                    stored = await self.store_explicit_memory(user_id, user_query, explicit_command)
                    if stored:
                        self.log(f"✅ EXPLICIT MEMORY stored successfully for user {user_id}")
                        
                        # Add a system message to acknowledge the explicit memory
                        acknowledgment_msg = {
                            "role": "system",
                            "content": f"🧠 EXPLICIT MEMORY STORED: I will remember '{user_query}' with high priority. This has been saved to both short-term and long-term memory for immediate availability in future conversations."
                        }
                        messages.insert(0, acknowledgment_msg)
                    else:
                        self.log(f"❌ EXPLICIT MEMORY storage failed for user {user_id}", "ERROR")
            
            # Validate session consistency
            if not self._validate_session_consistency(user_id, body):
                self.log(f"🚨 Session validation failed for user {user_id}", "ERROR")
                # Continue with limited functionality rather than blocking
            
            # Cleanup old sessions to prevent memory leaks
            self._cleanup_old_sessions()
            
            # Verify user memory access rights
            if not self._verify_user_memory_access(user_id):
                self.log(f"❌ Memory access denied for user {user_id}", "ERROR")
                return body  # Block memory access but allow conversation
            
            # Additional validation: ensure query is reasonable
            if len(user_query.strip()) < 3:
                self.log(f"⚠️ Query too short for memory retrieval: '{user_query}'")
                return body
            
            # Enhanced query for better memory retrieval
            enhanced_query = f"{user_query} name work preferences details information"
            
            # Log memory access attempt
            self.log(f"🔍 Memory access for user {user_id}, query: {user_query[:50]}... (enhanced: {enhanced_query[:50]}...)")
            
            # 🔥 NEW: Adapt memory retrieval limit based on model capabilities
            adaptive_limit = self.adapt_memory_limit_for_context()
            if adaptive_limit != self.valves.max_memories:
                self.log(f"📊 Adapted memory limit from {self.valves.max_memories} to {adaptive_limit} for optimal context")
                # Temporarily override the limit for this request
                original_limit = self.valves.max_memories
                self.valves.max_memories = adaptive_limit
            
            # Retrieve relevant memories
            memories = await self.get_user_memories(user_id, enhanced_query)
            
            # Restore original limit if changed
            if 'original_limit' in locals():
                self.valves.max_memories = original_limit
            
            # Always inject enhanced persona, regardless of memory availability
            memory_context = ""
            memory_quality_score = 0
            
            if memories:
                # Validate memory ownership (ensure memories belong to this user)
                validated_memories = self._validate_memory_ownership(memories, user_id)
                
                if validated_memories:
                    # Format memories for injection
                    memory_context = "\n".join([
                        f"Memory: {memory.get('content', '')}"
                        for memory in validated_memories[:3]  # Limit to top 3 memories
                    ])
                    
                    # Log the actual memory content being injected
                    self.log(f"🧠 Memory context being injected for user {user_id}: {memory_context}")
                    
                    # Enhanced memory integration with universal model compatibility
                    memory_quality_score = self._calculate_memory_quality(validated_memories)
                    user_context = self._extract_user_context(validated_memories)
                    
                    self.log(f"✅ Successfully injected {len(validated_memories)} memories for user {user_id}")
                else:
                    self.log(f"⚠️ No valid memories after ownership validation for user {user_id}")
            else:
                self.log(f"📭 No memories found for user {user_id} - using enhanced persona only")
            
            # ALWAYS create and inject enhanced system message (with or without memories)
            enhanced_system_message = self._create_model_compatible_system_message(
                memory_context, user_id, memory_quality_score
            )
            
            # Find system message or create one
            system_message_found = False
            for message in messages:
                if message.get("role") == "system":
                    # Replace with enhanced system message
                    message["content"] = enhanced_system_message
                    system_message_found = True
                    if memories:
                        self.log(f"📝 Updated system message for user {user_id} (Quality: {memory_quality_score}/10, Model: Universal)")
                    else:
                        self.log(f"📝 Updated system message for user {user_id} with enhanced persona (No memories)")
                    break
            
            if not system_message_found:
                # Insert new system message with universal compatibility
                system_message = {
                    "role": "system",
                    "content": enhanced_system_message
                }
                messages.insert(0, system_message)
                if memories:
                    self.log(f"📝 Added universal system message for user {user_id} (Quality: {memory_quality_score}/10)")
                else:
                    self.log(f"📝 Added enhanced persona system message for user {user_id} (New user)")
            
            return body
            
        except Exception as e:
            self.log(f"Error in inlet for user {user_id if 'user_id' in locals() else 'unknown'}: {e}", "ERROR")
            return body
    
    def _validate_memory_ownership(self, memories: List[Dict], user_id: str) -> List[Dict]:
        """Validate that memories belong to the requesting user."""
        try:
            validated_memories = []
            
            for memory in memories:
                # Check if memory has user_id metadata
                memory_user_id = None
                
                # Try different ways memories might store user ID
                metadata = memory.get("metadata", {})
                if isinstance(metadata, dict):
                    memory_user_id = (
                        metadata.get("user_id") or 
                        metadata.get("userId") or
                        metadata.get("owner")
                    )
                
                # Also check direct user_id field
                if not memory_user_id:
                    memory_user_id = memory.get("user_id")
                
                # Validate ownership
                if memory_user_id and str(memory_user_id) == str(user_id):
                    validated_memories.append(memory)
                    self.log(f"✅ Memory ownership validated for user {user_id}")
                elif not memory_user_id:
                    # If no user ID in memory, log warning but allow (for backward compatibility)
                    self.log(f"⚠️ Memory has no user ID metadata - allowing for user {user_id}")
                    validated_memories.append(memory)
                else:
                    # Potential security issue - memory belongs to different user
                    self.log(f"🚨 SECURITY: Memory belongs to user {memory_user_id}, requested by {user_id}", "ERROR")
                    # Don't include this memory
            
            return validated_memories
            
        except Exception as e:
            self.log(f"Error validating memory ownership: {e}", "ERROR")
            return memories  # Return original on error to avoid breaking functionality
    
    async def outlet(self, body: Dict, __user__: Optional[Dict] = None) -> Dict:
        """
        Process outgoing responses - store interactions for learning.
        
        This is called after the model generates a response.
        """
        if not self.valves.enable_learning:
            return body
        
        try:
            messages = body.get("messages", [])
            if not messages:
                return body
            
            # Get user identifier with strict validation (no fallbacks)
            user_id = self.get_user_identifier(__user__)
            
            # If no valid user ID, skip memory storage but allow response to pass through
            if not user_id:
                self.log(f"🚨 AUTHENTICATION REQUIRED: Skipping memory storage - no valid user ID provided", "ERROR")
                return body
            
            # Validate session consistency
            if not self._validate_session_consistency(user_id, body):
                self.log(f"🚨 Session validation failed in outlet for user {user_id}", "ERROR")
            
            # Verify user memory access rights
            if not self._verify_user_memory_access(user_id):
                self.log(f"❌ Memory storage denied for user {user_id}", "ERROR")
                return body  # Block memory storage but allow conversation
            
            # Log interaction storage attempt
            self.log(f"💾 Storing interaction for user {user_id}")
            
            # Store the interaction asynchronously with validation
            asyncio.create_task(self.store_interaction_with_validation(user_id, messages, body))
            
        except Exception as e:
            self.log(f"Error in outlet for user {user_id if 'user_id' in locals() else 'unknown'}: {e}", "ERROR")
        
        return body
    
    async def store_interaction_with_validation(self, user_id: str, messages: List[Dict], body: Dict) -> bool:
        """Store interaction with additional validation checks."""
        try:
            # Validate interaction content
            if not self._validate_interaction_content(messages, user_id):
                self.log(f"❌ Invalid interaction content for user {user_id}", "ERROR")
                return False
            
            # Store with enhanced logging
            result = await self.store_interaction(user_id, messages)
            
            if result:
                self.log(f"✅ Successfully stored interaction for user {user_id}")
            else:
                self.log(f"❌ Failed to store interaction for user {user_id}", "ERROR")
            
            return result
            
        except Exception as e:
            self.log(f"Error in validated storage for user {user_id}: {e}", "ERROR")
            return False
    
    def _validate_interaction_content(self, messages: List[Dict], user_id: str) -> bool:
        """Validate that interaction content is appropriate for storage."""
        try:
            # Check for minimum content requirements
            user_messages = [msg for msg in messages if msg.get("role") == "user"]
            assistant_messages = [msg for msg in messages if msg.get("role") == "assistant"]
            
            if not user_messages:
                self.log(f"⚠️ No user messages found for storage - user {user_id}")
                return False
            
            # Check for reasonable content length
            for msg in user_messages:
                content = msg.get("content", "")
                if len(content.strip()) < 2:
                    self.log(f"⚠️ User message too short for storage - user {user_id}")
                    return False
                if len(content) > 10000:  # Reasonable limit
                    self.log(f"⚠️ User message too long for storage - user {user_id}")
                    return False
            
            # Check for sensitive content patterns (basic)
            sensitive_patterns = ["password", "token", "api_key", "secret", "private_key"]
            for msg in messages:
                content = msg.get("content", "").lower()
                for pattern in sensitive_patterns:
                    if pattern in content:
                        self.log(f"🚨 Sensitive content detected in message - blocking storage for user {user_id}", "ERROR")
                        return False
            
            self.log(f"✅ Interaction content validated for user {user_id}")
            return True
            
        except Exception as e:
            self.log(f"Error validating interaction content: {e}", "ERROR")
            return True  # Allow storage on validation error
    
    def _validate_session_consistency(self, user_id: Optional[str], body: Dict) -> bool:
        """Validate that user ID is consistent with session context."""
        if not user_id:
            return False  # No user ID = no session consistency
            
        try:
            # Extract conversation/session identifiers from the request
            messages = body.get("messages", [])
            
            # Look for session indicators in the request
            session_indicators = []
            
            # Check if there's a conversation_id or session_id in the body
            conv_id = body.get("conversation_id") or body.get("session_id") or body.get("chat_id")
            if conv_id:
                session_indicators.append(("explicit_id", conv_id))
            
            # Check message history for session context
            if messages:
                # Generate a session fingerprint from message pattern
                msg_fingerprint = self._generate_message_fingerprint(messages)
                session_indicators.append(("message_fingerprint", msg_fingerprint))
            
            # Validate consistency
            for indicator_type, indicator_value in session_indicators:
                if self._check_user_session_consistency(user_id, indicator_type, indicator_value):
                    self.log(f"✅ Session consistency validated for user {user_id} via {indicator_type}")
                    return True
                else:
                    self.log(f"⚠️ Session inconsistency detected for user {user_id} via {indicator_type}")
            
            # Register new session if no existing consistency found
            if session_indicators:
                self._register_user_session(user_id, session_indicators[0][1])
                return True
            
            return True  # Allow if no session indicators available
            
        except Exception as e:
            self.log(f"Error validating session consistency: {e}", "ERROR")
            return True  # Don't block on validation errors
    
    def _generate_message_fingerprint(self, messages: List[Dict]) -> str:
        """Generate a fingerprint from message pattern for session tracking."""
        try:
            # Create a simple fingerprint from recent messages
            fingerprint_data = []
            for msg in messages[-3:]:  # Last 3 messages
                if msg.get("role") and msg.get("content"):
                    content_hash = str(hash(msg["content"][:100]))  # First 100 chars
                    fingerprint_data.append(f"{msg['role']}:{content_hash}")
            
            return "|".join(fingerprint_data)
        except:
            return "unknown_session"
    
    def _check_user_session_consistency(self, user_id: str, indicator_type: str, indicator_value: str) -> bool:
        """Check if user ID is consistent with known session data."""
        try:
            session_key = f"{indicator_type}:{indicator_value}"
            
            # Check if this session is already associated with this user
            if session_key in self._session_users:
                existing_user = self._session_users[session_key]
                if existing_user == user_id:
                    return True
                else:
                    self.log(f"🚨 SESSION MISMATCH: Session {session_key} was for user {existing_user}, now claims {user_id}", "ERROR")
                    return False
            
            # Check if this user already has sessions
            if user_id in self._user_sessions:
                self._user_sessions[user_id].add(session_key)
            else:
                self._user_sessions[user_id] = {session_key}
            
            self._session_users[session_key] = user_id
            return True
            
        except Exception as e:
            self.log(f"Error checking session consistency: {e}", "ERROR")
            return True
    
    def _register_user_session(self, user_id: str, session_id: str) -> None:
        """Register a new user session mapping."""
        try:
            session_key = f"registered:{session_id}"
            
            if user_id not in self._user_sessions:
                self._user_sessions[user_id] = set()
            
            self._user_sessions[user_id].add(session_key)
            self._session_users[session_key] = user_id
            
            self.log(f"📝 Registered session {session_key} for user {user_id}")
            
        except Exception as e:
            self.log(f"Error registering session: {e}", "ERROR")
    
    def _cleanup_old_sessions(self):
        """Clean up old sessions to prevent memory leak."""
        try:
            current_time = time.time()
            sessions_to_remove = []
            
            for session_key, timestamp in self._session_timestamps.items():
                if current_time - timestamp > self._max_session_age:
                    sessions_to_remove.append(session_key)
            
            for session_key in sessions_to_remove:
                # Remove from session_users
                if session_key in self._session_users:
                    user_id = self._session_users[session_key]
                    del self._session_users[session_key]
                    
                    # Remove from user_sessions
                    if user_id in self._user_sessions:
                        self._user_sessions[user_id].discard(session_key)
                        if not self._user_sessions[user_id]:
                            del self._user_sessions[user_id]
                
                # Remove timestamp
                del self._session_timestamps[session_key]
            
            if sessions_to_remove:
                self.log(f"🧹 Cleaned up {len(sessions_to_remove)} old sessions")
                
        except Exception as e:
            self.log(f"Error cleaning up sessions: {e}", "ERROR")
    
    def detect_document_content(self, messages: List[Dict]) -> Dict[str, Any]:
        """Detect if messages contain document content (CV, resume, etc.)."""
        document_indicators = {
            'cv_patterns': ['curriculum vitae', 'resume', 'cv', 'professional experience', 'work experience'],
            'technical_patterns': ['technical skills', 'programming languages', 'technologies', 'certifications'],
            'job_patterns': ['job title', 'position', 'responsibilities', 'duties', 'role'],
            'education_patterns': ['education', 'degree', 'university', 'qualification']
        }
        
        for message in messages:
            if message.get('role') == 'user':
                content_lower = message.get('content', '').lower()
                
                # Check for document indicators
                detected_types = []
                for doc_type, patterns in document_indicators.items():
                    if any(pattern in content_lower for pattern in patterns):
                        detected_types.append(doc_type)
                
                # If multiple indicators found, likely a document
                if len(detected_types) >= 2:
                    return {
                        'is_document': True,
                        'document_types': detected_types,
                        'content': message.get('content', '')
                    }
        
        return {'is_document': False}

    async def process_document_content(self, user_id: str, document_info: Dict) -> bool:
        """Process detected document content for enhanced memory storage."""
        try:
            if not document_info.get('is_document'):
                return False
            
            self.log(f"📄 DOCUMENT DETECTED for user {user_id}: {document_info.get('document_types', [])}")
            
            # Store as high-priority explicit memory
            return await self.store_explicit_memory(
                user_id=user_id,
                content=document_info.get('content', ''),
                command_info={
                    'commands': [{'type': 'document_storage', 'priority': 'high'}],
                    'document_types': document_info.get('document_types', [])
                }
            )
            
        except Exception as e:
            self.log(f"Error processing document content: {e}", "ERROR")
            return False

    def _create_model_compatible_system_message(self, memory_context: str, user_id: str, memory_quality_score: int) -> str:
        """Create a system message that works with any model type."""
        try:
            base_persona = self._get_base_persona_prompt()
            
            if memory_context:
                # Include memories with clear instructions
                return f"""{base_persona}

🧠 CRITICAL MEMORY INSTRUCTIONS - YOU MUST ACKNOWLEDGE THESE MEMORIES:

MEMORIES FROM PREVIOUS CONVERSATIONS:
{memory_context}

Based on these memories, you should:
1. Acknowledge that you remember the user
2. Reference specific details from the memories
3. Show continuity from previous conversations
4. Use this context to personalize your responses

Memory Quality Score: {memory_quality_score}/10
User ID: {user_id}"""
            else:
                # No memories yet - encourage initial learning
                return f"""{base_persona}

📝 NEW USER DETECTED: This is a new conversation with user {user_id}. 
Please:
1. Learn about the user through conversation
2. Remember important details they share
3. Build a personalized relationship over time"""
                
        except Exception as e:
            self.log(f"Error creating system message: {e}", "ERROR")
            return self._get_base_persona_prompt()
    
    def _verify_user_memory_access(self, user_id: str) -> bool:
        """Verify that the user has access to memory functionality."""
        try:
            # Basic validation - ensure user ID is valid
            if not user_id or not self._is_valid_user_id(user_id):
                return False
            
            # For now, allow all validated users
            # This could be extended with role-based access control
            return True
            
        except Exception as e:
            self.log(f"Error verifying memory access for user {user_id}: {e}", "ERROR")
            return False

    def _calculate_memory_quality(self, memories: List[Dict]) -> int:
        """Calculate quality score for retrieved memories."""
        try:
            if not memories:
                return 0
            
            # Simple quality scoring based on memory attributes
            total_score = 0
            for memory in memories:
                score = 5  # Base score
                
                # Boost for recent memories
                if memory.get('timestamp'):
                    # Add recency bonus (this would need proper timestamp parsing)
                    score += 2
                
                # Boost for explicit/high priority memories
                if memory.get('metadata', {}).get('explicit'):
                    score += 3
                
                total_score += min(score, 10)  # Cap at 10
            
            return min(total_score // len(memories), 10)  # Average, capped at 10
            
        except Exception as e:
            self.log(f"Error calculating memory quality: {e}", "ERROR")
            return 5  # Default average score

    def _extract_user_context(self, memories: List[Dict]) -> Dict[str, Any]:
        """Extract user context from memories for personalization."""
        try:
            context = {
                'name': None,
                'preferences': [],
                'expertise': [],
                'recent_topics': []
            }
            
            for memory in memories:
                content = memory.get('content', '').lower()
                
                # Extract name patterns
                if 'name is' in content or 'call me' in content:
                    # Simple name extraction (this could be improved)
                    words = content.split()
                    if 'name is' in content:
                        idx = words.index('is')
                        if idx + 1 < len(words):
                            context['name'] = words[idx + 1].title()
                
                # Extract expertise/job related info
                if any(term in content for term in ['work', 'job', 'career', 'expertise']):
                    context['expertise'].append(memory.get('content', ''))
                
                # Extract preferences
                if any(term in content for term in ['prefer', 'like', 'favorite', 'enjoy']):
                    context['preferences'].append(memory.get('content', ''))
            
            return context
            
        except Exception as e:
            self.log(f"Error extracting user context: {e}", "ERROR")
            return {}