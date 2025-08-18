"""
Model management endpoints.
"""

import time
import logging
from typing import Dict

import httpx
from fastapi import APIRouter

from config.config_unified import OLLAMA_BASE_URL, MODEL_CACHE_TTL
from core.unified_logging import log_service_status
from models.models import ModelListResponse, ModelInfo
from utilities.error_patterns import handle_api_errors, handle_service_errors, ErrorHandlerConfig

models_router = APIRouter()

# Improved model cache with proper TTL handling
class ModelCache:
    def __init__(self, ttl: int):
        self.data = []
        self.last_updated = 0
        self.ttl = ttl
    
    def is_expired(self) -> bool:
        """Check if cache has expired."""
        return (time.time() - self.last_updated) >= self.ttl
    
    def update(self, data: list):
        """Update cache with new data."""
        self.data = data
        self.last_updated = time.time()
    
    def get(self) -> list:
        """Get cached data if not expired, otherwise return empty list."""
        return self.data if not self.is_expired() else []
    
    def clear(self):
        """Clear the cache."""
        self.data = []
        self.last_updated = 0

_model_cache = ModelCache(MODEL_CACHE_TTL)


@handle_service_errors(
    operation_name="refresh_model_cache",
    config=ErrorHandlerConfig(
        max_retries=2,
        log_traceback=True)
)
async def refresh_model_cache(force: bool = False):
    """Refresh the model cache from Ollama."""
    global _model_cache

    # Check if refresh is needed using improved cache logic
    if not force and not _model_cache.is_expired():
        log_service_status("MODELS", "info", "Model cache is still fresh, skipping refresh")
        cached_data = _model_cache.get()
        return [model["id"] for model in cached_data] if cached_data else []

    ollama_url = OLLAMA_BASE_URL

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(f"{ollama_url}/api/tags")

        if response.status_code == 200:
            data = response.json()
            raw_models = data.get("models", [])

            # Transform models to OpenAI-compatible format
            models = []
            for model in raw_models:
                openai_model = {
                    "id": model.get("name", "unknown"),
                    "object": "model",
                    "created": int(time.time()),
                    "owned_by": "ollama",
                    "permission": [],
                    "root": model.get("name", "unknown"),
                    "parent": None,
                    # Store original Ollama data for internal use
                    "_ollama_data": model,
                }
                models.append(openai_model)

            # Update cache using improved cache logic
            _model_cache.update(models)

            log_service_status("MODELS", "ready", f"Refreshed model cache with {len(models)} models")
            return [model["id"] for model in models]  # Return just the model names for compatibility
        else:
            log_service_status("MODELS", "warning", f"Failed to fetch models: HTTP {response.status_code}")
            cached_data = _model_cache.get()
            return [model["id"] for model in cached_data]  # Return cached data on failure


@models_router.get("/v1/models")
@handle_api_errors(
    operation_name="list_models")
async def list_models():
    """
    OpenAI-compatible endpoint for model listing. Dynamically fetches available models from Ollama with caching.
    """
    # Always check ollama for latest models (reduced cache dependency)
    await refresh_model_cache(force=True)

    # Temporary workaround: ensure Mistral model is included if it exists in Ollama
    models_data = _model_cache.get().copy()
    mistral_exists = any(model["id"] == "mistral:7b-instruct-v0.3-q4_k_m" for model in models_data)
    logging.info(f"[MODELS DEBUG] Cache has {len(models_data)} models, Mistral exists: {mistral_exists}")
    logging.info(f"[MODELS DEBUG] Using OLLAMA_BASE_URL: {OLLAMA_BASE_URL}")

    if not mistral_exists:
        # Check if Mistral model exists in Ollama directly using error handling
        @handle_service_errors(
            operation_name="check_mistral_model",
            config=ErrorHandlerConfig(log_traceback=False)
        )
        async def check_mistral_model():
            logging.info(f"[MODELS DEBUG] Checking Ollama at {OLLAMA_BASE_URL}/api/tags")
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
                logging.info(f"[MODELS DEBUG] Ollama response status: {resp.status_code}")
                if resp.status_code == 200:
                    ollama_models = resp.json().get("models", [])
                    logging.info(f"[MODELS DEBUG] Found {len(ollama_models)} models in Ollama")
                    for model in ollama_models:
                        logging.info(f"[MODELS DEBUG] Ollama model: {model['name']}")
                        if model["name"] == "mistral:7b-instruct-v0.3-q4_k_m":
                            models_data.append(
                                {
                                    "id": "mistral:7b-instruct-v0.3-q4_k_m",
                                    "object": "model",
                                    "created": int(time.time()),
                                    "owned_by": "ollama",
                                    "permission": [],
                                }
                            )
                            logging.info("[MODELS DEBUG] Added Mistral model to response")
                            break

        await check_mistral_model()

    return {"object": "list", "data": models_data}
