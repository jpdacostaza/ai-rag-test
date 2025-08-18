# Architecture - Complete System Breakdown

## Core Application Layer

### FastAPI Backend (`core/main.py`)
The main application is a sophisticated FastAPI service that serves as the central hub:

**Application Setup:**
- **Lifespan Management**: Uses async context manager for proper startup/shutdown handling
- **Exception Handlers**: Global exception handling with correlation IDs and standardized responses
- **Middleware Stack**: Layered middleware for security, performance monitoring, rate limiting, correlation IDs, and request timeouts
- **Router Integration**: Modular router system with health, chat, models, upload, debug, memory, tools, gateway endpoints

**Key Functions:**
- `openai_chat_completions()`: Main OpenAI-compatible endpoint supporting both streaming and non-streaming responses
- `lifespan()`: Manages application lifecycle with memory service initialization and model cache setup
- `initialize_memory_service()`: Initializes global memory service with fallback handling
- `TimeoutMiddleware`: Prevents long-running requests (45s timeout) with proper error responses
- `CorrelationIdMiddleware`: Assigns unique correlation IDs for request tracing

**Advanced Features:**
- Multi-modal content support (text + images)
- Memory context injection with delimited boundaries
- Circuit breaker protection for LLM calls
- Streaming session management with heartbeats
- Comprehensive error handling with user-friendly messages

### Startup System (`core/startup.py`)
Robust, phased startup with idempotency guarantees:

**Phase Structure:**
1. **Phase 1 (5s)**: Quick initialization and CPU mode verification
2. **Phase 2 (10s)**: Storage and basic services setup
3. **Phase 3 (15s)**: Database connections (Redis/ChromaDB)
4. **Phase 4 (12min)**: Model and cache services (allows large model downloads)
5. **Phase 5 (10s)**: Background services initialization

**Key Functions:**
- `startup_event()`: Main coordinator with timeout management and duplicate prevention
- `_initialize_models_and_cache()`: Model preloading with eager loading for OpenWebUI
- `_initialize_database()`: Database manager setup with degraded mode fallback
- `_print_startup_summary()`: Consolidated health status reporting
- Duplicate message suppression system to prevent startup log spam

### Authentication & Security (`core/auth.py`)
Unified authentication manager consolidating all auth logic:

**Classes:**
- `UnifiedAuthManager`: Central auth handler with rate limiting and session management
- `AuthenticationError`: Custom exception for auth failures

**Key Methods:**
- `extract_user_from_request()`: Multi-strategy user extraction (user object, direct field, parameter)
- `authenticate_user_strict()`: Primary auth method with validation and rate limiting
- `validate_session_consistency()`: Ensures user session integrity across request
- `generate_session_token()`: Creates HMAC-signed session tokens
- `validate_session_token()`: Validates tokens with expiration checking

**Validation Features:**
- UUID, email, and user ID format validation
- Priority-based user extraction (id > email > username > name)
- In-memory rate limiting with sliding window
- Session token generation with HMAC signatures

## Service Layer Architecture

### LLM Service (`services/llm_service.py`)
Handles all Large Language Model interactions:

**Core Functionality:**
- `LLMService` class with Ollama/OpenAI dual support
- `call_llm()`: Unified LLM calling interface
- `call_ollama_llm()`: Ollama-specific implementation with error handling
- `call_openai_llm()`: OpenAI API integration
- `call_llm_stream()`: Streaming response handling
- `get_embeddings()`: Text embedding generation

**Advanced Features:**
- Configurable timeouts and connection pooling
- Automatic model detection and selection
- Error handling with circuit breaker integration
- Performance monitoring and metrics collection

### Database Manager (`services/database_manager.py`)
Comprehensive data persistence layer managing multiple storage systems:

**Core Components:**
- `DatabaseManager`: Main orchestrator class
- `ChromaClientProtocol`: Type-safe ChromaDB interface
- Connection factory integration for Redis/ChromaDB
- Enhanced connection pooling with health monitoring

