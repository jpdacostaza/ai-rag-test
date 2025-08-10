# OpenWebUI Enhanced Memory System Backend - RAG Architecture

A comprehensive backend system for OpenWebUI with advanced RAG (Retrieval-Augmented Generation) dual-database memory capabilities using Redis and ChromaDB for persistent, user-isolated, and semantically searchable memory.

## 🚀 Quick Start

```bash
# 1. Start all services with RAG architecture
docker-compose up -d

# 2. Import memory filter to OpenWebUI
./scripts/import/import_memory_function.ps1

# 3. Test the RAG memory system
./tests/memory/test_memory_simple.ps1

# 4. Check system status
./tests/memory/memory_system_status.ps1
```

### 🍊 Orange Pi 5 Plus Optimized
This project includes **zero-configuration optimizations** for Orange Pi 5 Plus ARM64 platforms:
- ✅ **CPU Affinity**: Ollama dedicated to cores 1-7, system on core 0
- ✅ **Memory Management**: 6GB allocation with swap disabled for consistent performance  
- ✅ **ARM64 Tuning**: Optimized threading, memory limits, and request handling
- ✅ **Thermal Aware**: Extended timeouts and resource management for ARM SoCs

**📖 Full optimization guide**: [Orange Pi 5 Plus Setup](docs/ORANGE_PI_5_PLUS_OPTIMIZATION.md)

## 📋 System Overview - RAG Dual-Database Architecture

### Core Components
- **Memory API** (`memory/api/enhanced_memory_api.py`) - RAG dual-database backend (Redis + ChromaDB)
- **Memory Functions** (`memory/functions/memory_filter_function.py`) - OpenWebUI integration with RAG
- **Main API** (`main.py`) - OpenAI-compatible endpoints with RAG support
- **Docker Services** - Redis, ChromaDB, Memory API, OpenWebUI with RAG configuration

### Key Features - RAG Enhancement
- ✅ **RAG Dual-Database** - Redis (short-term) + ChromaDB (long-term) storage
- ✅ **Importance-Based Routing** - Automatic storage strategy selection
- ✅ **Explicit Memory Processing** - Handle "remember this" commands
- ✅ **Semantic Search** - ChromaDB embeddings with retrieval augmentation
- ✅ **User Isolation** - Private memory per user with cross-session persistence
- ✅ **Cross-Chat Memory** - Remember across sessions with context augmentation
- ✅ **Automatic Injection** - Filter-based context injection with RAG
- ✅ **Fallback Retrieval** - Always provides relevant context with semantic search
- ✅ **Network Resilience** - Multi-host Docker networking with fallback strategies
 - ✅ **Unified User Identity Resolution** - Centralized resolution logic (services/user_identity.py) ensuring consistent user mapping across endpoints and pipelines
 - ✅ **Correlation IDs** - Automatic per-request correlation IDs with header propagation (X-Correlation-ID) for traceability

## 📁 Directory Structure

```
backend/
├── 📄 Core Application Files
│   ├── main.py                     # Main application
│   ├── memory/
│   │   ├── api/
│   │   │   ├── enhanced_memory_api.py   # Memory API (Redis + ChromaDB)
│   │   │   └── main.py                  # Memory API main entry
│   │   └── functions/
│   │       ├── memory_filter_function.py # OpenWebUI memory function
│   │       └── enhanced_memory_function.py # Enhanced memory function
│   └── docker-compose.yml          # Service orchestration
│
├── 📚 docs/                        # Documentation
│   ├── guides/                     # Setup & usage guides
│   ├── status/                     # Project status reports
│   └── *.md                        # Analysis & summaries
│
├── 🧪 tests/                       # Testing Suite
│   ├── memory/                     # Memory system tests
│   └── integration/                # Integration tests
│
├── 📜 scripts/                     # Utility Scripts
│   ├── import/                     # Function import scripts
│   └── memory/                     # Memory system scripts
│
├── 📦 archive/                     # Archived files
├── 🔧 Core modules (*.py)          # Application modules
└── 🏗️ Infrastructure               # handlers/, pipelines/, routes/, etc.
```

