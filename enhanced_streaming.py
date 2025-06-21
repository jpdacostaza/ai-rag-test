"""
Enhanced streaming utilities with GitHub-inspired best practices.
Implements custom event dispatching, usage tracking, and retry mechanisms.
"""

import asyncio
import time
import json
from typing import Dict, List, Optional, Any, AsyncGenerator, Callable, Union, Awaitable
from dataclasses import dataclass, asdict
from fastapi import HTTPException
from fastapi.responses import StreamingResponse
import logging
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = logging.getLogger(__name__)

# Global event listeners registry
EVENT_LISTENERS: Dict[str, List[Callable]] = {}

@dataclass
class UsageMetadata:
    """Comprehensive usage metadata tracking"""
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    reasoning_tokens: Optional[int] = None
    processing_time_ms: float = 0.0
    model_name: Optional[str] = None
    session_id: Optional[str] = None
    
    def update(self, other: 'UsageMetadata') -> None:
        """Update usage metadata with another instance"""
        self.input_tokens += other.input_tokens
        self.output_tokens += other.output_tokens
        self.total_tokens += other.total_tokens
        if other.reasoning_tokens:
            self.reasoning_tokens = (self.reasoning_tokens or 0) + other.reasoning_tokens
        self.processing_time_ms += other.processing_time_ms

