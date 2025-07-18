# API Documentation - Current System

**Last Updated**: 2025-07-18

## Base URL
```
http://localhost:3000
```

## Authentication
A### Docker Services
All services communicate through Docker internal networking:
- `backend-redis:6379` - Redis cache
- `backend-chroma:8000` - ChromaDB vector store  
- `backend-ollama:11434` - Ollama LLM service
- `backend-main:3000` - Main FastAPI applicationory operations require user authentication. Users are validated through OpenWebUI pipeline integration.

## Core Endpoints

### Health & Monitoring

#### `GET /health`
System health with service dependency injection
```json
{
  "status": "ok",
  "summary": "Health check: 3/3 services healthy. Redis: ✅, ChromaDB: ✅, Embeddings: ✅",
  "databases": {
    "redis": {"status": "healthy"},
    "chromadb": {"status": "healthy"}, 
    "embeddings": {"status": "healthy"}
  },
  "startup": {"startup_complete": true},
  "timestamp": "2025-07-18T10:30:00Z"
}
```

#### `GET /health/detailed`
Comprehensive service monitoring with subsystem details

#### `GET /health/features`
Feature availability tracking
```json
{
  "features": {
    "redis": {"available": true, "last_check": "2025-07-18T10:30:00Z"},
    "chromadb": {"available": true, "last_check": "2025-07-18T10:30:00Z"},
    "sentence_transformers": {"available": true, "last_check": "2025-07-18T10:30:00Z"}
  },
  "summary": {"total_features": 7, "available_features": 7, "health_percentage": 100.0}
}
```

### Chat System

#### `POST /v1/chat/completions`
OpenAI-compatible chat endpoint with memory integration
```json
{
  "model": "llama3.2:3b",
  "messages": [
    {"role": "user", "content": "Hello, how are you?"}
  ],
  "stream": false
}
```

#### POST /chat/completions_legacy
Legacy format support with automatic format detection

### Models

#### `GET /v1/models`
List available models from Ollama with caching
```json
{
  "object": "list",
  "data": [
    {
      "id": "llama3.2:3b",
      "object": "model", 
      "created": 1721304600,
      "owned_by": "ollama"
    }
  ]
}
```

### Memory System

#### `GET /memory/health`
Memory system health check
```json
{
  "status": "healthy",
  "timestamp": "2025-07-18T10:30:00Z",
  "redis": "healthy",
  "chromadb": "healthy", 
  "embeddings": "healthy"
}
```

### Document Management

#### POST /upload
Upload documents for memory indexing

#### POST /search
Search indexed documents

### Debug & Development

#### GET /debug/services
Get all service statistics

#### POST /debug/cache/clear
Clear cache (development only)

## Error Handling

All endpoints use consistent error handling with structured responses:

```json
{
  "error": {
    "type": "ValidationError",
    "message": "Invalid request format",
    "request_id": "req_123456789"
  }
}
```

## Rate Limiting
- Chat endpoints: 60 requests per minute per user
- Health endpoints: No rate limiting
- Upload endpoints: 10 requests per minute per user

## System Integration

### OpenWebUI Integration
The system integrates directly with OpenWebUI through:
- Pipeline-based memory processing
- User authentication validation
- Conversation storage and retrieval

### Docker Services
All services communicate through Docker internal networking:
- ackend-redis:6379 - Redis cache
- ackend-chroma:8000 - ChromaDB vector store  
- ackend-ollama:11434 - Ollama LLM service
- ackend-main:3000 - Main FastAPI application

## Development Notes

### Configuration
- Single unified configuration in `config/config_unified.py`
- No fallback configurations - all services use consistent settings
- Environment variables handled through Docker Compose

### Feature Registry
- Centralized tracking of optional dependencies
- Transparent import failure handling
- Health monitoring for all features

### Error Handling Patterns
- Decorator-based error handling (`@handle_api_errors`, `@handle_service_errors`)
- Structured error responses with request IDs
- Comprehensive logging with service status tracking

**Note**: API Gateway is currently disabled. All requests go directly to the main backend service.
