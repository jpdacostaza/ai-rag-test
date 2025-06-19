# Advanced LLM Backend with Tool-Augmented Intelligence & Enhanced Human Logging

> **📚 Note**: This README contains all project documentation, including setup guides, troubleshooting, and technical details. All separate .md files have been merged into this unified documentation.

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

## 📁 Project Structure

```
opt/backend/
├── main.py                     # Core FastAPI application with tool integration
├── ai_tools.py                 # Tool implementations (web search, calc, Python execution)
├── database.py                 # Database management with connection pooling
├── database_manager.py         # Centralized database operations (Redis + ChromaDB)
├── error_handler.py            # Enterprise error handling & recovery systems
├── watchdog.py                 # System health monitoring & alerting
├── app.py                      # ASGI entrypoint for production deployment
├── rag.py                      # RAG (Retrieval-Augmented Generation) implementation
├── upload.py                   # File upload and document processing
├── adaptive_learning.py        # Self-learning system with feedback loops
├── enhanced_integration.py     # Enhanced endpoints for advanced features
├── enhanced_document_processing.py  # Advanced document chunking & analysis
├── model_manager.py            # LLM model management and optimization
├── feedback_router.py          # User feedback collection & processing
├── storage_manager.py          # File storage and management
├── human_logging.py            # Beautiful console logging with emojis
├── requirements.txt            # Python dependencies with version pinning
├── Dockerfile                  # Optimized container build configuration
├── docker-compose.yml          # Multi-service orchestration with health checks
├── startup.sh                  # Container initialization and health verification
├── fix-permissions.sh          # Linux permissions setup script
├── manage-models.sh            # Model management utilities
├── test-model.sh               # Model testing script
├── add-model.sh                # Add new models to Ollama
├── enhanced-add-model.sh       # Enhanced model addition script
├── debug-openwebui-models.sh   # OpenWebUI model debugging
├── setup-github.sh             # GitHub repository setup
├── refresh-models.py           # Python model refresh utility
├── persona.json               # AI personality configuration
└── README.md                   # This comprehensive documentation
```

## 🔧 Core Components

### **main.py** - FastAPI Application Core
- **Async FastAPI Framework**: High-performance async endpoints with streaming support
- **Tool Orchestration**: Intelligent tool detection, selection, and execution logic
- **API Compatibility**: Full OpenAI API compatibility with extensions for tool usage
- **Request Management**: Unique request tracking, session management, and concurrent handling
- **Integration Layer**: Seamless integration with database, error handling, and monitoring systems

### **ai_tools.py** - Advanced Tool Engine
- **Secure Python Execution**: RestrictedPython sandbox with timeout protection and result capture
- **Web Intelligence**: DuckDuckGo search with automatic knowledge storage and semantic indexing
- **Wikipedia Integration**: Smart article retrieval with summary extraction and caching
- **Mathematical Computing**: Safe expression evaluation with comprehensive operator support
- **Real-time Data**: Weather, time zones, currency exchange, and news with API key management
- **System Monitoring**: Resource usage, performance metrics, and system status reporting

### **database.py** - Centralized Data Management  
- **Redis Operations**: Connection pooling, automatic retry, broken pipe recovery, and health monitoring
- **ChromaDB Integration**: Vector storage, semantic search, document indexing, and collection management
- **Embedding Management**: Sentence transformer model loading, caching, and vector generation
- **Health Monitoring**: Database connectivity checks, performance metrics, and failover logic
- **Operation Wrappers**: Safe execution with retry logic for all database operations

### **database_manager.py** - Database Operations Coordination
- **Unified Interface**: Centralized database operations for Redis and ChromaDB
- **Transaction Management**: Coordinated operations across multiple database systems
- **Connection Management**: Pooled connections with health monitoring and recovery
- **Data Consistency**: Ensures data integrity across Redis cache and ChromaDB vectors

### **error_handler.py** - Enterprise Error Management
- **Specialized Handlers**: Chat, tool, cache, memory, and Redis-specific error handling strategies
- **Graceful Degradation**: System continues operating when subsystems fail with user notification
- **User Experience**: Technical errors converted to helpful, actionable user messages
- **Request Tracking**: Correlation IDs for debugging, audit trails, and performance analysis
- **Recovery Logic**: Automatic retry mechanisms for transient failures and connection issues
- **Context Preservation**: Detailed error context including user state, operation type, and system status

