# Backend Demo Test Suite

This directory contains a comprehensive test suite for real-life simulation testing of the entire backend system. The tests cover all modules, APIs, tools, security features, and performance characteristics.

## 📁 Test Structure

```
demo-test/
├── master_test_runner.py              # Main orchestrator for all tests
├── comprehensive_test_suite_v2.py     # Basic API and integration tests
├── tool_integration_tests.py          # AI tools testing (weather, time, math, etc.)
├── security_tests.py                  # Authentication, authorization, security
├── performance_tests.py               # Load testing, performance, stress testing
├── results/                           # Generated test reports and results
└── README.md                          # This documentation
```

## 🚀 Quick Start

### Prerequisites
1. Backend system must be running on `http://localhost:8001`
2. All required dependencies installed (`pip install -r requirements.txt`)
3. Redis and ChromaDB services available
4. Valid API key configured

### Running Tests

```bash
# Navigate to the backend directory
cd /path/to/backend

# Run all tests (comprehensive)
python demo-test/master_test_runner.py --all

# Quick smoke tests (basic functionality)
python demo-test/master_test_runner.py --quick

# Specific test suites
python demo-test/master_test_runner.py --tools        # AI tools only
python demo-test/master_test_runner.py --security     # Security tests only
python demo-test/master_test_runner.py --performance  # Performance tests only

# Individual test modules
python demo-test/tool_integration_tests.py
python demo-test/security_tests.py
python demo-test/performance_tests.py
```

## 🧪 Test Modules

### 1. Comprehensive Integration Tests (`comprehensive_test_suite_v2.py`)
- **Purpose**: Basic API functionality and integration testing
- **Coverage**: 
  - Health endpoints
  - Basic authentication
  - Chat functionality
  - Core system integration
- **Duration**: ~2-3 minutes
- **Use Case**: Quick verification that the system is working

### 2. AI Tool Integration Tests (`tool_integration_tests.py`)
- **Purpose**: Comprehensive testing of all AI tools
- **Coverage**:
  - Weather tool (various cities, error cases)
  - Time tool (timezones, formats)
  - Math calculator (expressions, edge cases)
  - Unit conversion (different units)
  - Web search functionality
  - Wikipedia integration
  - Python code execution (security testing)
  - System information gathering
- **Duration**: ~5-10 minutes
- **Use Case**: Verify all AI tools work correctly with real-world inputs

### 3. Security & Authentication Tests (`security_tests.py`)
- **Purpose**: Security vulnerability and authentication testing
- **Coverage**:
  - API key validation (various formats)
  - Authorization mechanisms
  - Input validation and sanitization
  - SQL injection, XSS, command injection attempts
  - Rate limiting verification
  - CORS and security headers
  - Error information disclosure prevention
- **Duration**: ~3-5 minutes
- **Use Case**: Ensure system is secure against common attacks

### 4. Performance & Load Tests (`performance_tests.py`)
- **Purpose**: System performance under various load conditions
- **Coverage**:
  - Response time measurement
  - Concurrent request handling
  - Sustained load testing (60 seconds)
  - Cache performance verification
  - Memory leak detection
  - Error recovery testing
- **Duration**: ~5-10 minutes
- **Use Case**: Verify system performs adequately under real-world load

### 5. Master Test Runner (`master_test_runner.py`)
- **Purpose**: Orchestrates all test modules with unified reporting
- **Features**:
  - System readiness checking
  - Sequential test execution
  - Unified result reporting
  - Error handling and recovery
  - Multiple execution modes

## 📊 Test Results and Reports

### Generated Reports
All tests generate detailed JSON reports in the `demo-test/` directory:

- `comprehensive_test_report_YYYYMMDD_HHMMSS.json`
- `tool_test_report_YYYYMMDD_HHMMSS.json`
- `security_test_report_YYYYMMDD_HHMMSS.json`
- `performance_test_report_YYYYMMDD_HHMMSS.json`
- `master_test_report_YYYYMMDD_HHMMSS.json` (combined summary)

### Report Contents
Each report includes:
- **Summary Statistics**: Pass/fail counts, success rates, duration
- **Detailed Results**: Individual test outcomes with timing
- **Error Analysis**: Failed tests with error messages
- **Performance Metrics**: Response times, throughput, resource usage
- **Security Findings**: Vulnerabilities, warnings, recommendations

## 🎯 Real-Life Simulation Scenarios

