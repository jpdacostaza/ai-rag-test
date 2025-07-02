# Docker Setup Documentation

This document provides an overview of the Docker configuration for the AI Backend API with Memory Integration.

## Docker Files Overview

The system uses the following Docker files:

1. **docker-compose.yml**
   - Main orchestration file that defines all services and their relationships
   - Configures the complete system including backend, memory API, database services, and web UI

2. **Dockerfile.backend**
   - Builds the main backend API service (runs on port 3000)
   - Provides OpenAI-compatible API endpoints
   - Integrates with memory, models, and other services

3. **Dockerfile.memory**
   - Builds the memory API service (runs on port 8001, internal port 8080)
   - Provides memory storage and retrieval functionality
   - Includes integrated startup process

4. **Dockerfile.function-installer**
   - One-time container for installing memory functions into OpenWebUI
   - Used during initial setup phase
   - Automatically exits after completing its task

5. **Dockerfile** (Deprecated)
   - Not used in the current setup
   - Redundant and can be removed if not used elsewhere

## Services Overview

The system consists of several containerized services:

### Core Services

1. **backend**
   - Main FastAPI application (port 3000)
   - Built using Dockerfile.backend
   - Provides OpenAI-compatible endpoints and core functionality

2. **memory_api**
   - Memory management service (port 8001)
   - Built using Dockerfile.memory
   - Handles memory storage, retrieval, and learning

### Database Services

1. **redis**
   - In-memory cache and session storage (port 6379)
   - Used for short-term memory and caching

2. **chroma**
   - Vector database for embeddings (port 8000)
   - Used for semantic search and memory storage

### Model Services

1. **ollama**
   - Local model serving (port 11434)
   - Provides LLM inference capabilities

### Interface Services

1. **openwebui**
   - Web interface (port 8080)
   - Provides user-friendly access to the system

### Utility Services

1. **function_installer**
   - One-time service for installing memory functions
   - Only runs during setup phase

2. **watchtower** (Optional)
   - Automatic container updates
   - Disabled by default (in optional profile)

## Deployment Instructions

### Basic Deployment

To deploy the core services:

```bash
docker-compose up -d
```

### Including Function Installer

To include the function installer during deployment:

```bash
docker-compose --profile installer up -d
```

### Including Optional Services

To include all optional services:

```bash
docker-compose --profile optional --profile installer up -d
```

## Volume Mounts

The system uses several volume mounts to persist data:

1. **./storage/redis** - Redis data
2. **./storage/chroma** - ChromaDB data
3. **./storage/ollama** - Ollama models
4. **./storage/backend** - Backend data
5. **./storage/models** - Model cache
6. **./storage/memory** - Memory API data
7. **./storage/openwebui** - OpenWebUI data
8. **./memory/functions** - Memory functions

## Networking

All services communicate over the `backend-net` bridge network, which isolates the system from other Docker containers on the host.

## Maintenance Recommendations

1. **Redundant Files**:
   - The generic `Dockerfile` can be safely removed as it's not used in the current setup.

2. **Security**:
   - Consider reviewing volume mount permissions
   - Evaluate the need for exposed ports and limit as necessary

3. **Performance**:
   - Monitor Redis and ChromaDB resource usage
   - Consider adjusting worker counts based on host capabilities
