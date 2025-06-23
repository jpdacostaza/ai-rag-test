# Advanced LLM Backend with Tool-Augmented Intelligence & Enhanced Human Logging

> **📚 Documentation**: For comprehensive project documentation, reports, and technical details, see the [readme/](readme/) directory which contains all project documentation organized by category.

## 🚀 Project Overview

This is a **production-ready, enterprise-grade** FastAPI backend that provides **human-like reasoning** and **tool-augmented AI** capabilities with comprehensive system monitoring and **beautiful human-readable logging**. The system combines real-time tools, semantic memory, robust caching, fault-tolerant architecture, and OpenAI-compatible APIs to create an intelligent assistant that can:

- 🤖 **Local LLM with Ollama** - Default llama3.2:3b model with automatic verification and download
- 🎨 **Enhanced Human-Readable Logging** - Beautiful, colorful logs with emojis and clear status indicators
- 🧠 **Advanced Embeddings** - Qwen/Qwen3-Embedding-0.6B model with automatic fallback support
- 🔴 **Robust Redis Integration** - Connection pooling, health monitoring, and graceful degradation
- 🐍 **Secure Python Execution** - Sandboxed code execution with timeout protection
- 🌐 **Intelligent Web Search** - Real-time web search with automatic knowledge storage
- 📚 **Wikipedia Integration** - Search and retrieve summaries with caching
- 🧮 **Mathematical Calculator** - Safe expression evaluation with comprehensive operators
- 🌡️ **Weather & Time Services** - Real-time weather and timezone information
- 💾 **Semantic Memory** - Vector embeddings with ChromaDB for knowledge storage
- 🚀 **Streaming Responses** - Real-time API responses with error recovery
- 👀 **System Watchdog** - Automated health monitoring and recovery
- 🏥 **Health Checks** - Comprehensive service monitoring and diagnostics
- 🔗 **OpenWebUI Compatible** - Seamless integration with modern frontends
- 📥 **File Upload & RAG** - Document processing with vector storage and semantic search

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   OpenWebUI     │◄──►│  FastAPI Backend │◄──►│     Ollama      │
│   (Frontend)    │    │  (Tool Engine)   │    │  (llama3.2:3b)  │
│    Port 3000    │    │    Port 8001     │    │   Port 11434    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                    ┌───────────┼───────────┐
                    ▼           ▼           ▼
            ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
            │    Redis    │ │  ChromaDB   │ │ AI Tools    │
            │ (Cache &    │ │ (Semantic   │ │ (Real-time  │
            │ Sessions)   │ │  Memory)    │ │ Functions)  │
            │ Port 6379   │ │ Port 8002   │ │ (Weather,   │
            └─────────────┘ └─────────────┘ │ Time, etc.) │
                    ▲           ▲           └─────────────┘
                    └───────────┼───────────┐
                                ▼           ▼
                    ┌─────────────────────────┐
                    │    Enhanced Logging     │
                    │   & System Watchdog     │
                    │  (Health Monitoring &   │
                    │   Automatic Recovery)   │
                    └─────────────────────────┘
