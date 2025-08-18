# Routes - Complete API Endpoint Implementation

## Chat Routes (`routes/chat.py`)

### Legacy Chat Completions Endpoint
**Purpose**: Backward compatibility endpoint for existing chat completion implementations.

**Endpoint**: `/chat/completions_legacy`
**Method**: POST

**Implementation Details:**
- **Legacy Support**: Maintains compatibility with existing chat clients
- **Memory Integration**: Optional memory service integration for conversation context
- **Autonomous Routing**: Enhanced routing with autonomous decision-making capabilities
- **User Identity**: Automatic user identity resolution and session management

**Key Components:**
```python
@chat_router.post("/completions_legacy")
async def chat_completions_legacy(
    request: ChatRequest,
    chat_service: ChatService = Depends(get_chat_service),
    user_id: str = Depends(resolve_user_id)
):
    # Legacy chat completion logic with memory integration
```

### Memory Storage Helper
**Purpose**: Automatic memory storage for significant conversation interactions.

**Features:**
- **Automatic Storage**: Store important conversation turns based on criteria
- **User Association**: Proper user-scoped memory storage
- **Content Analysis**: Analyze conversation content for storage worthiness
- **Metadata Enrichment**: Add conversation metadata for better retrieval

### Autonomous Routing Capabilities
**Purpose**: Intelligent request routing based on conversation context and user intent.

**Routing Options:**
1. **Simplified Chat Router** (`services.simplified_chat_router`)
   - Basic autonomous routing logic
   - Context-aware response routing
   - Performance-optimized routing decisions

2. **Enhanced Chat Router** (`services.enhanced_chat_router`)
   - Advanced autonomous decision-making
   - Multi-model routing strategies
   - Sophisticated context analysis

**Fallback Handling**: Graceful degradation when autonomous routing is unavailable.

### User Document Indexing
**Purpose**: Automatic indexing of user-uploaded documents for retrieval-augmented generation.

**Implementation:**
```python
await index_user_document(
    user_id=user_id,
    document_content=content,
    document_metadata=metadata
)
```

**Features:**
- **Real-time Indexing**: Documents indexed immediately upon upload
- **User Isolation**: User-specific document collections
- **Metadata Preservation**: Rich metadata storage for better retrieval
- **Vector Embeddings**: Automatic embedding generation for semantic search

## Models Routes (`routes/models.py`)

### OpenAI-Compatible Model Listing
**Purpose**: OpenAI-compatible model discovery and availability checking.

**Endpoint**: `/v1/models`
**Method**: GET

**Features:**
- **Dynamic Discovery**: Real-time model fetching from Ollama API
- **Caching**: TTL-based model cache (5 minutes default) with manual refresh
- **Fallback Handling**: Graceful degradation when Ollama is unavailable
- **OpenAI Compatibility**: Full compatibility with OpenAI model format

**Response Format:**
```json
{
  "object": "list",
  "data": [
    {
      "id": "model-name",
      "object": "model",
      "created": 1234567890,
      "owned_by": "ollama",
      "permission": [],
      "root": "model-name",
      "parent": null
    }
  ]
}
```

**Temporary Workarounds:**
- **Mistral Inclusion**: Workaround for specific client compatibility requirements
- **Model Aliasing**: Support for alternative model names and aliases

## Memory Routes (`routes/memory.py`)

### Memory Health Endpoint
**Purpose**: Memory system specific health monitoring and diagnostics.

**Endpoint**: `/api/memory/health`
**Method**: GET

**Health Indicators:**
- **Memory Service Status**: Overall memory system health
- **Redis Connectivity**: Memory cache and session storage
- **ChromaDB Status**: Vector database for semantic search
- **Embedding Service**: Text embedding generation service

### Memory Storage Operations
**Purpose**: Store user memories with metadata and importance scoring.

**Store Memory**: `/api/memory/store`
```python
@memory_router.post("/store")
async def store_memory(
    request: MemoryStoreRequest,
    user_id: str = Depends(resolve_user_id)
):
    # Store memory with importance scoring and metadata
```

**Features:**
- **Importance Scoring**: 0.0-1.0 scale for memory prioritization
- **Metadata Enrichment**: Automatic timestamp and context addition
- **User Isolation**: Strict user-based memory segregation
- **Validation**: Input sanitization and user ID validation

### Memory Retrieval Operations
**Purpose**: Semantic memory search and retrieval with similarity scoring.

**Query Memory**: `/api/memory/query`
```python
@memory_router.post("/query")
async def query_memory(
    request: MemoryQueryRequest,
    user_id: str = Depends(resolve_user_id)
):
    # Semantic search with similarity scoring
```

