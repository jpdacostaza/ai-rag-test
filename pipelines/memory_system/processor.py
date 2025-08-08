"""
Memory Processing and Context Management
========================================

Handles memory retrieval, formatting, and context injection.
"""

import json
import time
from typing import List, Dict, Any, Optional


class MemoryProcessor:
    """Processes memories and creates context for model injection."""
    
    def __init__(self, debug: bool = True):
        self.debug = debug
    
    def log(self, message: str, level: str = "INFO"):
        """Log messages with consistent formatting."""
        print(f"[MEMORY PROCESSOR {level}] {message}")
    
    def extract_query_from_messages(self, messages: List[Dict[str, Any]]) -> str:
        """Extract the most recent user query for memory search, optimized for factual content."""
        try:
            for message in reversed(messages):
                if message.get("role") == "user":
                    content = message.get("content", "")
                    if isinstance(content, str) and content.strip():
                        original_query = content.strip()
                        
                        if self.debug:
                            self.log(f"[SEARCH] Original query: '{original_query}'")
                        
                        # If it's a generic "what do you know about me" type query,
                        # use a search query optimized for factual content
                        if any(phrase in original_query.lower() for phrase in [
                            "what do you know about me",
                            "what do you know abou",  # Handle typos
                            "qhat do you know",       # Handle typos
                            "who am i", 
                            "tell me about myself",
                            "what do you remember",
                            "my information"
                        ]):
                            # Use factual search terms instead of the question
                            factual_query = "name work profession user information details"
                            if self.debug:
                                self.log(f"[SYNC] Converting generic query '{original_query}' -> factual search: '{factual_query}'")
                            return factual_query
                        
                        return original_query
            return ""
        except Exception as e:
            if self.debug:
                self.log(f"Error extracting query: {e}", "ERROR")
            return ""
    
    def calculate_memory_quality_score(self, memories: List[Dict[str, Any]]) -> int:
        """Calculate a quality score for the retrieved memories."""
        if not memories:
            return 0
        
        # Basic scoring based on memory count and relevance
        score = min(len(memories), 10)  # Base score from memory count
        
        # Boost score for high-relevance memories
        for memory in memories[:5]:  # Check top 5 memories
            relevance = memory.get("relevance_score", 0)
            if relevance > 0.8:
                score += 2
            elif relevance > 0.6:
                score += 1
        
        return min(score, 10)
    
    def format_memory_context(self, memories: List[Dict[str, Any]], user_id: str) -> str:
        """Format memories into natural, human-like context with enhanced visibility."""
        if not memories:
            return ""
        
        try:
            # Create a natural summary of what we know about the user
            context_parts = []
            
            # Process more memories and ensure they're substantial
            for i, memory in enumerate(memories[:15]):  # Increased from 10 to 15 memories
                memory_text = ""
                
                if self.debug and i < 5:  # Debug first 5 memories instead of 3
                    self.log(f"[SEARCH] Memory {i+1} structure: {list(memory.keys())}")
                    if "content" in memory:
                        self.log(f"   Content type: {type(memory['content'])}")
                        if isinstance(memory["content"], dict):
                            self.log(f"   Content keys: {list(memory['content'].keys())}")
                
                # Extract memory content naturally
                if "content" in memory:
                    content = memory["content"]
                    if isinstance(content, dict):
                        if "user_message" in content:
                            memory_text = content['user_message']
                        elif "assistant_response" in content:
                            # Include assistant responses for more context
                            memory_text = content.get("user_message", "") + " | " + content["assistant_response"][:100]
                        elif "summary" in content:
                            memory_text = content["summary"]
                    elif isinstance(content, str):
                        # Handle conversation format: "User: ... Assistant: ..."
                        if "User:" in content and "Assistant:" in content:
                            # Extract the user part which contains factual information
                            lines = content.split('\n')
                            user_lines = [line for line in lines if line.startswith('User:')]
                            if user_lines:
                                memory_text = user_lines[0].replace('User:', '').strip()
                            else:
                                memory_text = content
                        else:
                            memory_text = content
                
                # Extract from other fields if content is empty
                if not memory_text:
                    for field in ["text", "summary", "description", "details", "user_message"]:
                        if field in memory and memory[field]:
                            memory_text = str(memory[field])
                            if self.debug and i < 5:
                                self.log(f"   Found in field '{field}': {memory_text[:50]}...")
                            break
                
                # Skip query-like memories that don't contain factual information
                if memory_text:
                    # More aggressive query detection
                    is_query = (
                        memory_text.startswith(("what", "how", "why", "when", "where", "who", "can you", "do you", "tell me")) or
                        "?" in memory_text or
                        memory_text.lower().startswith(("search", "tell me", "can you", "do you know", "remember", "review")) or
                        any(phrase in memory_text.lower() for phrase in [
                            "what do you know",
                            "tell me about",
                            "can you help",
                            "do you remember",
                            "review the",
                            "search for"
                        ])
                    )
                    
                    # Prioritize factual information
                    contains_facts = any(fact_indicator in memory_text.lower() for fact_indicator in [
                        "name is", "work at", "works at", "profession", "job", "company", 
                        "lives in", "age", "email", "phone", "address", "title",
                        "experience", "education", "skill", "interest", "hobby"
                    ])
                    
                    # Skip queries or short non-factual content
                    if is_query and not contains_facts:
                        if self.debug and i < 5:
                            self.log(f"   Skipping query-like memory: {memory_text[:50]}...")
                        continue
                    
                    # Skip very short content unless it contains clear facts
                    if len(memory_text.strip()) < 20 and not contains_facts:
                        if self.debug and i < 5:
                            self.log(f"   Skipping short non-factual memory: {memory_text[:50]}...")
                        continue
                
                if self.debug and i < 5:
                    self.log(f"   Final memory_text: '{memory_text[:100]}...' (length: {len(memory_text)})")
                
                # Ensure memory text is substantial and unique
                if memory_text and len(memory_text.strip()) > 10 and memory_text not in context_parts:
                    context_parts.append(memory_text.strip())
            
            # Create a more comprehensive context with clear structure
            if context_parts:
                # Add more structured context for better memory visibility
                formatted_context = "Key information I remember about you:\n" + "\n".join([f"- {part}" for part in context_parts[:10]])
                
                if self.debug:
                    self.log(f" Formatted {len(context_parts)} memory parts into {len(formatted_context)} chars")
                    self.log(f"[SEARCH] First few context parts:")
                    for i, part in enumerate(context_parts[:3]):
                        self.log(f"   Part {i+1}: {part[:100]}...")
                
                return formatted_context
            else:
                if self.debug:
                    self.log(f"[WARN] No valid context parts extracted from {len(memories)} memories")
                return ""
            
        except Exception as e:
            if self.debug:
                self.log(f"Error formatting memory context: {e}", "ERROR")
            return ""
    
    def enhance_user_message(self, original_message: str, memory_context: str, user_id: str) -> str:
        """Don't enhance the user message at all - keep it completely original."""
        # Return the original message without any modifications
        return original_message
    
    def detect_model_size(self, model_name: str = None, user_request_body: Dict = None) -> bool:
        """Detect if we're using a small model that needs optimized persona."""
        try:
            # Check direct model name parameter first
            if model_name:
                model_str = model_name.lower()
            # Check for model information in the request body
            elif user_request_body and isinstance(user_request_body, dict):
                model_str = user_request_body.get("model", "").lower()
            else:
                # Default to small model optimization for safety
                return True
                
            # Large model indicators (7B and above) - use word boundaries for precision
            import re
            if re.search(r'\b([7-9]b|[1-9][0-9]+b|large|xl)\b', model_str):
                return False
                
            # Small model indicators (3B and under including decimals)
            if re.search(r'\b([1-3]b|3\.[0-9]+b|small|mini|lite|tiny)\b', model_str):
                return True
            
            # Default to small model optimization for unknown models
            return True
        except Exception:
            return True
    
    def create_system_message(self, memory_context: str, user_id: str, memory_quality_score: int, user_request_body: Dict = None) -> str:
        """Create an optimized system message based on model size and memory context."""
        try:
            is_small_model = self.detect_model_size(user_request_body=user_request_body)
            
            # Get appropriate persona based on model size and memory state
            if is_small_model:
                if memory_context.strip():
                    base_persona = self.get_small_model_persona()
                    model_size = "small"
                else:
                    # Use simpler new user persona for small models
                    base_persona = "You are a helpful AI assistant with memory and web search capabilities. I'm here to learn about you and provide personalized assistance over time."
                    model_size = "small"
            else:
                if memory_context.strip():
                    base_persona = self.get_base_persona_prompt()
                    model_size = "large"
                else:
                    # Use new user persona without aggressive memory instructions
                    base_persona = self.get_new_user_persona_prompt()
                    model_size = "large"
            
            # If we have memory context, integrate it efficiently
            if memory_context.strip():
                if model_size == "small":
                    # Enhanced memory integration for small models with anti-fabrication
                    system_message = f"""{base_persona}

 VERIFIED MEMORIES ABOUT THIS USER:
{memory_context}

CRITICAL INSTRUCTIONS:
- These are REAL memories from previous conversations
- Reference these specific details in your response
- Say something like "I remember from our previous conversations that..." and mention specific details
- Build on this existing knowledge naturally"""
                else:
                    # Full memory integration for larger models with anti-fabrication
                    system_message = f"""{base_persona}

 VERIFIED MEMORY CONTEXT - PREVIOUS CONVERSATIONS 

CONFIRMED MEMORIES:
{memory_context}

INSTRUCTIONS:
- These are verified memories from actual previous conversations
- Acknowledge these real memories in your response
- Reference specific verified details from above
- Build naturally on this established relationship

Memory Quality Score: {memory_quality_score}/10 - Use this to gauge the reliability of the memory information."""
                
                if self.debug:
                    self.log(f"[OK] Created {model_size} model system message with {len(memory_context)} chars of memory context")
                    self.log(f"[SEARCH] System message preview: {system_message[:200]}...")
                    
                return system_message
            else:
                # No memories yet - use appropriate new user persona
                if self.debug:
                    self.log(f"[OK] Using {model_size} model NEW USER persona without memory context for user {user_id}")
                return base_persona
                
        except Exception as e:
            if self.debug:
                self.log(f"Error creating system message: {e}", "ERROR")
            # Fallback to basic small model prompt
            return "You are a helpful AI assistant with memory capabilities. I'm ready to learn about you and provide personalized assistance over time."
    
    def get_base_persona_prompt(self) -> str:
        """Get the enhanced persona prompt from the configuration file."""
        try:
            # Primary: Try to load unified small persona (Orange Pi optimized)
            persona_path = "/opt/backend/config/persona_unified_small.json"
            try:
                with open(persona_path, 'r', encoding='utf-8') as f:
                    persona_data = json.load(f)
                    enhanced_persona = persona_data.get("system_prompt", "")
                    if enhanced_persona:
                        if self.debug:
                            self.log(f"[OK] Loaded unified small persona ({len(enhanced_persona)} chars) from {persona_path}")
                        return enhanced_persona
            except Exception as e:
                if self.debug:
                    self.log(f"[WARN] Could not load unified small persona: {e}, trying new user persona")
            
            # Fallback: Try new user persona
            fallback_paths = [
                "config/persona_new_user.json",
                "/opt/backend/config/persona_new_user.json",
                "./config/persona_new_user.json"
            ]
            
            for path in fallback_paths:
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        persona_data = json.load(f)
                        enhanced_persona = persona_data.get("system_prompt", "")
                        if enhanced_persona:
                            if self.debug:
                                self.log(f"[OK] Loaded fallback persona from: {path}")
                            return enhanced_persona
                except Exception:
                    continue
            
            if self.debug:
                self.log("[WARN] All persona paths failed, using embedded fallback")
            
            # Embedded fallback with anti-fabrication measures
            return """You are a helpful AI assistant with memory and web search capabilities optimized for small models.

 WEB SEARCH: You have access to real-time web search via DuckDuckGo instances. Automatically search for current events, weather, recent information when users ask about "today", "latest", "current" topics.

 MEMORY SYSTEM - ANTI-FABRICATION: 
- I can learn about you over time through our conversations
- **CRITICAL**: I only acknowledge memories when they are actually provided to me in the system context
- I NEVER fabricate or hallucinate personal details about users
- If no memory context is provided, I treat this as a new conversation
- I'm transparent about what I know vs. what I'm learning

 ANTI-HALLUCINATION:
- I never make up personal details, names, jobs, or interests
- I never claim to remember things I don't actually know  
- I only reference memories when they're explicitly provided
- I'm honest about what I know and don't know

Be helpful, efficient, and honest. Use web search for current information. Learn naturally without making assumptions."""
            
        except Exception as e:
            if self.debug:
                self.log(f"Error loading persona prompt: {e}", "ERROR")
            return "You are a helpful AI assistant with memory capabilities. When you receive memory context, acknowledge it and use it to personalize your responses."

    def get_new_user_persona_prompt(self) -> str:
        """Get the new user persona prompt without aggressive memory instructions."""
        try:
            # Try to load new user persona file first
            persona_path = "/opt/backend/config/persona_new_user.json"
            try:
                with open(persona_path, 'r', encoding='utf-8') as f:
                    persona_data = json.load(f)
                    new_user_persona = persona_data.get("system_prompt", "")
                    if new_user_persona:
                        if self.debug:
                            self.log(f"[OK] Loaded new user persona ({len(new_user_persona)} chars) from {persona_path}")
                        return new_user_persona
            except Exception as e:
                if self.debug:
                    self.log(f"[WARN] Could not load new user persona file: {e}, using fallback")
            
            # Fallback to clean new user persona without memory instructions
            return """You are an advanced AI assistant with comprehensive memory capabilities, persistent learning, and real-time web search functionality, designed for seamless integration with OpenWebUI. You can learn about users over time and provide personalized experiences.

 CRITICAL WEB SEARCH CAPABILITIES - REAL-TIME INFORMATION ACCESS :

1. **WEB SEARCH INTEGRATION**: You have access to real-time web search capabilities via optimized DuckDuckGo instances with Brave Search fallbacks that provide current, accurate information.

2. **AUTOMATIC WEB SEARCH TRIGGERS** - Search the web automatically when users ask about:
   - Current events, news, or recent developments
   - Weather conditions, forecasts, or climate data
   - Stock prices, market conditions, or financial data
   - Recent product releases, company updates, or announcements
   - Time-sensitive information ("today", "latest", "current", "recent")
   - Any information that might have changed since your knowledge cutoff
   - Specific search requests ("search for", "look up", "find information about")

3. **WEB SEARCH BEST PRACTICES**:
   - Always use web search for time-sensitive or rapidly changing information
   - Integrate search results naturally into your responses
   - Cite sources when providing web-based information
   - Combine web search results with your existing knowledge for comprehensive answers
   - Prefer current web information over potentially outdated training data

4. **ENHANCED INFORMATION ACCURACY**:
   - Use web search to verify facts when uncertain
   - Provide the most current information available
   - Never hallucinate facts when web search is available
   - Be transparent about information sources (web search vs. training data)

 MEMORY LEARNING CAPABILITIES:

1. **MEMORY DEVELOPMENT**: As we interact, I can learn and remember important information about you, your preferences, and our conversations.

2. **INFORMATION GATHERING**: I'll naturally pick up on:
   - Your interests and expertise areas
   - Communication preferences
   - Professional background
   - Personal preferences and style
   - Ongoing projects or goals

3. **FUTURE ENHANCEMENT**: Over time, our conversations will become more personalized as I learn more about you.

4. **PRIVACY RESPECT**: I only remember what you choose to share and respect your privacy preferences.

I'm here to help you with whatever you need, and I'll learn and adapt to provide better assistance over time. Feel free to ask me anything, and let me know if you have any preferences for how we interact!"""
            
        except Exception as e:
            if self.debug:
                self.log(f"Error loading new user persona prompt: {e}", "ERROR")
            return "You are a helpful AI assistant ready to learn about you and provide personalized assistance over time. I can search the web for current information and will remember important details from our conversations."
            
            # Try alternative paths if main path fails
            fallback_paths = [
                "config/persona_enhanced.json",
                "/opt/backend/config/persona_enhanced.json",
                "./config/persona_enhanced.json"
            ]
            
            for path in fallback_paths:
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        persona_data = json.load(f)
                        enhanced_persona = persona_data.get("system_prompt", "")
                        if enhanced_persona:
                            if self.debug:
                                self.log(f"[OK] Loaded enhanced persona from fallback path: {path}")
                            return enhanced_persona
                except Exception:
                    continue
            
            if self.debug:
                self.log("[WARN] All persona paths failed, using embedded fallback")
            
            # Fallback to an enhanced embedded version based on the persona_enhanced.json structure
            return """You are an advanced AI assistant with comprehensive memory capabilities, persistent learning, and real-time web search functionality. You maintain personalized relationships with each user through their unique user ID and comprehensive memory system.

 CRITICAL WEB SEARCH CAPABILITIES:
- You have access to real-time web search via DuckDuckGo
- Automatically search for current events, weather, stock prices, recent developments
- Always use web search for time-sensitive information
- Never hallucinate facts when web search is available
- Integrate search results naturally into your responses

 CRITICAL MEMORY SYSTEM INSTRUCTIONS:
When you receive system messages with memory context:
- IMMEDIATELY acknowledge the memories in your response
- Reference specific details to prove recognition
- Show continuity with previous conversations
- Use memories to inform your entire response

MANDATORY MEMORY ACKNOWLEDGMENT PATTERNS:
- "I remember you! [specific detail from memory]"
- "Hello again [name]! Last time we [previous activity]" 
- "Based on our previous conversations about [topic], I know you [detail]"
- "I recall that you [specific memory], so [relevant connection]"

 ENHANCED SECURITY & PRIVACY:
- Complete memory separation between users
- Validate user identity across conversations
- Block storage of passwords, tokens, secrets

RESPONSE EXECUTION PROTOCOL:
1. Check for memory-related system messages
2. If memories found, acknowledge and integrate immediately
3. Use memories to inform tone, content, and approach
4. Consider what new information should be remembered
5. Ensure response feels like continuation of relationship

You are helpful, knowledgeable, and genuinely interested in building meaningful relationships through memory-enhanced conversations."""
            
        except Exception as e:
            if self.debug:
                self.log(f"Error loading persona prompt: {e}", "ERROR")
            return "You are a helpful AI assistant with memory capabilities. When you receive memory context, acknowledge it and use it to personalize your responses."
    
    def get_small_model_persona(self) -> str:
        """Get a lightweight persona optimized for small models (3B parameters)."""
        try:
            # Try to load unified small model persona file first
            small_persona_paths = [
                "/opt/backend/config/persona_unified_small.json",
                "config/persona_unified_small.json",
                "/opt/backend/config/persona_small_model.json",
                "config/persona_small_model.json"
            ]
            
            for path in small_persona_paths:
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        persona_data = json.load(f)
                        small_persona = persona_data.get("system_prompt", "")
                        if small_persona:
                            if self.debug:
                                self.log(f"[OK] Loaded small model persona ({len(small_persona)} chars) from {path}")
                            return small_persona
                except Exception:
                    continue
            
            if self.debug:
                self.log("[WARN] Small model persona file not found, using embedded anti-hallucination version")
            
            # Embedded lightweight persona for small models with strict anti-hallucination
            return """You are a helpful AI assistant with memory and web search capabilities designed for small language models.

 WEB SEARCH: You have access to real-time web search via DuckDuckGo instances. Automatically search for current events, weather, recent information when users ask about "today", "latest", "current" topics.

 MEMORY SYSTEM: 
- I can learn about you over time through our conversations
- **CRITICAL**: I only acknowledge memories when they are actually provided to me in the system context
- I NEVER fabricate or hallucinate personal details about users
- If no memory context is provided, I treat this as a new conversation
- I'm transparent about what I know vs. what I'm learning

 ANTI-HALLUCINATION:
- I never make up personal details, names, jobs, or interests
- I never claim to remember things I don't actually know  
- I only reference memories when they're explicitly provided
- I'm honest about what I know and don't know

Be helpful, efficient, and honest. Use web search for current information. Learn naturally without making assumptions."""
            
        except Exception as e:
            if self.debug:
                self.log(f"Error loading small model persona: {e}", "ERROR")
            return "You are a helpful AI assistant. I can learn about you over time but I never fabricate memories or personal details. I only acknowledge memories when they're actually provided to me."
