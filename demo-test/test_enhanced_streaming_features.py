"""
Test suite for enhanced streaming features with GitHub-inspired best practices.
Tests custom event dispatching, usage tracking, retry mechanisms, and monitoring.
"""

import asyncio
import pytest
import time
import json
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from enhanced_streaming import (
    EventDispatcher,
    StreamEvent,
    UsageMetadata,
    StreamMonitor,
    enhanced_stream_wrapper,
    robust_llm_call,
    StreamingResponseWithEvents,
    UsageTracker,
    usage_tracker
)


class TestEventDispatcher:
    """Test the custom event dispatcher"""
    
    def setup_method(self):
        """Clear event listeners before each test"""
        from enhanced_streaming import EVENT_LISTENERS
        EVENT_LISTENERS.clear()
    
    def test_register_sync_listener(self):
        """Test registering synchronous event listeners"""
        events_received = []
        
        def sync_listener(event: StreamEvent):
            events_received.append(event)
        
        EventDispatcher.register_listener("test_event", sync_listener)
        
        # Check listener was registered
        from enhanced_streaming import EVENT_LISTENERS
        assert "test_event" in EVENT_LISTENERS
        assert len(EVENT_LISTENERS["test_event"]) == 1
    
    async def test_register_async_listener(self):
        """Test registering asynchronous event listeners"""
        events_received = []
        
        async def async_listener(event: StreamEvent):
            events_received.append(event)
        
        EventDispatcher.register_listener("test_async", async_listener)
        
        # Dispatch event
        await EventDispatcher.dispatch_custom_event(
            "test_async",
            {"test": "data"},
            session_id="test_session"
        )
        
        await asyncio.sleep(0.1)  # Allow async processing
        assert len(events_received) == 1
        assert events_received[0].event_type == "test_async"
        assert events_received[0].data == {"test": "data"}
        assert events_received[0].session_id == "test_session"
    
    async def test_dispatch_custom_event(self):
        """Test dispatching custom events"""
        events_received = []
        
        async def event_listener(event: StreamEvent):
            events_received.append(event)
        
        EventDispatcher.register_listener("custom_event", event_listener)
        
        # Dispatch event
        await EventDispatcher.dispatch_custom_event(
            "custom_event",
            {"key": "value", "number": 42},
            session_id="session_123",
            metadata={"source": "test"}
        )
        
        await asyncio.sleep(0.1)
        assert len(events_received) == 1
        
        event = events_received[0]
        assert event.event_type == "custom_event"
        assert event.data["key"] == "value"
        assert event.data["number"] == 42
        assert event.session_id == "session_123"
        assert event.metadata["source"] == "test"
        assert isinstance(event.timestamp, float)
    
    async def test_listener_error_handling(self):
        """Test error handling in event listeners"""
        events_received = []
        
        async def failing_listener(event: StreamEvent):
            raise ValueError("Test error")
        
        async def working_listener(event: StreamEvent):
            events_received.append(event)
        
        EventDispatcher.register_listener("error_test", failing_listener)
        EventDispatcher.register_listener("error_test", working_listener)
        
        # Dispatch event - should not crash despite failing listener
        await EventDispatcher.dispatch_custom_event("error_test", {"test": "data"})
        
        await asyncio.sleep(0.1)
        # Working listener should still receive the event
        assert len(events_received) == 1


class TestUsageMetadata:
    """Test usage metadata tracking"""
    
    def test_usage_metadata_creation(self):
        """Test creating usage metadata"""
        usage = UsageMetadata(
            input_tokens=100,
            output_tokens=150,
            total_tokens=250,
            reasoning_tokens=25,
            processing_time_ms=1500.0,
            model_name="gpt-4",
            session_id="session_123"
        )
        
        assert usage.input_tokens == 100
        assert usage.output_tokens == 150
        assert usage.total_tokens == 250
        assert usage.reasoning_tokens == 25
        assert usage.processing_time_ms == 1500.0
        assert usage.model_name == "gpt-4"
        assert usage.session_id == "session_123"
    
    def test_usage_metadata_update(self):
        """Test updating usage metadata"""
        usage1 = UsageMetadata(input_tokens=100, output_tokens=50, total_tokens=150)
        usage2 = UsageMetadata(input_tokens=50, output_tokens=75, total_tokens=125, reasoning_tokens=10)
        
        usage1.update(usage2)
        
        assert usage1.input_tokens == 150
        assert usage1.output_tokens == 125
        assert usage1.total_tokens == 275
        assert usage1.reasoning_tokens == 10


