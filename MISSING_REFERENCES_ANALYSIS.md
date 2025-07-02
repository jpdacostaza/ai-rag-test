# Missing References and Endpoints Analysis

## Overview
This document identifies all missing functions, files, and endpoints referenced in the codebase.

## Missing Functions and References

### 1. Database Module Issues

#### Missing Functions in `database.py`:
- `store_chat_history_async` - Referenced in `routes/chat.py` line 17
- `retrieve_user_memory` - Referenced in `routes/chat.py` line 18 (conflicts with database_manager version)
- `index_user_document` - Referenced in `routes/chat.py` line 19 (conflicts with database_manager version)

**Issue**: The `database.py` module has different function signatures than what's expected in the imports.

### 2. Missing Route Files

#### Memory Route:
- File: `routes/memory.py` - Referenced but missing complete implementation
- Imports: `from database_manager import retrieve_user_memory`

### 3. Missing Utility Functions

#### Alert Manager:
- `alert_memory_pressure` - Referenced in `database_manager.py`
- `alert_service_down` - Referenced in `database_manager.py`
- `get_alert_manager` - Referenced in multiple files
- `alert_cache_performance` - Referenced in `utilities/cache_manager.py`

#### Storage Manager:
- Complete `StorageManager` class - Currently has stub implementation in `routes/health.py`

#### Watchdog Service:
- `start_watchdog_service` - Referenced in `startup.py`
- Complete `MockWatchdog` class - Currently has stub implementation

### 4. Model Manager Issues

#### Missing Functions:
- `initialize_model_cache` - Referenced in `main.py`
- `router` (as model_manager_router) - Referenced in `main.py`

### 5. User Profiles Issues
- `user_profile_manager` - Referenced in `routes/chat.py`

### 6. Web Search Tool Issues
- Functions in `web_search_tool.py` are referenced but need validation

## Endpoint Analysis

### Available Endpoints (from routes):

#### Health Router (`routes/health.py`):
- `GET /` - Root endpoint
- `GET /health` - Basic health check  
- `GET /health/detailed` - Detailed health check
- `GET /health/services` - Service status

#### Chat Router (`routes/chat.py`):
- `POST /chat` - Main chat endpoint

#### Models Router (`routes/models.py`):
- `GET /models` - List available models
- `POST /models/refresh` - Refresh model cache

#### Debug Router (`routes/debug.py`):
- `GET /debug/cache` - Cache debugging
- `GET /debug/database` - Database debugging

#### Upload Router (`routes/upload.py`):
- File upload endpoints (needs verification)

#### Model Manager Router:
- Missing - referenced as `model_manager_router` in main.py

#### Memory Router:
- Incomplete - `routes/memory.py` needs implementation

### Main Application Endpoints (`main.py`):
- `POST /v1/chat/completions` - OpenAI-compatible chat completions
- `GET /debug/routes` - Debug endpoint to list routes

### Memory API Endpoints (`memory/api/main.py`):
- Multiple memory-related endpoints (running on separate container)

## Complete Endpoint List

### Health Router Endpoints:
- `GET /` - Root endpoint (basic status)
- `GET /health` - Basic health check with database status
- `GET /health/simple` - Simple health check
- `GET /health/detailed` - Detailed health check with metrics
- `GET /health/redis` - Redis-specific health check
- `GET /health/chromadb` - ChromaDB-specific health check
- `GET /health/history/{service_name}` - Service history
- `GET /health/storage` - Storage health check
- `GET /alerts/stats` - Alert statistics
- `GET /startup-status` - Application startup status

### Chat Router Endpoints:
- `POST /chat` - Main chat endpoint (ChatRequest -> ChatResponse)

### Models Router Endpoints:
- `GET /v1/models` - List available models (OpenAI-compatible)

### Upload Router Endpoints:
- `POST /document` - Upload and index document
- `GET /formats` - Get supported file formats
- `POST /search` - Search uploaded documents
- `POST /document_json` - Upload document via JSON
- `POST /search_json` - Search documents via JSON

### Memory Router Endpoints:
- `POST /memory/retrieve` - Retrieve user memories
- `POST /memory/learn` - Store new memories
- `POST /learning/process_interaction` - Process learning interactions
- `GET /memory/health` - Memory system health

### Debug Router Endpoints:
- `GET /cache` - Cache debugging information
- `POST /cache/clear` - Clear cache
- `GET /memory` - Memory debugging information
- `GET /alerts` - Alert debugging information
- `GET /config` - Configuration debugging
- `GET /endpoints` - List all endpoints

### Main Application Endpoints:
- `POST /v1/chat/completions` - OpenAI-compatible chat completions (with streaming)
- `GET /debug/routes` - Debug endpoint to list all routes

### Missing Router Endpoints:
- Model Manager Router - Referenced but not implemented
  - Expected endpoints: model management, model pulling, model status

## Missing Critical Functions

### 1. Database Import Conflicts:

**In `routes/chat.py`:**
```python
from database import (
    store_chat_history_async,    # ❌ Missing async version
    retrieve_user_memory,        # ❌ Different signature
    index_user_document,         # ❌ Different signature  
)
```

**Available in `database.py`:**
- `store_chat_history` (sync version)
- `retrieve_user_memory` (different parameters)
- `index_user_document` (different parameters)

### 2. Model Manager Issues:

**In `main.py`:**
```python
from model_manager import router as model_manager_router, initialize_model_cache
```

**Missing:**
- `router` object/variable in model_manager.py
- `initialize_model_cache` function

### 3. User Profile Manager:

**In `routes/chat.py`:**
```python
from user_profiles import user_profile_manager
```

**Status:** Referenced but needs verification of implementation

### 4. Utility Functions:

**Alert Manager Functions:**
- `alert_memory_pressure` - Referenced in database_manager.py
- `alert_service_down` - Referenced in database_manager.py  
- `get_alert_manager` - Referenced in multiple files
- `alert_cache_performance` - Referenced in cache_manager.py

**Storage Manager:**
- Complete implementation missing (currently stubs)

**Watchdog Service:**
- `start_watchdog_service` - Referenced in startup.py
- Proper implementation needed

### 5. Memory API Integration:

**Container:** memory_api (separate service on port 8001)
**Main File:** `memory/api/main.py`
**Status:** Needs health endpoint and proper integration

## Recommendations

### High Priority Fixes:
1. Fix database function imports and signatures
2. Implement missing alert manager functions
3. Complete model manager router implementation
4. Fix user profile manager integration

### Medium Priority:
1. Complete storage manager implementation
2. Implement watchdog service
3. Complete memory router implementation

### Low Priority:
1. Add comprehensive error handling
2. Implement missing debug endpoints
3. Add monitoring and metrics endpoints

## Container Communication Issues

### Memory API:
- Runs on separate container (port 8001)
- May have connectivity issues with main backend
- Health endpoint missing or misconfigured

### Database Containers:
- Redis: Should be accessible on redis:6379
- ChromaDB: Should be accessible on chroma:8002
- Ollama: Should be accessible on ollama:11434

## Missing Environment Variables

Based on config.py, these environment variables should be verified:
- REDIS_HOST, REDIS_PORT
- CHROMA_HOST, CHROMA_PORT  
- OLLAMA_BASE_URL
- DEFAULT_MODEL
- EMBEDDING_MODEL
- Various timeout configurations

## Next Steps

1. Fix critical database import issues
2. Implement missing utility functions with proper stubs
3. Complete model manager integration
4. Test endpoint connectivity
5. Verify container communication
6. Add comprehensive error handling
