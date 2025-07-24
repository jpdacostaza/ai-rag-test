"""
Models package for the backend API.
"""

from .models import (
    # Message and Chat models
    MessageRole,
    OpenAIMessage,
    ChatRequest,
    OpenAIChatRequest,
    ChatResponse,
    
    # Model management
    ModelInfo,
    ModelListResponse,
    
    # Health monitoring
    HealthStatus,
    ServiceHealth,
    HealthResponse,
    DetailedHealthResponse,
    
    # Error handling
    ErrorResponse,
    
    # File upload
    UploadResponse,
    
    # Memory operations
    MemoryRequest,
    MemoryResponse,
    
    # Debug information
    DebugInfo,
    DebugResponse,
)

__all__ = [
    # Message and Chat models
    "MessageRole",
    "OpenAIMessage", 
    "ChatRequest",
    "OpenAIChatRequest",
    "ChatResponse",
    
    # Model management
    "ModelInfo",
    "ModelListResponse",
    
    # Health monitoring
    "HealthStatus",
    "ServiceHealth",
    "HealthResponse",
    "DetailedHealthResponse",
    
    # Error handling
    "ErrorResponse",
    
    # File upload
    "UploadResponse",
    
    # Memory operations
    "MemoryRequest",
    "MemoryResponse",
    
    # Debug information
    "DebugInfo",
    "DebugResponse",
]
