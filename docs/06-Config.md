# Configuration - Comprehensive System Configuration Management

## Unified Configuration System (`config/config_unified.py`)

### Configuration Architecture
**Purpose**: Centralized configuration management consolidating all system settings into a single, environment-aware configuration system.

**Replaces Multiple Config Files:**
- `config.py` (main backend config)
- `config_minimal.py` (pipeline config)
- `core/config.py` (centralized config)
- `pipelines/config.py` (pipeline specific)

### Configuration Singleton Pattern
**Purpose**: Ensure consistent configuration access across all system components.

**Usage Example:**
```python
from config.config_unified import Config

# Get singleton instance
config = Config.get_instance()

# Access configuration sections
model_settings = config.model
memory_settings = config.memory
database_settings = config.database
```

**Benefits:**
- **Consistency**: Single source of truth for all configuration
- **Environment Awareness**: Automatic environment variable loading
- **Type Safety**: Dataclass-based configuration with type hints
- **Validation**: Built-in configuration validation and error checking

## Model Configuration (`ModelConfig`)

### Primary Model Settings
**Purpose**: Core language model configuration for primary AI operations.

**Configuration Options:**
- **Default Model**: `"hf.co/lmstudio-community/Qwen3-4B-Instruct-2507-GGUF:Q4_K_M"`
  - Upgraded to Qwen3 4B parameter model for enhanced performance
  - Quantized Q4_K_M format for optimal memory usage
- **Provider**: Configurable between Ollama, OpenAI, and HuggingFace
- **Context Length**: 8192 tokens default, 16384 for memory contexts

### Ollama Configuration
**Purpose**: Local model deployment and management via Ollama.

**Settings:**
- **Base URL**: `"http://ollama:11434"` (Docker network endpoint)
- **Enable Ollama**: Boolean flag for Ollama usage
- **Auto Pull Models**: Automatic model download when requested
- **Model Cache TTL**: 300 seconds for model availability caching

**Environment Variables:**
- `OLLAMA_BASE_URL`: Ollama service endpoint
- `USE_OLLAMA`: Enable/disable Ollama integration
- `AUTO_PULL_MODELS`: Automatic model downloading
- `MODEL_CACHE_TTL`: Model cache duration

### OpenAI Configuration
**Purpose**: OpenAI API integration for cloud-based model access.

**Settings:**
- **API Base URL**: `"https://api.openai.com/v1"` (configurable for API proxies)
- **API Key**: Environment-based API key loading
- **Max Tokens**: 8192 tokens maximum per request
- **Timeout**: 180 seconds for API requests

**Environment Variables:**
- `OPENAI_API_BASE_URL`: OpenAI API endpoint
- `OPENAI_API_KEY`: API authentication key
- `OPENAI_API_MAX_TOKENS`: Maximum tokens per request
- `OPENAI_API_TIMEOUT`: Request timeout duration

## Memory Configuration (`MemoryConfig`)

### Memory API Settings
**Purpose**: Memory service endpoint and communication configuration.

**Configuration:**
- **API URL**: `"http://backend-memory-api:8080"` (Docker service endpoint)
- **API Port**: 8080 for memory service
- **Timeout**: 10.0 seconds for memory operations
- **Health Check**: Automatic service availability checking

**Environment Variables:**
- `MEMORY_API_URL`: Memory service endpoint
- `MEMORY_API_PORT`: Memory service port
- `MEMORY_TIMEOUT`: Memory operation timeout

### Memory Behavior Settings
**Purpose**: Memory system behavior and constraints configuration.

**Key Settings:**
- **Max Memories**: 5 memories per retrieval (controlled by OpenWebUI function)
- **Max Documents**: 50 documents maximum per user
- **Auto Store Enabled**: Automatic memory storage for important conversations
- **Auto Store Threshold**: 3 messages before automatic storage
- **Hybrid Search**: Combined semantic and keyword search

**Important Note**: `retrieval_threshold` is controlled by OpenWebUI Function, not backend configuration.

**Environment Variables:**
- `MAX_MEMORIES`: Maximum memories per query
- `MEMORY_MAX_DOCUMENTS`: Document limit per user
- `MEMORY_AUTO_STORE`: Enable automatic memory storage
- `MEMORY_AUTO_STORE_THRESHOLD`: Message threshold for auto-storage
- `MEMORY_HYBRID_SEARCH`: Enable hybrid search capabilities

