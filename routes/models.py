"""
Model management endpoints.
"""

import time
import logging
from typing import Dict

import httpx
from fastapi import APIRouter

from config import OLLAMA_BASE_URL, MODEL_CACHE_TTL
from human_logging import log_service_status
from models import ModelListResponse, ModelInfo

models_router = APIRouter()

# Model cache
_model_cache: Dict = {"data": [], "last_updated": 0, "ttl": MODEL_CACHE_TTL}


async def refresh_model_cache(force: bool = False):
    """Refresh the model cache from Ollama."""
    global _model_cache

    current_time = time.time()
    # Check if refresh is needed
    if not force and (current_time - _model_cache["last_updated"]) < _model_cache["ttl"]:
        log_service_status("MODELS", "info", "Model cache is still fresh, skipping refresh")
        return [model["id"] for model in _model_cache["data"]] if _model_cache["data"] else []

    try:
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

                # Update cache
                _model_cache["data"] = models
                _model_cache["last_updated"] = current_time

                log_service_status("MODELS", "ready", f"Refreshed model cache with {len(models)} models")
                return [model["id"] for model in models]  # Return just the model names for compatibility
            else:
                log_service_status("MODELS", "warning", f"Failed to fetch models: HTTP {response.status_code}")
                return [model["id"] for model in _model_cache["data"]]  # Return cached data on failure
    except Exception as e:
        log_service_status("MODELS", "warning", f"Error refreshing model cache: {e}")
        return [model["id"] for model in _model_cache["data"]] if _model_cache["data"] else []


@models_router.get("/v1/models")
async def list_models():
    """
    OpenAI-compatible endpoint for model listing. Dynamically fetches available models from Ollama with caching.
    """
    # Check if cache is still valid
    current_time = time.time()
    if current_time - _model_cache["last_updated"] > _model_cache["ttl"]:
        # Cache expired, refresh
        await refresh_model_cache()

    # Temporary workaround: ensure Mistral model is included if it exists in Ollama
    models_data = _model_cache["data"].copy()
    mistral_exists = any(model["id"] == "mistral:7b-instruct-v0.3-q4_k_m" for model in models_data)
    logging.info(f"[MODELS DEBUG] Cache has {len(models_data)} models, Mistral exists: {mistral_exists}")
    logging.info(f"[MODELS DEBUG] Using OLLAMA_BASE_URL: {OLLAMA_BASE_URL}")

    if not mistral_exists:
        # Check if Mistral model exists in Ollama directly
        try:
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
        except Exception as e:
            logging.warning(f"Failed to check Ollama for Mistral model: {e}")

    return {"object": "list", "data": models_data}
