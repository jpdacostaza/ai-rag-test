"""
LLM service for calling Ollama and OpenAI APIs.
"""

import asyncio
import json
import logging
import time
from typing import AsyncGenerator, List, Dict, Any, Optional

import httpx
from config import (
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
    MAX_KEEPALIVE_CONNECTIONS,
)
from human_logging import log_service_status


class LLMService:
    """Service for handling LLM API calls."""

    def __init__(self):
        """Initializes the LLMService with configuration from config.py."""
        self.default_model = DEFAULT_MODEL
        self.ollama_url = OLLAMA_BASE_URL
        self.use_ollama = USE_OLLAMA

    async def call_llm(
        self,
        messages: List[Dict[str, Any]],
        model: Optional[str] = None,
        api_url: Optional[str] = None,
        api_key: Optional[str] = None,
    ) -> str:
        """
        Calls an LLM API (Ollama or OpenAI) with the provided messages and returns the response.
        """
        model = model or self.default_model

        if self.use_ollama:
            return await self.call_ollama_llm(messages, model)
        else:
            return await self.call_openai_llm(messages, model, api_url, api_key)

    async def call_ollama_llm(self, messages: List[Dict[str, Any]], model: Optional[str] = None) -> str:
        """
        Asynchronously calls the Ollama API using the chat endpoint for better control.
        """
        model = model or self.default_model

        # Debug logging to see what messages are being sent
        logging.debug(f"[DEBUG] Sending {len(messages)} messages to Ollama model {model}")
        for i, msg in enumerate(messages):
            logging.debug(f"[DEBUG] Message {i}: role='{msg.get('role')}', content='{msg.get('content', '')[:100]}...'")

        # Use Ollama's chat endpoint which provides better control over system prompts
        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": 0.7, "top_p": 0.9},
        }
        timeout = LLM_TIMEOUT

        try:
            # Configure optimized timeouts and connection pooling
            timeout = httpx.Timeout(
                timeout=LLM_TIMEOUT, connect=CONNECTION_TIMEOUT, read=READ_TIMEOUT, write=WRITE_TIMEOUT
            )

            limits = httpx.Limits(
                max_keepalive_connections=MAX_KEEPALIVE_CONNECTIONS,
                max_connections=CONNECTION_POOL_SIZE,
                keepalive_expiry=30.0,
            )

            async with httpx.AsyncClient(timeout=timeout, limits=limits) as client:
                response = await client.post(f"{self.ollama_url}/api/chat", json=payload)
                response.raise_for_status()
                data = response.json()
                llm_response = data.get("message", {}).get("content", "")
                logging.debug(f"[DEBUG] Ollama response length: {len(llm_response)} chars")
                logging.debug(f"[DEBUG] Ollama response content: '{llm_response[:200]}...'")
                return llm_response
        except httpx.RequestError as e:
            log_service_status("OLLAMA", "failed", f"Connection to Ollama at {self.ollama_url} failed: {e}")
            raise Exception(f"Cannot connect to Ollama service at {self.ollama_url}") from e
        except httpx.HTTPStatusError as e:
            log_service_status(
                "OLLAMA",
                "failed",
                f"Ollama API returned an error: {e.response.status_code} - {e.response.text}",
            )
            raise

    async def call_openai_llm(
        self,
        messages: List[Dict[str, Any]],
        model: Optional[str] = None,
        api_url: Optional[str] = None,
        api_key: Optional[str] = None,
    ) -> str:
        """
        Asynchronously calls an OpenAI-compatible API.
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

        try:
            # Configure optimized timeouts and connection pooling
            timeout = httpx.Timeout(
                timeout=OPENAI_API_TIMEOUT, connect=CONNECTION_TIMEOUT, read=READ_TIMEOUT, write=WRITE_TIMEOUT
            )

            limits = httpx.Limits(
                max_keepalive_connections=MAX_KEEPALIVE_CONNECTIONS,
                max_connections=CONNECTION_POOL_SIZE,
                keepalive_expiry=30.0,
            )

            async with httpx.AsyncClient(timeout=timeout, limits=limits) as client:
                resp = await client.post(api_url, headers=headers, json=payload)
                resp.raise_for_status()
                data = resp.json()
                return data.get("choices", [{}])[0].get("message", {}).get("content", "")
        except httpx.RequestError as e:
            log_service_status("OPENAI", "failed", f"Connection to OpenAI API at {api_url} failed: {e}")
            raise Exception(f"Cannot connect to OpenAI service at {api_url}") from e
        except httpx.HTTPStatusError as e:
            log_service_status(
                "OPENAI",
                "failed",
                f"OpenAI API returned an error: {e.response.status_code} - {e.response.text}",
            )
            raise

    async def call_llm_stream(
        self,
        messages: List[Dict[str, Any]],
        model: Optional[str] = None,
        api_url: Optional[str] = None,
        api_key: Optional[str] = None,
        stop_event=None,
        session_id: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        """
        Streams tokens from an LLM API (Ollama or OpenAI) in real time.
        """
        model = model or self.default_model

        if self.use_ollama:
            async for token in self.call_ollama_llm_stream(messages, model, stop_event, session_id):
                yield token
        else:
            async for token in self.call_openai_llm_stream(messages, model, api_url, api_key, stop_event, session_id):
                yield token

    async def call_ollama_llm_stream(
        self,
        messages: List[Dict[str, Any]],
        model: Optional[str] = None,
        stop_event=None,
        session_id: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        """
        Asynchronously streams tokens from the Ollama API with proper resource management.
        """
        from services.streaming_service import STREAM_SESSION_STOP

        model = model or self.default_model
        prompt = "\n".join(f"{msg.get('role', 'user').capitalize()}: {msg.get('content', '')}" for msg in messages)
        payload = {"model": model, "messages": messages, "stream": True}
        timeout = LLM_TIMEOUT

        client = None
        try:
            client = httpx.AsyncClient(timeout=timeout)
            async with client.stream("POST", f"{self.ollama_url}/api/chat", json=payload) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    # Check stop conditions
                    if (stop_event and stop_event.is_set()) or (session_id and STREAM_SESSION_STOP.get(session_id)):
                        log_service_status("OLLAMA", "info", f"Stream stopped for session {session_id}")
                        break

                    if not line:
                        continue

                    try:
                        data = json.loads(line)
                        if (
                            (choices := data.get("choices"))
                            and (delta := choices[0].get("delta"))
                            and (content := delta.get("content"))
                        ):
                            yield content
                        if data.get("done"):
                            log_service_status("OLLAMA", "info", "Stream completed successfully")
                            break
                    except json.JSONDecodeError:
                        continue

        except httpx.RequestError as e:
            log_service_status("OLLAMA", "failed", f"Streaming connection to Ollama failed: {e}")
            yield "Error: Cannot connect to Ollama service"
        except Exception as e:
            log_service_status("OLLAMA", "failed", f"Ollama streaming failed: {e}")
            yield f"Error: {str(e)}"
        finally:
            # Ensure proper cleanup
            if client:
                await client.aclose()
            if session_id and session_id in STREAM_SESSION_STOP:
                STREAM_SESSION_STOP.pop(session_id, None)

    async def call_openai_llm_stream(
        self,
        messages: List[Dict[str, Any]],
        model: Optional[str] = None,
        api_url: Optional[str] = None,
        api_key: Optional[str] = None,
        stop_event=None,
        session_id: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
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
        from config import EMBEDDING_MODEL

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


# Export convenience functions for backward compatibility
async def call_llm(
    messages: List[Dict[str, Any]],
    model: Optional[str] = None,
    api_url: Optional[str] = None,
    api_key: Optional[str] = None,
) -> str:
    """Convenience function for LLM calls."""
    return await llm_service.call_llm(messages, model, api_url, api_key)


async def call_llm_stream(
    messages: List[Dict[str, Any]],
    model: Optional[str] = None,
    api_url: Optional[str] = None,
    api_key: Optional[str] = None,
    stop_event=None,
    session_id: Optional[str] = None,
) -> AsyncGenerator[str, None]:
    """Convenience function for LLM streaming."""
    async for token in llm_service.call_llm_stream(messages, model, api_url, api_key, stop_event, session_id):
        yield token


async def get_embeddings(text: str, model: Optional[str] = None) -> Optional[List[float]]:
    """Convenience function for getting embeddings."""
    return await llm_service.get_embeddings(text, model)