class TestStreamMonitor:
    """Test stream monitoring functionality"""
    
    async def test_stream_monitor_chunk_tracking(self):
        """Test monitoring stream chunks"""
        events_received = []
        
        async def event_listener(event: StreamEvent):
            events_received.append(event)
        
        EventDispatcher.register_listener("stream_chunk_received", event_listener)
        
        monitor = StreamMonitor("test_session")
        
        # Monitor some chunks
        await monitor.monitor_chunk("Hello")
        await monitor.monitor_chunk(" world")
        
        await asyncio.sleep(0.1)
        assert len(events_received) == 2
        
        # Check first chunk event
        event1 = events_received[0]
        assert event1.event_type == "stream_chunk_received"
        assert event1.data["chunk_number"] == 1
        assert event1.data["chunk_size"] == 5
        assert event1.data["session_id"] == "test_session"
        
        # Check second chunk event
        event2 = events_received[1]
        assert event2.data["chunk_number"] == 2
        assert event2.data["chunk_size"] == 6
    
    async def test_stream_monitor_completion(self):
        """Test monitoring stream completion"""
        events_received = []
        
        async def event_listener(event: StreamEvent):
            events_received.append(event)
        
        EventDispatcher.register_listener("stream_completed", event_listener)
        
        monitor = StreamMonitor("test_session")
        
        # Simulate some chunks
        await monitor.monitor_chunk("Hello")
        await monitor.monitor_chunk(" world")
        
        # Complete the stream
        total_content = "Hello world"
        await monitor.monitor_completion(total_content)
        
        await asyncio.sleep(0.1)
        completion_events = [e for e in events_received if e.event_type == "stream_completed"]
        assert len(completion_events) == 1
        
        event = completion_events[0]
        assert event.data["total_chunks"] == 2
        assert event.data["total_content_length"] == 11
        assert event.data["session_id"] == "test_session"
        assert event.data["estimated_tokens"] == 2  # "Hello" and "world"


class TestEnhancedStreamWrapper:
    """Test enhanced stream wrapper"""
    
    async def test_enhanced_stream_wrapper_success(self):
        """Test successful stream wrapping"""
        events_received = []
        
        async def event_listener(event: StreamEvent):
            events_received.append(event)
        
        EventDispatcher.register_listener("stream_started", event_listener)
        EventDispatcher.register_listener("stream_completed", event_listener)
        EventDispatcher.register_listener("stream_chunk_received", event_listener)
        
        # Create a test stream
        async def test_stream():
            for chunk in ["Hello", " ", "world", "!"]:
                yield chunk
        
        # Wrap the stream
        wrapped_stream = enhanced_stream_wrapper(
            test_stream(),
            session_id="test_session",
            model_name="test_model"
        )
        
        # Consume the stream
        chunks = []
        async for chunk in wrapped_stream:
            chunks.append(chunk)
        
        await asyncio.sleep(0.1)
        
        # Check collected chunks
        assert chunks == ["Hello", " ", "world", "!"]
        
        # Check events
        start_events = [e for e in events_received if e.event_type == "stream_started"]
        completion_events = [e for e in events_received if e.event_type == "stream_completed"]
        chunk_events = [e for e in events_received if e.event_type == "stream_chunk_received"]
        
        assert len(start_events) == 1
        assert len(completion_events) == 1
        assert len(chunk_events) == 4  # One for each chunk
        
        # Verify start event
        start_event = start_events[0]
        assert start_event.data["session_id"] == "test_session"
        assert start_event.data["model_name"] == "test_model"
        
        # Verify completion event
        completion_event = completion_events[0]
        assert completion_event.data["total_chunks"] == 4
        assert completion_event.data["session_id"] == "test_session"
    
    async def test_enhanced_stream_wrapper_cancellation(self):
        """Test stream wrapper handling cancellation"""
        events_received = []
        
        async def event_listener(event: StreamEvent):
            events_received.append(event)
        
        EventDispatcher.register_listener("stream_cancelled", event_listener)
        
        # Create a stream that will be cancelled
        async def slow_stream():
            for i in range(10):
                yield f"chunk_{i}"
                await asyncio.sleep(0.1)
        
        wrapped_stream = enhanced_stream_wrapper(
            slow_stream(),
            session_id="cancel_test"
        )
        
        # Start consuming but cancel early
        chunks = []
        try:
            async for chunk in wrapped_stream:
                chunks.append(chunk)
                if len(chunks) >= 2:
                    raise asyncio.CancelledError()
        except asyncio.CancelledError:
            pass
        
        await asyncio.sleep(0.1)
        
        # Check cancellation event
        cancel_events = [e for e in events_received if e.event_type == "stream_cancelled"]
        assert len(cancel_events) == 1
        
        cancel_event = cancel_events[0]
        assert cancel_event.data["session_id"] == "cancel_test"
        assert "partial_content_length" in cancel_event.data


