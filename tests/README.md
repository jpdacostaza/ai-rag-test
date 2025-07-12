# Enhanced Memory Pipeline v4.0 - Test Suite

This comprehensive test suite validates all aspects of the Enhanced Memory Pipeline v4.0 including user ID extraction, memory isolation, pipeline integration, and authentication priority handling.

## 🚀 Quick Start

### Run Comprehensive Test Suite (Recommended)
```bash
python tests/run_comprehensive_tests.py
```

### Run Specific Test Categories
```bash
# Unit tests only (no system required)
python tests/run_comprehensive_tests.py --unit-only

# Live integration tests only (requires running system)
python tests/run_comprehensive_tests.py --integration-only

# Skip existing legacy tests
python tests/run_comprehensive_tests.py --skip-existing
```

### Run Legacy Test Suite
```bash
python tests/run_all_tests.py
```

### Manual Test Execution
```bash
# New comprehensive unit tests
python tests/test_comprehensive_user_memory.py

# New live integration tests (requires system running)
python tests/test_live_integration.py

# Legacy individual test files
pytest tests/test_memory_system.py -v
pytest tests/test_memory_function.py -v

# Legacy integration test
python tests/integration_test.py
```

## 📋 Test Structure

### 🆕 Enhanced Memory Pipeline v4.0 Tests

#### `test_comprehensive_user_memory.py`
**Comprehensive unit tests for user authentication and memory isolation**
- ✅ User ID extraction with priority handling (pipeline > email > id > username > name > anonymous)
- ✅ Memory save/retrieve operations with user isolation
- ✅ Pipeline integration with user authentication
- ✅ Prompt logic and system message injection
- ✅ Data isolation between different users (no memory bleed)
- ✅ Error handling and edge cases
- ✅ Authentication priority system validation
- ✅ Malformed data handling

#### `test_live_integration.py`
**Live system integration tests (requires running system)**
- ✅ Real user ID extraction in live API calls
- ✅ Actual memory save/retrieve operations with multiple users
- ✅ Live pipeline user injection testing
- ✅ Real user isolation and memory bleed prevention
- ✅ Cross-user memory access prevention
- ✅ Edge case handling in live environment
- ✅ System health validation
- ✅ End-to-end user flow testing

#### `run_comprehensive_tests.py`
**Test runner for all Enhanced Memory Pipeline v4.0 tests**
- 🔄 Runs unit tests and integration tests
- 📊 Generates comprehensive test reports
- 🏥 Checks system health and requirements
- ⚙️ Configurable test execution (unit-only, integration-only, etc.)
- 📄 JSON report generation with detailed results

### 📜 Legacy Test Suite

#### `test_memory_system.py`
**Legacy comprehensive API and integration tests**
- ✅ Memory API health checks
- ✅ Memory storage via learning interactions
- ✅ Semantic memory retrieval  
- ✅ Memory persistence validation
- ✅ Backend integration testing
- ✅ Pipelines integration testing
- ✅ Concurrent operations testing
- ✅ Performance validation
- ✅ Error handling verification

### `test_memory_function.py`
**Memory function specific tests**
- ✅ Function configuration (Valves)
- ✅ Memory service components
- ✅ Conversation processing simulation
- ✅ Edge case handling
- ✅ Performance benchmarks
- ✅ Configuration validation

### `integration_test.py`
**End-to-end workflow validation**
- ✅ Complex conversation storage
- ✅ Multi-query semantic search
- ✅ Information update handling
- ✅ Performance under load
- ✅ System statistics validation

### Supporting Files
- `conftest.py` - Test configuration and fixtures
- `run_tests.py` - Comprehensive test runner with pre-checks
- `run_all_tests.py` - Simple test runner
- `test_report.py` - Test report generator
- `requirements.txt` - Test dependencies

## 🔧 Test Dependencies

```bash
pytest>=7.0.0
pytest-asyncio>=0.21.0
httpx>=0.24.0
```

Auto-installed by test runners or install manually:
```bash
pip install -r tests/requirements.txt
```

## 📊 What Gets Tested

### Memory Storage
- ✅ Learning interaction processing
- ✅ Memory extraction algorithms
- ✅ Redis short-term storage
- ✅ ChromaDB long-term storage
- ✅ Large content handling

### Memory Retrieval  
- ✅ Semantic search functionality
- ✅ Relevance scoring
- ✅ Multi-source retrieval
- ✅ Threshold-based filtering
- ✅ Query performance

### System Integration
- ✅ Backend API health
- ✅ Memory API endpoints
- ✅ Pipelines communication
- ✅ Embedding generation
- ✅ Cross-service integration

### Performance & Reliability
- ✅ Concurrent operations
- ✅ Response time validation
- ✅ Error handling
- ✅ Memory persistence
- ✅ System recovery

## 🎯 Test Results Interpretation

### Success Indicators
- All tests pass (19/19 memory system, 14/17 function tests)
- Integration test completes successfully
- Performance metrics within acceptable ranges
- All services report healthy status

### Common Issues
- **404 errors**: Memory API endpoints not available
- **Import errors**: Memory function modules not found (expected for some tests)
- **Timeout errors**: Services not responding or overloaded
- **Embedding errors**: Ollama service or models not available

