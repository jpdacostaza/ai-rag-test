"""
Unit tests for database_manager module.

This module contains comprehensive tests for database operations,
including Redis connections, ChromaDB operations, and embedding functionality.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import json

from database_manager import DatabaseManager, db_manager, get_database_health, get_embedding


class TestDatabaseManager:
    """Test cases for DatabaseManager class."""

    @patch("database_manager.redis.ConnectionPool")
    @patch("database_manager.chromadb.Client")
    @patch("database_manager.SentenceTransformer")
    @patch("database_manager.log_service_status")
    def test_database_manager_initialization(self, mock_log, mock_transformer, mock_chroma, mock_redis):
        """Test DatabaseManager initialization."""
        mock_redis_pool = Mock()
        mock_redis.return_value = mock_redis_pool

        mock_chroma_client = Mock()
        mock_chroma_collection = Mock()
        mock_chroma_client.get_or_create_collection.return_value = mock_chroma_collection
        mock_chroma.return_value = mock_chroma_client

        mock_embedding_model = Mock()
        mock_transformer.return_value = mock_embedding_model

        dm = DatabaseManager()

        assert dm.redis_pool == mock_redis_pool
        assert dm.chroma_client == mock_chroma_client
        assert dm.embedding_model == mock_embedding_model

    @patch("database_manager.redis.ConnectionPool")
    def test_redis_initialization_with_env_vars(self, mock_redis):
        """Test Redis initialization with environment variables."""
        with patch.dict("os.environ", {"REDIS_HOST": "test-host", "REDIS_PORT": "1234"}):
            with patch("database_manager.chromadb.Client"), patch("database_manager.SentenceTransformer"):
                DatabaseManager()

                mock_redis.assert_called_with(
                    host="test-host",
                    port=1234,
                    db=0,
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=10,
                    socket_keepalive=True,
                    socket_keepalive_options={},
                    retry_on_timeout=True,
                )

    @patch("database_manager.redis.ConnectionPool")
    @patch("database_manager.log_service_status")
    def test_redis_initialization_failure(self, mock_log, mock_redis):
        """Test Redis initialization failure handling."""
        mock_redis.side_effect = Exception("Connection failed")

        with patch("database_manager.chromadb.Client"), patch("database_manager.SentenceTransformer"):
            dm = DatabaseManager()

            assert dm.redis_pool is None
            mock_log.assert_called_with("REDIS", "error", "Failed to initialize Redis: Connection failed")

    @patch("database_manager.redis.ConnectionPool")
    @patch("database_manager.chromadb.Client")
    @patch("database_manager.log_service_status")
    def test_chromadb_initialization_failure(self, mock_log, mock_chroma, mock_redis):
        """Test ChromaDB initialization failure handling."""
        mock_chroma.side_effect = Exception("ChromaDB failed")

        with patch("database_manager.SentenceTransformer"):
            dm = DatabaseManager()

            assert dm.chroma_client is None
            assert dm.chroma_collection is None
            mock_log.assert_called_with("CHROMADB", "error", "Failed to initialize ChromaDB: ChromaDB failed")

    def test_get_redis_client_success(self):
        """Test successful Redis client retrieval."""
        mock_redis = Mock()
        dm = DatabaseManager()
        dm.redis_pool = Mock()
        dm.redis_pool.connection.return_value = mock_redis

        result = dm.get_redis_client()
        assert result == mock_redis

    def test_get_redis_client_no_pool(self):
        """Test Redis client retrieval when no pool exists."""
        dm = DatabaseManager()
        dm.redis_pool = None

        result = dm.get_redis_client()
        assert result is None

    @patch("database_manager.log_service_status")
    def test_get_redis_client_connection_error(self, mock_log):
        """Test Redis client retrieval with connection error."""
        dm = DatabaseManager()
        dm.redis_pool = Mock()
        dm.redis_pool.connection.side_effect = Exception("Connection error")

        result = dm.get_redis_client()
        assert result is None
        mock_log.assert_called()

    def test_is_redis_available_true(self):
        """Test Redis availability check when Redis is available."""
        dm = DatabaseManager()
        dm.redis_pool = Mock()

        assert dm.is_redis_available() is True

    def test_is_redis_available_false(self):
        """Test Redis availability check when Redis is not available."""
        dm = DatabaseManager()
        dm.redis_pool = None

        assert dm.is_redis_available() is False

    def test_is_chromadb_available_true(self):
        """Test ChromaDB availability check when ChromaDB is available."""
        dm = DatabaseManager()
        dm.chroma_client = Mock()
        dm.chroma_collection = Mock()

        assert dm.is_chromadb_available() is True

    def test_is_chromadb_available_false(self):
        """Test ChromaDB availability check when ChromaDB is not available."""
        dm = DatabaseManager()
        dm.chroma_client = None
        dm.chroma_collection = None

        assert dm.is_chromadb_available() is False

    def test_is_embeddings_available_true(self):
        """Test embeddings availability check when model is available."""
        dm = DatabaseManager()
        dm.embedding_model = Mock()

        assert dm.is_embeddings_available() is True

    def test_is_embeddings_available_false(self):
        """Test embeddings availability check when model is not available."""
        dm = DatabaseManager()
        dm.embedding_model = None

        assert dm.is_embeddings_available() is False

    def test_get_health_status_all_healthy(self):
        """Test health status when all services are healthy."""
        dm = DatabaseManager()
        dm.redis_pool = Mock()
        dm.chroma_client = Mock()
        dm.chroma_collection = Mock()
        dm.embedding_model = Mock()

        with patch.object(dm, "get_redis_client") as mock_get_redis:
            mock_redis = Mock()
            mock_redis.ping.return_value = True
            mock_get_redis.return_value = mock_redis

            dm.chroma_client.heartbeat.return_value = None  # No exception means healthy

            result = dm.get_health_status()

            assert result["redis"]["available"] is True
            assert result["chromadb"]["available"] is True
            assert result["chromadb"]["client"] is True
            assert result["chromadb"]["collection"] is True
            assert result["embeddings"]["available"] is True
            assert result["embeddings"]["model"] is True


class TestStandaloneFunctions:
    """Test cases for standalone functions."""

    @patch("database_manager.db_manager")
    def test_get_database_health(self, mock_db_manager):
        """Test get_database_health function."""
        mock_health = {"redis": {"available": True}, "chromadb": {"available": True}, "embeddings": {"available": True}}
        mock_db_manager.get_health_status.return_value = mock_health

        result = get_database_health()
        assert result == mock_health

    @patch("database_manager.db_manager")
    def test_get_embedding_success(self, mock_db_manager):
        """Test successful embedding generation."""
        mock_model = Mock()
        mock_model.encode.return_value = [0.1, 0.2, 0.3]
        mock_db_manager.embedding_model = mock_model

        result = get_embedding("test text")

        assert result == [0.1, 0.2, 0.3]
        mock_model.encode.assert_called_with("test text")

    @patch("database_manager.db_manager")
    def test_get_embedding_no_model(self, mock_db_manager):
        """Test embedding generation when model is unavailable."""
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
        mock_log.assert_called_with("EMBEDDINGS", "error", "Failed to generate embedding: Model error")


class TestCacheOperations:
    """Test cases for cache operations with proper database manager instance."""

    def test_execute_redis_operation_success(self):
        """Test successful Redis operation execution."""
        dm = DatabaseManager()

        def test_operation(redis_client):
            """TODO: Add proper docstring for test_operation."""
            return "success"

        with patch.object(dm, "get_redis_client") as mock_get_redis:
            mock_redis = Mock()
            mock_get_redis.return_value = mock_redis

            result = dm.execute_redis_operation(test_operation, "test_op")

            assert result == "success"

    def test_execute_redis_operation_no_client(self):
        """Test Redis operation when client is unavailable."""
        dm = DatabaseManager()

        def test_operation(redis_client):
            """TODO: Add proper docstring for test_operation."""
            return "success"

        with patch.object(dm, "get_redis_client") as mock_get_redis:
            mock_get_redis.return_value = None

            result = dm.execute_redis_operation(test_operation, "test_op")

            assert result is None

    @patch("database_manager.log_service_status")
    def test_execute_redis_operation_exception(self, mock_log):
        """Test Redis operation with exception."""
        dm = DatabaseManager()

        def test_operation(redis_client):
            """TODO: Add proper docstring for test_operation."""
            raise Exception("Operation failed")

        with patch.object(dm, "get_redis_client") as mock_get_redis:
            mock_redis = Mock()
            mock_get_redis.return_value = mock_redis

            result = dm.execute_redis_operation(test_operation, "test_op")

            assert result is None
            mock_log.assert_called()


if __name__ == "__main__":
    pytest.main([__file__])
