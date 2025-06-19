"""
LLM Manager Module
=================

Centralized management for all LLM-related functions including:
- Ollama API calls (streaming and non-streaming)
- OpenAI API calls (streaming and non-streaming)
- Model configuration and defaults
- Error handling and logging for LLM operations
- Session management for streaming

This module separates LLM functionality from the main application logic
for better organization, debugging, and maintenance.
"""

import os
import json
import logging
import httpx
from typing import Dict, List, Optional, AsyncGenerator, Any
from human_logging import log_service_status

# --- Configuration Constants ---
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "llama3.2:3b")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
USE_OLLAMA = os.getenv("USE_OLLAMA", "true").lower() == "true"

# Global dict to track streaming sessions
STREAM_SESSION_STOP: Dict[str, bool] = {}

class LLMManager:
    """Centralized LLM operations manager"""
    
    def __init__(self):
        self.default_model = DEFAULT_MODEL
        self.ollama_url = OLLAMA_BASE_URL
        self.use_ollama = USE_OLLAMA
        
        # Default options for LLM calls
        self.default_options = {
            "temperature": 0.7,
            "top_p": 0.9,
            "max_tokens": 4096
        }
        
        log_service_status("LLM_MANAGER", "ready", f"Initialized with model: {self.default_model}, Ollama: {self.use_ollama}")
    
    async def call_llm(self, messages: List[Dict[str, str]], model: Optional[str] = None, 
                      api_url: Optional[str] = None, api_key: Optional[str] = None) -> str:
        """
        Main entry point for LLM calls. Routes to appropriate provider.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            model: Model name to use (defaults to DEFAULT_MODEL)
            api_url: API URL for OpenAI-compatible services
            api_key: API key for OpenAI-compatible services
            
        Returns:
            str: LLM response content
        """
        model = model or self.default_model
        
        try:
            if self.use_ollama:
                return await self._call_ollama_llm(messages, model)
            else:
                return await self._call_openai_llm(messages, model, api_url, api_key)
        except Exception as e:
            log_service_status("LLM_MANAGER", "error", f"LLM call failed: {str(e)}")
            raise
    
    async def call_llm_stream(self, messages: List[Dict[str, str]], model: Optional[str] = None,
                             api_url: Optional[str] = None, api_key: Optional[str] = None,
                             stop_event=None, session_id: Optional[str] = None) -> AsyncGenerator[str, None]:
        """
        Stream tokens from LLM in real-time.
        
        Args:
            messages: List of message dictionaries
            model: Model name to use
            api_url: API URL for OpenAI services
            api_key: API key for OpenAI services
            stop_event: Event to stop streaming
            session_id: Session ID for tracking
            
        Yields:
            str: Individual tokens from the LLM
        """
        model = model or self.default_model
        
        try:
            if self.use_ollama:
                async for token in self._call_ollama_llm_stream(messages, model, stop_event, session_id):
                    yield token
            else:
                async for token in self._call_openai_llm_stream(messages, model, api_url, api_key, stop_event, session_id):
                    yield token
        except Exception as e:
            log_service_status("LLM_MANAGER", "error", f"LLM streaming failed: {str(e)}")
            yield f"Error: {str(e)}"
    
    async def _call_ollama_llm(self, messages: List[Dict[str, str]], model: str) -> str:
        """
        Call Ollama API for single response.
        
        Args:
            messages: List of message dictionaries
            model: Model name
            
        Returns:
            str: Response content
        """
        # Debug logging
        logging.info(f"[LLM_MANAGER] Sending {len(messages)} messages to Ollama model {model}")
        for i, msg in enumerate(messages):
            logging.debug(f"[LLM_MANAGER] Message {i}: {msg.get('role', 'unknown')} - {msg.get('content', '')[:100]}...")
        
        # Prepare payload for Ollama chat API
        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": self.default_options["temperature"],
                "top_p": self.default_options["top_p"]
            }
        }
        
        timeout = int(os.getenv("LLM_TIMEOUT", "180"))
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.ollama_url}/api/chat",
                    json=payload,
                    timeout=timeout
                )
                response.raise_for_status()
                data = response.json()
                
                # Extract response content
                content = data.get("message", {}).get("content", "")
                
                if content:
                    logging.info(f"[LLM_MANAGER] Ollama response received: {len(content)} characters")
                    logging.debug(f"[LLM_MANAGER] Response preview: {content[:200]}...")
                else:
                    logging.warning(f"[LLM_MANAGER] Empty response from Ollama. Full data: {data}")
                
                return content
                
        except httpx.RequestError as e:
            error_msg = f"Connection to Ollama at {self.ollama_url} failed: {e}"
            log_service_status("OLLAMA", "failed", error_msg)
            raise Exception(f"Cannot connect to Ollama service at {self.ollama_url}") from e
        except httpx.HTTPStatusError as e:
            error_msg = f"Ollama API returned an error: {e.response.status_code} - {e.response.text}"
            log_service_status("OLLAMA", "failed", error_msg)
            raise Exception(error_msg) from e
    
    async def _call_openai_llm(self, messages: List[Dict[str, str]], model: str,
                              api_url: Optional[str] = None, api_key: Optional[str] = None) -> str:
        """
        Call OpenAI-compatible API for single response.
        
        Args:
            messages: List of message dictionaries
            model: Model name
            api_url: API URL
            api_key: API key
            
        Returns:
            str: Response content
        """
        api_url = api_url or os.getenv("OPENAI_API_BASE_URL", "https://api.openai.com/v1")
        api_key = api_key or os.getenv("OPENAI_API_KEY")
        
        if not api_url.endswith('/chat/completions'):
            api_url = f"{api_url.rstrip('/')}/chat/completions"
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "max_tokens": self.default_options["max_tokens"],
            "temperature": self.default_options["temperature"]
        }
        
        timeout = int(os.getenv("OPENAI_API_TIMEOUT", "180"))
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(api_url, headers=headers, json=payload, timeout=timeout)
                response.raise_for_status()
                data = response.json()
                
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                logging.info(f"[LLM_MANAGER] OpenAI response received: {len(content)} characters")
                
                return content
                
        except httpx.RequestError as e:
            error_msg = f"Connection to OpenAI API at {api_url} failed: {e}"
            log_service_status("OPENAI", "failed", error_msg)
            raise Exception(f"Cannot connect to OpenAI service at {api_url}") from e
        except httpx.HTTPStatusError as e:
            error_msg = f"OpenAI API returned an error: {e.response.status_code} - {e.response.text}"
            log_service_status("OPENAI", "failed", error_msg)
            raise Exception(error_msg) from e
    
    async def _call_ollama_llm_stream(self, messages: List[Dict[str, str]], model: str,
                                     stop_event=None, session_id: Optional[str] = None) -> AsyncGenerator[str, None]:
        """
        Stream tokens from Ollama API.
        
        Args:
            messages: List of message dictionaries
            model: Model name
            stop_event: Event to stop streaming
            session_id: Session ID for tracking
            
        Yields:
            str: Individual tokens
        """
        # Convert messages to prompt format for Ollama generate endpoint
        prompt = "\n".join(f"{msg.get('role', 'user').capitalize()}: {msg.get('content', '')}" for msg in messages)
        
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": True
        }
        
        timeout = int(os.getenv("LLM_TIMEOUT", "180"))
        
        try:
            async with httpx.AsyncClient() as client:
                async with client.stream("POST", f"{self.ollama_url}/api/generate", json=payload, timeout=timeout) as resp:
                    resp.raise_for_status()
                    
                    async for line in resp.aiter_lines():
                        # Check for stop conditions
                        if (stop_event and stop_event.is_set()) or (session_id and STREAM_SESSION_STOP.get(session_id)):
                            break
                        
                        if not line:
                            continue
                        
                        try:
                            data = json.loads(line)
                            if "response" in data:
                                yield data["response"]
                            if data.get("done"):
                                break
                        except json.JSONDecodeError:
                            continue
                            
        except httpx.RequestError as e:
            log_service_status("OLLAMA", "failed", f"Streaming connection to Ollama failed: {e}")
            yield "Error: Cannot connect to Ollama service"
        except Exception as e:
            log_service_status("OLLAMA", "failed", f"Ollama streaming failed: {e}")
            yield f"Error: {str(e)}"
    
    async def _call_openai_llm_stream(self, messages: List[Dict[str, str]], model: str,
                                     api_url: Optional[str] = None, api_key: Optional[str] = None,
                                     stop_event=None, session_id: Optional[str] = None) -> AsyncGenerator[str, None]:
        """
        Stream tokens from OpenAI-compatible API.
        
        Args:
            messages: List of message dictionaries
            model: Model name
            api_url: API URL
            api_key: API key
            stop_event: Event to stop streaming
            session_id: Session ID for tracking
            
        Yields:
            str: Individual tokens
        """
        api_url = api_url or os.getenv("OPENAI_API_BASE_URL", "https://api.openai.com/v1")
        api_key = api_key or os.getenv("OPENAI_API_KEY")
        
        if not api_url.endswith('/chat/completions'):
            api_url = f"{api_url.rstrip('/')}/chat/completions"
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        payload = {
            "model": model,
            "messages": messages,
            "stream": True,
            "max_tokens": self.default_options["max_tokens"],
            "temperature": self.default_options["temperature"]
        }
        
        timeout = int(os.getenv("OPENAI_API_TIMEOUT", "180"))
        
        try:
            async with httpx.AsyncClient() as client:
                async with client.stream("POST", api_url, headers=headers, json=payload, timeout=timeout) as resp:
                    resp.raise_for_status()
                    
                    async for line in resp.aiter_lines():
                        # Check for stop conditions
                        if (stop_event and stop_event.is_set()) or (session_id and STREAM_SESSION_STOP.get(session_id)):
                            break
                        
                        if not line or not line.startswith("data: "):
                            continue
                        
                        line_text = line[6:]
                        if line_text.strip() == "[DONE]":
                            break
                        
                        try:
                            data = json.loads(line_text)
                            if (choices := data.get("choices")) and (delta := choices[0].get("delta")) and (content := delta.get("content")):
                                yield content
                        except json.JSONDecodeError:
                            continue
                            
        except httpx.RequestError as e:
            log_service_status("OPENAI", "failed", f"Streaming connection to OpenAI API failed: {e}")
            yield "Error: Cannot connect to OpenAI API"
        except Exception as e:
            log_service_status("OPENAI", "failed", f"OpenAI streaming failed: {e}")
            yield f"Error: {str(e)}"
    
    def stop_streaming_session(self, session_id: str):
        """Stop a streaming session by session ID."""
        STREAM_SESSION_STOP[session_id] = True
        log_service_status("LLM_MANAGER", "info", f"Stopped streaming session: {session_id}")
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get current model configuration information."""
        return {
            "default_model": self.default_model,
            "ollama_url": self.ollama_url,
            "use_ollama": self.use_ollama,
            "default_options": self.default_options
        }

# Global LLM manager instance
llm_manager = LLMManager()

# Convenience functions for backward compatibility
async def call_llm(messages, model=None, api_url=None, api_key=None):
    """Backward compatibility wrapper for main LLM call."""
    return await llm_manager.call_llm(messages, model, api_url, api_key)

async def call_llm_stream(messages, model=None, api_url=None, api_key=None, stop_event=None, session_id=None):
    """Backward compatibility wrapper for LLM streaming."""
    async for token in llm_manager.call_llm_stream(messages, model, api_url, api_key, stop_event, session_id):
        yield token

def stop_streaming_session(session_id: str):
    """Backward compatibility wrapper for stopping streaming."""
    llm_manager.stop_streaming_session(session_id)

# Deprecated function wrappers (for compatibility)
async def call_ollama_llm(messages, model=None):
    """DEPRECATED: Use llm_manager.call_llm() instead."""
    return await llm_manager._call_ollama_llm(messages, model or DEFAULT_MODEL)

async def call_openai_llm(messages, model=None, api_url=None, api_key=None):
    """DEPRECATED: Use llm_manager.call_llm() instead."""
    return await llm_manager._call_openai_llm(messages, model or DEFAULT_MODEL, api_url, api_key)