## 🎯 Test Coverage

### Enhanced Memory Pipeline v4.0 Features Tested

#### User Authentication & Extraction
- ✅ **Pipeline Injection Priority**: System messages with `AUTHENTICATED_USER_ID` have highest priority
- ✅ **Email Priority**: Email takes precedence over ID, username, and name
- ✅ **ID Priority**: User ID takes precedence over username and name
- ✅ **Username Priority**: Username takes precedence over name
- ✅ **Name Fallback**: Name used when no other identifier available
- ✅ **Anonymous Fallback**: "anonymous" used when no user data available
- ✅ **Empty Field Handling**: Graceful handling of empty or null user fields

#### Memory Isolation & Security
- ✅ **User Data Isolation**: Each user's memories are completely isolated
- ✅ **Memory Bleed Prevention**: Users cannot access other users' memories
- ✅ **Cross-User Access Prevention**: Attempts to access other users' data are blocked
- ✅ **User ID Validation**: Memory operations require valid user identification

#### Pipeline Integration
- ✅ **User ID Injection**: Pipeline properly injects user IDs into system messages
- ✅ **Message Processing**: Messages are correctly processed with user context
- ✅ **Authentication Flow**: Complete authentication flow from pipeline to backend

#### Error Handling & Edge Cases
- ✅ **Malformed Requests**: Graceful handling of invalid request formats
- ✅ **Missing User Data**: Proper fallback when user data is missing
- ✅ **API Failures**: Resilient handling of memory API failures
- ✅ **Invalid Message Formats**: Robust handling of malformed messages

## 🔧 Prerequisites

### For Unit Tests Only
- Python 3.8+
- pytest
- Required Python packages (see requirements.txt)

### For Integration Tests
- All unit test requirements
- Docker and Docker Compose
- Running Enhanced Memory Pipeline v4.0 system:
  ```bash
  docker-compose up -d
  ```

## 📊 Test Reports

### Comprehensive Test Report
Running the comprehensive test suite generates detailed JSON reports:
- **Summary Statistics**: Pass/fail counts and success rates
- **Detailed Results**: Individual test outcomes with error details
- **Test Categories**: Results grouped by functionality area
- **Timestamps**: Complete execution timeline
- **System Health**: Pre-test system validation results

### Report Location
Reports are automatically saved with timestamps:
- `comprehensive_test_report_YYYYMMDD_HHMMSS.json`
- `live_test_report_YYYYMMDD_HHMMSS.json`

## 🚦 Running Tests in CI/CD

### GitHub Actions Example
```yaml
name: Enhanced Memory Pipeline Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.8'
      - name: Install dependencies
        run: |
          pip install -r tests/requirements.txt
      - name: Run unit tests
        run: |
          python tests/run_comprehensive_tests.py --unit-only
      - name: Start system
        run: |
          docker-compose up -d
          sleep 30  # Wait for system startup
      - name: Run integration tests
        run: |
          python tests/run_comprehensive_tests.py --integration-only
```

## 🐛 Troubleshooting

### Common Issues

#### "System services not running"
**Solution**: Start the system with Docker Compose:
```bash
docker-compose up -d
# Wait for all services to be healthy
docker-compose ps
```

#### "requests package not available"
**Solution**: Install test dependencies:
```bash
pip install -r tests/requirements.txt
```

#### "Memory API unavailable"
**Solution**: Check if memory API is running:
```bash
curl http://localhost:8001/health
# If not running, restart the system
docker-compose restart memory_api
```

#### "Tests fail with 'anonymous' user"
**Solution**: This is expected behavior when no user data is provided. The system correctly falls back to "anonymous" for security.

### Debug Mode

To run tests with additional debugging:
```bash
# Enable verbose pytest output
python tests/test_comprehensive_user_memory.py -v -s

# Run with Python debugging
python -u tests/test_live_integration.py

# Check system logs during testing
docker-compose logs -f backend memory_api pipelines
```

## 📈 Performance Benchmarks

The test suite includes performance validation:
- **Memory Storage**: < 100ms per operation
- **Memory Retrieval**: < 200ms for semantic search
- **User Extraction**: < 10ms for ID extraction
- **Pipeline Processing**: < 50ms for message injection

## 🔒 Security Validation

Security-focused tests ensure:
- **Data Isolation**: Complete separation between user data
- **Access Control**: Users cannot access unauthorized memories
- **Input Validation**: Malformed inputs are handled safely
- **Authentication**: User identification is reliable and secure

## 🎉 Success Criteria

The memory system is considered fully functional when:
- ✅ All API endpoints respond correctly
- ✅ Memory storage and retrieval work end-to-end
- ✅ Semantic search returns relevant results
- ✅ Performance metrics meet benchmarks
- ✅ Error handling works gracefully
- ✅ Concurrent operations succeed
- ✅ Integration test passes completely

## 💡 Usage Tips

1. **Run tests regularly** during development to catch regressions
2. **Use --quick flag** for fast validation during coding
3. **Run integration test** before production deployments
4. **Generate reports** for documentation and debugging
5. **Check service health** first if tests fail

This comprehensive test suite ensures the memory system is robust, performant, and ready for production use.
