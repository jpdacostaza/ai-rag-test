"""
Test configuration and fixtures for memory system tests.
"""

import pytest
import asyncio
import httpx
import time
from typing import Dict, Any, Optional, List

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
