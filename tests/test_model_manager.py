"""
Comprehensive tests for ModelManager functionality.
Tests model cache management, Ollama API interactions, and API endpoints.
"""

import os
import time
from unittest.mock import AsyncMock, Mock, patch
import pytest
import httpx
from fastapi import HTTPException
from fastapi.testclient import TestClient

# Import the model manager components
from model_manager import (
    router,
    refresh_model_cache,
    pull_model,
    ensure_model_available,
    _model_cache,
    OLLAMA_BASE_URL,
    list_available_models,
    get_model_details,
    delete_model,
    pull_model_endpoint,
    ensure_default_model,
)


class TestModelCache:
    """Test model cache functionality."""

    def setup_method(self):
        """Reset the model cache before each test."""
        _model_cache["data"] = []
        _model_cache["last_updated"] = 0
        _model_cache["ttl"] = 300

    @pytest.mark.asyncio
    @patch('model_manager.httpx.AsyncClient')
    @patch('model_manager.logging')
    async def test_refresh_model_cache_success(self, mock_logging, mock_client):
        """Test successful model cache refresh."""
        # Mock the HTTP response
        mock_response = Mock()
        mock_response.json.return_value = {
            "models": [
                {"name": "llama3.2:3b"},
                {"name": "codellama:7b"}
            ]
        }
        mock_response.raise_for_status.return_value = None
        
        mock_client_instance = AsyncMock()
        mock_client_instance.get.return_value = mock_response
        mock_client.return_value.__aenter__.return_value = mock_client_instance
        
        await refresh_model_cache(force=True)
        
        # Verify cache was updated
        assert len(_model_cache["data"]) == 2
        assert _model_cache["data"][0]["id"] == "llama3.2:3b"
        assert _model_cache["data"][1]["id"] == "codellama:7b"
        assert _model_cache["last_updated"] > 0
        
        # Verify logging
        mock_logging.info.assert_any_call("[MODELS] Refreshing model cache...")
        mock_logging.info.assert_any_call("[MODELS] Successfully fetched 2 models from Ollama.")

    @pytest.mark.asyncio
    @patch('model_manager.httpx.AsyncClient')
    @patch('model_manager.logging')
    async def test_refresh_model_cache_connection_error(self, mock_logging, mock_client):
        """Test model cache refresh with connection error."""
        mock_client_instance = AsyncMock()
        mock_client_instance.get.side_effect = httpx.RequestError("Connection failed")
        mock_client.return_value.__aenter__.return_value = mock_client_instance
        
        await refresh_model_cache(force=True)
        
        # Verify cache is empty due to error
        assert len(_model_cache["data"]) == 0
        
        # Verify error logging
        mock_logging.error.assert_called_with(
            "[MODELS] Failed to connect to Ollama to refresh models: Connection failed"
        )

    @pytest.mark.asyncio
    @patch('model_manager.time.time')
    async def test_refresh_model_cache_ttl_check(self, mock_time):
        """Test that cache refresh respects TTL."""
        # Set up cache with recent update
        _model_cache["last_updated"] = 1000
        _model_cache["ttl"] = 300
        mock_time.return_value = 1200  # 200 seconds later, within TTL
        
        with patch('model_manager.httpx.AsyncClient') as mock_client:
            await refresh_model_cache(force=False)
            
            # HTTP client should not be called
            mock_client.assert_not_called()

    @pytest.mark.asyncio
    @patch('model_manager.httpx.AsyncClient')
    @patch('model_manager.logging')
    async def test_refresh_model_cache_unexpected_error(self, mock_logging, mock_client):
        """Test model cache refresh with unexpected error."""
        mock_client_instance = AsyncMock()
        mock_client_instance.get.side_effect = ValueError("Unexpected error")
        mock_client.return_value.__aenter__.return_value = mock_client_instance
        
        await refresh_model_cache(force=True)
        
        # Verify error logging
        mock_logging.error.assert_called_with(
            "[MODELS] An unexpected error occurred while fetching Ollama models: Unexpected error"
        )


