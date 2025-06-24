"""
Pydantic models and request/response schemas for the FastAPI backend.
"""
from pydantic import BaseModel
from typing import Dict, List, Optional, Union, Any
from datetime import datetime

# Chat models
class ChatRequest(BaseModel):
    user_id: str
    message: str

class ChatResponse(BaseModel):
    response: str

# OpenAI-compatible models
class OpenAIMessage(BaseModel):
    role: str
    content: Union[str, List[Dict[str, Any]]]

class OpenAIChatRequest(BaseModel):
    model: str
    messages: List[OpenAIMessage]
    stream: Optional[bool] = False
    max_tokens: Optional[int] = 4096
    temperature: Optional[float] = 0.7
    user: Optional[str] = None

class OpenAIChoice(BaseModel):
    index: int
    message: OpenAIMessage
    finish_reason: str

class OpenAIChatResponse(BaseModel):
    id: str
    object: str
    created: int
    model: str
    choices: List[OpenAIChoice]

# Streaming models
class StreamChoice(BaseModel):
    index: int
    delta: Dict[str, str]
    finish_reason: Optional[str] = None

class StreamResponse(BaseModel):
    id: str
    object: str
    created: int
    model: str
    choices: List[StreamChoice]

# Model listing
class ModelInfo(BaseModel):
    id: str
    object: str = "model"
    created: int
    owned_by: str = "ollama"
    permission: List = []
    root: Optional[str] = None
    parent: Optional[str] = None

class ModelListResponse(BaseModel):
    object: str = "list"
    data: List[ModelInfo]

# Memory and learning models
class MemoryRequest(BaseModel):
    user_id: str
    query: str
    limit: Optional[int] = 3
    threshold: Optional[float] = 0.7

class MemoryResponse(BaseModel):
    memories: List[Dict[str, Any]]
    count: int
    user_id: str
    query: str

class LearningRequest(BaseModel):
    user_id: str
    conversation_id: Optional[str] = None
    user_message: str
    assistant_response: str
    response_time: Optional[float] = 1.0
    tools_used: Optional[List[str]] = []
    source: Optional[str] = "api"

class LearningResponse(BaseModel):
    status: str
    result: Dict[str, Any]
    user_id: str
    source: str

# Pipeline models
class PipelineInfo(BaseModel):
    id: str
    name: str
    type: str
    description: str
    author: str
    version: str
    object: Optional[str] = "pipeline"
    author_url: Optional[str] = None
    license: Optional[str] = "MIT"
    requirements: Optional[List[str]] = []
    url: Optional[str] = None
    meta: Optional[Dict[str, Any]] = None

class PipelineListResponse(BaseModel):
    data: List[PipelineInfo]

# Health check models
class ServiceHealth(BaseModel):
    status: str
    available: bool
    message: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

class DatabaseHealth(BaseModel):
    redis: ServiceHealth
    chromadb: ServiceHealth
    embeddings: ServiceHealth

class HealthResponse(BaseModel):
    status: str
    summary: str
    databases: DatabaseHealth
    cache: Optional[Dict[str, Any]] = None

class DetailedHealthResponse(BaseModel):
    status: str
    timestamp: str
    overall_status: str
    services: Dict[str, Dict[str, Any]]
    summary: Dict[str, int]

# Error models
class ErrorDetail(BaseModel):
    type: str
    code: int
    message: str
    details: Optional[Any] = None
    request_id: Optional[str] = None
    timestamp: str

class ErrorResponse(BaseModel):
    error: ErrorDetail

# Admin models
class CacheStatusResponse(BaseModel):
    status: str
    cache_stats: Optional[Dict[str, Any]] = None
    message: Optional[str] = None

class SessionInfo(BaseModel):
    session_id: str
    created_at: float
    age_seconds: float
    is_stopped: bool
    stopped_at: Optional[float] = None

class SessionStatusResponse(BaseModel):
    status: str
    total_sessions: int
    active_sessions: List[SessionInfo]
    timestamp: str

# Test endpoint models
class ModelTestRequest(BaseModel):
    model: str

class ModelTestResponse(BaseModel):
    status: str
    model: str
    available: bool
    error: Optional[str] = None
    timestamp: float

class RefreshModelsResponse(BaseModel):
    status: str
    models_cached: int
    models: List[str]
    error: Optional[str] = None
    timestamp: float

class ModelCacheStatusResponse(BaseModel):
    status: str
    cache: Dict[str, Any]
    timestamp: float
