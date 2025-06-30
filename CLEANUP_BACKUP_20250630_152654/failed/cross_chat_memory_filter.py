"""
title: Cross-Chat Memory Filter
author: Backend Team
author_url: http://localhost:8001
funding_url:
version: 2.0.0
license: MIT
description: Persistent memory filter for OpenWebUI - remembers users across all chat sessions
requirements: requests
"""

import os

import requests
import hashlib
import json


class Valves:
    """TODO: Add proper docstring for Valves class."""

    def __init__(self):
        """TODO: Add proper docstring for __init__."""
        self.backend_url = "http://llm_backend:8001"  # Use Docker service name from within OpenWebUI container
        self.api_key = os.getenv("API_KEY", "default_test_key")
        self.memory_limit = 5
        self.enable_learning = True
        self.enable_memory_injection = True
        self.max_memory_length = 600
        self.debug_mode = True
        self.global_memory = True  # Enable cross-chat memory
        self.remember_user_info = True  # Store user information globally


class Filter:
    """TODO: Add proper docstring for Filter class."""

    def __init__(self):
        """TODO: Add proper docstring for __init__."""
        self.valves = Valves()

    def inlet(self, body: dict, user=None) -> dict:
        """Pre-process the request - inject global memory context and store for learning"""

        try:
            # Enhanced user ID extraction with multiple fallbacks
            user_id = self._extract_user_id(user, body)
            chat_id = body.get("chat_id", "default")
            messages = body.get("messages", [])

            if self.valves.debug_mode:
                print(f"[Cross-Chat Memory] Processing user: {user_id}, chat: {chat_id}")
                print(f"[Cross-Chat Memory] User object: {user}")
                print(f"[Cross-Chat Memory] Chat messages: {len(messages)}")

            # Get the latest user message for context retrieval
            latest_message = ""
            for message in reversed(messages):
                if message.get("role") == "user":
                    latest_message = message.get("content", "")
                    break

            # Inject global memory context if enabled
            if self.valves.enable_memory_injection and latest_message and messages:
                try:
                    enhanced_messages = self._inject_global_memory_context(messages, user_id, latest_message)
                    if enhanced_messages and len(enhanced_messages) > len(messages):
                        body["messages"] = enhanced_messages
                        if self.valves.debug_mode:
                            print(
                                f"[Cross-Chat Memory] Injected global memory, message count: {len(enhanced_messages)}"
                            )
                except Exception as e:
                    if self.valves.debug_mode:
                        print(f"[Cross-Chat Memory] Memory injection failed: {str(e)}")

            # Store interaction for global learning if enabled
            if self.valves.enable_learning and latest_message:
                try:
                    self._store_global_interaction(latest_message, user_id, chat_id, messages)
                    if self.valves.debug_mode:
                        print(f"[Cross-Chat Memory] Stored global interaction for user {user_id}")
                except Exception as e:
                    if self.valves.debug_mode:
                        print(f"[Cross-Chat Memory] Global learning storage failed: {str(e)}")

            # Store user information if this looks like an introduction
            if self.valves.remember_user_info and latest_message:
                try:
                    self._store_user_information(latest_message, user_id)
                except Exception as e:
                    if self.valves.debug_mode:
                        print(f"[Cross-Chat Memory] User info storage failed: {str(e)}")

        except Exception as e:
            if self.valves.debug_mode:
                print(f"[Cross-Chat Memory] Inlet processing error: {str(e)}")

        return body

    def outlet(self, body: dict, user=None) -> dict:
        """Post-process the response - store AI responses for better context"""

        try:
            user_id = self._extract_user_id(user, body)

            if self.valves.debug_mode:
                print(f"[Cross-Chat Memory] Outlet processing for user: {user_id}")

            # Extract AI response for learning
            if self.valves.enable_learning and body:
                ai_response = body.get("content", "") or body.get("message", "")
                if ai_response:
                    self._store_ai_response(ai_response, user_id)

        except Exception as e:
            if self.valves.debug_mode:
                print(f"[Cross-Chat Memory] Outlet processing error: {str(e)}")

        return body

    def _extract_user_id(self, user, body) -> str:
        """Extract user ID with multiple fallback strategies"""

        # Strategy 1: Direct user object
        if user and isinstance(user, dict):
            if "id" in user:
                return str(user["id"])
            if "email" in user:
                return f"email_{user['email']}"
            if "username" in user:
                return f"user_{user['username']}"
            if "name" in user:
                return f"name_{user['name']}"

        # Strategy 2: Extract from body/headers
        if body:
            chat_id = body.get("chat_id")
            if chat_id and chat_id != "default":
                # Use a hash of chat_id as user identifier if no user ID available
                return f"chat_user_{hashlib.md5(str(chat_id).encode()).hexdigest()[:8]}"

        # Strategy 3: Anonymous user with session tracking
        return "anonymous_user"

    def _inject_global_memory_context(self, messages: list, user_id: str, query: str) -> list:
        """Inject relevant global memory context across all conversations"""

        try:
            # Retrieve global memories for this user (not tied to specific chat)
            response = requests.post(
                f"{self.valves.backend_url}/api/memory/retrieve",
                json={
                    "user_id": user_id,
                    "query": query,
                    "limit": self.valves.memory_limit,
                    "global_search": True,  # Search across all conversations
                },
                headers={"Authorization": f"Bearer {self.valves.api_key}", "Content-Type": "application/json"},
                timeout=15,
            )

            if response.status_code == 200:
                memory_data = response.json()
                memories = memory_data.get("memories", [])

                if self.valves.debug_mode:
                    print(f"[Cross-Chat Memory] Retrieved {len(memories)} global memories for {user_id}")

                if memories:
                    # Create global memory context message
                    memory_context = self._format_global_memory_context(memories, user_id)

                    # Insert memory context at the beginning of the conversation
                    enhanced_messages = [{"role": "system", "content": memory_context}] + messages.copy()

                    return enhanced_messages

        except Exception as e:
            if self.valves.debug_mode:
                print(f"[Cross-Chat Memory] Global memory retrieval error: {str(e)}")

        return messages

    def _format_global_memory_context(self, memories: list, user_id: str) -> str:
        """Format global memories into context message"""
        if not memories:
            return ""

        context_parts = [
            f"## Global Memory Context for User {user_id}:",
            "This information has been remembered from previous conversations across all chats:",
            "",
        ]

        for i, memory in enumerate(memories, 1):
            content = memory.get("content", "")
            metadata = memory.get("metadata", {})

            # Truncate if too long
            if len(content) > self.valves.max_memory_length:
                content = content[: self.valves.max_memory_length] + "..."

            # Add context about when this was learned
            timestamp = metadata.get("timestamp", "unknown time")
            context_parts.append(f"{i}. {content}")
            if timestamp != "unknown time":
                context_parts.append(f"   (Learned: {timestamp})")

        context_parts.extend(
            [
                "",
                "Use this context to provide personalized responses. The user should feel that you remember them from previous conversations.",
                "",
            ]
        )

        return "\n".join(context_parts)

    def _store_global_interaction(self, user_message: str, user_id: str, chat_id: str, messages: list):
        """Store interaction globally for cross-chat learning"""

        try:
            # Prepare global interaction data
            interaction_data = {
                "user_id": user_id,
                "conversation_id": f"global_{user_id}",  # Use global conversation ID
                "user_message": user_message,
                "timestamp": None,  # Backend will set this
                "context": {
                    "original_chat_id": chat_id,
                    "message_count": len(messages) if messages else 0,
                    "filter": "cross_chat_memory_filter",
                    "global_memory": True,
                },
            }

            # Send to backend for global processing
            response = requests.post(
                f"{self.valves.backend_url}/api/learning/process_interaction",
                json=interaction_data,
                headers={"Authorization": f"Bearer {self.valves.api_key}", "Content-Type": "application/json"},
                timeout=15,
            )

            if self.valves.debug_mode:
                print(f"[Cross-Chat Memory] Global learning response: {response.status_code}")

        except Exception as e:
            if self.valves.debug_mode:
                print(f"[Cross-Chat Memory] Global learning storage error: {str(e)}")

    def _store_user_information(self, user_message: str, user_id: str):
        """Store user information for persistent memory"""

        try:
            # Look for user information patterns
            user_info_keywords = [
                "my name is",
                "i'm",
                "i am",
                "call me",
                "i work",
                "i live",
                "my job",
                "my profession",
                "i like",
                "i love",
                "i hate",
                "i prefer",
                "remember that",
                "note that",
                "important:",
                "please remember",
                "don't forget",
            ]

            message_lower = user_message.lower()
            if any(keyword in message_lower for keyword in user_info_keywords):

                # Store as user profile information
                profile_data = {
                    "user_id": user_id,
                    "conversation_id": f"profile_{user_id}",
                    "user_message": f"USER PROFILE INFO: {user_message}",
                    "timestamp": None,
                    "context": {"type": "user_profile", "filter": "cross_chat_memory_filter", "persistent": True},
                }

                response = requests.post(
                    f"{self.valves.backend_url}/api/learning/process_interaction",
                    json=profile_data,
                    headers={"Authorization": f"Bearer {self.valves.api_key}", "Content-Type": "application/json"},
                    timeout=15,
                )

                if self.valves.debug_mode:
                    print(f"[Cross-Chat Memory] Stored user profile info: {response.status_code}")

        except Exception as e:
            if self.valves.debug_mode:
                print(f"[Cross-Chat Memory] User info storage error: {str(e)}")

    def _store_ai_response(self, ai_response: str, user_id: str):
        """Store AI responses to improve context for future interactions"""

        try:
            if len(ai_response) > 50:  # Only store substantial responses
                response_data = {
                    "user_id": user_id,
                    "conversation_id": f"global_{user_id}",
                    "user_message": f"ASSISTANT PROVIDED: {ai_response[:200]}...",  # Truncate long responses
                    "timestamp": None,
                    "context": {
                        "type": "assistant_response",
                        "filter": "cross_chat_memory_filter",
                        "response_learning": True,
                    },
                }

                response = requests.post(
                    f"{self.valves.backend_url}/api/learning/process_interaction",
                    json=response_data,
                    headers={"Authorization": f"Bearer {self.valves.api_key}", "Content-Type": "application/json"},
                    timeout=15,
                )

                if self.valves.debug_mode:
                    print(f"[Cross-Chat Memory] Stored AI response context: {response.status_code}")

        except Exception as e:
            if self.valves.debug_mode:
                print(f"[Cross-Chat Memory] AI response storage error: {str(e)}")
