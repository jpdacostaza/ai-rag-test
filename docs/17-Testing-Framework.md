# Testing Framework & Methodology

## Testing Strategy Overview

This document outlines the comprehensive testing framework and methodology for our OpenAI-compatible FastAPI backend with advanced RAG memory capabilities.

## Testing Philosophy

### 1. **Test-Driven Development (TDD)**
- Write tests before implementation
- Red-Green-Refactor cycle
- Comprehensive coverage requirements
- Continuous testing integration

### 2. **Pyramid Testing Strategy**
```
       ┌─────────────────┐
       │   E2E Tests     │  ← Few, high-value
       │   (Selenium)    │
       └─────────────────┘
      ┌─────────────────────┐
      │ Integration Tests   │  ← Some, critical paths
      │ (FastAPI TestClient)│
      └─────────────────────┘
    ┌─────────────────────────┐
    │     Unit Tests          │  ← Many, fast, isolated
    │   (pytest, unittest)   │
    └─────────────────────────┘
```

### 3. **Quality Gates**
- Minimum 90% code coverage
- All tests must pass before merge
- Performance benchmarks must meet thresholds
- Security tests must validate

## Test Framework Components

### Core Testing Libraries

**Primary Framework:**
```python
pytest==7.4.0              # Test runner and framework
pytest-asyncio==0.21.0     # Async test support
pytest-cov==4.1.0          # Coverage reporting
pytest-mock==3.11.1        # Mocking utilities
pytest-benchmark==4.0.0    # Performance testing
```

**Supporting Libraries:**
```python
httpx==0.24.1              # Async HTTP client for testing
faker==19.3.0              # Test data generation
factory-boy==3.3.0         # Model factories
responses==0.23.1          # HTTP request mocking
freezegun==1.2.2           # Time mocking
```

### Test Configuration (`pytest.ini`)

```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
asyncio_mode = auto
markers =
    unit: Unit tests (fast, isolated)
    integration: Integration tests (slower, with dependencies)
    e2e: End-to-end tests (slowest, full system)
    performance: Performance benchmark tests
    security: Security validation tests
    memory: Memory system specific tests
    llm: LLM integration tests
addopts = 
    --strict-markers
    --disable-warnings
    --cov=.
    --cov-report=html:htmlcov
    --cov-report=term-missing
    --cov-fail-under=90
```

## Test Organization Structure

### Directory Layout
```
tests/
├── conftest.py                 # Shared fixtures and configuration
├── unit/                       # Unit tests
│   ├── test_auth.py
│   ├── test_config.py
│   ├── test_error_handler.py
│   ├── test_metrics.py
│   ├── test_security.py
│   ├── services/
│   │   ├── test_llm_service.py
│   │   ├── test_memory_service.py
│   │   └── test_model_manager.py
│   ├── utilities/
│   │   ├── test_ai_tools.py
│   │   └── test_watchdog.py
│   └── routes/
│       ├── test_chat.py
│       ├── test_health.py
│       └── test_memory.py
├── integration/                # Integration tests
│   ├── test_chat_flow.py
│   ├── test_memory_integration.py
│   ├── test_api_gateway.py
│   └── test_llm_integration.py
├── e2e/                       # End-to-end tests
│   ├── test_full_chat_session.py
│   ├── test_document_upload.py
│   └── test_system_health.py
├── performance/               # Performance tests
│   ├── test_chat_benchmarks.py
│   ├── test_memory_performance.py
│   └── test_concurrent_load.py
└── security/                  # Security tests
    ├── test_auth_security.py
    ├── test_input_validation.py
    └── test_xss_prevention.py
```

## Test Categories & Examples

### 1. Unit Tests

