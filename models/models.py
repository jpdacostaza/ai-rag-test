"""
Pydantic models for the backend API.
"""

from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field
from enum import Enum

class MessageRole(str, Enum):
    """Message role enumeration."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

class OpenAIMessage(BaseModel):
    """OpenAI-compatible message format."""
    role: MessageRole
    content: str
    name: Optional[str] = None

class ChatRequest(BaseModel):
    """Chat request model."""
    message: str = Field(..., description="The user's message")
    conversation_id: Optional[str] = Field(None, description="Optional conversation ID for context")
    model: Optional[str] = Field(None, description="Model to use for the chat")
    system_prompt: Optional[str] = Field(None, description="Custom system prompt")
    max_tokens: Optional[int] = Field(None, description="Maximum tokens to generate")
    temperature: Optional[float] = Field(None, description="Temperature for generation")
    stream: Optional[bool] = Field(False, description="Whether to stream the response")

class OpenAIChatRequest(BaseModel):
    """OpenAI-compatible chat request."""
    model: str = Field(..., description="Model to use")
    messages: List[OpenAIMessage] = Field(..., description="List of messages")
    max_tokens: Optional[int] = Field(None, description="Maximum tokens to generate")
    temperature: Optional[float] = Field(0.7, description="Temperature for generation")
    top_p: Optional[float] = Field(1.0, description="Top-p sampling")
    stream: Optional[bool] = Field(False, description="Whether to stream the response")
    stop: Optional[Union[str, List[str]]] = Field(None, description="Stop sequences")

class ChatResponse(BaseModel):
    """Chat response model."""
    message: str = Field(..., description="The assistant's response")
    conversation_id: Optional[str] = Field(None, description="Conversation ID")
    model: Optional[str] = Field(None, description="Model used for the response")
    timestamp: Optional[str] = Field(None, description="Response timestamp")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

class ModelInfo(BaseModel):
    """Model information."""
    id: str = Field(..., description="Model identifier")
    object: str = Field("model", description="Object type")
    created: Optional[int] = Field(None, description="Creation timestamp")
    owned_by: Optional[str] = Field("ollama", description="Model owner")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional model details")

class ModelListResponse(BaseModel):
    """Model list response."""
    object: str = Field("list", description="Object type")
    data: List[ModelInfo] = Field(..., description="List of available models")

class HealthStatus(str, Enum):
    """Health status enumeration."""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"
    UNKNOWN = "unknown"

class ServiceHealth(BaseModel):
    """Individual service health."""
    status: HealthStatus
    message: Optional[str] = None
    response_time: Optional[float] = None
    details: Optional[Dict[str, Any]] = None

class HealthResponse(BaseModel):
    """Basic health response."""
    status: HealthStatus
    timestamp: str
    version: Optional[str] = None

class DetailedHealthResponse(BaseModel):
    """Detailed health response with service breakdown."""
    status: HealthStatus
    timestamp: str
    version: Optional[str] = None
    services: Dict[str, ServiceHealth]
    uptime: Optional[float] = None

class ErrorResponse(BaseModel):
    """Error response model."""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")
    type: Optional[str] = Field(None, description="Error type")
    code: Optional[int] = Field(None, description="Error code")

class UploadResponse(BaseModel):
    """File upload response."""
    filename: str = Field(..., description="Uploaded filename")
    size: int = Field(..., description="File size in bytes")
    content_type: str = Field(..., description="File content type")
    status: str = Field(..., description="Upload status")
    message: Optional[str] = Field(None, description="Additional message")

class MemoryRequest(BaseModel):
    """Memory operation request."""
    content: str = Field(..., description="Content to store or query")
    conversation_id: Optional[str] = Field(None, description="Conversation ID")
    operation: Optional[str] = Field("store", description="Operation type (store, query, delete)")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

class MemoryResponse(BaseModel):
    """Memory operation response."""
    status: str = Field(..., description="Operation status")
    message: str = Field(..., description="Response message")
    data: Optional[Dict[str, Any]] = Field(None, description="Response data")
    conversation_id: Optional[str] = Field(None, description="Conversation ID")

class DebugInfo(BaseModel):
    """Debug information."""
    component: str = Field(..., description="Component name")
    status: str = Field(..., description="Component status")
    details: Dict[str, Any] = Field(..., description="Detailed information")
    timestamp: str = Field(..., description="Debug timestamp")

class DebugResponse(BaseModel):
    """Debug response."""
    system_info: Dict[str, Any] = Field(..., description="System information")
    services: List[DebugInfo] = Field(..., description="Service debug information")
    timestamp: str = Field(..., description="Debug timestamp")
