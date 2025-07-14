# API Documentation - Updated Architecture

## Overview

This document provides comprehensive API documentation for the AI backend system, updated to reflect the new service-oriented architecture with dependency injection, async patterns, and comprehensive observability.

## Base URL

```
http://localhost:8000
```

## Authentication

The API uses session-based authentication with optional API key support.

### Headers

```
Content-Type: application/json
X-Correlation-ID: uuid4-string (optional, auto-generated if not provided)
X-User-ID: user-identifier (optional)
Authorization: Bearer <token> (if using API key authentication)
```

## Core Endpoints

### 1. Chat API

#### POST `/api/v1/chat/`

Process chat requests with LLM integration, memory management, and tool usage.

**Service Architecture:**
- Uses `ChatService` with dependency injection
- Integrates `LLMService`, `MemoryService`, `CacheService`
- Supports concurrent memory retrieval and caching

**Request:**
```json
{
  "message": "Hello, how can you help me?",
  "user_id": "user123",
  "conversation_id": "conv456",
  "model": "llama3.2:3b",
  "system_prompt": "You are a helpful assistant",
  "max_tokens": 2000,
  "temperature": 0.7,
  "stream": false,
  "use_memory": true,
  "tools_enabled": true,
  "context": {
    "session_id": "session789",
    "metadata": {}
  }
}
```

**Response:**
```json
{
  "message": "Hello! I'm here to help you with any questions or tasks you might have...",
  "user_id": "user123",
  "conversation_id": "conv456",
  "model_used": "llama3.2:3b",
  "tokens_used": 156,
  "response_time_ms": 1247,
  "memory_used": true,
  "cached": false,
  "tools_used": [],
  "context": {
    "correlation_id": "abc123",
    "session_id": "session789",
    "timestamp": "2025-07-14T10:30:00Z"
  }
}
```

**Performance Headers:**
```
X-Response-Time: 1.247s
X-Memory-Usage: 45.2MB
X-Database-Queries: 3
X-Cache-Hit: false
X-Correlation-ID: abc123
```

**Error Responses:**
```json
{
  "error": "Chat processing failed",
  "error_code": "CHAT_SERVICE_ERROR",
  "details": "LLM service unavailable",
  "correlation_id": "abc123",
  "timestamp": "2025-07-14T10:30:00Z"
}
```

#### POST `/api/v1/chat/stream`

Stream chat responses for real-time conversation.

**Request:** Same as above with `"stream": true`

**Response:** Server-Sent Events (SSE)
```
data: {"type": "start", "correlation_id": "abc123"}

data: {"type": "token", "content": "Hello", "tokens_so_far": 1}

data: {"type": "token", "content": "!", "tokens_so_far": 2}

data: {"type": "end", "total_tokens": 156, "response_time_ms": 1247}
```

#### GET `/api/v1/chat/history/{user_id}`

Retrieve chat history for a user.

**Service Architecture:**
- Uses `MemoryService` with dependency injection
- Supports pagination and filtering

**Parameters:**
- `user_id` (path): User identifier
- `limit` (query): Number of conversations to return (default: 50)
- `offset` (query): Pagination offset (default: 0)
- `conversation_id` (query): Filter by specific conversation

**Response:**
```json
{
  "conversations": [
    {
      "conversation_id": "conv456",
      "messages": [
        {
          "role": "user",
          "content": "Hello",
          "timestamp": "2025-07-14T10:30:00Z"
        },
        {
          "role": "assistant", 
          "content": "Hello! How can I help?",
          "timestamp": "2025-07-14T10:30:01Z"
        }
      ],
      "created_at": "2025-07-14T10:30:00Z",
      "updated_at": "2025-07-14T10:30:01Z"
    }
  ],
  "total": 25,
  "has_more": true
}
```

### 2. File Upload API

#### POST `/api/v1/upload/`

Upload and process files for knowledge base integration.

**Service Architecture:**
- Uses `VectorService` and `MemoryService` with dependency injection
- Async file processing with proper resource management

**Request:** Multipart form data
```
Content-Type: multipart/form-data

file: <file_content>
user_id: user123
description: "Research paper on AI"
tags: ["ai", "research"]
process_immediately: true
```

**Response:**
```json
{
  "file_id": "file789",
  "filename": "research_paper.pdf",
  "size": 2048576,
  "type": "application/pdf",
  "status": "processing",
  "user_id": "user123",
  "upload_time": "2025-07-14T10:30:00Z",
  "processing_info": {
    "chunks_created": 45,
    "embeddings_generated": 45,
    "indexed": true
  }
}
```

#### GET `/api/v1/upload/status/{file_id}`

Check file processing status.

**Response:**
```json
{
  "file_id": "file789",
  "status": "completed",
  "progress": 100,
  "chunks_processed": 45,
  "embeddings_created": 45,
  "processing_time_ms": 15420,
  "error": null
}
```

