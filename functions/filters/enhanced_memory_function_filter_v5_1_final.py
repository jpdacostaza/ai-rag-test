"""
Enhanced Memory Function Filter v5.1 - FINAL VERSION
Persistent cross-session memory for OpenWebUI
- Fixed identity extraction with regex patterns
- Enhanced storage with proper async API calls
- Debug logging for troubleshooting
- Clean fact storage with high importance
"""
import json
import re
import asyncio
import aiohttp
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field

class Filter:
    class Valves(BaseModel):
        priority: int = Field(
            default=1, description="Priority level for this filter"
        )
        memory_api_url: str = Field(
            default="http://memory-api:5001", 
            description="Memory API base URL"
        )
        similarity_threshold: float = Field(
            default=-0.4,
            description="Minimum similarity score for memory retrieval"
        )
        max_memories_per_query: int = Field(
            default=10,
            description="Maximum memories to retrieve per query"
        )
        store_conversation_summaries: bool = Field(
            default=True,
            description="Whether to store conversation summaries"
        )
        debug_logging: bool = Field(
            default=True,
            description="Enable debug logging"
        )

    def __init__(self):
        self.valves = self.Valves()
        self.type = "filter"
        self.name = "Enhanced Memory Filter"
        self.version = "5.1"

    def _log(self, message: str):
        """Debug logging"""
        if self.valves.debug_logging:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"[{timestamp}] [INFO] Enhanced Memory Filter v{self.version}: {message}")

    def _extract_identity_facts(self, message: str) -> List[Dict[str, Any]]:
        """Enhanced identity fact extraction with improved regex patterns"""
        facts = []
        
        # Skip questions and interrogative sentences - but be more selective
        # Only skip if the message starts with question words or is clearly interrogative
        question_start_patterns = [
            r'^\s*\?',  # Starts with question mark
            r'^\s*(?:what|who|where|when|why|how)\b',  # Starts with question words
            r'^\s*(?:do you|can you|are you|would you|could you)\b',  # Starts with question phrases
        ]
        
        import re
        # Only skip if message STARTS with a question pattern
        if any(re.search(pattern, message.lower()) for pattern in question_start_patterns):
            self._log(f"Skipping extraction from question: {message[:30]}...")
            return facts
        
        # Also extract from mixed statements - split on question marks and process declarative parts
        declarative_parts = []
        if '?' in message:
            # Split by question marks and take parts that might contain declarations
            parts = message.split('?')
            for part in parts:
                # Keep parts that contain common declaration patterns
                if any(keyword in part.lower() for keyword in ['my name is', 'i am', 'i live', 'i work']):
                    declarative_parts.append(part.strip())
        else:
            declarative_parts = [message]
        
        # Process each declarative part
        for part in declarative_parts:
            if len(part) < 10:  # Skip very short parts
                continue
                
            self._log(f"Processing declarative part: {part[:50]}...")
            facts.extend(self._extract_facts_from_text(part))
        
        return facts

    def _extract_facts_from_text(self, text: str) -> List[Dict[str, Any]]:
        """Extract identity facts from a text segment"""
        facts = []
        
        # More comprehensive name patterns - only for declarative statements
        name_patterns = [
            r"(?:my name is|i am|i'm|call me|name's)\s+([A-Z][A-Za-z\.]*(?:\s+[A-Z][A-Za-z\.]*)*)",
            r"(?:i am|i'm)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
            r"name(?:\s+is)?\s*:?\s*([A-Z][A-Za-z\.]+)",
        ]
        
        for pattern in name_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                name = match.group(1).strip()
                # Clean up the name (remove extra spaces, but keep periods) and validate
                name = re.sub(r'\s+', ' ', name)
                # Only accept names that are 2-30 characters and don't contain "and"
                if 2 <= len(name) <= 30 and 'and' not in name.lower() and not name.lower() in ['a', 'an', 'the']:
                    facts.append({
                        "content": f"User's name is {name}",
                        "type": "identity_fact",
                        "keywords": f"name {name.lower().replace('.', '')} user identity",
                        "importance": 0.95
                    })
                    self._log(f"Extracted name: '{name}'")
                    break  # Only take the first valid name
        
        # Enhanced work/company patterns
        work_patterns = [
            r"(?:i work at|i work for|i'm at|i'm with|work at|work for|employed at|employed by)\s+([A-Za-z][A-Za-z0-9\s&\.,-]*)",
            r"(?:company|employer|workplace|job)\s*:?\s*([A-Z][A-Za-z0-9\s&\.,-]+)",
            r"at\s+([A-Z][A-Za-z0-9\s&\.,-]+)(?:\s+(?:company|corp|inc|ltd))?",
        ]
        
        for pattern in work_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                company = match.group(1).strip()
                # Clean company name
                company = re.sub(r'\s+', ' ', company)
                if len(company) > 1 and not company.lower() in ['a', 'an', 'the', 'my', 'our']:
                    facts.append({
                        "content": f"User works at {company}",
                        "type": "identity_fact", 
                        "keywords": f"work company {company.lower()} job employer",
                        "importance": 0.9
                    })
                    self._log(f"Extracted workplace: '{company}'")
        
        # Additional personal facts
        personal_patterns = [
            (r"(?:i live in|i'm from|from|live in)\s+([A-Z][A-Za-z\s]{2,20})(?:\.|,|$|\sand)", "location"),
            (r"(?:i am|i'm)\s+(\d+)\s+years old", "age"),
            (r"(?:my role is|i am a|i'm a|i work as)\s+([A-Za-z\s]{3,30})(?:\.|,|$|\sand)", "role"),
        ]
        
        for pattern, fact_type in personal_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                value = match.group(1).strip()
                if len(value) > 1:
                    facts.append({
                        "content": f"User's {fact_type} is {value}",
                        "type": "personal_fact",
                        "keywords": f"{fact_type} {value.lower()} user",
                        "importance": 0.8
                    })
                    self._log(f"Extracted {fact_type}: '{value}'")
        
        return facts

    def _resolve_user_id(self, body: Dict[str, Any], user: Optional[Dict[str, Any]] = None) -> str:
        """Resolve a stable user_id instead of hardcoded global_user.

        Order:
          1. Explicit user dict id/username/email
          2. body['user_id'] if supplied
          3. First system message metadata.user_id (if any future schema)
          4. Fallback to valves default (global_user)
        """
        if user:
            for key in ("id", "user_id", "email", "username"):
                val = user.get(key)
                if val:
                    return str(val)
        if isinstance(body, dict):
            for key in ("user_id", "uid", "userId"):
                if key in body and body[key]:
                    return str(body[key])
        # scan messages for embedded user id
        for msg in body.get("messages", []) if isinstance(body, dict) else []:
            if msg.get("role") == "system":
                meta = msg.get("metadata") or {}
                uid = meta.get("user_id") or meta.get("uid")
                if uid:
                    return str(uid)
        return "global_user"

    async def _store_memory_async(self, content: str, metadata: Dict[str, Any], body: Optional[Dict[str, Any]] = None, user: Optional[Dict[str, Any]] = None) -> bool:
        """Store memory with proper async handling"""
        try:
            # Resolve user id
            user_id = self._resolve_user_id(body or {}, user)
            
            # Build proper metadata for API
            api_metadata = {
                **metadata,
                "timestamp": datetime.now().isoformat(),
                "source": "openwebui_enhanced_filter_v5.1",
                "context": metadata.get("context", ""),
                "explicit": False
            }
            
            memory_data = {
                "user_id": user_id,
                "content": content,
                "metadata": api_metadata,
                "importance": metadata.get("importance", 0.5),
                "memory_type": metadata.get("type", "conversation")
            }
            
            self._log(f"Attempting to store: user_id={user_id}, content='{content[:40]}...', type={metadata.get('type')}")
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.valves.memory_api_url}/api/memory/store",
                    json=memory_data,
                    timeout=aiohttp.ClientTimeout(total=15)
                ) as response:
                    response_text = await response.text()
                    if response.status == 200:
                        self._log(f"[OK] Stored memory: {content[:50]}...")
                        return True
                    else:
                        self._log(f"[ERROR] Storage failed (status {response.status}): {response_text}")
                        return False
                        
        except Exception as e:
            self._log(f"[ERROR] Storage error: {str(e)}")
            return False

    async def _store_conversation_memory_enhanced(self, body: Dict[str, Any], user: Optional[Dict[str, Any]] = None) -> int:
        """Store conversation memory and identity facts with enhanced error handling"""
        stored_count = 0
        
        # Get messages from body
        messages = body.get("messages", [])
        if not messages:
            return stored_count
            
        # Process last few messages for identity facts
        recent_messages = messages[-3:] if len(messages) >= 3 else messages
        
        for message in recent_messages:
            content = message.get("content", "")
            role = message.get("role", "")
            
            if role == "user" and content:
                # Extract and store identity facts
                identity_facts = self._extract_identity_facts(content)
                
                for fact in identity_facts:
                    success = await self._store_memory_async(
                        fact["content"],
                        {
                            "type": fact["type"],
                            "keywords": fact["keywords"],
                            "importance": fact["importance"],
                            "extraction_method": "regex_enhanced"
                        },
                        body,
                        user
                    )
                    if success:
                        stored_count += 1
                
                # Store conversation summary if enabled
                if self.valves.store_conversation_summaries and len(content) > 20:
                    summary = f"User discussed: {content[:100]}..." if len(content) > 100 else content
                    success = await self._store_memory_async(
                        summary,
                        {
                            "type": "conversation_summary",
                            "keywords": " ".join(content.lower().split()[:5]),
                            "importance": 0.5,
                            "extraction_method": "conversation_summary"
                        },
                        body,
                        user
                    )
                    if success:
                        stored_count += 1
        
        return stored_count

    async def _retrieve_memories_async(self, query: str, body: Optional[Dict[str, Any]] = None, user: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Retrieve relevant memories with enhanced filtering (dynamic user id)."""
        try:
            # Resolve user id using conversation body + user info
            user_id = self._resolve_user_id(body or {}, user)
            query_data = {
                "user_id": user_id, 
                "query": query,
                "limit": self.valves.max_memories_per_query,
                "similarity_threshold": self.valves.similarity_threshold
            }
            
            self._log(f"Retrieving memories: user_id={user_id}, query='{query[:30]}...', threshold={self.valves.similarity_threshold}")
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.valves.memory_api_url}/api/memory/retrieve",
                    json=query_data,
                    timeout=aiohttp.ClientTimeout(total=15)
                ) as response:
                    
                    response_text = await response.text()
                    if response.status == 200:
                        result = await response.json()
                        memories = result.get("memories", [])
                        
                        self._log(f"API returned {len(memories)} total memories")
                        
                        # Enhanced filtering - prioritize identity facts
                        identity_facts = [m for m in memories if m.get("metadata", {}).get("type") == "identity_fact"]
                        other_memories = [m for m in memories if m.get("metadata", {}).get("type") != "identity_fact"]
                        
                        # Debug what we found
                        self._log(f"Raw memories: {len(memories)}, Identity facts: {len(identity_facts)}")
                        for i, fact in enumerate(identity_facts[:2]):
                            content = fact.get("content", "")
                            score = fact.get("similarity_score", 0)
                            self._log(f"Identity fact {i+1}: {content[:40]}... (score: {score:.3f})")
                        
                        # Combine with identity facts first
                        filtered_memories = identity_facts[:4] + other_memories[:4]
                        
                        self._log(f"Retrieved {len(filtered_memories)} memories ({len(identity_facts)} identity facts)")
                        return filtered_memories
                    else:
                        self._log(f"[ERROR] Retrieval failed (status {response.status}): {response_text}")
                        return []
                        
        except Exception as e:
            self._log(f"[ERROR] Retrieval error: {str(e)}")
            return []

    async def inlet(self, body: Dict[str, Any], user: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Process incoming messages and retrieve relevant memories"""
        
        # Get the last user message
        messages = body.get("messages", [])
        if not messages:
            return body
            
        last_message = messages[-1]
        if last_message.get("role") != "user":
            return body
            
        user_content = last_message.get("content", "")
        if not user_content:
            return body

        self._log(f"Processing user message: {user_content[:50]}...")

        # Retrieve relevant memories
        memories = await self._retrieve_memories_async(user_content, body, user)
        
        if memories:
            # Create memory context for the AI
            memory_context = "\n\n**IMPORTANT MEMORY CONTEXT - ACKNOWLEDGE AND USE THIS INFORMATION:**\n"
            
            for i, memory in enumerate(memories):
                content = memory.get("content", "")
                metadata = memory.get("metadata", {})
                memory_type = metadata.get("type", "unknown")
                importance = metadata.get("importance", 0.5)
                similarity = memory.get("similarity_score", 0)
                
                memory_context += f"• [{memory_type.upper()}] {content} (relevance: {similarity:.2f})\n"
            
            memory_context += "\n**CRITICAL: You MUST acknowledge this information about the user and use it naturally in your response. When users ask 'what do you know about me', reference this information directly.**\n"
            
            # Find and enhance the system message instead of adding a separate one
            system_message_found = False
            for message in body["messages"]:
                if message.get("role") == "system":
                    # Enhance existing system message with memory context
                    message["content"] = message["content"] + memory_context
                    system_message_found = True
                    self._log(f"Enhanced existing system message with {len(memories)} memories")
                    break
            
            # If no system message exists, create one with memory context
            if not system_message_found:
                enhanced_system_prompt = f"""You are a helpful AI assistant with memory capabilities.

{memory_context}

Please assist the user with their request while naturally incorporating any relevant information you know about them."""
                
                memory_message = {
                    "role": "system", 
                    "content": enhanced_system_prompt
                }
                body["messages"].insert(0, memory_message)
                self._log(f"Created new system message with {len(memories)} memories")
        else:
            self._log("No relevant memories found")
        
        return body

    async def outlet(self, body: Dict[str, Any], user: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Process outgoing messages and store conversation memory"""
        
        try:
            # Store memories from this conversation
            stored_count = await self._store_conversation_memory_enhanced(body, user)
            self._log(f"Successfully stored {stored_count} high-quality memories")
            
        except Exception as e:
            self._log(f"[ERROR] Error in outlet processing: {str(e)}")
        
        return body
