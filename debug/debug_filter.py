"""
title: Debug Filter
author: Backend Team
version: 1.0.0
description: Debug filter to verify OpenWebUI filter execution
"""

class Valves:
    def __init__(self):
        self.debug_mode = True

class Filter:
    def __init__(self):
        self.valves = Valves()
        print("[DEBUG FILTER] Filter initialized!")

    def inlet(self, body: dict, user = None) -> dict:
        print(f"[DEBUG FILTER] Inlet called!")
        print(f"[DEBUG FILTER] Body: {body}")
        print(f"[DEBUG FILTER] User: {user}")
        
        # Add a debug message to the conversation
        messages = body.get('messages', [])
        if messages:
            # Add debug info as a system message
            messages.insert(-1, {
                "role": "system", 
                "content": "DEBUG: Memory filter is working! This message was injected by the debug filter."
            })
            body['messages'] = messages
        
        return body

    def outlet(self, body: dict, user = None) -> dict:
        print(f"[DEBUG FILTER] Outlet called!")
        print(f"[DEBUG FILTER] Response body: {body}")
        return body
