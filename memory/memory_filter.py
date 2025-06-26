"""
title: Memory Filter
author: Backend Team
author_url: http://localhost:8001
funding_url:
version: 1.0.0
license: MIT
description: Advanced memory filter for OpenWebUI with conversation persistence and context injection
requirements: requests
"""

import os

import requests


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


class Filter:
    """TODO: Add proper docstring for Filter class."""

    def __init__(self):
        """TODO: Add proper docstring for __init__."""
        self.valves = Valves()

    def inlet(self, body: dict, user=None) -> dict:
        """Pre-process the request - inject memory context and store for learning"""

        try:
            if self.valves.debug_mode:
                print(
                    f"[Memory Filter] Inlet processing for user: {user.get('id', 'anonymous') if user else 'anonymous'}"
                )

            # Extract user information
            user_id = user.get("id", "anonymous") if user else "anonymous"
            chat_id = body.get("chat_id", "default")
            messages = body.get("messages", [])

            # Get the latest user message for context retrieval
            latest_message = ""
            for message in reversed(messages):
                if message.get("role") == "user":
                    latest_message = message.get("content", "")
                    break

            # Inject memory context if enabled
            if self.valves.enable_memory_injection and latest_message and messages:
                try:
                    enhanced_messages = self._inject_memory_context(messages, user_id, chat_id, latest_message)
                    if enhanced_messages and len(enhanced_messages) > len(messages):
                        body["messages"] = enhanced_messages
                        if self.valves.debug_mode:
                            print(f"[Memory Filter] Injected memory context, message count: {len(enhanced_messages)}")
                except Exception as e:
                    if self.valves.debug_mode:
                        print(f"[Memory Filter] Memory injection failed: {str(e)}")

            # Store interaction for learning if enabled
            if self.valves.enable_learning and latest_message:
                try:
                    self._store_interaction(latest_message, user_id, chat_id, messages)
                    if self.valves.debug_mode:
                        print(f"[Memory Filter] Stored interaction for learning")
                except Exception as e:
                    if self.valves.debug_mode:
                        print(f"[Memory Filter] Learning storage failed: {str(e)}")

        except Exception as e:
            if self.valves.debug_mode:
                print(f"[Memory Filter] Inlet processing error: {str(e)}")

        return body

    def outlet(self, body: dict, user=None) -> dict:
        """Post-process the response - could add response learning here"""

        if self.valves.debug_mode:
            print(f"[Memory Filter] Outlet processing")

        # For now, just return the response unchanged
        # Future enhancement: store AI responses for better context
        return body

    def _inject_memory_context(self, messages: list, user_id: str, chat_id: str, query: str) -> list:
        """Inject relevant memory context into messages"""

        try:
            response = requests.post(
                f"{self.valves.backend_url}/api/memory/retrieve",
                json={"user_id": user_id, "query": query, "limit": self.valves.memory_limit},
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
                print(f"[Memory Filter] Memory retrieval error: {str(e)}")

        return messages

    def _format_memory_context(self, memories: list) -> str:
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

    def _store_interaction(self, user_message: str, user_id: str, chat_id: str, messages: list):
        """Store interaction for learning"""

        try:
            # Prepare interaction data
            interaction_data = {
                "user_id": user_id,
                "conversation_id": chat_id,
                "user_message": user_message,
                "timestamp": None,  # Backend will set this
                "context": {"message_count": len(messages) if messages else 0, "filter": "memory_filter"},
            }

            # Send to backend for processing
            response = requests.post(
                f"{self.valves.backend_url}/api/learning/process_interaction",
                json=interaction_data,
                headers={"Authorization": f"Bearer {self.valves.api_key}", "Content-Type": "application/json"},
                timeout=10,
            )

            if self.valves.debug_mode:
                print(f"[Memory Filter] Learning response: {response.status_code}")

        except Exception as e:
            if self.valves.debug_mode:
                print(f"[Memory Filter] Learning storage error: {str(e)}")
