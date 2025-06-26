"""
Comprehensive tests for DatabaseManager with proper mocking.
Tests database initialization, Redis operations, ChromaDB operations, and embedding functionality.
"""

import json
import os
import time
from unittest.mock import Mock, patch, MagicMock
import pytest

from database_manager import (
    DatabaseManager,
    get_database_health,
    get_embedding,
    db_manager,
    get_cache,
    set_cache,
    get_chat_history,
    store_chat_history,
    index_user_document,
    retrieve_user_memory,
)


class TestDatabaseManagerInitialization:
    """Test DatabaseManager initialization with various scenarios."""

    @patch.dict("os.environ", {}, clear=True)
    @patch("database_manager.redis.Redis.ping")
    @patch("database_manager.redis.ConnectionPool")
    @patch("database_manager.chromadb.HttpClient")
    @patch("database_manager.SentenceTransformer")
    @patch("database_manager.log_service_status")
    def test_successful_initialization_with_defaults(
        self, mock_log, mock_transformer, mock_chroma, mock_redis, mock_ping
    ):
        """Test successful initialization with default settings."""
        # Setup mocks
        mock_redis_pool = Mock()
        mock_redis.return_value = mock_redis_pool
        mock_ping.return_value = True

        mock_chroma_client = Mock()
        mock_chroma_collection = Mock()
        mock_chroma_client.get_or_create_collection.return_value = mock_chroma_collection
        mock_chroma_client.list_collections.return_value = []
        mock_chroma.return_value = mock_chroma_client

        mock_embedding_model = Mock()
        mock_embedding_model.encode.return_value = [0.1, 0.2, 0.3]
        mock_transformer.return_value = mock_embedding_model

        dm = DatabaseManager()

        assert dm.redis_pool == mock_redis_pool
        assert dm.chroma_client == mock_chroma_client
        assert dm.chroma_collection == mock_chroma_collection
        assert dm.embedding_model == mock_embedding_model

    @patch.dict("os.environ", {"REDIS_HOST": "test-host", "REDIS_PORT": "1234"}, clear=True)
    @patch("database_manager.redis.Redis.ping")
    @patch("database_manager.redis.ConnectionPool")
    @patch("database_manager.chromadb.HttpClient")
    @patch("database_manager.SentenceTransformer")
    @patch("database_manager.log_service_status")
    def test_redis_initialization_with_env_vars(self, mock_log, mock_transformer, mock_chroma, mock_redis, mock_ping):
        """Test Redis initialization with environment variables."""
        mock_ping.return_value = True
        mock_embedding_model = Mock()
        mock_embedding_model.encode.return_value = [0.1, 0.2, 0.3]
        mock_transformer.return_value = mock_embedding_model

        DatabaseManager()

        # Check that Redis was called with the correct parameters
        mock_redis.assert_called_once()
        call_kwargs = mock_redis.call_args[1]
        assert call_kwargs["host"] == "test-host"
        assert call_kwargs["port"] == 1234

    @patch("database_manager.redis.Redis.ping")
    @patch("database_manager.redis.ConnectionPool")
    @patch("database_manager.chromadb.HttpClient")
    @patch("database_manager.SentenceTransformer")
    @patch("database_manager.log_service_status")
    def test_redis_initialization_failure(self, mock_log, mock_transformer, mock_chroma, mock_redis, mock_ping):
        """Test Redis initialization failure handling."""
        mock_redis.side_effect = Exception("Connection failed")
        mock_embedding_model = Mock()
        mock_embedding_model.encode.return_value = [0.1, 0.2, 0.3]
        mock_transformer.return_value = mock_embedding_model

        dm = DatabaseManager()

        assert dm.redis_pool is None

    @patch("database_manager.redis.Redis.ping")
    @patch("database_manager.redis.ConnectionPool")
    @patch("database_manager.chromadb.HttpClient")
    @patch("database_manager.SentenceTransformer")
    @patch("database_manager.log_service_status")
    def test_chromadb_initialization_failure(self, mock_log, mock_transformer, mock_chroma, mock_redis, mock_ping):
        """Test ChromaDB initialization failure handling."""
        mock_ping.return_value = True
        mock_chroma.side_effect = Exception("ChromaDB failed")
        mock_embedding_model = Mock()
        mock_embedding_model.encode.return_value = [0.1, 0.2, 0.3]
        mock_transformer.return_value = mock_embedding_model

        dm = DatabaseManager()

        assert dm.chroma_client is None
        assert dm.chroma_collection is None
        # Check that ChromaDB error was logged
        mock_log.assert_any_call("CHROMADB", "failed", "Failed to initialize: ChromaDB failed")


