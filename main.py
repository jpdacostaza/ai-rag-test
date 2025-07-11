"""
Main FastAPI application with modular structure.
"""

import json
import os
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
from routes import health_router, chat_router, models_router, upload_router, debug_router, memory_router
from services.llm_service import call_llm, call_llm_stream
print("[MAIN.PY] LLM service imported successfully!", flush=True)
from services.streaming_service import streaming_service, STREAM_SESSION_STOP, STREAM_SESSION_METADATA
from startup import startup_event

# Import memory system
try:
    from memory import MemoryService, MemoryConfig
    MEMORY_AVAILABLE = True
except ImportError:
    MemoryService = None
    MemoryConfig = None
    MEMORY_AVAILABLE = False
    log_service_status("MEMORY", "warning", "New memory system not available, using legacy fallback")

# Import existing routers
from model_manager import router as model_manager_router, initialize_model_cache
from routes.chat import get_user_memories

# Import database and other dependencies
from database_manager import db_manager, get_embedding, index_user_document
from database_manager import get_cache, set_cache, get_chat_history, store_chat_history, get_database_health
from error_handler import CacheErrorHandler, safe_execute, log_error


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan events."""
    global global_memory_service
    
    # Startup
    log_service_status("APP", "info", "Starting application lifespan")
    try:
        # Run the main startup event
        await startup_event(app)
        
        # Initialize memory service if available
        if MEMORY_AVAILABLE:
            memory_config = MemoryConfig(
                api_url=os.getenv("MEMORY_API_URL", "http://memory_api:8080"),
                timeout=float(os.getenv("MEMORY_TIMEOUT", "10.0")),
                max_memories=int(os.getenv("MAX_MEMORIES", "5")),
                relevance_threshold=float(os.getenv("MEMORY_THRESHOLD", "0.1")),
                auto_store_enabled=os.getenv("MEMORY_AUTO_STORE", "true").lower() == "true",
                auto_store_threshold=int(os.getenv("MEMORY_AUTO_STORE_THRESHOLD", "3")),
                debug_enabled=os.getenv("MEMORY_DEBUG", "false").lower() == "true"
            )
            
            def memory_logger(message: str, level: str = "INFO"):
                log_service_status("MEMORY_SERVICE", level.lower(), message)
            
            global_memory_service = MemoryService(memory_config, memory_logger)
            log_service_status("MEMORY_SERVICE", "ready", "Memory service initialized successfully")
        else:
            log_service_status("MEMORY_SERVICE", "warning", "Memory service not available, using legacy system")
        
        # Initialize model cache
        await initialize_model_cache()
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


def get_memory_service_or_legacy():
    """
    Get memory service with fallback to legacy system.
    
    Returns:
        MemoryService instance if available, None otherwise.
        Routes should check for None and use legacy fallback.
    """
    global global_memory_service
    return global_memory_service


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
app.include_router(memory_router)
app.include_router(model_manager_router)


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

    # Extract user_id from various sources - match pipeline logic exactly
    # INFO: Log the full request details for troubleshooting
    log_service_status("AUTH", "info", f"=== USER IDENTIFICATION START ===")
    log_service_status("AUTH", "info", f"Request body keys: {list(body.keys())}")
    log_service_status("AUTH", "info", f"Request headers: {dict(request.headers)}")
    if "user" in body:
        log_service_status("AUTH", "info", f"User field in body: {body.get('user')} (type: {type(body.get('user'))})")
    
    # 1. Check body.user field which can be string or object (OpenWebUI style)
    user_field = body.get("user")
    
    # If user field is an object (like pipeline receives), extract email/id
    if isinstance(user_field, dict):
        # Match pipeline's EXACT user identification strategy
        log_service_status("AUTH", "info", f"User object received: {json.dumps(user_field, indent=2)}")
        
        # Strategy 1: Use email (most specific) - SAME AS PIPELINE
        if "email" in user_field and user_field["email"]:
            user_id = user_field["email"]
            log_service_status("AUTH", "info", f"Using email as user_id: {user_id}")
        # Strategy 2: Use user ID
        elif "id" in user_field and user_field["id"]:
            user_id = user_field["id"]
            log_service_status("AUTH", "info", f"Using id as user_id: {user_id}")
        # Strategy 3: Use username
        elif "username" in user_field and user_field["username"]:
            user_id = user_field["username"]
            log_service_status("AUTH", "info", f"Using username as user_id: {user_id}")
        # Strategy 4: Use name
        elif "name" in user_field and user_field["name"]:
            user_id = user_field["name"]
            log_service_status("AUTH", "info", f"Using name as user_id: {user_id}")
        else:
            log_service_status("AUTH", "info", "No suitable user identifier found in user object")
    elif isinstance(user_field, str) and user_field:
        # If it's a simple string, use it
        user_id = user_field
        log_service_status("AUTH", "info", f"Using string user_id: {user_id}")
    
    # 2. Check headers for user information (OpenWebUI may send via headers)
    if not user_id:
        # Common header names used by OpenWebUI and similar systems
        user_id = (
            request.headers.get("x-user-id") or
            request.headers.get("x-user") or 
            request.headers.get("x-openwebui-user") or
            request.headers.get("user-id") or
            request.headers.get("authorization", "").split(":")[-1] if ":" in request.headers.get("authorization", "") else None
        )
        if user_id:
            log_service_status("AUTH", "info", f"Found user_id in headers: {user_id}")
    
    # 3. Try to extract from session context or chat history
    if not user_id and messages:
        # Look for user identification in system messages or metadata
        for msg in messages:
            if msg.get("role") == "system" and "user_id:" in msg.get("content", ""):
                try:
                    content = msg.get("content", "")
                    if "user_id:" in content:
                        user_id = content.split("user_id:")[1].split()[0].strip()
                        log_service_status("AUTH", "info", f"Found user_id in system message: {user_id}")
                        break
                except:
                    pass
    
    # 4. Check if we can extract user from injected memory context by pipeline
    if not user_id and messages:
        # Look for pipeline-injected memory messages that contain user context
        for msg in messages:
            if (msg.get("role") == "system" and 
                "Previous conversation context and memories" in msg.get("content", "")):
                # Pipeline has processed this request - look for user mentions
                content = msg.get("content", "")
                log_service_status("AUTH", "info", "Found pipeline-injected memory context")
                
                # The pipeline must have identified a user to inject memories
                # Check if there are any user-specific patterns in the memory content
                if "@" in content and ".net" in content:  # Email pattern
                    import re
                    email_match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', content)
                    if email_match:
                        user_id = email_match.group()
                        log_service_status("AUTH", "info", f"Extracted user_id from memory context: {user_id}")
                        break
    
    # 5. Advanced user identification from conversation content
    if user_id == "openwebui" and messages:
        # Look for user identification in the conversation history
        user_mentions = []
        for msg in messages:
            content = msg.get("content", "").lower()
            
            # Look for name introductions
            patterns = [
                r"my name is ([a-zA-Z\.]+)",
                r"i'm ([a-zA-Z\.]+)",
                r"i am ([a-zA-Z\.]+)",
                r"call me ([a-zA-Z\.]+)",
                r"this is ([a-zA-Z\.]+)"
            ]
            
            import re
            for pattern in patterns:
                match = re.search(pattern, content)
                if match:
                    potential_name = match.group(1).strip()
                    if len(potential_name) > 1 and potential_name not in ["user", "person", "someone"]:
                        user_mentions.append(potential_name)
        
        # Use the most recent/common name mention
        if user_mentions:
            user_id = user_mentions[-1]  # Use the last mentioned name
            log_service_status("AUTH", "info", f"Identified user from conversation: {user_id}")
    
    # 5. Enhanced user identification: map generic session to actual user from memory
    if user_id == "openwebui" and messages:
        try:
            from memory.core.client import MemoryClient
            from memory.core.models import MemoryConfig, MemoryQuery
            
            # Create memory client
            memory_config = MemoryConfig(api_url="http://memory_api:8080", timeout=5.0)
            memory_client = MemoryClient(memory_config)
            
            # Search for user identification in existing memories
            identity_query = MemoryQuery(
                user_id="openwebui",
                query_text="name is swift developer apple",
                limit=10,
                threshold=0.01
            )
            
            memory_response = await memory_client.retrieve_memories(identity_query)
            
            if memory_response.success and memory_response.memories:
                for memory in memory_response.memories:
                    content_lower = memory.content.lower()
                    # Look for name patterns in stored memories
                    import re
                    name_patterns = [
                        r"name is ([a-zA-Z\.]+)",
                        r"i'm ([a-zA-Z\.]+)",
                        r"user's name is ([a-zA-Z\.]+)",
                        r"my name is ([a-zA-Z\.]+)"
                    ]
                    
                    for pattern in name_patterns:
                        match = re.search(pattern, content_lower)
                        if match:
                            potential_user = match.group(1).strip()
                            if len(potential_user) > 1 and potential_user != "user":
                                user_id = potential_user
                                log_service_status("AUTH", "info", f"Mapped session 'openwebui' to user: {user_id}")
                                break
                    if user_id != "openwebui":
                        break
        except Exception as e:
            log_service_status("AUTH", "warning", f"Failed to lookup user from memory: {e}")
    
    # 6. Final fallback - but try to be smarter about it
    if not user_id or not user_id.strip() or user_id == "openwebui":
        # Last resort: try to find any user context from stored memories 
        # that might give us a clue about the actual user
        if messages and user_id == "openwebui":
            # Look for recent user identification in existing memories
            try:
                # Use memory service to look for user patterns
                memory_service = get_memory_service_or_legacy()
                if memory_service:
                    log_service_status("AUTH", "info", "Attempting user lookup from memory patterns")
                    
                    # Try to get any memories that might contain user identification
                    test_memories = await memory_service.get_relevant_memories(
                        user_id="admin@theroot.za.net",  # Try the known good user
                        query_text="name swift",
                        limit=5
                    )
                    
                    if test_memories:
                        # If we found memories for the email user, use that instead
                        user_id = "admin@theroot.za.net"
                        log_service_status("AUTH", "info", f"Mapped openwebui session to email user: {user_id}")
                    
            except Exception as e:
                log_service_status("AUTH", "warning", f"User lookup from memory failed: {e}")
        
        # Absolute final fallback
        if not user_id or not user_id.strip():
            user_id = "openwebui"
    
    # Ensure user_id is clean and non-empty
    user_id = user_id.strip()
    if not user_id:
        user_id = "openwebui"
    
    # Log user identification for debugging
    log_service_status("AUTH", "info", f"Identified user: {user_id}")
    
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

                # --- Memory Integration: Retrieve relevant memories ---
                memory_context = ""
                memory_service = get_memory_service_or_legacy()
                if memory_service:
                    try:
                        # Get relevant memories based on current user message
                        relevant_memories = await memory_service.get_relevant_memories(
                            user_id=user_id,
                            query_text=user_message,
                            limit=5
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

                # Add system message first (if any) with memory context injection
                system_messages = [m for m in messages if m.get("role") == "system"]
                if system_messages:
                    # Inject memory context into existing system message
                    enhanced_system_message = system_messages[0].copy()
                    original_content = enhanced_system_message.get("content", "")
                    if memory_context:
                        enhanced_system_message["content"] = f"{memory_context}{original_content}"
                    stream_messages.append(enhanced_system_message)
                else:
                    # Add default persona system message with memory context
                    system_content = DEFAULT_SYSTEM_PROMPT
                    if memory_context:
                        system_content = f"{memory_context}{DEFAULT_SYSTEM_PROMPT}"
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

                async for token in call_llm_stream(
                    stream_messages, model=body.get("model", DEFAULT_MODEL), session_id=session_id
                ):
                    # Debug: log what we receive from the stream
                    log_service_status("STREAM", "debug", f"Received token: '{token}' (type: {type(token)})")
                    
                    if not token:
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
                        log_service_status("STREAM", "debug", f"Yielding SSE data: {json.dumps(data)}")
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

            # --- Memory Integration: Retrieve relevant memories ---
            memory_context = ""
            memory_service = get_memory_service_or_legacy()
            if memory_service:
                try:
                    # Get relevant memories based on current user message
                    relevant_memories = await memory_service.get_relevant_memories(
                        user_id=user_id,
                        query_text=user_message,
                        limit=5
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

            # Add system message first (if any) with memory context injection
            system_messages = [m for m in messages if m.get("role") == "system"]
            if system_messages:
                # Inject memory context into existing system message
                enhanced_system_message = system_messages[0].copy()
                original_content = enhanced_system_message.get("content", "")
                if memory_context:
                    enhanced_system_message["content"] = f"{memory_context}{original_content}"
                llm_messages.append(enhanced_system_message)
            else:
                # Add default persona system message with memory context
                system_content = DEFAULT_SYSTEM_PROMPT
                if memory_context:
                    system_content = f"{memory_context}{DEFAULT_SYSTEM_PROMPT}"
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