#### GET `/api/v1/upload/files/{user_id}`

List uploaded files for a user.

**Response:**
```json
{
  "files": [
    {
      "file_id": "file789",
      "filename": "research_paper.pdf",
      "size": 2048576,
      "status": "completed",
      "upload_time": "2025-07-14T10:30:00Z",
      "chunks": 45,
      "description": "Research paper on AI"
    }
  ],
  "total": 12
}
```

### 3. Health & Monitoring API

#### GET `/health`

Comprehensive health check for all services.

**Service Architecture:**
- Uses dependency injection to check all services
- Async health checks with timeout handling

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-07-14T10:30:00Z",
  "version": "1.0.0",
  "services": {
    "redis": {
      "status": "healthy",
      "response_time_ms": 2.3,
      "connections": 5,
      "memory_usage": "45.2MB"
    },
    "vector_db": {
      "status": "healthy",
      "response_time_ms": 15.7,
      "collections": 3,
      "documents": 15420
    },
    "llm_service": {
      "status": "healthy",
      "model": "llama3.2:3b",
      "response_time_ms": 1247.5,
      "requests_today": 342
    },
    "memory_service": {
      "status": "healthy",
      "provider": "database",
      "memories_stored": 5430
    }
  },
  "performance": {
    "avg_response_time_ms": 156.3,
    "requests_per_minute": 23.4,
    "error_rate": 0.02,
    "uptime_seconds": 86400
  }
}
```

#### GET `/health/detailed`

Detailed health information with service metrics.

**Response:**
```json
{
  "status": "healthy",
  "detailed_metrics": {
    "system": {
      "cpu_usage": 23.4,
      "memory_usage": 67.8,
      "disk_usage": 45.2,
      "load_average": [1.2, 1.1, 1.0]
    },
    "database": {
      "connection_pool": {
        "active": 8,
        "idle": 12,
        "total": 20
      },
      "query_performance": {
        "avg_query_time_ms": 12.5,
        "slow_queries": 0,
        "total_queries": 1547
      }
    },
    "cache": {
      "hit_rate": 0.87,
      "memory_usage": "256MB",
      "keys": 1247,
      "operations_per_second": 450
    }
  }
}
```

#### GET `/metrics`

Prometheus-compatible metrics endpoint.

**Response:** (Prometheus format)
```
# HELP http_requests_total Total number of HTTP requests
# TYPE http_requests_total counter
http_requests_total{method="GET",endpoint="/health"} 1547

# HELP http_request_duration_seconds HTTP request duration in seconds
# TYPE http_request_duration_seconds histogram
http_request_duration_seconds_bucket{le="0.1"} 1200
http_request_duration_seconds_bucket{le="0.5"} 1450
http_request_duration_seconds_bucket{le="1.0"} 1500

# HELP memory_usage_bytes Memory usage in bytes
# TYPE memory_usage_bytes gauge
memory_usage_bytes 473841664
```

### 4. Debug & Development API

#### GET `/api/v1/debug/config`

Current service configuration (development only).

**Response:**
```json
{
  "environment": "development",
  "services": {
    "redis": {
      "host": "localhost",
      "port": 6379,
      "max_connections": 100
    },
    "llm": {
      "provider": "ollama",
      "model": "llama3.2:3b",
      "timeout": 300
    },
    "vector_db": {
      "host": "localhost",
      "port": 8000,
      "collection": "llm_memory"
    }
  },
  "features": {
    "caching_enabled": true,
    "memory_enabled": true,
    "tools_enabled": true,
    "debug_mode": true
  }
}
```

#### GET `/api/v1/debug/performance`

Performance metrics and profiling data.

**Response:**
```json
{
  "request_metrics": {
    "total_requests": 15420,
    "avg_response_time": 156.3,
    "p95_response_time": 450.2,
    "p99_response_time": 1200.5
  },
  "service_metrics": {
    "chat_service": {
      "requests": 8420,
      "avg_time": 234.5,
      "success_rate": 0.98
    },
    "memory_service": {
      "requests": 4230,
      "avg_time": 45.2,
      "success_rate": 0.995
    }
  },
  "resource_usage": {
    "memory_mb": 512.3,
    "cpu_percent": 23.4,
    "db_connections": 8,
    "cache_size_mb": 256.7
  }
}
```

## Service Integration Patterns

### Dependency Injection Example

```python
from fastapi import APIRouter, Depends
from services.chat_service import ChatService
from services.dependencies import get_chat_service

router = APIRouter()

@router.post("/chat")
async def chat_endpoint(
    request: ChatRequest,
    chat_service: ChatService = Depends(get_chat_service)
) -> ChatResponse:
    return await chat_service.process_chat_request(request)