**Bulk Query**: `/api/memory/bulk_query`
```python
@memory_router.post("/bulk_query")
async def bulk_query_memory(
    request: BulkMemoryQueryRequest,
    user_id: str = Depends(resolve_user_id)
):
    # Concurrent multiple memory queries
```

### Memory Management Operations
**Purpose**: User memory management and administrative functions.

**List User Memories**: `/api/memory/user/{user_id}`
- Retrieve all memories for a specific user with pagination
- Filter by memory type, importance, or date range
- Support for pagination and sorting

**Clear User Memories**: `/api/memory/user/{user_id}` (DELETE)
- Clear all memories for a user (administrative function)
- Requires admin privileges or user ownership verification
- Audit logging for memory deletion operations

**Memory Statistics**: `/api/memory/stats`
- Memory system performance and usage statistics
- User-specific and system-wide metrics
- Memory distribution and access patterns

## Upload Routes (`routes/upload.py`)

### Document Upload and Processing
**Purpose**: Document ingestion with automatic processing for RAG integration.

**Upload Document**: `/upload/document`
```python
@upload_router.post("/document")
async def upload_document(
    file: UploadFile,
    user_id: str = Depends(resolve_user_id),
    description: Optional[str] = Form(None)
):
    # Document processing pipeline
```

**Processing Pipeline:**
1. **File Validation**: Type, size, and content validation
2. **Text Extraction**: Format-specific text extraction
3. **Chunking**: Intelligent text segmentation
4. **Embedding**: Vector generation and storage
5. **Indexing**: ChromaDB storage with metadata

**Supported Formats**: PDF, DOC, DOCX, TXT, MD, JSON, Python files

### Document Search Operations
**Purpose**: Semantic search across uploaded documents with relevance ranking.

**Search Documents**: `/upload/search`
```python
@upload_router.post("/search")
async def search_documents(
    request: DocumentSearchRequest,
    user_id: str = Depends(resolve_user_id)
):
    # Semantic document search
```

**Features:**
- **Semantic Search**: Vector similarity-based document retrieval
- **User Isolation**: Search limited to user's uploaded documents
- **Result Ranking**: Relevance-based result ordering
- **Snippet Extraction**: Relevant text snippet highlighting

### Format Support and Limits
**Purpose**: Document format support information and upload constraints.

**Supported Formats**: `/upload/formats`
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

### JSON Convenience Endpoints
**Purpose**: JSON-based upload and search for testing and API integration.

**JSON Upload**: `/upload/document_json`
**JSON Search**: `/upload/search_json`

**Features**: Same functionality as multipart endpoints but with JSON payloads for easier programmatic access.

## Tools Routes (`routes/tools.py`)

### Available Tools Listing
**Purpose**: List available tools with descriptions and usage examples.

**List Tools**: `/tools`
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

### Enhanced Web Search Tool
**Purpose**: Enhanced web search with structured results and caching.

**Web Search**: `/tools/web_search`
```python
@tools_router.post("/web_search")
async def web_search(
    request: WebSearchRequest
):
    # Enhanced web search with DuckDuckGo
```

