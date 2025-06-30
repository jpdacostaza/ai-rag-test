"""
OpenWebUI Memory Function - Robust Version
==========================================

A simplified, error-resistant memory function for OpenWebUI.
"""

import json
import time
import traceback
from typing import Dict, List, Optional, Any

try:
    from pydantic import BaseModel
except ImportError:
    # Fallback if pydantic is not available
    class BaseModel:
        def __init__(self, **data):
            for key, value in data.items():
                setattr(self, key, value)

try:
    import httpx
except ImportError:
    try:
        import subprocess
        import sys
        subprocess.check_call([sys.executable, "-m", "pip", "install", "httpx"])
        import httpx
    except:
        # Fallback to requests if httpx fails
        try:
            import requests as httpx
            # Simple adapter for requests
            class HttpxClient:
                def __init__(self, timeout=30.0):
                    self.timeout = timeout
                
                def post(self, url, json=None):
                    import requests
                    return requests.post(url, json=json, timeout=self.timeout)
                
                def get(self, url, params=None):
                    import requests
                    return requests.get(url, params=params, timeout=self.timeout)
            
            httpx.Client = HttpxClient
        except:
            print("Warning: Neither httpx nor requests available")


class Valves(BaseModel):
    """Function configuration valves."""
    # Backend integration
    memory_api_url: str = "http://memory_api:8000"
    
    # Memory settings
    enable_memory: bool = True
    max_memories: int = 3
    memory_threshold: float = 0.7
    
    # Persona settings  
    enable_persona: bool = True
    persona_template: str = "Based on our conversation history: {memory_context}"
    
    # Safety settings
    always_active: bool = True
    safe_mode: bool = True
    
    # Debug
    debug: bool = False


