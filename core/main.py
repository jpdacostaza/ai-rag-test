"""
Main FastAPI application with modular structure.
"""

import json
import os
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Dict

from fastapi import FastAPI, Request, Body, Depends, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse, PlainTextResponse
from starlette.middleware.base import BaseHTTPMiddleware
import asyncio

# CRITICAL: CPU-only mode enforcement
# Note: CPU-only enforcement moved to environment variables and package configuration

# Import modules
from config.config_unified import DEFAULT_MODEL, OLLAMA_BASE_URL
from handlers import create_exception_handlers

# Initialize unified logging EARLY, before importing other modules
from core.unified_logging import setup_logging, get_logger, log_api_request, log_service_status, set_correlation_id, get_correlation_id
setup_logging()

# Diagnostics: report process and handler info once at import time
import logging as _logging_diag, os as _os_diag
if not getattr(_os_diag, "_LOG_IMPORT_DIAG_DONE", False):
    root_handlers = _logging_diag.getLogger().handlers
    print(f"[DIAG] Process PID={_os_diag.getpid()} handler_count={len(root_handlers)} handlers={[type(h).__name__ for h in root_handlers]}", flush=True)
    _os_diag._LOG_IMPORT_DIAG_DONE = True

# Environment variable to control stream debug logging (can cause performance overhead)
ENABLE_STREAM_DEBUG = os.getenv("ENABLE_STREAM_DEBUG", "false").lower() == "true"
from models.models import ChatRequest, ChatResponse, OpenAIMessage, OpenAIChatRequest, ModelListResponse, ErrorResponse
from routes import health_router, chat_router, models_router, upload_router, debug_router
from routes import memory_router
from routes.tools import tools_router
from services.llm_service import call_llm, call_llm_stream
print("[MAIN.PY] LLM service imported successfully!", flush=True)
from services.streaming_service import streaming_service, STREAM_SESSION_STOP, STREAM_SESSION_METADATA
from services.user_identity import resolve_user_id
from core.startup import startup_event

# Get logger after setup
logger = get_logger(__name__)

# Disable uvicorn access logging completely - must be done early
import logging
uvicorn_access = logging.getLogger("uvicorn.access")
uvicorn_access.disabled = True
uvicorn_access.setLevel(logging.CRITICAL)
uvicorn_access.propagate = False

uvicorn_error = logging.getLogger("uvicorn.error") 
uvicorn_error.disabled = True
uvicorn_error.setLevel(logging.CRITICAL)
uvicorn_error.propagate = False

uvicorn_main = logging.getLogger("uvicorn")
uvicorn_main.disabled = True
uvicorn_main.setLevel(logging.CRITICAL)
uvicorn_main.propagate = False

# Import memory system
# TODO: Enhanced Memory System is available via pipeline integration, not direct import
# The memory functionality is now provided through OpenWebUI pipeline filters
# Legacy fallback through database_manager is still available
MEMORY_AVAILABLE = False  # Using pipeline-based memory instead
log_service_status("MEMORY", "info", "Using Enhanced Memory Pipeline (not direct import)")

# Import existing routers
from services.model_manager import router as model_manager_router, initialize_model_cache
from routes.chat import get_user_memories

