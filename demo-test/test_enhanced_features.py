"""
Test suite for newly added FastAPI enhancements and features.
Tests global exception handlers, enhanced middleware, streaming improvements, and session management.
"""

import asyncio
import json
import pytest
import time
import uuid
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from fastapi import HTTPException
from fastapi.exceptions import RequestValidationError
from httpx import AsyncClient

# Import the main app and functions
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import (
    app, 
    cleanup_old_sessions, 
    stop_streaming_session,
    STREAM_SESSION_STOP,
    STREAM_SESSION_METADATA,
    call_ollama_llm_stream,
    call_openai_llm_stream
)

# Test client for FastAPI
client = TestClient(app)


class TestGlobalExceptionHandlers:
    """Test the new global exception handlers."""
    
    def test_http_exception_handler(self):
        """Test HTTP exception handler returns structured error response."""
        # Test 404 error
        response = client.get("/nonexistent-endpoint")
        assert response.status_code == 404
        
        error_data = response.json()
        assert "error" in error_data
        assert error_data["error"]["type"] == "http_error"
        assert error_data["error"]["code"] == 404
        assert "timestamp" in error_data["error"]
        
    def test_validation_exception_handler(self):
        """Test validation error handler with invalid request data."""
        # Send invalid chat request (missing required fields)
        response = client.post("/chat", json={})
        assert response.status_code == 422
        
        error_data = response.json()
        assert "error" in error_data
        assert error_data["error"]["type"] == "validation_error"
        assert error_data["error"]["code"] == 422
        assert "details" in error_data["error"]
        assert "timestamp" in error_data["error"]
        
    def test_chat_input_validation(self):
        """Test chat endpoint input validation."""
        # Test empty message
        response = client.post("/chat", json={
            "user_id": "test_user",
            "message": ""
        })
        assert response.status_code == 400
        
        error_data = response.json()
        assert "error" in error_data
        assert "Message cannot be empty" in error_data["error"]["message"]


class TestEnhancedMiddleware:
    """Test the enhanced middleware functionality."""
    
    def test_request_id_generation(self):
        """Test that requests get unique request IDs."""
        response1 = client.get("/health/simple")
        response2 = client.get("/health/simple")
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        # Check X-Request-ID headers exist and are different
        request_id1 = response1.headers.get("X-Request-ID")
        request_id2 = response2.headers.get("X-Request-ID")
        
        assert request_id1 is not None
        assert request_id2 is not None
        assert request_id1 != request_id2
        
    def test_process_time_header(self):
        """Test that process time header is added."""
        response = client.get("/health/simple")
        assert response.status_code == 200
        
        process_time = response.headers.get("X-Process-Time")
        assert process_time is not None
        assert "ms" in process_time
        
        # Should be a valid float value
        time_value = float(process_time.replace("ms", ""))
        assert time_value >= 0


class TestSessionManagement:
    """Test enhanced session management for streaming."""
    
    def setup_method(self):
        """Clean up sessions before each test."""
        STREAM_SESSION_STOP.clear()
        STREAM_SESSION_METADATA.clear()
        
    def test_session_creation_and_cleanup(self):
        """Test session creation and cleanup functionality."""
        session_id = "test_session_1"
        
        # Create session
        STREAM_SESSION_STOP[session_id] = False
        STREAM_SESSION_METADATA[session_id] = {
            "created_at": time.time(),
            "user_id": "test_user",
            "model": "test_model"
        }
        
        assert session_id in STREAM_SESSION_STOP
        assert session_id in STREAM_SESSION_METADATA
        
        # Test stop session
        stop_streaming_session(session_id)
        assert STREAM_SESSION_STOP[session_id] is True
        assert "stopped_at" in STREAM_SESSION_METADATA[session_id]
        
    def test_old_session_cleanup(self):
        """Test automatic cleanup of old sessions."""
        current_time = time.time()
        
        # Create old session (2 hours ago)
        old_session = "old_session"
        STREAM_SESSION_STOP[old_session] = False
        STREAM_SESSION_METADATA[old_session] = {
            "created_at": current_time - 7200,  # 2 hours ago
            "user_id": "test_user"
        }
        
        # Create new session
        new_session = "new_session"
        STREAM_SESSION_STOP[new_session] = False
        STREAM_SESSION_METADATA[new_session] = {
            "created_at": current_time,
            "user_id": "test_user"
        }
        
        # Run cleanup with 1 hour max age
        cleanup_old_sessions(max_age_seconds=3600)
        
        # Old session should be removed, new session should remain
        assert old_session not in STREAM_SESSION_STOP
        assert old_session not in STREAM_SESSION_METADATA
        assert new_session in STREAM_SESSION_STOP
        assert new_session in STREAM_SESSION_METADATA


