"""
Enhanced Memory Pipeline with Actual Memory Integration
Zero-configuration memory system that automatically enhances conversations with relevant memories.
Designed for optimal performance while maintaining model intelligence.
"""

import asyncio
import json
from typing import Optional
from pydantic import BaseModel, Field


class Pipeline:
    """Enhanced Memory Pipeline - Now with actual memory functionality when enabled"""
    
    class Valves(BaseModel):
        """Configuration for the Enhanced Memory Pipeline"""
        MEMORY_ENABLED: bool = Field(
            default=True,  # Changed to True by default
            description="Enable memory retrieval and enhancement"
        )
        MEMORY_API_URL: str = Field(
            default="http://memory-api:5001",
            description="Memory API base URL"
        )
        DEBUG_LOGGING: bool = Field(
            default=False,
            description="Enable debug logging for troubleshooting"
        )
        INTELLIGENT_CONTEXT: bool = Field(
            default=True,
            description="Enable intelligent context understanding"
        )
        ENABLE_GLOBAL_CONTEXT: bool = Field(
            default=True,
            description="Enable global context processing"
        )
        MAX_MEMORY_RESULTS: int = Field(
            default=5,
            description="Maximum number of memories to retrieve"
        )
        MEMORY_RELEVANCE_THRESHOLD: float = Field(
            default=0.3,
            description="Minimum relevance score for memory inclusion"
        )

    def __init__(self):
        self.type = "filter"
        self.id = "enhanced_memory_pipeline"
        self.name = "Enhanced Memory Pipeline"
        self.valves = self.Valves()

    def log(self, message: str, level: str = "INFO"):
        """Enhanced logging with debug support"""
        if self.valves.DEBUG_LOGGING or level == "ERROR":
            print(f"[{level}] Enhanced Memory Pipeline: {message}")

    async def fetch_memories(self, query: str) -> list:
        """Fetch relevant memories using zero-conf approach"""
        if not self.valves.MEMORY_ENABLED:
            return []
            
        try:
            self.log(f"Fetching memories for query: {query[:100]}...")
            
            # Use zero-conf memory integration
            try:
                # Try to import memory service from our backend
                import sys
                import os
                sys.path.append('/app/backend/data')
                
                from services.memory_service import MemoryService
                
                memory_service = MemoryService()
                results = await memory_service.retrieve_memories(
                    user_id="global_user",  # Use a global user for pipeline memories
                    query=query,
                    limit=self.valves.MAX_MEMORY_RESULTS
                )
                
                memories = results.get("memories", [])
                self.log(f"Retrieved {len(memories)} relevant memories")
                return memories
                
            except ImportError:
                self.log("Memory service not available, using fallback", "WARNING")
                return []
                
        except Exception as e:
            self.log(f"Memory fetch failed: {e}", "ERROR")
            return []

    def extract_query_from_messages(self, messages: list) -> str:
        """Extract a meaningful query from the conversation messages"""
        if not messages:
            return ""
            
        # Get the last user message as the primary query
        last_message = messages[-1]
        if last_message.get("role") == "user":
            return last_message.get("content", "")
            
        # Fallback: combine recent user messages
        user_messages = [
            msg.get("content", "") 
            for msg in messages[-3:] 
            if msg.get("role") == "user"
        ]
        return " ".join(user_messages)

    def format_memories_for_context(self, memories: list) -> str:
        """Format memories into a context string for the model"""
        if not memories:
            return ""
            
        context_parts = ["## Relevant Context from Memory:\n"]
        
        for i, memory in enumerate(memories, 1):
            content = memory.get("content", "")
            metadata = memory.get("metadata", {})
            relevance = memory.get("relevance_score", 0)
            
            # Format each memory
            context_parts.append(f"**Memory {i}** (relevance: {relevance:.2f}):")
            context_parts.append(f"{content}")
            
            if metadata:
                context_parts.append(f"*Context: {metadata}*")
            context_parts.append("")  # Empty line between memories
            
        return "\n".join(context_parts)

    async def inlet(self, body: dict, user: Optional[dict] = None) -> dict:
        """Process incoming requests with memory enhancement"""
        try:
            if not self.valves.ENABLE_GLOBAL_CONTEXT:
                self.log("Global context disabled, passing through")
                return body
                
            self.log("Processing request for memory enhancement")
            
            messages = body.get("messages", [])
            if not messages:
                self.log("No messages found, passing through")
                return body
                
            # Extract query for memory search
            query = self.extract_query_from_messages(messages)
            if not query:
                self.log("No query extracted, passing through")
                return body
                
            self.log(f"Extracted query: {query[:100]}...")
            
            # Fetch relevant memories if enabled
            if self.valves.MEMORY_ENABLED and self.valves.INTELLIGENT_CONTEXT:
                memories = await self.fetch_memories(query)
                
                if memories:
                    # Format memories into context
                    memory_context = self.format_memories_for_context(memories)
                    
                    # Add memory context to the conversation
                    if memory_context:
                        # Find the last user message and enhance it
                        for i in range(len(messages) - 1, -1, -1):
                            if messages[i].get("role") == "user":
                                original_content = messages[i].get("content", "")
                                enhanced_content = f"{memory_context}\n\n## Current Request:\n{original_content}"
                                messages[i]["content"] = enhanced_content
                                self.log(f"Enhanced message with {len(memories)} memories")
                                break
                else:
                    self.log("No relevant memories found")
            else:
                self.log("Memory functionality disabled")
                
            return body
            
        except Exception as e:
            self.log(f"Inlet error: {e}", "ERROR")
            return body

    async def outlet(self, body: dict, user: Optional[dict] = None) -> dict:
        """Process outgoing responses"""
        try:
            self.log("Processing response")
            
            # Future: Could add response analysis and memory storage here
            # For now, just pass through
            
            return body
            
        except Exception as e:
            self.log(f"Outlet error: {e}", "ERROR")
            return body