class TestDatabaseManagerMethods:
    """Test DatabaseManager methods."""

    def setup_method(self):
        """Set up test fixtures."""
        self.dm = DatabaseManager.__new__(DatabaseManager)  # Create without __init__
        self.dm.redis_pool = Mock()
        self.dm.chroma_client = Mock()
        self.dm.chroma_collection = Mock()
        self.dm.embedding_model = Mock()

    def test_get_redis_client_success(self):
        """Test successful Redis client retrieval."""
        mock_redis_client = Mock()
        mock_redis_client.ping.return_value = True

        with patch("database_manager.redis.Redis") as mock_redis_class:
            mock_redis_class.return_value = mock_redis_client

            result = self.dm.get_redis_client()

            assert result == mock_redis_client
            mock_redis_class.assert_called_with(connection_pool=self.dm.redis_pool)
            mock_redis_client.ping.assert_called_once()

    @patch("database_manager.log_service_status")
    def test_get_redis_client_no_pool(self, mock_log):
        """Test Redis client retrieval when no pool exists."""
        self.dm.redis_pool = None

        with patch.object(self.dm, "_initialize_redis") as mock_init:
            mock_init.return_value = None  # Reinit fails

            result = self.dm.get_redis_client()

            assert result is None
            mock_init.assert_called_once()

    @patch("database_manager.log_service_status")
    def test_get_redis_client_connection_error(self, mock_log):
        """Test Redis client retrieval with connection error."""
        import redis

        mock_redis_client = Mock()
        mock_redis_client.ping.side_effect = redis.RedisError("Connection error")

        with patch("database_manager.redis.Redis") as mock_redis_class:
            mock_redis_class.return_value = mock_redis_client
            with patch.object(self.dm, "_initialize_redis") as mock_init:
                mock_init.return_value = None  # Reinit fails

                result = self.dm.get_redis_client()

                assert result is None

    def test_is_redis_available_true(self):
        """Test Redis availability check when Redis is available."""
        with patch.object(self.dm, "get_redis_client") as mock_get_redis:
            mock_get_redis.return_value = Mock()

            assert self.dm.is_redis_available() is True

    def test_is_redis_available_false(self):
        """Test Redis availability check when Redis is not available."""
        with patch.object(self.dm, "get_redis_client") as mock_get_redis:
            mock_get_redis.return_value = None

            assert self.dm.is_redis_available() is False

    def test_is_chromadb_available_true(self):
        """Test ChromaDB availability check when ChromaDB is available."""
        assert self.dm.is_chromadb_available() is True

    def test_is_chromadb_available_false(self):
        """Test ChromaDB availability check when ChromaDB is not available."""
        self.dm.chroma_client = None
        assert self.dm.is_chromadb_available() is False

    def test_is_embeddings_available_true(self):
        """Test embeddings availability check when embeddings are available."""
        assert self.dm.is_embeddings_available() is True

    def test_is_embeddings_available_false(self):
        """Test embeddings availability check when embeddings are not available."""
        self.dm.embedding_model = None
        assert self.dm.is_embeddings_available() is False

    def test_get_health_status_all_healthy(self):
        """Test health status when all services are healthy."""
        with patch.object(self.dm, "is_redis_available", return_value=True):
            status = self.dm.get_health_status()

            expected = {
                "redis": {"available": True},
                "chromadb": {
                    "available": True,
                    "client": True,
                    "collection": True,
                },
                "embeddings": {"available": True, "model": True},
            }
            assert status == expected


class TestStandaloneFunctions:
    """Test standalone utility functions."""

    @patch("database_manager.db_manager")
    def test_get_database_health(self, mock_db_manager):
        """Test get_database_health function."""
        expected_health = {"redis": {"available": True}}
        mock_db_manager.get_health_status.return_value = expected_health

        result = get_database_health()

        assert result == expected_health
        mock_db_manager.get_health_status.assert_called_once()

    @patch("database_manager.db_manager")
    def test_get_embedding_success(self, mock_db_manager):
        """Test successful embedding generation."""
        import numpy as np

        mock_model = Mock()
        mock_embedding = np.array([0.1, 0.2, 0.3])
        mock_model.encode.return_value = [mock_embedding]  # Returns list with one embedding
        mock_db_manager.embedding_model = mock_model

        result = get_embedding("test text")

        # The function returns the first element of the array - result should be the numpy array
        assert result is not None
        assert np.array_equal(result, mock_embedding)
        mock_model.encode.assert_called_once_with(["test text"])

    @patch("database_manager.db_manager")
    def test_get_embedding_no_model(self, mock_db_manager):
        """Test embedding generation when no model is available."""
        mock_db_manager.embedding_model = None

        result = get_embedding("test text")

        assert result is None

    @patch("database_manager.db_manager")
    @patch("database_manager.log_service_status")
    def test_get_embedding_model_error(self, mock_log, mock_db_manager):
        """Test embedding generation with model error."""
        mock_model = Mock()
        mock_model.encode.side_effect = Exception("Model error")
        mock_db_manager.embedding_model = mock_model

        result = get_embedding("test text")

        assert result is None
        mock_log.assert_called_with("EMBEDDINGS", "warning", "Failed to generate embedding: Model error")


