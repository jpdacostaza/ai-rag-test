# APIs - Complete Endpoint Documentation

## OpenAI-Compatible Endpoints

### POST `/v1/chat/completions`
**Purpose**: Main chat completion endpoint fully compatible with OpenAI API specification.

**Request Format:**
```json
{
  "model": "string (required)",
  "messages": [
    {
      "role": "system|user|assistant",
      "content": "string or multimodal array"
    }
  ],
  "stream": boolean (optional, default: false),
  "temperature": number (optional),
  "max_tokens": number (optional),
  "user": "string (optional)"
}
```

**Core Functionality:**
- **Multimodal Support**: Handles text and image content in message arrays
- **Streaming Support**: Server-Sent Events (SSE) for real-time token streaming
- **Memory Integration**: Automatic memory context injection with delimited boundaries
- **History Integration**: Chat history retrieval and persistence via Redis
- **User Context**: Comprehensive user identification and session management

**Advanced Features:**
- **Circuit Breaker Protection**: Prevents cascade failures during LLM service issues
- **Heartbeat Management**: Maintains connection stability during long streaming sessions
- **Error Recovery**: Graceful degradation with user-friendly error messages
- **Performance Monitoring**: Request timing and success rate tracking
- **Cache Integration**: Response caching for non-time-sensitive queries

**Response Formats:**
- **Non-Streaming**: Standard OpenAI completion format with choices array
- **Streaming**: SSE chunks with delta content and finish reasons
- **Error Handling**: Standardized error responses with correlation IDs

### GET `/v1/models`
**Purpose**: OpenAI-compatible model listing with dynamic discovery.

**Response Format:**
```json
{
  "object": "list",
  "data": [
    {
      "id": "model-name",
      "object": "model",
      "created": 1234567890,
      "owned_by": "ollama|openai",
      "permission": [],
      "root": "model-name",
      "parent": null
    }
  ]
}
```

**Features:**
- **Dynamic Discovery**: Real-time model fetching from Ollama API
- **Caching**: TTL-based model cache (5 minutes default) with manual refresh
- **Fallback Handling**: Graceful degradation when Ollama is unavailable
- **OpenAI Compatibility**: Full compatibility with OpenAI model format

## Memory Management APIs

### GET `/api/memory/health`
**Purpose**: Memory system health and status reporting.

**Response Format:**
```json
{
  "status": "healthy|degraded|unhealthy",
  "timestamp": "ISO-8601",
  "redis": {
    "status": "healthy|unhealthy",
    "latency_ms": number
  },
  "chromadb": {
    "status": "healthy|unhealthy",
    "collections": number
  },
  "embeddings": {
    "status": "healthy|unhealthy",
    "model": "string"
  }
}
```

### POST `/api/memory/store`
**Purpose**: Store user memories with metadata and importance scoring.

**Request Format:**
```json
{
  "user_id": "string (required)",
  "content": "string (required)",
  "metadata": {},
  "importance": 0.5,
  "memory_type": "conversation|fact|preference"
}
```

**Advanced Features:**
- **Importance Scoring**: 0.0-1.0 scale for memory prioritization
- **Metadata Enrichment**: Automatic timestamp and context addition
- **User Isolation**: Strict user-based memory segregation
- **Validation**: Input sanitization and user ID validation

### POST `/api/memory/query`
**Purpose**: Semantic memory search with similarity scoring.

**Request Format:**
```json
{
  "user_id": "string (required)",
  "query": "string (required)",
  "limit": 5,
  "min_score": 0.0
}
```

**Response Format:**
```json
{
  "success": true,
  "memories": [
    {
      "content": "string",
      "metadata": {},
      "similarity_score": 0.85,
      "distance": 0.15
    }
  ],
  "total_count": number
}
```

### POST `/api/memory/bulk_query`
**Purpose**: Concurrent multiple memory queries for efficiency.

