"""
Test configuration and fixtures for memory system tests.
Enhanced with async testing patterns and service layer fixtures.
"""

import pytest
import pytest_asyncio
import asyncio
import httpx
import time
from typing import Dict, Any, Optional, List
from unittest.mock import AsyncMock, MagicMock

# Import our services for testing
from services.chat_service import ChatService
from services.redis_service import RedisService
from services.vector_service import VectorService
from models.models import ChatRequest, ChatResponse

# Test configuration
TEST_CONFIG = {
    "backend_url": "http://localhost:3000",
    "memory_api_url": "http://localhost:8001",
    "pipelines_url": "http://localhost:9099",
    "test_user_id": "test_user_memory_system",
    "test_timeout": 30,
}

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
async def http_client():
    """Provide an async HTTP client for tests."""
    async with httpx.AsyncClient(timeout=TEST_CONFIG["test_timeout"]) as client:
        yield client

# New service layer test fixtures
@pytest_asyncio.fixture
async def mock_redis_client():
    """Mock Redis client for testing."""
    mock_client = AsyncMock()
    mock_client.get.return_value = None
    mock_client.set.return_value = True
    mock_client.delete.return_value = 1
    mock_client.exists.return_value = True
    mock_client.ping.return_value = True
    mock_client.info.return_value = {
        "used_memory_human": "1M",
        "connected_clients": 1,
        "total_commands_processed": 100,
        "uptime_in_seconds": 3600
    }
    return mock_client

@pytest_asyncio.fixture
async def mock_vector_client():
    """Mock ChromaDB client for testing."""
    mock_client = MagicMock()
    mock_collection = MagicMock()
    
    # Mock collection methods
    mock_collection.add.return_value = None
    mock_collection.query.return_value = {
        "documents": [["Test document"]],
        "distances": [[0.5]],
        "metadatas": [[{"type": "test"}]],
        "ids": [["test_id"]]
    }
    mock_collection.count.return_value = 1
    
    # Mock client methods
    mock_client.get_collection.return_value = mock_collection
    mock_client.get_or_create_collection.return_value = mock_collection
    mock_client.create_collection.return_value = mock_collection
    mock_client.list_collections.return_value = [mock_collection]
    
    return mock_client

@pytest_asyncio.fixture
async def mock_cache_service():
    """Mock cache service for testing."""
    mock_service = MagicMock()
    mock_service.get.return_value = None
    mock_service.set.return_value = True
    mock_service.get_stats.return_value = {
        "size": 10,
        "max_size": 1000,
        "hit_count": 5,
        "miss_count": 5,
        "total_requests": 10,
        "hit_rate": "50.0%",
        "hit_rate_numeric": 0.5
    }
    return mock_service

@pytest_asyncio.fixture
async def mock_memory_service():
    """Mock memory service for testing."""
    mock_service = AsyncMock()
    mock_service.store_conversation_memory.return_value = True
    mock_service.get_relevant_memories.return_value = []
    return mock_service

@pytest_asyncio.fixture
async def redis_service(mock_redis_client):
    """Create RedisService instance with mocked client."""
    return RedisService(redis_client=mock_redis_client)

@pytest_asyncio.fixture
async def vector_service(mock_vector_client):
    """Create VectorService instance with mocked client."""
    return VectorService(chroma_client=mock_vector_client)

@pytest_asyncio.fixture
async def chat_service(mock_cache_service, mock_memory_service, mock_redis_client):
    """Create ChatService instance with mocked dependencies."""
    # Mock database manager
    mock_db_manager = MagicMock()
    mock_db_manager.redis_client = mock_redis_client
    
    return ChatService(
        cache_service=mock_cache_service,
        memory_service=mock_memory_service,
        database_manager=mock_db_manager
    )

@pytest.fixture
def sample_chat_request():
    """Sample chat request for testing."""
    return ChatRequest(
        user_id="test_user_123",
        message="Hello, how are you?"
    )

@pytest.fixture
def sample_chat_response():
    """Sample chat response for testing."""
    return ChatResponse(
        response="I'm doing well, thank you for asking!"
    )

# Test utility classes
class AsyncTestCase:
    """Base class for async test cases with common utilities."""
    
    @staticmethod
    async def wait_for_condition(condition_func, timeout=5.0, interval=0.1):
        """Wait for a condition to become true with timeout."""
        end_time = asyncio.get_event_loop().time() + timeout
        while asyncio.get_event_loop().time() < end_time:
            if await condition_func() if asyncio.iscoroutinefunction(condition_func) else condition_func():
                return True
            await asyncio.sleep(interval)
        return False
    
    @staticmethod
    async def simulate_delay(seconds=0.1):
        """Simulate async delay for testing."""
        await asyncio.sleep(seconds)
    
    @staticmethod
    def assert_chat_response_valid(response: ChatResponse):
        """Assert that a chat response is valid."""
        assert isinstance(response, ChatResponse)
        assert response.response is not None
        assert isinstance(response.response, str)
        assert len(response.response.strip()) > 0

@pytest.fixture
def test_user_id():
    """Provide a unique test user ID."""
    return f"{TEST_CONFIG['test_user_id']}_{int(time.time())}"

@pytest.fixture
def test_config():
    """Provide test configuration."""
    return TEST_CONFIG.copy()

@pytest.fixture
async def cleanup_test_data(http_client, test_user_id):
    """Clean up test data after each test."""
    yield
    
    # Cleanup after test
    try:
        # Clean up any test memories
        await http_client.delete(
            f"{TEST_CONFIG['memory_api_url']}/memories/user/{test_user_id}"
        )
    except Exception:
        pass  # Ignore cleanup errors

class TestHelper:
    """Helper class for common test operations."""
    
    @staticmethod
    async def wait_for_service(client: httpx.AsyncClient, url: str, timeout: int = 30) -> bool:
        """Wait for a service to be available."""
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = await client.get(url)
                if response.status_code == 200:
                    return True
            except Exception:
                pass
            await asyncio.sleep(1)
        return False
    
    @staticmethod
    async def store_memory_via_learning(
        client: httpx.AsyncClient, 
        user_id: str, 
        content: str,
        conversation_id: Optional[str] = None,
        assistant_response: Optional[str] = None
    ) -> Dict[str, Any]:
        """Store memory via the learning interaction endpoint."""
        learning_data = {
            "user_id": user_id,
            "conversation_id": conversation_id or f"test_conv_{int(time.time())}",
            "user_message": content,
            "assistant_response": assistant_response or "I understand.",
            "response_time": 1.0,
            "source": "test"
        }
        
        response = await client.post(
            f"{TEST_CONFIG['memory_api_url']}/api/learning/process_interaction",
            json=learning_data
        )
        response.raise_for_status()
        return response.json()
    
    @staticmethod
    async def retrieve_memories(
        client: httpx.AsyncClient,
        user_id: str,
        query: str,
        limit: int = 5,
        threshold: float = 0.001
    ) -> Dict[str, Any]:
        """Retrieve memories for a user."""
        retrieve_data = {
            "user_id": user_id,
            "query": query,
            "limit": limit,
            "threshold": threshold
        }
        
        response = await client.post(
            f"{TEST_CONFIG['memory_api_url']}/api/memory/retrieve",
            json=retrieve_data
        )
        response.raise_for_status()
        return response.json()
