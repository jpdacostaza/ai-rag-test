"""
Test Suite for Async Context Managers
=====================================

Comprehensive tests for the async context managers including HTTP client management,
database connections, and resource cleanup patterns.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch, Mock
import httpx
from contextlib import asynccontextmanager

from utilities.async_context_managers import (
    HTTPClientManager,
    DatabaseConnectionManager,
    safe_http_request,
    redis_connection,
    vector_connection
)
from tests.conftest import AsyncTestCase


@pytest.mark.asyncio
@pytest.mark.infrastructure
class TestHTTPClientManager(AsyncTestCase):
    """Test suite for HTTPClientManager."""
    
    async def test_http_client_creation(self):
        """Test that HTTP client is created properly."""
        async with HTTPClientManager() as client:
            assert isinstance(client, httpx.AsyncClient)
            assert client.is_closed is False
    
    async def test_http_client_cleanup(self):
        """Test that HTTP client is properly cleaned up."""
        manager = HTTPClientManager()
        client = await manager.__aenter__()
        
        # Client should be open
        assert client.is_closed is False
        
        # Close the client
        await manager.__aexit__(None, None, None)
        
        # Client should be closed
        assert client.is_closed is True
    
    async def test_http_client_with_custom_timeout(self):
        """Test HTTP client with custom timeout."""
        timeout = 30.0
        async with HTTPClientManager(timeout=timeout) as client:
            assert client.timeout.read == timeout
    
    async def test_http_client_with_custom_limits(self):
        """Test HTTP client with custom connection limits."""
        limits = httpx.Limits(max_keepalive_connections=10, max_connections=20)
        async with HTTPClientManager(limits=limits) as client:
            assert client._limits.max_keepalive_connections == 10
            assert client._limits.max_connections == 20
    
    async def test_http_client_error_handling_in_context(self):
        """Test error handling within HTTP client context."""
        async with HTTPClientManager() as client:
            # Should handle exceptions gracefully
            try:
                # Simulate an error
                raise ValueError("Test error")
            except ValueError:
                pass
        
        # Client should still be properly closed
        assert client.is_closed is True
    
    async def test_concurrent_http_clients(self):
        """Test multiple concurrent HTTP client contexts."""
        async def create_client():
            async with HTTPClientManager() as client:
                return client.is_closed
        
        # Create multiple clients concurrently
        tasks = [create_client() for _ in range(5)]
        results = await asyncio.gather(*tasks)
        
        # All clients should have been properly managed
        assert all(result is False for result in results)


@pytest.mark.asyncio
@pytest.mark.infrastructure
class TestDatabaseConnectionManager(AsyncTestCase):
    """Test suite for DatabaseConnectionManager."""
    
    async def test_database_connection_creation(self):
        """Test database connection creation."""
        with patch('asyncpg.connect') as mock_connect:
            mock_conn = AsyncMock()
            mock_connect.return_value = mock_conn
            
            async with DatabaseConnectionManager("postgresql://test") as conn:
                assert conn == mock_conn
                mock_connect.assert_called_once_with("postgresql://test")
    
    async def test_database_connection_cleanup(self):
        """Test database connection cleanup."""
        with patch('asyncpg.connect') as mock_connect:
            mock_conn = AsyncMock()
            mock_connect.return_value = mock_conn
            
            manager = DatabaseConnectionManager("postgresql://test")
            conn = await manager.__aenter__()
            
            # Connection should be available
            assert conn == mock_conn
            
            # Close the connection
            await manager.__aexit__(None, None, None)
            
            # Connection close should have been called
            mock_conn.close.assert_called_once()
    
    async def test_database_connection_error_handling(self):
        """Test database connection error handling."""
        with patch('asyncpg.connect') as mock_connect:
            mock_connect.side_effect = Exception("Database connection failed")
            
            with pytest.raises(Exception, match="Database connection failed"):
                async with DatabaseConnectionManager("postgresql://test"):
                    pass
    
    async def test_database_connection_context_error(self):
        """Test error handling within database context."""
        with patch('asyncpg.connect') as mock_connect:
            mock_conn = AsyncMock()
            mock_connect.return_value = mock_conn
            
            try:
                async with DatabaseConnectionManager("postgresql://test") as conn:
                    raise ValueError("Test error in context")
            except ValueError:
                pass
            
            # Connection should still be closed
            mock_conn.close.assert_called_once()


@pytest.mark.asyncio
@pytest.mark.infrastructure
class TestSafeHttpRequest(AsyncTestCase):
    """Test suite for safe_http_request function."""
    
    async def test_successful_http_request(self):
        """Test successful HTTP request."""
        with patch('utilities.async_context_managers.HTTPClientManager') as mock_manager:
            mock_client = AsyncMock()
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"status": "success"}
            mock_client.get.return_value = mock_response
            
            mock_manager.return_value.__aenter__.return_value = mock_client
            mock_manager.return_value.__aexit__.return_value = None
            
            result = await safe_http_request("GET", "https://example.com")
            
            assert result == {"status": "success"}
            mock_client.get.assert_called_once_with("https://example.com")
    
    async def test_http_request_with_data(self):
        """Test HTTP request with POST data."""
        with patch('utilities.async_context_managers.HTTPClientManager') as mock_manager:
            mock_client = AsyncMock()
            mock_response = Mock()
            mock_response.status_code = 201
            mock_response.json.return_value = {"created": True}
            mock_client.post.return_value = mock_response
            
            mock_manager.return_value.__aenter__.return_value = mock_client
            mock_manager.return_value.__aexit__.return_value = None
            
            data = {"name": "test"}
            result = await safe_http_request("POST", "https://example.com", json=data)
            
            assert result == {"created": True}
            mock_client.post.assert_called_once_with("https://example.com", json=data)
    
    async def test_http_request_error_handling(self):
        """Test HTTP request error handling."""
        with patch('utilities.async_context_managers.HTTPClientManager') as mock_manager:
            mock_client = AsyncMock()
            mock_client.get.side_effect = httpx.RequestError("Network error")
            
            mock_manager.return_value.__aenter__.return_value = mock_client
            mock_manager.return_value.__aexit__.return_value = None
            
            result = await safe_http_request("GET", "https://example.com")
            
            assert result is None
    
    async def test_http_request_timeout(self):
        """Test HTTP request timeout handling."""
        with patch('utilities.async_context_managers.HTTPClientManager') as mock_manager:
            mock_client = AsyncMock()
            mock_client.get.side_effect = httpx.TimeoutException("Request timeout")
            
            mock_manager.return_value.__aenter__.return_value = mock_client
            mock_manager.return_value.__aexit__.return_value = None
            
            result = await safe_http_request("GET", "https://example.com")
            
            assert result is None
    
    async def test_http_request_non_200_status(self):
        """Test HTTP request with non-200 status code."""
        with patch('utilities.async_context_managers.HTTPClientManager') as mock_manager:
            mock_client = AsyncMock()
            mock_response = Mock()
            mock_response.status_code = 404
            mock_response.json.return_value = {"error": "Not found"}
            mock_client.get.return_value = mock_response
            
            mock_manager.return_value.__aenter__.return_value = mock_client
            mock_manager.return_value.__aexit__.return_value = None
            
            result = await safe_http_request("GET", "https://example.com")
            
            assert result is None


@pytest.mark.asyncio
@pytest.mark.infrastructure
class TestRedisConnection(AsyncTestCase):
    """Test suite for redis_connection function."""
    
    async def test_redis_connection_success(self, mock_redis_client):
        """Test successful Redis connection."""
        with patch('redis.asyncio.Redis') as mock_redis:
            mock_redis.return_value = mock_redis_client
            
            async with redis_connection() as redis:
                assert redis == mock_redis_client
                redis.ping.assert_called_once()
    
    async def test_redis_connection_failure(self):
        """Test Redis connection failure."""
        with patch('redis.asyncio.Redis') as mock_redis:
            mock_client = AsyncMock()
            mock_client.ping.side_effect = Exception("Redis connection failed")
            mock_redis.return_value = mock_client
            
            with pytest.raises(Exception, match="Redis connection failed"):
                async with redis_connection():
                    pass
    
    async def test_redis_connection_cleanup(self, mock_redis_client):
        """Test Redis connection cleanup."""
        with patch('redis.asyncio.Redis') as mock_redis:
            mock_redis.return_value = mock_redis_client
            
            async with redis_connection() as redis:
                assert redis == mock_redis_client
            
            # Close should be called on exit
            mock_redis_client.close.assert_called_once()


@pytest.mark.asyncio
@pytest.mark.infrastructure
class TestVectorConnection(AsyncTestCase):
    """Test suite for vector_connection function."""
    
    async def test_vector_connection_success(self, mock_vector_client):
        """Test successful vector database connection."""
        with patch('utilities.async_context_managers.get_vector_client') as mock_get_client:
            mock_get_client.return_value = mock_vector_client
            
            async with vector_connection() as client:
                assert client == mock_vector_client
    
    async def test_vector_connection_failure(self):
        """Test vector database connection failure."""
        with patch('utilities.async_context_managers.get_vector_client') as mock_get_client:
            mock_get_client.side_effect = Exception("Vector DB connection failed")
            
            with pytest.raises(Exception, match="Vector DB connection failed"):
                async with vector_connection():
                    pass
    
    async def test_vector_connection_cleanup(self, mock_vector_client):
        """Test vector database connection cleanup."""
        with patch('utilities.async_context_managers.get_vector_client') as mock_get_client:
            mock_get_client.return_value = mock_vector_client
            
            async with vector_connection() as client:
                assert client == mock_vector_client
            
            # Close should be called if available
            if hasattr(mock_vector_client, 'close'):
                mock_vector_client.close.assert_called_once()


@pytest.mark.asyncio
@pytest.mark.performance
class TestAsyncContextManagerPerformance:
    """Performance tests for async context managers."""
    
    async def test_concurrent_http_connections(self):
        """Test performance of concurrent HTTP connections."""
        import time
        
        async def make_request():
            async with HTTPClientManager() as client:
                # Simulate work
                await asyncio.sleep(0.1)
                return True
        
        start_time = time.time()
        
        # Create 10 concurrent connections
        tasks = [make_request() for _ in range(10)]
        results = await asyncio.gather(*tasks)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should complete concurrently (not sequentially)
        assert duration < 1.0, f"Concurrent connections took too long: {duration}s"
        assert all(results)
    
    async def test_context_manager_overhead(self):
        """Test overhead of context manager creation."""
        import time
        
        start_time = time.time()
        
        # Create many context managers
        for _ in range(100):
            async with HTTPClientManager() as client:
                pass
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should not have excessive overhead
        assert duration < 5.0, f"Context manager overhead too high: {duration}s"


@pytest.mark.asyncio
@pytest.mark.error_handling
class TestAsyncContextManagerErrorRecovery:
    """Test error recovery patterns in async context managers."""
    
    async def test_resource_cleanup_on_exception(self):
        """Test that resources are cleaned up even when exceptions occur."""
        cleanup_called = False
        
        class TestManager:
            async def __aenter__(self):
                return self
            
            async def __aexit__(self, exc_type, exc_val, exc_tb):
                nonlocal cleanup_called
                cleanup_called = True
        
        try:
            async with TestManager():
                raise ValueError("Test exception")
        except ValueError:
            pass
        
        assert cleanup_called, "Cleanup was not called on exception"
    
    async def test_nested_context_manager_cleanup(self):
        """Test cleanup order in nested context managers."""
        cleanup_order = []
        
        class OrderedManager:
            def __init__(self, name):
                self.name = name
            
            async def __aenter__(self):
                return self
            
            async def __aexit__(self, exc_type, exc_val, exc_tb):
                cleanup_order.append(self.name)
        
        try:
            async with OrderedManager("outer"):
                async with OrderedManager("inner"):
                    raise ValueError("Test exception")
        except ValueError:
            pass
        
        # Inner should be cleaned up before outer
        assert cleanup_order == ["inner", "outer"]
