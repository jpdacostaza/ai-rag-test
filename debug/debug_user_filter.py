"""
title: Debug User Filter
author: Backend Team
author_url: http://localhost:8001
funding_url: 
version: 1.0.0
license: MIT
description: Debug filter to see what user information is passed from OpenWebUI
requirements: requests
"""

import requests
import json

class Valves:
    def __init__(self):
        self.debug_mode = True

class Filter:
    def __init__(self):
        self.valves = Valves()

    def inlet(self, body: dict, user = None) -> dict:
        """Debug what user information is being passed"""
        
        try:
            print(f"[DEBUG USER FILTER] =================================")
            print(f"[DEBUG USER FILTER] Body keys: {list(body.keys()) if body else 'None'}")
            print(f"[DEBUG USER FILTER] User type: {type(user)}")
            print(f"[DEBUG USER FILTER] User content: {user}")
            
            if user:
                print(f"[DEBUG USER FILTER] User keys: {list(user.keys()) if isinstance(user, dict) else 'Not a dict'}")
                if isinstance(user, dict):
                    for key, value in user.items():
                        print(f"[DEBUG USER FILTER] User.{key}: {value}")
                        
            # Extract chat_id and other info from body
            chat_id = body.get('chat_id', 'no-chat-id')
            messages = body.get('messages', [])
            print(f"[DEBUG USER FILTER] Chat ID: {chat_id}")
            print(f"[DEBUG USER FILTER] Message count: {len(messages)}")
            
            # Check for any user identifier in messages
            if messages:
                latest_msg = messages[-1] if messages else {}
                print(f"[DEBUG USER FILTER] Latest message: {latest_msg}")
            
            print(f"[DEBUG USER FILTER] =================================")
            
        except Exception as e:
            print(f"[DEBUG USER FILTER] Error: {str(e)}")
        
        return body

    def outlet(self, body: dict, user = None) -> dict:
        """Debug outlet processing"""
        print(f"[DEBUG USER FILTER] Outlet - User: {user}")
        return body
