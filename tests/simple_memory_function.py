"""
title: Simple Memory Function
author: Backend Team
version: 1.0.0
description: Simple memory function for OpenWebUI
"""

class Valves:
    def __init__(self):
        self.backend_url = "http://host.docker.internal:8001"
        self.api_key = "f2b985dd-219f-45b1-a90e-170962cc7082"
        self.debug_mode = True

class Function:
    def __init__(self):
        self.valves = Valves()

    def pipe(self, body: dict):
        # Simple function that just prints debug info
        print(f"[Simple Memory Function] Processing request")
        print(f"[Simple Memory Function] Body keys: {body.keys()}")
        
        # Return the body unchanged
        return body