class TestRobustLLMCall:
    """Test robust LLM call with retry mechanisms"""
    
    async def test_robust_llm_call_success(self):
        """Test successful LLM call"""
        events_received = []
        
        async def event_listener(event: StreamEvent):
            events_received.append(event)
        
        EventDispatcher.register_listener("llm_call_attempt", event_listener)
        EventDispatcher.register_listener("llm_call_success", event_listener)
        
        # Mock LLM function
        async def mock_llm(prompt: str):
            return f"Response to: {prompt}"
        
        result = await robust_llm_call(
            mock_llm,
            "Hello",
            session_id="test_session"
        )
        
        assert result == "Response to: Hello"
        
        await asyncio.sleep(0.1)
        
        # Check events
        attempt_events = [e for e in events_received if e.event_type == "llm_call_attempt"]
        success_events = [e for e in events_received if e.event_type == "llm_call_success"]
        
        assert len(attempt_events) == 1
        assert len(success_events) == 1
    
    async def test_robust_llm_call_with_retry(self):
        """Test LLM call with retries"""
        events_received = []
        
        async def event_listener(event: StreamEvent):
            events_received.append(event)
        
        EventDispatcher.register_listener("llm_call_failed", event_listener)
        EventDispatcher.register_listener("llm_call_success", event_listener)
        
        # Mock LLM function that fails twice then succeeds
        call_count = 0
        
        async def failing_llm(prompt: str):
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                raise ConnectionError("Network error")
            return f"Success: {prompt}"
        
        result = await robust_llm_call(
            failing_llm,
            "Test prompt",
            session_id="retry_test"
        )
        
        assert result == "Success: Test prompt"
        assert call_count == 3  # Failed twice, succeeded on third try
        
        await asyncio.sleep(0.1)
        
        # Check events
        failed_events = [e for e in events_received if e.event_type == "llm_call_failed"]
        success_events = [e for e in events_received if e.event_type == "llm_call_success"]
        
        assert len(failed_events) == 2  # Two failures
        assert len(success_events) == 1  # One success


class TestUsageTracker:
    """Test usage tracking system"""
    
    def setup_method(self):
        """Clear usage data before each test"""
        usage_tracker.clear_usage()
    
    def test_track_usage(self):
        """Test tracking usage data"""
        usage = UsageMetadata(
            input_tokens=100,
            output_tokens=50,
            total_tokens=150,
            session_id="session_1"        )
        
        usage_tracker.track_usage("session_1", usage)
        
        retrieved_usage = usage_tracker.get_usage("session_1")
        assert retrieved_usage is not None
        assert retrieved_usage.input_tokens == 100
        assert retrieved_usage.output_tokens == 50
        assert retrieved_usage.total_tokens == 150
    
    def test_track_multiple_sessions(self):
        """Test tracking multiple sessions"""
        usage1 = UsageMetadata(input_tokens=100, output_tokens=50, total_tokens=150)
        usage2 = UsageMetadata(input_tokens=200, output_tokens=75, total_tokens=275)
        
        usage_tracker.track_usage("session_1", usage1)
        usage_tracker.track_usage("session_2", usage2)
        
        total_usage = usage_tracker.get_total_usage()
        assert total_usage.input_tokens == 300
        assert total_usage.output_tokens == 125
        assert total_usage.total_tokens == 425
    
    def test_update_existing_session(self):
        """Test updating existing session usage"""
        usage1 = UsageMetadata(input_tokens=100, output_tokens=50, total_tokens=150)
        usage2 = UsageMetadata(input_tokens=50, output_tokens=25, total_tokens=75)
        
        usage_tracker.track_usage("session_1", usage1)
        usage_tracker.track_usage("session_1", usage2)  # Update same session
        
        retrieved_usage = usage_tracker.get_usage("session_1")
        assert retrieved_usage is not None
        assert retrieved_usage.input_tokens == 150  # 100 + 50
        assert retrieved_usage.output_tokens == 75   # 50 + 25
        assert retrieved_usage.total_tokens == 225   # 150 + 75


class TestStreamingResponseWithEvents:
    """Test enhanced streaming response"""
    
    async def test_streaming_response_with_events(self):
        """Test creating streaming response with events"""
        events_received = []
        
        async def event_listener(event: StreamEvent):
            events_received.append(event)
        
        EventDispatcher.register_listener("stream_started", event_listener)
        
        # Create test content
        async def test_content():
            for chunk in ["Hello", " ", "world"]:
                yield chunk
        
        # Create streaming response
        response = StreamingResponseWithEvents(
            content=test_content(),
            session_id="response_test",
            media_type="text/event-stream"
        )
        
        # Check headers
        assert response.headers["Content-Type"] == "text/event-stream"
        assert response.headers["X-Session-ID"] == "response_test"
        
        # Consume the response (this would normally be done by FastAPI)
        chunks = []
        async for chunk in response.body_iterator:
            chunks.append(chunk)
        
        assert chunks == ["Hello", " ", "world"]
        
        await asyncio.sleep(0.1)
        
        # Check that stream events were dispatched
        start_events = [e for e in events_received if e.event_type == "stream_started"]
        assert len(start_events) >= 1


