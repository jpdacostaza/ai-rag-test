# Comprehensive Real-Life Simulation Test Report
Generated: 2025-06-25T13:40:23.818883

## Executive Summary
- **Duration:** 743.51 seconds
- **Phases Completed:** 7
- **Test Users Created:** 5
- **Overall Success Rate:** 76.7%

## Phase Results

### Module Imports

- **Success Rate:** 12/12 (100.0%)
- **Modules Tested:**
  - ✅ main - Main application
  - ✅ config - Configuration
  - ✅ database - Database interface
  - ✅ database_manager - Database manager
  - ✅ human_logging - Logging system
  - ✅ error_handler - Error handling
  - ✅ routes.health - Health routes
  - ✅ routes.chat - Chat routes
  - ✅ routes.models - Models routes
  - ✅ routes.upload - Upload routes
  - ✅ routes.pipeline - Pipeline routes
  - ✅ routes.debug - Debug routes

### Service Health

- **Healthy Services:** 4/4
  - ✅ /health (8.83ms)
  - ✅ / (12.46ms)
  - ✅ /upload/health (3.01ms)
  - ✅ /v1/models (66.23ms)

### Concurrent Operations

- **Total Requests:** 10
- **Successful:** 10
- **Duration:** 3.39s
- **Requests/Second:** 2.95

### Edge Cases


### Performance Load

- **Load Test Results:**
  - **Health check load**
    - Iterations: 50
    - Avg Response: 11.49ms
    - P95 Response: 29.55ms
    - Success Rate: 100.0%
  - **Search load**
    - Iterations: 25
    - Avg Response: 351.87ms
    - P95 Response: 376.48ms
    - Success Rate: 100.0%
  - **Chat load**
    - Iterations: 10
    - Avg Response: 2361.02ms
    - P95 Response: 21134.29ms
    - Success Rate: 90.0%

### Integration Scenarios


### Cleanup Recovery


## Errors Encountered

- **Phase:** load_test
  - **Error:** HTTPConnectionPool(host='localhost', port=9099): Read timed out. (read timeout=30)

