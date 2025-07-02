# Project Handover Document
**Date:** July 2, 2025  
**Project:** AI Backend API with Memory Integration  
**Status:** Development in Progress  

## Quick Start

### Current System State
- **Main Backend:** Running on port 3000 (FastAPI)
- **Memory API:** Running on port 8001 (Separate FastAPI service)
- **OpenWebUI:** Running on port 8080 (Frontend interface)
- **Ollama:** Running on port 11434 (LLM service)
- **Redis:** Running on port 6379 (Cache/session storage)
- **ChromaDB:** Running on port 8002 (Vector database)

### Docker Services Status
All services are containerized and running via docker-compose:
```bash
docker-compose up -d  # Start all services
docker-compose ps     # Check status
docker-compose logs   # View logs
```

## System Architecture

### Core Components
1. **Main Backend** (`main.py`) - Primary FastAPI application
2. **Memory API** (`memory/api/main.py`) - Dedicated memory management service
3. **Database Layer** - Redis + ChromaDB for hybrid storage
4. **LLM Integration** - Ollama for local model serving
5. **Web Interface** - OpenWebUI for user interaction

### Key Features Implemented
- ✅ OpenAI-compatible API endpoints (`/v1/chat/completions`)
- ✅ Streaming chat responses
- ✅ Memory storage and retrieval
- ✅ Multi-model support via Ollama
- ✅ Health monitoring endpoints
- ✅ File upload and document indexing
- ✅ Web search integration
- ✅ Comprehensive error handling

## Current Issues & Missing Components

### Critical Issues (Must Fix First)
1. **Model Manager Missing** - `model_manager.py` file doesn't exist but is imported
2. **Database Import Conflicts** - Conflicting function signatures between `database.py` and `database_manager.py`
3. **Missing Alert Manager** - Referenced functions don't exist

### Detailed Missing References
See `MISSING_REFERENCES_ANALYSIS.md` for complete list of:
- Missing functions
- Import conflicts
- Incomplete implementations
- Available vs expected endpoints

## File Structure Overview

```
backend/
├── main.py                     # ✅ Main FastAPI app with OpenAI endpoints
├── config.py                   # ✅ Configuration management
├── database.py                 # ⚠️  Basic database utilities (conflicts with database_manager)
├── database_manager.py         # ✅ Main database manager with full functionality
├── models.py                   # ✅ Pydantic models for API
├── startup.py                  # ✅ Application startup logic
├── security.py                 # ✅ Security middleware
├── error_handler.py            # ✅ Error handling utilities
├── human_logging.py            # ✅ Logging system
├── web_search_tool.py          # ✅ Web search functionality
├── user_profiles.py            # ✅ User profile management
├── storage_manager.py          # ✅ Storage utilities
├── watchdog.py                 # ✅ System monitoring
├── model_manager.py            # ❌ MISSING - Critical file
├── routes/                     # Route handlers
│   ├── health.py              # ✅ Health check endpoints
│   ├── chat.py                # ⚠️  Chat endpoints (import issues)
│   ├── models.py              # ✅ Model management
│   ├── upload.py              # ✅ File upload
│   ├── debug.py               # ✅ Debug endpoints
│   └── memory.py              # ✅ Memory endpoints
├── services/                   # Business logic
│   ├── llm_service.py         # ✅ LLM API calls
│   ├── streaming_service.py   # ✅ Streaming responses
│   └── tool_service.py        # ✅ Tool integration
├── utilities/                  # Utility functions
│   ├── alert_manager.py       # ⚠️  Missing key functions
│   ├── cache_manager.py       # ✅ Cache management
│   ├── memory_pool.py         # ✅ Memory optimization
│   └── ...
└── memory/                     # Memory API service
    ├── api/main.py            # ✅ Memory API server
    └── ...
```

## Development Workflow

### Starting Development
1. **Check System Status:**
   ```bash
   docker-compose ps
   curl http://localhost:3000/health
   curl http://localhost:8001/health
   ```

2. **Access Interfaces:**
   - Main API: http://localhost:3000
   - Memory API: http://localhost:8001
   - OpenWebUI: http://localhost:8080
   - API Docs: http://localhost:3000/docs

3. **View Logs:**
   ```bash
   docker-compose logs backend    # Main backend logs
   docker-compose logs memory_api # Memory service logs
   docker-compose logs ollama     # LLM service logs
   ```

### Key Endpoints for Testing

#### Health Checks
- `GET /health` - Main backend health
- `GET /health/detailed` - Detailed system status
- `GET /debug/routes` - List all available endpoints

#### Chat Functionality
- `POST /v1/chat/completions` - OpenAI-compatible chat
- `POST /chat` - Internal chat endpoint

#### Memory Operations
- `POST /memory/retrieve` - Get memories
- `POST /memory/learn` - Store memories

## Immediate Next Steps

### Priority 1: Fix Critical Issues
1. **Create `model_manager.py`:**
   ```python
   # Need to implement:
   # - router (FastAPI router object)
   # - initialize_model_cache() function
   ```

2. **Fix Database Imports:**
   ```python
   # In routes/chat.py, either:
   # - Implement missing async functions in database.py
   # - Update imports to use database_manager functions
   ```

3. **Implement Missing Alert Functions:**
   ```python
   # In utilities/alert_manager.py:
   # - alert_memory_pressure()
   # - alert_service_down()
   # - get_alert_manager()
   ```

### Priority 2: Testing & Validation
1. **Test All Endpoints** - Use the endpoint list in MISSING_REFERENCES_ANALYSIS.md
2. **Validate Memory Integration** - Ensure main backend ↔ memory API communication
3. **Test OpenWebUI Integration** - Verify chat functionality through web interface

### Priority 3: Documentation & Cleanup
1. **API Documentation** - Update OpenAPI specs
2. **Code Cleanup** - Remove stub implementations
3. **Performance Optimization** - Review and optimize database queries

## Configuration Notes

### Environment Variables
Key variables in docker-compose.yml:
- `REDIS_HOST=redis`
- `CHROMA_HOST=chroma`  
- `OLLAMA_BASE_URL=http://ollama:11434`
- `DEFAULT_MODEL=llama3.2:3b`

### Database Configuration
- **Redis:** Session storage, caching, short-term memory
- **ChromaDB:** Vector embeddings, long-term memory
- **Embedding Model:** `intfloat/e5-small-v2` (HuggingFace)

## Troubleshooting

### Common Issues
1. **Import Errors:** Check MISSING_REFERENCES_ANALYSIS.md for missing functions
2. **Database Connection:** Verify Redis and ChromaDB containers are running
3. **Model Loading:** Check Ollama container and model availability
4. **Memory API:** Ensure memory_api container is healthy

### Debug Commands
```bash
# Check container status
docker-compose ps

# View specific service logs
docker-compose logs -f backend
docker-compose logs -f memory_api
docker-compose logs -f ollama

# Restart services
docker-compose restart backend
docker-compose restart memory_api

# Full rebuild
docker-compose build --no-cache
docker-compose up -d
```

## Contact & Resources

### Key Files for Reference
- `MISSING_REFERENCES_ANALYSIS.md` - Complete missing components analysis
- `docker-compose.yml` - Service configuration
- `main.py` - Primary application entry point
- `memory/api/main.py` - Memory service entry point

### Testing URLs
- Health: http://localhost:3000/health
- API Docs: http://localhost:3000/docs
- Memory Health: http://localhost:8001/health
- OpenWebUI: http://localhost:8080

---
**Note:** This project is actively being developed. The main backend API is functional for basic chat operations, but several components need completion as outlined in the missing references analysis.
