"""
Memory Filter Function for OpenWebUI
====================================

This module provides the OpenWebUI memory function that was referenced in README.md
but was missing from the codebase. This function integrates with OpenWebUI's
function system to provide memory capabilities.

The function provides:
- Memory storage and retrieval
- Integration with Enhanced Memory Pipeline
- User context management
- Conversation tracking

This bridges the gap between OpenWebUI functions and the memory system.
"""

import asyncio
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any

# Memory function metadata for OpenWebUI
FUNCTION_METADATA = {
    "type": "function",
    "name": "memory_filter",
    "description": "Enhanced memory storage and retrieval function for OpenWebUI",
    "version": "1.0.0",
    "author": "AI RAG Backend Team",
    "requirements": ["requests", "asyncio"],
    "permissions": ["network"]
}

class MemoryFilterFunction:
    """
    OpenWebUI memory function that integrates with the Enhanced Memory Pipeline.
    
    This function provides memory capabilities directly within OpenWebUI conversations,
    allowing for automatic memory storage and context-aware responses.
    """
    
    def __init__(self):
        """Initialize the memory filter function."""
        self.memory_api_url = os.getenv("MEMORY_API_URL", "http://memory-api:5001")
        self.enabled = True
        
    async def store_memory(self, user_id: str, content: str, metadata: Optional[Dict] = None) -> bool:
        """
        Store memory content for a user.
        
        Args:
            user_id: User identifier
            content: Memory content to store
            metadata: Additional metadata for the memory
            
        Returns:
            bool: True if storage was successful
        """
        try:
            import httpx
            
            payload = {
                "user_id": user_id,
                "content": content,
                "metadata": metadata or {},
                "importance": self._calculate_importance(content),
                "memory_type": "conversation"
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.memory_api_url}/api/memory/store",
                    json=payload
                )
                
                return response.status_code == 200
                
        except Exception as e:
            print(f"[MEMORY_FUNCTION] Storage failed: {e}")
            return False
    
    async def retrieve_memories(self, user_id: str, query: str, limit: int = 5) -> List[Dict]:
        """
        Retrieve relevant memories for a user query.
        
        Args:
            user_id: User identifier
            query: Query to search for relevant memories
            limit: Maximum number of memories to retrieve
            
        Returns:
            List[Dict]: List of relevant memories
        """
        try:
            import httpx
            
            payload = {
                "user_id": user_id,
                "query": query,
                "limit": limit,
                "min_score": 0.1
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.memory_api_url}/api/memory/retrieve",
                    json=payload
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data.get("memories", [])
                else:
                    return []
                    
        except Exception as e:
            print(f"[MEMORY_FUNCTION] Retrieval failed: {e}")
            return []
    
    async def process_interaction(self, user_id: str, user_message: str, assistant_response: str) -> bool:
        """
        Process a conversation interaction for learning.
        
        Args:
            user_id: User identifier
            user_message: User's message
            assistant_response: Assistant's response
            
        Returns:
            bool: True if processing was successful
        """
        try:
            import httpx
            
            payload = {
                "user_id": user_id,
                "conversation_id": f"conv_{int(datetime.now().timestamp())}",
                "user_message": user_message,
                "assistant_response": assistant_response,
                "source": "openwebui_function",
                "timestamp": datetime.now().isoformat()
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.memory_api_url}/api/learning/process_interaction",
                    json=payload
                )
                
                return response.status_code == 200
                
        except Exception as e:
            print(f"[MEMORY_FUNCTION] Interaction processing failed: {e}")
            return False
    
    def _calculate_importance(self, content: str) -> float:
        """
        Calculate importance score for memory content.
        
        Args:
            content: Content to analyze
            
        Returns:
            float: Importance score between 0.0 and 1.0
        """
        # Simple importance calculation based on content characteristics
        importance = 0.5  # Default importance
        
        # Boost importance for personal information
        personal_indicators = [
            "my name is", "i am", "i work", "i live", "my job",
            "my favorite", "i like", "i love", "remember that",
            "important", "birthday", "anniversary"
        ]
        
        content_lower = content.lower()
        for indicator in personal_indicators:
            if indicator in content_lower:
                importance += 0.1
        
        # Boost for questions and explicit memory requests
        if any(word in content_lower for word in ["remember", "recall", "note", "important"]):
            importance += 0.2
        
        # Cap at 1.0
        return min(importance, 1.0)
    
    def _extract_user_id(self, context: Dict) -> Optional[str]:
        """
        Extract user ID from OpenWebUI context.
        
        Args:
            context: OpenWebUI context dictionary
            
        Returns:
            Optional[str]: User ID if found
        """
        # Try various ways to extract user ID from OpenWebUI context
        user_id = context.get("user", {}).get("id")
        if not user_id:
            user_id = context.get("user_id")
        if not user_id:
            user_id = context.get("__user__", {}).get("id")
        
        return user_id

