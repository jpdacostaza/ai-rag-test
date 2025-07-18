"""
Simple Memory Filter Pipeline for OpenWebUI
==========================================

A basic memory filter pipeline that follows the correct OpenWebUI pipeline format.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel


class Pipeline:
    class Valves(BaseModel):
        pipelines: List[str] = ["*"]
        priority: int = 0
        enable_memory: bool = True
        memory_api_url: str = "http://memory_api:8001"
        debug: bool = True

    @property
    def pipelines(self):
        """Return pipelines configuration for OpenWebUI compatibility."""
        return [
            {
                "id": "simple_memory_filter",
                "name": "Simple Memory Filter"
            }
        ]

    def __init__(self):
        self.type = "filter"
        self.id = "simple_memory_filter"
        self.name = "Simple Memory Filter"
        self.valves = self.Valves()

    async def on_startup(self):
        print(f"on_startup:{__name__}")
        if self.valves.debug:
            print("Simple Memory Filter Pipeline initialized")

    async def on_shutdown(self):
        print(f"on_shutdown:{__name__}")

    async def inlet(self, body: dict, user: Optional[dict] = None) -> dict:
        """Process incoming messages before they reach the model."""
        if self.valves.debug:
            print(f"inlet:{__name__}")
            print(f"User: {user.get('name', 'Unknown') if user else 'Unknown'}")
        
        # Add memory context to the conversation if enabled
        if self.valves.enable_memory:
            messages = body.get("messages", [])
            if messages:
                last_message = messages[-1].get("content", "")
                
                # Add a simple memory instruction to the system message
                system_message = {
                    "role": "system",
                    "content": f"[Memory Context] Previous conversation context available. Current query: {last_message[:100]}..."
                }
                
                # Insert system message at the beginning
                messages.insert(0, system_message)
                body["messages"] = messages
        
        return body

    async def outlet(self, body: dict, user: Optional[dict] = None) -> dict:
        """Process outgoing messages after model generates response."""
        if self.valves.debug:
            print(f"outlet:{__name__}")
        
        # Here you could store the conversation to memory
        if self.valves.enable_memory:
            print("Storing conversation to memory (placeholder)")
        
        return body
