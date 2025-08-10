"""
title: Debug Test Function
author: Debug
date: 2025-08-08
version: 1.0
license: MIT
description: Minimal function to test execution
"""

class Filter:
    def __init__(self):
        self.name = "Debug Test Function"
        print("[DEBUG] Test function initialized!")
        
    async def inlet(self, body: dict, __user__=None) -> dict:
        print(f"[DEBUG] Inlet called with: {len(body.get('messages', []))} messages")
        
        # Add a debug message to the conversation
        messages = body.get("messages", [])
        if messages:
            last_msg = messages[-1]
            if last_msg.get("role") == "user":
                original = last_msg["content"]
                last_msg["content"] = f"[DEBUG: Function is working!] {original}"
                
        return body
        
    async def outlet(self, body: dict, __user__=None) -> dict:
        print(f"[DEBUG] Outlet called")
        return body
