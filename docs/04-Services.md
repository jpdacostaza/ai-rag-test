# Services - Complete Service Layer Documentation

## Core LLM Services

### LLM Service (`services/llm_service.py`)
**Purpose**: Unified interface for Large Language Model interactions supporting multiple providers.

**Main Class: `LLMService`**
- **Initialization**: Configures provider settings, URLs, timeouts, and connection pools
- **Provider Support**: Ollama (local), OpenAI (API), with automatic fallback handling

**Core Methods:**
- `call_llm(messages, model, api_url, api_key)`: Main interface for LLM calls
  - Automatic provider detection based on configuration
  - Message format standardization across providers
  - Error handling with circuit breaker integration
  - Performance monitoring and metrics collection

- `call_ollama_llm(messages, model)`: Ollama-specific implementation
  - Uses `/api/chat` endpoint with streaming disabled
  - Configurable temperature (0.7) and top_p (0.9) parameters
  - 60-second timeout with 10-second connection timeout
  - Automatic model availability checking

- `call_openai_llm(messages, model, api_url, api_key)`: OpenAI API implementation
  - Full OpenAI API compatibility
  - Token limit management (configurable max tokens)
  - API key handling with environment variable support
  - Rate limiting and error handling

- `call_llm_stream(messages, model, session_id)`: Streaming response handling
  - Server-Sent Events (SSE) compatible output
  - Session management for streaming connections
  - Heartbeat mechanism for long-running streams
  - Token-by-token response streaming

- `get_embeddings(text, model)`: Text embedding generation
  - Multi-provider embedding support (Ollama, OpenAI, Sentence Transformers)
  - Batch processing for multiple texts
  - Caching for frequently requested embeddings
  - Vector normalization and format standardization

**Advanced Features:**
- Connection pooling with configurable limits
- Automatic retry logic with exponential backoff
- Circuit breaker protection against service failures
- Comprehensive error logging with context
- Performance metrics for response times and success rates

## Data & Storage Services

### Database Manager (`services/database_manager.py`)
**Purpose**: Comprehensive data persistence layer managing Redis, ChromaDB, and embeddings.

**Main Class: `DatabaseManager`**
- **Multi-Store Orchestration**: Coordinates Redis caching, ChromaDB vectors, and embedding models
- **Health Monitoring**: Continuous health checks for all storage components
- **Connection Management**: Advanced connection pooling and retry logic

**Core Initialization:**
- `ensure_initialized()`: Async initialization with component verification
  - Redis connection establishment with auth handling
  - ChromaDB client setup with collection management
  - Embedding model loading with GPU/CPU detection
  - Health status verification for all components

**Redis Operations:**
- `get_chat_history(user_key, limit)`: Retrieves conversation history
  - JSON deserialization with error handling
  - Configurable history limits (default 10 messages)
  - Automatic cleanup of old conversations
  - User isolation with key prefixing

- `store_chat_history(user_key, messages)`: Persists conversations
  - Atomic operations with rollback on failure
  - Message deduplication and validation
  - Automatic timestamp addition
  - Conversation threading support

- `get_cache(key)` / `set_cache(key, value, ttl)`: General caching
  - TTL-based expiration with configurable defaults
  - JSON serialization for complex objects
  - Cache invalidation and warming strategies
  - Memory pressure monitoring

**ChromaDB Vector Operations:**
- `store_vector_data(content, metadata)`: Document embedding storage
  - Automatic text chunking for large documents
  - Metadata enrichment with timestamps and user context
  - Duplicate detection and handling
  - Batch processing for efficiency

- `query_chroma(query, limit, filters)`: Semantic search
  - Vector similarity search with configurable distance metrics
  - Result ranking and filtering
  - Metadata-based query refinement
  - Performance optimization for large collections

- `index_document_chunks(documents, user_id)`: Document processing pipeline
  - Text preprocessing and normalization
  - Intelligent chunking based on content structure
  - Embedding generation and storage
  - Progress tracking for large document sets

**Health & Monitoring:**
- `get_health_status()`: Comprehensive health reporting
  - Component-specific health checks (Redis, ChromaDB, embeddings)
  - Performance metrics (latency, success rates)
  - Resource utilization monitoring
  - Alert generation for critical issues

- `is_redis_available()` / `is_chromadb_available()` / `is_embeddings_available()`: Component health
  - Real-time availability checking
  - Graceful degradation support
  - Fallback mechanism activation
  - Service recovery detection

### Authentication & Identity Services

### Auth Validator (`services/auth_validator.py`)
**Purpose**: Unified user authentication and validation system eliminating duplicate auth logic.

**Main Classes:**
- `UserIDType`: Enumeration of user identifier types (pipeline injection, email, UUID, username, name, anonymous)
- `ValidationLevel`: Strictness levels (strict, moderate, permissive)
- `AuthConfig`: Configuration for validation behavior
- `UserContext`: Rich user context with metadata and validation scoring
- `AuthValidator`: Main validation service

**Core Methods:**
- `extract_and_validate_user(request_data)`: Primary authentication method
  - Priority-based extraction: pipeline injection > user object > direct field > message metadata > anonymous
  - Comprehensive validation with configurable strictness
  - Session consistency verification
  - User context enrichment with metadata

- `extract_pipeline_user_id(messages)`: Pipeline injection handling
  - Searches for `AUTHENTICATED_USER_ID` in system messages
  - Supports Enhanced Memory Pipeline integration
  - Extracts user context from pipeline metadata
  - Validates extracted user identifiers

- `is_valid_user_id(user_id)`: Format validation
  - UUID format checking with regex validation
  - Email format validation with domain verification
  - Username format validation (alphanumeric with limited special chars)
  - Length constraints and invalid pattern detection