**Example: LLM Service Test**
```python
# tests/unit/services/test_llm_service.py
import pytest
from unittest.mock import AsyncMock, patch
from services.llm_service import LLMService

class TestLLMService:
    @pytest.fixture
    def llm_service(self):
        return LLMService()
    
    @pytest.mark.asyncio
    async def test_generate_response_success(self, llm_service):
        # Arrange
        with patch('services.llm_service.aiohttp.ClientSession') as mock_session:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = {
                "choices": [{"message": {"content": "Test response"}}]
            }
            mock_session.return_value.__aenter__.return_value.post.return_value.__aenter__.return_value = mock_response
            
            # Act
            result = await llm_service.generate_response("Test prompt")
            
            # Assert
            assert result == "Test response"
            mock_session.return_value.__aenter__.return_value.post.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_response_error_handling(self, llm_service):
        # Test error handling scenarios
        with patch('services.llm_service.aiohttp.ClientSession') as mock_session:
            mock_session.return_value.__aenter__.return_value.post.side_effect = Exception("Network error")
            
            with pytest.raises(Exception, match="Network error"):
                await llm_service.generate_response("Test prompt")
```

**Example: Memory Service Test**
```python
# tests/unit/services/test_memory_service.py
import pytest
from unittest.mock import AsyncMock, patch
from services.memory_service import MemoryService

class TestMemoryService:
    @pytest.fixture
    def memory_service(self):
        return MemoryService()
    
    @pytest.mark.asyncio
    async def test_store_memory_success(self, memory_service):
        with patch('services.memory_service.ChromaDBManager') as mock_chroma:
            mock_chroma.return_value.add_memory = AsyncMock()
            
            await memory_service.store_memory("user123", "Important information")
            
            mock_chroma.return_value.add_memory.assert_called_once_with(
                user_id="user123",
                content="Important information"
            )
    
    @pytest.mark.asyncio
    async def test_retrieve_memories(self, memory_service):
        with patch('services.memory_service.ChromaDBManager') as mock_chroma:
            mock_chroma.return_value.search_memories = AsyncMock(
                return_value=["Memory 1", "Memory 2"]
            )
            
            memories = await memory_service.retrieve_memories("user123", "query")
            
            assert len(memories) == 2
            assert "Memory 1" in memories
```

### 2. Integration Tests

**Example: Chat Flow Integration**
```python
# tests/integration/test_chat_flow.py
import pytest
from fastapi.testclient import TestClient
from core.main import app

class TestChatFlowIntegration:
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_complete_chat_flow(self, client):
        # Test full chat completion flow
        response = client.post("/v1/chat/completions", json={
            "model": "llama2",
            "messages": [{"role": "user", "content": "Hello, world!"}],
            "user": "test_user"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "choices" in data
        assert len(data["choices"]) > 0
        assert "message" in data["choices"][0]
    
    def test_streaming_chat_flow(self, client):
        # Test streaming response
        response = client.post("/v1/chat/completions", json={
            "model": "llama2",
            "messages": [{"role": "user", "content": "Count to 5"}],
            "stream": True,
            "user": "test_user"
        })
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/plain; charset=utf-8"
```

**Example: Memory Integration Test**
```python
# tests/integration/test_memory_integration.py
import pytest
from fastapi.testclient import TestClient
from core.main import app

class TestMemoryIntegration:
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_memory_persistence_across_requests(self, client):
        # First request - store information
        response1 = client.post("/v1/chat/completions", json={
            "model": "llama2",
            "messages": [{"role": "user", "content": "My name is Alice"}],
            "user": "test_user_memory"
        })
        assert response1.status_code == 200
        
        # Second request - retrieve information
        response2 = client.post("/v1/chat/completions", json={
            "model": "llama2",
            "messages": [{"role": "user", "content": "What is my name?"}],
            "user": "test_user_memory"
        })
        assert response2.status_code == 200
        
        # Verify memory was used
        data = response2.json()
        response_content = data["choices"][0]["message"]["content"].lower()
        assert "alice" in response_content
```

### 3. Performance Tests

**Example: Chat Benchmark**
```python
# tests/performance/test_chat_benchmarks.py
import pytest
from fastapi.testclient import TestClient
from core.main import app

class TestChatPerformance:
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    @pytest.mark.benchmark
    def test_chat_response_time(self, client, benchmark):
        def chat_request():
            return client.post("/v1/chat/completions", json={
                "model": "llama2",
                "messages": [{"role": "user", "content": "Hello"}],
                "user": "benchmark_user"
            })
        
        result = benchmark(chat_request)
        assert result.status_code == 200
        # Benchmark automatically records timing
    
    @pytest.mark.benchmark
    def test_concurrent_chat_requests(self, client, benchmark):
        import asyncio
        import httpx
        
        async def concurrent_requests():
            async with httpx.AsyncClient(app=app) as ac:
                tasks = []
                for i in range(10):  # 10 concurrent requests
                    task = ac.post("/v1/chat/completions", json={
                        "model": "llama2",
                        "messages": [{"role": "user", "content": f"Request {i}"}],
                        "user": f"concurrent_user_{i}"
                    })
                    tasks.append(task)
                
                responses = await asyncio.gather(*tasks)
                return responses
        
        responses = benchmark(lambda: asyncio.run(concurrent_requests()))
        assert all(r.status_code == 200 for r in responses)
```

