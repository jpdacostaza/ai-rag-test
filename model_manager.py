import logging
import os
import time
from typing import Any
from typing import Dict

import httpx
from fastapi import APIRouter
from fastapi import HTTPException

router = APIRouter(tags=["Model Management"])

# --- Configuration ---
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
CUSTOM_MODEL_DIR = os.path.abspath("storage/models")

# --- Model Cache ---
_model_cache: Dict[str, Any] = {"data": [], "last_updated": 0, "ttl": 300}  # 5 minutes

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
                    "created": int(time.time()),  # Use current timestamp instead of parsing
                    "owned_by": "ollama",
                }
                for model in models_data
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


async def pull_model(model_name: str) -> bool:
    """
    Pull a model from Ollama registry if it's not available locally.
    Returns True if model is successfully pulled or already available.
    """
    try:
        logging.info(f"[MODELS] Pulling model {model_name} from Ollama registry...")
        async with httpx.AsyncClient(timeout=300.0) as client:  # 5 minute timeout for model downloads
            resp = await client.post(
                f"{OLLAMA_BASE_URL}/api/pull", 
                json={"name": model_name},
                timeout=300.0
            )
            resp.raise_for_status()
            logging.info(f"[MODELS] Successfully pulled model {model_name}")
            return True
    except httpx.RequestError as e:
        logging.error(f"[MODELS] Failed to connect to Ollama for model pull: {e}")
        return False
    except httpx.HTTPStatusError as e:
        logging.error(f"[MODELS] Model pull failed with HTTP {e.response.status_code}: {e.response.text}")
        return False
    except Exception as e:
        logging.error(f"[MODELS] Unexpected error during model pull: {e}")
        return False


async def ensure_model_available(model_name: str, auto_pull: bool = True) -> bool:
    """
    Checks if a model is available in the cache. Refreshes if cache is stale.
    If auto_pull is True and the model is not found, attempts to pull it from Ollama registry.
    """
    await refresh_model_cache()  # Refresh if stale
    model_exists = any(model["id"] == model_name for model in _model_cache["data"])
    
    if not model_exists and auto_pull:
        logging.info(f"[MODELS] Model {model_name} not found locally, attempting to pull...")
        pull_success = await pull_model(model_name)
        if pull_success:
            # Refresh cache after successful pull
            await refresh_model_cache(force=True)
            model_exists = any(model["id"] == model_name for model in _model_cache["data"])
            if model_exists:
                logging.info(f"[MODELS] Model {model_name} is now available after pull")
            else:
                logging.warning(f"[MODELS] Model {model_name} pull completed but model not found in cache")
        else:
            logging.error(f"[MODELS] Failed to pull model {model_name}")
    
    return model_exists


# --- API Endpoints ---

async def initialize_model_cache():
    """Initialize model cache on startup. Called from application lifespan."""
    await refresh_model_cache(force=True)


@router.get("/models", response_model=Dict[str, Any])
async def list_available_models():
    """
    Returns a list of available models, compatible with the OpenAI API format.
    Refreshes the cache if it is expired.
    """
    await refresh_model_cache()
    return {"object": "list", "data": _model_cache["data"]}


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
            resp = await client.request(
                "DELETE", f"{OLLAMA_BASE_URL}/api/delete", json={"name": model_name}            )
            resp.raise_for_status()
        await refresh_model_cache(force=True)  # Refresh cache after deletion
        return {"status": "deleted", "model": model_name}
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise HTTPException(status_code=404, detail=f"Model '{model_name}' not found in Ollama.")
        else:
            raise HTTPException(
                status_code=500, detail=f"Failed to delete model from Ollama: {e.response.text}"
            )
    except httpx.RequestError as e:
        raise HTTPException(status_code=500, detail=f"Failed to connect to Ollama: {e}")


@router.post("/models/{model_name}/pull")
async def pull_model_endpoint(model_name: str):
    """Manually pull a model from Ollama registry."""
    try:
        success = await pull_model(model_name)
        if success:
            await refresh_model_cache(force=True)  # Refresh cache after pull
            return {
                "status": "success", 
                "message": f"Model {model_name} pulled successfully",
                "model": model_name
            }
        else:
            raise HTTPException(
                status_code=500, 
                detail=f"Failed to pull model {model_name} from Ollama registry"
            )
    except Exception as e:
        logging.error(f"[MODELS] Error in pull endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Error pulling model: {str(e)}")


@router.post("/models/ensure-default")
async def ensure_default_model():
    """Ensure the default model is available, pulling it if necessary."""
    default_model = os.getenv("DEFAULT_MODEL", "llama3.2:3b")
    try:
        is_available = await ensure_model_available(default_model, auto_pull=True)
        if is_available:
            return {
                "status": "success",
                "message": f"Default model {default_model} is available",
                "model": default_model,
                "pulled": True
            }
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to ensure default model {default_model} is available"
            )
    except Exception as e:
        logging.error(f"[MODELS] Error ensuring default model: {e}")
        raise HTTPException(status_code=500, detail=f"Error ensuring default model: {str(e)}")
