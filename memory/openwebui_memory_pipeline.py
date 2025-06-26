"""
title: Memory Function
author: Backend Team
author_url: http://localhost:8001
funding_url:
version: 1.0.0
license: MIT
description: Advanced memory function for OpenWebUI with conversation persistence and context injection
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


class Function:
    """TODO: Add proper docstring for Function class."""

    def __init__(self):
        """TODO: Add proper docstring for __init__."""
        self.valves = Valves()

    def pipe(self, body: dict):
        """Process message through memory function"""

        # Simple debug output
        if self.valves.debug_mode:
            print(f"[Memory Function] Processing request")
            messages = body.get("messages", [])
            if messages:
                last_message = messages[-1].get("content", "")
                print(f"[Memory Function] Last message: {last_message[:50]}...")

        # For now, just return the body unchanged
        return body
