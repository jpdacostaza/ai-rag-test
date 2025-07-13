# API Documentation - OpenWebUI Enhanced Memory System Backend

## Overview

This document provides comprehensive API documentation for the OpenWebUI Enhanced Memory System Backend, including OpenAPI specifications and endpoint details.

## 🌐 Service Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        API Gateway                              │
│                    Backend API (Port 3000)                     │
└─────────────────────┬───────────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────────┐
│                   Memory API (Port 8001)                       │
│  ├─ Memory Storage & Retrieval                                 │
│  ├─ User Authentication                                         │
│  └─ Cross-Session Persistence                                  │
└─────────────────────────────────────────────────────────────────┘
```

## 🔗 API Endpoints

### Backend API (Port 3000)

#### Chat Endpoints
- **POST** `/api/chat/completions` - Stream chat completions with memory integration
- **POST** `/api/chat/query` - Single chat query with context injection
- **GET** `/api/chat/models` - List available chat models

#### Memory Endpoints  
- **GET** `/api/memory/user/{user_id}` - Retrieve user memories
- **POST** `/api/memory/store` - Store new memory
- **PUT** `/api/memory/update/{memory_id}` - Update existing memory
- **DELETE** `/api/memory/user/{user_id}` - Clear user memories

#### Upload Endpoints
- **POST** `/api/upload/document` - Upload and process documents
- **GET** `/api/upload/status/{task_id}` - Check upload processing status

#### Health & Debug
- **GET** `/api/health` - System health check
- **GET** `/api/debug/status` - Detailed system status
- **GET** `/api/models/list` - List available LLM models

### Memory API (Port 8001)

#### Core Memory Operations
- **GET** `/health` - Memory service health check
- **POST** `/api/memory/store` - Store memories with automatic Redis/ChromaDB routing
- **GET** `/api/memory/retrieve/{user_id}` - Retrieve relevant memories for user
- **POST** `/api/memory/query` - Semantic memory search
- **DELETE** `/api/memory/clear/{user_id}` - Clear user memory data

#### Authentication & Sessions
- **POST** `/api/auth/validate` - Validate user authentication
- **GET** `/api/auth/session/{user_id}` - Get user session info

## 📋 OpenAPI Specification

### Backend API OpenAPI Schema

```yaml
openapi: 3.0.3
info:
  title: OpenWebUI Enhanced Memory System Backend API
  description: Comprehensive backend API for conversational memory and LLM integration
  version: 1.0.0
  contact:
    name: Backend API Support
    
servers:
  - url: http://localhost:3000
    description: Development server
  - url: http://backend:3000  
    description: Docker environment

paths:
  /api/chat/completions:
    post:
      summary: Stream chat completions with memory
      description: Process chat messages with automatic memory injection and storage
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                messages:
                  type: array
                  items:
                    type: object
                    properties:
                      role:
                        type: string
                        enum: [system, user, assistant]
                      content:
                        type: string
                model:
                  type: string
                  default: "llama3.2:3b"
                stream:
                  type: boolean
                  default: true
                user:
                  type: object
                  properties:
                    id:
                      type: string
                    email:
                      type: string
      responses:
        '200':
          description: Successful response
          content:
            text/event-stream:
              schema:
                type: string
        '500':
          description: Internal server error
          
  /api/memory/user/{user_id}:
    get:
      summary: Retrieve user memories
      parameters:
        - name: user_id
          in: path
          required: true
          schema:
            type: string
        - name: limit
          in: query
          schema:
            type: integer
            default: 10
      responses:
        '200':
          description: User memories retrieved
          content:
            application/json:
              schema:
                type: object
                properties:
                  memories:
                    type: array
                    items:
                      type: object
                      properties:
                        id:
                          type: string
                        content:
                          type: string
                        timestamp:
                          type: string
                        relevance_score:
                          type: number
                  total:
                    type: integer
                    
  /api/health:
    get:
      summary: System health check
      responses:
        '200':
          description: System is healthy
          content:
            application/json:
              schema:
                type: object
                properties:
                  status:
                    type: string
                    example: "healthy"
                  services:
                    type: object
                    properties:
                      memory_api:
                        type: string
                      database:
                        type: string
                      llm_service:
                        type: string
                  timestamp:
                    type: string
