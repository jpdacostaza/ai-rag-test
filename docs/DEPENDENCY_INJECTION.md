# Dependency Injection Documentation

## Overview

The AI backend uses FastAPI's dependency injection system to provide clean separation of concerns, improve testability, and enable flexible service configuration. All services are provided through dependency injection rather than global imports.

## Core Concepts

### 1. Service Dependencies
Services are created and managed through dependency functions that handle initialization, configuration, and lifecycle management.

### 2. Dependency Graph
The dependency graph ensures proper initialization order and prevents circular dependencies:

```
Application Startup
├── Configuration (Settings)
├── Database Manager
├── Redis Service
├── Core Services
│   ├── Cache Service (depends on Redis)
│   ├── Vector Service (depends on Database)
│   ├── Memory Service (depends on Database, Vector)
│   └── LLM Service (independent)
└── High-Level Services
    └── Chat Service (depends on LLM, Memory, Cache)
```

### 3. Scope Management
- **Singleton**: Services are created once and reused across requests
- **Request-scoped**: Some dependencies are created per request (e.g., database sessions)
- **Application-scoped**: Configuration and connection pools live for the application lifetime

## Service Dependencies Implementation

### 1. Core Dependencies (`services/dependencies.py`)

```python
from functools import lru_cache
from typing import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from config.settings import Settings
from core.database import DatabaseManager
from services.redis_service import RedisService
from services.cache_service import CacheService
from services.vector_service import VectorService
from services.memory_service import MemoryService
from services.llm_service import LLMService
from services.chat_service import ChatService

# Configuration dependency (singleton)
@lru_cache()
def get_settings() -> Settings:
    """Get application settings (cached singleton)"""
    return Settings()

# Database dependencies
@lru_cache()
def get_database_manager(settings: Settings = Depends(get_settings)) -> DatabaseManager:
    """Get database manager (singleton)"""
    return DatabaseManager(settings.database_url)

async def get_database_session(
    db_manager: DatabaseManager = Depends(get_database_manager)
) -> AsyncGenerator[AsyncSession, None]:
    """Get database session (request-scoped)"""
    async with db_manager.get_session() as session:
        try:
            yield session
        finally:
            await session.close()

# Redis service dependency
@lru_cache()
def get_redis_service(settings: Settings = Depends(get_settings)) -> RedisService:
    """Get Redis service (singleton)"""
    return RedisService(settings)

# Core service dependencies
@lru_cache()
def get_cache_service(
    redis_service: RedisService = Depends(get_redis_service)
) -> CacheService:
    """Get cache service (singleton)"""
    return CacheService(redis_service)

@lru_cache()
def get_vector_service(
    settings: Settings = Depends(get_settings),
    db_manager: DatabaseManager = Depends(get_database_manager)
) -> VectorService:
    """Get vector service (singleton)"""
    return VectorService(settings, db_manager)

@lru_cache()
def get_memory_service(
    settings: Settings = Depends(get_settings),
    db_manager: DatabaseManager = Depends(get_database_manager),
    vector_service: VectorService = Depends(get_vector_service)
) -> MemoryService:
    """Get memory service (singleton)"""
    return MemoryService(settings, db_manager, vector_service)

@lru_cache()
def get_llm_service(settings: Settings = Depends(get_settings)) -> LLMService:
    """Get LLM service (singleton)"""
    return LLMService(settings)

# High-level service dependencies
@lru_cache()
def get_chat_service(
    llm_service: LLMService = Depends(get_llm_service),
    memory_service: MemoryService = Depends(get_memory_service),
    cache_service: CacheService = Depends(get_cache_service),
    redis_service: RedisService = Depends(get_redis_service)
) -> ChatService:
    """Get chat service (singleton)"""
    return ChatService(llm_service, memory_service, cache_service, redis_service)

# Health check dependencies
def get_health_services(
    redis_service: RedisService = Depends(get_redis_service),
    vector_service: VectorService = Depends(get_vector_service),
    memory_service: MemoryService = Depends(get_memory_service),
    llm_service: LLMService = Depends(get_llm_service)
) -> Dict[str, BaseService]:
    """Get all services for health checking"""
    return {
        "redis": redis_service,
        "vector": vector_service,
        "memory": memory_service,
        "llm": llm_service
    }
```

### 2. Route Usage Pattern