class TestCacheOperations:
    """Test cache operations."""

    def test_execute_redis_operation_success(self):
        """Test successful Redis operation execution."""
        dm = DatabaseManager.__new__(DatabaseManager)
        mock_redis_client = Mock()

        def test_operation(redis_client):
            """TODO: Add proper docstring for test_operation."""
            return "success"

        with patch.object(dm, "get_redis_client") as mock_get_redis:
            mock_get_redis.return_value = mock_redis_client

            result = dm.execute_redis_operation(test_operation, "test_op")

            assert result == "success"

    @patch("database_manager.log_service_status")
    def test_execute_redis_operation_no_client(self, mock_log):
        """Test Redis operation when no client is available."""
        dm = DatabaseManager.__new__(DatabaseManager)

        def test_operation(redis_client):
            """TODO: Add proper docstring for test_operation."""
            return "success"

        with patch.object(dm, "get_redis_client") as mock_get_redis:
            mock_get_redis.return_value = None

            result = dm.execute_redis_operation(test_operation, "test_op")

            assert result is None

    @patch("time.sleep")  # Mock sleep to speed up test
    @patch("database_manager.log_service_status")
    @patch("database_manager.RedisConnectionHandler.handle_redis_error")
    def test_execute_redis_operation_exception(self, mock_error_handler, mock_log, mock_sleep):
        """Test Redis operation with exception."""
        import redis

        dm = DatabaseManager.__new__(DatabaseManager)

        def test_operation(redis_client):
            """TODO: Add proper docstring for test_operation."""
            raise redis.RedisError("Operation failed")

        with patch.object(dm, "get_redis_client") as mock_get_redis:
            mock_redis_client = Mock()
            mock_get_redis.return_value = mock_redis_client

            result = dm.execute_redis_operation(test_operation, "test_op", max_retries=1)

            assert result is None


class TestCacheUtilityFunctions:
    """Test cache utility functions."""

    @patch("builtins.__import__")
    def test_get_cache_hit(self, mock_import):
        """Test cache hit scenario."""
        mock_logging = Mock()
        mock_import.return_value = mock_logging

        mock_db_manager = Mock()
        mock_redis_client = Mock()
        mock_redis_client.get.return_value = "cached_value"
        mock_db_manager.get_redis_client.return_value = mock_redis_client

        result = get_cache(mock_db_manager, "test_key")

        assert result == "cached_value"
        mock_redis_client.get.assert_called_once_with("test_key")

    @patch("builtins.__import__")
    def test_get_cache_miss(self, mock_import):
        """Test cache miss scenario."""
        mock_logging = Mock()
        mock_import.return_value = mock_logging

        mock_db_manager = Mock()
        mock_redis_client = Mock()
        mock_redis_client.get.return_value = None
        mock_db_manager.get_redis_client.return_value = mock_redis_client

        result = get_cache(mock_db_manager, "test_key")

        assert result is None

    @patch("builtins.__import__")
    def test_set_cache_success(self, mock_import):
        """Test successful cache set."""
        mock_logging = Mock()
        mock_import.return_value = mock_logging

        mock_db_manager = Mock()
        mock_redis_client = Mock()
        mock_db_manager.get_redis_client.return_value = mock_redis_client

        result = set_cache(mock_db_manager, "test_key", "test_value", 7200)

        assert result is True
        mock_redis_client.setex.assert_called_once_with("test_key", 7200, "test_value")


