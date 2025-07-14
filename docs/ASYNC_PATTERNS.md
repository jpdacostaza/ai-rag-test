# Async Patterns and Best Practices

## Overview

This document outlines the async patterns, best practices, and implementation guidelines for the AI backend system. All services follow proper async/await patterns for optimal performance and scalability.

## Core Async Principles

### 1. Async-First Architecture
Every service operation is designed to be non-blocking:

```python
# ✅ Correct: All service methods are async
class ChatService:
    async def process_chat_request(self, request: ChatRequest) -> ChatResponse:
        # Non-blocking operations
        memories = await self.memory_service.get_memories(request.user_id)
        response = await self.llm_service.call_llm(request.messages)
        return response

# ❌ Incorrect: Blocking operations
class ChatService:
    def process_chat_request(self, request: ChatRequest) -> ChatResponse:
        # Blocks the event loop
        memories = self.memory_service.get_memories_sync(request.user_id)
        response = self.llm_service.call_llm_sync(request.messages)
        return response
```

### 2. Proper Async Context Management
Use async context managers for resource management:

```python
# ✅ Async context manager for HTTP clients
class LLMService:
    async def call_llm(self, messages: List[Dict]) -> str:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(self.api_url, json={
                "messages": messages
            })
            return response.json()["content"]

# ✅ Async context manager for database sessions
class MemoryService:
    async def store_memory(self, memory: ConversationMemory) -> None:
        async with get_database_session() as session:
            session.add(memory)
            await session.commit()
```

### 3. Concurrent Operations with asyncio.gather()
Execute independent operations concurrently:

```python
# ✅ Concurrent execution
class ChatService:
    async def process_chat_request(self, request: ChatRequest) -> ChatResponse:
        # These operations can run concurrently
        memory_task = self.memory_service.get_memories(request.user_id)
        cache_task = self.cache_service.get_cached_response(request.cache_key)
        context_task = self.vector_service.search_similar(request.query)
        
        # Await all results together
        memories, cached_response, context = await asyncio.gather(
            memory_task, cache_task, context_task
        )
        
        if cached_response:
            return cached_response
            
        return await self._generate_response(memories, context, request)

# ❌ Sequential execution (slower)
class ChatService:
    async def process_chat_request(self, request: ChatRequest) -> ChatResponse:
        memories = await self.memory_service.get_memories(request.user_id)
        cached_response = await self.cache_service.get_cached_response(request.cache_key)
        context = await self.vector_service.search_similar(request.query)
        # Sequential execution is slower when operations are independent
```

## Service Patterns

### 1. Service Base Class Pattern
All services inherit from a common base:

```python
class BaseService:
    """Base class for all services with common functionality"""
    
    def __init__(self):
        self.logger = get_structured_logger(self.__class__.__name__)
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize service resources"""
        if not self._initialized:
            await self._setup_resources()
            self._initialized = True
    
    async def cleanup(self) -> None:
        """Cleanup service resources"""
        if self._initialized:
            await self._cleanup_resources()
            self._initialized = False
    
    async def _setup_resources(self) -> None:
        """Override in subclasses"""
        pass
    
    async def _cleanup_resources(self) -> None:
        """Override in subclasses"""
        pass
    
    async def health_check(self) -> Dict[str, Any]:
        """Check service health"""
        return {
            "service": self.__class__.__name__,
            "status": "healthy" if self._initialized else "not_initialized",
            "timestamp": datetime.utcnow().isoformat()
        }
```