```python
# routes/chat.py
from fastapi import APIRouter, Depends, HTTPException
from services.chat_service import ChatService
from services.dependencies import get_chat_service
from models.requests import ChatRequest
from models.responses import ChatResponse

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])

@router.post("/", response_model=ChatResponse)
async def chat_endpoint(
    request: ChatRequest,
    chat_service: ChatService = Depends(get_chat_service)
) -> ChatResponse:
    """Process chat request using injected chat service"""
    try:
        return await chat_service.process_chat_request(request)
    except ChatServiceError as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/stream")
async def chat_stream_endpoint(
    request: ChatRequest,
    chat_service: ChatService = Depends(get_chat_service)
):
    """Stream chat responses using injected chat service"""
    try:
        async for chunk in chat_service.process_chat_stream(request):
            yield f"data: {chunk}\n\n"
    except ChatServiceError as e:
        yield f"event: error\ndata: {str(e)}\n\n"

@router.get("/history/{user_id}")
async def get_chat_history(
    user_id: str,
    memory_service: MemoryService = Depends(get_memory_service)
) -> List[ConversationMemory]:
    """Get chat history using injected memory service"""
    try:
        return await memory_service.get_user_conversations(user_id)
    except MemoryServiceError as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### 3. Health Check Route

```python
# routes/health.py
from fastapi import APIRouter, Depends
from services.dependencies import get_health_services
from typing import Dict, Any

router = APIRouter(prefix="/health", tags=["health"])

@router.get("/")
async def health_check(
    services: Dict[str, BaseService] = Depends(get_health_services)
) -> Dict[str, Any]:
    """Check health of all services"""
    health_results = {}
    
    for service_name, service in services.items():
        try:
            health_results[service_name] = await service.health_check()
        except Exception as e:
            health_results[service_name] = {
                "status": "unhealthy",
                "error": str(e)
            }
    
    overall_healthy = all(
        result.get("status") == "healthy" 
        for result in health_results.values()
    )
    
    return {
        "status": "healthy" if overall_healthy else "unhealthy",
        "services": health_results,
        "timestamp": datetime.utcnow().isoformat()
    }
```

## Advanced Dependency Patterns

### 1. Conditional Dependencies

```python
def get_llm_service_by_provider(
    provider: str,
    settings: Settings = Depends(get_settings)
) -> LLMService:
    """Get LLM service based on provider"""
    if provider == "openai":
        return OpenAILLMService(settings)
    elif provider == "ollama":
        return OllamaLLMService(settings)
    else:
        raise ValueError(f"Unknown LLM provider: {provider}")

@router.post("/chat/{provider}")
async def chat_with_provider(
    provider: str,
    request: ChatRequest,
    llm_service: LLMService = Depends(get_llm_service_by_provider)
):
    """Chat with specific LLM provider"""
    return await llm_service.process_request(request)
```

### 2. Request-Scoped Dependencies

```python
async def get_request_context(request: Request) -> RequestContext:
    """Create request-specific context"""
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    user_id = request.headers.get("X-User-ID")
    
    return RequestContext(
        correlation_id=correlation_id,
        user_id=user_id,
        timestamp=datetime.utcnow(),
        request_id=str(uuid.uuid4())
    )

@router.post("/chat")
async def chat_endpoint(
    request: ChatRequest,
    context: RequestContext = Depends(get_request_context),
    chat_service: ChatService = Depends(get_chat_service)
):
    """Chat with request context"""
    return await chat_service.process_chat_request(request, context)
```

### 3. Dependency Override for Testing

```python
# tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock

from main import app
from services.dependencies import get_chat_service, get_llm_service

@pytest.fixture
def mock_llm_service():
    """Mock LLM service for testing"""
    mock = AsyncMock(spec=LLMService)
    mock.call_llm.return_value = "Mock response"
    return mock

@pytest.fixture
def mock_chat_service(mock_llm_service):
    """Mock chat service with dependencies"""
    mock = AsyncMock(spec=ChatService)
    mock.llm_service = mock_llm_service
    return mock

@pytest.fixture
def test_client(mock_chat_service):
    """Test client with mocked dependencies"""
    app.dependency_overrides[get_chat_service] = lambda: mock_chat_service
    app.dependency_overrides[get_llm_service] = lambda: mock_chat_service.llm_service
    
    with TestClient(app) as client:
        yield client
    
    # Cleanup overrides
    app.dependency_overrides.clear()

# Test usage
def test_chat_endpoint(test_client, mock_chat_service):
    response = test_client.post("/api/v1/chat/", json={
        "message": "Hello",
        "user_id": "test_user"
    })
    
    assert response.status_code == 200
    mock_chat_service.process_chat_request.assert_called_once()
