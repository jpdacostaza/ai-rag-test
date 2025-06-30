# Cache Issue Mitigation Guide

## Overview
This document outlines the strategies implemented to prevent cache-related issues, particularly the JSON response format problem we encountered.

## Root Cause Analysis
The cache issue occurred because:
1. **Cached Responses**: Old responses with JSON formatting were cached and being returned instead of generating new responses
2. **System Prompt Changes**: When we updated the system prompt to enforce plain text responses, cached entries weren't invalidated
3. **Format Inconsistency**: No validation was in place to ensure cached responses matched the expected format

## Mitigation Strategies Implemented

### 1. Cache Versioning System
- **File**: `cache_manager.py`
- **Feature**: Automatic cache invalidation when version changes
- **How it works**: 
  - Cache version is stored in Redis (`cache:version`)
  - On startup, if version doesn't match, all cache is invalidated
  - Version should be incremented when making significant changes

### 2. System Prompt Change Detection
- **File**: `cache_manager.py` → `check_system_prompt_change()`
- **Feature**: Automatic cache invalidation when system prompt changes
- **How it works**:
  - System prompt hash is stored in Redis (`cache:system_prompt_hash`)
  - Before each LLM call, current prompt is hashed and compared
  - If different, chat cache is invalidated automatically

### 3. Response Format Validation
- **File**: `cache_manager.py` → `validate_response_format()`
- **Feature**: Prevents caching and retrieval of incorrectly formatted responses
- **How it works**:
  - Validates responses are plain text, not JSON
  - Rejects caching of JSON-formatted responses
  - Invalidates cached entries that contain JSON when retrieved

### 4. Enhanced Cache Management
- **File**: `cache_manager.py` → `CacheManager` class
- **Features**:
  - Metadata storage with cached values (timestamp, version, format)
  - Automatic migration from old cache format
  - Granular invalidation (chat-only vs. all cache)

### 5. Administrative Endpoints
- **File**: `main.py` → `/admin/cache/*` endpoints
- **Features**:
  - `GET /admin/cache/status` - View cache statistics
  - `POST /admin/cache/invalidate?cache_type=chat` - Invalidate specific cache types
  - `POST /admin/cache/check-prompt` - Force system prompt check

### 6. Startup Initialization
- **File**: `init_cache.py` and `main.py` startup
- **Feature**: Automatic cache management initialization
- **How it works**:
  - Runs cache version check on startup
  - Initializes system prompt monitoring
  - Provides startup script for deployments

## Usage Guidelines

### For Development
1. **Increment cache version** in `cache_manager.py` when:
   - Changing system prompts significantly
   - Modifying response format requirements
   - Making breaking changes to cache structure

2. **Test cache behavior** after changes:
   ```bash
   curl http://localhost:8001/admin/cache/status
   ```

3. **Force cache invalidation** if needed:
   ```bash
   curl -X POST http://localhost:8001/admin/cache/invalidate?cache_type=chat
   ```

### For Deployment
1. **Run cache initialization** script:
   ```bash
   python init_cache.py
   ```

2. **Monitor cache health** in health endpoint:
   ```bash
   curl http://localhost:8001/health
   ```

### For Troubleshooting
1. **Check cache statistics**:
   ```bash
   curl http://localhost:8001/admin/cache/status
   ```

2. **Clear problematic cache**:
   ```bash
   # Clear chat cache only
   curl -X POST http://localhost:8001/admin/cache/invalidate?cache_type=chat
   
   # Clear all cache (nuclear option)
   curl -X POST http://localhost:8001/admin/cache/invalidate?cache_type=all
   ```

3. **Force system prompt check**:
   ```bash
   curl -X POST http://localhost:8001/admin/cache/check-prompt
   ```

## Prevention Checklist

### ✅ Before System Prompt Changes
- [ ] Increment `CACHE_VERSION` in `cache_manager.py`
- [ ] Test with fresh user ID to verify new behavior
- [ ] Check that cached responses are invalidated

### ✅ Before Deployment
- [ ] Run `python init_cache.py` to initialize cache management
- [ ] Verify health endpoint shows cache information
- [ ] Test admin endpoints are working

### ✅ After Deployment
- [ ] Monitor logs for cache invalidation messages
- [ ] Verify response format is consistent
- [ ] Check cache statistics for anomalies

## Configuration

### Environment Variables
```bash
# Cache settings (optional)
CACHE_TTL=600  # Default cache TTL in seconds
CACHE_MAX_SIZE=10000  # Maximum cache entries
```

### Cache Version Management
Update this in `cache_manager.py` when making breaking changes:
```python
CACHE_VERSION = "v2.1.0"  # Increment when needed
```

## Monitoring

### Health Endpoint
The `/health` endpoint now includes cache information:
```json
{
  "status": "ok",
  "cache": {
    "version": "v2.0.0",
    "cache_counts": {
      "chat": 15,
      "history": 5,
      "other": 2
    },
    "total_keys": 22
  }
}
```

### Log Messages
Watch for these log messages:
- `[CACHE] Cache version mismatch. Upgrading...`
- `[CACHE] System prompt changed, invalidating chat cache`
- `[CACHE] Detected JSON response format - invalidating`
- `[CACHE] Skipping cache for key - invalid format`

## Recovery Procedures

### If Cache Issues Persist
1. **Manual cache clear**:
   ```bash
   docker-compose exec redis redis-cli FLUSHDB
   ```

2. **Restart with fresh cache**:
   ```bash
   docker-compose restart llm_backend
   ```

3. **Check logs** for cache-related messages:
   ```bash
   docker-compose logs llm_backend | grep CACHE
   ```

This comprehensive cache management system should prevent the JSON response format issue from recurring while providing tools for monitoring and troubleshooting.