### User Interaction Patterns
The tests simulate realistic user interactions:
- Casual chat conversations
- Specific tool usage (weather, time, calculations)
- Document upload and RAG queries
- Multiple concurrent users
- Error conditions and recovery

### System Stress Scenarios
- High concurrency (5-20 simultaneous requests)
- Sustained load (1 request/second for 60 seconds)
- Memory pressure (50+ consecutive requests)
- Error injection and recovery
- Cache performance under load

### Security Attack Simulations
- SQL injection attempts
- Cross-site scripting (XSS)
- Command injection
- Path traversal attacks
- Authentication bypass attempts
- Rate limiting evasion

## 🔧 Configuration

### Test Configuration
Modify test parameters in each module:

```python
# In tool_integration_tests.py
class ToolTestSuite:
    def __init__(self, base_url="http://localhost:8001", 
                 api_key="your-api-key"):
        # Configure endpoints and credentials
```

### Environment Variables
Set these environment variables for testing:
```bash
export BACKEND_URL="http://localhost:8001"
export API_KEY="f2b985dd-219f-45b1-a90e-170962cc7082"
export TEST_USER_PREFIX="test_user"
```

## 📈 Performance Benchmarks

### Expected Performance Metrics
- **Health Endpoints**: < 100ms response time
- **Chat Endpoints**: < 3s average response time
- **Tool Endpoints**: < 5s for weather/time, < 10s for search/wiki
- **Concurrent Load**: Handle 10+ simultaneous requests
- **Error Rate**: < 1% under normal load
- **Cache Hit Rate**: > 80% for repeated queries

### Performance Thresholds
Tests use these criteria for pass/fail:
- Response time: Acceptable < 5s, Warning > 10s
- Success rate: Pass > 95%, Fail < 90%
- Concurrent handling: Pass if all requests complete
- Memory stability: Pass if response times don't increase > 50%

## 🐛 Troubleshooting

### Common Issues

1. **Connection Refused**
   ```
   Error: Cannot connect to backend
   Solution: Ensure backend is running on http://localhost:8001
   ```

2. **Authentication Failures**
   ```
   Error: 401 Unauthorized
   Solution: Check API key configuration
   ```

3. **Test Timeouts**
   ```
   Error: Request timeout
   Solution: Increase timeout values or check system performance
   ```

4. **High Failure Rates**
   ```
   Error: Many tests failing
   Solution: Check backend logs, database connectivity, resource usage
   ```

### Debug Mode
Enable verbose output by modifying the test modules:
```python
# Add to any test module
logging.basicConfig(level=logging.DEBUG)
print(f"Response: {response.text}")  # Add debug prints
```

## 🔍 Test Analysis

### Interpreting Results

**Green (✅)**: Test passed successfully
**Yellow (⚠️)**: Test passed with warnings or performance issues
**Red (❌)**: Test failed

### Key Metrics to Monitor
1. **Success Rate**: Should be > 95% for production readiness
2. **Response Times**: Average should be < 3s for chat endpoints
3. **Concurrent Performance**: System should handle 10+ users
4. **Security Score**: All security tests should pass
5. **Cache Effectiveness**: Should show > 10% speedup for repeated queries

### Production Readiness Criteria
- All comprehensive tests pass
- Security tests pass with no critical issues
- Performance tests meet response time thresholds
- No memory leaks detected
- Error recovery works correctly

## 📚 Extensions

### Adding New Tests
1. Create new test module in `demo-test/`
2. Follow existing patterns for result reporting
3. Add to `master_test_runner.py` if needed
4. Update this README

### Custom Scenarios
Create custom test scenarios by:
```python
# Example custom test
def test_custom_scenario(self):
    """Test specific business logic."""
    # Your custom test logic here
    pass
```

## 📝 Maintenance

### Regular Testing
- Run daily: `--quick` for basic health checks
- Run weekly: `--all` for comprehensive validation
- Run before releases: Full performance and security testing
- Run after changes: Relevant test modules

### Updating Tests
- Keep test data current (cities, timezones, etc.)
- Update expected responses as system evolves
- Add new test cases for new features
- Review and update performance thresholds

---

## 🎯 Summary

This comprehensive test suite provides:
- **Real-world simulation** of user interactions
- **Complete coverage** of all backend modules
- **Security validation** against common attacks
- **Performance verification** under various loads
- **Detailed reporting** for analysis and monitoring
- **Automated execution** with minimal setup

Use these tests to ensure your backend system is robust, secure, and performant for production deployment.
