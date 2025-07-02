"""
Main FastAPI application with modular structure.
"""

import json
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Dict

from fastapi import FastAPI, Request, Body, Depends, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import asyncio

# CRITICAL: Import and enforce CPU-only mode BEFORE any ML libraries
from utilities.cpu_enforcer import enforce_cpu_only_mode

# Enforce CPU-only mode immediately
enforce_cpu_only_mode()

# Import modules
from config import DEFAULT_MODEL, OLLAMA_BASE_URL, DEFAULT_SYSTEM_PROMPT
from handlers import create_exception_handlers
from human_logging import log_api_request, log_service_status
from models import ChatRequest, ChatResponse, OpenAIMessage, OpenAIChatRequest, ModelListResponse, ErrorResponse
from routes import health_router, chat_router, models_router, upload_router, debug_router
from services.llm_service import call_llm, call_llm_stream
from services.streaming_service import streaming_service, STREAM_SESSION_STOP, STREAM_SESSION_METADATA
from startup import startup_event

# Import existing routers
from model_manager import router as model_manager_router, initialize_model_cache

# Import database and other dependencies
from database_manager import db_manager, get_embedding, index_user_document, retrieve_user_memory
from database_manager import get_cache, set_cache, get_chat_history, store_chat_history, get_database_health
from error_handler import CacheErrorHandler, safe_execute, log_error


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan events."""
    # Startup
    log_service_status("APP", "info", "Starting application lifespan")
    try:
        # Run the main startup event
        await startup_event(app)
        # Initialize model cache
        await initialize_model_cache()
        log_service_status("APP", "ready", "Application startup completed successfully")
    except Exception as e:
        log_service_status("APP", "error", f"Error during application startup: {e}")
        raise

    yield

    # Shutdown
    log_service_status("APP", "info", "Application shutting down")


# Import security configuration
from security import configure_security, validate_environment

# Validate environment variables at startup
validate_environment()

# Create FastAPI app with lifespan
app = FastAPI(
    title="AI Backend API", description="Modular FastAPI backend for AI-powered application", lifespan=lifespan
)

# Configure security middleware first
configure_security(app)

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
            return JSONResponse(
                status_code=504,
                content={
                    "error": "Request timeout",
                    "message": f"Request took longer than {self.timeout} seconds",
                    "suggestion": "Try a simpler query or break it into smaller parts",
                },
            )


# Add timeout middleware
app.add_middleware(TimeoutMiddleware, timeout=45)

# Include route modules
app.include_router(health_router)
app.include_router(chat_router)
app.include_router(models_router)

# Include additional routers
app.include_router(upload_router)
app.include_router(debug_router)
app.include_router(model_manager_router)


# OpenAI-compatible chat completions endpoint
@app.post("/v1/chat/completions")
async def openai_chat_completions(request: Request, body: dict = Body(...)):
    """
    OpenAI-compatible chat completions endpoint for OpenWebUI, with streaming support.
    """
    start_time = time.time()

    # Validate required fields
    if "model" not in body or not body["model"]:
        raise HTTPException(status_code=400, detail="Missing required field: 'model'")

    if "messages" not in body or not isinstance(body["messages"], list) or len(body["messages"]) == 0:
        raise HTTPException(
            status_code=400, detail="Missing or invalid required field: 'messages' (must be a non-empty list)"
        )

    # Validate messages structure
    for i, message in enumerate(body["messages"]):
        if not isinstance(message, dict):
            raise HTTPException(status_code=400, detail=f"Message at index {i} must be an object")
        if "role" not in message or "content" not in message:
            raise HTTPException(status_code=400, detail=f"Message at index {i} must have 'role' and 'content' fields")

    # Extract user_id and message from OpenAI-style request
    user_id = body.get("user", "openwebui")
    messages = body.get("messages", [])
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
        session_id = f"{user_id}:{body.get('model', DEFAULT_MODEL)}:{int(time.time())}"
        streaming_service.create_session(session_id, user_id, body.get("model", DEFAULT_MODEL))

        async def event_stream():
            """Enhanced event stream with proper error handling and cleanup."""
            try:
                log_service_status("STREAM", "info", f"Starting stream for session {session_id}")

                # --- Retrieve chat history and memory for streaming ---
                try:
                    history = await get_chat_history(f"user:{user_id}", limit=10)
                except Exception as e:
                    CacheErrorHandler.handle_cache_error(
                        e, "get_history", f"history:{user_id}", user_id, getattr(request.state, "request_id", "unknown")
                    )
                    history = []

                # Build enhanced message format with chat history for streaming
                stream_messages = []

                # Add system message first (if any)
                system_messages = [m for m in messages if m.get("role") == "system"]
                if system_messages:
                    stream_messages.extend(system_messages)
                else:
                    # Add default persona system message if none provided
                    stream_messages.append({"role": "system", "content": DEFAULT_SYSTEM_PROMPT})

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

                async for token in call_llm_stream(
                    stream_messages, model=body.get("model", DEFAULT_MODEL), session_id=session_id
                ):
                    if not token:
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
                        yield f"data: {json.dumps(data)}\n\n"
                    except Exception as e:
                        log_service_status("STREAM", "error", f"Error yielding token: {e}")
                        break

                # Store the complete streaming response in chat history
                if full_response:

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
                                        "timestamp": datetime.utcnow().isoformat(),
                                    },
                                ],
                            )
                        except Exception as e:
                            CacheErrorHandler.handle_cache_error(
                                e, "store_streaming_chat", f"chat:{user_id}", user_id, session_id
                            )

                    await store_streaming_chat()
                    log_service_status(
                        "STREAM", "info", f"Stored streaming response for user {user_id}: {len(full_response)} chars"
                    )

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

        return StreamingResponse(
            event_stream(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Session-ID": session_id},
        )

    else:
        # Non-streaming response - call LLM directly with specified model
        try:
            # --- Retrieve chat history and memory for OpenWebUI integration ---
            try:
                history = await get_chat_history(f"user:{user_id}", limit=10)
            except Exception as e:
                CacheErrorHandler.handle_cache_error(
                    e, "get_history", f"history:{user_id}", user_id, getattr(request.state, "request_id", "unknown")
                )
                history = []

            # Build enhanced message format with chat history
            llm_messages = []

            # Add system message first (if any)
            system_messages = [m for m in messages if m.get("role") == "system"]
            if system_messages:
                llm_messages.extend(system_messages)
            else:
                # Add default persona system message if none provided
                llm_messages.append({"role": "system", "content": DEFAULT_SYSTEM_PROMPT})

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

            # Call LLM directly with the specified model
            llm_response = await call_llm(llm_messages, model=body.get("model", DEFAULT_MODEL))

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
                                    "timestamp": datetime.utcnow().isoformat(),
                                },
                            ],
                        )
                    except Exception as e:
                        CacheErrorHandler.handle_cache_error(
                            e, "store_chat", f"chat:{user_id}", user_id, getattr(request.state, "request_id", "unknown")
                        )

                await store_chat()

            end_time = time.time()
            response_time = (end_time - start_time) * 1000
            log_api_request("POST", "/v1/chat/completions", 200, response_time)

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
            raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")


# Middleware for request tracking
@app.middleware("http")
async def request_middleware(request: Request, call_next):
    """Enhanced middleware with request tracking and timing."""
    # Generate unique request ID
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id

    # Start timing
    start_time = time.time()

    # Log request start
    log_service_status("REQUEST", "info", f"[{request_id}] {request.method} {request.url.path} - Started")

    try:
        # Process request
        response = await call_next(request)

        # Calculate timing
        end_time = time.time()
        response_time_ms = (end_time - start_time) * 1000

        # Log successful completion
        log_service_status(
            "REQUEST",
            "info",
            f"[{request_id}] {request.method} {request.url.path} - "
            f"Completed {response.status_code} in {response_time_ms:.2f}ms",
        )

        # Add timing headers
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = f"{response_time_ms:.2f}ms"

        # Log API request for monitoring
        log_api_request(request.method, request.url.path, response.status_code, response_time_ms)

        return response

    except Exception as e:
        # Calculate timing for failed requests
        end_time = time.time()
        response_time_ms = (end_time - start_time) * 1000

        # Log error
        log_service_status(
            "REQUEST",
            "error",
            f"[{request_id}] {request.method} {request.url.path} - " f"Failed after {response_time_ms:.2f}ms: {str(e)}",
        )

        # Re-raise to let exception handlers deal with it
        raise


@app.get("/debug/routes")
async def debug_routes():
    """Debug endpoint to list all available routes"""
    routes = []
    for route in app.routes:
        try:
            if hasattr(route, "path"):
                path = getattr(route, "path", "unknown")
                methods = getattr(route, "methods", {"GET"})
                routes.append({"path": path, "methods": list(methods) if methods else ["GET"]})
        except Exception:
            continue
    return {"total_routes": len(routes), "routes": sorted(routes, key=lambda x: x["path"])}


# Application lifespan is now handled in the lifespan context manager above
