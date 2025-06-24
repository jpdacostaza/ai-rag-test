"""
title: Memory Pipeline
author: Backend Team
author_url: http://localhost:8001
funding_url: 
version: 1.0.0
license: MIT
description: Advanced memory pipeline for OpenWebUI with conversation persistence and context injection
requirements: requests
"""

from typing import List, Union, Generator, Iterator
import requests
import json
import logging

class Pipeline:
    def __init__(self):
        # Pipeline metadata
        self.name = "Memory Pipeline"
        self.id = "memory_pipeline"
        self.type = "filter"
        self.description = "Advanced memory pipeline for OpenWebUI with conversation persistence and context injection"
        
        # Configuration valves
        self.valves = self.Valves(
            **{
                "backend_url": "http://host.docker.internal:8001",
                "api_key": "f2b985dd-219f-45b1-a90e-170962cc7082",
                "memory_limit": 3,
                "enable_learning": True,
                "enable_memory_injection": True,
                "max_memory_length": 500,
                "debug_mode": False
            }
        )

    class Valves:
        def __init__(self, **kwargs):
            self.backend_url = kwargs.get("backend_url", "http://host.docker.internal:8001")
            self.api_key = kwargs.get("api_key", "f2b985dd-219f-45b1-a90e-170962cc7082")
            self.memory_limit = kwargs.get("memory_limit", 3)
            self.enable_learning = kwargs.get("enable_learning", True)
            self.enable_memory_injection = kwargs.get("enable_memory_injection", True)
            self.max_memory_length = kwargs.get("max_memory_length", 500)
            self.debug_mode = kwargs.get("debug_mode", False)

    def pipes(self) -> List[dict]:
        """Return available pipes"""
        return [
            {
                "id": "memory_pipe",
                "name": "Memory Pipe",
                "description": "Memory-enhanced conversation processing"
            }
        ]

    def pipe(self, user_message: str, model_id: str, messages: List[dict], body: dict) -> Union[str, Generator, Iterator]:
        """Process message through memory pipeline"""
        
        # Extract user information
        user_id = body.get("user", {}).get("id", "anonymous")
        chat_id = body.get("chat_id", "default")
        
        if self.valves.debug_mode:
            print(f"[Memory Pipeline] Processing message for user {user_id}, chat {chat_id}")
        
        # Inject memory context if enabled
        if self.valves.enable_memory_injection:
            try:
                enhanced_messages = self._inject_memory_context(messages, user_id, chat_id)
                body["messages"] = enhanced_messages
                
                if self.valves.debug_mode:
                    print(f"[Memory Pipeline] Injected memory context, message count: {len(enhanced_messages)}")
                    
            except Exception as e:
                if self.valves.debug_mode:
                    print(f"[Memory Pipeline] Memory injection failed: {str(e)}")
                # Continue without memory injection if it fails
        
        # Store interaction for learning if enabled
        if self.valves.enable_learning:
            try:
                self._store_interaction(user_message, user_id, chat_id, messages)
                
                if self.valves.debug_mode:
                    print(f"[Memory Pipeline] Stored interaction for learning")
                    
            except Exception as e:
                if self.valves.debug_mode:
                    print(f"[Memory Pipeline] Learning storage failed: {str(e)}")
        
        return user_message

    def _inject_memory_context(self, messages: List[dict], user_id: str, chat_id: str) -> List[dict]:
        """Inject relevant memory context into messages"""
        
        # Get the latest user message for context retrieval
        latest_message = ""
        for message in reversed(messages):
            if message.get("role") == "user":
                latest_message = message.get("content", "")
                break
        
        if not latest_message:
            return messages
        
        # Retrieve relevant memories from backend
        try:
            response = requests.post(
                f"{self.valves.backend_url}/api/memory/retrieve",
                json={
                    "user_id": user_id,
                    "query": latest_message,
                    "limit": self.valves.memory_limit
                },
                headers={
                    "Authorization": f"Bearer {self.valves.api_key}",
                    "Content-Type": "application/json"
                },
                timeout=10
            )
            
            if response.status_code == 200:
                memory_data = response.json()
                memories = memory_data.get("memories", [])
                
                if memories:
                    # Create memory context message
                    memory_context = self._format_memory_context(memories)
                    
                    # Insert memory context before the latest user message
                    enhanced_messages = messages.copy()
                    
                    # Find the last user message and insert context before it
                    for i in range(len(enhanced_messages) - 1, -1, -1):
                        if enhanced_messages[i].get("role") == "user":
                            enhanced_messages.insert(i, {
                                "role": "system",
                                "content": memory_context
                            })
                            break
                    
                    return enhanced_messages
                    
        except Exception as e:
            if self.valves.debug_mode:
                print(f"[Memory Pipeline] Memory retrieval error: {str(e)}")
        
        return messages

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
        
        context_parts.append("## Current Conversation:")
        
        return "\n".join(context_parts)

    def _store_interaction(self, user_message: str, user_id: str, chat_id: str, messages: List[dict]):
        """Store interaction for learning"""
        
        try:
            # Prepare interaction data
            interaction_data = {
                "user_id": user_id,
                "conversation_id": chat_id,
                "user_message": user_message,
                "timestamp": None,  # Backend will set this
                "context": {
                    "message_count": len(messages),
                    "pipeline": "memory_pipeline"
                }
            }
            
            # Send to backend for processing
            response = requests.post(
                f"{self.valves.backend_url}/api/learning/process_interaction",
                json=interaction_data,
                headers={
                    "Authorization": f"Bearer {self.valves.api_key}",
                    "Content-Type": "application/json"
                },
                timeout=10
            )
            
            if self.valves.debug_mode:
                print(f"[Memory Pipeline] Learning response: {response.status_code}")
                
        except Exception as e:
            if self.valves.debug_mode:
                print(f"[Memory Pipeline] Learning storage error: {str(e)}")