```

### Memory API OpenAPI Schema

```yaml
openapi: 3.0.3
info:
  title: Enhanced Memory API
  description: Standalone memory service with Redis and ChromaDB integration
  version: 1.0.0
  
servers:
  - url: http://localhost:8001
    description: Memory API server
    
paths:
  /health:
    get:
      summary: Memory service health check
      responses:
        '200':
          description: Service is healthy
          content:
            application/json:
              schema:
                type: object
                properties:
                  status:
                    type: string
                  redis_connected:
                    type: boolean
                  chromadb_connected:
                    type: boolean
                  memory_count:
                    type: integer
                    
  /api/memory/store:
    post:
      summary: Store user memory
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                user_id:
                  type: string
                content:
                  type: string
                context:
                  type: string
                metadata:
                  type: object
      responses:
        '200':
          description: Memory stored successfully
          content:
            application/json:
              schema:
                type: object
                properties:
                  memory_id:
                    type: string
                  storage_location:
                    type: string
                    enum: [redis, chromadb]
```

## 🔧 Authentication

### User Authentication Flow
1. **User ID Extraction**: Multiple fallback strategies
   - Pipeline injection (OpenWebUI)
   - Email address
   - User ID field
   - Username field
   - Anonymous fallback

2. **Session Management**: Automatic session lifecycle
   - Session creation and validation
   - Timeout handling
   - Cross-service consistency

## 📊 Response Formats

### Standard Success Response
```json
{
  "success": true,
  "data": {},
  "timestamp": "2025-07-13T10:30:00Z",
  "request_id": "req_123456789"
}
```

### Standard Error Response
```json
{
  "success": false,
  "error": {
    "code": "MEMORY_SERVICE_UNAVAILABLE",
    "message": "Memory service is temporarily unavailable",
    "details": {}
  },
  "timestamp": "2025-07-13T10:30:00Z",
  "request_id": "req_123456789"
}
```

## 🚀 Getting Started

### Testing API Endpoints

```bash
# Health check
curl http://localhost:3000/api/health

# Memory API health
curl http://localhost:8001/health

# Store memory
curl -X POST http://localhost:8001/api/memory/store \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test_user", "content": "User likes coffee"}'

# Retrieve memories
curl http://localhost:8001/api/memory/retrieve/test_user
```

### Integration Examples

#### Python Integration
```python
import requests

# Store memory
response = requests.post('http://localhost:8001/api/memory/store', 
    json={
        'user_id': 'user123',
        'content': 'User prefers morning meetings',
        'context': 'scheduling_preference'
    })

# Query memories
memories = requests.get('http://localhost:8001/api/memory/retrieve/user123')
```

#### JavaScript Integration
```javascript
// Store memory
const response = await fetch('http://localhost:8001/api/memory/store', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        user_id: 'user123',
        content: 'User likes dark theme',
        context: 'ui_preference'
    })
});

// Retrieve memories
const memories = await fetch('http://localhost:8001/api/memory/retrieve/user123');
const data = await memories.json();
```

## 🔍 Troubleshooting

### Common Issues

1. **Memory API Unavailable (Port 8001)**
   - Check Docker container: `docker-compose ps memory_api`
   - View logs: `docker-compose logs memory_api`
   - Restart: `docker-compose restart memory_api`

2. **Database Connection Errors**
   - Verify Redis: `docker-compose ps redis`
   - Verify ChromaDB: `docker-compose ps chroma`
   - Check network connectivity

3. **Authentication Failures**
   - Verify user_id format
   - Check OpenWebUI pipeline registration
   - Review authentication logs

### Debug Endpoints

- **GET** `/api/debug/status` - Comprehensive system status
- **GET** `/api/debug/memory/{user_id}` - User memory debug info
- **GET** `/api/debug/connections` - Database connection status

## 📈 Performance Guidelines

### Rate Limits
- Chat API: 100 requests/minute per user
- Memory API: 1000 requests/minute per user
- Upload API: 10 requests/minute per user

### Optimization Tips
1. Use streaming for chat completions
2. Batch memory operations when possible
3. Implement client-side caching for frequent queries
4. Monitor memory usage and clear old sessions

---

*This documentation is automatically updated with each API change. Last updated: July 13, 2025*