### **watchdog.py** - System Health & Monitoring
- **Multi-Service Monitoring**: Redis, ChromaDB, and Ollama health tracking with performance metrics
- **Health History**: 24-hour rolling history with timestamps, response times, and error tracking
- **Intelligent Alerting**: Configurable thresholds with escalation and automatic recovery attempts
- **Background Processing**: Async monitoring loops with configurable intervals and timeout handling
- **API Integration**: RESTful health endpoints for external monitoring and dashboard integration
- **Performance Analytics**: Response time trending, error rate analysis, and capacity planning data
- **ChromaDB for semantic long-term storage
- **Automatic knowledge indexing from web searches and interactions
- **Context-aware retrieval with semantic similarity matching
- **Persistent storage with Docker volume management
## 🚀 Quick Start & Deployment

## 🚀 Quick Start & Deployment

### 🎯 **Performance-Optimized Quick Start** (Recommended)

**Quick Start:**
```bash
# 1. Start all services with Docker Compose
docker-compose up --build -d

# 2. The system will automatically:
#    - Download llama3.2:3b model (~2GB) if not available
#    - Configure all services (Redis, ChromaDB, Ollama, Backend)
#    - Set up OpenWebUI at http://localhost:3000
#    - Start backend API at http://localhost:8001

# 3. Monitor startup progress
docker logs -f backend-llm-backend

# 4. Verify services are ready
curl http://localhost:8001/health
```

**For other systems:**
```bash
# 1. Start all services with Docker Compose
docker-compose up --build -d

# 2-5. Same as above
```

### 🚀 **What Happens on First Run**

The system automatically handles everything:

1. **Model Download**: Downloads llama3.2:3b (2GB) from Ollama registry
2. **Service Initialization**: Starts Redis, ChromaDB, and backend services  
3. **Health Verification**: Ensures all services are operational
4. **Ready to Use**: OpenWebUI available at http://localhost:3000

**Expected Startup Logs:**
```
[MODEL] 📝 Missing - Model llama3.2:3b not found in Ollama
[MODEL] 📝 Downloading - Downloading model llama3.2:3b to Ollama
[MODEL] ✅ Ready - Model llama3.2:3b downloaded successfully
[MODEL] ✅ Ready - Default model llama3.2:3b is available
```

### 🔧 **Alternative Deployment Methods**

```bash
# Option A: Development Mode (with live reload)
python -m uvicorn app:app --reload --host 0.0.0.0 --port 8001

# Option B: Direct Python startup
python app.py

# Option C: Docker development mode
docker-compose -f docker-compose.yml up --build
```

### 📊 **Service Overview**

| Service | Port | Description | Status Check |
|---------|------|-------------|--------------|
| **OpenWebUI** | 3000 | Web interface | http://localhost:3000 |
| **Backend API** | 8001 | FastAPI with tools/RAG | http://localhost:8001/health |
| **Ollama** | 11434 | llama3.2:3b model | Internal only |
| **ChromaDB** | 8002 | Vector database | Internal only |
| **Redis** | 6379 | Cache & sessions | Internal only |

### 🤖 **Model Configuration**

| Setting | Value | Description |
|---------|-------|-------------|
| **Default Model** | llama3.2:3b | 2GB local model |
| **Auto-Download** | ✅ Enabled | Downloads on first run |
| **Verification** | ✅ Enabled | Checks availability on startup |
| **Fallback** | OpenAI API | If Ollama unavailable |

### 🐳 **Docker Deployment with Persistent Volumes**

The performance-optimized Docker configuration includes:

- ✅ **Automatic model download** - llama3.2:3b downloaded on first startup
- ✅ **Persistent model storage** - No re-download between restarts
- ✅ **Optimized health checks** - Adaptive intervals based on stability
- ✅ **Complete isolation** - All services in isolated network
- ✅ **Resource limits** - Production-ready constraints
- ✅ **Automatic restarts** - Unless explicitly stopped

