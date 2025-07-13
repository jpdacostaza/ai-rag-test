"""
Memory Pipeline for OpenWebUI
Integrates with the memory function system to provide enhanced memory capabilities
"""

from typing import List, Optional, Dict, Any
import requests
import json
import os
from pydantic import BaseModel


class Pipeline:
    """
    Memory Pipeline - Enhanced Memory Function Integration
    
    This pipeline integrates with the memory API to provide:
    - Automatic memory storage and retrieval
    - Context-aware conversations
    - Memory-enhanced responses
    """
    
    class Valves(BaseModel):
        """Configuration valves for the memory pipeline"""
        memory_api_url: str = "http://memory-api:5001"
        enable_memory: bool = True
        memory_threshold: int = 100  # Minimum response length to store
        debug_mode: bool = False
    
    def __init__(self):
        """Initialize the memory pipeline"""
        self.type = "filter"
        self.name = "Memory Pipeline"
        self.valves = self.Valves()
        
    async def on_startup(self):
        """Called when the pipeline starts up"""
        print(f"🧠 Memory Pipeline starting up...")
        print(f"Memory API URL: {self.valves.memory_api_url}")
        
    async def on_shutdown(self):
        """Called when the pipeline shuts down"""
        print(f"🧠 Memory Pipeline shutting down...")
        
    async def on_valves_updated(self):
        """Called when configuration valves are updated"""
        print(f"🧠 Memory Pipeline valves updated")
        
    def pipe(
        self, 
        user_message: str, 
        model_id: str, 
        messages: List[Dict[str, Any]], 
        body: Dict[str, Any]
    ) -> str:
        """
        Process the conversation through memory pipeline
        
        Args:
            user_message: The current user message
            model_id: The model being used
            messages: Full conversation history
            body: Request body with additional parameters
            
        Returns:
            Enhanced response with memory context
        """
        
        if not self.valves.enable_memory:
            return user_message
            
        try:
            # Check if memory API is available
            memory_url = f"{self.valves.memory_api_url}/health"
            response = requests.get(memory_url, timeout=5)
            
            if response.status_code == 200:
                if self.valves.debug_mode:
                    print(f"🧠 Memory API is healthy")
                    
                # Get memory context for the user message
                memory_context = self._get_memory_context(user_message, messages)
                
                if memory_context:
                    # Enhance the user message with memory context
                    enhanced_message = f"""[MEMORY CONTEXT]
{memory_context}

[USER MESSAGE]
{user_message}"""
                    
                    if self.valves.debug_mode:
                        print(f"🧠 Enhanced message with memory context")
                        
                    return enhanced_message
                    
        except Exception as e:
            if self.valves.debug_mode:
                print(f"🧠 Memory pipeline error: {str(e)}")
                
        return user_message
        
    def _get_memory_context(self, user_message: str, messages: List[Dict[str, Any]]) -> str:
        """
        Retrieve relevant memory context for the current conversation
        
        Args:
            user_message: Current user message
            messages: Conversation history
            
        Returns:
            Relevant memory context or empty string
        """
        try:
            # Extract user ID from messages if available
            user_id = "default_user"
            
            # Call memory API to get relevant context
            memory_url = f"{self.valves.memory_api_url}/memory/search"
            payload = {
                "query": user_message,
                "user_id": user_id,
                "limit": 3
            }
            
            response = requests.post(
                memory_url, 
                json=payload, 
                timeout=10,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("memories"):
                    # Format memory context
                    context_parts = []
                    for memory in data["memories"]:
                        context_parts.append(f"- {memory.get('content', '')}")
                    
                    return "\\n".join(context_parts)
                    
        except Exception as e:
            if self.valves.debug_mode:
                print(f"🧠 Error retrieving memory context: {str(e)}")
                
        return ""