### 2. Service Implementation Pattern
```python
class LLMService(BaseService):
    def __init__(self, settings: Settings):
        super().__init__()
        self.settings = settings
        self._client: Optional[httpx.AsyncClient] = None
    
    async def _setup_resources(self) -> None:
        """Initialize HTTP client with connection pooling"""
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0),
            limits=httpx.Limits(
                max_keepalive_connections=5,
                max_connections=10
            )
        )
        self.logger.info("LLM service initialized")
    
    async def _cleanup_resources(self) -> None:
        """Cleanup HTTP client"""
        if self._client:
            await self._client.aclose()
            self._client = None
        self.logger.info("LLM service cleaned up")
    
    async def call_llm(self, messages: List[Dict]) -> str:
        """Make async LLM call with proper error handling"""
        if not self._client:
            raise LLMServiceError("Service not initialized")
        
        try:
            response = await self._client.post(
                f"{self.settings.llm_api_url}/chat/completions",
                json={
                    "model": self.settings.llm_model,
                    "messages": messages,
                    "stream": False
                },
                headers={"Authorization": f"Bearer {self.settings.llm_api_key}"}
            )
            response.raise_for_status()
            
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            
            self.logger.info("LLM call successful", 
                           model=self.settings.llm_model,
                           message_count=len(messages))
            
            return content
            
        except httpx.HTTPStatusError as e:
            self.logger.error("LLM API error", 
                            status_code=e.response.status_code,
                            error=str(e))
            raise LLMServiceError(f"LLM API error: {e.response.status_code}") from e
        
        except httpx.RequestError as e:
            self.logger.error("LLM request error", error=str(e))
            raise LLMServiceError(f"LLM request failed: {str(e)}") from e
```

### 3. Streaming Response Pattern
```python
class LLMService(BaseService):
    async def call_llm_stream(self, messages: List[Dict]) -> AsyncGenerator[str, None]:
        """Stream LLM responses with proper async iteration"""
        if not self._client:
            raise LLMServiceError("Service not initialized")
        
        try:
            async with self._client.stream(
                "POST",
                f"{self.settings.llm_api_url}/chat/completions",
                json={
                    "model": self.settings.llm_model,
                    "messages": messages,
                    "stream": True
                },
                headers={"Authorization": f"Bearer {self.settings.llm_api_key}"}
            ) as response:
                response.raise_for_status()
                
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]  # Remove "data: " prefix
                        if data == "[DONE]":
                            break
                        
                        try:
                            chunk = json.loads(data)
                            if "choices" in chunk and chunk["choices"]:
                                delta = chunk["choices"][0].get("delta", {})
                                if "content" in delta:
                                    yield delta["content"]
                        except json.JSONDecodeError:
                            continue  # Skip malformed chunks
                            
        except httpx.HTTPStatusError as e:
            self.logger.error("LLM streaming error", 
                            status_code=e.response.status_code)
            raise LLMServiceError(f"LLM streaming error: {e.response.status_code}") from e
```

## Error Handling Patterns

### 1. Service-Level Error Handling
Define specific exception types for each service:

```python
# Service-specific exceptions
class LLMServiceError(Exception):
    """LLM service related errors"""
    pass

class MemoryServiceError(Exception):
    """Memory service related errors"""
    pass

class VectorServiceError(Exception):
    """Vector service related errors"""
    pass

# Error handling decorator
def handle_service_errors(operation_name: str):
    """Decorator for consistent service error handling"""
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(self, *args, **kwargs):
            try:
                return await func(self, *args, **kwargs)
            except Exception as e:
                self.logger.error(
                    f"{operation_name} failed",
                    error=str(e),
                    error_type=type(e).__name__
                )
                # Re-raise as service-specific error
                service_name = self.__class__.__name__
                raise globals()[f"{service_name}Error"](
                    f"{operation_name} failed: {str(e)}"
                ) from e
        return wrapper
    return decorator

# Usage in service methods
class ChatService(BaseService):
    @handle_service_errors("process_chat_request")
    async def process_chat_request(self, request: ChatRequest) -> ChatResponse:
        # Implementation here
        pass
```

### 2. Circuit Breaker Pattern
Prevent cascading failures with circuit breaker:

```python
class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    async def call(self, func: Callable, *args, **kwargs):
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = "HALF_OPEN"
            else:
                raise CircuitBreakerError("Circuit breaker is OPEN")
        
        try:
            result = await func(*args, **kwargs)
            # Success - reset failure count
            if self.state == "HALF_OPEN":
                self.state = "CLOSED"
            self.failure_count = 0
            return result
            
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.failure_count >= self.failure_threshold:
                self.state = "OPEN"
            
            raise e

# Usage in service
class LLMService(BaseService):
    def __init__(self, settings: Settings):
        super().__init__()
        self.circuit_breaker = CircuitBreaker()
    
    async def call_llm(self, messages: List[Dict]) -> str:
        return await self.circuit_breaker.call(self._make_llm_call, messages)
```

