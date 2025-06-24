"""
Routes module for the FastAPI backend.
"""
from .health import health_router
from .chat import chat_router
from .models import models_router

__all__ = ["health_router", "chat_router", "models_router"]