**Key Functions:**
- `ensure_initialized()`: Async initialization with health checks
- `get_health_status()`: Comprehensive health reporting for all components
- `store_vector_data()`: Document embedding storage in ChromaDB
- `query_chroma()`: Semantic search with similarity scoring
- `get_chat_history()`/`store_chat_history()`: Redis-based conversation persistence
- `get_embeddings()`: Text-to-vector conversion
- `index_document_chunks()`: Document chunking and indexing

**Storage Systems:**
- **Redis**: Chat history, caching, session data
- **ChromaDB**: Vector embeddings, semantic search
- **Sentence Transformers**: Local embedding generation

### Chat Service (`services/chat_service.py`)
Business logic layer for chat operations:

**Core Class:**
- `ChatService`: Main service with dependency injection
- `ChatContext`: Context object for chat processing

**Processing Pipeline:**
- `process_chat()`: Main chat processing workflow
- `_build_context()`: Context assembly with user profiles
- `_check_cache()`: Response caching with time-sensitive detection
- `_generate_response()`: Response generation with tool integration
- `_generate_llm_response()`: LLM interaction with memory context
- `_enhance_with_web_search()`: Automatic web search enhancement
- `_store_conversation()`: Persistence and memory storage

## Data Flow Architecture

### Chat Completion Flow (Detailed)
1. **Request Reception**: FastAPI receives OpenAI-compatible request at `/v1/chat/completions`
2. **Validation**: Message structure validation, required field checking
3. **Identity Resolution**: Multi-strategy user identification via `resolve_user_id()`
4. **Middleware Processing**: 
   - Correlation ID assignment
   - Rate limiting check (token bucket algorithm)
   - Performance monitoring start
5. **Context Building**:
   - Chat history retrieval from Redis
   - Memory context from ChromaDB via semantic search
   - User profile integration
   - System prompt enhancement with memory injection
6. **LLM Interaction**:
   - Circuit breaker check
   - Model selection and availability verification
   - Streaming or non-streaming call based on request
   - Error handling and retry logic
7. **Response Processing**:
   - Response streaming with SSE (Server-Sent Events)
   - Heartbeat management for long connections
   - Response caching for non-time-sensitive queries
8. **Persistence**:
   - Chat history storage in Redis
   - Memory storage in ChromaDB for important conversations
   - Metrics and logging recording

### Memory Integration Flow
1. **Retrieval**: Query ChromaDB with user context and current message
2. **Relevance Scoring**: Semantic similarity calculation
3. **Context Injection**: Memory insertion into system prompt with delimiters
4. **LLM Processing**: Enhanced context sent to LLM
5. **Storage Decision**: Automatic assessment for long-term memory storage
6. **Persistence**: Important conversations stored as searchable memories

## Data Stores & Persistence

### Redis Configuration
- **Purpose**: Fast caching and chat history
- **Key Patterns**:
  - `chat:{user_id}:{hash}`: Cached responses
  - `user:{user_id}`: Chat history
  - `rate_limit:{user_id}`: Rate limiting counters
- **Features**: Async operations, connection pooling, health monitoring

### ChromaDB Configuration  
- **Purpose**: Vector storage and semantic search
- **Collections**: Dynamic collection creation per user/context
- **Features**: Embedding storage, similarity search, metadata filtering
- **Integration**: Sentence Transformers for local embeddings

### Embedding Pipeline
- **Providers**: Ollama, Sentence Transformers, OpenAI
- **Models**: Configurable embedding models per provider
- **Processing**: Text chunking, vectorization, storage with metadata

## Runtime Environment

### Docker Compose Orchestration
- **Redis**: Caching and session storage
- **ChromaDB**: Vector database for embeddings
- **Ollama**: Local LLM serving
- **Backend**: Main FastAPI application
- **Memory API**: Separate memory service
- **Pipelines**: Enhanced memory and anti-hallucination
- **Gateway**: Load balancing and security
- **OpenWebUI**: Frontend interface
- **Watchtower**: Container auto-updates

### Health & Monitoring
- **Startup Sequence**: Phased initialization with timeout protection
- **Health Endpoints**: Comprehensive service health reporting
- **Metrics**: Prometheus-compatible metrics export
- **Logging**: Structured JSON logging with correlation tracking
- **Circuit Breakers**: Service failure protection
