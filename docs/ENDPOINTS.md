# API Endpoints Documentation

This document provides a comprehensive list of all available API endpoints in the AI Backend system.

## Chat Endpoints

### `/chat/completions` (POST)

- **Purpose**: Process user chat messages and return AI responses.
- **Functionality**:
  - Detects and executes tools when appropriate.
  - Retrieves relevant user memory.
  - Uses the LLM for generating responses.
  - Stores important conversations in memory.
  - Caches responses for efficiency.

### `/v1/chat/completions` (POST)

- **Purpose**: OpenAI-compatible chat endpoint for OpenWebUI integration.
- **Functionality**:
  - Supports streaming responses.
  - Compatible with OpenAI client libraries.
  - Maintains chat history.
  - Processes multi-modal content.

## Model Endpoints

### `/v1/models` (GET)

- **Purpose**: OpenAI-compatible endpoint for listing available models.
- **Functionality**:
  - Dynamically fetches models from Ollama.
  - Caches results for efficiency.
  - Formats response to be OpenAI-compatible.

## Health Check Endpoints

### `/health` (GET)

- **Purpose**: Simple health check for the API.
- **Returns**: Basic health status of the API.

### `/health/system` (GET)

- **Purpose**: Comprehensive system health check.
- **Returns**: Detailed health status of all system components.

### `/health/database` (GET)

- **Purpose**: Check database connectivity.
- **Returns**: Status of database connections.

### `/health/models` (GET)

- **Purpose**: Check model availability.
- **Returns**: Status of available models.

### `/health/storage` (GET)

- **Purpose**: Check storage system health.
- **Returns**: Status of storage systems.

## Debug Endpoints

### `/debug/cache` (GET)

- **Purpose**: Get cache statistics.
- **Returns**: Information about the cache performance.

### `/debug/cache/clear` (POST)

- **Purpose**: Clear the system cache.
- **Action**: Removes all cached data.

### `/debug/memory` (GET)

- **Purpose**: Get memory usage statistics.
- **Returns**: Information about memory and CPU usage.

### `/debug/alerts` (GET)

- **Purpose**: Get current system alerts.
- **Returns**: Information about active and resolved alerts.

### `/debug/config` (GET)

- **Purpose**: Get current system configuration.
- **Returns**: Sanitized configuration information.

### `/debug/endpoints` (GET)

- **Purpose**: List all available API endpoints.
- **Returns**: Dynamic list of all registered endpoints.

### `/debug/routes` (GET)

- **Purpose**: Alternative endpoint to list all routes.
- **Returns**: List of all available routes and methods.

## Memory Endpoints

### `/api/memory/retrieve` (POST)

- **Purpose**: Retrieve relevant memories for a user query.
- **Used by**: OpenWebUI Functions for memory injection.

### `/api/memory/learn` (POST)

- **Purpose**: Learn from a document and store in user's memory.
- **Action**: Processes and stores documents in memory.

### `/api/learning/process_interaction` (POST)

- **Purpose**: Process an interaction for adaptive learning.
- **Used by**: OpenWebUI Functions to store learning data.

### `/api/memory/health` (GET)

- **Purpose**: Health check for memory endpoints.
- **Returns**: Status of memory-related endpoints.

## Upload Endpoints

### `/upload/document` (POST)

- **Purpose**: Upload and process a document for RAG integration.
- **Action**: Processes documents for later retrieval.

### `/upload/formats` (GET)

- **Purpose**: Get list of supported file formats.
- **Returns**: Information about supported file types.

### `/upload/search` (POST)

- **Purpose**: Search through uploaded documents.
- **Action**: Performs semantic search on documents.

### `/upload/document_json` (POST)

- **Purpose**: Upload document via JSON payload (for testing).
- **Action**: Processes document content provided in JSON.

### `/upload/search_json` (POST)

- **Purpose**: Search documents via JSON payload (for testing).
- **Action**: Searches documents using JSON input.

## Notes

- The `/debug/endpoints` endpoint dynamically generates a list of all registered endpoints by examining the FastAPI app routes.
- All endpoints are documented in the appropriate router files in the `routes` directory.
- OpenAI compatibility is maintained for key endpoints to ensure integration with tools like OpenWebUI.