@dataclass
class StreamEvent:
    """Custom stream event structure"""
    event_type: str
    data: Dict[str, Any]
    timestamp: float
    session_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class EventDispatcher:
    """Custom event dispatcher for streaming operations"""
    
    @staticmethod
    def register_listener(event_type: str, callback: Union[Callable[[StreamEvent], None], Callable[[StreamEvent], Awaitable[None]]]) -> None:
        """Register an event listener"""
        if event_type not in EVENT_LISTENERS:
            EVENT_LISTENERS[event_type] = []
        EVENT_LISTENERS[event_type].append(callback)
    
    @staticmethod
    async def dispatch_event(event: StreamEvent) -> None:
        """Dispatch an event to all registered listeners"""
        listeners = EVENT_LISTENERS.get(event.event_type, [])
        for listener in listeners:
            try:
                if asyncio.iscoroutinefunction(listener):
                    await listener(event)
                else:
                    listener(event)
            except Exception as e:
                logger.error(f"Error in event listener for {event.event_type}: {e}")
    
    @staticmethod
    async def dispatch_custom_event(
        event_type: str, 
        data: Dict[str, Any], 
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Dispatch a custom event"""
        event = StreamEvent(
            event_type=event_type,
            data=data,
            timestamp=time.time(),
            session_id=session_id,
            metadata=metadata or {}
        )
        await EventDispatcher.dispatch_event(event)

class StreamMonitor:
    """Non-intrusive stream monitoring"""
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.chunk_count = 0
        self.start_time = time.time()
        self.usage = UsageMetadata(session_id=session_id)
    
    async def monitor_chunk(self, chunk: str, metadata: Optional[Dict] = None) -> None:
        """Monitor a streaming chunk without blocking"""
        self.chunk_count += 1
        
        # Dispatch monitoring event
        await EventDispatcher.dispatch_custom_event(
            "stream_chunk_received",
            {
                "chunk_number": self.chunk_count,
                "chunk_size": len(chunk),
                "session_id": self.session_id,
                "elapsed_time": time.time() - self.start_time
            },
            session_id=self.session_id,
            metadata=metadata
        )
    
    async def monitor_completion(self, total_content: str) -> None:
        """Monitor stream completion"""
        total_time = time.time() - self.start_time
        self.usage.processing_time_ms = total_time * 1000
        self.usage.output_tokens = len(total_content.split())  # Simple token estimation
        
        await EventDispatcher.dispatch_custom_event(
            "stream_completed",
            {
                "total_chunks": self.chunk_count,
                "total_content_length": len(total_content),
                "processing_time_ms": self.usage.processing_time_ms,
                "estimated_tokens": self.usage.output_tokens,
                "session_id": self.session_id
            },
            session_id=self.session_id
        )

async def enhanced_stream_wrapper(
    original_stream: AsyncGenerator[str, None],
    session_id: str,
    model_name: Optional[str] = None,
    monitor_enabled: bool = True
) -> AsyncGenerator[str, None]:
    """Enhanced stream wrapper with monitoring and event dispatching"""
    monitor = StreamMonitor(session_id) if monitor_enabled else None
    total_content = ""
    
    # Dispatch stream start event
    await EventDispatcher.dispatch_custom_event(
        "stream_started",
        {
            "session_id": session_id,
            "model_name": model_name,
            "monitor_enabled": monitor_enabled
        },
        session_id=session_id
    )
    
    try:
        async for chunk in original_stream:
            total_content += chunk
            
            if monitor:
                await monitor.monitor_chunk(chunk, {"model_name": model_name})
            
            yield chunk
            
    except asyncio.CancelledError:
        logger.warning(f"Stream cancelled for session {session_id}")
        await EventDispatcher.dispatch_custom_event(
            "stream_cancelled",
            {"session_id": session_id, "partial_content_length": len(total_content)},
            session_id=session_id
        )
        raise
    except Exception as e:
        logger.error(f"Stream error for session {session_id}: {e}")
        await EventDispatcher.dispatch_custom_event(
            "stream_error",
            {"session_id": session_id, "error": str(e), "partial_content_length": len(total_content)},
            session_id=session_id
        )
        raise
    finally:
        if monitor:
            await monitor.monitor_completion(total_content)

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=8),
    retry=retry_if_exception_type((ConnectionError, TimeoutError, HTTPException))
)
async def robust_llm_call(
    llm_function: Callable,
    *args,
    session_id: Optional[str] = None,
    **kwargs
) -> Any:
    """Robust LLM call with retry mechanisms"""
    attempt_start = time.time()
    
    try:
        if session_id:
            await EventDispatcher.dispatch_custom_event(
                "llm_call_attempt",
                {"session_id": session_id, "function": llm_function.__name__},
                session_id=session_id
            )
        
        result = await llm_function(*args, **kwargs)
        
        if session_id:
            await EventDispatcher.dispatch_custom_event(
                "llm_call_success",
                {
                    "session_id": session_id,
                    "function": llm_function.__name__,
                    "duration_ms": (time.time() - attempt_start) * 1000
                },
                session_id=session_id
            )
        
        return result
        
    except Exception as e:
        if session_id:
            await EventDispatcher.dispatch_custom_event(
                "llm_call_failed",
                {
                    "session_id": session_id,
                    "function": llm_function.__name__,
                    "error": str(e),
                    "duration_ms": (time.time() - attempt_start) * 1000
                },
                session_id=session_id
            )
        raise

class StreamingResponseWithEvents(StreamingResponse):
    """Enhanced StreamingResponse with proper content-type and event support"""
    
    def __init__(
        self,
        content: AsyncGenerator[str, None],
        session_id: str,
        status_code: int = 200,
        headers: Optional[Dict[str, str]] = None,
        media_type: Optional[str] = None,
        background = None,
        monitor_enabled: bool = True
    ):
        # Set proper content-type for streaming
        final_headers = headers or {}
        if media_type:
            final_headers["Content-Type"] = media_type
        elif "Content-Type" not in final_headers:
            final_headers["Content-Type"] = "text/event-stream"
        
        # Add session ID to headers
        final_headers["X-Session-ID"] = session_id
        
        # Wrap content with enhanced monitoring
        enhanced_content = enhanced_stream_wrapper(
            content, 
            session_id=session_id,
            monitor_enabled=monitor_enabled
        )
        
        super().__init__(
            content=enhanced_content,
            status_code=status_code,
            headers=final_headers,
            background=background
        )

# Usage tracking utilities
class UsageTracker:
    """Global usage tracking system"""
    
    _instance = None
    _usage_data: Dict[str, UsageMetadata] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def track_usage(self, session_id: str, usage: UsageMetadata) -> None:
        """Track usage for a session"""
        if session_id in self._usage_data:
            self._usage_data[session_id].update(usage)
        else:
            self._usage_data[session_id] = usage
    
    def get_usage(self, session_id: str) -> Optional[UsageMetadata]:
        """Get usage data for a session"""
        return self._usage_data.get(session_id)
    
    def get_total_usage(self) -> UsageMetadata:
        """Get total usage across all sessions"""
        total = UsageMetadata()
        for usage in self._usage_data.values():
            total.update(usage)
        return total
    
    def clear_usage(self, session_id: Optional[str] = None) -> None:
        """Clear usage data"""
        if session_id:
            self._usage_data.pop(session_id, None)
        else:
            self._usage_data.clear()

# Global usage tracker instance
usage_tracker = UsageTracker()

# Example event listeners
async def log_stream_events(event: StreamEvent) -> None:
    """Example event listener that logs stream events"""
    logger.info(f"Stream Event: {event.event_type} - {event.data}")

def setup_default_listeners():
    """Setup default event listeners"""
    EventDispatcher.register_listener("stream_started", log_stream_events)
    EventDispatcher.register_listener("stream_completed", log_stream_events)
    EventDispatcher.register_listener("stream_error", log_stream_events)
    EventDispatcher.register_listener("stream_cancelled", log_stream_events)

# Initialize default listeners
setup_default_listeners()
