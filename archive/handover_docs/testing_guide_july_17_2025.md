# TESTING GUIDE - JULY 17, 2025

## 🧪 **TESTING INFRASTRUCTURE OVERVIEW**

### **Test Organization**
All tests are now organized in the `tests/` directory with a unified runner system:

```
tests/
├── run_focused_memory_tests.py      # Priority tests (7 tests)
├── run_memory_tests.py              # Standard memory tests  
├── run_memory_tests_comprehensive.py # Full test suite
├── run_comprehensive_tests.py       # System-wide tests
├── run_all_tests.py                 # All test runners
├── test_memory_*.py                 # Memory-specific tests
├── test_pipeline_*.py               # Pipeline tests
├── test_*.py                        # Various component tests
└── config/                          # Test configurations
```

### **Main Test Runner**
**Location:** `run_tests.py` (in project root)

**Usage:**
```bash
# Run all available tests
python run_tests.py

# Run specific test suites
python run_tests.py --focused          # Priority memory tests
python run_tests.py --memory           # Memory tests
python run_tests.py --comprehensive    # Full comprehensive tests
python run_tests.py --help             # Show help
```

---

## 🎯 **MEMORY SYSTEM TESTING**

### **Focused Memory Tests (Priority)**
**Runner:** `tests/run_focused_memory_tests.py`  
**Purpose:** Quick validation of core memory functionality  
**Duration:** ~2 minutes  
**Success Rate:** 100% (7/7 tests)

**Test Coverage:**
```
✅ test_memory_function.py (0.20s)
   - Basic memory function validation
   - Import and initialization checks
   
✅ test_memory_service_endpoints.py (44.23s)
   - Memory API endpoint validation
   - Store/retrieve functionality
   - Health check endpoints
   
✅ test_memory_service_validation.py (11.97s)
   - Input validation testing
   - Error handling verification
   - Data integrity checks
   
✅ test_memory_localhost.py (7.80s)
   - Local memory API testing
   - Direct database connections
   - Service availability checks
   
✅ test_memory_final.py (2.12s)
   - Final integration testing
   - End-to-end workflows
   - System state validation
   
✅ test_enhanced_memory.py (39.17s)
   - RAG system functionality
   - Dual-database operations
   - Importance classification
   
✅ test_memory_service_basic.py (0.33s)
   - Basic service functionality
   - Configuration validation
   - Service startup checks
```

### **Comprehensive Memory Tests**
**Runner:** `tests/run_memory_tests_comprehensive.py`  
**Purpose:** Full memory system validation  
**Duration:** ~10 minutes  
**Coverage:** All memory-related functionality

**Test Categories:**
1. **Basic Functionality**: Core memory operations
2. **RAG System**: Dual-database operations
3. **Pipeline Integration**: Memory pipeline testing
4. **Performance**: Response time and throughput
5. **Error Handling**: Failure scenarios
6. **Security**: Authentication and validation

---

## 🔧 **RUNNING TESTS**

### **Prerequisites**
```bash
# Ensure Docker containers are running
docker-compose up -d

# Verify system health
curl http://localhost:5001/health
curl http://localhost:3000/health

# Check container status
docker ps
```

### **Quick Test Execution**
```bash
# From project root directory
cd e:\Projects\opt\backend

# Run priority tests (recommended first)
python run_tests.py --focused

# If priority tests pass, run full suite
python run_tests.py
```

### **Individual Test Execution**
```bash
# Run specific test file
cd tests
python test_memory_service_endpoints.py

# Run specific test runner
python run_focused_memory_tests.py
```

### **Test Output Examples**
```
FOCUSED MEMORY TEST RUNNER
============================================================
Running 3 priority tests...
============================================================
Running: test_memory_function.py
============================================================
✅ PASSED - test_memory_function.py (0.20s)
============================================================
Running: test_memory_service_endpoints.py
============================================================
✅ PASSED - test_memory_service_endpoints.py (44.23s)
============================================================

FOCUSED MEMORY TEST SUMMARY
============================================================
Total Tests: 7
Passed: 7
Failed: 0
Success Rate: 100.0%
Total Duration: 105.82s
```

---

## 🔍 **DEBUGGING TEST FAILURES**

### **Common Issues and Solutions**

#### **1. Container Not Running**
**Error:** `Connection refused` or `Service unavailable`
**Solution:**
```bash
# Check container status
docker ps

# Restart services
docker-compose down
docker-compose up -d

# Wait for services to be ready
sleep 30
```

#### **2. Database Connection Issues**
**Error:** `Database not accessible` or `Connection timeout`
**Solution:**
```bash
# Check database health
docker logs backend-redis
docker logs backend-chroma

# Test direct connections
curl http://localhost:6379  # Redis
curl http://localhost:8000/api/v1/heartbeat  # ChromaDB
```

#### **3. Unicode Encoding Issues (Windows)**
**Error:** `UnicodeEncodeError` or `cp1252 codec can't encode`
**Solution:**
```bash
# Set environment variables
set PYTHONIOENCODING=utf-8
set PYTHONLEGACYWINDOWSSTDIO=1

# Or use the focused test runner (has built-in fixes)
python run_tests.py --focused
```

#### **4. Memory API Errors**
**Error:** `404 Not Found` or `500 Internal Server Error`
**Solution:**
```bash
# Check memory API logs
docker logs backend-memory-api

# Test memory API directly
curl -X POST http://localhost:5001/api/memory/store \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test","content":"test"}'
```

### **Test Debugging Commands**
```bash
# Check test environment
python -c "import requests; print(requests.get('http://localhost:5001/health').text)"

# Run single test with verbose output
python -v tests/test_memory_function.py

# Check Python path and imports
python -c "import sys; print(sys.path)"
```

