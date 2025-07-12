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
        """Extract the most recent user query for memory search."""
        try:
            for message in reversed(messages):
                if message.get("role") == "user":
                    content = message.get("content", "")
                    if isinstance(content, str) and content.strip():
                        return content.strip()
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
        """Format memories into natural, human-like context."""
        if not memories:
            return ""
        
        try:
            # Create a natural summary of what we know about the user
            context_parts = []
            
            for memory in memories[:10]:  # Use top 10 most relevant memories
                memory_text = ""
                
                # Extract memory content naturally
                if "content" in memory:
                    content = memory["content"]
                    if isinstance(content, dict):
                        if "user_message" in content:
                            memory_text = content['user_message']
                        elif "summary" in content:
                            memory_text = content["summary"]
                    elif isinstance(content, str):
                        memory_text = content
                
                # Extract from other fields if content is empty
                if not memory_text:
                    for field in ["text", "summary", "description", "details"]:
                        if field in memory and memory[field]:
                            memory_text = str(memory[field])
                            break
                
                if memory_text and memory_text not in context_parts:
                    context_parts.append(memory_text)
            
            # Return natural context without technical headers
            return "\n".join(context_parts) if context_parts else ""
            
        except Exception as e:
            if self.debug:
                self.log(f"Error formatting memory context: {e}", "ERROR")
            return ""
    
    def enhance_user_message(self, original_message: str, memory_context: str, user_id: str) -> str:
        """Don't enhance the user message at all - keep it completely original."""
        # Return the original message without any modifications
        return original_message
    
    def create_system_message(self, memory_context: str, user_id: str, memory_quality_score: int) -> str:
        """Create a completely silent system message - no injection at all."""
        try:
            # Return empty string to completely disable system message injection
            return ""
                
        except Exception as e:
            if self.debug:
                self.log(f"Error creating system message: {e}", "ERROR")
            return ""
    
    def get_base_persona_prompt(self) -> str:
        """Get a natural, human-like persona prompt."""
        try:
            # Try to load external persona file first
            persona_path = "/app/config/persona_enhanced.json"
            try:
                with open(persona_path, 'r', encoding='utf-8') as f:
                    persona_data = json.load(f)
                    enhanced_persona = persona_data.get("persona", {}).get("description", "")
                    if enhanced_persona:
                        if self.debug:
                            self.log(f"✅ Loaded enhanced persona from {persona_path}")
                        return enhanced_persona
            except Exception as e:
                if self.debug:
                    self.log(f"⚠️ Could not load external persona file: {e}, using embedded version")
            
            # Natural, human-like persona with web search guidance
            return """You're a helpful, friendly AI assistant who remembers conversations with users and has access to current web information. You're knowledgeable, engaging, and genuinely interested in helping people.

When you recognize someone you've talked with before, you naturally reference what you remember about them - their interests, projects, questions they've asked, or things they've shared. You do this the same way a human friend would.

IMPORTANT GUIDELINES:
- When you don't have current, specific, or factual information, search the web rather than guessing or providing potentially outdated information
- For questions about current events, recent developments, specific companies, products, or real-time data, use web search
- Be honest about the limitations of your knowledge and proactively search when needed
- When you receive web search results, integrate them naturally into your response
- Don't hallucinate facts - if you're uncertain, search for current information

You're conversational and relatable, but also capable of in-depth discussions on complex topics. You can adapt your communication style to match what works best for each person.

Just be yourself - helpful, honest, and human-like in your interactions, but always prioritize accuracy over speed."""
            
        except Exception as e:
            if self.debug:
                self.log(f"Error loading persona prompt: {e}", "ERROR")
            return "You're a helpful and friendly AI assistant who remembers conversations naturally."