class TestStreamingEnhancements:
    """Test streaming response enhancements."""
    
    @pytest.mark.asyncio
    async def test_ollama_stream_resource_cleanup(self):
        """Test proper resource cleanup in Ollama streaming."""
        messages = [{"role": "user", "content": "test message"}]
        
        # Mock httpx.AsyncClient
        with patch('main.httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client
            
            # Mock stream response
            mock_response = AsyncMock()
            mock_response.raise_for_status = MagicMock()
            mock_response.aiter_lines = AsyncMock(return_value=[
                '{"response": "test", "done": false}',
                '{"response": " token", "done": true}'
            ])
            
            mock_client.stream.return_value.__aenter__ = AsyncMock(return_value=mock_response)
            mock_client.stream.return_value.__aexit__ = AsyncMock(return_value=None)
            
            # Test streaming
            tokens = []
            async for token in call_ollama_llm_stream(messages, session_id="test_session"):
                tokens.append(token)
                
            # Verify tokens received
            assert "test" in tokens
            assert " token" in tokens
            
            # Verify client cleanup was called
            mock_client.aclose.assert_called_once()
            
    @pytest.mark.asyncio
    async def test_openai_stream_resource_cleanup(self):
        """Test proper resource cleanup in OpenAI streaming."""
        messages = [{"role": "user", "content": "test message"}]
        
        with patch('main.httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client
            
            # Mock stream response
            mock_response = AsyncMock()
            mock_response.raise_for_status = MagicMock()
            mock_response.aiter_lines = AsyncMock(return_value=[
                'data: {"choices": [{"delta": {"content": "test"}}]}',
                'data: {"choices": [{"delta": {"content": " token"}}]}',
                'data: [DONE]'
            ])
            
            mock_client.stream.return_value.__aenter__ = AsyncMock(return_value=mock_response)
            mock_client.stream.return_value.__aexit__ = AsyncMock(return_value=None)
            
            # Test streaming
            tokens = []
            async for token in call_openai_llm_stream(messages, session_id="test_session"):
                tokens.append(token)
                
            # Verify tokens received
            assert "test" in tokens
            assert " token" in tokens
            
            # Verify client cleanup was called
            mock_client.aclose.assert_called_once()


class TestAdminEndpoints:
    """Test new admin endpoints for session management."""
    
    def setup_method(self):
        """Clean up sessions before each test."""
        STREAM_SESSION_STOP.clear()
        STREAM_SESSION_METADATA.clear()
        
    def test_session_status_endpoint(self):
        """Test session status admin endpoint."""
        # Create test sessions
        session1 = "session_1"
        session2 = "session_2"
        current_time = time.time()
        
        STREAM_SESSION_METADATA[session1] = {
            "created_at": current_time,
            "user_id": "user1",
            "model": "model1"
        }
        STREAM_SESSION_METADATA[session2] = {
            "created_at": current_time - 100,
            "user_id": "user2", 
            "model": "model2"
        }
        
        response = client.get("/admin/sessions/status")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "ok"
        assert data["total_sessions"] == 2
        assert len(data["active_sessions"]) == 2
        
        # Check session details
        session_ids = [s["session_id"] for s in data["active_sessions"]]
        assert session1 in session_ids
        assert session2 in session_ids
        
    def test_session_cleanup_endpoint(self):
        """Test session cleanup admin endpoint."""
        # Create old session
        old_session = "old_session"
        STREAM_SESSION_METADATA[old_session] = {
            "created_at": time.time() - 7200,  # 2 hours ago
            "user_id": "test_user"
        }
        
        response = client.post("/admin/sessions/cleanup")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "ok"
        assert "cleaned up" in data["message"].lower()
        assert data["active_sessions"] == 0


class TestHealthCheckEnhancements:
    """Test enhanced health check endpoints."""
    
    def test_simple_health_with_uptime(self):
        """Test simple health check includes uptime."""
        response = client.get("/health/simple")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "ok"
        assert "uptime_seconds" in data
        assert isinstance(data["uptime_seconds"], (int, float))
        assert data["uptime_seconds"] >= 0
        assert "timestamp" in data
        assert data["timestamp"].endswith("Z") or "T" in data["timestamp"]  # ISO format


class TestStreamingChatCompletions:
    """Test enhanced streaming in chat completions endpoint."""
    
    @patch('main.call_llm_stream')
    def test_streaming_response_headers(self, mock_stream):
        """Test streaming response includes proper headers."""
        # Mock async generator
        async def mock_generator():
            yield "test"
            yield " token"
            
        mock_stream.return_value = mock_generator()
        
        # Test streaming request
        response = client.post("/v1/chat/completions", json={
            "messages": [{"role": "user", "content": "test"}],
            "stream": True,
            "user": "test_user",
            "model": "test_model"
        })
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/event-stream; charset=utf-8"
        assert "X-Session-ID" in response.headers
        
        # Verify session was created
        session_id = response.headers["X-Session-ID"]
        assert session_id.startswith("test_user:test_model:")


class TestErrorResponseStructure:
    """Test structured error responses across the application."""
    
    def test_structured_error_format(self):
        """Test that all errors follow the structured format."""
        # Test HTTP error
        response = client.get("/nonexistent")
        error = response.json()["error"]
        
        required_fields = ["type", "code", "message", "timestamp"]
        for field in required_fields:
            assert field in error
            
        assert error["type"] == "http_error"
        assert error["code"] == 404
        
    def test_validation_error_details(self):
        """Test validation errors include detailed information."""
        response = client.post("/chat", json={"invalid": "data"})
        error = response.json()["error"]
        
        assert error["type"] == "validation_error"
        assert error["code"] == 422
        assert "details" in error
        assert len(error["details"]) > 0


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