### 4. Security Tests

**Example: Input Validation Security**
```python
# tests/security/test_input_validation.py
import pytest
from fastapi.testclient import TestClient
from core.main import app

class TestInputValidationSecurity:
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_xss_prevention(self, client):
        # Test XSS attack prevention
        malicious_input = "<script>alert('xss')</script>"
        response = client.post("/v1/chat/completions", json={
            "model": "llama2",
            "messages": [{"role": "user", "content": malicious_input}],
            "user": "security_test"
        })
        
        assert response.status_code == 200
        data = response.json()
        response_content = data["choices"][0]["message"]["content"]
        assert "<script>" not in response_content
    
    def test_sql_injection_prevention(self, client):
        # Test SQL injection prevention
        malicious_input = "'; DROP TABLE users; --"
        response = client.post("/api/memory/search", json={
            "query": malicious_input,
            "user_id": "security_test"
        })
        
        # Should not cause server error
        assert response.status_code in [200, 400]  # Either processed safely or rejected
    
    def test_oversized_request_handling(self, client):
        # Test handling of oversized requests
        large_content = "A" * 100000  # 100KB message
        response = client.post("/v1/chat/completions", json={
            "model": "llama2",
            "messages": [{"role": "user", "content": large_content}],
            "user": "security_test"
        })
        
        # Should either process or reject gracefully
        assert response.status_code in [200, 413, 422]
```

## Test Fixtures and Utilities

### Global Fixtures (`conftest.py`)

```python
# conftest.py
import pytest
import asyncio
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from core.main import app

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)

@pytest.fixture
def mock_redis():
    """Mock Redis client."""
    with patch('redis.asyncio.Redis') as mock:
        mock_instance = AsyncMock()
        mock.return_value = mock_instance
        yield mock_instance

@pytest.fixture
def mock_chromadb():
    """Mock ChromaDB client."""
    with patch('chromadb.Client') as mock:
        mock_instance = AsyncMock()
        mock.return_value = mock_instance
        yield mock_instance

@pytest.fixture
def mock_llm_service():
    """Mock LLM service."""
    with patch('services.llm_service.LLMService') as mock:
        mock_instance = AsyncMock()
        mock_instance.generate_response = AsyncMock(return_value="Mocked response")
        mock.return_value = mock_instance
        yield mock_instance

@pytest.fixture
def test_user_data():
    """Test user data factory."""
    from faker import Faker
    fake = Faker()
    
    return {
        "user_id": fake.uuid4(),
        "username": fake.user_name(),
        "email": fake.email(),
        "chat_id": fake.uuid4()
    }

@pytest.fixture
def sample_chat_messages():
    """Sample chat messages for testing."""
    return [
        {"role": "user", "content": "Hello, how are you?"},
        {"role": "assistant", "content": "I'm doing well, thank you! How can I help you today?"},
        {"role": "user", "content": "Can you explain quantum computing?"}
    ]
```

## Test Data Management

### Factory Pattern for Test Data

```python
# tests/factories.py
import factory
from faker import Faker
from datetime import datetime, timezone

fake = Faker()

class ChatMessageFactory(factory.Factory):
    class Meta:
        model = dict
    
    role = factory.Iterator(["user", "assistant"])
    content = factory.LazyFunction(lambda: fake.text(max_nb_chars=200))
    timestamp = factory.LazyFunction(lambda: datetime.now(timezone.utc).isoformat())

class UserFactory(factory.Factory):
    class Meta:
        model = dict
    
    user_id = factory.LazyFunction(lambda: fake.uuid4())
    username = factory.LazyFunction(lambda: fake.user_name())
    email = factory.LazyFunction(lambda: fake.email())
    created_at = factory.LazyFunction(lambda: datetime.now(timezone.utc).isoformat())

class MemoryFactory(factory.Factory):
    class Meta:
        model = dict
    
    memory_id = factory.LazyFunction(lambda: fake.uuid4())
    user_id = factory.LazyFunction(lambda: fake.uuid4())
    content = factory.LazyFunction(lambda: fake.text(max_nb_chars=500))
    relevance_score = factory.LazyFunction(lambda: fake.random.uniform(0.1, 1.0))
    created_at = factory.LazyFunction(lambda: datetime.now(timezone.utc).isoformat())
```