```

### 4. Dependency Caching and Lifecycle

```python
class ServiceLifecycleManager:
    """Manages service lifecycle and cleanup"""
    
    def __init__(self):
        self._services: Dict[str, BaseService] = {}
        self._initialized = False
    
    async def initialize_services(self):
        """Initialize all services in dependency order"""
        if self._initialized:
            return
        
        # Initialize services in dependency order
        services_config = [
            ("settings", get_settings),
            ("database", get_database_manager),
            ("redis", get_redis_service),
            ("cache", get_cache_service),
            ("vector", get_vector_service),
            ("memory", get_memory_service),
            ("llm", get_llm_service),
            ("chat", get_chat_service)
        ]
        
        for service_name, service_factory in services_config:
            try:
                service = service_factory()
                if hasattr(service, 'initialize'):
                    await service.initialize()
                self._services[service_name] = service
                logger.info(f"Initialized {service_name} service")
            except Exception as e:
                logger.error(f"Failed to initialize {service_name}: {e}")
                raise
        
        self._initialized = True
        logger.info("All services initialized successfully")
    
    async def cleanup_services(self):
        """Cleanup all services in reverse dependency order"""
        if not self._initialized:
            return
        
        # Cleanup in reverse order
        for service_name in reversed(list(self._services.keys())):
            service = self._services[service_name]
            try:
                if hasattr(service, 'cleanup'):
                    await service.cleanup()
                logger.info(f"Cleaned up {service_name} service")
            except Exception as e:
                logger.error(f"Failed to cleanup {service_name}: {e}")
        
        self._services.clear()
        self._initialized = False
        logger.info("All services cleaned up")