**Features:**
- **Result Caching**: TTL-based caching (5 minutes default)
- **Safe Search**: Content filtering and safe search enforcement
- **Region Support**: Localized search results
- **Performance Optimization**: Fast response times with caching

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
  "total_results": 10,
  "search_time_ms": 150,
  "cached": false
}
```

## Health Routes (`routes/health.py`)

### Basic Health Check
**Purpose**: Essential service health monitoring for load balancers and monitoring systems.

**Endpoint**: `/health`
**Method**: GET

**Health Checks Performed:**
- **Database Connectivity**: Redis and ChromaDB connection status
- **Service Dependencies**: External service availability
- **Application State**: FastAPI application startup status
- **Resource Availability**: Basic resource health indicators

### Detailed Health Check
**Purpose**: Comprehensive health reporting with component-level diagnostics.

**Endpoint**: `/health/detailed`
**Method**: GET

**Comprehensive Checks:**
- **Database Health**: Individual database service status with latency
- **Memory Usage**: System memory consumption and limits
- **Service Performance**: Response times and error rates
- **Feature Availability**: Optional feature and capability status
- **Circuit Breaker Status**: Service circuit breaker states

### Kubernetes Health Endpoints
**Purpose**: Kubernetes-compatible health check endpoints for container orchestration.

**Readiness Probe**: `/health/readiness`
- Indicates service is ready to handle requests
- Checks all dependencies are available
- Returns 200 when ready, 503 when not ready

**Liveness Probe**: `/health/liveness`
- Indicates service is alive and functioning
- Basic health check without external dependencies
- Used by Kubernetes for container restart decisions

### Service-Specific Health Endpoints
**Purpose**: Individual service health monitoring for detailed diagnostics.

**Storage Health**: `/health/storage`
- Redis and ChromaDB specific health metrics
- Storage capacity and performance indicators
- Connection pool status and statistics

**Alerts Health**: `/health/alerts`
- Active alert monitoring and status
- Alert history and notification status
- Warning and error count tracking

**Startup Status**: `/health/startup`
- Application startup progress monitoring
- Startup error detection and reporting
- Initialization phase tracking

## Gateway Routes (`routes/gateway.py`)

### Gateway Health and Status
**Purpose**: API Gateway health monitoring and configuration access.

**Gateway Health**: `/gateway/health`
- Gateway service health and routing status
- Backend service connectivity
- Load balancing status

**Gateway Status**: `/gateway/status`
- Performance metrics and routing statistics
- Request distribution across backend services
- Error rates and response times

**Gateway Configuration**: `/gateway/config` (Admin access)
- Gateway configuration display
- Routing rules and policies
- Security settings and access controls

## Debug Routes (`routes/debug.py`)

### System Diagnostics
**Purpose**: Development and debugging endpoints for system analysis.

**Cache Statistics**: `/debug/cache`
```json
{
  "size": 1250,
  "max_size": 10000,
  "hit_count": 8500,
  "miss_count": 1750,
  "hit_rate": "82.9%",
  "memory_usage_mb": 64
}
```

**Redis Statistics**: `/debug/redis`
- Redis-specific performance metrics
- Memory usage and key distribution
- Connection status and throughput

**Vector Statistics**: `/debug/vector`
- ChromaDB performance metrics
- Vector collection statistics
- Embedding generation performance

**Service Statistics**: `/debug/services`
- All service statistics in single response
- Performance metrics across all components
- Error rates and health indicators

### Administrative Functions
**Purpose**: Administrative and maintenance operations.

**Configuration Display**: `/debug/config`
- Sanitized configuration display (secrets masked)
- Environment variable status
- Configuration validation results

**Endpoint Discovery**: `/debug/endpoints`
- Dynamic endpoint listing with HTTP methods
- Route documentation and parameter information
- API usage statistics

**Alert Management**: `/debug/alerts`
- Current system alerts and warnings
- Alert history and resolution status
- Alert configuration and thresholds

### Platform-Specific Considerations
**Purpose**: Handle platform-specific functionality and limitations.

**Windows Compatibility**: Resource module usage guarded for Windows compatibility
**Memory Monitoring**: Alternative memory monitoring methods for different platforms
**Performance Metrics**: Platform-appropriate performance measurement techniques

## Route Security and Validation

### Authentication and Authorization
**Purpose**: Secure access control across all route endpoints.

**Authentication Methods:**
- **User ID Resolution**: Automatic user identity resolution
- **Token Validation**: JWT token validation for protected endpoints
- **Session Management**: Secure session handling and validation

**Authorization Levels:**
- **Public**: Open access endpoints (health checks)
- **User**: User-authenticated endpoints (chat, memory)
- **Admin**: Administrative endpoints (debug, config)

### Input Validation and Sanitization
**Purpose**: Comprehensive input validation for security and data integrity.

**Validation Features:**
- **Type Validation**: Strict type checking for all inputs
- **Size Limits**: Request size and parameter limits
- **Content Filtering**: Malicious content detection and filtering
- **Parameter Validation**: Query parameter and path validation

### Error Handling and Response Standards
**Purpose**: Consistent error handling and response formats across all routes.

**Error Response Format:**
```json
{
  "error": {
    "type": "ValidationError",
    "message": "User-friendly error description",
    "details": "Technical error details for debugging",
    "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
    "timestamp": "2025-01-09T10:30:00Z",
    "path": "/api/memory/store",
    "method": "POST",
    "status_code": 400
  },
  "success": false
}
```

**Error Handling Features:**
- **Correlation IDs**: Request tracing across all endpoints
- **Structured Errors**: Consistent error format with detailed information
- **User-Friendly Messages**: Clear error messages for end users
- **Debug Information**: Technical details for developers and debugging

### Performance Optimization
**Purpose**: Route-level performance optimization and monitoring.

**Optimization Features:**
- **Response Caching**: Intelligent caching for appropriate endpoints
- **Connection Pooling**: Efficient database connection management
- **Async Processing**: Non-blocking request processing
- **Resource Management**: Proper resource cleanup and management

**User-Scoped Operations**: Most endpoints support user identification via headers for proper data isolation and security.
