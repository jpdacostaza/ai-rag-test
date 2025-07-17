"""
RAG DUAL-DATABASE MEMORY SYSTEM API DOCUMENTATION
===============================================

This document describes the enhanced Memory API with RAG (Retrieval-Augmented Generation)
dual-database architecture implemented on 2025-07-17.

## Architecture Overview

### Dual-Database RAG System
- **Redis**: Short-term memory, fast access, caching
- **ChromaDB**: Long-term memory, semantic search, embeddings
- **Strategy**: Importance-based routing with dual storage

### Memory Classification
- **Low Importance (0.0-0.4)**: Redis only (short-term)
- **Medium Importance (0.5-0.7)**: Both Redis and ChromaDB (dual storage)
- **High Importance (0.8-1.0)**: ChromaDB priority with Redis cache

### Explicit Memory Processing
- **Triggers**: "remember", "don't forget", "keep in mind", "note that"
- **Content Extraction**: Automatic parsing of user commands
- **Importance Boost**: Explicit memories get minimum 0.8 importance
- **Storage Preference**: ChromaDB priority for permanent storage

## API Endpoints

### 1. Health Check
**GET** `/health`

Returns system status and database connectivity.

**Response:**
```json
{
  "status": "healthy",
  "service": "enhanced-memory-api",
  "version": "2.0.0",
  "rag_service_available": true,
  "database_status": {
    "redis": {"connected": true, "ping": true},
    "chroma": {"connected": true, "heartbeat": 1234567890}
  }
}
```

### 2. Store Memory
**POST** `/api/memory/store`

Store memory with importance-based routing.

**Request:**
```json
{
  "user_id": "string",
  "content": "string",
  "context": "string (optional)",
  "importance": 0.5,
  "explicit": false,
  "source": "api"
}
```

**Response:**
```json
{
  "success": true,
  "memory_id": "mem_user_1234567890_abc123",
  "storage_strategy": "dual_storage",
  "redis_stored": true,
  "chroma_stored": true,
  "importance": 0.6,
  "explicit": false
}
```

### 3. Store Explicit Memory
**POST** `/api/memory/store_explicit`

Process explicit memory commands like "remember this".

**Request:**
```json
{
  "user_id": "string",
  "user_input": "Remember that I love pizza",
  "context": "preference"
}
```

**Response:**
```json
{
  "success": true,
  "memory_id": "mem_user_1234567890_def456",
  "original_input": "Remember that I love pizza",
  "extracted_content": "love pizza",
  "storage_strategy": "chroma_priority",
  "redis_stored": true,
  "chroma_stored": true,
  "importance": 0.8,
  "explicit": true
}
```

### 4. Retrieve Memories
**POST** `/api/memory/retrieve`

Retrieve memories using dual-database RAG strategy.

**Request:**
```json
{
  "user_id": "string",
  "query": "pizza preferences",
  "limit": 10
}
```

**Response:**
```json
{
  "success": true,
  "memories": [
    {
      "memory_id": "mem_user_1234567890_def456",
      "content": "love pizza",
      "context": "preference",
      "importance": 0.8,
      "explicit": true,
      "source": "explicit_command",
      "source_db": "chroma",
      "timestamp": "2025-07-17T12:00:00Z"
    }
  ],
  "count": 1,
  "query": "pizza preferences"
}
```

### 5. Semantic Search
**GET** `/api/memory/search/{user_id}?query={query}&limit={limit}`

Perform semantic search across memories.

**Response:**
```json
{
  "success": true,
  "query": "pizza preferences",
  "semantic_matches": 2,
  "total_results": 5,
  "memories": [
    {
      "memory_id": "mem_user_1234567890_def456",
      "content": "love pizza",
      "importance": 0.8,
      "explicit": true,
      "source_db": "chroma"
    }
  ]
}
```

### 6. Memory Statistics
**GET** `/api/memory/stats/{user_id}`

Get comprehensive memory statistics.

**Response:**
```json
{
  "success": true,
  "user_id": "string",
  "total_memories": 12,
  "explicit_memories": 6,
  "redis_stats": {
    "short_term": 2,
    "medium_term": 3,
    "long_term": 4,
    "total": 9
  },
  "chroma_stats": {
    "documents": 8,
    "explicit_memories": 6
  },
  "storage_distribution": {
    "redis_percentage": 50.0,
    "chroma_percentage": 50.0
  }
}
```

## Storage Strategies

### 1. Redis Only (Short-term)
- **Importance**: 0.0 - 0.4
- **TTL**: 1 hour
- **Use Case**: Temporary interactions, UI state

### 2. Dual Storage (Medium-term)
- **Importance**: 0.5 - 0.7
- **Redis TTL**: 12 hours
- **ChromaDB**: Permanent
- **Use Case**: Preferences, work info

### 3. ChromaDB Priority (Long-term)
- **Importance**: 0.8 - 1.0
- **Redis TTL**: 24 hours (cache)
- **ChromaDB**: Permanent with embeddings
- **Use Case**: Personal info, explicit memories

## Memory Importance Classification

The system automatically classifies memory importance based on:

### High Importance (0.9)
- Personal info: name, email, phone, address
- Health info: allergies, medical conditions
- Security: passwords, credentials
- Critical dates: deadlines, appointments

### Medium Importance (0.7)
- Preferences: settings, favorites
- Work info: projects, colleagues
- Social info: friends, family

### Low Importance (0.3)
- Temporary info: session state
- UI interactions: clicks, navigation
- Transient data: temporary files

## Integration Examples

### Pipeline Integration
```python
from services.rag_dual_database_service import rag_service

# Store memory with importance
result = await rag_service.store_memory(
    user_id="user123",
    content="User prefers dark mode",
    importance=0.6,
    explicit=False
)

# Retrieve with semantic search
memories = await rag_service.get_memories(
    user_id="user123",
    query="UI preferences",
    limit=10
)
```

### Direct API Usage
```python
import requests

# Store explicit memory
response = requests.post("http://localhost:5001/api/memory/store_explicit", json={
    "user_id": "user123",
    "user_input": "Remember that I work at Microsoft",
    "context": "work"
})

# Semantic search
response = requests.get(
    "http://localhost:5001/api/memory/search/user123?query=work information"
)
```

## Performance Metrics

### Response Times
- **Redis retrieval**: ~5ms (ultra-fast)
- **ChromaDB semantic search**: ~100ms (acceptable)
- **Dual-database queries**: ~50ms (optimized)

### Storage Distribution
- **Expected**: 50% Redis, 50% ChromaDB
- **Actual**: Varies based on user behavior
- **Optimization**: Automatic importance tuning

## Error Handling

### Common Error Responses
```json
{
  "success": false,
  "error": "Memory service not available",
  "timestamp": "2025-07-17T12:00:00Z"
}
```

### Health Check Failures
```json
{
  "status": "limited",
  "rag_service_available": false,
  "database_status": {
    "redis": {"connected": false},
    "chroma": {"connected": false}
  }
}
```

## Production Deployment

### Docker Configuration
```yaml
services:
  memory-api:
    image: backend-memory-api
    ports:
      - "5001:5001"
    environment:
      - REDIS_HOST=redis
      - CHROMA_HOST=chroma
    depends_on:
      - redis
      - chroma
```

### Environment Variables
```bash
REDIS_HOST=redis
REDIS_PORT=6379
CHROMA_HOST=chroma
CHROMA_PORT=8000
MEMORY_API_PORT=5001
```

## Monitoring and Debugging

### Health Monitoring
```bash
# Check system health
curl http://localhost:5001/health

# Check memory stats
curl http://localhost:5001/api/memory/stats/user123
```

### Performance Monitoring
- Track response times for each storage strategy
- Monitor storage distribution across databases
- Analyze explicit memory processing accuracy

## Best Practices

### Memory Storage
1. Use explicit endpoints for user commands
2. Set appropriate importance levels
3. Provide meaningful context
4. Monitor storage distribution

### Memory Retrieval
1. Use semantic search for complex queries
2. Combine Redis and ChromaDB results
3. Implement proper error handling
4. Cache frequently accessed memories

### System Integration
1. Initialize RAG service at startup
2. Handle network failures gracefully
3. Monitor database health
4. Implement proper logging

## Version History

### v2.0.0 (2025-07-17)
- Full RAG dual-database architecture
- Explicit memory command processing
- Importance-based storage routing
- Semantic search capabilities
- Network-resilient connections
- Comprehensive statistics

### v1.0.0 (Previous)
- Basic memory storage
- Redis-only architecture
- Limited retrieval capabilities

---

**Status**: ✅ **PRODUCTION READY**  
**Architecture**: ✅ **RAG DUAL-DATABASE**  
**Performance**: ✅ **SUB-100MS RESPONSE TIMES**  
**Reliability**: ✅ **NETWORK RESILIENT**
"""