# Import database and other dependencies
from services.database_manager import db_manager, get_embedding, index_user_document
from services.database_manager import get_cache, set_cache, get_chat_history, store_chat_history, get_database_health
from core.error_handler import safe_execute, log_error


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan events."""
    global global_memory_service
    
    # Startup
    log_service_status("APP", "info", "Starting application lifespan")
    try:
        # Run the main startup event (includes model cache initialization)
        await startup_event(app)
        
        # Initialize Memory Service (complementary to Enhanced Memory Pipeline)
        # The Memory Service provides unified interface for routes and API endpoints
        # while Enhanced Memory Pipeline handles OpenWebUI filter integration
        log_service_status("APP", "info", "Initializing Memory Service...")
        initialize_memory_service()
        
        # Model cache already initialized in startup_event, no need to duplicate
        log_service_status("APP", "ready", "Application startup completed successfully")
    except Exception as e:
        log_service_status("APP", "error", f"Error during application startup: {e}")
        raise

    yield

    # Shutdown
    log_service_status("APP", "info", "Application shutting down")
    global_memory_service = None


# Global memory service instance
global_memory_service = None


def initialize_memory_service():
    """Initialize the global memory service instance."""
    global global_memory_service
    if global_memory_service is None:
        try:
            from services.memory_service import get_memory_service
            global_memory_service = get_memory_service()
            # Avoid duplicate success log; lifespan already logs application readiness
            # Use service status if specific memory success visibility needed
            from core.unified_logging import log_service_status as _lss
            _lss("MEMORY", "ready", "Memory service initialized successfully")
        except Exception as e:
            logger.warning(f"[WARN] Memory service initialization failed: {e}")
            global_memory_service = None
    return global_memory_service


def get_memory_service_or_legacy():
    """
    Get memory service instance or None for legacy fallback.
    
    Returns:
        MemoryService instance if available, None otherwise.
        The Memory Service has built-in fallback capabilities.
    """
    global global_memory_service
    
    # Try to initialize if not already done
    if global_memory_service is None:
        global_memory_service = initialize_memory_service()
    
    return global_memory_service


# Import security configuration
from core.security import configure_security, perform_environment_validation
from core.config_validation import validate_configuration

# Validate environment variables at startup (non-fatal)
perform_environment_validation()
validate_configuration()

"""FastAPI application instance and metrics instrumentation."""
app = FastAPI(
    title="AI Backend API", description="Modular FastAPI backend for AI-powered application", lifespan=lifespan
)

from core.metrics import (
    METRICS_ENABLED,
    generate_latest,
    CONTENT_TYPE_LATEST,
    chat_requests_total,
    memory_injections_total,
    streaming_heartbeats_total,
    llm_request_latency_seconds,
    llm_stream_latency_seconds,
    llm_request_errors_total,
)
from utilities.circuit_breaker import get_llm_breaker

@app.get("/metrics")
async def metrics():  # Minimal metrics endpoint
    if not METRICS_ENABLED:
        return PlainTextResponse("metrics_disabled", status_code=200)
    return PlainTextResponse(generate_latest(), media_type=CONTENT_TYPE_LATEST)

# Configure security middleware first
configure_security(app)

# Add performance monitoring middleware
from middleware.performance_middleware import PerformanceMiddleware
from middleware.rate_limit_middleware import RateLimitMiddleware
app.add_middleware(PerformanceMiddleware, enable_memory_tracking=True, enable_cpu_tracking=True)
app.add_middleware(RateLimitMiddleware, limit_per_minute=120)

# Add exception handlers
exception_handlers = create_exception_handlers()
for exception_type, handler in exception_handlers:
    app.add_exception_handler(exception_type, handler)


# Timeout middleware to prevent long-running requests
class TimeoutMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, timeout: int = 45):
        super().__init__(app)
        self.timeout = timeout

    async def dispatch(self, request: Request, call_next):
        try:
            return await asyncio.wait_for(call_next(request), timeout=self.timeout)
        except asyncio.TimeoutError:
            from core.error_response import build_error
            return build_error(
                code="request_timeout",
                message=f"Request exceeded timeout of {self.timeout} seconds",
                status=504,
                details={"timeout_seconds": self.timeout, "suggestion": "Simplify or split the request"},
                retryable=True,
            )


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """Assign or propagate a correlation ID per request and expose to logging + response headers."""
    def __init__(self, app):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        incoming = request.headers.get("x-correlation-id") or request.headers.get("x-request-id")
        cid = incoming or str(uuid.uuid4())
        # store in context and request.state
        set_correlation_id(cid)
        request.state.correlation_id = cid
        try:
            response = await call_next(request)
        finally:
            # no cleanup needed; context var will be overwritten next request
            pass
        if hasattr(response, 'headers'):
            response.headers['X-Correlation-ID'] = cid
        return response

# Add correlation + timeout middleware (order: correlation first so others can read it)
app.add_middleware(CorrelationIdMiddleware)
app.add_middleware(TimeoutMiddleware, timeout=45)

# Include route modules
app.include_router(health_router)
app.include_router(chat_router)
app.include_router(models_router)

# Include additional routers
app.include_router(upload_router)
app.include_router(debug_router)
app.include_router(memory_router)
app.include_router(tools_router)
app.include_router(model_manager_router)

# Include gateway router (re-enabled)
from routes import gateway_router
app.include_router(gateway_router)

# Version endpoint (simple build metadata; extend with git hash if injected at build time)
@app.get("/version")
async def version():
    commit = os.getenv("GIT_COMMIT")
    if not commit:
        # Best-effort local git lookup (non-fatal)
        try:
            import subprocess
            commit = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], stderr=subprocess.DEVNULL).decode().strip()
        except Exception:
            commit = "unknown"
    build = {
        "version": os.getenv("APP_VERSION", "0.0.0"),
        "commit": commit,
        "build_time": os.getenv("BUILD_TIME", "unknown"),
    }
    # Surface active memory provider for quick diagnostics
    try:
        from services.memory_service import get_memory_service
        provider = get_memory_service().provider_type.value
    except Exception:
        provider = None
    return {"build": build, "memory_provider": provider}


# OpenAI-compatible chat completions endpoint
@app.post("/v1/chat/completions")
async def openai_chat_completions(request: Request, body: dict = Body(...)):
    """
    OpenAI-compatible chat completions endpoint for OpenWebUI, with streaming support.
    """
    start_time = time.time()
    
    # Initialize variables early to avoid scope issues
    messages = []
    user_id = None

    # Validate required fields
    if "model" not in body or not body["model"]:
        raise HTTPException(status_code=400, detail="Missing required field: 'model'")

    if "messages" not in body or not isinstance(body["messages"], list) or len(body["messages"]) == 0:
        raise HTTPException(
            status_code=400, detail="Missing or invalid required field: 'messages' (must be a non-empty list)"
        )

    # Validate messages structure and extract early to avoid scope issues
    messages = body.get("messages", [])
    for i, message in enumerate(messages):
        if not isinstance(message, dict):
            raise HTTPException(status_code=400, detail=f"Message at index {i} must be an object")
        if "role" not in message or "content" not in message:
            raise HTTPException(status_code=400, detail=f"Message at index {i} must have 'role' and 'content' fields")

    user_id = resolve_user_id(request, body, messages)
    if user_id:
        log_service_status("AUTH", "info", f"Identified user: {user_id}")
    else:
        log_service_status("AUTH", "warning", "No user identification resolved")
    
    stream = body.get("stream", False)

    # Use the last user message as the prompt
    user_message = ""
    for m in reversed(messages):
        if m.get("role") == "user":
            content = m.get("content", "")

            # Handle multi-modal content (list format)
            if isinstance(content, list):
                # Extract text from multi-modal content
                text_parts = []
                has_non_text_content = False
                has_any_content = False

                for part in content:
                    if isinstance(part, dict):
                        has_any_content = True
                        if part.get("type") == "text":
                            text_content = part.get("text", "").strip()
                            if text_content:  # Only add non-empty text
                                text_parts.append(text_content)
                        elif part.get("type") in ["image_url", "image"]:
                            has_non_text_content = True

                user_message = " ".join(text_parts).strip()

                # Handle empty text cases
                if not user_message:
                    if has_non_text_content:
                        # Has images but no text
                        user_message = "Please analyze this image."
                    elif has_any_content:
                        # Has content parts but all text is empty - provide generic fallback
                        user_message = "Please respond to this message."

            elif isinstance(content, str):
                # Handle simple string content
                user_message = content.strip()
                # Provide fallback for empty string
                if not user_message:
                    user_message = "Please respond to this message."
            else:
                # Handle other content types by converting to string
                user_message = str(content).strip()
                # Provide fallback for empty content
                if not user_message:
                    user_message = "Please respond to this message."
            break

    if not user_message:
        raise HTTPException(status_code=400, detail="No user message found in the messages list")

    # Streaming support
    if stream:
        session_id = f"{user_id}:{int(time.time())}"
        streaming_service.create_session(session_id, user_id, body.get("model", DEFAULT_MODEL))

        async def event_stream():
            """Enhanced event stream with proper error handling and cleanup."""
            try:
                log_service_status("STREAM", "info", f"Starting stream for session {session_id}")

                # --- Retrieve chat history and memory for streaming ---
                try:
                    history = await get_chat_history(f"user:{user_id}", limit=10)
                except Exception as e:
                    # Log cache error and continue without cache - non-blocking
                    log_service_status("CACHE", "warning", f"Cache operation failed for user {user_id}, continuing without cache: {e}")
                    history = []

                # --- Memory Integration: Retrieve relevant memories ---
                memory_context = ""
                memory_service = get_memory_service_or_legacy()
                if memory_service:
                    try:
                        # Get relevant memories based on current user message
                        relevant_memories = await memory_service.get_relevant_memories(
                            user_id=user_id,
                            context=user_message,
                            max_memories=5
                        )
                        if relevant_memories:
                            memory_context = memory_service.format_memories_for_injection(relevant_memories)
                            log_service_status("MEMORY", "info", f"Retrieved {len(relevant_memories)} memories for user {user_id}")
                    except Exception as e:
                        log_service_status("MEMORY", "error", f"Error retrieving memories for user {user_id}: {e}")
                else:
                    log_service_status("MEMORY", "warning", "Memory service not available, using legacy system only")

                # Build enhanced message format with chat history for streaming
                stream_messages = []

                # Add system message first (if any) with memory context injection + delimiters
                system_messages = [m for m in messages if m.get("role") == "system"]
                if system_messages:
                    # Inject memory context into existing system message
                    enhanced_system_message = system_messages[0].copy()
                    original_content = enhanced_system_message.get("content", "")
                    if memory_context:
                        memory_injections_total.inc()
                        enhanced_system_message["content"] = f"<BEGIN_MEMORY_CONTEXT>\n{memory_context}\n<END_MEMORY_CONTEXT>\n{original_content}"
                    stream_messages.append(enhanced_system_message)
                else:
                    # No system prompts/personas - just use memory context if available
                    if memory_context:
                        memory_injections_total.inc()
                        system_content = f"<BEGIN_MEMORY_CONTEXT>\n{memory_context}\n<END_MEMORY_CONTEXT>"
                        stream_messages.append({"role": "system", "content": system_content})

                # Add historical chat messages (maintain conversation context)
                if history:
                    # Convert history to proper chat format
                    for entry in history[-5:]:  # Last 5 conversations for context
                        if isinstance(entry, dict):
                            user_msg = entry.get("user_message", "")
                            assistant_msg = entry.get("assistant_response", "")
                            if user_msg:
                                stream_messages.append({"role": "user", "content": str(user_msg)})
                            if assistant_msg:
                                stream_messages.append({"role": "assistant", "content": str(assistant_msg)})

                # Add current conversation messages (excluding system messages already added)
                current_messages = [m for m in messages if m.get("role") != "system"]
                stream_messages.extend(current_messages)

                token_count = 0
                full_response = ""  # Collect the full response for storage

                last_heartbeat = time.time()
                HEARTBEAT_INTERVAL = 20  # seconds

                # Circuit breaker guard for streaming path
                breaker = get_llm_breaker()
                if not breaker.allow():
                    if METRICS_ENABLED:
                        llm_request_errors_total.labels(phase="circuit_open").inc()
                    raise HTTPException(status_code=503, detail="LLM service temporarily unavailable (circuit open)")

                stream_error = False
                async def _wrapped_stream():
                    nonlocal stream_error
                    try:
                        async for token in call_llm_stream(
                            stream_messages, model=body.get("model", DEFAULT_MODEL), session_id=session_id
                        ):
                            yield token
                    except Exception:
                        stream_error = True
                        raise

                async for token in _wrapped_stream():
                    # Debug: log what we receive from the stream (only if enabled)
                    if ENABLE_STREAM_DEBUG:
                        log_service_status("STREAM", "debug", f"Received token: '{token}' (type: {type(token)})")
                    
                    if not token:
                        if ENABLE_STREAM_DEBUG:
                            log_service_status("STREAM", "debug", "Skipping empty token")
                        continue

                    # Check if stream was stopped
                    if STREAM_SESSION_STOP.get(session_id, False):
                        log_service_status("STREAM", "info", f"Stream {session_id} stopped by client")
                        break

                    token_count += 1
                    full_response += token  # Accumulate the full response
                    data = {
                        "id": f"chatcmpl-{session_id}",
                        "object": "chat.completion.chunk",
                        "created": int(time.time()),
                        "model": body.get("model", DEFAULT_MODEL),
                        "choices": [{"index": 0, "delta": {"content": token}, "finish_reason": None}],
                    }

                    try:
                        if ENABLE_STREAM_DEBUG:
                            log_service_status("STREAM", "debug", f"Yielding SSE data: {json.dumps(data)}")
                        yield f"data: {json.dumps(data)}\n\n"
                    except Exception as e:
                        log_service_status("STREAM", "error", f"Error yielding token: {e}")
                        break

                    # Heartbeat (avoid idle disconnects)
                    now = time.time()
                    if now - last_heartbeat > HEARTBEAT_INTERVAL:
                        last_heartbeat = now
                        try:
                            if METRICS_ENABLED:
                                streaming_heartbeats_total.inc()
                            heartbeat_payload = {"event": "heartbeat", "ts": int(now)}
                            yield f"data: {json.dumps(heartbeat_payload)}\n\n"
                        except Exception:
                            pass

                # Store the complete streaming response in chat history (and update breaker)
                if full_response:
                    if stream_error:
                        breaker.record_failure()
                        if METRICS_ENABLED:
                            llm_request_errors_total.labels(phase="stream").inc()
                    else:
                        breaker.record_success()

                    async def store_streaming_chat():
                        try:
                            await store_chat_history(
                                f"user:{user_id}",
                                [
                                    {
                                        "role": "user",
                                        "content": user_message,
                                        "timestamp": datetime.fromtimestamp(start_time).isoformat(),
                                    },
                                    {
                                        "role": "assistant",
                                        "content": str(full_response),
                                        "timestamp": datetime.now(timezone.utc).isoformat(),
                                    },
                                ])
                        except Exception as e:
                            # Log cache error and continue - non-blocking for streaming
                            log_service_status("CACHE", "warning", f"Cache store failed for user {user_id}, conversation not cached: {e}")

                    await store_streaming_chat()
                    log_service_status(
                        "STREAM", "info", f"Stored streaming response for user {user_id}: {len(full_response)} chars"
                    )

                    # --- Memory Integration: Store conversation in memory ---
                    memory_service = get_memory_service_or_legacy()
                    if memory_service:
                        try:
                            # Track and auto-store conversation for memory learning
                            conversation_messages = [
                                {"role": "user", "content": user_message},
                                {"role": "assistant", "content": str(full_response)}
                            ]
                            memory_stored = await memory_service.track_conversation_and_store(
                                user_id=user_id,
                                messages=conversation_messages
                            )
                            if memory_stored:
                                log_service_status("MEMORY", "info", f"Stored conversation in memory for user {user_id}")
                        except Exception as e:
                            log_service_status("MEMORY", "error", f"Error storing conversation in memory for user {user_id}: {e}")

                # End of stream
                final_data = {
                    "id": f"chatcmpl-{session_id}",
                    "object": "chat.completion.chunk",
                    "created": int(time.time()),
                    "model": body.get("model", DEFAULT_MODEL),
                    "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
                }
                yield f"data: {json.dumps(final_data)}\n\n"
                yield "data: [DONE]\n\n"

                log_service_status("STREAM", "info", f"Stream {session_id} completed with {token_count} tokens")

            except Exception as e:
                log_service_status("STREAM", "error", f"Stream {session_id} failed: {e}")
                # Send error in SSE format
                error_data = {
                    "id": f"chatcmpl-{session_id}",
                    "object": "chat.completion.chunk",
                    "created": int(time.time()),
                    "model": body.get("model", DEFAULT_MODEL),
                    "choices": [{"index": 0, "delta": {"content": f"Error: {str(e)}"}, "finish_reason": "stop"}],
                }
                yield f"data: {json.dumps(error_data)}\n\n"
                yield "data: [DONE]\n\n"
            finally:
                # Cleanup
                STREAM_SESSION_STOP.pop(session_id, None)
                log_service_status("STREAM", "info", f"Cleaned up session {session_id}")
                if METRICS_ENABLED:
                    try:
                        llm_stream_latency_seconds.observe(time.time() - start_time)
                    except Exception:
                        pass

        if METRICS_ENABLED:
            chat_requests_total.labels(stream="true").inc()
        return StreamingResponse(
            event_stream(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Session-ID": session_id})

    else:
        # Non-streaming response - call LLM directly with specified model
        try:
            # --- Retrieve chat history and memory for OpenWebUI integration ---
            try:
                history = await get_chat_history(f"user:{user_id}", limit=10)
            except Exception as e:
                # Log cache error and continue without cache - non-blocking
                log_service_status("CACHE", "warning", f"Cache operation failed for user {user_id}, continuing without cache: {e}")
                history = []

            # --- Memory Integration: Retrieve relevant memories ---
            memory_context = ""
            memory_service = get_memory_service_or_legacy()
            if memory_service:
                try:
                    # Get relevant memories based on current user message
                    relevant_memories = await memory_service.get_relevant_memories(
                        user_id=user_id,
                        context=user_message,
                        max_memories=5
                    )
                    if relevant_memories:
                        memory_context = memory_service.format_memories_for_injection(relevant_memories)
                        log_service_status("MEMORY", "info", f"Retrieved {len(relevant_memories)} memories for user {user_id}")
                except Exception as e:
                    log_service_status("MEMORY", "error", f"Error retrieving memories for user {user_id}: {e}")
            else:
                log_service_status("MEMORY", "warning", "Memory service not available, using legacy system only")

            # Build enhanced message format with chat history
            llm_messages = []

            # Add system message first (if any) with memory context injection + delimiters
            system_messages = [m for m in messages if m.get("role") == "system"]
            if system_messages:
                # Inject memory context into existing system message
                enhanced_system_message = system_messages[0].copy()
                original_content = enhanced_system_message.get("content", "")
                if memory_context:
                    memory_injections_total.inc()
                    enhanced_system_message["content"] = f"<BEGIN_MEMORY_CONTEXT>\n{memory_context}\n<END_MEMORY_CONTEXT>\n{original_content}"
                llm_messages.append(enhanced_system_message)
            else:
                # No system prompts/personas - just use memory context if available
                if memory_context:
                    memory_injections_total.inc()
                    system_content = f"<BEGIN_MEMORY_CONTEXT>\n{memory_context}\n<END_MEMORY_CONTEXT>"
                    llm_messages.append({"role": "system", "content": system_content})

            # Add historical chat messages (maintain conversation context)
            if history:
                # Convert history to proper chat format
                for entry in history[-5:]:  # Last 5 conversations for context
                    if isinstance(entry, dict):
                        user_msg = entry.get("message", "")
                        assistant_msg = entry.get("response", "")
                        if user_msg:
                            llm_messages.append({"role": "user", "content": str(user_msg)})
                        if assistant_msg:
                            llm_messages.append({"role": "assistant", "content": str(assistant_msg)})

            # Add current conversation messages (excluding system messages already added)
            current_messages = [m for m in messages if m.get("role") != "system"]
            llm_messages.extend(current_messages)

            # Circuit breaker protected LLM call
            breaker = get_llm_breaker()
            if not breaker.allow():
                if METRICS_ENABLED:
                    llm_request_errors_total.labels(phase="circuit_open").inc()
                raise HTTPException(status_code=503, detail="LLM service temporarily unavailable (circuit open)")

            llm_call_start = time.time()
            try:
                llm_response = await call_llm(llm_messages, model=body.get("model", DEFAULT_MODEL))
                breaker.record_success()
            except Exception:
                breaker.record_failure()
                if METRICS_ENABLED:
                    llm_request_errors_total.labels(phase="call").inc()
                raise
            finally:
                if METRICS_ENABLED:
                    llm_request_latency_seconds.observe(time.time() - llm_call_start)

            # Store chat history using the existing logic but with the actual response
            if llm_response:

                async def store_chat():
                    try:
                        await store_chat_history(
                            f"user:{user_id}",
                            [
                                {
                                    "role": "user",
                                    "content": user_message,
                                    "timestamp": datetime.fromtimestamp(start_time).isoformat(),
                                },
                                {
                                    "role": "assistant",
                                    "content": str(llm_response),
                                    "timestamp": datetime.now(timezone.utc).isoformat(),
                                },
                            ])
                    except Exception as e:
                        # Log cache error and continue - non-blocking for non-streaming requests
                        log_service_status("CACHE", "warning", f"Cache store failed for user {user_id}, conversation not cached: {e}")

                await store_chat()

                # --- Memory Integration: Store conversation in memory ---
                memory_service = get_memory_service_or_legacy()
                if memory_service:
                    try:
                        # Track and auto-store conversation for memory learning
                        conversation_messages = [
                            {"role": "user", "content": user_message},
                            {"role": "assistant", "content": str(llm_response)}
                        ]
                        memory_stored = await memory_service.track_conversation_and_store(
                            user_id=user_id,
                            messages=conversation_messages
                        )
                        if memory_stored:
                            log_service_status("MEMORY", "info", f"Stored conversation in memory for user {user_id}")
                    except Exception as e:
                        log_service_status("MEMORY", "error", f"Error storing conversation in memory for user {user_id}: {e}")

            end_time = time.time()
            response_time = (end_time - start_time) * 1000
            log_api_request("POST", "/v1/chat/completions", 200, response_time)

            if METRICS_ENABLED:
                chat_requests_total.labels(stream=str(stream).lower()).inc()
            return {
                "id": "chatcmpl-1",
                "object": "chat.completion",
                "created": int(time.time()),
                "model": body.get("model", DEFAULT_MODEL),
                "choices": [
                    {
                        "index": 0,
                        "message": {"role": "assistant", "content": llm_response or ""},
                        "finish_reason": "stop",
                    }
                ],
            }
        except Exception as e:
            # Log the error and return a proper error response
            log_service_status("OPENAI_CHAT", "error", f"Error in OpenAI chat completions endpoint: {e}")
            log_error(e, "OpenAI chat completions", user_id, getattr(request.state, "request_id", "unknown"))
            if METRICS_ENABLED:
                llm_request_errors_total.labels(phase="endpoint").inc()
            raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")