# Application startup/shutdown
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    await service_manager.initialize_services()

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup services on shutdown"""
    await service_manager.cleanup_services()
```

## Service Factory Pattern

### 1. Abstract Service Factory

```python
from abc import ABC, abstractmethod

class ServiceFactory(ABC):
    """Abstract factory for creating services"""
    
    @abstractmethod
    async def create_service(self, settings: Settings) -> BaseService:
        """Create service instance"""
        pass
    
    @abstractmethod
    def get_service_name(self) -> str:
        """Get service name for registration"""
        pass

class LLMServiceFactory(ServiceFactory):
    """Factory for creating LLM services"""
    
    async def create_service(self, settings: Settings) -> LLMService:
        service = LLMService(settings)
        await service.initialize()
        return service
    
    def get_service_name(self) -> str:
        return "llm"

class ServiceRegistry:
    """Registry for managing service factories"""
    
    def __init__(self):
        self._factories: Dict[str, ServiceFactory] = {}
        self._services: Dict[str, BaseService] = {}
    
    def register_factory(self, factory: ServiceFactory):
        """Register a service factory"""
        service_name = factory.get_service_name()
        self._factories[service_name] = factory
    
    async def get_service(self, service_name: str, settings: Settings) -> BaseService:
        """Get or create service instance"""
        if service_name not in self._services:
            if service_name not in self._factories:
                raise ValueError(f"No factory registered for service: {service_name}")
            
            factory = self._factories[service_name]
            service = await factory.create_service(settings)
            self._services[service_name] = service
        
        return self._services[service_name]

# Usage with dependency injection
service_registry = ServiceRegistry()
service_registry.register_factory(LLMServiceFactory())

async def get_service_from_registry(
    service_name: str,
    settings: Settings = Depends(get_settings)
) -> BaseService:
    """Get service from registry"""
    return await service_registry.get_service(service_name, settings)
```

### 2. Environment-Specific Services

```python
def get_environment_specific_service(
    service_type: str,
    settings: Settings = Depends(get_settings)
) -> BaseService:
    """Get service based on environment configuration"""
    
    if settings.environment == "test":
        # Return mock services for testing
        return get_mock_service(service_type)
    elif settings.environment == "development":
        # Return development services with debug logging
        return get_development_service(service_type, settings)
    elif settings.environment == "production":
        # Return production services with full monitoring
        return get_production_service(service_type, settings)
    else:
        raise ValueError(f"Unknown environment: {settings.environment}")

# Configuration-based service selection
def get_llm_service_configured(
    settings: Settings = Depends(get_settings)
) -> LLMService:
    """Get LLM service based on configuration"""
    
    if settings.llm_provider == "openai":
        return OpenAILLMService(settings)
    elif settings.llm_provider == "anthropic":
        return AnthropicLLMService(settings)
    elif settings.llm_provider == "ollama":
        return OllamaLLMService(settings)
    else:
        # Default fallback
        return OpenAILLMService(settings)
```

## Testing with Dependency Injection

### 1. Service Mocking

```python
# tests/tests/test_dependencies.py
import pytest
from unittest.mock import AsyncMock, Mock
from fastapi import FastAPI
from fastapi.testclient import TestClient

from services.dependencies import get_chat_service, get_llm_service
from services.chat_service import ChatService
from services.llm_service import LLMService

@pytest.fixture
def mock_services():
    """Create all mock services"""
    return {
        "llm": AsyncMock(spec=LLMService),
        "memory": AsyncMock(spec=MemoryService),
        "cache": AsyncMock(spec=CacheService),
        "redis": AsyncMock(spec=RedisService)
    }

@pytest.fixture
def test_app(mock_services):
    """Create test app with mocked dependencies"""
    app = FastAPI()
    
    # Override dependencies with mocks
    app.dependency_overrides[get_llm_service] = lambda: mock_services["llm"]
    app.dependency_overrides[get_memory_service] = lambda: mock_services["memory"]
    app.dependency_overrides[get_cache_service] = lambda: mock_services["cache"]
    app.dependency_overrides[get_redis_service] = lambda: mock_services["redis"]
    
    # Create chat service with mocked dependencies
    def override_chat_service():
        return ChatService(
            llm_service=mock_services["llm"],
            memory_service=mock_services["memory"],
            cache_service=mock_services["cache"],
            redis_service=mock_services["redis"]
        )
    
    app.dependency_overrides[get_chat_service] = override_chat_service
    
    # Include routes
    from routes.chat import router
    app.include_router(router)
    
    yield app
    
    # Cleanup
    app.dependency_overrides.clear()

def test_dependency_injection(test_app, mock_services):
    """Test that dependencies are properly injected"""
    with TestClient(test_app) as client:
        # Configure mock behavior
        mock_services["llm"].call_llm.return_value = "Test response"
        mock_services["cache"].get_cached_response.return_value = None
        
        # Make request
        response = client.post("/api/v1/chat/", json={
            "message": "Hello",
            "user_id": "test_user"
        })
        
        # Verify dependencies were used
        assert response.status_code == 200
        mock_services["llm"].call_llm.assert_called()
        mock_services["cache"].get_cached_response.assert_called()
```

### 2. Integration Testing

```python
@pytest.fixture(scope="session")
async def test_services():
    """Create real services for integration testing"""
    settings = Settings(
        redis_host="localhost",
        redis_port=6380,  # Test Redis
        database_url="sqlite:///test.db",
        llm_provider="mock"  # Use mock LLM for testing
    )
    
    # Create services with test configuration
    redis_service = RedisService(settings)
    memory_service = MemoryService(settings, redis_service)
    llm_service = MockLLMService(settings)  # Test implementation
    chat_service = ChatService(llm_service, memory_service)
    
    # Initialize services
    await redis_service.initialize()
    await memory_service.initialize()
    await llm_service.initialize()
    await chat_service.initialize()
    
    yield {
        "redis": redis_service,
        "memory": memory_service,
        "llm": llm_service,
        "chat": chat_service
    }
    
    # Cleanup
    await chat_service.cleanup()
    await llm_service.cleanup()
    await memory_service.cleanup()
    await redis_service.cleanup()

@pytest.mark.asyncio
async def test_service_integration(test_services):
    """Test service integration with real dependencies"""
    chat_service = test_services["chat"]
    
    request = ChatRequest(
        message="Hello, world!",
        user_id="test_user"
    )
    
    # Test real service interaction
    response = await chat_service.process_chat_request(request)
    
    assert response.message is not None
    assert response.user_id == "test_user"
    
    # Verify data was stored
    memories = await test_services["memory"].get_memories("test_user")
    assert len(memories) > 0
```

## Performance Considerations

### 1. Dependency Caching
- Use `@lru_cache()` for singleton services
- Avoid creating services multiple times
- Cache expensive initialization operations

### 2. Lazy Loading
```python
class LazyServiceProvider:
    def __init__(self, factory: Callable[[], BaseService]):
        self._factory = factory
        self._service: Optional[BaseService] = None
    
    def get_service(self) -> BaseService:
        if self._service is None:
            self._service = self._factory()
        return self._service

def get_lazy_llm_service() -> LazyServiceProvider:
    return LazyServiceProvider(lambda: LLMService(get_settings()))
```

### 3. Connection Pooling
```python
@lru_cache()
def get_database_pool(settings: Settings = Depends(get_settings)):
    """Get shared database connection pool"""
    return create_engine(
        settings.database_url,
        pool_size=20,
        max_overflow=30,
        pool_pre_ping=True
    )
```

## Best Practices

### DO ✅
1. **Use @lru_cache()** for singleton services
2. **Define clear dependency graphs** to avoid circular dependencies
3. **Override dependencies in tests** for proper isolation
4. **Initialize services properly** with async setup methods
5. **Cleanup resources** in service lifecycle methods
6. **Use type hints** for all dependency functions
7. **Handle dependency failures** gracefully
8. **Document service dependencies** clearly

### DON'T ❌
1. **Create circular dependencies** between services
2. **Use global state** instead of dependency injection
3. **Initialize services in route handlers** - use dependencies
4. **Forget to cleanup resources** in test overrides
5. **Mix singleton and request-scoped** dependencies incorrectly
6. **Create dependencies without proper error handling**
7. **Skip dependency caching** for expensive services
8. **Use mutable default arguments** in dependency functions

This dependency injection system provides clean separation of concerns, excellent testability, and flexible service configuration for the AI backend.
