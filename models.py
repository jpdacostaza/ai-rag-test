"""
Pydantic models and request/response schemas for the FastAPI backend.
"""

from pydantic import BaseModel
from typing import Dict, List, Optional, Union, Any
from datetime import datetime


# Chat models
class ChatRequest(BaseModel):
    """TODO: Add proper docstring for ChatRequest class."""

    user_id: str
    message: str


class ChatResponse(BaseModel):
    """TODO: Add proper docstring for ChatResponse class."""

    response: str


# OpenAI-compatible models
class OpenAIMessage(BaseModel):
    """TODO: Add proper docstring for OpenAIMessage class."""

    role: str
    content: Union[str, List[Dict[str, Any]]]


class OpenAIChatRequest(BaseModel):
    """TODO: Add proper docstring for OpenAIChatRequest class."""

    model: str
    messages: List[OpenAIMessage]
    stream: Optional[bool] = False
    max_tokens: Optional[int] = 4096
    temperature: Optional[float] = 0.7
    user: Optional[str] = None


class OpenAIChoice(BaseModel):
    """TODO: Add proper docstring for OpenAIChoice class."""

    index: int
    message: OpenAIMessage
    finish_reason: str


class OpenAIChatResponse(BaseModel):
    """TODO: Add proper docstring for OpenAIChatResponse class."""

    id: str
    object: str
    created: int
    model: str
    choices: List[OpenAIChoice]


# Streaming models
class StreamChoice(BaseModel):
    """TODO: Add proper docstring for StreamChoice class."""

    index: int
    delta: Dict[str, str]
    finish_reason: Optional[str] = None


class StreamResponse(BaseModel):
    """TODO: Add proper docstring for StreamResponse class."""

    id: str
    object: str
    created: int
    model: str
    choices: List[StreamChoice]


# Model listing
class ModelInfo(BaseModel):
    """TODO: Add proper docstring for ModelInfo class."""

    id: str
    object: str = "model"
    created: int
    owned_by: str = "ollama"
    permission: List = []
    root: Optional[str] = None
    parent: Optional[str] = None


class ModelListResponse(BaseModel):
    """TODO: Add proper docstring for ModelListResponse class."""

    object: str = "list"
    data: List[ModelInfo]


# Memory and learning models
class MemoryRequest(BaseModel):
    """TODO: Add proper docstring for MemoryRequest class."""

    user_id: str
    query: str
    limit: Optional[int] = 3
    threshold: Optional[float] = 0.7


class MemoryResponse(BaseModel):
    """TODO: Add proper docstring for MemoryResponse class."""

    memories: List[Dict[str, Any]]
    count: int
    user_id: str
    query: str


class LearningRequest(BaseModel):
    """TODO: Add proper docstring for LearningRequest class."""

    user_id: str
    conversation_id: Optional[str] = None
    user_message: str
    assistant_response: str
    response_time: Optional[float] = 1.0
    tools_used: Optional[List[str]] = []
    source: Optional[str] = "api"


class LearningResponse(BaseModel):
    """TODO: Add proper docstring for LearningResponse class."""

    status: str
    result: Dict[str, Any]
    user_id: str
    source: str


# Pipeline models
class PipelineInfo(BaseModel):
    """TODO: Add proper docstring for PipelineInfo class."""

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
    """TODO: Add proper docstring for PipelineListResponse class."""

    data: List[PipelineInfo]


# Health check models
class ServiceHealth(BaseModel):
    """TODO: Add proper docstring for ServiceHealth class."""

    status: str
    available: bool
    message: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class DatabaseHealth(BaseModel):
    """TODO: Add proper docstring for DatabaseHealth class."""

    redis: ServiceHealth
    chromadb: ServiceHealth
    embeddings: ServiceHealth


class HealthResponse(BaseModel):
    """TODO: Add proper docstring for HealthResponse class."""

    status: str
    summary: str
    databases: DatabaseHealth
    cache: Optional[Dict[str, Any]] = None


class DetailedHealthResponse(BaseModel):
    """TODO: Add proper docstring for DetailedHealthResponse class."""

    status: str
    timestamp: str
    overall_status: str
    services: Dict[str, Dict[str, Any]]
    summary: Dict[str, int]


# Error models
class ErrorDetail(BaseModel):
    """TODO: Add proper docstring for ErrorDetail class."""

    type: str
    code: int
    message: str
    details: Optional[Any] = None
    request_id: Optional[str] = None
    timestamp: str


class ErrorResponse(BaseModel):
    """TODO: Add proper docstring for ErrorResponse class."""

    error: ErrorDetail


# Admin models
class CacheStatusResponse(BaseModel):
    """TODO: Add proper docstring for CacheStatusResponse class."""

    status: str
    cache_stats: Optional[Dict[str, Any]] = None
    message: Optional[str] = None


class SessionInfo(BaseModel):
    """TODO: Add proper docstring for SessionInfo class."""

    session_id: str
    created_at: float
    age_seconds: float
    is_stopped: bool
    stopped_at: Optional[float] = None


class SessionStatusResponse(BaseModel):
    """TODO: Add proper docstring for SessionStatusResponse class."""

    status: str
    total_sessions: int
    active_sessions: List[SessionInfo]
    timestamp: str


# Test endpoint models
class ModelTestRequest(BaseModel):
    """TODO: Add proper docstring for ModelTestRequest class."""

    model: str


class ModelTestResponse(BaseModel):
    """TODO: Add proper docstring for ModelTestResponse class."""

    status: str
    model: str
    available: bool
    error: Optional[str] = None
    timestamp: float


class RefreshModelsResponse(BaseModel):
    """TODO: Add proper docstring for RefreshModelsResponse class."""

    status: str
    models_cached: int
    models: List[str]
    error: Optional[str] = None
    timestamp: float


class ModelCacheStatusResponse(BaseModel):
    """TODO: Add proper docstring for ModelCacheStatusResponse class."""

    status: str
    cache: Dict[str, Any]
    timestamp: float
