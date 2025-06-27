"""
title: Memory Function (Full Version)
author: Backend Team
author_url: http://localhost:8001
funding_url:
version: 1.0.0
license: MIT
description: Advanced memory function for OpenWebUI with conversation persistence and context injection
requirements: requests
"""

import os

from typing import List, Union, Generator, Iterator
import requests
import json


class Valves:
    """TODO: Add proper docstring for Valves class."""

    def __init__(self):
        """TODO: Add proper docstring for __init__."""
        self.backend_url = "http://host.docker.internal:8001"
        self.api_key = os.getenv("API_KEY", "default_test_key")
        self.memory_limit = 3
        self.enable_learning = True
        self.enable_memory_injection = True
        self.max_memory_length = 500
        self.debug_mode = True


class Function:
    """TODO: Add proper docstring for Function class."""

    def __init__(self):
        """TODO: Add proper docstring for __init__."""
        self.valves = Valves()

    def pipe(self, user_message: str, model_id: str, messages: List[dict], body: dict) -> str:
        """Process message through memory function"""

        try:
            # Extract user information
            user_id = "anonymous"
            chat_id = "default"

            if body and isinstance(body, dict):
                if "user" in body and isinstance(body["user"], dict):
                    user_id = body["user"].get("id", "anonymous")
                chat_id = body.get("chat_id", "default")

            if self.valves.debug_mode:
                print(f"[Memory Function] Processing message for user {user_id}, chat {chat_id}")

            # Inject memory context if enabled
            if self.valves.enable_memory_injection and messages:
                try:
                    enhanced_messages = self._inject_memory_context(messages, user_id, chat_id)
                    if enhanced_messages and len(enhanced_messages) > len(messages):
                        body["messages"] = enhanced_messages
                        if self.valves.debug_mode:
                            print(f"[Memory Function] Injected memory context, message count: {len(enhanced_messages)}")
                except Exception as e:
                    if self.valves.debug_mode:
                        print(f"[Memory Function] Memory injection failed: {str(e)}")

            # Store interaction for learning if enabled
            if self.valves.enable_learning:
                try:
                    self._store_interaction(user_message, user_id, chat_id, messages)
                    if self.valves.debug_mode:
                        print(f"[Memory Function] Stored interaction for learning")
                except Exception as e:
                    if self.valves.debug_mode:
                        print(f"[Memory Function] Learning storage failed: {str(e)}")

        except Exception as e:
            if self.valves.debug_mode:
                print(f"[Memory Function] Main processing error: {str(e)}")

        return user_message

    def _inject_memory_context(self, messages: List[dict], user_id: str, chat_id: str) -> List[dict]:
        """Inject relevant memory context into messages"""

        if not messages:
            return messages

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
                json={"user_id": user_id, "query": latest_message, "limit": self.valves.memory_limit},
                headers={"Authorization": f"Bearer {self.valves.api_key}", "Content-Type": "application/json"},
                timeout=10,
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
                            enhanced_messages.insert(i, {"role": "system", "content": memory_context})
                            break

                    return enhanced_messages

        except Exception as e:
            if self.valves.debug_mode:
                print(f"[Memory Function] Memory retrieval error: {str(e)}")

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
                content = content[: self.valves.max_memory_length] + "..."

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
                "context": {"message_count": len(messages) if messages else 0, "pipeline": "memory_function"},
            }

            # Send to backend for processing
            response = requests.post(
                f"{self.valves.backend_url}/api/learning/process_interaction",
                json=interaction_data,
                headers={"Authorization": f"Bearer {self.valves.api_key}", "Content-Type": "application/json"},
                timeout=10,
            )

            if self.valves.debug_mode:
                print(f"[Memory Function] Learning response: {response.status_code}")

        except Exception as e:
            if self.valves.debug_mode:
                print(f"[Memory Function] Learning storage error: {str(e)}")