---

## 📊 **TEST REPORTING**

### **Test Reports Location**
```
logs/
├── focused_memory_test_report.md     # Focused test results
├── memory_test_report.json          # Comprehensive test results
├── memory_test_summary.md           # Test summary
└── comprehensive_test_*.log         # Detailed logs
```

### **Report Contents**
- **Test execution times**
- **Pass/fail status for each test**
- **Error messages and stack traces**
- **System health information**
- **Performance metrics**

### **Report Example**
```markdown
# Focused Memory Test Report

**Run Time**: 2025-07-17 21:06:42
**Total Tests**: 7
**Passed**: 7
**Failed**: 0
**Success Rate**: 100.0%
**Total Duration**: 105.82s

## Test Results
- ✅ PASSED **test_memory_function.py** (0.20s)
- ✅ PASSED **test_memory_service_endpoints.py** (44.23s)
- ✅ PASSED **test_memory_service_validation.py** (11.97s)
```

---

## 🔄 **CONTINUOUS TESTING**

### **Pre-Commit Testing**
```bash
# Before committing changes
python run_tests.py --focused

# If focused tests pass, run full suite
python run_tests.py
```

### **Post-Deployment Testing**
```bash
# After container restart
docker-compose up -d
sleep 30  # Wait for services
python run_tests.py --focused
```

### **Performance Testing**
```bash
# Run performance-focused tests
python tests/test_network_resilience.py
python tests/test_memory_service_proper.py
```

---

## 🚀 **PIPELINE TESTING**

### **Pipeline Test Categories**
1. **Memory Pipeline Tests**
   - `test_pipeline_memory_async.py`
   - `test_pipeline_integration.py`
   - `test_pipeline_final.py`

2. **Integration Tests**
   - `test_openwebui_integration.py`
   - `test_pipeline_openwebui.py`
   - `test_pipeline_direct.py`

3. **Performance Tests**
   - `test_network_resilience.py`
   - `test_pipeline_fixed.py`

### **Pipeline Test Execution**
```bash
# Run all pipeline tests
python tests/run_comprehensive_tests.py

# Run specific pipeline test
python tests/test_pipeline_memory_async.py
```

---

## 🛠️ **DEVELOPMENT TESTING**

### **Testing New Features**
1. **Write test first** (TDD approach)
2. **Run existing tests** to ensure no regression
3. **Test new feature specifically**
4. **Run full test suite** before committing

### **Test Development Guidelines**
```python
# Example test structure
def test_memory_feature():
    # Setup
    setup_test_environment()
    
    # Execute
    result = call_memory_function()
    
    # Verify
    assert result.success == True
    assert result.data is not None
    
    # Cleanup
    cleanup_test_environment()
```

### **Mock Testing**
```python
# For testing without full system
from unittest.mock import patch, MagicMock

@patch('services.memory_service.MemoryService')
def test_memory_with_mock(mock_service):
    mock_service.return_value.store.return_value = {"success": True}
    # Test logic here
```

---

## 📋 **TEST MAINTENANCE**

### **Regular Test Maintenance**
1. **Weekly**: Run full test suite
2. **After changes**: Run focused tests
3. **Before deployment**: Run comprehensive tests
4. **Monthly**: Review test coverage

### **Test Environment Maintenance**
```bash
# Clean test environment
docker-compose down
docker volume prune
docker-compose up -d

# Reset test databases
python scripts/flush_databases.py
```

### **Test Data Management**
```bash
# Clear test data
rm -rf logs/test_*
rm -rf storage/test_*

# Backup test configurations
cp tests/config/* backup/test_config/
```

---

## 🎯 **PERFORMANCE BENCHMARKS**

### **Expected Performance**
```
Memory Storage: ~200ms average
Memory Retrieval: ~500ms average
Pipeline Processing: ~1-2s average
Database Queries: <100ms average
Health Checks: <50ms average
```

### **Performance Test Commands**
```bash
# Memory system performance
python tests/test_memory_service_proper.py

# Network resilience
python tests/test_network_resilience.py

# End-to-end performance
python tests/test_memory_comprehensive.py
```

---

## 🔧 **TROUBLESHOOTING GUIDE**

### **Test Environment Issues**
1. **Check Docker containers**: `docker ps`
2. **Verify service health**: `curl http://localhost:5001/health`
3. **Check logs**: `docker logs backend-memory-api`
4. **Reset environment**: `docker-compose down && docker-compose up -d`

### **Test Execution Issues**
1. **Check Python environment**: `python --version`
2. **Verify imports**: `python -c "import requests"`
3. **Check working directory**: `pwd`
4. **Use absolute paths**: `python /full/path/to/test.py`

### **Common Test Failures**
1. **Timeout errors**: Increase timeout values
2. **Connection errors**: Check service availability
3. **Import errors**: Verify Python path
4. **Encoding errors**: Use focused test runner

---

## 🎉 **SUCCESS CRITERIA**

### **Minimum Test Requirements**
- **Focused memory tests**: 100% pass rate
- **Basic functionality**: All core features working
- **No critical errors**: System stable
- **Performance acceptable**: Within benchmark ranges

### **Full Test Suite Success**
- **All test categories**: Comprehensive coverage
- **Performance tests**: Meeting benchmarks
- **Integration tests**: Full system validation
- **Security tests**: No vulnerabilities

---

**Last Updated:** July 17, 2025  
**Test Suite Version:** 2.0 (RAG Implementation)  
**Status:** Production-ready with comprehensive coverage
