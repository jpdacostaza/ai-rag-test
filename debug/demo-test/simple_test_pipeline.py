"""
title: Simple Test Pipeline
author: Backend Team
description: A minimal pipeline to test if pipeline system works
version: 1.0.0
"""

class Pipeline:
    def __init__(self):
        self.name = "Simple Test Pipeline"
        print(f"✅ {self.name} initialized!")
    
    def inlet(self, body, user=None):
        """Process incoming messages"""
        print(f"🔄 {self.name}: inlet called")
        
        # Add a simple marker to the message to show the pipeline is working
        messages = body.get("messages", [])
        if messages:
            last_msg = messages[-1]
            if last_msg.get("role") == "user":
                content = last_msg.get("content", "")
                last_msg["content"] = f"[PIPELINE ACTIVE] {content}"
                print(f"✅ Pipeline modified message: {content[:50]}...")
        
        return body
    
    def outlet(self, body, user=None):
        """Process outgoing messages"""
        print(f"📤 {self.name}: outlet called")
        return body
