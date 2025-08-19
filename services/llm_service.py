"""
LLM service for calling Ollama and OpenAI APIs with advanced prompt caching.
"""

import asyncio
import json
import logging
import time
from typing import AsyncGenerator, List, Dict, Any, Optional

import httpx
from config.config_unified import (
    DEFAULT_MODEL,
    OLLAMA_BASE_URL,
    USE_OLLAMA,
    OPENAI_API_BASE_URL,
    OPENAI_API_KEY,
    OPENAI_API_MAX_TOKENS,
    OPENAI_API_TIMEOUT,
    LLM_TIMEOUT,
    CONNECTION_TIMEOUT,
    READ_TIMEOUT,
    WRITE_TIMEOUT,
    CONNECTION_POOL_SIZE,
    MAX_KEEPALIVE_CONNECTIONS)
from utilities.error_patterns import handle_service_errors, handle_llm_errors, ErrorHandlerConfig
from core.unified_logging import get_logger, log_function_call, log_performance, log_service_status
from services.prompt_cache_service import prompt_cache_service


class LLMService:
    """Service for handling LLM API calls with advanced prompt caching."""

    def __init__(self):
        """Initializes the LLMService with configuration and prompt caching."""
        self.default_model = DEFAULT_MODEL
        self.ollama_url = OLLAMA_BASE_URL
        self.use_ollama = USE_OLLAMA
        self.logger = get_logger(__name__)
        
        # Initialize prompt caching
        self.cache_service = prompt_cache_service
        
        self.logger.info(
            f"LLM Service initialized - use_ollama: {self.use_ollama}, ollama_url: {self.ollama_url}, default_model: {self.default_model}"
        )
        log_service_status("LLM", "info", f"LLM Service initialized with prompt caching - use_ollama: {self.use_ollama}")

    async def call_llm(
        self,
        messages: List[Dict[str, Any]],
        model: Optional[str] = None,
        api_url: Optional[str] = None,
        api_key: Optional[str] = None,
        enable_caching: bool = True,
        cache_type: str = "conversation") -> str:
        """
        Calls an LLM API with prompt caching support.
        
        Args:
            messages: List of message dictionaries
            model: Model name
            api_url: API URL override
            api_key: API key override  
            enable_caching: Whether to use prompt caching
            cache_type: Type of cache to use
        """
        model = model or self.default_model

        # Generate cache key from messages for response caching
        cache_key = self._generate_cache_key(messages, model)
        
        # Check cache first if enabled
        if enable_caching:
            cached_response = await self.cache_service.get_cached_prompt(
                cache_key, model, cache_type
            )
            if cached_response:
                log_service_status("LLM", "info", f"🚀 [OLLAMA] Cache hit for {model} ({cached_response.token_count} tokens saved)")
                return cached_response.content

        # Call LLM API
        if self.use_ollama:
            response = await self.call_ollama_llm(messages, model, enable_caching)
        else:
            response = await self.call_openai_llm(messages, model, api_url, api_key, enable_caching)
        
        # Cache the response if enabled
        if enable_caching and response:
            await self.cache_service.cache_prompt(
                cache_key, response, model, cache_type
            )
            log_service_status("LLM", "info", f"💾 [OLLAMA] Response cached for {model}")
        
        return response

    def _generate_cache_key(self, messages: List[Dict[str, Any]], model: str) -> str:
        """Generate cache key from messages and model."""
        # Extract just the content for caching key
        content_parts = []
        for msg in messages:
            if isinstance(msg.get('content'), str):
                content_parts.append(f"{msg.get('role', '')}:{msg['content']}")
        
        combined_content = "|".join(content_parts)
        return f"{model}:{combined_content}"

    @handle_llm_errors(
        operation_name="call_ollama_llm"
    )
    async def call_ollama_llm(
        self, 
        messages: List[Dict[str, Any]], 
        model: Optional[str] = None,
        enable_caching: bool = True
    ) -> str:
        """
        Asynchronously calls the Ollama API using the chat endpoint with caching support.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content' keys
            model: Optional model name, defaults to configured default model
            enable_caching: Whether to enhance request with cache controls
            
        Returns:
            str: The response content from the LLM
            
        Raises:
            Exception: If connection fails or API returns an error
        """
        model = model or self.default_model

        # Enhance messages with cache controls if enabled
        if enable_caching:
            # Extract system prompt if present for caching
            system_prompt = None
            enhanced_messages = []
            
            for msg in messages:
                if msg.get('role') == 'system':
                    system_prompt = msg.get('content', '')
                else:
                    enhanced_messages.append(msg)
            
            # Create enhanced request with cache controls
            enhanced_request = self.cache_service.enhance_prompt_with_caching(
                enhanced_messages, 
                system_prompt=system_prompt
            )
            
            # Use enhanced messages for Ollama (note: Ollama doesn't support cache_control directly,
            # but we structure the request optimally for future compatibility)
            if enhanced_request.get('system'):
                ollama_messages = [{'role': 'system', 'content': enhanced_request['system'][0]['text']}]
                ollama_messages.extend(enhanced_request['messages'])
            else:
                ollama_messages = enhanced_request['messages']
        else:
            ollama_messages = messages

        payload = {
            "model": model,
            "messages": ollama_messages,
            "stream": False,
            "options": {"temperature": 0.7, "top_p": 0.9},
        }

        log_service_status("OLLAMA", "debug", f"Attempting connection to {self.ollama_url}/api/chat")
        
        # Use configured timeout values instead of hardcoded ones
        timeout = httpx.Timeout(timeout=LLM_TIMEOUT, connect=CONNECTION_TIMEOUT)
        
        async with httpx.AsyncClient(timeout=timeout) as client:
            log_service_status("OLLAMA", "debug", f"HTTPX client created, sending POST request")
            response = await client.post(f"{self.ollama_url}/api/chat", json=payload)
            log_service_status("OLLAMA", "debug", f"Response received with status: {response.status_code}")
            response.raise_for_status()
            data = response.json()
            return data.get("message", {}).get("content", "")

    @handle_llm_errors(
        operation_name="call_openai_llm"
    )
    async def call_openai_llm(
        self,
        messages: List[Dict[str, Any]],
        model: Optional[str] = None,
        api_url: Optional[str] = None,
        api_key: Optional[str] = None) -> str:
        """
        Asynchronously calls an OpenAI-compatible API.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content' keys
            model: Optional model name, defaults to configured default model
            api_url: Optional API URL, defaults to configured OpenAI base URL
            api_key: Optional API key, defaults to configured OpenAI API key
            
        Returns:
            str: The response content from the LLM
            
        Raises:
            Exception: If connection fails or API returns an error
        """
        model = model or self.default_model
        api_url = api_url or OPENAI_API_BASE_URL
        api_key = api_key or OPENAI_API_KEY

        if api_url and not api_url.endswith("/chat/completions"):
            api_url = f"{api_url.rstrip('/')}/chat/completions"

        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}
        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "max_tokens": OPENAI_API_MAX_TOKENS,
            "temperature": 0.7,
        }
        timeout = OPENAI_API_TIMEOUT

        # Configure optimized timeouts and connection pooling
        timeout = httpx.Timeout(
            timeout=OPENAI_API_TIMEOUT, connect=CONNECTION_TIMEOUT, read=READ_TIMEOUT, write=WRITE_TIMEOUT
        )

        limits = httpx.Limits(
            max_keepalive_connections=MAX_KEEPALIVE_CONNECTIONS,
            max_connections=CONNECTION_POOL_SIZE,
            keepalive_expiry=30.0)

        async with httpx.AsyncClient(timeout=timeout, limits=limits) as client:
            resp = await client.post(api_url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            return data.get("choices", [{}])[0].get("message", {}).get("content", "")

    @handle_llm_errors(
        operation_name="call_llm_stream"
    )
    async def call_llm_stream(
        self,
        messages: List[Dict[str, Any]],
        model: Optional[str] = None,
        api_url: Optional[str] = None,
        api_key: Optional[str] = None,
        stop_event=None,
        session_id: Optional[str] = None) -> AsyncGenerator[str, None]:
        """
        Streams tokens from an LLM API (Ollama or OpenAI) in real time.
        """
        model = model or self.default_model
        self.logger.debug(
            f"Starting LLM stream - use_ollama={self.use_ollama}, model={model}, session_id={session_id}"
        )
        log_service_status("LLM", "info", f"CALL_LLM_STREAM: use_ollama = {self.use_ollama}, model = {model}")

        if self.use_ollama:
            self.logger.debug("Using Ollama path for LLM streaming")
            log_service_status("LLM", "info", "CALL_LLM_STREAM: Using Ollama path")
            async for token in self.call_ollama_llm_stream(messages, model, stop_event, session_id):
                yield token
        else:
            self.logger.debug("Using OpenAI path for LLM streaming")
            log_service_status("LLM", "info", "CALL_LLM_STREAM: Using OpenAI path")
            async for token in self.call_openai_llm_stream(messages, model, api_url, api_key, stop_event, session_id):
                yield token

    async def call_ollama_llm_stream(
        self,
        messages: List[Dict[str, Any]],
        model: Optional[str] = None,
        stop_event=None,
        session_id: Optional[str] = None) -> AsyncGenerator[str, None]:
        """
        Asynchronously calls the Ollama API using the chat endpoint with streaming.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content' keys
            model: Optional model name, defaults to configured default model
            stop_event: Optional event to stop streaming
            session_id: Optional session identifier for tracking
            
        Yields:
            str: Individual tokens from the LLM response
            
        Raises:
            Exception: If connection fails or API returns an error
        """
        model = model or self.default_model
        
        payload = {
            "model": model,
            "messages": messages,
            "stream": True,
            "options": {"temperature": 0.7, "top_p": 0.9},
        }

        try:
            log_service_status("OLLAMA", "info", f"Starting Ollama stream for model {model}")
            
            # Use configured timeout values instead of hardcoded ones
            timeout = httpx.Timeout(timeout=LLM_TIMEOUT, connect=CONNECTION_TIMEOUT, read=READ_TIMEOUT, write=WRITE_TIMEOUT)
            
            async with httpx.AsyncClient(timeout=timeout) as client:
                log_service_status("OLLAMA", "debug", f"HTTPX client created for streaming, sending POST request")
                async with client.stream("POST", f"{self.ollama_url}/api/chat", json=payload) as response:
                    log_service_status("OLLAMA", "debug", f"Stream response received with status: {response.status_code}")
                    response.raise_for_status()
                    
                    async for line in response.aiter_lines():
                        if stop_event and stop_event.is_set():
                            log_service_status("OLLAMA", "info", "Stream stopped by stop event")
                            break
                            
                        if line.strip():
                            try:
                                data = json.loads(line)
                                if "message" in data and "content" in data["message"]:
                                    content = data["message"]["content"]
                                    if content:
                                        yield content
                                        
                                # Check if streaming is done
                                if data.get("done", False):
                                    log_service_status("OLLAMA", "info", "Ollama stream completed successfully")
                                    break
                                    
                            except json.JSONDecodeError:
                                # Skip malformed JSON lines
                                continue
                                
        except httpx.RequestError as e:
            log_service_status("OLLAMA", "failed", f"Connection to Ollama at {self.ollama_url} failed: {e}")
            raise ConnectionError(f"Cannot connect to Ollama service at {self.ollama_url}") from e
        except httpx.HTTPStatusError as e:
            log_service_status(
                "OLLAMA",
                "failed", 
                f"Ollama API returned an error: {e.response.status_code} - {e.response.text}")
            raise

    async def call_openai_llm_stream(
        self,
        messages: List[Dict[str, Any]],
        model: Optional[str] = None,
        api_url: Optional[str] = None,
        api_key: Optional[str] = None,
        stop_event=None,
        session_id: Optional[str] = None) -> AsyncGenerator[str, None]:
        """
        Asynchronously streams tokens from an OpenAI-compatible API with proper resource management.
        """
        from services.streaming_service import STREAM_SESSION_STOP

        model = model or self.default_model
        api_url = api_url or OPENAI_API_BASE_URL
        api_key = api_key or OPENAI_API_KEY

        if api_url and not api_url.endswith("/chat/completions"):
            api_url = f"{api_url.rstrip('/')}/chat/completions"

        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}
        payload = {
            "model": model,
            "messages": messages,
            "stream": True,
            "max_tokens": OPENAI_API_MAX_TOKENS,
            "temperature": 0.7,
        }
        timeout = OPENAI_API_TIMEOUT

        client = None
        try:
            client = httpx.AsyncClient(timeout=timeout)
            async with client.stream("POST", api_url, headers=headers, json=payload) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    # Check stop conditions
                    if (stop_event and stop_event.is_set()) or (session_id and STREAM_SESSION_STOP.get(session_id)):
                        log_service_status("OPENAI", "info", f"Stream stopped for session {session_id}")
                        break

                    if not line or not line.startswith("data: "):
                        continue

                    line_text = line[6:]
                    if line_text.strip() == "[DONE]":
                        log_service_status("OPENAI", "info", "Stream completed successfully")
                        break

                    try:
                        data = json.loads(line_text)
                        if (
                            (choices := data.get("choices"))
                            and (delta := choices[0].get("delta"))
                            and (content := delta.get("content"))
                        ):
                            yield content
                    except json.JSONDecodeError:
                        continue

        except httpx.RequestError as e:
            log_service_status("OPENAI", "failed", f"Streaming connection to OpenAI API failed: {e}")
            yield "Error: Cannot connect to OpenAI API"
        except Exception as e:
            log_service_status("OPENAI", "failed", f"OpenAI streaming failed: {e}")
            yield f"Error: {str(e)}"
        finally:
            # Ensure proper cleanup
            if client:
                await client.aclose()
            if session_id and session_id in STREAM_SESSION_STOP:
                STREAM_SESSION_STOP.pop(session_id, None)

    async def get_embeddings(self, text: str, model: Optional[str] = None) -> Optional[List[float]]:
        """
        Get embeddings for text using Ollama.
        """
        from config.config_unified import EMBEDDING_MODEL

        model = model or EMBEDDING_MODEL

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(f"{self.ollama_url}/api/embeddings", json={"model": model, "prompt": text})

                if response.status_code == 200:
                    result = response.json()
                    embeddings = result.get("embedding", [])
                    if embeddings:
                        log_service_status(
                            "embeddings", "info", f"Generated embeddings with dimension {len(embeddings)}"
                        )
                        return embeddings
                    else:
                        log_service_status("embeddings", "warning", "Empty embeddings returned")
                        return None
                else:
                    log_service_status(
                        "embeddings", "error", f"Ollama embeddings API returned status {response.status_code}"
                    )
                    return None

        except httpx.ConnectError:
            log_service_status("embeddings", "warning", f"Cannot connect to Ollama at {self.ollama_url}")
            return None
        except Exception as e:
            log_service_status("embeddings", "error", f"Error getting embeddings: {e}")
            return None


