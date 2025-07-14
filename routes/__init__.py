"""
Routes module for the FastAPI backend.
"""

from .health import health_router
from .chat import chat_router
from .models import models_router
from .upload import upload_router
from .debug import debug_router
# from .gateway import gateway_router  # DISABLED - API Gateway removed
# from .memory import memory_router  # TODO: memory.py doesn't exist - causing import errors

__all__ = ["health_router", "chat_router", "models_router", "upload_router", "debug_router"]
# "memory_router" removed - routes/memory.py doesn't exist
# "gateway_router" removed - API Gateway disabled
