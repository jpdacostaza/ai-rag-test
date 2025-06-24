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

import requests


class Valves:
    def __init__(self):
        self.backend_url = "http://host.docker.internal:8001"
        self.api_key = "f2b985dd-219f-45b1-a90e-170962cc7082"
        self.memory_limit = 3
        self.enable_learning = True
        self.enable_memory_injection = True
        self.max_memory_length = 500
        self.debug_mode = True


class Function:
    def __init__(self):
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
