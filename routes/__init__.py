"""
Routes module for the FastAPI backend.
"""
from .health import health_router
from .chat import chat_router
from .models import models_router
from .upload import upload_router
from .pipeline import pipeline_router
from .debug import debug_router

__all__ = ["health_router", "chat_router", "models_router", "upload_router", "pipeline_router", "debug_router"]
