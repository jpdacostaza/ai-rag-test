"""
Integration example for enhanced streaming features with GitHub-inspired best practices.
Demonstrates how to integrate the new streaming capabilities with the main FastAPI application.
"""

import asyncio
import time
import sys
import os
from typing import Dict, Any, AsyncGenerator, Optional
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import our enhanced streaming utilities
from enhanced_streaming import (
    EventDispatcher,
    StreamEvent,
    UsageMetadata,
    enhanced_stream_wrapper,
    robust_llm_call,
    StreamingResponseWithEvents,
    usage_tracker
)

# Example: Enhanced chat endpoint with new streaming features
async def enhanced_chat_completion(
    prompt: str,
    model: str = "gpt-3.5-turbo",
    session_id: Optional[str] = None
) -> StreamingResponseWithEvents:
    """
    Enhanced chat completion with comprehensive monitoring and event dispatching
    """
    
    # Generate session ID if not provided
    if not session_id:
        import uuid
        session_id = str(uuid.uuid4())
      # Mock LLM function with usage tracking
    async def mock_llm_call(prompt: str) -> AsyncGenerator[str, None]:
        """Mock LLM call that returns a generator"""
        async def generator():
            words = [
                "I", " understand", " your", " question", " about", " enhanced", 
                " streaming", " features.", " Let", " me", " provide", " a", 
                " comprehensive", " response", " with", " proper", " monitoring", 
                " and", " event", " dispatching."
            ]
            
            for word in words:
                await asyncio.sleep(0.1)  # Simulate processing time
                yield word
            
            # Track usage metadata after completion
            usage = UsageMetadata(
                input_tokens=len(prompt.split()),
                output_tokens=len(words),
                total_tokens=len(prompt.split()) + len(words),
                model_name=model,
                session_id=session_id,
                processing_time_ms=len(words) * 100  # 100ms per word
            )
            usage_tracker.track_usage(session_id, usage)
        
        return generator()
    
    # Get the stream generator
    stream_generator = await mock_llm_call(prompt)
    
    # Wrap with enhanced monitoring
    enhanced_stream = enhanced_stream_wrapper(
        stream_generator,
        session_id=session_id,
        model_name=model,
        monitor_enabled=True
    )
    
    # Return enhanced streaming response
    return StreamingResponseWithEvents(
        content=enhanced_stream,
        session_id=session_id,
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Model": model
        }
    )

# Example: Event listeners for monitoring
async def log_stream_metrics(event: StreamEvent) -> None:
    """Log streaming metrics for monitoring"""
    if event.event_type == "stream_completed":
        data = event.data
        print(f"Stream completed for session {event.session_id}:")
        print(f"  - Total chunks: {data.get('total_chunks', 0)}")
        print(f"  - Content length: {data.get('total_content_length', 0)}")
        print(f"  - Processing time: {data.get('processing_time_ms', 0):.2f}ms")
        print(f"  - Estimated tokens: {data.get('estimated_tokens', 0)}")

async def track_llm_performance(event: StreamEvent) -> None:
    """Track LLM performance metrics"""
    if event.event_type == "llm_call_success":
        data = event.data
        print(f"LLM call succeeded for session {event.session_id}:")
        print(f"  - Function: {data.get('function', 'unknown')}")
        print(f"  - Duration: {data.get('duration_ms', 0):.2f}ms")
    elif event.event_type == "llm_call_failed":
        data = event.data
        print(f"LLM call failed for session {event.session_id}:")
        print(f"  - Function: {data.get('function', 'unknown')}")
        print(f"  - Error: {data.get('error', 'unknown')}")
        print(f"  - Duration: {data.get('duration_ms', 0):.2f}ms")

# Setup event listeners
def setup_monitoring():
    """Setup comprehensive monitoring event listeners"""
    EventDispatcher.register_listener("stream_completed", log_stream_metrics)
    EventDispatcher.register_listener("llm_call_success", track_llm_performance)
    EventDispatcher.register_listener("llm_call_failed", track_llm_performance)

# Example: Usage analytics endpoint
async def get_usage_analytics() -> Dict[str, Any]:
    """Get comprehensive usage analytics"""
    total_usage = usage_tracker.get_total_usage()
    
    return {
        "total_usage": {
            "input_tokens": total_usage.input_tokens,
            "output_tokens": total_usage.output_tokens,
            "total_tokens": total_usage.total_tokens,
            "processing_time_ms": total_usage.processing_time_ms
        },
        "sessions_count": len(usage_tracker._usage_data),
        "average_tokens_per_session": (
            total_usage.total_tokens / len(usage_tracker._usage_data) 
            if usage_tracker._usage_data else 0
        ),
        "average_processing_time_ms": (
            total_usage.processing_time_ms / len(usage_tracker._usage_data)
            if usage_tracker._usage_data else 0
        )
    }