**Request Format:**
```json
{
  "user_id": "string (required)",
  "queries": ["query1", "query2", "query3"],
  "limit": 5,
  "min_score": 0.0
}
```

**Features:**
- **Concurrent Processing**: Parallel query execution for performance
- **Individual Error Handling**: Per-query error capture and reporting
- **Batch Optimization**: Efficient resource utilization for multiple queries

### GET `/api/memory/user/{user_id}`
**Purpose**: Retrieve all memories for a specific user with pagination.

**Query Parameters:**
- `limit`: Number of results (1-100, default 10)
- `memory_type`: Filter by memory type
- `offset`: Pagination offset

### DELETE `/api/memory/user/{user_id}`
**Purpose**: Clear all memories for a user (administrative function).

**Security**: Requires admin privileges or user ownership verification.

### GET `/api/memory/stats`
**Purpose**: Memory system statistics and performance metrics.

**Response Format:**
```json
{
  "timestamp": "ISO-8601",
  "database_health": {},
  "cache_stats": {},
  "memory_system": {
    "redis_available": boolean,
    "chromadb_available": boolean,
    "embeddings_available": boolean,
    "total_memories": number,
    "active_users": number
  }
}
```

## Document Upload & Search APIs

### POST `/upload/document`
**Purpose**: Document ingestion with automatic processing for RAG integration.

**Request Format (Multipart):**
- `file`: Document file (PDF, DOC, DOCX, TXT, MD, JSON, Python)
- `user_id`: User identifier for document isolation
- `description`: Optional document description

**Processing Pipeline:**
1. **File Validation**: Type, size, and content validation
2. **Text Extraction**: Format-specific text extraction
3. **Chunking**: Intelligent text segmentation
4. **Embedding**: Vector generation and storage
5. **Indexing**: ChromaDB storage with metadata

**Response Format:**
```json
{
  "success": true,
  "message": "Document processed successfully",
  "data": {
    "chunks_processed": number,
    "document_id": "string",
    "file_size": number,
    "processing_time_ms": number
  }
}
```

### GET `/upload/formats`
**Purpose**: Supported file formats and upload limits.

**Response Format:**
```json
{
  "supported_mime_types": [
    "text/plain",
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/markdown",
    "text/x-python",
    "application/json"
  ],
  "max_file_size_mb": 10,
  "description": "Supported file formats for document upload and processing"
}
```

### POST `/upload/search`
**Purpose**: Semantic search across uploaded documents.

**Request Format:**
```json
{
  "query": "string (required)",
  "user_id": "string (required)",
  "limit": 5
}
```

**Advanced Features:**
- **Semantic Search**: Vector similarity-based document retrieval
- **User Isolation**: Search limited to user's uploaded documents
- **Result Ranking**: Relevance-based result ordering
- **Snippet Extraction**: Relevant text snippet highlighting

### POST `/upload/document_json` / `/upload/search_json`
**Purpose**: JSON-based upload and search for testing and API integration.

**Features**: Same functionality as multipart endpoints but with JSON payloads for easier programmatic access.

## Tools & Utilities APIs

### GET `/tools`
**Purpose**: List available tools with descriptions and usage examples.

**Response Format:**
```json
{
  "tools": [
    {
      "name": "web_search",
      "description": "Enhanced web search with DuckDuckGo",
      "examples": ["search for latest AI news", "find information about Python"]
    },
    {
      "name": "time_lookup",
      "description": "Current time in any location",
      "examples": ["what time is it in Tokyo", "current time in New York"]
    }
  ]
}
```

### POST `/tools/web_search`
**Purpose**: Enhanced web search with structured results.

**Request Format:**
```json
{
  "query": "string (required)",
  "max_results": 5,
  "region": "us-en",
  "safe_search": "moderate"
}
```

