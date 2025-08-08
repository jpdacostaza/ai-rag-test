"""
title: Enhanced Memory Function Filter
author: AI Assistant  
date: 2025-08-08
version: 3.0
license: MIT
description: Zero-configuration memory function filter that automatically enhances conversations with relevant user memories. Works as an OpenWebUI Function, not a Pipeline.
requirements: requests
"""

import asyncio
import json
import requests
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class Filter:
    """Enhanced Memory Function Filter - OpenWebUI Function Implementation"""
    
    class Valves(BaseModel):
        """Configuration valves for the Enhanced Memory Filter"""
        MEMORY_ENABLED: bool = Field(
            default=True,
            description="Enable memory retrieval and enhancement globally"
        )
        MEMORY_API_URL: str = Field(
            default="http://memory-api:5001",
            description="Memory API base URL (use localhost:5001 for local testing)"
        )
        MAX_MEMORIES: int = Field(
            default=3,
            description="Maximum number of memories to retrieve"
        )
        DEBUG_LOGGING: bool = Field(
            default=True,
            description="Enable debug logging for troubleshooting"
        )
        USER_ID_SOURCE: str = Field(
            default="global_user",
            description="User ID to use for memory storage (global_user for shared memories)"
        )

    def __init__(self):
        """Initialize the Enhanced Memory Filter as an OpenWebUI Function"""
        # This is a Function Filter, not a Pipeline
        self.valves = self.Valves()
        
        # Set filter properties for OpenWebUI
        self.name = "Enhanced Memory Filter"
        self.description = "Automatically enhances conversations with relevant user memories"
        
        if self.valves.DEBUG_LOGGING:
            print(f"[INFO] {self.name}: Initialized as OpenWebUI Function Filter")

    async def inlet(self, body: dict, __user__: Optional[dict] = None) -> dict:
        """
        Pre-process user input by adding relevant memories as context
        This runs BEFORE the message is sent to the LLM
        """
        if not self.valves.MEMORY_ENABLED:
            if self.valves.DEBUG_LOGGING:
                print(f"[INFO] {self.name}: Memory disabled, skipping enhancement")
            return body

        try:
            # Extract user message
            messages = body.get("messages", [])
            if not messages:
                return body
                
            # Get the latest user message
            latest_message = None
            for msg in reversed(messages):
                if msg.get("role") == "user":
                    latest_message = msg.get("content", "")
                    break
            
            if not latest_message:
                if self.valves.DEBUG_LOGGING:
                    print(f"[INFO] {self.name}: No user message found")
                return body

            if self.valves.DEBUG_LOGGING:
                print(f"[INFO] {self.name}: Processing user message: {latest_message[:100]}...")

            # Retrieve relevant memories
            memories = await self._retrieve_memories(latest_message)
            
            if memories:
                # Add memory context to the conversation
                memory_context = self._format_memory_context(memories)
                
                # Find the last user message and enhance it
                for i in reversed(range(len(messages))):
                    if messages[i].get("role") == "user":
                        original_content = messages[i]["content"]
                        enhanced_content = f"{memory_context}\n\n{original_content}"
                        messages[i]["content"] = enhanced_content
                        
                        if self.valves.DEBUG_LOGGING:
                            print(f"[INFO] {self.name}: Enhanced message with {len(memories)} memories")
                        break
                        
            else:
                if self.valves.DEBUG_LOGGING:
                    print(f"[INFO] {self.name}: No relevant memories found")

        except Exception as e:
            if self.valves.DEBUG_LOGGING:
                print(f"[ERROR] {self.name}: Error in inlet - {str(e)}")
            # Don't fail the request if memory enhancement fails
            
        return body

    async def outlet(self, body: dict, __user__: Optional[dict] = None) -> dict:
        """
        Post-process LLM response and store conversation memories
        This runs AFTER the LLM generates a response
        """
        if not self.valves.MEMORY_ENABLED:
            return body

        try:
            # Extract conversation for memory storage
            messages = body.get("messages", [])
            if len(messages) >= 2:
                # Store the latest user-assistant exchange
                await self._store_conversation_memory(messages)
                
        except Exception as e:
            if self.valves.DEBUG_LOGGING:
                print(f"[ERROR] {self.name}: Error in outlet - {str(e)}")
            
        return body

    async def _retrieve_memories(self, query: str) -> List[Dict[str, Any]]:
        """Retrieve relevant memories from the memory API"""
        try:
            user_id = self.valves.USER_ID_SOURCE
            
            # Make async request to memory API
            memory_url = f"{self.valves.MEMORY_API_URL}/api/memory/retrieve"
            payload = {
                "user_id": user_id,
                "query": query,
                "limit": self.valves.MAX_MEMORIES
            }
            
            # Use requests in async context (consider aiohttp for production)
            response = requests.post(memory_url, json=payload, timeout=5)
            
            if response.status_code == 200:
                result = response.json()
                memories = result.get("memories", [])
                
                if self.valves.DEBUG_LOGGING:
                    print(f"[INFO] {self.name}: Retrieved {len(memories)} memories from API")
                
                return memories
            else:
                if self.valves.DEBUG_LOGGING:
                    print(f"[WARNING] {self.name}: Memory API returned {response.status_code}")
                return []
                
        except Exception as e:
            if self.valves.DEBUG_LOGGING:
                print(f"[ERROR] {self.name}: Memory retrieval failed - {str(e)}")
            return []

    async def _store_conversation_memory(self, messages: List[Dict[str, Any]]) -> None:
        """Store conversation exchange as memory"""
        try:
            # Find the latest user-assistant pair
            user_msg = None
            assistant_msg = None
            
            for msg in reversed(messages):
                if msg.get("role") == "assistant" and not assistant_msg:
                    assistant_msg = msg.get("content", "")
                elif msg.get("role") == "user" and not user_msg:
                    user_msg = msg.get("content", "")
                    
                if user_msg and assistant_msg:
                    break
            
            if user_msg and assistant_msg:
                # Create memory content
                memory_content = f"User asked: {user_msg[:200]}... Assistant responded about relevant context."
                
                # Store memory
                user_id = self.valves.USER_ID_SOURCE
                memory_url = f"{self.valves.MEMORY_API_URL}/api/memory/store"
                payload = {
                    "user_id": user_id,
                    "content": memory_content,
                    "context": json.dumps({
                        "type": "conversation_exchange",
                        "user_query": user_msg[:100]
                    }),
                    "importance": 0.6,
                    "source": "conversation_filter"
                }
                
                response = requests.post(memory_url, json=payload, timeout=5)
                
                if self.valves.DEBUG_LOGGING:
                    if response.status_code == 200:
                        print(f"[INFO] {self.name}: Stored conversation memory")
                    else:
                        print(f"[WARNING] {self.name}: Memory storage failed: {response.status_code}")
                        
        except Exception as e:
            if self.valves.DEBUG_LOGGING:
                print(f"[ERROR] {self.name}: Memory storage error - {str(e)}")

    def _format_memory_context(self, memories: List[Dict[str, Any]]) -> str:
        """Format retrieved memories as context for the LLM"""
        if not memories:
            return ""
        
        context_lines = ["## Relevant Context from Memory:"]
        
        for i, memory in enumerate(memories, 1):
            content = memory.get("content", "")
            similarity = memory.get("similarity_score", 0)
            
            context_lines.append(f"**Memory {i}** (relevance: {similarity:.2f}):")
            context_lines.append(content)
            context_lines.append("")  # Empty line for spacing
        
        return "\n".join(context_lines)
