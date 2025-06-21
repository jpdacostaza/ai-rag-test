"""
Quick fix for /v1/models endpoint to make OpenWebUI work.
This patch replaces the broken /v1/models endpoint with a working one.
"""

from fastapi import FastAPI
from model_manager import refresh_model_cache, _model_cache
import logging

def patch_v1_models_endpoint(app: FastAPI):
    """Replace the broken /v1/models endpoint with a working one."""
    
    # Remove the existing broken endpoint
    routes_to_remove = []
    for route in app.routes:
        if hasattr(route, 'path') and route.path == '/v1/models':
            routes_to_remove.append(route)
    
    for route in routes_to_remove:
        app.routes.remove(route)
    
    # Add the new working endpoint
    @app.get("/v1/models")
    async def list_models_working():
        """
        OpenAI-compatible endpoint for model listing. Uses model_manager for reliable model fetching.
        """
        try:
            logging.info("[MODELS] Fetching models for OpenWebUI via /v1/models")
            
            # Refresh cache if needed
            await refresh_model_cache()
            
            # Return in OpenAI format
            result = {
                "object": "list",
                "data": _model_cache["data"]
            }
            
            logging.info(f"[MODELS] Returning {len(_model_cache['data'])} models to OpenWebUI")
            return result
            
        except Exception as e:
            logging.error(f"Error in /v1/models endpoint: {e}")
            # Fallback to empty list
            return {
                "object": "list", 
                "data": []
            }
    
    logging.info("[PATCH] Successfully patched /v1/models endpoint")
