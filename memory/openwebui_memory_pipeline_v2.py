"""
title: Advanced Memory Pipeline
author: Backend Team
author_url: http://localhost:9099
funding_url:
version: 2.0.0
license: MIT
description: Advanced memory pipeline for OpenWebUI with conversation persistence and context injection
requirements: requests
"""

import os
from typing import List, Optional, Dict, Any
import requests
import json
from pydantic import BaseModel


class Pipeline:
    class Valves(BaseModel):
        pipelines: List[str] = []
        priority: int = 0
        backend_url: str = "http://memory_api:8000"  # Docker compose service name
        api_key: str = "default_test_key"
        memory_limit: int = 3
        enable_learning: bool = True
        enable_memory_injection: bool = True
        max_memory_length: int = 500
        debug_mode: bool = True

    def __init__(self):
        self.type = "filter"
        self.name = "Advanced Memory Pipeline"
        self.valves = self.Valves(
            **{
                "pipelines": ["*"],  # Connect to all pipelines
            }
        )

    async def on_startup(self):
        print(f"[Memory Pipeline] Starting up: {self.name}")
        pass

    async def on_shutdown(self):
        print(f"[Memory Pipeline] Shutting down: {self.name}")
        pass

    async def inlet(self, body: dict, user: Optional[dict] = None) -> dict:
        """Process incoming messages and inject memory context"""
        
        if self.valves.debug_mode:
            print(f"[Memory Pipeline] Processing inlet request")

        try:
            # Extract user information
            user_id = "anonymous"
            chat_id = "default"
            
            if user and isinstance(user, dict):
                user_id = user.get("id", "anonymous")
            
            # Get messages from body
            messages = body.get("messages", [])
            if not messages:
                return body

            # Get the latest user message
            latest_message = ""
            for message in reversed(messages):
                if message.get("role") == "user":
                    latest_message = message.get("content", "")
                    break

            if self.valves.debug_mode:
                print(f"[Memory Pipeline] Processing message for user {user_id}")
                print(f"[Memory Pipeline] Latest message: {latest_message[:100]}...")

            # Inject memory context if enabled
            if self.valves.enable_memory_injection and latest_message:
                try:
                    enhanced_messages = await self._inject_memory_context(messages, user_id, latest_message)
                    if enhanced_messages and len(enhanced_messages) > len(messages):
                        body["messages"] = enhanced_messages
                        if self.valves.debug_mode:
                            print(f"[Memory Pipeline] Injected memory context, message count: {len(enhanced_messages)}")
                except Exception as e:
                    if self.valves.debug_mode:
                        print(f"[Memory Pipeline] Memory injection failed: {str(e)}")

            # Store interaction for learning if enabled
            if self.valves.enable_learning and latest_message:
                try:
                    await self._store_interaction(latest_message, user_id, messages)
                    if self.valves.debug_mode:
                        print(f"[Memory Pipeline] Stored interaction for learning")
                except Exception as e:
                    if self.valves.debug_mode:
                        print(f"[Memory Pipeline] Learning storage failed: {str(e)}")

        except Exception as e:
            if self.valves.debug_mode:
                print(f"[Memory Pipeline] Main processing error: {str(e)}")

        return body

    async def outlet(self, body: dict, user: Optional[dict] = None) -> dict:
        """Process outgoing responses (optional for memory pipeline)"""
        if self.valves.debug_mode:
            print(f"[Memory Pipeline] Processing outlet response")
        return body

    async def _inject_memory_context(self, messages: List[dict], user_id: str, query: str) -> List[dict]:
        """Inject relevant memory context into messages"""

        try:
            # Retrieve relevant memories from backend
            memory_response = await self._retrieve_memories(user_id, query)
            
            if memory_response and "memories" in memory_response:
                memories = memory_response["memories"]
                
                if memories:
                    # Create memory context message
                    memory_context = self._format_memory_context(memories)
                    
                    # Insert memory context at the beginning as system message
                    enhanced_messages = [
                        {"role": "system", "content": memory_context}
                    ] + messages.copy()
                    
                    return enhanced_messages

        except Exception as e:
            if self.valves.debug_mode:
                print(f"[Memory Pipeline] Memory retrieval error: {str(e)}")

        return messages

    async def _retrieve_memories(self, user_id: str, query: str) -> Optional[Dict[str, Any]]:
        """Retrieve memories from backend"""
        
        try:
            # For now, we'll use a simple synchronous request
            # In production, you'd want to use aiohttp for async requests
            response = requests.post(
                f"{self.valves.backend_url}/api/memory/retrieve",
                json={
                    "user_id": user_id, 
                    "query": query, 
                    "limit": self.valves.memory_limit
                },
                headers={
                    "Authorization": f"Bearer {self.valves.api_key}", 
                    "Content-Type": "application/json"
                },
                timeout=10,
            )

            if response.status_code == 200:
                return response.json()
            else:
                if self.valves.debug_mode:
                    print(f"[Memory Pipeline] Backend response error: {response.status_code}")
                
        except Exception as e:
            if self.valves.debug_mode:
                print(f"[Memory Pipeline] Memory retrieval request error: {str(e)}")
        
        return None

    def _format_memory_context(self, memories: List[dict]) -> str:
        """Format memories into context message"""
        if not memories:
            return ""

        context_parts = ["## Relevant Context from Previous Conversations:"]

        for i, memory in enumerate(memories, 1):
            content = memory.get("content", "")
            # Truncate if too long
            if len(content) > self.valves.max_memory_length:
                content = content[:self.valves.max_memory_length] + "..."

            context_parts.append(f"{i}. {content}")

        context_parts.append("\n## Current Conversation:")

        return "\n".join(context_parts)

    async def _store_interaction(self, user_message: str, user_id: str, messages: List[dict]):
        """Store interaction for learning"""

        try:
            # Prepare interaction data
            interaction_data = {
                "user_id": user_id,
                "conversation_id": f"pipeline_{user_id}",
                "user_message": user_message,
                "timestamp": None,  # Backend will set this
                "context": {
                    "message_count": len(messages) if messages else 0, 
                    "pipeline": "advanced_memory_pipeline",
                    "version": "2.0.0"
                },
            }

            # Send to backend for processing (async in production)
            response = requests.post(
                f"{self.valves.backend_url}/api/learning/process_interaction",
                json=interaction_data,
                headers={
                    "Authorization": f"Bearer {self.valves.api_key}", 
                    "Content-Type": "application/json"
                },
                timeout=10,
            )

            if self.valves.debug_mode:
                print(f"[Memory Pipeline] Learning response: {response.status_code}")

        except Exception as e:
            if self.valves.debug_mode:
                print(f"[Memory Pipeline] Learning storage error: {str(e)}")
