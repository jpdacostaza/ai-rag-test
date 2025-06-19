# FastAPI AI Backend

A comprehensive FastAPI-based AI backend service with RAG capabilities, document processing, and chat functionality.

## Quick Start

```bash
# Start the services
docker-compose up -d

# Check service health
curl http://localhost:8001/health

# Access OpenWebUI
http://localhost:3000
```

## Documentation

All documentation files are located in the `/readme` folder:

- [Project Structure](readme/PROJECT_STRUCTURE.md)
- [Refactoring Report](readme/REFACTORING_COMPLETION_REPORT.md)
- [Validation Report](readme/FINAL_COMPREHENSIVE_VALIDATION_REPORT.md)
- [Testing Summary](readme/FINAL_TESTING_SUMMARY.md)

## Services

- **Backend API**: `http://localhost:8001`
- **OpenWebUI**: `http://localhost:3000`
- **Redis**: `localhost:6379`
- **ChromaDB**: `http://localhost:8000`

## Features

- 🤖 Chat completions with multiple LLM models
- 📄 Document upload and RAG processing
- 💾 Redis caching and session management
- 🔍 Semantic search with ChromaDB
- 🛡️ API key authentication
- 📊 Health monitoring and metrics
- 🔧 AI tools integration (weather, time, units)

## Development

The codebase is organized into modular components:

- `core/` - Core functionality (database, schemas, error handling)
- `managers/` - Business logic managers
- `routers/` - API endpoints
- `utils/` - Utility functions
- `config/` - Configuration files
- `scripts/` - Deployment scripts

## Status

✅ **Refactoring Complete** - Modular architecture implemented  
🔧 **In Progress** - Functionality fixes for authentication and chat endpoints