# Global LLM service instance
llm_service = LLMService()
llm_service.logger.info(f"LLM service instance created - service=llm_service, instance_id={id(llm_service)}")


# Export convenience functions for backward compatibility
async def call_llm(
    messages: List[Dict[str, Any]],
    model: Optional[str] = None,
    api_url: Optional[str] = None,
    api_key: Optional[str] = None) -> str:
    """Convenience function for LLM calls."""
    return await llm_service.call_llm(messages, model, api_url, api_key)


async def call_llm_stream(
    messages: List[Dict[str, Any]],
    model: Optional[str] = None,
    api_url: Optional[str] = None,
    api_key: Optional[str] = None,
    stop_event=None,
    session_id: Optional[str] = None) -> AsyncGenerator[str, None]:
    """Convenience function for LLM streaming."""
    import time
    current_time = int(time.time())
    llm_service.logger.info(f"LLM stream entry point called - model={model}, session_id={session_id}, timestamp={current_time}")
    log_service_status("LLM", "info", f"CALL_LLM_STREAM_ENTRY_POINT: Called at {current_time} with model={model}, session_id={session_id}")
    async for token in llm_service.call_llm_stream(messages, model, api_url, api_key, stop_event, session_id):
        llm_service.logger.debug(f"Token yielded - token={token}, session_id={session_id}")
        log_service_status("LLM", "debug", f"STANDALONE: Yielding token: '{token}'")
        yield token


async def get_embeddings(text: str, model: Optional[str] = None) -> Optional[List[float]]:
    """Convenience function for getting embeddings."""
    return await llm_service.get_embeddings(text, model)
