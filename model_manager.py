from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional, Dict, Any
import os
import shutil
import httpx
import time
import asyncio
import logging

router = APIRouter(tags=["Model Management"])

# --- Configuration ---
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
CUSTOM_MODEL_DIR = os.path.abspath("storage/models")

# --- Model Cache ---
_model_cache: Dict[str, Any] = {
    "data": [],
    "last_updated": 0,
    "ttl": 300  # 5 minutes
}

# --- Helper Functions ---

async def refresh_model_cache(force: bool = False) -> None:
    """
    Refreshes the model cache from the Ollama API and local directories.
    """
    global _model_cache
    current_time = time.time()
    if not force and (current_time - _model_cache["last_updated"] < _model_cache["ttl"]):
        return

    logging.info("[MODELS] Refreshing model cache...")
    ollama_models = []
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
            resp.raise_for_status()
            models_data = resp.json().get("models", [])
            ollama_models = [
                {
                    "id": model["name"],
                    "object": "model",
                    "created": int(time.mktime(time.strptime(model["modified_at"], "%Y-%m-%dT%H:%M:%S.%f%z"))),
                    "owned_by": "ollama"
                } for model in models_data
            ]
        logging.info(f"[MODELS] Successfully fetched {len(ollama_models)} models from Ollama.")
    except httpx.RequestError as e:
        logging.error(f"[MODELS] Failed to connect to Ollama to refresh models: {e}")
    except Exception as e:
        logging.error(f"[MODELS] An unexpected error occurred while fetching Ollama models: {e}")

    # Combine with local models (if any)
    # custom_models = list_models_in_dir(CUSTOM_MODEL_DIR) # You can extend this
    
    _model_cache["data"] = ollama_models
    _model_cache["last_updated"] = time.time()

async def ensure_model_available(model_name: str) -> bool:
    """
    Checks if a model is available in the cache. Refreshes if cache is stale.
    """
    await refresh_model_cache() # Refresh if stale
    return any(model["id"] == model_name for model in _model_cache["data"])

# --- API Endpoints ---

@router.on_event("startup")
async def on_startup():
    """Initial model cache population on startup."""
    await refresh_model_cache(force=True)

@router.get("/models", response_model=Dict[str, Any])
async def list_available_models():
    """
    Returns a list of available models, compatible with the OpenAI API format.
    Refreshes the cache if it is expired.
    """
    await refresh_model_cache()
    return {
        "object": "list",
        "data": _model_cache["data"]
    }

@router.post("/models/refresh")
async def force_refresh_models():
    """Forces an immediate refresh of the model cache."""
    await refresh_model_cache(force=True)
    return {"status": "refreshed", "models_found": len(_model_cache["data"])}

@router.get("/models/{model_name}")
async def get_model_details(model_name: str):
    """Get details about a specific model from the cache."""
    await refresh_model_cache()
    model_info = next((m for m in _model_cache["data"] if m["id"] == model_name), None)
    if not model_info:
        raise HTTPException(status_code=404, detail=f"Model '{model_name}' not found.")
    return model_info

@router.delete("/models/{model_name}")
async def delete_model(model_name: str):
    """Deletes a model from Ollama."""
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.request("DELETE", f"{OLLAMA_BASE_URL}/api/delete", json={"name": model_name})
            resp.raise_for_status()
        await refresh_model_cache(force=True) # Refresh cache after deletion
        return {"status": "deleted", "model": model_name}
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise HTTPException(status_code=404, detail=f"Model '{model_name}' not found in Ollama.")
        else:
            raise HTTPException(status_code=500, detail=f"Failed to delete model from Ollama: {e.response.text}")
    except httpx.RequestError as e:
        raise HTTPException(status_code=500, detail=f"Failed to connect to Ollama: {e}")
