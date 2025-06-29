# Backend Directory Structure

This directory contains the OpenWebUI memory system backend with organized file structure.

## 📁 Directory Structure

### Core Application
- `main.py` - Main application entry point
- `enhanced_memory_api.py` - Enhanced memory API with Redis + ChromaDB
- `memory_filter_function.py` - OpenWebUI memory filter function
- `openwebui_api_bridge.py` - API bridge for pipeline integration
- `docker-compose.yml` - Docker composition for all services
- `requirements.txt` - Python dependencies

### Core Modules
- `config.py` - Configuration management
- `models.py` - Data models
- `database.py` - Database utilities
- `security.py` - Security utilities
- `validation.py` - Input validation

### Specialized Modules
- `adaptive_learning.py` - Adaptive learning system
- `cache_manager.py` - Caching functionality  
- `database_manager.py` - Database management
- `enhanced_document_processing.py` - Document processing
- `enhanced_integration.py` - System integration
- `enhanced_streaming.py` - Streaming capabilities
- `error_handler.py` - Error handling
- `feedback_router.py` - Feedback routing
- `human_logging.py` - Human interaction logging
- `model_manager.py` - Model management
- `rag.py` - RAG (Retrieval Augmented Generation)
- `startup.py` - Application startup
- `storage_manager.py` - Storage management
- `upload.py` - File upload handling
- `user_profiles.py` - User profile management
- `watchdog.py` - System monitoring
- `web_search_tool.py` - Web search integration

### Organized Directories

#### `docs/` - Documentation
- `status/` - Project status reports
- `guides/` - Setup and usage guides
- `backend_analysis_summary.md`
- `CONVERSATION_SYNC_SUMMARY_JUNE27.md`
- `MEMORY_SYSTEM_SUCCESS_REPORT.md`

#### `tests/` - Test Files
- `memory/` - Memory system tests
  - `test_memory_simple.ps1`
  - `test_memory_validation.ps1`
  - `test_memory_system_comprehensive.ps1`
  - `demo_memory_system.ps1`
  - `memory_system_status.ps1`
- `integration/` - Integration tests
  - `test_complete_integration.py`
  - `test_direct_pipeline.py`
  - `test_memory_pipeline_filter.py`

#### `scripts/` - Utility Scripts
- `import/` - Function import scripts
  - `import_memory_function.ps1`
  - `update_memory_filter.ps1`
- `memory/` - Memory system scripts
  - `start-memory-system.ps1`

#### `memory/` - Memory Pipeline Components
- Memory pipeline implementations
- Memory processing utilities

#### `handlers/` - Request Handlers
- Exception handlers
- Request processing

#### `pipelines/` - Pipeline Components
- Pipeline routes and implementations

#### `routes/` - API Routes
- REST API endpoint definitions

#### `services/` - Service Layer
- Business logic services

#### `setup/` - Setup and Configuration
- Installation and setup scripts

#### `storage/` - Storage Components
- Storage implementations and utilities

#### `utilities/` - Utility Functions
- Helper functions and utilities

#### `archive/` - Archived Files
- Old implementations
- Redundant files
- Test data files

## 🚀 Quick Start

1. **Start Services**: `docker-compose up -d`
2. **Import Memory Filter**: `scripts/import/import_memory_function.ps1`
3. **Test Memory System**: `tests/memory/test_memory_simple.ps1`
4. **Check Status**: `tests/memory/memory_system_status.ps1`

## 📚 Documentation

- **Setup Guide**: `docs/guides/MEMORY_PIPELINE_SETUP_GUIDE.md`
- **Usage Guide**: `docs/guides/MEMORY_PIPELINE_USAGE_GUIDE.md`
- **Test Plan**: `docs/guides/MEMORY_PIPELINE_TEST_PLAN.md`
- **Success Report**: `docs/MEMORY_SYSTEM_SUCCESS_REPORT.md`

## 🧪 Testing

- **Simple Test**: `tests/memory/test_memory_simple.ps1`
- **Full Validation**: `tests/memory/test_memory_validation.ps1`
- **Comprehensive Suite**: `tests/memory/test_memory_system_comprehensive.ps1`
- **Interactive Demo**: `tests/memory/demo_memory_system.ps1`

## 🔧 Management

- **Import Memory Filter**: `scripts/import/import_memory_function.ps1`
- **Update Filter**: `scripts/import/update_memory_filter.ps1`
- **Start Memory System**: `scripts/memory/start-memory-system.ps1`
- **System Status**: `tests/memory/memory_system_status.ps1`