**Persistent Volumes:**
```yaml
volumes:  - ./storage/ollama:/home/ollama/.ollama               # Ollama models (llama3.2:3b)
  - ./storage/models:/home/models/.cache/torch         # Embedding models
  - ./storage/chroma:/chroma                          # Vector database
  - ./storage/redis:/data                             # Redis persistence
  - ./storage/backend:/opt/backend/data               # Backend data
```

## 🔧 Manual Installation & Configuration Guide

## 🚦 Current System Status

### ✅ **System Ready** (As of June 18, 2025)

Your backend is currently **fully operational** with the following configuration:

| Component | Status | Details |
|-----------|--------|---------|
| **LLM Model** | ✅ Ready | llama3.2:3b (2.02GB) downloaded and available |
| **Backend API** | ✅ Running | Port 8001, all endpoints operational |
| **OpenWebUI** | ✅ Running | Port 3000, configured to use backend |
| **Ollama** | ✅ Running | Port 11434, model verified |
| **Redis** | ✅ Healthy | Cache and sessions working |
| **ChromaDB** | ✅ Healthy | Vector database ready |
| **File Upload** | ✅ Ready | RAG pipeline operational |

### 🧪 **Verified Features**
- ✅ Model automatic download and verification
- ✅ OpenAI-compatible API endpoints
- ✅ Request flow through backend (no direct Ollama access)
- ✅ Health monitoring and logging
- ✅ File upload and document search
- ✅ All services communicating properly

### 🔗 **Access URLs**
- **OpenWebUI**: http://localhost:3000
- **Backend API**: http://localhost:8001
- **API Documentation**: http://localhost:8001/docs
- **Health Check**: http://localhost:8001/health

## 🔧 Manual Installation & Configuration Guide

### Prerequisites
- **Docker & Docker Compose**: Latest versions with container support
- **System Requirements**: 8GB+ RAM recommended, GPU optional for faster inference
- **Network**: Stable internet connection for model downloads and external API calls

### 1. Clone and Setup
```bash
cd /opt/backend
# All configuration files are already optimized for production use
```

### 2. Start All Services
```bash
# Start all services with health checks and dependency management
docker-compose up --build -d

# Monitor startup progress
docker-compose logs -f
```

### Startup Sequence
The services start in the following order for optimal reliability:
1. **Redis & ChromaDB**: Core data services initialize first
2. **Ollama**: LLM service starts with model loading
3. **Backend API**: FastAPI app starts with database connections
4. **OpenWebUI**: Web interface connects to backend
5. **Watchdog Monitoring**: Health monitoring begins after 10-second delay

This sequence ensures all dependencies are ready before monitoring begins.

### 3. Access Services
- **🎯 Backend API**: http://localhost:8001 (Main FastAPI backend with tools)
- **🖥️ OpenWebUI**: http://localhost:3000 (User-friendly chat interface)
- **🔍 ChromaDB**: http://localhost:8002 (Vector database management)
- **⚡ Redis**: localhost:6379 (Cache and session storage)
- **🤖 Ollama**: http://localhost:11434 (Local LLM inference engine)

### 4. Health Verification
```bash
# Check overall system health
curl http://localhost:8001/health

# Verify individual services
curl http://localhost:8001/health/redis
curl http://localhost:8001/health/chromadb
curl http://localhost:8001/health/ollama

# Monitor system in real-time
python test_watchdog.py continuous
```

### 5. Test Core Functionality
```bash
# Test Python code execution with security sandbox
curl -X POST http://localhost:8001/chat \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test", "message": "run python: import numpy as np; print(np.array([1,2,3]).sum())"}'

# Test intelligent web search with knowledge storage
curl -X POST http://localhost:8001/chat \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test", "message": "search latest developments in machine learning 2025"}'

# Test Wikipedia integration with semantic memory
curl -X POST http://localhost:8001/chat \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test", "message": "wikipedia quantum computing"}'

# Test mathematical calculations
curl -X POST http://localhost:8001/chat \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test", "message": "calculate sqrt(144) + 5^2"}'

# Test streaming responses
curl -X POST http://localhost:8001/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "Explain quantum computing"}], "stream": true}'
```