class TestChatHistory:
    """Test chat history functions."""

    def test_get_chat_history_success(self):
        """Test successful chat history retrieval."""

        # Create a mock that simulates the entire Redis operation flow
        def mock_execute_redis_operation(operation_func, operation_name):
            """TODO: Add proper docstring for mock_execute_redis_operation."""
            # Create a mock redis client
            mock_redis_client = Mock()
            # Mock the lrange call to return JSON strings
            mock_redis_client.lrange.return_value = [
                '{"timestamp": 1234567890, "message": "Hello", "response": "Hi there"}'
            ]
            # Execute the operation function with our mock client
            return operation_func(mock_redis_client)

        with patch("database_manager.db_manager") as mock_db_manager:
            mock_db_manager.execute_redis_operation.side_effect = mock_execute_redis_operation

            result = get_chat_history("user123", 5)

            assert len(result) == 1
            assert result[0]["message"] == "Hello"
            assert result[0]["response"] == "Hi there"
            assert result[0]["timestamp"] == 1234567890

    @patch("database_manager.db_manager")
    def test_store_chat_history_success(self, mock_db_manager):
        """Test successful chat history storage."""
        mock_db_manager.execute_redis_operation.return_value = True

        result = store_chat_history("user123", "Hello", "Hi there")

        assert result is True
        mock_db_manager.execute_redis_operation.assert_called_once()


class TestDocumentIndexing:
    """Test document indexing functions."""

    @patch("database_manager.get_embedding")
    @patch("database_manager.time.time")
    @patch("database_manager.log_service_status")
    def test_index_user_document_success(self, mock_log, mock_time, mock_get_embedding):
        """Test successful document indexing."""
        mock_time.return_value = 1234567890

        # Create a proper mock embedding with tolist method
        mock_embedding = Mock()
        mock_embedding.tolist.return_value = [0.1, 0.2, 0.3]
        mock_get_embedding.return_value = mock_embedding

        # Import the module and patch the global db_manager after import
        import database_manager

        original_db_manager = database_manager.db_manager

        try:
            mock_db_manager = Mock()
            mock_collection = Mock()
            mock_db_manager.chroma_collection = mock_collection
            database_manager.db_manager = mock_db_manager

            result = index_user_document("user123", "Test document content", {"type": "note"})

            assert result is True
            mock_collection.add.assert_called_once()
        finally:
            # Restore the original db_manager
            database_manager.db_manager = original_db_manager

    @patch("database_manager.log_service_status")
    def test_index_user_document_no_collection(self, mock_log):
        """Test document indexing when no ChromaDB collection is available."""
        with patch("database_manager.db_manager") as mock_db_manager:
            mock_db_manager.chroma_collection = None

            result = index_user_document("user123", "Test document content")

            assert result is False
            mock_log.assert_called_with("CHROMADB", "warning", "ChromaDB collection not available")


class TestMemoryRetrieval:
    """Test memory retrieval functions."""

    @patch("database_manager.get_embedding")
    @patch("database_manager.log_service_status")
    def test_retrieve_user_memory_success(self, mock_log, mock_get_embedding):
        """Test successful memory retrieval."""
        # Create a comprehensive mock embedding that passes all validation
        mock_embedding = Mock()
        mock_embedding.tolist.return_value = [0.1, 0.2, 0.3]
        mock_embedding.size = 3  # For NumPy array check
        mock_embedding.__len__ = lambda: 3  # For __len__ check
        mock_get_embedding.return_value = mock_embedding

        mock_results = {
            "documents": [["Test document"]],
            "metadatas": [[{"user_id": "user123", "type": "note"}]],
            "distances": [[0.2]],
            "ids": [["doc_1"]],
        }

        # Import the module and patch the global db_manager after import
        import database_manager

        original_db_manager = database_manager.db_manager

        try:
            mock_db_manager = Mock()
            mock_collection = Mock()
            mock_collection.query.return_value = mock_results
            mock_db_manager.chroma_collection = mock_collection
            database_manager.db_manager = mock_db_manager

            result = retrieve_user_memory("user123", "test query", 5)

            assert len(result) == 1
            assert result[0]["content"] == "Test document"
            assert result[0]["similarity"] == 0.8  # 1 - 0.2
        finally:
            # Restore the original db_manager
            database_manager.db_manager = original_db_manager

    @patch("database_manager.log_service_status")
    def test_retrieve_user_memory_no_collection(self, mock_log):
        """Test memory retrieval when no ChromaDB collection is available."""
        with patch("database_manager.db_manager") as mock_db_manager:
            mock_db_manager.chroma_collection = None

            result = retrieve_user_memory("user123", "test query")

            assert result == []
            mock_log.assert_called_with("CHROMADB", "warning", "ChromaDB collection not available")


if __name__ == "__main__":
    pytest.main([__file__])