```

### 🔄 Request Flow
All user requests flow through your backend - **no direct access to Ollama**:

```
User → OpenWebUI → Your Backend → [Tools/RAG/Cache] → Ollama → Response
```

**Security & Control:**
- ✅ All requests authenticated with API key
- ✅ No direct Ollama access (port 11434 internal only)
- ✅ Complete request logging and monitoring
- ✅ Rate limiting and caching handled by backend
- ✅ RAG and tool integration on every request

## 📁 Complete Project Structure

```
opt/backend/
├── 🎯 Core Application Files
│   ├── main.py                     # FastAPI app with tool integration & all endpoints
│   ├── app.py                      # ASGI entrypoint for production deployment
│   ├── ai_tools.py                 # 8 production tools (Python, web, weather, etc.)
│   ├── database_manager.py         # Centralized database operations (Redis + ChromaDB)
│   ├── database.py                 # Database management with connection pooling
│   ├── rag.py                      # RAG (Retrieval-Augmented Generation) implementation
│   └── upload.py                   # File upload and document processing
│
├── 🧠 Enhanced Intelligence
│   ├── adaptive_learning.py        # Self-learning system with feedback loops
│   ├── enhanced_integration.py     # Enhanced endpoints for advanced features
│   ├── enhanced_document_processing.py  # Advanced document chunking & analysis
│   └── model_manager.py            # LLM model management and optimization
│
├── 🛡️ System Management
│   ├── error_handler.py            # Enterprise error handling & recovery
│   ├── watchdog.py                 # System health monitoring & alerting
│   ├── human_logging.py            # Beautiful console logging with emojis
│   ├── feedback_router.py          # User feedback collection & processing
│   └── storage_manager.py          # File storage and management
│
├── 🚀 Deployment & Configuration
│   ├── Dockerfile                  # Optimized container build (llama user)
│   ├── docker-compose.yml          # Multi-service orchestration
│   ├── requirements.txt            # Python dependencies with versions
│   ├── persona.json               # AI personality configuration
│   └── refresh-models.py           # Python model refresh utility
│   └── persona.json               # AI personality configuration
│
├── � Shell Scripts & Utilities
│   ├── startup.sh                  # Container initialization script
│   ├── fix-permissions.sh          # Linux permissions setup script
│   ├── manage-models.sh            # Model management utilities
│   ├── test-model.sh               # Model testing script
│   ├── add-model.sh                # Add new models to Ollama
│   ├── enhanced-add-model.sh       # Enhanced model addition script
│   ├── debug-openwebui-models.sh   # OpenWebUI model debugging
│   ├── setup-github.sh             # GitHub repository setup
│   └── refresh-models.py           # Python model refresh utility
│
├── �📁 Data Storage (Persistent Volumes)
│   ├── storage/backend/            # Application data storage
│   ├── storage/models/             # Embedding model cache (Qwen3-0.6B)
│   ├── storage/chroma/             # Vector database (ChromaDB + ONNX cache)
│   ├── storage/redis/              # Redis persistence data
│   ├── storage/ollama/             # LLM models (llama3.2:3b + keys)
│   └── storage/openwebui/          # Web UI data & vector DB
│
└── 📚 Documentation
    └── README.md                   # This comprehensive guide