# OpenWebUI Function Interface
class Function:
    """
    OpenWebUI Function class for memory integration.
    
    This class provides the standard OpenWebUI function interface
    for the memory filter functionality.
    """
    
    def __init__(self):
        """Initialize the memory function."""
        self.memory_function = MemoryFilterFunction()
        
    def valves(self) -> Dict:
        """Return function valves (configuration options)."""
        return {
            "MEMORY_API_URL": {
                "type": "str",
                "default": "http://memory-api:5001",
                "description": "Memory API URL"
            },
            "ENABLE_AUTO_MEMORY": {
                "type": "bool", 
                "default": True,
                "description": "Enable automatic memory storage"
            },
            "MEMORY_THRESHOLD": {
                "type": "float",
                "default": 0.5,
                "description": "Minimum importance threshold for memory storage"
            }
        }
    
    async def inlet(self, body: Dict, __user__: Optional[Dict] = None) -> Dict:
        """
        Process incoming request (OpenWebUI inlet).
        
        Args:
            body: Request body from OpenWebUI
            __user__: User context from OpenWebUI
            
        Returns:
            Dict: Modified request body with memory context
        """
        try:
            if not self.memory_function.enabled:
                return body
            
            # Extract user information
            user_id = self.memory_function._extract_user_id({"__user__": __user__}) if __user__ else None
            if not user_id:
                return body
            
            # Get the latest user message
            messages = body.get("messages", [])
            if not messages:
                return body
            
            latest_message = messages[-1]
            if latest_message.get("role") != "user":
                return body
            
            user_content = latest_message.get("content", "")
            
            # Retrieve relevant memories
            memories = await self.memory_function.retrieve_memories(
                user_id=user_id,
                query=user_content,
                limit=3
            )
            
            # Inject memory context into system message if memories exist
            if memories:
                memory_context = self._format_memory_context(memories)
                
                # Find or create system message
                system_message = None
                for msg in messages:
                    if msg.get("role") == "system":
                        system_message = msg
                        break
                
                if system_message:
                    # Append to existing system message
                    current_content = system_message.get("content", "")
                    system_message["content"] = f"{current_content}\n\n{memory_context}"
                else:
                    # Create new system message
                    messages.insert(0, {
                        "role": "system",
                        "content": memory_context
                    })
            
            return body
            
        except Exception as e:
            print(f"[MEMORY_FUNCTION] Inlet processing failed: {e}")
            return body
    
    async def outlet(self, body: Dict, __user__: Optional[Dict] = None) -> Dict:
        """
        Process outgoing response (OpenWebUI outlet).
        
        Args:
            body: Response body from OpenWebUI
            __user__: User context from OpenWebUI
            
        Returns:
            Dict: Processed response body
        """
        try:
            if not self.memory_function.enabled:
                return body
            
            # Extract user information
            user_id = self.memory_function._extract_user_id({"__user__": __user__}) if __user__ else None
            if not user_id:
                return body
            
            # Extract messages for interaction processing
            messages = body.get("messages", [])
            if len(messages) < 2:
                return body
            
            # Get user message and assistant response
            user_message = ""
            assistant_response = ""
            
            for msg in reversed(messages):
                if msg.get("role") == "user" and not user_message:
                    user_message = msg.get("content", "")
                elif msg.get("role") == "assistant" and not assistant_response:
                    assistant_response = msg.get("content", "")
                
                if user_message and assistant_response:
                    break
            
            # Process the interaction for learning
            if user_message and assistant_response:
                await self.memory_function.process_interaction(
                    user_id=user_id,
                    user_message=user_message,
                    assistant_response=assistant_response
                )
            
            return body
            
        except Exception as e:
            print(f"[MEMORY_FUNCTION] Outlet processing failed: {e}")
            return body
    
    def _format_memory_context(self, memories: List[Dict]) -> str:
        """
        Format memories into context string.
        
        Args:
            memories: List of memory dictionaries
            
        Returns:
            str: Formatted memory context
        """
        if not memories:
            return ""
        
        context_parts = ["## Relevant Memory Context"]
        context_parts.append("Here are some relevant memories about this user:")
        
        for i, memory in enumerate(memories, 1):
            content = memory.get("content", "")
            timestamp = memory.get("metadata", {}).get("timestamp", "")
            if timestamp:
                context_parts.append(f"{i}. {content} (from {timestamp})")
            else:
                context_parts.append(f"{i}. {content}")
        
        context_parts.append("\nUse this information to provide more personalized and contextual responses.")
        
        return "\n".join(context_parts)

# Export the function for OpenWebUI
def get_function():
    """Return the memory filter function for OpenWebUI."""
    return Function()

# For direct script execution
if __name__ == "__main__":
    print("Memory Filter Function for OpenWebUI")
    print("=====================================")
    print(f"Function: {FUNCTION_METADATA['name']}")
    print(f"Version: {FUNCTION_METADATA['version']}")
    print(f"Description: {FUNCTION_METADATA['description']}")
    print("\nThis function should be imported into OpenWebUI as a custom function.")
