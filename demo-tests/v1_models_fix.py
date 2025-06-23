"""
Working /v1/models endpoint for OpenWebUI compatibility.
This file contains a simple, working implementation.
"""

from fastapi import APIRouter
from model_manager import refresh_model_cache, _model_cache
import logging

# Create a router for the working v1 endpoints
v1_router = APIRouter(prefix="/v1", tags=["OpenAI Compatible"])

@v1_router.get("/models")
async def list_models_v1():
    """
    OpenAI-compatible endpoint for model listing.
    Uses the working model_manager for reliable model fetching.
    """
    try:
        logging.info("[V1/MODELS] Fetching models for OpenWebUI")
        
        # Refresh cache if needed using the working model_manager
        await refresh_model_cache()
        
        # Return in OpenAI format using the working cache
        result = {
            "object": "list",
            "data": _model_cache["data"]
        }
        
        logging.info(f"[V1/MODELS] Successfully returning {len(_model_cache['data'])} models")
        for model in _model_cache["data"]:
            logging.info(f"[V1/MODELS] Model available: {model.get('id', 'unknown')}")
        
        return result
        
    except Exception as e:
        logging.error(f"[V1/MODELS] Error in /v1/models endpoint: {e}")
        # Return empty list on error to prevent crashes
        return {
            "object": "list", 
            "data": []
        }