```

### 🔧 Core Components Details

#### **main.py** - FastAPI Application Core (1400+ lines)
- **20+ API Endpoints**: Chat, health, models, feedback, enhanced features
- **Tool Orchestration**: Intelligent tool detection, selection, and execution
- **Streaming Support**: Server-sent events with error recovery
- **Session Management**: Concurrent streaming with automatic cleanup
- **OpenAI Compatibility**: Full `/v1/chat/completions` and `/v1/models` support

#### **ai_tools.py** - Advanced Tool Engine (367 lines)
- **8 Production Tools**: Time, weather, Python execution, web search, Wikipedia, math, text chunking, unit conversion
- **Security**: RestrictedPython sandbox with timeout protection
- **Intelligence**: Automatic knowledge storage and semantic indexing
- **Performance**: Caching and optimized execution

#### **database_manager.py** + **database.py** - Data Management
- **Dual Database**: Redis (cache/sessions) + ChromaDB (vectors/memory)
- **Connection Pooling**: Optimized with automatic retry and recovery
- **Embedding Pipeline**: Qwen3-Embedding-0.6B with fallback support
- **Health Monitoring**: Real-time status and performance metrics

#### **Enhanced Intelligence Modules**
- **adaptive_learning.py**: Self-learning with 5 feedback types and pattern recognition
- **enhanced_document_processing.py**: 5 chunking strategies for 5 document types
- **enhanced_integration.py**: 7 advanced endpoints for learning and documents

#### **System Management**
- **error_handler.py**: 5 specialized error handlers with graceful degradation
- **watchdog.py**: 24/7 monitoring of 3 core services with health history
- **human_logging.py**: Beautiful logs with emojis and color coding

## 🔬 Complete System Capabilities

### 🤖 LLM & Model Management
- **Default Model**: llama3.2:3b (2GB) with automatic download
- **Model Verification**: Startup checks and manual verification endpoints
- **Embedding System**: Qwen3-Embedding-0.6B (1024-dim vectors) with fallback
- **OpenAI Compatibility**: Full API compatibility with streaming support

### 🛠️ Tool Integration (8 Tools)
1. **⏰ Time & Date**: Current time with timezone support + external API lookup
2. **🌤️ Weather**: Dual-source weather (Open-Meteo + WeatherAPI.com)
3. **🐍 Python Execution**: Sandboxed code execution with security controls
4. **🌐 Web Search**: DuckDuckGo search with automatic knowledge storage
5. **📚 Wikipedia**: Article retrieval with configurable summary length
6. **🧮 Mathematics**: Safe expression evaluation and calculations
7. **🔄 Text Processing**: Advanced chunking with overlap control
8. **📐 Unit Conversion**: 6 categories, 20+ units (temp, length, weight, etc.)

### 🧠 Memory & Storage Systems
- **Short-term Memory**: Redis-based chat history with TTL management
- **Long-term Memory**: ChromaDB vector storage with semantic search
- **Automatic Indexing**: Web search results and interactions stored
- **Context Awareness**: Semantic retrieval across user sessions
- **Persistent Storage**: Docker volumes for data persistence

### 🔒 Security & Performance
- **Sandboxed Execution**: RestrictedPython for code safety
- **Connection Pooling**: Optimized database connections
- **Timeout Protection**: Configurable timeouts for all operations
- **Input Validation**: Comprehensive request validation
- **Error Recovery**: Automatic retry logic for transient failures

### 📊 Enhanced Intelligence Features
- **Adaptive Learning**: 5 feedback types with pattern recognition
- **Document Processing**: 5 chunking strategies for 5 document types
- **User Insights**: Personalized recommendations and preferences
- **Quality Scoring**: Content quality assessment and optimization
- **Performance Analytics**: Response time and engagement tracking

### 🏥 Monitoring & Health
- **System Watchdog**: 24/7 monitoring of 3 core services
- **Health Endpoints**: 7 health check endpoints with detailed status
- **Performance Metrics**: Response time, error rates, resource usage
- **Health History**: 24-hour rolling history with trend analysis
- **Graceful Degradation**: Continues operation when subsystems fail

### 🔌 API Architecture (20+ Endpoints)
- **Chat Endpoints**: Main chat, OpenAI-compatible, enhanced chat
- **Model Management**: List, verify, download models
- **Health Monitoring**: Basic, detailed, service-specific health
- **Document Processing**: Upload, advanced processing, RAG
- **Enhanced Features**: Learning feedback, insights, strategies
- **Streaming Support**: Real-time responses with session management

### 🛠️ Advanced Tool Suite

#### 🔧 Available Tools (ai_tools.py)
1. **⏰ Time & Date Services**
   - `get_current_time(timezone)` - Current time with timezone support
   - `get_time_from_timeanddate(location)` - Time lookup from external API

2. **🌤️ Weather Services**
   - `get_weather(city)` - Open-Meteo weather with WeatherAPI.com fallback
   - `get_weather_weatherapi(city)` - Direct WeatherAPI.com integration

3. **🐍 Secure Python Code Execution**
   - `run_python_code(code)` - Sandboxed Python execution with timeout protection
   - RestrictedPython environment with security controls
   - Result capturing and error handling

4. **🌐 Intelligent Web Search**
   - DuckDuckGo search with automatic knowledge storage
   - Real-time web content retrieval and indexing
   - Semantic storage for future reference

5. **📚 Wikipedia Integration**
   - `wikipedia_search(query, sentences)` - Smart article retrieval with summary extraction
   - Configurable summary length (1-10 sentences)
   - Automatic caching and error handling

6. **🧮 Mathematical Computing**
   - Safe expression evaluation with comprehensive operator support
   - Mathematical functions and calculations
   - Error handling for invalid expressions

7. **🔄 Text Processing**
   - `chunk_text(text, chunk_size, chunk_overlap)` - Advanced text chunking with overlap
   - Recursive character splitting for optimal content organization
   - Configurable chunk sizes and overlap parameters

8. **📐 Unit Conversion**
   - `convert_units(value, from_unit, to_unit)` - Comprehensive unit conversion
   - Temperature: Celsius ↔ Fahrenheit ↔ Kelvin
   - Length: meters ↔ feet ↔ inches ↔ yards ↔ kilometers ↔ miles
   - Weight: kilograms ↔ pounds ↔ ounces ↔ grams
   - Volume: liters ↔ gallons ↔ milliliters ↔ fluid ounces
   - Speed: m/s ↔ km/h ↔ mph ↔ knots
   - Energy: joules ↔ calories ↔ BTU ↔ kWh

### 🧠 Intelligent Memory System
- **Short-term Memory**: Redis-based chat history with automatic expiration
- **Long-term Memory**: ChromaDB semantic memory with vector embeddings
- **Automatic Knowledge Storage**: Web search results automatically indexed for future retrieval
- **Context-Aware Retrieval**: Semantic search across user's historical interactions
- **Context-Aware Caching**: Smart cache keys based on user intent

### 🔄 Streaming & API Compatibility
- **Real-time Streaming**: Server-sent events (SSE) for live responses with error recovery
- **OpenAI Compatible**: `/v1/chat/completions` and `/v1/models` endpoints with full feature parity
- **Multiple API Formats**: Support for various client integrations and frameworks
- **Session Management**: Handle concurrent streaming sessions with automatic cleanup
- **Request Tracking**: Unique request IDs for debugging and performance analysis

### 🔒 Security & Performance
- **Sandboxed Code Execution**: Restricted Python environment with security controls
- **Intelligent Caching**: Redis-based response caching with TTL management
- **Timeout Protection**: Configurable timeouts prevent long-running operations
- **Connection Pooling**: Optimized database connections with automatic recovery
- **Resource Monitoring**: Memory and CPU usage tracking with alerts

### 🛡️ Enterprise-Grade Error Handling
- **Centralized Error Management**: Dedicated error handling module (`error_handler.py`) with specialized handlers
- **Graceful Degradation**: System continues operating when subsystems fail (Redis offline, ChromaDB unavailable)
- **User-Friendly Messages**: Technical errors converted to helpful user messages with context
- **Specialized Handlers**: Different error handling strategies for chat, tools, cache, memory, and Redis operations
- **Request Tracking**: Unique request IDs for error correlation, debugging, and audit trails
- **Safe Execution**: Wrapper functions for critical operations with configurable fallback values
- **Context-Aware Logging**: Detailed error context including user ID, operation type, input data, and system state
- **Automatic Recovery**: Built-in retry logic for transient network errors and connection issues

## 🧠 Enhanced Learning & Document Processing

### 🎯 Adaptive Learning System (adaptive_learning.py)

#### Core Components
1. **ConversationAnalyzer**
   - Analyzes user interactions for learning patterns
   - Extracts topics, sentiment, and feedback classification
   - Calculates context relevance and engagement metrics

2. **AdaptiveLearningSystem**
   - Processes feedback loops for continuous improvement
   - Learns user preferences and interaction patterns
   - Automatically expands knowledge base from interactions
   - Provides personalized recommendations

#### Feedback Types
- **POSITIVE**: Good, helpful responses
- **NEGATIVE**: Incorrect or unhelpful responses  
- **NEUTRAL**: Standard interactions
- **CORRECTION**: User corrections to AI responses
- **CLARIFICATION**: Follow-up questions for better understanding

#### Learning Patterns
- **Query Patterns**: Common question types and preferences
- **Context Preferences**: User's preferred information depth and style
- **Tool Preferences**: Most effective tools for specific user needs

### 📄 Enhanced Document Processing (enhanced_document_processing.py)

#### Document Types
- **TEXT**: Plain text documents
- **CODE**: Source code with syntax awareness
- **ACADEMIC**: Research papers and academic content
- **TECHNICAL**: Technical documentation and manuals
- **MIXED**: General documents with varied content

#### Chunking Strategies
- **SEMANTIC**: Content-aware chunking based on meaning
- **FIXED_SIZE**: Traditional fixed-size chunks with overlap
- **PARAGRAPH**: Paragraph-boundary-aware chunking
- **SENTENCE**: Sentence-level chunking for precision
- **ADAPTIVE**: Dynamic chunking based on content analysis

#### Document Analysis Features
- **Language Detection**: Automatic language identification
- **Content Complexity**: Readability and technical complexity scoring
- **Topic Extraction**: Key theme and subject identification
- **Structure Analysis**: Document organization and hierarchy detection

#### Processing Pipeline
1. **Document Upload** → **Content Analysis** → **Strategy Selection**
2. **Intelligent Chunking** → **Quality Scoring** → **Vector Storage**
3. **Metadata Extraction** → **Index Creation** → **Semantic Search Ready**

## 🔌 API Endpoints

### 📋 Core Chat & Streaming Endpoints
- **`POST /chat`** - Main chat endpoint with tool integration and memory
- **`POST /v1/chat/completions`** - OpenAI-compatible chat completions with streaming
- **`POST /api/chat/completions`** - Alternative chat completions endpoint
- **`POST /v1/stop_stream`** - Stop active streaming sessions
- **`POST /api/stop_stream`** - Alternative stream stopping endpoint

### 🤖 Model Management
- **`GET /v1/models`** - List available models (OpenAI-compatible)
- **`GET /v1/models/verify/{model_name}`** - Verify and download specific models
- **`GET /capabilities`** - System capabilities and feature overview

### 🏥 Health & Monitoring
- **`GET /health`** - Basic system health check
- **`GET /health/simple`** - Simplified health status
- **`GET /health/detailed`** - Comprehensive health with all subsystems
- **`GET /health/redis`** - Redis-specific health status
- **`GET /health/chromadb`** - ChromaDB-specific health status
- **`GET /health/history/{service_name}`** - Service health history (24h)
- **`GET /health/storage`** - Storage system health and usage

### 📁 Document & RAG
- **File upload endpoints** (integrated from upload.py)
- **Document processing** with vector storage
- **Semantic search** across uploaded documents

## � System Monitoring & Health Management

### Comprehensive Watchdog System (watchdog.py)
The backend includes an enterprise-grade monitoring system that continuously tracks the health of all critical subsystems:

**Monitored Services:**
- **Redis**: Connection health, response time, memory usage, client connections, operational status
- **ChromaDB**: Collection access, document operations, query performance, storage health
- **Ollama**: API connectivity, model availability, response times, service status

**Watchdog Features:**
- **Delayed Startup**: Configurable startup delay (default: 10 seconds) to ensure all services are ready
- **Continuous Monitoring**: Configurable check intervals (default: 30 seconds) with async execution  
- **Health History**: 24-hour rolling history with timestamps and performance metrics
- **Intelligent Alerting**: Configurable alert thresholds with automatic escalation
- **Graceful Degradation**: System continues operating even when monitoring services fail
- **Performance Metrics**: Response time tracking, error rate analysis, and trend detection
- **Automatic Recovery**: Built-in reconnection logic for transient failures (broken pipe errors, network timeouts)
- **Real-time Status**: Live health dashboard with service-specific details
- **Smart Initialization**: Starts after FastAPI app initialization to prevent startup conflicts

### Health Check Endpoints

```bash
# Basic health check
GET /health