### 3. Retry with Exponential Backoff
```python
async def retry_with_backoff(
    func: Callable,
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    backoff_factor: float = 2.0
):
    """Retry function with exponential backoff"""
    for attempt in range(max_retries + 1):
        try:
            return await func()
        except Exception as e:
            if attempt == max_retries:
                raise e
            
            delay = min(base_delay * (backoff_factor ** attempt), max_delay)
            await asyncio.sleep(delay)

# Usage in service
class MemoryService(BaseService):
    async def store_memory(self, memory: ConversationMemory) -> None:
        await retry_with_backoff(
            lambda: self._store_memory_internal(memory),
            max_retries=3
        )
```

## Testing Patterns

### 1. Async Test Setup
```python
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock

@pytest_asyncio.fixture
async def llm_service():
    """Create LLM service for testing"""
    settings = MagicMock()
    settings.llm_api_url = "http://test-api"
    settings.llm_api_key = "test-key"
    settings.llm_model = "test-model"
    
    service = LLMService(settings)
    await service.initialize()
    yield service
    await service.cleanup()

@pytest_asyncio.fixture
async def mock_http_client():
    """Mock HTTP client for testing"""
    mock_client = AsyncMock(spec=httpx.AsyncClient)
    mock_response = AsyncMock()
    mock_response.json.return_value = {
        "choices": [{"message": {"content": "Test response"}}]
    }
    mock_client.post.return_value = mock_response
    return mock_client
```

### 2. Service Testing Patterns
```python
@pytest.mark.asyncio
async def test_llm_service_call(llm_service, mock_http_client):
    """Test LLM service call with mocked HTTP client"""
    # Arrange
    llm_service._client = mock_http_client
    messages = [{"role": "user", "content": "Hello"}]
    
    # Act
    result = await llm_service.call_llm(messages)
    
    # Assert
    assert result == "Test response"
    mock_http_client.post.assert_called_once()
    call_args = mock_http_client.post.call_args
    assert call_args[1]["json"]["messages"] == messages

@pytest.mark.asyncio
async def test_service_error_handling(llm_service, mock_http_client):
    """Test service error handling"""
    # Arrange
    llm_service._client = mock_http_client
    mock_http_client.post.side_effect = httpx.HTTPStatusError(
        "API Error", request=MagicMock(), response=MagicMock(status_code=500)
    )
    
    # Act & Assert
    with pytest.raises(LLMServiceError) as exc_info:
        await llm_service.call_llm([{"role": "user", "content": "Hello"}])
    
    assert "LLM API error: 500" in str(exc_info.value)

@pytest.mark.asyncio
async def test_concurrent_operations():
    """Test concurrent service operations"""
    # Arrange
    mock_memory_service = AsyncMock()
    mock_cache_service = AsyncMock()
    mock_vector_service = AsyncMock()
    
    mock_memory_service.get_memories.return_value = ["memory1", "memory2"]
    mock_cache_service.get_cached_response.return_value = None
    mock_vector_service.search_similar.return_value = ["context1"]
    
    chat_service = ChatService(
        memory_service=mock_memory_service,
        cache_service=mock_cache_service,
        vector_service=mock_vector_service
    )
    
    # Act
    request = ChatRequest(user_id="user1", query="test query")
    start_time = time.time()
    
    # This should execute concurrently
    await chat_service.process_chat_request(request)
    
    end_time = time.time()
    
    # Assert - operations should have run concurrently
    assert all([
        mock_memory_service.get_memories.called,
        mock_cache_service.get_cached_response.called,
        mock_vector_service.search_similar.called
    ])
    
    # Should be faster than sequential execution
    assert end_time - start_time < 0.1  # Assuming mocks respond instantly
```

### 3. Integration Testing
```python
@pytest.mark.asyncio
async def test_service_integration():
    """Test service integration with real dependencies"""
    # Use test database and Redis instances
    test_settings = Settings(
        redis_host="localhost",
        redis_port=6380,  # Test Redis port
        database_url="sqlite:///test.db"
    )
    
    # Initialize services
    redis_service = RedisService(test_settings)
    memory_service = MemoryService(redis_service, test_settings)
    chat_service = ChatService(memory_service=memory_service)
    
    try:
        await redis_service.initialize()
        await memory_service.initialize()
        await chat_service.initialize()
        
        # Test actual service interaction
        memory = ConversationMemory(
            user_id="test_user",
            message="Test message",
            response="Test response"
        )
        
        await memory_service.store_memory(memory)
        retrieved_memories = await memory_service.get_memories("test_user")
        
        assert len(retrieved_memories) == 1
        assert retrieved_memories[0].message == "Test message"
        
    finally:
        # Cleanup
        await chat_service.cleanup()
        await memory_service.cleanup()
        await redis_service.cleanup()
```