**Response Format:**
```json
{
  "query": "string",
  "results": [
    {
      "title": "string",
      "url": "string",
      "snippet": "string",
      "published": "ISO-8601",
      "source": "string"
    }
  ],
  "total_results": number,
  "search_time_ms": number,
  "cached": boolean
}
```

**Advanced Features:**
- **Result Caching**: TTL-based caching (5 minutes default)
- **Safe Search**: Content filtering and safe search enforcement
- **Region Support**: Localized search results
- **Performance Optimization**: Fast response times with caching

## Health & Monitoring APIs

### GET `/health`
**Purpose**: Basic health check for load balancers and monitoring.

**Response**: `{"status": "healthy", "timestamp": "ISO-8601"}`

### GET `/health/detailed`
**Purpose**: Comprehensive health reporting with component breakdown.

**Response Format:**
```json
{
  "status": "healthy|degraded|unhealthy",
  "timestamp": "ISO-8601",
  "components": {
    "database": {
      "status": "healthy",
      "redis": {"status": "healthy", "latency_ms": 1.2},
      "chromadb": {"status": "healthy", "collections": 5},
      "embeddings": {"status": "healthy", "model": "sentence-transformers"}
    },
    "services": {
      "llm": {"status": "healthy", "provider": "ollama"},
      "memory": {"status": "healthy", "memories_count": 1250},
      "streaming": {"status": "healthy", "active_sessions": 3}
    },
    "external": {
      "ollama": {"status": "healthy", "models": 3},
      "web_search": {"status": "healthy", "cache_hits": 0.75}
    }
  },
  "performance": {
    "uptime_seconds": 3600,
    "requests_per_minute": 25,
    "avg_response_time_ms": 150
  }
}
```

### GET `/health/readiness` / `/health/liveness`
**Purpose**: Kubernetes-style readiness and liveness probes.

**Readiness**: Indicates service is ready to handle requests
**Liveness**: Indicates service is alive and functioning

### GET `/health/storage`
**Purpose**: Storage system health with capacity and performance metrics.

### GET `/health/alerts`
**Purpose**: Current alerts and warning status.

## Gateway Management APIs

### GET `/gateway/health`
**Purpose**: API Gateway health and routing status.

### GET `/gateway/status`
**Purpose**: Gateway performance metrics and routing statistics.

### GET `/gateway/config`
**Purpose**: Gateway configuration and routing rules (admin access).

## Debug & Administrative APIs

### GET `/debug/cache`
**Purpose**: Cache statistics and performance metrics.

**Response Format:**
```json
{
  "size": number,
  "max_size": number,
  "hit_count": number,
  "miss_count": number,
  "hit_rate": "percentage",
  "memory_usage_mb": number
}
```

### POST `/debug/cache/clear`
**Purpose**: Clear cache (administrative function).

### GET `/debug/redis` / `/debug/vector`
**Purpose**: Component-specific statistics and health metrics.

### GET `/debug/services`
**Purpose**: All service statistics in single response.

### GET `/debug/memory`
**Purpose**: System memory usage without external dependencies.

### GET `/debug/config`
**Purpose**: Sanitized configuration display (secrets masked).

### GET `/debug/endpoints`
**Purpose**: Dynamic endpoint listing with HTTP methods.

## Response Standards

### Success Responses
- **Status Codes**: 200 (success), 201 (created), 202 (accepted)
- **Format**: Consistent JSON structure with success indicators
- **Headers**: Correlation IDs for request tracing

### Error Responses
- **Status Codes**: 400 (bad request), 401 (unauthorized), 403 (forbidden), 404 (not found), 429 (rate limited), 500 (server error), 503 (service unavailable)
- **Format**: Standardized error structure with correlation IDs
- **Details**: User-friendly messages with technical details for debugging

### Streaming Responses
- **Format**: Server-Sent Events (SSE) with proper MIME types
- **Heartbeats**: Regular keepalive messages for connection stability
- **Error Handling**: In-stream error delivery with graceful termination