- `create_session(user_context)` / `get_session(session_id)`: Session management
  - Session creation with unique identifiers
  - Session timeout handling (configurable, default 24 hours)
  - Session cleanup and garbage collection
  - Context preservation across requests

### User Identity (`services/user_identity.py`)
**Purpose**: User identity resolution with multiple extraction strategies.

**Core Function:**
- `resolve_user_id(request, body, messages)`: Multi-strategy user identification
  - Body inspection for user objects and direct fields
  - Header extraction for authenticated sessions
  - Pipeline message analysis for injected user context
  - Bearer token parsing and validation
  - Session fingerprinting as fallback

**Identity Sources (Priority Order):**
1. Body `__user__` object (highest priority)
2. Direct `user_id` field in body
3. Message metadata with user information
4. Authorization headers (Bearer tokens)
5. Session fingerprinting based on request characteristics

### User Profiles (`services/user_profiles.py`)
**Purpose**: Lightweight user profile management and context building.

**Main Class: `UserProfileManager`**
- `extract_user_info(message)`: Information extraction from natural language
  - Name extraction with greeting patterns
  - Location identification from conversational cues
  - Age detection and validation
  - Interest and preference inference

- `update_profile(user_id, profile_data)`: Profile persistence
  - Incremental profile updates
  - Data validation and sanitization
  - Preference tracking and learning
  - Privacy-aware information handling

- `build_context_for_llm(user_id)`: LLM context enhancement
  - Profile-based personalization
  - Context-aware greeting generation
  - Preference integration for response customization
  - History-based context enrichment

## Tool & Utility Services

### Tool Service (`services/tool_service.py`)
**Purpose**: Tool detection, execution, and integration system.

**Main Class: `ToolService`**
- **Tool Detection**: Intelligent tool selection based on user intent
- **Execution Management**: Safe tool execution with error handling
- **Response Integration**: Tool output formatting and integration

**Supported Tools:**
- `_execute_time_tool()`: Time and timezone queries
  - Robust location extraction from natural language
  - TimeAndDate.com integration for accurate time data
  - Timezone conversion and DST handling
  - Geographic name resolution and validation

- `_execute_weather_tool()`: Weather information retrieval
  - Location-based weather data fetching
  - Forecast integration with multiple day support
  - Weather condition interpretation
  - Integration with KNMI and other weather APIs

- `_execute_conversion_tool()`: Unit conversion utility
  - Multi-unit support (length, weight, temperature, currency)
  - Precision handling and rounding rules
  - Unit validation and standardization
  - Historical conversion rate support

- `_execute_search_tool()`: Web search integration
  - DuckDuckGo search API integration
  - Result filtering and ranking
  - Safe search and content filtering
  - Structured result formatting

- `_execute_python_tool()`: Python code execution
  - Sandboxed code execution environment
  - Security restrictions and validation
  - Output capture and formatting
  - Error handling and user feedback

**Advanced Features:**
- Intent recognition with natural language processing
- Context-aware tool selection
- Error recovery and fallback strategies
- Performance monitoring and optimization
- Security validation for all tool inputs

### Streaming Service (`services/streaming_service.py`)
**Purpose**: Management of streaming sessions and real-time communication.

**Core Functionality:**
- Session lifecycle management (creation, monitoring, cleanup)
- Streaming metadata tracking and persistence
- Connection state management and heartbeat monitoring
- Error handling and recovery for streaming connections

### Model Management Services

### Model Manager (`services/model_manager.py`)
**Purpose**: Model discovery, caching, and lifecycle management.

**Key Functions:**
- `refresh_model_cache()`: Dynamic model discovery from Ollama
- `pull_model(model_name)`: Automatic model downloading
- `ensure_model_available()`: Model availability verification with auto-pull
- `list_available_models()`: OpenAI-compatible model listing
- `delete_model()`: Model removal and cleanup

### Model Preloader (`services/model_preloader.py`)
**Purpose**: Essential model preloading for OpenWebUI integration.

**Core Functions:**
- `initialize_models_for_openwebui()`: Eager model loading
- Model availability verification and preloading
- Embedding model initialization and validation
- Performance optimization for model loading

## Adapter Services

### Redis Service (`services/redis_service.py`)
**Purpose**: Async Redis wrapper with error handling and connection management.

**Core Methods:**
- `set(key, value, ttl)` / `get(key)`: Basic key-value operations
- `list_push(key, values)` / `list_get(key, start, end)`: List operations
- `exists(key)` / `delete(key)`: Key management
- `health_check()`: Connection validation
- `get_stats()`: Performance and usage statistics

### Vector Service (`services/vector_service.py`)
**Purpose**: ChromaDB wrapper with comprehensive vector operations.

**Core Methods:**
- `store_embeddings(collection, documents, embeddings, metadata)`: Vector storage
- `search(collection, query_embedding, n_results, filters)`: Similarity search
- `create_collection()` / `delete_collection()`: Collection management
- `get_collection_count()`: Statistics and monitoring
- `health_check()`: Service availability verification

## Service Dependencies & Integration

### Dependencies (`services/dependencies.py`)
**Purpose**: Dependency injection container for service management.

**Provided Dependencies:**
- `get_cache_service()`: Cache service with fallback handling
- `get_memory_service()`: Memory service with legacy compatibility
- `get_database_manager()`: Database manager singleton
- `get_redis_service()` / `get_vector_service()`: Specialized service adapters
- `get_chat_service()`: Chat service with injected dependencies

**Integration Patterns:**
- FastAPI dependency injection compatibility
- Service lifecycle management
- Error handling and graceful degradation
- Legacy system compatibility layers