## 🌐 OpenWebUI Connection Settings

### Access OpenWebUI
- **URL**: http://localhost:3000
- **Container**: `backend-openwebui`

### Connection Configuration

#### 1. Ollama API (Local Models)
```
Settings → Connections → Ollama API
URL: http://ollama:11434 (Docker) or http://localhost:11434 (Local)
```

#### 2. OpenAI API (Cloud Models)
```
Settings → Connections → OpenAI API
URL: https://api.openai.com/v1
API Key: Your OpenAI API key
```

#### 3. Custom Backend (Tool-Augmented Responses)
```
Settings → Connections → OpenAI API (Custom)
URL: http://llm_backend:8001/v1 (Docker) or http://localhost:8001/v1 (Local)
API Key: f2b985dd-219f-45b1-a90e-170962cc7082
```

### Environment Variables
Add to your `.env` file:
```env
# LLM Configuration (Current)
DEFAULT_MODEL=llama3.2:3b                   # Current default model
USE_OLLAMA=true                              # Primary LLM provider
OLLAMA_BASE_URL=http://ollama:11434              # Ollama service URL

# Fallback Configuration
OPENAI_API_KEY=sk-your_api_key_here         # Optional for OpenAI fallback
OPENAI_API_BASE_URL=https://api.openai.com/v1

# Backend Configuration
BACKEND_API_KEY=f2b985dd-219f-45b1-a90e-170962cc7082
```

### Model Management
```bash
# Current model (automatically downloaded)
llama3.2:3b - Ready and operational

# Manual model management via API
curl http://localhost:8001/v1/models/verify/llama3.2:3b

# Pull additional Ollama models (if needed)
docker exec backend-ollama ollama pull mistral:7b
docker exec backend-ollama olloma pull codellama:7b

# List available models
docker exec backend-ollama ollama list
```

For detailed configuration, see the Environment Variables section below.

## ⚙️ Configuration & Optimization

### Environment Variables
```bash
# LLM Configuration (Updated)
DEFAULT_MODEL=llama3.2:3b                   # Current default model (2GB)
USE_OLLAMA=true                              # Primary LLM provider
OLLAMA_BASE_URL=http://ollama:11434              # Ollama service URL
LLM_TIMEOUT=180                             # Request timeout in seconds

# Database Configuration  
REDIS_HOST=redis                            # Redis container hostname
REDIS_PORT=6379                             # Redis port
CHROMA_HOST=chroma                          # ChromaDB hostname
CHROMA_PORT=8000                            # ChromaDB port
CHROMA_DB_DIR=./chroma_db                   # Persistent storage path
EMBEDDING_MODEL=Qwen/Qwen3-Embedding-0.6B  # Current embedding model

# Performance Tuning
CACHE_TTL=604800                            # Cache time-to-live (7 days)
SIMILARITY_THRESHOLD=0.92                   # Semantic similarity threshold
LLM_TIMEOUT=180                             # LLM request timeout (seconds)
MAX_REQUESTS_PER_MINUTE=60                  # Rate limiting
POOL_SIZE=20                                # Connection pool size

# Watchdog Configuration
WATCHDOG_STARTUP_DELAY=10                   # Startup delay before monitoring begins (seconds)
WATCHDOG_CHECK_INTERVAL=30                  # Health check interval (seconds)
WATCHDOG_TIMEOUT=5                          # Health check timeout
WATCHDOG_MAX_RETRIES=3                      # Retry attempts before failure
WATCHDOG_ALERT_THRESHOLD=3                  # Consecutive failures before alert

# Security & Authentication
API_KEY=your-secure-api-key-here            # Backend API security
JWT_SECRET=your-jwt-secret-for-tokens       # Session management
ALLOWED_ORIGINS=["http://localhost:3000"]   # CORS configuration
```

### Production Redis Configuration
Optimized for LRU caching with 1GB memory limit:
```
maxmemory 1gb
maxmemory-policy allkeys-lru
save 60 1000
```

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

---

*All documentation has been consolidated into this README for easy reference and maintenance.*
