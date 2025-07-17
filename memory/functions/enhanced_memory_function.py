"""
Enhanced Memory Function for OpenWebUI - RAG Architecture
Provides intelligent memory storage and retrieval across conversations using dual-database RAG system
"""

import json
import requests
import httpx
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime


class MemoryFunction:
    """Enhanced memory function for OpenWebUI integration with RAG dual-database architecture"""
    
    def __init__(self):
        self.name = "Enhanced Memory Function - RAG"
        self.description = "Stores and retrieves user context and memories using RAG dual-database system (Redis + ChromaDB)"
        self.version = "2.0.0"
        
    def get_function_definition(self) -> Dict[str, Any]:
        """Get the OpenWebUI function definition for RAG architecture"""
        return {
            "id": "enhanced_memory_rag",
            "name": "Enhanced Memory RAG",
            "description": "Intelligent memory storage and retrieval using RAG dual-database system for persistent conversations",
            "type": "function",
            "spec": {
                "type": "function",
                "function": {
                    "name": "process_memory_rag",
                    "description": "Process user messages to store memories and inject relevant context using RAG architecture",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "content": {
                                "type": "string",
                                "description": "The content to process for memory storage with importance classification"
                            },
                            "user_id": {
                                "type": "string", 
                                "description": "Unique user identifier"
                            },
                            "metadata": {
                                "type": "object",
                                "description": "Additional metadata for the memory including importance level"
                            },
                            "importance": {
                                "type": "number",
                                "description": "Importance level (0.0-1.0) for storage strategy selection"
                            }
                        },
                        "required": ["content"]
                    }
                }
            },
            "valve": {
                "MEMORY_API_URL": {
                    "type": "str",
                    "default": "http://memory_api:8080",
                    "title": "Memory API URL"
                },
                "memory_threshold": {
                    "type": "float",
                    "default": 0.1,
                    "title": "Memory Similarity Threshold"
                },
                "max_memories": {
                    "type": "int", 
                    "default": 5,
                    "title": "Maximum Memories to Retrieve"
                },
                "enable_learning": {
                    "type": "bool",
                    "default": True,
                    "title": "Enable Memory Learning"
                }
            }
        }
    
    async def store_memory(self, content: str, user_id: str = None, metadata: Dict = None) -> bool:
        """Store a memory in the memory system"""
        try:
            memory_api_url = getattr(self, 'memory_api_url', 'http://memory_api:8080')
            
            payload = {
                "content": content,
                "metadata": {
                    "user_id": user_id or "default",
                    "timestamp": datetime.now().isoformat(),
                    "type": "conversation",
                    **(metadata or {})
                }
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{memory_api_url}/store",
                    json=payload,
                    timeout=10.0
                )
                return response.status_code == 200
                
        except Exception as e:
            print(f"Error storing memory: {e}")
            return False
    
    async def retrieve_memories(self, query: str, user_id: str = None, max_memories: int = 5) -> List[Dict]:
        """Retrieve relevant memories based on query"""
        try:
            memory_api_url = getattr(self, 'memory_api_url', 'http://memory_api:8080')
            
            params = {
                "query": query,
                "max_memories": max_memories,
                "user_id": user_id or "default"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{memory_api_url}/search",
                    params=params,
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data.get('memories', [])
                else:
                    return []
                    
        except Exception as e:
            print(f"Error retrieving memories: {e}")
            return []
    
    async def process_memory(self, content: str, user_id: str = None, metadata: Dict = None) -> Dict[str, Any]:
        """Main function to process memory storage and retrieval"""
        try:
            # Store the current content as a memory
            stored = await self.store_memory(content, user_id, metadata)
            
            # Retrieve relevant memories
            memories = await self.retrieve_memories(content, user_id)
            
            result = {
                "stored": stored,
                "retrieved_memories": len(memories),
                "relevant_context": [
                    {
                        "content": memory.get("content", ""),
                        "relevance": memory.get("score", 0.0),
                        "timestamp": memory.get("metadata", {}).get("timestamp", "")
                    }
                    for memory in memories[:3]  # Top 3 most relevant
                ]
            }
            
            return result
            
        except Exception as e:
            return {
                "error": f"Memory processing failed: {str(e)}",
                "stored": False,
                "retrieved_memories": 0,
                "relevant_context": []
            }


# Function instance for export
memory_function = MemoryFunction()


def get_function_spec():
    """Get the function specification for OpenWebUI"""
    return memory_function.get_function_definition()


async def process_memory(content: str, user_id: str = None, metadata: Dict = None):
    """Main function entry point"""
    return await memory_function.process_memory(content, user_id, metadata)


# OpenWebUI Function Integration
class Functions:
    """OpenWebUI Functions class"""
    
    def __init__(self):
        self.memory = MemoryFunction()
    
    async def process_memory(self, content: str, user_id: str = None, metadata: Dict = None):
        """Process memory for OpenWebUI"""
        return await self.memory.process_memory(content, user_id, metadata)


# Export for OpenWebUI
__all__ = ['Functions', 'get_function_spec', 'process_memory', 'memory_function']