## 🧪 Testing

### Memory System Tests
```bash
# Quick functionality check
./tests/memory/test_memory_simple.ps1

# Comprehensive validation  
./tests/memory/test_memory_validation.ps1

# Full test suite
./tests/memory/test_memory_system_comprehensive.ps1

# Interactive demo
./tests/memory/demo_memory_system.ps1

# System status
./tests/memory/memory_system_status.ps1
```

## 🔧 Management

### Memory Filter Management
```bash
# Import memory filter to OpenWebUI
./scripts/import/import_memory_function.ps1

# Update existing filter
./scripts/import/update_memory_filter.ps1

# Debug import issues
./scripts/import/import_function_debug.ps1
```

### System Management
```bash
# Start memory system
./scripts/memory/start-memory-system.ps1

# Check Docker services
docker-compose ps

# View logs
docker-compose logs memory_api
docker-compose logs openwebui
```

## 📚 Documentation

### Quick Reference
- **Setup Guide**: `docs/guides/MEMORY_PIPELINE_SETUP_GUIDE.md`
- **Usage Guide**: `docs/guides/MEMORY_PIPELINE_USAGE_GUIDE.md`
- **Test Plan**: `docs/guides/MEMORY_PIPELINE_TEST_PLAN.md`

### Status Reports
- **Success Report**: `docs/MEMORY_SYSTEM_SUCCESS_REPORT.md`
- **Project Status**: `docs/status/`

### Detailed Structure
See `README_STRUCTURE.md` for complete directory documentation.

## 🎯 Memory System Workflow

1. **User sends message** → OpenWebUI receives
2. **Memory Filter activated** → Retrieves relevant memories
3. **Context injection** → Memories added to system message
4. **LLM processes** → Generates response with memory context
5. **Response stored** → New interaction saved for future recall
6. **Cross-chat persistence** → Available in all future conversations

## 🔧 Configuration

### Environment Variables
```bash
REDIS_URL=redis://localhost:6379
CHROMADB_URL=http://localhost:8002
MEMORY_API_URL=http://localhost:8000
OPENWEBUI_URL=http://localhost:3000
# Optional logging / tracing
LOG_LEVEL=INFO
LOG_STYLE=human            # or json

# Correlation / request tracing
ENABLE_CORRELATION_ID=true  # (middleware auto-enabled; header X-Correlation-ID respected)
```

### Memory Filter Settings
- **Threshold**: 0.3 (semantic similarity)
- **Max memories**: 3 per retrieval
- **Fallback**: Empty query if no matches
- **Debug logging**: Enabled

## 🚨 Troubleshooting

### Common Issues
1. **Filter not working**: Check OpenWebUI functions list
2. **No memories**: Verify Redis/ChromaDB connectivity
3. **Import fails**: Use debug import script
4. **Performance issues**: Check service logs
5. **User not recognized**: Confirm client sends one of: body.user.{email|id|username}, X-User-Id header, AUTHENTICATED_USER_ID system message (pipeline), or Authorization Bearer token
6. **Missing correlation ID**: Ensure reverse proxy forwards X-Correlation-ID or allow backend to generate one

### Debug Commands
```bash
# Check services
docker-compose ps

# Test memory API directly
curl http://localhost:8000/health

# Verify filter installation
./tests/memory/memory_system_status.ps1

# Identity resolver unit tests
pytest -q tests/test_user_identity.py

# Correlation ID middleware tests
pytest -q tests/test_correlation_id.py
```

## 🎉 Success Indicators

When working correctly, you should see:
- ✅ AI references previous conversations
- ✅ Cross-chat memory persistence
- ✅ Context injection in responses
- ✅ User-specific memory isolation

## 📞 Support

For detailed technical information, see:
- Architecture: `docs/backend_analysis_summary.md`
- Implementation: `docs/MEMORY_SYSTEM_SUCCESS_REPORT.md`
- Integration: `docs/CONVERSATION_SYNC_SUMMARY_JUNE27.md`

---

**Status**: ✅ **OPERATIONAL** - Memory system fully functional and production-ready!
