# Comprehensive Real-Life Simulation Test Report
Generated: 2025-06-25T18:33:10.449957

## Executive Summary
- **Duration:** 765.10 seconds
- **Phases Completed:** 7
- **Test Users Created:** 5
- **Overall Success Rate:** 83.3%

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
  - ✅ /health (1009.06ms)
  - ✅ / (19.73ms)
  - ✅ /upload/health (15.43ms)
  - ✅ /v1/models (115.75ms)

### Concurrent Operations

- **Total Requests:** 10
- **Successful:** 10
- **Duration:** 7.24s
- **Requests/Second:** 1.38

### Edge Cases


### Performance Load

- **Load Test Results:**
  - **Health check load**
    - Iterations: 50
    - Avg Response: 1014.58ms
    - P95 Response: 1030.82ms
    - Success Rate: 100.0%
  - **Search load**
    - Iterations: 25
    - Avg Response: 15.6ms
    - P95 Response: 27.39ms
    - Success Rate: 100.0%
  - **Chat load**
    - Iterations: 10
    - Avg Response: 3108.0ms
    - P95 Response: 27838.93ms
    - Success Rate: 90.0%

### Integration Scenarios


### Cleanup Recovery


## Errors Encountered

- **Phase:** load_test
  - **Error:** HTTPConnectionPool(host='localhost', port=9099): Read timed out. (read timeout=30)

