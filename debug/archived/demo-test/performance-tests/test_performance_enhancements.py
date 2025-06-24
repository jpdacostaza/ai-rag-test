"""
Performance and Load Testing for Enhanced FastAPI Features
Tests performance impact of new enhancements and validates under load.
"""

import asyncio
import pytest
import time
import concurrent.futures
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
import statistics

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app, STREAM_SESSION_STOP, STREAM_SESSION_METADATA

client = TestClient(app)


class TestPerformanceImpact:
    """Test performance impact of new enhancements."""
    
    def test_middleware_performance_overhead(self):
        """Test middleware doesn't add significant overhead."""
        endpoint = "/health/simple"
        num_requests = 100
        
        # Measure response times
        response_times = []
        for _ in range(num_requests):
            start_time = time.time()
            response = client.get(endpoint)
            end_time = time.time()
            
            assert response.status_code == 200
            response_times.append((end_time - start_time) * 1000)  # Convert to ms
            
        # Calculate statistics
        avg_time = statistics.mean(response_times)
        max_time = max(response_times)
        min_time = min(response_times)
        
        print(f"\nMiddleware Performance Stats:")
        print(f"Average response time: {avg_time:.2f}ms")
        print(f"Min response time: {min_time:.2f}ms") 
        print(f"Max response time: {max_time:.2f}ms")
        
        # Performance assertions (adjust based on your requirements)
        assert avg_time < 50  # Average should be under 50ms
        assert max_time < 200  # Max should be under 200ms
        
    def test_concurrent_request_handling(self):
        """Test handling multiple concurrent requests with enhanced middleware."""
        num_concurrent = 20
        endpoint = "/health/simple"
        
        def make_request():
            response = client.get(endpoint)
            return response.status_code, response.headers.get("X-Request-ID")
            
        # Use ThreadPoolExecutor for concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_concurrent) as executor:
            futures = [executor.submit(make_request) for _ in range(num_concurrent)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
            
        # Verify all requests succeeded
        status_codes = [result[0] for result in results]
        request_ids = [result[1] for result in results]
        
        assert all(code == 200 for code in status_codes)
        assert len(set(request_ids)) == num_concurrent  # All request IDs should be unique
        
    def test_session_cleanup_performance(self):
        """Test performance of session cleanup with many sessions."""
        from main import cleanup_old_sessions
        
        # Create many test sessions
        num_sessions = 1000
        current_time = time.time()
        
        # Clear existing sessions
        STREAM_SESSION_STOP.clear()
        STREAM_SESSION_METADATA.clear()
        
        # Create mix of old and new sessions
        for i in range(num_sessions):
            session_id = f"session_{i}"
            # Make half the sessions old
            created_time = current_time - (7200 if i < num_sessions // 2 else 100)
            
            STREAM_SESSION_STOP[session_id] = False
            STREAM_SESSION_METADATA[session_id] = {
                "created_at": created_time,
                "user_id": f"user_{i}",
                "model": "test_model"
            }
            
        # Measure cleanup performance
        start_time = time.time()
        cleanup_old_sessions(max_age_seconds=3600)
        cleanup_time = (time.time() - start_time) * 1000
        
        print(f"\nSession cleanup performance:")
        print(f"Cleaned up {num_sessions // 2} sessions in {cleanup_time:.2f}ms")
        
        # Should cleanup old sessions efficiently
        assert cleanup_time < 100  # Should complete in under 100ms
        assert len(STREAM_SESSION_METADATA) == num_sessions // 2  # Half should remain


class TestLoadTesting:
    """Load testing for enhanced features."""
    
    @patch('main.call_llm_stream')
    def test_streaming_under_load(self, mock_stream):
        """Test streaming performance under load."""
        # Mock streaming response
        async def mock_generator():
            for i in range(10):
                yield f"token_{i}"
                await asyncio.sleep(0.01)  # Simulate realistic delay
                
        mock_stream.return_value = mock_generator()
        
        num_concurrent_streams = 10
        
        def start_stream():
            response = client.post("/v1/chat/completions", json={
                "messages": [{"role": "user", "content": "test"}],
                "stream": True,
                "user": f"user_{time.time()}",
                "model": "test_model"
            })
            return response.status_code
            
        # Start multiple concurrent streams
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_concurrent_streams) as executor:
            futures = [executor.submit(start_stream) for _ in range(num_concurrent_streams)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
            
        # All streams should start successfully
        assert all(status == 200 for status in results)
        
    def test_error_handler_under_load(self):
        """Test error handlers don't become bottleneck under load."""
        num_requests = 50
        
        def make_error_request():
            # Make request that will trigger validation error
            response = client.post("/chat", json={})
            return response.status_code, response.json()
            
        start_time = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_error_request) for _ in range(num_requests)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
            
        total_time = (time.time() - start_time) * 1000
        
        print(f"\nError handler load test:")
        print(f"Processed {num_requests} error requests in {total_time:.2f}ms")
        print(f"Average: {total_time / num_requests:.2f}ms per request")
        
        # Verify all requests properly handled
        status_codes = [result[0] for result in results]
        responses = [result[1] for result in results]
        
        assert all(code == 422 for code in status_codes)
        assert all("error" in resp for resp in responses)
        assert total_time < 5000  # Should complete in under 5 seconds


class TestMemoryUsage:
    """Test memory usage of enhanced features."""
    
    def test_session_metadata_memory_efficiency(self):
        """Test session metadata doesn't cause memory leaks."""
        import tracemalloc
        from main import cleanup_old_sessions
        
        # Start memory tracing
        tracemalloc.start()
        
        # Create and cleanup sessions multiple times
        for cycle in range(5):
            # Create sessions
            for i in range(100):
                session_id = f"cycle_{cycle}_session_{i}"
                STREAM_SESSION_STOP[session_id] = False
                STREAM_SESSION_METADATA[session_id] = {
                    "created_at": time.time() - 7200,  # Old session
                    "user_id": f"user_{i}",
                    "model": "test_model"
                }
                
            # Cleanup sessions
            cleanup_old_sessions(max_age_seconds=3600)
            
        # Get current memory usage
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        print(f"\nMemory usage after session cycles:")
        print(f"Current: {current / 1024 / 1024:.2f} MB")
        print(f"Peak: {peak / 1024 / 1024:.2f} MB")
        
        # Memory should be reasonable
        assert current / 1024 / 1024 < 50  # Less than 50MB
        assert len(STREAM_SESSION_METADATA) == 0  # All cleaned up


class TestErrorRecovery:
    """Test error recovery and resilience of enhanced features."""
    
    def test_middleware_error_recovery(self):
        """Test middleware handles errors gracefully."""
        # This will trigger the general exception handler
        with patch('main.log_service_status', side_effect=Exception("Logging error")):
            response = client.get("/health/simple")
            
        # Should still work despite logging error
        assert response.status_code == 200
        
    @patch('main.httpx.AsyncClient')
    def test_streaming_error_recovery(self, mock_client_class):
        """Test streaming handles connection errors gracefully."""
        # Mock client that raises error
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client
        mock_client.stream.side_effect = Exception("Connection failed")
        
        response = client.post("/v1/chat/completions", json={
            "messages": [{"role": "user", "content": "test"}],
            "stream": True,
            "user": "test_user"
        })
        
        # Should handle error gracefully
        assert response.status_code == 200
        content = response.content.decode()
        assert "Error:" in content
        
    def test_session_cleanup_error_resilience(self):
        """Test session cleanup is resilient to corrupted data."""
        from main import cleanup_old_sessions
        
        # Add session with corrupted metadata
        STREAM_SESSION_METADATA["corrupted_session"] = {
            "created_at": "invalid_timestamp",  # Invalid data
            "user_id": "test_user"
        }
        
        # Add valid session
        STREAM_SESSION_METADATA["valid_session"] = {
            "created_at": time.time() - 7200,
            "user_id": "test_user"
        }
        
        # Cleanup should handle corrupted data gracefully
        try:
            cleanup_old_sessions(max_age_seconds=3600)
        except Exception as e:
            pytest.fail(f"Session cleanup failed with corrupted data: {e}")
            
        # Valid session should still be processed
        assert "corrupted_session" in STREAM_SESSION_METADATA  # Corrupted data might remain
        assert "valid_session" not in STREAM_SESSION_METADATA  # Valid old session cleaned up


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
