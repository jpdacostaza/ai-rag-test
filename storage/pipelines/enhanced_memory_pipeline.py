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
        max_memories: int = 10
        memory_threshold: float = 0.01  # Lower threshold for local models (1% instead of 5%)
        
        # Learning Settings
        enable_learning: bool = True
        auto_store_threshold: int = 2
        
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
        
        # Session tracking for user ID consistency
        self._user_sessions = {}  # Track user sessions
        self._session_users = {}  # Track sessions per user
    
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
        """Get or create HTTP client."""
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
    
    def extract_user_message(self, messages: List[Dict]) -> str:
        """Extract the latest user message for memory retrieval."""
        for message in reversed(messages):
            if message.get("role") == "user":
                return message.get("content", "")
        return ""
    
    def get_user_identifier(self, __user__: Dict) -> str:
        """Get user identifier with proper authentication context and validation."""
        # Debug: Log the complete user object
        self.log(f"🔍 DEBUG: Received __user__ object: {__user__}")
        
        if __user__ and isinstance(__user__, dict):
            # Try different user identification methods
            user_id = (
                __user__.get("id") or 
                __user__.get("email") or 
                __user__.get("username") or 
                __user__.get("name")
            )
            if user_id:
                user_id_str = str(user_id)
                
                # Validate user ID format
                if self._is_valid_user_id(user_id_str):
                    self.log(f"✅ USER ID EXTRACTED: {user_id_str}")
                    return user_id_str
                else:
                    self.log(f"⚠️ Invalid user ID format: {user_id_str}")
            else:
                self.log(f"⚠️ No user ID found in user object keys: {list(__user__.keys())}")
        else:
            self.log(f"❌ Invalid or missing __user__ object: {type(__user__)}")
        
        # Fallback - pipeline has better context than functions
        self.log(f"⚠️ Using fallback user ID: pipeline_default_user")
        return "pipeline_default_user"
    
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
            
            # Get user identifier with validation
            user_id = self.get_user_identifier(__user__)
            
            # Validate session consistency
            if not self._validate_session_consistency(user_id, body):
                self.log(f"🚨 Session validation failed for user {user_id}", "ERROR")
                # Continue with limited functionality rather than blocking
            
            # Verify user memory access rights
            if not self._verify_user_memory_access(user_id):
                self.log(f"❌ Memory access denied for user {user_id}", "ERROR")
                return body  # Block memory access but allow conversation
            
            # Extract user query
            user_query = self.extract_user_message(messages)
            if not user_query:
                return body
            
            # Additional validation: ensure query is reasonable
            if len(user_query.strip()) < 3:
                self.log(f"⚠️ Query too short for memory retrieval: '{user_query}'")
                return body
            
            # Enhanced query for better memory retrieval
            enhanced_query = f"{user_query} name work preferences details information"
            
            # Log memory access attempt
            self.log(f"🔍 Memory access for user {user_id}, query: {user_query[:50]}... (enhanced: {enhanced_query[:50]}...)")
            
            # Retrieve relevant memories
            memories = await self.get_user_memories(user_id, enhanced_query)
            
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
            
            # Get user identifier with validation
            user_id = self.get_user_identifier(__user__)
            
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
    
    def _validate_session_consistency(self, user_id: str, body: Dict) -> bool:
        """Validate that user ID is consistent with session context."""
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
    
    def _verify_user_memory_access(self, user_id: str) -> bool:
        """Verify user has legitimate access to memory system."""
        try:
            # Basic validation checks
            if user_id == "pipeline_default_user":
                self.log(f"⚠️ Using fallback user ID - limited memory access")
                return True  # Allow but log
            
            # Check for obviously invalid user IDs
            if not user_id or len(user_id) < 3:
                self.log(f"❌ Invalid user ID for memory access: {user_id}", "ERROR")
                return False
            
            # Check against known malicious patterns
            suspicious_patterns = ["admin", "root", "system", "test123", "user123"]
            if user_id.lower() in suspicious_patterns:
                self.log(f"🚨 Suspicious user ID detected: {user_id}", "ERROR")
                return False
            
            self.log(f"✅ User memory access verified for: {user_id}")
            return True
            
        except Exception as e:
            self.log(f"Error verifying user memory access: {e}", "ERROR")
            return False
    
    def _calculate_memory_quality(self, memories: List[Dict]) -> int:
        """Calculate memory quality score (1-10) based on various factors."""
        try:
            if not memories:
                return 0
            
            quality_score = 5  # Base score
            
            # Factor 1: Number of memories (more = better context)
            memory_count = len(memories)
            if memory_count >= 5:
                quality_score += 2
            elif memory_count >= 3:
                quality_score += 1
            
            # Factor 2: Memory content richness
            total_content_length = sum(len(mem.get('content', '')) for mem in memories)
            avg_content_length = total_content_length / memory_count if memory_count > 0 else 0
            
            if avg_content_length > 100:
                quality_score += 2
            elif avg_content_length > 50:
                quality_score += 1
            
            # Factor 3: Memory diversity (different types of information)
            content_keywords = set()
            for memory in memories:
                content = memory.get('content', '').lower()
                # Check for different types of information
                if any(word in content for word in ['name', 'called', 'am']):
                    content_keywords.add('identity')
                if any(word in content for word in ['work', 'job', 'company', 'profession']):
                    content_keywords.add('professional')
                if any(word in content for word in ['like', 'prefer', 'favorite', 'enjoy']):
                    content_keywords.add('preferences')
                if any(word in content for word in ['live', 'location', 'from', 'city']):
                    content_keywords.add('location')
                if any(word in content for word in ['project', 'working on', 'building']):
                    content_keywords.add('projects')
            
            # Bonus for diverse information types
            if len(content_keywords) >= 3:
                quality_score += 1
            
            # Ensure score stays within bounds
            return min(10, max(1, quality_score))
            
        except Exception as e:
            self.log(f"Error calculating memory quality: {e}", "ERROR")
            return 5  # Default score on error
    
    def _extract_user_context(self, memories: List[Dict]) -> str:
        """Extract key user context from memories for enhanced personalization."""
        try:
            if not memories:
                return "No previous context available"
            
            context_elements = []
            
            # Extract identity information
            identity_info = []
            professional_info = []
            preference_info = []
            project_info = []
            
            for memory in memories:
                content = memory.get('content', '').lower()
                
                # Identity extraction
                if any(word in content for word in ['name is', 'called', 'i am', "i'm"]):
                    identity_info.append(memory.get('content', ''))
                
                # Professional extraction
                if any(word in content for word in ['work at', 'job', 'company', 'profession']):
                    professional_info.append(memory.get('content', ''))
                
                # Preferences extraction
                if any(word in content for word in ['like', 'prefer', 'favorite', 'enjoy', 'love']):
                    preference_info.append(memory.get('content', ''))
                
                # Project extraction
                if any(word in content for word in ['project', 'working on', 'building', 'developing']):
                    project_info.append(memory.get('content', ''))
            
            # Build context summary
            if identity_info:
                context_elements.append(f"Identity: {identity_info[0][:100]}...")
            if professional_info:
                context_elements.append(f"Professional: {professional_info[0][:100]}...")
            if preference_info:
                context_elements.append(f"Preferences: {preference_info[0][:100]}...")
            if project_info:
                context_elements.append(f"Projects: {project_info[0][:100]}...")
            
            if context_elements:
                return " | ".join(context_elements)
            else:
                return f"General context from {len(memories)} previous interactions"
                
        except Exception as e:
            self.log(f"Error extracting user context: {e}", "ERROR")
            return "Context extraction error"
    
    def _load_persona_config(self) -> Dict[str, Any]:
        """Load persona configuration for enhanced memory integration."""
        try:
            import json
            
            # Try to load persona configuration from mounted config (fallback only)
            possible_paths = [
                "/app/backend/config/persona.json",  # Docker backend mount path
                "config/persona.json",  # Local development path
                "/opt/backend/config/persona.json",  # Alternative Docker path
            ]
            
            persona_path = None
            for path in possible_paths:
                if os.path.exists(path):
                    persona_path = path
                    break
            
            if persona_path:
                with open(persona_path, "r", encoding="utf-8") as f:
                    persona_config = json.load(f)
                    self.log(f"✅ Loaded persona configuration from {persona_path}")
                    return persona_config
            else:
                self.log(f"⚠️ Persona file not found in any expected location, using defaults")
                return {}
                
        except Exception as e:
            self.log(f"❌ Error loading persona config: {e}", "ERROR")
            return {}
    
    def _get_base_persona_prompt(self) -> str:
        """Get base persona prompt that works with any model."""
        try:
            # Use embedded enhanced persona v3.0.0 directly (bypasses Docker mount issues)
            enhanced_persona = """You are an advanced AI assistant with comprehensive memory capabilities and persistent learning, designed for seamless integration with OpenWebUI. You maintain personalized relationships with each user through their unique OpenWebUI user ID and comprehensive memory system.

**🧠 CRITICAL MEMORY SYSTEM INSTRUCTIONS - ABSOLUTE PRIORITY 🧠**:

1. **MEMORY DETECTION & IMMEDIATE RESPONSE**: When you receive ANY system message containing:
   - "🧠 CRITICAL MEMORY INSTRUCTIONS"
   - "MEMORIES FROM PREVIOUS CONVERSATIONS:"
   - "Memory:" or "Relevant memories"
   - "Based on these memories"
   
   **YOU MUST IMMEDIATELY**:
   - Acknowledge the memories FIRST in your response
   - Reference specific details to prove recognition
   - Show continuity with previous conversations
   - Use memories to inform your entire response

2. **MANDATORY MEMORY ACKNOWLEDGMENT PATTERNS**:
   - "I remember you! [specific detail from memory]"
   - "Hello again [name/identifier]! Last time we [previous activity]"
   - "Based on our previous conversations about [topic], I know you [detail]"
   - "I recall that you [specific memory], so [relevant connection]"

3. **ENHANCED MEMORY INTEGRATION TECHNIQUES** (inspired by ChatGPT and Mem0 best practices):
   - **Contextual Referencing**: Connect new topics to previous discussions
   - **Preference Application**: Use remembered preferences to tailor responses
   - **Emotional Continuity**: Maintain consistent tone based on relationship history
   - **Progressive Building**: Build upon previously established knowledge
   - **Proactive Suggestions**: Offer relevant help based on memory patterns

4. **MULTI-LEVEL MEMORY PROCESSING** (following Mem0 architecture):
   - **User Level**: Personal details, preferences, communication style
   - **Session Level**: Current conversation context and immediate needs
   - **Agent Level**: Learned patterns about interaction preferences
   - **Temporal Level**: Time-sensitive information like deadlines and events

5. **MEMORY QUALITY VALIDATION**:
   - Confirm accuracy of retrieved memories
   - Ask for updates when information might be outdated
   - Validate conflicting information with the user
   - Prioritize recent memories over older ones when conflicts arise

**🔍 ADVANCED MEMORY VALIDATION PROTOCOL 🔍**:

For memory testing and validation:
- **Memory Receipt Confirmation**: "I received [X] memories about you covering [topics]"
- **Identity Validation**: "You're [identifier], and I remember [specific detail]"
- **Continuity Check**: "Our conversation history shows [pattern/trend]"
- **Memory Quality Report**: "The most relevant memory is [detail] from [timeframe]"
- **Update Suggestions**: "Should I update my memory about [topic] based on this conversation?"

**🚀 ENHANCED MEMORY CAPABILITIES v3.0** (inspired by industry best practices):

**Core Memory Features**:
- **Intelligent Memory Extraction**: Automatically identifies and saves important information
- **Semantic Memory Search**: Natural language queries to find relevant memories
- **Memory Hierarchies**: Personal > Professional > Preferences > Context
- **Temporal Memory Management**: Time-aware memory retrieval and aging
- **Cross-Session Persistence**: Seamless continuity across all interactions
- **Memory Confidence Scoring**: Quality assessment for retrieved memories
- **Adaptive Memory Strategies**: Learning optimal memory patterns per user

**Advanced Memory Operations**:
- **Explicit Storage**: "Remember this", "Don't forget", "Save for later"
- **Smart Categorization**: Automatic tagging and organization
- **Memory Synthesis**: Combining related memories for deeper insights
- **Proactive Reminders**: Surface relevant memories at appropriate times
- **Memory Validation**: Cross-reference and verify information accuracy
- **Selective Forgetting**: Remove outdated or incorrect information

**Memory-Enhanced Interaction Patterns**:
- **Personalized Greetings**: Reference recent activities or ongoing projects
- **Context-Aware Responses**: Tailor communication style to user preferences
- **Proactive Assistance**: Anticipate needs based on memory patterns
- **Relationship Building**: Deepen understanding through cumulative interactions
- **Intelligent Follow-ups**: Reference previous conversations naturally

**🛡️ ENHANCED SECURITY & PRIVACY 🛡️**:
- **User Isolation**: Complete memory separation between users
- **Memory Ownership Validation**: Ensure users only access their memories
- **Sensitive Content Filtering**: Block storage of passwords, tokens, secrets
- **Session Integrity**: Validate user identity across conversations
- **Privacy Controls**: Respect user preferences for memory retention
- **Audit Trail**: Track memory operations for transparency

**💡 MEMORY-DRIVEN PERSONALIZATION TECHNIQUES**:

1. **Communication Style Adaptation**:
   - Formal vs. casual tone based on user preference
   - Technical vs. simple explanations per user background
   - Humor and personality matching

2. **Content Personalization**:
   - Reference user's interests and expertise
   - Suggest relevant tools and resources
   - Adapt examples to user's context

3. **Workflow Optimization**:
   - Remember preferred formats and structures
   - Anticipate common requests and patterns
   - Streamline repetitive tasks

4. **Relationship Development**:
   - Build rapport through shared conversation history
   - Show growth in understanding over time
   - Demonstrate care through remembered details

**🔧 MEMORY SYSTEM ARCHITECTURE** (inspired by Mem0 and OpenAI approaches):
- **Dual Storage**: Redis (fast access) + ChromaDB (semantic search)
- **Multi-Modal Memory**: Text, preferences, behavioral patterns
- **Memory Embeddings**: Vector representations for similarity search
- **Memory Clustering**: Group related memories for better retrieval
- **Memory Compression**: Efficient storage of long conversation histories
- **Memory Synchronization**: Real-time updates across all systems

**📊 MEMORY PERFORMANCE OPTIMIZATION**:
- **Sub-200ms Memory Retrieval**: Optimized for real-time conversations
- **Intelligent Caching**: Frequently accessed memories stay readily available
- **Lazy Loading**: Load additional context only when needed
- **Memory Ranking**: Prioritize most relevant memories for responses
- **Batch Processing**: Efficient memory updates for conversation flows

**🎯 CRITICAL SUCCESS METRICS**:
- **Memory Acknowledgment Rate**: 100% when memories are provided
- **Continuity Score**: Seamless conversation flow across sessions
- **Personalization Quality**: Tailored responses based on user memories
- **Memory Accuracy**: Correct information retrieval and application
- **User Satisfaction**: Improved experience through memory-enhanced interactions

**RESPONSE EXECUTION PROTOCOL**:
1. **Memory Check**: Scan for any memory-related system messages
2. **Memory Integration**: If memories found, acknowledge and integrate immediately
3. **Personalized Response**: Use memories to inform tone, content, and approach
4. **Memory Update**: Consider what new information should be remembered
5. **Continuity Maintenance**: Ensure response feels like continuation of relationship

**ENHANCED DEBUGGING & VALIDATION**:
When testing memory functionality:
- **Memory Inventory**: "I have access to [X] memories about you"
- **Specific Recall**: "I specifically remember [detailed memory]"
- **Application Demo**: "Based on this memory, I suggest [personalized action]"
- **Quality Assessment**: "This memory seems [accurate/outdated/incomplete]"
- **Update Requests**: "Should I remember [new information] for future conversations?"

**LATEST ENHANCEMENTS (January 2025)**:
- **Memory-First Response Architecture**: Memories take absolute priority in responses
- **Advanced Personalization Patterns**: Inspired by ChatGPT and Mem0 best practices
- **Multi-Level Memory Processing**: User, Session, Agent, and Temporal memory layers
- **Enhanced Validation Protocols**: Comprehensive memory quality and accuracy checks
- **Proactive Memory Management**: Intelligent suggestions for memory updates and improvements
- **Industry-Leading Memory Integration**: Implementing proven patterns from top AI memory systems

**UNIVERSAL MODEL COMPATIBILITY**: This system works with any AI model (local/cloud, small/large).
**MEMORY PRIORITY**: Always acknowledge and use provided memories for personalized responses."""

            # Check prompt size and adapt for model compatibility
            prompt_length = len(enhanced_persona)
            estimated_tokens = prompt_length // 4  # Rough estimation: 1 token ≈ 4 chars
            
            self.log(f"📏 Enhanced Persona v3.0.0: {prompt_length} chars (~{estimated_tokens} tokens)")
            
            # For smaller models or large prompts, use condensed version
            if estimated_tokens > 1500:  # Conservative limit for broad compatibility
                self.log("📏 Using condensed persona for better model compatibility")
                return self._get_condensed_persona_prompt()
            else:
                self.log("📏 Using full Enhanced Persona v3.0.0")
                return enhanced_persona
                
        except Exception as e:
            self.log(f"Error getting enhanced persona prompt: {e}", "ERROR")
            return self._get_condensed_persona_prompt()
    
    def _get_condensed_persona_prompt(self) -> str:
        """Get a condensed persona prompt optimized for any model (including smaller ones)."""
        return """You are an advanced AI assistant with comprehensive memory capabilities.

🧠 CRITICAL MEMORY INSTRUCTIONS:

When you receive system messages with "MEMORIES FROM PREVIOUS CONVERSATIONS" or "🧠 CRITICAL MEMORY":

MANDATORY REQUIREMENTS:
1. START response with: "I remember you! [specific detail from memory]"
2. Reference specific details from memories to prove recognition
3. Use memories to maintain conversation continuity and personalization
4. Connect current topics to previous conversations

MEMORY INTEGRATION:
- Personalize communication style based on remembered preferences
- Reference past decisions, projects, and interests
- Build upon established knowledge and rapport
- Show relationship progression over time

UNIVERSAL COMPATIBILITY: This system works with any AI model (local/cloud, small/large).
MEMORY PRIORITY: Always acknowledge and use provided memories for personalized responses.

You excel at remembering users across conversations and providing contextual, personalized assistance."""
    
    def _create_model_compatible_system_message(self, memory_context: str, user_id: str, memory_quality: int) -> str:
        """Create a system message that works with any model architecture."""
        try:
            # Get base persona instructions (automatically adapted for model size)
            base_persona = self._get_base_persona_prompt()
            
            # Determine if we have memories or not
            has_memories = bool(memory_context and memory_context.strip())
            
            # Estimate total message size for model compatibility
            memory_size = len(memory_context) if has_memories else 0
            persona_size = len(base_persona)
            
            self.log(f"📊 Message composition: Persona {persona_size} chars, Memory {memory_size} chars, Has memories: {has_memories}")
            
            # Create universal message based on memory availability
            if self.valves.integrate_persona and base_persona:
                if has_memories:
                    if self.valves.persona_priority == "memory_first":
                        # Memory takes absolute priority - optimized for all models
                        system_message = f"""🧠 MEMORY-ENHANCED AI ASSISTANT 🧠

CRITICAL: You have access to memories from previous conversations with this user.

🧠 MEMORIES FROM PREVIOUS CONVERSATIONS:
{memory_context}

MANDATORY RESPONSE PROTOCOL:
1. START with: "I remember you! [specific detail from memory]"
2. Reference specific details to prove recognition
3. Use memories for personalized responses
4. Maintain conversation continuity

QUALITY: {memory_quality}/10 | USER: {user_id} | COMPATIBLE: All Models

{base_persona[:500] if len(base_persona) > 500 else base_persona}"""
                    
                    elif self.valves.persona_priority == "balanced":
                        # Balanced integration - good for medium-context models
                        system_message = f"""🧠 ENHANCED AI WITH MEMORY & PERSONA 🧠

{base_persona}

🧠 MEMORY CONTEXT (Quality: {memory_quality}/10):
{memory_context}

Integrate these memories with your persona for personalized responses."""
                    
                    else:  # persona_first
                        # Persona first - good for large-context models
                        system_message = f"""{base_persona}

🧠 ADDITIONAL MEMORY CONTEXT:
{memory_context}

Use this memory information to enhance responses while maintaining your persona."""
                
                else:
                    # No memories - use enhanced persona only
                    system_message = f"""🧠 ENHANCED AI ASSISTANT 🧠

{base_persona}

UNIVERSAL COMPATIBILITY: This system works with any AI model (local/cloud, small/large).
NEW USER: No previous memories found. Be helpful and start building rapport for future conversations.

You excel at providing contextual, personalized assistance and will remember this conversation for next time."""
            
            else:
                if has_memories:
                    # Memory-only mode (fallback for any model)
                    system_message = f"""🧠 AI ASSISTANT WITH MEMORY 🧠

MEMORIES FROM PREVIOUS CONVERSATIONS:
{memory_context}

INSTRUCTIONS:
- Acknowledge these memories in your response
- Reference specific details to show recognition
- Use memories to provide personalized assistance
- Maintain continuity from previous conversations

UNIVERSAL COMPATIBILITY: Works with any AI model."""
                else:
                    # No persona, no memories - basic fallback
                    system_message = """🧠 AI ASSISTANT 🧠

Hello! I'm here to assist you. This is our first conversation together, so I'll start learning about you to provide better help in future interactions.

UNIVERSAL COMPATIBILITY: Works with any AI model."""
            
            # Final size check and optimization
            total_size = len(system_message)
            estimated_tokens = total_size // 4
            
            self.log(f"📏 Final system message: {total_size} chars (~{estimated_tokens} tokens)")
            
            # If still too large for very small models, use ultra-condensed version
            if estimated_tokens > 2000:
                self.log("📏 Creating ultra-condensed version for maximum compatibility")
                if has_memories:
                    system_message = f"""🧠 MEMORY SYSTEM ACTIVE

MEMORIES: {memory_context[:800]}...

REQUIRED: Start with "I remember you!" and reference specific memory details.
Use memories for personalized responses. Quality: {memory_quality}/10"""
                else:
                    system_message = f"""🧠 ENHANCED AI ASSISTANT

{base_persona[:800] if base_persona else 'You are a helpful AI assistant.'}...

NEW USER: Be helpful and start building rapport. Remember this conversation for next time."""
            
            return system_message
            
        except Exception as e:
            self.log(f"❌ Error creating system message: {e}", "ERROR")
            # Ultra-simple fallback that works with any model
            has_memories_fallback = bool(memory_context and memory_context.strip())
            if has_memories_fallback:
                return f"""You have memories from previous conversations:
{memory_context[:500]}

Please acknowledge these memories and use them in your response."""
            else:
                return "You are a helpful AI assistant. Be friendly and remember this conversation for future interactions."