# Detailed health with all subsystems
GET /health/detailed

# Individual service health
GET /health/redis
GET /health/chromadb  

# Service health history
GET /health/history/{service_name}?hours=24

# Storage system health
GET /health/storage
```

### Watchdog Configuration

Environment variables for watchdog configuration:
```bash
WATCHDOG_CHECK_INTERVAL=30    # Seconds between checks
WATCHDOG_TIMEOUT=5            # Timeout for health checks
WATCHDOG_MAX_RETRIES=3        # Retry attempts before marking unhealthy
WATCHDOG_ALERT_THRESHOLD=3    # Consecutive failures before alert
```

### Testing the Watchdog

```bash
# Monitor the system logs
docker logs -f backend-llm-backend

# Check individual service health
curl http://localhost:8001/health/redis
curl http://localhost:8001/health/chromadb

# Test system health monitoring
curl http://localhost:8001/health/detailed
```

### Health Status Values

- **healthy**: Service is fully operational
- **degraded**: Service has issues but is partially functional
- **unhealthy**: Service is not responding or has critical errors
- **unknown**: Unable to determine service status

## 📂 Project Organization

This project follows a clean, organized structure that separates concerns and makes development efficient:

```
📁 Root Directory - Core Application
├── main.py                 # FastAPI backend entry point  
├── ai_tools.py            # AI tool implementations
├── database_manager.py    # Database operations
├── cache_manager.py       # Redis cache operations  
├── human_logging.py       # Enhanced logging system
├── README.md              # Project documentation
└── requirements.txt       # Dependencies