class Function:
    """OpenWebUI Memory Function - Robust implementation."""
    
    def __init__(self):
        try:
            self.valves = Valves()
            self.client = httpx.Client(timeout=30.0)
        except Exception as e:
            print(f"Memory Function init error: {e}")
            # Create minimal valves for safe operation
            self.valves = type('Valves', (), {
                'enable_memory': True,
                'memory_api_url': 'http://memory_api:8000',
                'max_memories': 3,
                'enable_persona': True,
                'persona_template': 'Based on our conversation history: {memory_context}',
                'always_active': True,
                'safe_mode': True,
                'debug': False
            })()
            self.client = None
    
    def log(self, message: str, level: str = "INFO"):
        """Safe logging with error handling."""
        try:
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            print(f"[{timestamp}] [{level}] [Memory Function] {message}")
        except:
            print(f"[Memory Function] {message}")
    
    def store_memory(self, user_id: str, content: str, metadata: Optional[Dict] = None) -> bool:
        """Store memory via the memory API with error handling."""
        if not self.client or not getattr(self.valves, 'enable_memory', True):
            return False
        
        try:
            # Extract conversation components for learning API
            user_message = ""
            assistant_response = ""
            
            # Parse the content if it's a conversation exchange
            if "User: " in content and "Assistant: " in content:
                try:
                    parts = content.split("Assistant: ")
                    if len(parts) == 2:
                        user_message = parts[0].replace("User: ", "").strip()
                        assistant_response = parts[1].strip()
                except:
                    user_message = content
            else:
                user_message = content
            
            payload = {
                "user_id": user_id,
                "conversation_id": metadata.get("conversation_id", "unknown") if metadata else "unknown",
                "user_message": user_message,
                "assistant_response": assistant_response,
                "context": metadata or {},
                "source": "openwebui_function_v2"
            }
            
            response = self.client.post(
                f"{self.valves.memory_api_url}/api/learning/process_interaction",
                json=payload
            )
            
            if response.status_code == 200:
                if getattr(self.valves, 'debug', False):
                    self.log(f"Memory stored successfully for user {user_id}")
                return True
            else:
                if getattr(self.valves, 'debug', False):
                    self.log(f"Failed to store memory: {response.status_code}", "ERROR")
                return False
                
        except Exception as e:
            if getattr(self.valves, 'debug', False):
                self.log(f"Error storing memory: {str(e)}", "ERROR")
            return False
    
    def retrieve_memories(self, user_id: str, query: str, limit: int = 3) -> List[Dict]:
        """Retrieve relevant memories via the memory API with error handling."""
        if not self.client or not getattr(self.valves, 'enable_memory', True):
            return []
        
        try:
            payload = {
                "user_id": user_id,
                "query": query,
                "limit": limit
            }
            
            response = self.client.post(
                f"{self.valves.memory_api_url}/api/memory/retrieve",
                json=payload
            )
            
            if response.status_code == 200:
                result = response.json()
                memories = result.get("memories", [])
                if getattr(self.valves, 'debug', False):
                    self.log(f"Retrieved {len(memories)} memories for user {user_id}")
                return memories
            else:
                if getattr(self.valves, 'debug', False):
                    self.log(f"Failed to retrieve memories: {response.status_code}", "ERROR")
                return []
                
        except Exception as e:
            if getattr(self.valves, 'debug', False):
                self.log(f"Error retrieving memories: {str(e)}", "ERROR")
            return []

    def inlet(self, body: dict, user: Optional[dict] = None) -> dict:
        """Process incoming messages and inject memory context (inlet filter)."""
        # Always return body to prevent breaking the conversation
        if not getattr(self.valves, 'enable_memory', True) and not getattr(self.valves, 'always_active', True):
            return body
        
        try:
            user_id = user.get("id", "anonymous") if user else "anonymous"
            
            # Get the current message
            messages = body.get("messages", [])
            if not messages:
                return body
            
            current_message = messages[-1].get("content", "")
            if not current_message:
                return body
            
            # Retrieve relevant memories
            memories = self.retrieve_memories(user_id, current_message, getattr(self.valves, 'max_memories', 3))
            
            if memories:
                # Format memory context
                if getattr(self.valves, 'enable_persona', True):
                    memory_context = ""
                    for memory in memories:
                        content = memory.get('content', '')
                        if content:
                            memory_context += f"- {content}\n"
                    
                    if memory_context:
                        persona_template = getattr(self.valves, 'persona_template', 'Based on our conversation history: {memory_context}')
                        persona_message = persona_template.format(memory_context=memory_context.strip())
                    else:
                        return body
                else:
                    # Simple memory injection
                    persona_message = "Previous conversation context:\n"
                    for i, memory in enumerate(memories, 1):
                        persona_message += f"{i}. {memory.get('content', '')}\n"
                
                # Inject memory into the system message or create one
                try:
                    system_message = None
                    for msg in messages:
                        if msg.get("role") == "system":
                            system_message = msg
                            break
                    
                    if system_message:
                        # Append to existing system message
                        system_message["content"] = f"{system_message['content']}\n\n{persona_message}"
                    else:
                        # Create new system message
                        system_message = {
                            "role": "system",
                            "content": persona_message
                        }
                        messages.insert(0, system_message)
                    
                    if getattr(self.valves, 'debug', False):
                        self.log(f"Injected {len(memories)} memories for user {user_id}")
                        
                except Exception as e:
                    if getattr(self.valves, 'debug', False):
                        self.log(f"Error injecting memories: {str(e)}", "ERROR")
            
            return body
            
        except Exception as e:
            if getattr(self.valves, 'debug', False):
                self.log(f"Error in inlet: {str(e)}", "ERROR")
            # Always return the original body to prevent breaking conversations
            return body

    def outlet(self, body: dict, user: Optional[dict] = None) -> dict:
        """Process outgoing responses and store them as memories (outlet filter)."""
        # Always return body to prevent breaking the conversation
        if not getattr(self.valves, 'enable_memory', True) and not getattr(self.valves, 'always_active', True):
            return body
        
        try:
            user_id = user.get("id", "anonymous") if user else "anonymous"
            
            # Get the generated response
            messages = body.get("messages", [])
            if not messages:
                return body
            
            # Find the assistant's response
            assistant_message = None
            for msg in reversed(messages):
                if msg.get("role") == "assistant":
                    assistant_message = msg
                    break
            
            if assistant_message:
                content = assistant_message.get("content", "")
                if content:
                    # Store the conversation exchange
                    metadata = {
                        "timestamp": time.time(),
                        "conversation_id": body.get("chat_id", "unknown"),
                        "model": body.get("model", "unknown"),
                        "function_version": "2.1.0"
                    }
                    
                    # Store both user input and assistant response
                    if len(messages) >= 2:
                        user_message = ""
                        for msg in reversed(messages[:-1]):
                            if msg.get("role") == "user":
                                user_message = msg.get("content", "")
                                break
                        
                        if user_message:
                            exchange_content = f"User: {user_message}\nAssistant: {content}"
                            success = self.store_memory(user_id, exchange_content, metadata)
                            if success and getattr(self.valves, 'debug', False):
                                self.log(f"Stored conversation exchange for user {user_id}")
            
            return body
            
        except Exception as e:
            if getattr(self.valves, 'debug', False):
                self.log(f"Error in outlet: {str(e)}", "ERROR")
            # Always return the original body to prevent breaking conversations
            return body
