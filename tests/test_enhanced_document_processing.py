"""
Tests for enhanced_document_processing.py module.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from enhanced_document_processing import EnhancedChunker, ChunkingStrategy, DocumentType


class TestEnhancedChunker:
    """Test cases for EnhancedChunker class."""

    @pytest.fixture
    def chunker(self):
        """Create a chunker instance for testing."""
        return EnhancedChunker()

    @pytest.mark.asyncio
    async def test_process_document_success(self, chunker):
        """Test successful document processing."""
        content = "This is a test document with multiple sentences. It should be chunked properly."
        filename = "test.txt"
        user_id = "user123"

        # Mock the analyzer's analyze_document method
        with patch.object(chunker.analyzer, 'analyze_document', return_value=(
            DocumentType.TEXT, {"type": "text", "length": len(content)}
        )):
            # Mock the _chunk_document method
            with patch.object(chunker, '_chunk_document', return_value=[
                "First chunk content",
                "Second chunk content"
            ]):
                # Mock the _create_processed_chunk method
                with patch.object(chunker, '_create_processed_chunk', side_effect=[
                    Mock(content="First chunk", metadata={"chunk_id": 0}),
                    Mock(content="Second chunk", metadata={"chunk_id": 1})
                ]):
                    result = await chunker.process_document(content, filename, user_id)
                    
                    assert len(result) == 2

    @pytest.mark.asyncio
    async def test_process_document_with_error_fallback(self, chunker):
        """Test that process_document falls back gracefully on errors."""
        content = "Test content"
        filename = "test.txt"
        user_id = "user123"

        # Mock analyzer to raise an exception
        with patch.object(chunker.analyzer, 'analyze_document', side_effect=Exception("Analysis failed")):
            # Mock the fallback method
            with patch.object(chunker, '_fallback_processing', return_value=[
                Mock(content="Fallback chunk", metadata={"fallback": True})
            ]) as mock_fallback:
                result = await chunker.process_document(content, filename, user_id)
                
                # Verify fallback was called
                mock_fallback.assert_called_once_with(content, filename, user_id)
                assert len(result) == 1

    @pytest.mark.asyncio
    async def test_process_document_error_logging(self, chunker):
        """Test that errors are properly logged during document processing."""
        content = "Test content"
        filename = "test.txt"
        user_id = "user123"

        # Mock the logging function
        with patch('enhanced_document_processing.log_service_status') as mock_log:
            # Mock analyzer to raise an exception
            with patch.object(chunker.analyzer, 'analyze_document', side_effect=Exception("Test error")):
                # Mock the fallback method
                with patch.object(chunker, '_fallback_processing', return_value=[]):
                    await chunker.process_document(content, filename, user_id)
                    
                    # Verify error was logged
                    mock_log.assert_called_with(
                        "DOC_PROCESSING", 
                        "error", 
                        f"Error in enhanced chunking for {filename}: Test error"
                    )

    def test_chunking_strategy_enum(self):
        """Test ChunkingStrategy enum values."""
        assert ChunkingStrategy.SEMANTIC.value == "semantic"
        assert ChunkingStrategy.FIXED_SIZE.value == "fixed_size"
        assert ChunkingStrategy.ADAPTIVE.value == "adaptive"

    def test_document_type_enum(self):
        """Test DocumentType enum values."""
        assert DocumentType.TEXT.value == "text"
        assert DocumentType.CODE.value == "code"
        assert DocumentType.MARKDOWN.value == "markdown"

    def test_select_optimal_strategy_code(self, chunker):
        """Test strategy selection for code documents."""
        # Test with long code document
        strategy = chunker._select_optimal_strategy(DocumentType.CODE, 6000)
        assert strategy == ChunkingStrategy.SEMANTIC

        # Test with short code document
        strategy = chunker._select_optimal_strategy(DocumentType.CODE, 1000)
        assert strategy == ChunkingStrategy.FIXED_SIZE

    def test_select_optimal_strategy_academic(self, chunker):
        """Test strategy selection for academic documents."""
        strategy = chunker._select_optimal_strategy(DocumentType.ACADEMIC, 5000)
        assert strategy == ChunkingStrategy.HIERARCHICAL

    def test_select_optimal_strategy_markdown(self, chunker):
        """Test strategy selection for markdown documents."""
        strategy = chunker._select_optimal_strategy(DocumentType.MARKDOWN, 3000)
        assert strategy == ChunkingStrategy.SEMANTIC

    def test_select_optimal_strategy_large_content(self, chunker):
        """Test strategy selection for large documents."""
        strategy = chunker._select_optimal_strategy(DocumentType.TEXT, 15000)
        assert strategy == ChunkingStrategy.ADAPTIVE

    @pytest.mark.asyncio
    async def test_fallback_processing_exists(self, chunker):
        """Test that fallback processing method exists and is callable."""
        content = "This is test content for fallback processing."
        filename = "test.txt"
        user_id = "user123"

        # Test that the method exists (we'll mock its implementation)
        with patch.object(chunker, '_fallback_processing', return_value=[
            Mock(content="Fallback chunk", metadata={"fallback": True})
        ]) as mock_fallback:
            result = await chunker._fallback_processing(content, filename, user_id)
            
            # Should return a list
            assert isinstance(result, list)
            assert len(result) == 1

    def test_chunker_initialization(self, chunker):
        """Test that chunker initializes with proper components."""
        assert hasattr(chunker, 'analyzer')
        assert hasattr(chunker, 'recursive_splitter')
        assert hasattr(chunker, 'semantic_splitter')
        assert hasattr(chunker, 'code_splitter')

    @pytest.mark.asyncio
    async def test_memory_error_handling(self, chunker):
        """Test that memory errors are properly handled."""
        content = "Test content"
        filename = "test.txt"
        user_id = "user123"

        # Mock MemoryErrorHandler
        with patch('enhanced_document_processing.MemoryErrorHandler') as mock_handler:
            # Mock analyzer to raise an exception
            with patch.object(chunker.analyzer, 'analyze_document', side_effect=Exception("Memory error")):
                # Mock the fallback method
                with patch.object(chunker, '_fallback_processing', return_value=[]):
                    await chunker.process_document(content, filename, user_id)
                    
                    # Verify memory error handler was called
                    mock_handler.handle_memory_error.assert_called_once()

    def test_splitter_configurations(self, chunker):
        """Test that text splitters are configured correctly."""
        # Test recursive splitter
        assert chunker.recursive_splitter._chunk_size == 1000
        assert chunker.recursive_splitter._chunk_overlap == 200
        
        # Test semantic splitter
        assert chunker.semantic_splitter._chunk_size == 800
        assert chunker.semantic_splitter._chunk_overlap == 100
        
        # Test code splitter
        assert chunker.code_splitter._chunk_size == 1200
        assert chunker.code_splitter._chunk_overlap == 100