```

### Async Service Usage

```python
class ChatService:
    async def process_chat_request(self, request: ChatRequest) -> ChatResponse:
        # Concurrent operations
        memories, cached, context = await asyncio.gather(
            self.memory_service.get_memories(request.user_id),
            self.cache_service.get_cached(request.cache_key),
            self.vector_service.search_similar(request.query)
        )
        
        if cached:
            return cached
            
        response = await self.llm_service.call_llm(request.messages)
        await self.memory_service.store_memory(request, response)
        
        return response
```

### Error Handling Pattern

```python
@handle_service_errors("process_chat")
async def process_chat_request(self, request: ChatRequest) -> ChatResponse:
    try:
        return await self._process_internal(request)
    except LLMServiceError as e:
        self.logger.error("LLM service error", error=str(e))
        raise ChatServiceError("Failed to process chat request") from e
```

## Response Formats

### Success Response

All successful responses follow this structure:

```json
{
  "data": { /* endpoint specific data */ },
  "meta": {
    "correlation_id": "abc123",
    "timestamp": "2025-07-14T10:30:00Z",
    "version": "1.0.0"
  },
  "performance": {
    "response_time_ms": 156.3,
    "cached": false,
    "service_times": {
      "chat_service": 120.5,
      "llm_service": 1100.2,
      "memory_service": 15.7
    }
  }
}
```

### Error Response

All error responses follow this structure:

```json
{
  "error": {
    "message": "Chat processing failed",
    "code": "CHAT_SERVICE_ERROR", 
    "details": "LLM service unavailable",
    "correlation_id": "abc123",
    "timestamp": "2025-07-14T10:30:00Z"
  },
  "meta": {
    "endpoint": "/api/v1/chat/",
    "method": "POST",
    "user_id": "user123"
  }
}
```

### HTTP Status Codes

- `200` - Success
- `201` - Created (file uploads)
- `400` - Bad Request (validation errors)
- `401` - Unauthorized
- `404` - Not Found
- `422` - Validation Error
- `429` - Rate Limited
- `500` - Internal Server Error
- `502` - Service Unavailable
- `503` - Service Temporarily Unavailable

## Rate Limiting

Rate limiting is applied per endpoint and user:

- Chat API: 100 requests per minute per user
- File Upload: 10 files per minute per user
- Health checks: No limit
- Debug endpoints: 60 requests per minute (development only)

Rate limit headers:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1642176000
X-RateLimit-Window: 60
```

## Caching

The API implements multi-level caching:

1. **Response Caching**: Common responses cached for 5 minutes
2. **Memory Caching**: User memory cached for 1 hour
3. **Vector Caching**: Similarity searches cached for 30 minutes

Cache headers:
```
X-Cache-Status: HIT|MISS|STALE
X-Cache-Age: 150
X-Cache-TTL: 300
```

## Monitoring & Observability

### Correlation IDs

Every request gets a correlation ID for tracing:
- Auto-generated if not provided
- Included in all log entries
- Returned in response headers
- Used for distributed tracing

### Structured Logging

All API interactions are logged with structured data:

```json
{
  "timestamp": "2025-07-14T10:30:00Z",
  "level": "INFO",
  "message": "Chat request processed",
  "correlation_id": "abc123",
  "user_id": "user123",
  "endpoint": "/api/v1/chat/",
  "response_time_ms": 156.3,
  "status_code": 200,
  "service": "chat_service"
}
```

### Performance Metrics

Every response includes performance information:
- Request processing time
- Service-specific timing
- Memory usage delta
- Database query count
- Cache hit/miss status

## Testing & Development

### Test Endpoints

Development environment includes test endpoints:

- `POST /api/v1/test/chat` - Test chat with mock responses
- `POST /api/v1/test/memory` - Test memory storage
- `GET /api/v1/test/health` - Simplified health check

### Mock Responses

For development and testing, mock responses can be enabled:

```bash
export ENABLE_MOCK_RESPONSES=true
export MOCK_LLM_DELAY=100  # ms
```

### Integration Testing

Example integration test:

```python
import pytest
from fastapi.testclient import TestClient

def test_chat_endpoint_integration():
    with TestClient(app) as client:
        response = client.post("/api/v1/chat/", json={
            "message": "Hello",
            "user_id": "test_user"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert data["user_id"] == "test_user"
        assert "correlation_id" in data["context"]
```

## Security Considerations

### Input Validation

All inputs are validated using Pydantic models:
- Message length limits
- User ID format validation
- File type restrictions
- SQL injection prevention

### Rate Limiting

Implemented at multiple levels:
- API gateway level
- Service level
- User level

### CORS Configuration

Configurable CORS settings:
```python
allow_origins=["https://yourdomain.com"]
allow_methods=["GET", "POST"]
allow_headers=["*"]
```

### Authentication

Multiple authentication methods supported:
- Session-based authentication
- API key authentication
- JWT tokens (optional)

This API documentation reflects the modern service-oriented architecture with dependency injection, async patterns, comprehensive monitoring, and enterprise-grade error handling.
