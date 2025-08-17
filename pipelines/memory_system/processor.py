"""
Memory Processing and Context Management
========================================

Handles memory retrieval, formatting, and context injection.
"""

import json
import os
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
        """Detect if we're using a small model - no longer affects persona selection."""
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
        """Create system message with only memory context - no personas/prompts."""
        try:
            # Return only memory context if available, otherwise empty
            if memory_context and memory_context.strip():
                # Just return the memory context without any persona/prompt wrapper
                system_message = f"Previous conversation context:\n{memory_context}"
                
                if self.debug:
                    self.log(f"[OK] Created system message with {len(memory_context)} chars of memory context only")
                    
                return system_message
            else:
                # No memories and no persona - return empty string
                if self.debug:
                    self.log(f"[OK] No memory context for user {user_id}, returning empty system message")
                return ""
                
        except Exception as e:
            if self.debug:
                self.log(f"Error creating system message: {e}", "ERROR")
            # Fallback to empty string
            return ""

    # End of MemoryProcessor class