class TestModelPulling:
    """Test model pulling functionality."""

    @pytest.mark.asyncio
    @patch('model_manager.httpx.AsyncClient')
    @patch('model_manager.logging')
    async def test_pull_model_success(self, mock_logging, mock_client):
        """Test successful model pulling."""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        
        mock_client_instance = AsyncMock()
        mock_client_instance.post.return_value = mock_response
        mock_client.return_value.__aenter__.return_value = mock_client_instance
        
        result = await pull_model("llama3.2:3b")
        
        assert result is True
        mock_logging.info.assert_any_call("[MODELS] Pulling model llama3.2:3b from Ollama registry...")
        mock_logging.info.assert_any_call("[MODELS] Successfully pulled model llama3.2:3b")

    @pytest.mark.asyncio
    @patch('model_manager.httpx.AsyncClient')
    @patch('model_manager.logging')
    async def test_pull_model_request_error(self, mock_logging, mock_client):
        """Test model pulling with request error."""
        mock_client_instance = AsyncMock()
        mock_client_instance.post.side_effect = httpx.RequestError("Connection failed")
        mock_client.return_value.__aenter__.return_value = mock_client_instance
        
        result = await pull_model("llama3.2:3b")
        
        assert result is False
        mock_logging.error.assert_called_with(
            "[MODELS] Failed to connect to Ollama for model pull: Connection failed"
        )

    @pytest.mark.asyncio
    @patch('model_manager.httpx.AsyncClient')
    @patch('model_manager.logging')
    async def test_pull_model_http_error(self, mock_logging, mock_client):
        """Test model pulling with HTTP error."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.text = "Model not found"
        
        mock_client_instance = AsyncMock()
        mock_client_instance.post.side_effect = httpx.HTTPStatusError(
            "404 Client Error", request=Mock(), response=mock_response
        )
        mock_client.return_value.__aenter__.return_value = mock_client_instance
        
        result = await pull_model("nonexistent:model")
        
        assert result is False
        mock_logging.error.assert_called_with(
            "[MODELS] Model pull failed with HTTP 404: Model not found"
        )

    @pytest.mark.asyncio
    @patch('model_manager.httpx.AsyncClient')
    @patch('model_manager.logging')
    async def test_pull_model_unexpected_error(self, mock_logging, mock_client):
        """Test model pulling with unexpected error."""
        mock_client_instance = AsyncMock()
        mock_client_instance.post.side_effect = ValueError("Unexpected error")
        mock_client.return_value.__aenter__.return_value = mock_client_instance
        
        result = await pull_model("llama3.2:3b")
        
        assert result is False
        mock_logging.error.assert_called_with(
            "[MODELS] Unexpected error during model pull: Unexpected error"
        )


class TestEnsureModelAvailable:
    """Test model availability checking and pulling."""

    def setup_method(self):
        """Reset the model cache before each test."""
        _model_cache["data"] = []
        _model_cache["last_updated"] = 0

    @pytest.mark.asyncio
    @patch('model_manager.refresh_model_cache')
    @patch('model_manager.logging')
    async def test_ensure_model_available_exists(self, mock_logging, mock_refresh):
        """Test ensure_model_available when model exists in cache."""
        # Set up cache with existing model
        _model_cache["data"] = [
            {"id": "llama3.2:3b", "object": "model", "owned_by": "ollama"}
        ]
        
        result = await ensure_model_available("llama3.2:3b", auto_pull=True)
        
        assert result is True
        mock_refresh.assert_called_once()

    @pytest.mark.asyncio
    @patch('model_manager.pull_model')
    @patch('model_manager.refresh_model_cache')
    @patch('model_manager.logging')
    async def test_ensure_model_available_pulls_missing(self, mock_logging, mock_refresh, mock_pull):
        """Test ensure_model_available when model needs to be pulled."""
        # Set up empty cache initially, then with pulled model
        mock_refresh.side_effect = [
            None,  # First call - cache remains empty
            None   # Second call after pull - cache gets populated
        ]
        
        def mock_refresh_side_effect(force=False):
            if force:  # Second call after pull
                _model_cache["data"] = [
                    {"id": "llama3.2:3b", "object": "model", "owned_by": "ollama"}
                ]
        
        mock_refresh.side_effect = mock_refresh_side_effect
        mock_pull.return_value = True
        
        result = await ensure_model_available("llama3.2:3b", auto_pull=True)
        
        assert result is True
        mock_pull.assert_called_once_with("llama3.2:3b")
        assert mock_refresh.call_count >= 2

    @pytest.mark.asyncio
    @patch('model_manager.pull_model')
    @patch('model_manager.refresh_model_cache')
    @patch('model_manager.logging')
    async def test_ensure_model_available_pull_fails(self, mock_logging, mock_refresh, mock_pull):
        """Test ensure_model_available when pull fails."""
        mock_pull.return_value = False
        
        result = await ensure_model_available("nonexistent:model", auto_pull=True)
        
        assert result is False
        mock_pull.assert_called_once_with("nonexistent:model")
        mock_logging.error.assert_called_with("[MODELS] Failed to pull model nonexistent:model")

    @pytest.mark.asyncio
    @patch('model_manager.refresh_model_cache')
    async def test_ensure_model_available_no_auto_pull(self, mock_refresh):
        """Test ensure_model_available with auto_pull=False."""
        # Empty cache
        _model_cache["data"] = []
        
        result = await ensure_model_available("missing:model", auto_pull=False)
        
        assert result is False


class TestAPIEndpoints:
    """Test API endpoints."""

    def setup_method(self):
        """Reset the model cache before each test."""
        _model_cache["data"] = []
        _model_cache["last_updated"] = 0

    @pytest.mark.asyncio
    @patch('model_manager.refresh_model_cache')
    async def test_list_available_models(self, mock_refresh):
        """Test the list_available_models endpoint."""
        # Set up cache
        _model_cache["data"] = [
            {"id": "llama3.2:3b", "object": "model", "owned_by": "ollama"},
            {"id": "codellama:7b", "object": "model", "owned_by": "ollama"}
        ]
        
        result = await list_available_models()
        
        assert result["object"] == "list"
        assert len(result["data"]) == 2
        assert result["data"][0]["id"] == "llama3.2:3b"
        mock_refresh.assert_called_once()

    @pytest.mark.asyncio
    @patch('model_manager.refresh_model_cache')
    async def test_get_model_details_exists(self, mock_refresh):
        """Test get_model_details for existing model."""
        # Set up cache
        _model_cache["data"] = [
            {"id": "llama3.2:3b", "object": "model", "owned_by": "ollama"}
        ]
        
        result = await get_model_details("llama3.2:3b")
        
        assert result["id"] == "llama3.2:3b"
        assert result["object"] == "model"

    @pytest.mark.asyncio
    @patch('model_manager.refresh_model_cache')
    async def test_get_model_details_not_found(self, mock_refresh):
        """Test get_model_details for non-existent model."""
        # Empty cache
        _model_cache["data"] = []
        
        with pytest.raises(HTTPException) as exc_info:
            await get_model_details("nonexistent:model")
        
        assert exc_info.value.status_code == 404
        assert "not found" in exc_info.value.detail

    @pytest.mark.asyncio
    @patch('model_manager.refresh_model_cache')
    @patch('model_manager.httpx.AsyncClient')
    async def test_delete_model_success(self, mock_client, mock_refresh):
        """Test successful model deletion."""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        
        mock_client_instance = AsyncMock()
        mock_client_instance.request.return_value = mock_response
        mock_client.return_value.__aenter__.return_value = mock_client_instance
        
        result = await delete_model("llama3.2:3b")
        
        assert result["status"] == "deleted"
        assert result["model"] == "llama3.2:3b"
        mock_refresh.assert_called_with(force=True)

    @pytest.mark.asyncio
    @patch('model_manager.httpx.AsyncClient')
    async def test_delete_model_not_found(self, mock_client):
        """Test model deletion when model not found."""
        mock_response = Mock()
        mock_response.status_code = 404
        
        mock_client_instance = AsyncMock()
        mock_client_instance.request.side_effect = httpx.HTTPStatusError(
            "404 Client Error", request=Mock(), response=mock_response
        )
        mock_client.return_value.__aenter__.return_value = mock_client_instance
        
        with pytest.raises(HTTPException) as exc_info:
            await delete_model("nonexistent:model")
        
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    @patch('model_manager.pull_model')
    @patch('model_manager.refresh_model_cache')
    async def test_pull_model_endpoint_success(self, mock_refresh, mock_pull):
        """Test successful model pull endpoint."""
        mock_pull.return_value = True
        
        result = await pull_model_endpoint("llama3.2:3b")
        
        assert result["status"] == "success"
        assert result["model"] == "llama3.2:3b"
        mock_refresh.assert_called_with(force=True)

    @pytest.mark.asyncio
    @patch('model_manager.pull_model')
    async def test_pull_model_endpoint_failure(self, mock_pull):
        """Test model pull endpoint failure."""
        mock_pull.return_value = False
        
        with pytest.raises(HTTPException) as exc_info:
            await pull_model_endpoint("nonexistent:model")
        
        assert exc_info.value.status_code == 500
        assert "Failed to pull model" in exc_info.value.detail

    @pytest.mark.asyncio
    @patch('model_manager.ensure_model_available')
    @patch.dict(os.environ, {"DEFAULT_MODEL": "llama3.2:3b"})
    async def test_ensure_default_model_success(self, mock_ensure):
        """Test successful default model ensuring."""
        mock_ensure.return_value = True
        
        result = await ensure_default_model()
        
        assert result["status"] == "success"
        assert result["model"] == "llama3.2:3b"
        assert result["pulled"] is True
        mock_ensure.assert_called_once_with("llama3.2:3b", auto_pull=True)

    @pytest.mark.asyncio
    @patch('model_manager.ensure_model_available')
    @patch.dict(os.environ, {"DEFAULT_MODEL": "missing:model"})
    async def test_ensure_default_model_failure(self, mock_ensure):
        """Test default model ensuring failure."""
        mock_ensure.return_value = False
        
        with pytest.raises(HTTPException) as exc_info:
            await ensure_default_model()
        
        assert exc_info.value.status_code == 500
        assert "Failed to ensure default model" in exc_info.value.detail


class TestConfiguration:
    """Test configuration and constants."""

    def test_ollama_base_url_default(self):
        """Test default OLLAMA_BASE_URL."""
        with patch.dict(os.environ, {}, clear=True):
            # Re-import to get fresh configuration
            import importlib
            import model_manager
            importlib.reload(model_manager)
            
            # Default should be used
            assert model_manager.OLLAMA_BASE_URL == "http://ollama:11434"

    def test_ollama_base_url_from_env(self):
        """Test OLLAMA_BASE_URL from environment variable."""
        with patch.dict(os.environ, {"OLLAMA_BASE_URL": "http://custom:8080"}):
            import importlib
            import model_manager
            importlib.reload(model_manager)
            
            assert model_manager.OLLAMA_BASE_URL == "http://custom:8080"

    def test_model_cache_structure(self):
        """Test model cache structure."""
        assert "data" in _model_cache
        assert "last_updated" in _model_cache
        assert "ttl" in _model_cache
        assert _model_cache["ttl"] == 300  # 5 minutes
        assert isinstance(_model_cache["data"], list)


if __name__ == "__main__":
    pytest.main([__file__])