## Test Execution & CI/CD Integration

### Running Tests Locally

```bash
# Run all tests
pytest

# Run specific test categories
pytest -m unit                    # Unit tests only
pytest -m integration            # Integration tests only
pytest -m "unit or integration"  # Unit and integration tests

# Run with coverage
pytest --cov=. --cov-report=html

# Run performance benchmarks
pytest -m performance --benchmark-only

# Run security tests
pytest -m security
```

### GitHub Actions CI Configuration

```yaml
# .github/workflows/test.yml
name: Test Suite

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.9, 3.10, 3.11]
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pytest-cov pytest-asyncio
    
    - name: Run unit tests
      run: pytest -m unit --cov=. --cov-report=xml
    
    - name: Run integration tests
      run: pytest -m integration
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
```

## Metrics and Reporting

### Coverage Requirements
- **Minimum Coverage**: 90% overall
- **Critical Components**: 95% coverage required
  - Core authentication
  - Security middleware
  - Memory management
  - LLM service integration

### Test Metrics Dashboard
```python
# Generated automatically by pytest-html
Test Results Summary:
├── Total Tests: 247
├── Passed: 243
├── Failed: 2
├── Skipped: 2
├── Coverage: 92.3%
├── Execution Time: 45.2s
└── Performance Benchmarks:
    ├── Chat Response: 150ms avg
    ├── Memory Retrieval: 50ms avg
    └── Concurrent Load: 500 req/s
```

## Best Practices & Guidelines

### 1. **Test Naming Conventions**
```python
def test_[component]_[scenario]_[expected_outcome]:
    # Example: test_chat_service_invalid_input_raises_validation_error
    pass
```

### 2. **Test Structure (AAA Pattern)**
```python
def test_example():
    # Arrange - Set up test data and conditions
    user_id = "test_user"
    message = "Hello"
    
    # Act - Execute the code under test
    result = chat_service.process_message(user_id, message)
    
    # Assert - Verify the expected outcome
    assert result is not None
    assert "response" in result
```

### 3. **Mock Guidelines**
- Mock external dependencies (APIs, databases)
- Don't mock the code under test
- Use realistic mock data
- Verify mock interactions when relevant

### 4. **Test Independence**
- Each test should be isolated and independent
- Tests should not depend on execution order
- Clean up test data after each test
- Use fixtures for shared setup

### 5. **Performance Test Considerations**
- Set realistic performance thresholds
- Test under various load conditions
- Monitor resource usage during tests
- Use benchmark fixtures for consistent measurement

## Troubleshooting Common Issues

### 1. **Async Test Issues**
```python
# Problem: Async test not running
def test_async_function():  # Missing @pytest.mark.asyncio
    await some_async_function()

# Solution:
@pytest.mark.asyncio
async def test_async_function():
    await some_async_function()
```

### 2. **Mock Scope Issues**
```python
# Problem: Mock not working in async context
with patch('module.function') as mock:
    await async_function()  # Mock may not apply

# Solution: Use async context managers
async with patch('module.function') as mock:
    await async_function()
```

### 3. **Database Test Isolation**
```python
# Use fixtures for database cleanup
@pytest.fixture(autouse=True)
async def cleanup_database():
    yield
    # Cleanup after each test
    await database.clear_test_data()
```

## Conclusion

This comprehensive testing framework ensures high-quality, reliable code through:
- Multi-layered testing strategy
- Comprehensive coverage requirements
- Performance and security validation
- Automated CI/CD integration
- Clear testing guidelines and best practices

The framework supports both development velocity and production reliability, providing confidence in system behavior across all scenarios.
