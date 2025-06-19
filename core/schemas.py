"""
Data Models and Schemas for the FastAPI LLM Backend
Centralized location for all Pydantic models and data classes
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


# Chat-related schemas
class ChatRequest(BaseModel):
    user_id: str
    message: str


class ChatResponse(BaseModel):
    response: str


class ChatHistoryItem(BaseModel):
    timestamp: datetime
    message: str
    response: str
    user_id: str


# Health check schemas
class HealthStatus(BaseModel):
    status: str
    timestamp: float
    message: Optional[str] = None


class ServiceHealth(BaseModel):
    name: str
    status: str  # healthy, degraded, unhealthy
    last_check: datetime
    response_time_ms: Optional[float] = None
    error_message: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class DetailedHealthResponse(BaseModel):
    status: str
    timestamp: str
    overall_status: str
    services: Dict[str, Dict[str, Any]]
    summary: Dict[str, int]


# Tool and API schemas
class ToolRequest(BaseModel):
    tool_name: str
    parameters: Dict[str, Any]
    user_id: str


class ToolResponse(BaseModel):
    tool_name: str
    success: bool
    result: Any
    error_message: Optional[str] = None
    execution_time_ms: float


# Cache schemas
class CacheStats(BaseModel):
    version: str
    total_keys: int
    cache_counts: Dict[str, int]
    memory_usage: str
    connected_clients: int


class CacheSetRequest(BaseModel):
    key: str
    value: str
    ttl: Optional[int] = 300


# Document processing schemas
class DocumentUploadResponse(BaseModel):
    success: bool
    message: str
    document_id: Optional[str] = None
    chunks_processed: Optional[int] = None


class DocumentSearchRequest(BaseModel):
    query: str
    user_id: str
    limit: Optional[int] = 5


class DocumentSearchResponse(BaseModel):
    success: bool
    query: str
    results_count: int
    results: List[Dict[str, Any]]


# Model management schemas
class ModelInfo(BaseModel):
    id: str
    object: str = "model"
    created: int
    owned_by: str
    permission: List[Any] = []


class ModelsResponse(BaseModel):
    object: str = "list"
    data: List[ModelInfo]


# OpenAI compatibility schemas
class OpenAIMessage(BaseModel):
    role: str
    content: str


class OpenAIChatRequest(BaseModel):
    model: str
    messages: List[OpenAIMessage]
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = None
    top_p: Optional[float] = 1.0
    frequency_penalty: Optional[float] = 0.0
    presence_penalty: Optional[float] = 0.0
    stream: Optional[bool] = False


class OpenAIChatChoice(BaseModel):
    index: int
    message: OpenAIMessage
    finish_reason: str


class OpenAIChatResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[OpenAIChatChoice]
    usage: Optional[Dict[str, int]] = None


# Error response schemas
class ErrorResponse(BaseModel):
    error: str
    message: str
    code: Optional[int] = None
    details: Optional[Dict[str, Any]] = None


class ValidationErrorResponse(BaseModel):
    error: str = "validation_error"
    message: str
    field_errors: List[Dict[str, Any]]


# System monitoring schemas
class SystemMetrics(BaseModel):
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    network_io: Dict[str, float]
    timestamp: datetime


class ServiceMetrics(BaseModel):
    service_name: str
    uptime: float
    request_count: int
    error_count: int
    average_response_time: float
    last_updated: datetime
