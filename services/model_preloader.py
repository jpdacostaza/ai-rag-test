"""
Model Preloader Service
=======================

Ensures critical models are available at startup for OpenWebUI integration.
Downloads models if they don't exist locally.
"""

import asyncio
import logging
import time
from typing import List, Set

from config.config_unified import DEFAULT_MODEL, EMBEDDING_MODEL
from services.model_manager import ensure_model_available, refresh_model_cache
from core.unified_logging import log_service_status


class ModelPreloader:
    """Handles eager loading of essential models during startup."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.required_models: List[str] = []
        self.loaded_models: Set[str] = set()
        
    def add_required_models(self, models: List[str]) -> None:
        """Add models to the required list."""
        self.required_models.extend(models)
        
    async def preload_essential_models(self, timeout_per_model: int = 300) -> bool:
        """
        Preload all essential models for OpenWebUI integration.
        
        Args:
            timeout_per_model: Maximum time to wait for each model download (seconds)
            
        Returns:
            bool: True if all models loaded successfully, False otherwise
        """
        if not self.required_models:
            # Set default required models
            self.required_models = [
                DEFAULT_MODEL,  # Main conversation model
                "nomic-embed-text:latest",  # Embedding model for search
            ]
            
        log_service_status("MODEL_PRELOADER", "info", f"Starting preload of {len(self.required_models)} essential models")
        
        success_count = 0
        total_models = len(self.required_models)
        
        for model_name in self.required_models:
            start_time = time.time()
            log_service_status("MODEL_PRELOADER", "info", f"Checking model: {model_name}")
            
            try:
                # First refresh cache to see what's already available
                await refresh_model_cache()
                
                # Try to ensure model is available (will pull if needed)
                success = await asyncio.wait_for(
                    ensure_model_available(model_name, auto_pull=True),
                    timeout=timeout_per_model
                )
                
                elapsed = time.time() - start_time
                
                if success:
                    self.loaded_models.add(model_name)
                    success_count += 1
                    log_service_status("MODEL_PRELOADER", "ready", 
                                     f"Model {model_name} available ({elapsed:.1f}s)")
                else:
                    log_service_status("MODEL_PRELOADER", "warning", 
                                     f"Failed to load model {model_name} after {elapsed:.1f}s")
                    
            except asyncio.TimeoutError:
                log_service_status("MODEL_PRELOADER", "warning", 
                                 f"Timeout loading model {model_name} after {timeout_per_model}s")
            except Exception as e:
                log_service_status("MODEL_PRELOADER", "warning", 
                                 f"Error loading model {model_name}: {e}")
        
        # Final status
        if success_count == total_models:
            log_service_status("MODEL_PRELOADER", "ready", 
                             f"All {total_models} models loaded successfully")
            return True
        else:
            log_service_status("MODEL_PRELOADER", "warning", 
                             f"Loaded {success_count}/{total_models} models")
            return False
    
    async def verify_models_available(self) -> dict:
        """
        Verify that all required models are available in Ollama.
        
        Returns:
            dict: Status information about model availability
        """
        await refresh_model_cache()
        
        from services.model_manager import _model_cache
        available_models = {model["id"] for model in _model_cache.get("data", [])}
        
        status = {
            "required_models": self.required_models,
            "available_models": list(available_models),
            "missing_models": [m for m in self.required_models if m not in available_models],
            "loaded_count": len(self.loaded_models),
            "total_required": len(self.required_models)
        }
        
        return status


# Global instance
model_preloader = ModelPreloader()


async def initialize_models_for_openwebui() -> bool:
    """
    Initialize all models required for OpenWebUI integration.
    This should be called during application startup.
    
    Returns:
        bool: True if initialization successful
    """
    log_service_status("MODEL_INIT", "info", "Initializing models for OpenWebUI integration")
    
    # Add essential models
    essential_models = [
        DEFAULT_MODEL,  # Main conversation model from config
        "nomic-embed-text:latest",  # Embedding model
    ]
    
    # Add any additional models based on environment
    import os
    extra_models = os.getenv("PRELOAD_MODELS", "").split(",")
    extra_models = [m.strip() for m in extra_models if m.strip()]
    
    all_models = essential_models + extra_models
    model_preloader.add_required_models(all_models)
    
    # Preload with reasonable timeout (5 minutes per model)
    success = await model_preloader.preload_essential_models(timeout_per_model=300)
    
    if success:
        log_service_status("MODEL_INIT", "ready", "All models initialized for OpenWebUI")
    else:
        log_service_status("MODEL_INIT", "warning", "Some models failed to initialize")
    
    return success


async def get_model_status() -> dict:
    """Get current model status for health checks."""
    return await model_preloader.verify_models_available()