📁 demo-tests/ - Development & Testing
├── cache-tests/           # Cache system tests
├── debug-tools/          # Debugging utilities
├── integration-tests/    # Full system tests
├── model-tests/         # AI model tests
├── results/             # Test result files
└── *.py                 # Test and demo scripts

📁 readme/ - Documentation
├── ORGANIZATION_SUMMARY.md    # This organization guide
├── ai_tools_test_report.md   # AI tools test results
├── CURRENT_STATUS.md         # Project status
└── *.md                      # Technical reports & guides

📁 utils/ - Shared Utilities
└── Shared utility functions

📁 storage/ - Data Storage  
└── Runtime data storage (created automatically)
```

**Benefits:**
- 🎯 **Clear Separation**: Production code, tests, and docs are separated
- 🔍 **Easy Navigation**: Developers know exactly where to find files
- 🚀 **Clean Deployment**: Root contains only production-ready code
- 📚 **Centralized Docs**: All documentation in one organized location

## 📡 API Endpoints

## 📡 API Endpoints

### Chat Endpoints
- `POST /chat` - Main chat interface with tool support
- `POST /v1/chat/completions` - OpenAI-compatible chat completions
- `POST /api/chat/completions` - Alternative OpenWebUI endpoint

### Model Management
- `GET /v1/models` - List available models
- `GET /v1/models/verify/{model_name}` - Verify and download models
- `GET /test` - Backend status and default model info
- `POST /v1/stop_stream` - Stop streaming sessions
- `POST /api/stop_stream` - Alternative stop endpoint

### File Upload & RAG
- `POST /upload` - Upload documents for RAG processing
- `POST /search` - Search uploaded documents
- `GET /documents` - List uploaded documents
- `DELETE /documents/{doc_id}` - Delete documents

### Health & Monitoring
- `GET /health` - System health check
- `GET /health/detailed` - Detailed system monitoring
- Service-specific health monitoring

## 📚 Documentation

For comprehensive project documentation, visit the [readme/](readme/) directory which contains:

- **Project Status Reports** - Final achievements and completion summaries
- **Code Review Reports** - Detailed code analysis and quality metrics
- **Testing Documentation** - Comprehensive test reports and results
- **System Health Reports** - Service monitoring and health verification
- **Cleanup & Maintenance** - Code cleanup and optimization reports
- **Technical Analysis** - Duplicate code analysis and refactoring plans

See [readme/README.md](readme/README.md) for a complete documentation index.

---

*Project Status: **COMPLETED** ✅ - All tests passing, services healthy, code quality optimized*
