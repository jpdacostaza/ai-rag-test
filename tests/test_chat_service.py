"""
Test Suite for ChatService
==========================

Comprehensive tests for the ChatService class, including async patterns,
error handling, and service interactions.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from services.chat_service import ChatService, ChatContext
from models.models import ChatRequest, ChatResponse
from tests.conftest import AsyncTestCase


@pytest.mark.asyncio
@pytest.mark.service_layer
class TestChatService(AsyncTestCase):
    """Test suite for ChatService functionality."""
    
    async def test_chat_service_initialization(self, chat_service):
        """Test that ChatService initializes correctly."""
        assert isinstance(chat_service, ChatService)
        assert hasattr(chat_service, 'process_chat')
        assert hasattr(chat_service, '_generate_response')
        assert hasattr(chat_service, '_store_conversation')
    
    async def test_process_chat_basic(self, chat_service, sample_chat_request):
        """Test basic chat processing functionality."""
        with patch('services.chat_service.call_llm') as mock_llm:
            mock_llm.return_value = "Mock LLM response"
            
            response = await chat_service.process_chat(sample_chat_request)
            
            self.assert_chat_response_valid(response)
            assert "Mock LLM response" in response.response
            mock_llm.assert_called_once()
    
    async def test_process_chat_with_cache_hit(self, chat_service, sample_chat_request, mock_cache_service):
        """Test chat processing with cache hit."""
        # Setup cache to return a response
        mock_cache_service.get.return_value = {"response": "Cached response"}
        
        response = await chat_service.process_chat(sample_chat_request)
        
        self.assert_chat_response_valid(response)
        assert response.response == "Cached response"
        mock_cache_service.get.assert_called_once()
    
    async def test_process_chat_with_cache_miss(self, chat_service, sample_chat_request, mock_cache_service):
        """Test chat processing with cache miss."""
        # Setup cache to return None (miss)
        mock_cache_service.get.return_value = None
        
        with patch('services.chat_service.call_llm') as mock_llm:
            mock_llm.return_value = "Fresh LLM response"
            
            response = await chat_service.process_chat(sample_chat_request)
            
            self.assert_chat_response_valid(response)
            assert "Fresh LLM response" in response.response
            mock_cache_service.get.assert_called_once()
            mock_cache_service.set.assert_called_once()
    
    async def test_generate_response_with_context(self, chat_service):
        """Test response generation with conversation context."""
        context = ChatContext()
        context.user_id = "test_user"
        context.message = "What's my name?"
        context.history = [{"message": "My name is John", "response": "Nice to meet you, John!"}]
        context.memories = ["User's name is John"]
        context.request_id = "test_123"
        
        with patch('services.chat_service.call_llm') as mock_llm:
            mock_llm.return_value = "Your name is John!"
            
            response = await chat_service._generate_response(context)
            
            assert response == "Your name is John!"
            mock_llm.assert_called_once()
            
            # Check that context was included in LLM call
            call_args = mock_llm.call_args[0][0]  # Get the messages argument
            assert any("John" in str(msg) for msg in call_args)
    
    async def test_store_conversation_memory(self, chat_service, mock_memory_service):
        """Test conversation memory storage."""
        context = ChatContext()
        context.user_id = "test_user"
        context.message = "Remember that I like coffee"
        context.history = []
        context.memories = []
        context.request_id = "test_123"
        response = "I'll remember that you like coffee!"
        
        result = await chat_service._store_conversation(context, response)
        
        assert result is True
        mock_memory_service.store_conversation_memory.assert_called_once()
    
    async def test_error_handling_in_process_chat(self, chat_service, sample_chat_request):
        """Test error handling during chat processing."""
        with patch('services.chat_service.call_llm') as mock_llm:
            mock_llm.side_effect = Exception("LLM service unavailable")
            
            response = await chat_service.process_chat(sample_chat_request)
            
            # Should return an error response instead of crashing
            self.assert_chat_response_valid(response)
            assert "trouble processing" in response.response.lower() or "error" in response.response.lower()
    
    async def test_empty_message_handling(self, chat_service):
        """Test handling of empty messages."""
        empty_request = ChatRequest(user_id="test_user", message="")
        
        response = await chat_service.process_chat(empty_request)
        
        # Should handle empty messages gracefully
        self.assert_chat_response_valid(response)
    
    async def test_concurrent_chat_requests(self, chat_service):
        """Test handling multiple concurrent chat requests."""
        requests = [
            ChatRequest(user_id=f"user_{i}", message=f"Hello from user {i}")
            for i in range(5)
        ]
        
        with patch('services.chat_service.call_llm') as mock_llm:
            mock_llm.return_value = "Hello back!"
            
            # Process requests concurrently
            tasks = [chat_service.process_chat(req) for req in requests]
            responses = await asyncio.gather(*tasks)
            
            # All responses should be valid
            assert len(responses) == 5
            for response in responses:
                self.assert_chat_response_valid(response)
            
            # LLM should have been called for each request
            assert mock_llm.call_count == 5
    
    @pytest.mark.performance
    async def test_chat_service_performance(self, chat_service, sample_chat_request):
        """Test chat service performance under load."""
        import time
        
        with patch('services.chat_service.call_llm') as mock_llm:
            mock_llm.return_value = "Quick response"
            
            start_time = time.time()
            
            # Process multiple requests
            tasks = [chat_service.process_chat(sample_chat_request) for _ in range(10)]
            responses = await asyncio.gather(*tasks)
            
            end_time = time.time()
            duration = end_time - start_time
            
            # Should complete within reasonable time (adjust threshold as needed)
            assert duration < 5.0, f"Chat processing took too long: {duration}s"
            assert len(responses) == 10
            
            for response in responses:
                self.assert_chat_response_valid(response)


@pytest.mark.asyncio
@pytest.mark.unit
class TestChatContext:
    """Test suite for ChatContext functionality."""
    
    def test_chat_context_creation(self):
        """Test ChatContext creation and attributes."""
        context = ChatContext()
        context.user_id = "test_user"
        context.message = "Hello"
        context.history = []
        context.memories = []
        context.request_id = "test_123"
        
        assert context.user_id == "test_user"
        assert context.message == "Hello"
        assert context.history == []
        assert context.memories == []
        assert context.request_id == "test_123"
    
    def test_chat_context_with_data(self):
        """Test ChatContext with actual data."""
        history = [{"message": "Hi", "response": "Hello!"}]
        memories = ["User prefers short responses"]
        
        context = ChatContext()
        context.user_id = "test_user"
        context.message = "How are you?"
        context.history = history
        context.memories = memories
        context.request_id = "test_456"
        
        assert len(context.history) == 1
        assert len(context.memories) == 1
        assert context.history[0]["message"] == "Hi"
        assert "short responses" in context.memories[0]


@pytest.mark.asyncio
@pytest.mark.error_handling
class TestChatServiceErrorHandling:
    """Test suite for ChatService error handling."""
    
    async def test_llm_service_failure(self, chat_service, sample_chat_request):
        """Test handling of LLM service failures."""
        with patch('services.chat_service.call_llm') as mock_llm:
            mock_llm.side_effect = ConnectionError("LLM service down")
            
            response = await chat_service.process_chat(sample_chat_request)
            
            # Should return graceful error message
            assert isinstance(response, ChatResponse)
            assert "trouble" in response.response.lower() or "error" in response.response.lower()
    
    async def test_memory_service_failure(self, chat_service, sample_chat_request, mock_memory_service):
        """Test handling of memory service failures."""
        mock_memory_service.store_conversation_memory.side_effect = Exception("Memory service down")
        
        with patch('services.chat_service.call_llm') as mock_llm:
            mock_llm.return_value = "Response despite memory failure"
            
            response = await chat_service.process_chat(sample_chat_request)
            
            # Should still return response even if memory storage fails
            assert isinstance(response, ChatResponse)
            assert "Response despite memory failure" in response.response
    
    async def test_cache_service_failure(self, chat_service, sample_chat_request, mock_cache_service):
        """Test handling of cache service failures."""
        mock_cache_service.get.side_effect = Exception("Cache service down")
        mock_cache_service.set.side_effect = Exception("Cache service down")
        
        with patch('services.chat_service.call_llm') as mock_llm:
            mock_llm.return_value = "Response despite cache failure"
            
            response = await chat_service.process_chat(sample_chat_request)
            
            # Should still work without cache
            assert isinstance(response, ChatResponse)
            assert "Response despite cache failure" in response.response