## Performance Optimization

### 1. Connection Pooling
```python
class DatabaseManager:
    def __init__(self, database_url: str):
        self.engine = create_async_engine(
            database_url,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,
            pool_recycle=3600
        )
        self.session_factory = async_sessionmaker(
            self.engine,
            expire_on_commit=False
        )
    
    async def get_session(self) -> AsyncSession:
        """Get database session from pool"""
        return self.session_factory()

class RedisService:
    def __init__(self, settings: Settings):
        self.pool = aioredis.ConnectionPool.from_url(
            f"redis://{settings.redis_host}:{settings.redis_port}",
            max_connections=20,
            retry_on_timeout=True
        )
        self.redis = aioredis.Redis(connection_pool=self.pool)
```

### 2. Caching Strategies
```python
class CacheService(BaseService):
    def __init__(self, redis_service: RedisService):
        super().__init__()
        self.redis = redis_service
        self._local_cache = {}  # In-memory cache for hot data
    
    async def get_with_fallback(self, key: str, fallback_func: Callable) -> Any:
        """Multi-level caching with fallback"""
        # Check local cache first
        if key in self._local_cache:
            return self._local_cache[key]
        
        # Check Redis cache
        redis_value = await self.redis.get(key)
        if redis_value:
            value = json.loads(redis_value)
            self._local_cache[key] = value  # Cache locally
            return value
        
        # Fallback to original function
        value = await fallback_func()
        
        # Store in both caches
        await asyncio.gather(
            self.redis.setex(key, 3600, json.dumps(value)),  # Redis with TTL
            self._update_local_cache(key, value)  # Local cache
        )
        
        return value
    
    async def _update_local_cache(self, key: str, value: Any) -> None:
        """Update local cache with size limit"""
        if len(self._local_cache) > 1000:  # Simple LRU
            # Remove oldest entries
            oldest_keys = list(self._local_cache.keys())[:100]
            for old_key in oldest_keys:
                del self._local_cache[old_key]
        
        self._local_cache[key] = value
```

### 3. Memory Management
```python
class MemoryOptimizedService:
    def __init__(self):
        self._weak_refs = weakref.WeakValueDictionary()
        self._cleanup_tasks = set()
    
    async def process_large_data(self, data: List[Dict]) -> List[Dict]:
        """Process data in chunks to manage memory"""
        chunk_size = 100
        results = []
        
        for i in range(0, len(data), chunk_size):
            chunk = data[i:i + chunk_size]
            chunk_results = await self._process_chunk(chunk)
            results.extend(chunk_results)
            
            # Force garbage collection after each chunk
            if i % (chunk_size * 10) == 0:
                gc.collect()
        
        return results
    
    async def _process_chunk(self, chunk: List[Dict]) -> List[Dict]:
        """Process a single chunk of data"""
        tasks = [self._process_item(item) for item in chunk]
        return await asyncio.gather(*tasks)
    
    def _schedule_cleanup(self, delay: int = 60):
        """Schedule periodic cleanup"""
        async def cleanup():
            await asyncio.sleep(delay)
            gc.collect()
            # Remove completed tasks
            self._cleanup_tasks = {task for task in self._cleanup_tasks if not task.done()}
        
        task = asyncio.create_task(cleanup())
        self._cleanup_tasks.add(task)
```

## Monitoring and Observability