# Example: Session-specific usage endpoint
async def get_session_usage(session_id: str) -> Dict[str, Any]:
    """Get usage data for a specific session"""
    usage = usage_tracker.get_usage(session_id)
    
    if not usage:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {
        "session_id": session_id,
        "input_tokens": usage.input_tokens,
        "output_tokens": usage.output_tokens,
        "total_tokens": usage.total_tokens,
        "processing_time_ms": usage.processing_time_ms,
        "model_name": usage.model_name
    }

# Demonstration function
async def demonstrate_enhanced_streaming():
    """Demonstrate the enhanced streaming features"""
    print("🚀 Enhanced Streaming Features Demonstration")
    print("=" * 50)
    
    # Setup monitoring
    setup_monitoring()
    
    # Test enhanced chat completion
    print("\n1. Testing Enhanced Chat Completion...")
    response = await enhanced_chat_completion(
        prompt="What are the benefits of enhanced streaming?",
        model="gpt-4",
        session_id="demo_session_1"
    )
      # Consume the streaming response
    print("\nStreaming response:")
    content = ""
    async for chunk in response.body_iterator:
        chunk_str = chunk.decode('utf-8') if isinstance(chunk, bytes) else str(chunk)
        content += chunk_str
        print(chunk_str, end="", flush=True)
    
    print(f"\n\nComplete response: {content}")
    
    # Wait for async events to complete
    await asyncio.sleep(0.5)
    
    # Show usage analytics
    print("\n2. Usage Analytics:")
    analytics = await get_usage_analytics()
    for key, value in analytics.items():
        print(f"   {key}: {value}")
    
    # Show session-specific usage
    print("\n3. Session-specific Usage:")
    session_usage = await get_session_usage("demo_session_1")
    for key, value in session_usage.items():
        print(f"   {key}: {value}")
    
    # Test retry mechanism
    print("\n4. Testing Retry Mechanism...")
    
    call_count = 0
    async def failing_function(prompt: str):
        nonlocal call_count
        call_count += 1
        if call_count <= 2:
            raise ConnectionError("Simulated network error")
        return f"Success after {call_count} attempts: {prompt}"
    
    try:
        result = await robust_llm_call(
            failing_function,
            "Test retry mechanism",
            session_id="retry_demo"
        )
        print(f"Retry result: {result}")
    except Exception as e:
        print(f"Retry failed: {e}")
    
    print("\n✅ Enhanced Streaming Features Demonstration Complete!")

# Integration with FastAPI
def create_enhanced_app() -> FastAPI:
    """Create FastAPI app with enhanced streaming endpoints"""
    app = FastAPI(title="Enhanced Streaming API", version="1.0.0")    
    # Setup monitoring on startup
    @app.on_event("startup")
    async def startup_event():
        setup_monitoring()
        print("Enhanced streaming monitoring setup complete")
    
    @app.post("/chat/stream")
    async def stream_chat(
        prompt: str,
        model: str = "gpt-3.5-turbo",
        session_id: Optional[str] = None
    ):
        """Enhanced streaming chat endpoint"""
        return await enhanced_chat_completion(prompt, model, session_id)
    
    @app.get("/analytics/usage")
    async def usage_analytics():
        """Get usage analytics"""
        return await get_usage_analytics()
    
    @app.get("/analytics/usage/{session_id}")
    async def session_usage(session_id: str):
        """Get session-specific usage"""
        return await get_session_usage(session_id)
    
    @app.delete("/analytics/usage/{session_id}")
    async def clear_session_usage(session_id: str):
        """Clear usage data for a session"""
        usage_tracker.clear_usage(session_id)
        return {"message": f"Usage data cleared for session {session_id}"}
    
    @app.delete("/analytics/usage")
    async def clear_all_usage():
        """Clear all usage data"""
        usage_tracker.clear_usage()
        return {"message": "All usage data cleared"}
    
    return app

# Main execution
if __name__ == "__main__":
    # Run the demonstration
    asyncio.run(demonstrate_enhanced_streaming())