## Database Configuration (`DatabaseConfig`)

### Redis Configuration
**Purpose**: Redis cache and session storage configuration.

**Settings:**
- **Host**: `"backend-redis"` (Docker service name)
- **Port**: 6379 (standard Redis port)
- **Database**: 0 (default Redis database)
- **Password**: Optional password authentication

**Environment Variables:**
- `REDIS_HOST`: Redis server hostname
- `REDIS_PORT`: Redis server port
- `REDIS_DB`: Redis database number
- `REDIS_PASSWORD`: Redis authentication password

**Special Handling**: Empty password strings converted to `None` to resolve Redis authentication issues.

### ChromaDB Configuration
**Purpose**: Vector database configuration for embeddings and semantic search.

**Settings:**
- **Host**: `"backend-chroma"` (Docker service name)
- **Port**: 8000 (ChromaDB HTTP port)
- **HTTP Mode**: `use_http_chroma = True` for HTTP API access
- **Collection Management**: Automatic collection creation and management

**Environment Variables:**
- `CHROMA_HOST`: ChromaDB server hostname
- `CHROMA_PORT`: ChromaDB server port
- `USE_HTTP_CHROMA`: Enable HTTP API mode

### Embedding Configuration
**Purpose**: Text embedding model configuration optimized for ARM64 architecture.

**Optimized Settings:**
- **Model**: `"sentence-transformers/all-MiniLM-L6-v2"`
  - 45MB model size for efficient memory usage
  - 2.5x faster than nomic-embed-text on ARM64
  - Excellent performance on Orange Pi 5 Plus hardware
- **Provider**: HuggingFace for direct model access
- **Storage**: `"./storage/sentence_transformers"` for model caching

**Environment Variables:**
- `EMBEDDING_MODEL`: Embedding model name
- `EMBEDDING_PROVIDER`: Provider selection (ollama/huggingface/sentence_transformers)
- `SENTENCE_TRANSFORMERS_HOME`: Model storage directory

## Service Configuration (`ServiceConfig`)

### Backend API Configuration
**Purpose**: Main backend service network and endpoint configuration.

**Settings:**
- **Host**: `"0.0.0.0"` (bind to all interfaces)
- **Port**: 3000 (FastAPI application port)
- **URL**: `"http://backend:3000"` (internal Docker network)

**Environment Variables:**
- `BACKEND_HOST`: Service bind address
- `BACKEND_PORT`: Service port number
- `BACKEND_URL`: Service external URL

### Memory API Configuration
**Purpose**: Memory service specific endpoint configuration.

**Settings:**
- **Host**: `"0.0.0.0"` (bind to all interfaces)
- **Port**: 5001 (memory service port)
- **URL**: `"http://memory-api:5001"` (internal Docker network)

### OpenWebUI Integration
**Purpose**: OpenWebUI frontend integration configuration.

**Settings:**
- **URL**: `"http://openwebui:8080"` (OpenWebUI service endpoint)
- **Integration**: Seamless frontend-backend communication
- **Function Integration**: OpenWebUI function compatibility

## Additional Configuration Files

### Gateway Configuration (`config/gateway_config.py`)
**Purpose**: API Gateway specific configuration and routing rules.

**Features:**
- **Target Services**: Backend service endpoint definitions
- **Load Balancing**: Service instance management and health checking
- **Routing Policies**: Request routing based on patterns and rules
- **Circuit Breaker**: Service failure detection and recovery

### Pipeline Configuration (`config/pipeline_config.py`)
**Purpose**: Processing pipeline configuration for memory and data processing.

**Components:**
- **Memory Pipeline**: Memory processing workflow configuration
- **Data Pipeline**: Data ingestion and processing settings
- **Processing Stages**: Individual pipeline stage configuration
- **Error Handling**: Pipeline error recovery and retry logic

### Autonomous Configuration (`config/autonomous_config.py`)
**Purpose**: Autonomous system behavior and decision-making configuration.

**Features:**
- **Decision Thresholds**: Autonomous decision-making criteria
- **Action Policies**: Automated action execution rules
- **Learning Settings**: System learning and adaptation configuration
- **Safety Limits**: Autonomous operation safety constraints

### RAG System Configuration (`config/rag_system_config.py`)
**Purpose**: Retrieval-Augmented Generation system configuration.