### 1. Performance Monitoring
```python
class PerformanceMonitor:
    def __init__(self):
        self.metrics = defaultdict(list)
    
    async def monitor_operation(self, operation_name: str, func: Callable, *args, **kwargs):
        """Monitor operation performance"""
        start_time = time.perf_counter()
        start_memory = psutil.Process().memory_info().rss
        
        try:
            result = await func(*args, **kwargs)
            
            end_time = time.perf_counter()
            end_memory = psutil.Process().memory_info().rss
            
            duration = end_time - start_time
            memory_diff = end_memory - start_memory
            
            self.metrics[operation_name].append({
                "duration": duration,
                "memory_change": memory_diff,
                "timestamp": datetime.utcnow(),
                "success": True
            })
            
            logger.info(
                f"Operation completed",
                operation=operation_name,
                duration=duration,
                memory_change=memory_diff
            )
            
            return result
            
        except Exception as e:
            end_time = time.perf_counter()
            duration = end_time - start_time
            
            self.metrics[operation_name].append({
                "duration": duration,
                "timestamp": datetime.utcnow(),
                "success": False,
                "error": str(e)
            })
            
            logger.error(
                f"Operation failed",
                operation=operation_name,
                duration=duration,
                error=str(e)
            )
            
            raise
    
    def get_stats(self, operation_name: str) -> Dict[str, Any]:
        """Get performance statistics"""
        metrics = self.metrics[operation_name]
        if not metrics:
            return {}
        
        durations = [m["duration"] for m in metrics if m["success"]]
        success_rate = sum(1 for m in metrics if m["success"]) / len(metrics)
        
        return {
            "operation": operation_name,
            "total_calls": len(metrics),
            "success_rate": success_rate,
            "avg_duration": sum(durations) / len(durations) if durations else 0,
            "min_duration": min(durations) if durations else 0,
            "max_duration": max(durations) if durations else 0,
            "last_24h": len([m for m in metrics if 
                           datetime.utcnow() - m["timestamp"] < timedelta(hours=24)])
        }
```

### 2. Health Checks
```python
class HealthCheckService:
    def __init__(self, services: Dict[str, BaseService]):
        self.services = services
    
    async def check_all_services(self) -> Dict[str, Any]:
        """Check health of all services"""
        health_checks = {}
        
        check_tasks = {
            name: service.health_check() 
            for name, service in self.services.items()
        }
        
        results = await asyncio.gather(
            *check_tasks.values(), 
            return_exceptions=True
        )
        
        for (name, _), result in zip(check_tasks.items(), results):
            if isinstance(result, Exception):
                health_checks[name] = {
                    "status": "unhealthy",
                    "error": str(result)
                }
            else:
                health_checks[name] = result
        
        overall_status = "healthy" if all(
            check.get("status") == "healthy" 
            for check in health_checks.values()
        ) else "unhealthy"
        
        return {
            "overall_status": overall_status,
            "services": health_checks,
            "timestamp": datetime.utcnow().isoformat()
        }
```

## Best Practices Summary

### DO ✅
1. **Use async/await consistently** across all service methods
2. **Implement proper error handling** with service-specific exceptions
3. **Use dependency injection** for all service dependencies
4. **Write comprehensive async tests** with proper mocking
5. **Monitor performance** with structured logging and metrics
6. **Use connection pooling** for database and HTTP connections
7. **Implement circuit breakers** for external service calls
8. **Use context managers** for resource management
9. **Execute independent operations concurrently** with asyncio.gather()
10. **Implement proper cleanup** in service lifecycle methods

### DON'T ❌
1. **Mix sync and async code** - stick to async throughout
2. **Block the event loop** with synchronous operations
3. **Ignore error handling** - always handle and log errors properly
4. **Create services without dependency injection** - use the DI pattern
5. **Write tests without async fixtures** - use pytest-asyncio
6. **Skip resource cleanup** - always implement cleanup methods
7. **Use global state** - inject dependencies instead
8. **Make direct database calls from routes** - use service layer
9. **Ignore performance monitoring** - track all important operations
10. **Create services without health checks** - implement health monitoring

### Performance Guidelines
- **Target response times**: < 100ms for cache operations, < 500ms for database operations
- **Concurrency**: Services should handle 100+ concurrent requests
- **Memory usage**: Monitor and limit memory growth
- **Connection limits**: Use appropriate pool sizes for databases and HTTP clients
- **Timeouts**: Set reasonable timeouts for all external operations

### Security Guidelines
- **Input validation**: Validate all inputs at service boundaries
- **Error information**: Don't leak sensitive data in error messages
- **Authentication**: Handle authentication at service level when needed
- **Rate limiting**: Implement rate limiting for external API calls
- **Logging**: Never log sensitive data like API keys or passwords

This async architecture provides the foundation for a scalable, maintainable, and high-performance AI backend system.