class TestIntegration:
    """Integration tests for enhanced streaming features"""
    
    def setup_method(self):
        """Setup for integration tests"""
        from enhanced_streaming import EVENT_LISTENERS
        EVENT_LISTENERS.clear()
        usage_tracker.clear_usage()
    
    async def test_full_streaming_workflow(self):
        """Test complete streaming workflow with all features"""
        events_received = []
        
        async def comprehensive_listener(event: StreamEvent):
            events_received.append(event)
        
        # Register listeners for all event types
        for event_type in ["stream_started", "stream_chunk_received", "stream_completed", 
                          "llm_call_attempt", "llm_call_success"]:
            EventDispatcher.register_listener(event_type, comprehensive_listener)
        
        # Mock LLM function with usage tracking
        async def mock_llm_with_usage(prompt: str):
            # Simulate token usage
            usage = UsageMetadata(
                input_tokens=len(prompt.split()),
                output_tokens=10,
                total_tokens=len(prompt.split()) + 10,
                model_name="test_model",
                session_id="integration_test"
            )
            usage_tracker.track_usage("integration_test", usage)
            
            # Return streaming content
            async def content_generator():
                for word in ["This", " is", " a", " test", " response"]:
                    yield word
            
            return content_generator()
        
        # Execute robust LLM call
        stream_generator = await robust_llm_call(
            mock_llm_with_usage,
            "Test prompt for integration",
            session_id="integration_test"
        )
        
        # Wrap with enhanced streaming
        enhanced_stream = enhanced_stream_wrapper(
            stream_generator,
            session_id="integration_test",
            model_name="test_model"
        )
        
        # Create streaming response
        response = StreamingResponseWithEvents(
            content=enhanced_stream,
            session_id="integration_test",
            media_type="text/event-stream"
        )
        
        # Consume the response
        chunks = []
        async for chunk in response.body_iterator:
            chunks.append(chunk)
        
        await asyncio.sleep(0.1)
        
        # Verify results
        assert chunks == ["This", " is", " a", " test", " response"]
        
        # Verify usage tracking
        usage = usage_tracker.get_usage("integration_test")
        assert usage is not None
        assert usage.input_tokens == 4  # "Test prompt for integration"
        assert usage.output_tokens == 10
        assert usage.model_name == "test_model"
        
        # Verify events were dispatched
        event_types = [e.event_type for e in events_received]
        assert "llm_call_attempt" in event_types
        assert "llm_call_success" in event_types
        assert "stream_started" in event_types
        assert "stream_completed" in event_types
        assert "stream_chunk_received" in event_types
        
        # Verify stream chunk events
        chunk_events = [e for e in events_received if e.event_type == "stream_chunk_received"]
        assert len(chunk_events) == 5  # One for each chunk


# Performance tests
class TestPerformance:
    """Performance tests for enhanced streaming features"""
    
    async def test_event_dispatcher_performance(self):
        """Test event dispatcher performance with many listeners"""
        listeners_count = 100
        events_received = 0
        
        async def counting_listener(event: StreamEvent):
            nonlocal events_received
            events_received += 1
        
        # Register many listeners
        for i in range(listeners_count):
            EventDispatcher.register_listener("performance_test", counting_listener)
        
        start_time = time.time()
        
        # Dispatch events
        for i in range(10):
            await EventDispatcher.dispatch_custom_event("performance_test", {"test": i})
        
        await asyncio.sleep(0.1)  # Allow async processing
        
        end_time = time.time()
        
        # Performance assertions
        assert events_received == listeners_count * 10
        assert (end_time - start_time) < 1.0  # Should complete in under 1 second
    
    async def test_usage_tracker_performance(self):
        """Test usage tracker performance with many sessions"""
        sessions_count = 1000
        
        start_time = time.time()
        
        # Track usage for many sessions
        for i in range(sessions_count):
            usage = UsageMetadata(
                input_tokens=100,
                output_tokens=50,
                total_tokens=150,
                session_id=f"session_{i}"
            )
            usage_tracker.track_usage(f"session_{i}", usage)
        
        # Calculate total usage
        total_usage = usage_tracker.get_total_usage()
        
        end_time = time.time()
        
        # Performance and correctness assertions
        assert total_usage.input_tokens == sessions_count * 100
        assert total_usage.output_tokens == sessions_count * 50
        assert total_usage.total_tokens == sessions_count * 150
        assert (end_time - start_time) < 1.0  # Should complete in under 1 second


if __name__ == "__main__":
    # Run tests with asyncio
    import pytest
    pytest.main([__file__, "-v"])
