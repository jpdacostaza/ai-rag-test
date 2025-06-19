# Backend Project Structure

## Directory Organization

### `/docs/` - Documentation
- `CACHE_MEMORY_ENHANCEMENT_SUMMARY.md` - Comprehensive cache and memory system documentation
- `CACHE_TESTING_SUMMARY.md` - Cache testing methodology and results
- `INTEGRATION_TEST_RESULTS.md` - Latest integration test results
- `MODEL_MEMORY_ANALYSIS.md` - Memory architecture analysis
- `STARTUP_MEMORY_HEALTH_SUMMARY.md` - Startup health check documentation

### `/tests/` - Test Files
- `comprehensive_integration_test.py` - Full system integration test
- `comprehensive_cache_memory_test.py` - Comprehensive cache and memory tests
- `direct_cache_logging_test.py` - Cache logging validation
- `memory_architecture_test.py` - Memory system architecture tests
- `real_world_cache_simulation.py` - Real-world usage simulation
- `simple_cache_test.py` - Basic cache functionality tests
- `test_cache_manager.py` - Cache manager unit tests
- `test_adaptive_learning.py` - Adaptive learning system tests
- `demo_*.py` - Demonstration scripts

### `/test_results/` - Generated Test Data
- `*.json` files - Test results and request samples
- This directory is in `.gitignore` as results are generated

### Core Files
- `startup_memory_health.py` - Startup health check system
- `memory_cache_health.py` - Memory and cache health utilities
- `cache_manager.py` - Enhanced cache management with logging
- `main.py` - Main application with integrated health checks

## Recent Enhancements

### ✅ Cache Management
- Enhanced cache manager with detailed logging
- Cache hit/miss/set operations logged
- Response format validation
- TTL and versioning support

### ✅ Startup Health Checks
- Redis connectivity validation
- ChromaDB connectivity validation
- Intelligent status reporting (healthy/degraded/failed)
- Integration with main startup sequence

### ✅ Memory Architecture
- Three-tier memory system documented
- Redis for short-term cache and chat history
- ChromaDB for long-term semantic memory
- Graceful degradation when components unavailable

### ✅ Integration Testing
- Comprehensive test coverage
- Real-world scenario validation
- Performance testing
- End-to-end integration verification

## Running Tests

```bash
# Run comprehensive integration test
python tests/comprehensive_integration_test.py

# Run specific cache tests
python tests/simple_cache_test.py
python tests/comprehensive_cache_memory_test.py

# Run memory architecture tests
python tests/memory_architecture_test.py

# Run real-world simulation
python tests/real_world_cache_simulation.py
```

## Health Monitoring

```bash
# Check overall health
curl http://localhost:8001/health

# Check memory systems specifically
curl http://localhost:8001/health/memory

# Check individual components
curl http://localhost:8001/health/redis
curl http://localhost:8001/health/chromadb
```

## Documentation

See `/docs/` directory for comprehensive documentation on:
- Cache and memory system architecture
- Testing methodologies
- Integration results
- Startup health check implementation