**Components:**
- **Retrieval Settings**: Document retrieval parameters
- **Indexing Configuration**: Document indexing and processing
- **Generation Parameters**: Text generation settings
- **Context Management**: Context window and memory management

### Prompt Templates (`config/unified_prompt*.json`)
**Purpose**: System prompt templates for different conversation contexts.

**Template Types:**
- **unified_prompt.json**: Full-featured system prompt with memory integration
- **unified_prompt_minimal.json**: Minimal system prompt for lightweight usage
- **Custom Prompts**: Specialized prompts for specific use cases

**Features:**
- **Memory Integration**: Prompts with memory context instructions
- **Role Definition**: Clear AI assistant role and behavior definition
- **Context Awareness**: Instructions for context-aware responses
- **User Interaction**: Guidelines for natural user interaction

### Weather Tools Configuration (`config/weather_tools_config.json`)
**Purpose**: Weather service integration and tool configuration.

**Configuration:**
- **API Endpoints**: Weather service API endpoints
- **Location Services**: Geographic location resolution
- **Data Sources**: Weather data provider configuration
- **Cache Settings**: Weather data caching and refresh intervals

## Security and Performance Configuration

### Security Configuration
**Purpose**: Comprehensive security settings across all components.

**Key Areas:**
- **Authentication**: JWT secret keys and token expiration
- **Authorization**: Role-based access control settings
- **CORS Settings**: Cross-origin resource sharing configuration
- **Rate Limiting**: Request rate limiting and throttling
- **Encryption**: Data encryption keys and algorithms

**Environment Variables:**
- `JWT_SECRET_KEY`: JWT token signing key
- `CORS_ORIGINS`: Allowed CORS origins
- `RATE_LIMIT_*`: Various rate limiting settings
- `ENCRYPTION_KEY`: Data encryption key

### Performance Configuration
**Purpose**: System performance optimization and monitoring.

**Components:**
- **Caching**: Redis cache configuration and TTL settings
- **Connection Pooling**: Database connection pool settings
- **Resource Limits**: Memory and CPU usage limits
- **Monitoring**: Performance metrics collection settings

### Logging Configuration
**Purpose**: Comprehensive logging configuration across all components.

**Features:**
- **Log Levels**: Configurable logging verbosity
- **Log Formats**: Structured logging format configuration
- **Log Destinations**: File, console, and remote logging
- **Correlation IDs**: Request tracing configuration

**Environment Variables:**
- `LOG_LEVEL`: Global logging level
- `LOG_FORMAT`: Logging format (JSON/text)
- `LOG_FILE`: Log file destination
- `ENABLE_REQUEST_LOGGING`: Request/response logging toggle

## Environment-Specific Recommendations

### Development Environment
**Purpose**: Optimized configuration for development workflow.

**Recommendations:**
- **Debug Mode**: Enable detailed debugging and logging
- **Hot Reload**: Enable automatic code reload
- **Relaxed Security**: Reduced security for development ease
- **Local Services**: Configure for local service endpoints

### Production Environment
**Purpose**: Production-ready configuration optimization.

**Recommendations:**
- **Security Hardening**: Maximum security configuration
- **Performance Tuning**: Optimized performance settings
- **Monitoring**: Comprehensive monitoring and alerting
- **Error Handling**: Production-appropriate error responses

### Configuration Normalization
**Purpose**: Consistency improvements across configuration files.

**Current Issues and Recommendations:**
- **CORS Environment Names**: Normalize CORS environment variable names across Docker Compose and code
- **Logging Toggles**: Add toggles for uvicorn/access logs and validation strictness
- **Validation Settings**: Standardize validation strictness controls
- **Service Discovery**: Implement service discovery for dynamic endpoint configuration

## Legacy Compatibility and Migration

### Legacy Alias Support
**Purpose**: Maintain compatibility with existing configuration references.

**Features:**
- **Backward Compatibility**: Support for legacy configuration keys
- **Gradual Migration**: Smooth transition to new configuration system
- **Deprecation Warnings**: Clear warnings for deprecated configuration options
- **Migration Tools**: Automated configuration migration utilities

### Configuration Validation
**Purpose**: Comprehensive configuration validation and error prevention.

**Validation Types:**
- **Type Checking**: Ensure correct data types for all settings
- **Range Validation**: Verify values are within acceptable ranges
- **Dependency Validation**: Check interdependent settings
- **Environment Validation**: Verify required environment variables exist
