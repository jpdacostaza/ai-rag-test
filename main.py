from fastapi import FastAPI, Request, Body, Response, Depends, status, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel
import logging
import time
from datetime import datetime
from dataclasses import asdict # Import asdict
import itertools
import sys

# Initialize human-readable logging
from human_logging import init_logging, log_service_status, log_api_request
init_logging(level="INFO")

from ai_tools import get_current_time, get_weather, convert_units
from database import (
    db_manager, 
    get_cache, set_cache, 
    store_chat_history, get_chat_history, 
    index_user_document, retrieve_user_memory, 
    get_embedding, get_database_health
)
from error_handler import ErrorHandler, ChatErrorHandler, ToolErrorHandler, CacheErrorHandler, MemoryErrorHandler, RedisConnectionHandler, safe_execute, log_error
import os
import re
import json
import uuid
from watchdog import get_watchdog, start_watchdog_service, get_health_status, get_system_overview
import asyncio
import redis
from typing import Optional, AsyncGenerator, Dict

import httpx

# Import authentication and middleware
from authentication import auth_manager, validate_api_key, extract_api_key_from_request, create_auth_exception
from middleware_new import setup_middleware

# Import and include upload router
from upload import upload_router
# Import and include enhanced router
from enhanced_integration import enhanced_router, start_enhanced_background_tasks
from feedback_router import feedback_router
from model_manager import router as model_manager_router, refresh_model_cache, ensure_model_available, _model_cache

# Import and include missing endpoints router
from missing_endpoints import missing_router

app = FastAPI()

# Directly add the authentication middleware for debugging
from middleware_new import AuthenticationMiddleware
app.add_middleware(AuthenticationMiddleware)

# Log middleware setup completion
from human_logging import log_service_status
log_service_status("MIDDLEWARE", "ready", "Authentication middleware directly added to app")

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Middleware to log API requests and responses."""
    print("DEBUG: Function-based middleware log_requests() called")
    print(f"📊 LOG MIDDLEWARE: Processing {request.method} {request.url.path}")
    start_time = time.time()
    response = await call_next(request)
    end_time = time.time()
    response_time_ms = (end_time - start_time) * 1000
    log_api_request(request.method, request.url.path, response.status_code, response_time_ms)
    return response

app.include_router(model_manager_router)
app.include_router(missing_router)

# Include upload router
app.include_router(upload_router)
# Include enhanced router
app.include_router(enhanced_router)
app.include_router(feedback_router)

# Model configuration  
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "llama3.2:3b")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
USE_OLLAMA = os.getenv("USE_OLLAMA", "true").lower() == "true"

# Global variable to store watchdog thread
watchdog_thread = None

async def _spinner_log(message, duration=2, interval=0.2):
    """Show a spinner/progress animation in the logs for a given duration."""
    spinner = itertools.cycle(['|', '/', '-', '\\'])
    steps = int(duration / interval)
    for _ in range(steps):
        sys.stdout.write(f"\r{message} {next(spinner)}")
        sys.stdout.flush()
        await asyncio.sleep(interval)
    sys.stdout.write("\r" + " " * (len(message) + 2) + "\r")
    sys.stdout.flush()

@app.on_event("startup")
async def startup_event():
    """Initialize services after FastAPI app has started."""
    global watchdog_thread
    
    # Enhanced startup logging
    log_service_status("STARTUP", "starting", "🚀 FastAPI LLM Backend Starting...")
    _log_system_info()
    _log_environment_variables()
    
    # Storage
    log_service_status("STARTUP", "starting", "Initializing storage structure...")
    await _spinner_log("[STARTUP] Initializing storage structure", 2)
    from storage_manager import initialize_storage
    storage_success = initialize_storage()
    if not storage_success:
        log_service_status("STARTUP", "degraded", "Storage initialization had issues - some features may be affected")
    else:
        log_service_status("STARTUP", "ready", "Storage structure initialized successfully")
    
    # Database
    log_service_status("STARTUP", "starting", "Initializing database connections...")
    await _spinner_log("[STARTUP] Initializing database connections", 2)
    from database import db_manager
    
    # Store Redis pool in app state for dependency injection (like working implementation)
    if hasattr(db_manager, 'redis_pool') and db_manager.redis_pool is not None:
        app.state.redis_pool = db_manager.redis_pool
        log_service_status("STARTUP", "ready", "Redis pool stored in app state")
    else:
        app.state.redis_pool = None
        log_service_status("STARTUP", "degraded", "Redis pool not available - some features may be degraded")
    
    # Model preload
    log_service_status("STARTUP", "starting", f"Verifying and preloading model: {DEFAULT_MODEL}")
    await _spinner_log(f"[MODEL] Preloading {DEFAULT_MODEL}", 2)
    try:
        model_available = await ensure_model_available(DEFAULT_MODEL)
        if model_available:
            log_service_status("MODEL", "ready", f"Default model {DEFAULT_MODEL} is available")
            # Preload model into memory by running a dummy inference
            try:
                preload_payload = {
                    "model": DEFAULT_MODEL,
                    "prompt": "Hello!",
                    "stream": False
                }
                async with httpx.AsyncClient() as client:
                    resp = await client.post(f"{OLLAMA_BASE_URL}/api/generate", json=preload_payload, timeout=60)
                    if resp.status_code == 200:
                        log_service_status("MODEL", "preloaded", f"Model {DEFAULT_MODEL} preloaded into memory")
                    else:
                        log_service_status("MODEL", "warning", f"Model {DEFAULT_MODEL} preload failed: HTTP {resp.status_code}")
            except Exception as e:
                log_service_status("MODEL", "warning", f"Model {DEFAULT_MODEL} preload failed: {e}")
        else:
            log_service_status("MODEL", "error", f"Failed to ensure default model {DEFAULT_MODEL} is available")
    except Exception as e:
        log_service_status("MODEL", "error", f"Error checking default model {DEFAULT_MODEL}: {str(e)}")
      # Initialize model cache on startup
    log_service_status("STARTUP", "starting", "Initializing model cache...")
    await refresh_model_cache()
      # Initialize cache management system with health check
    log_service_status("STARTUP", "starting", "Initializing cache management and memory systems...")
    from startup_memory_health import initialize_memory_systems
    memory_init_success = initialize_memory_systems()
    if memory_init_success:
        log_service_status("MEMORY", "ready", "Memory and cache systems initialized successfully")
    else:
        log_service_status("MEMORY", "warning", "Memory and cache systems initialization had issues")
    
    # Background services
    log_service_status("STARTUP", "starting", "Initializing background services...")
    await _spinner_log("[STARTUP] Initializing background services", 2)
    await asyncio.sleep(2)
    log_service_status("STARTUP", "starting", "Waiting 2 seconds for services to initialize...")
    
    # Watchdog
    watchdog_thread = start_watchdog_service()
    log_service_status("WATCHDOG", "starting", "Service started with delayed initialization")

    # Enhanced background tasks
    await start_enhanced_background_tasks()
    log_service_status("ENHANCED_SYSTEM", "ready", "Enhanced learning and document processing systems initialized")
    
    # Final summary banner
    await _spinner_log("[STARTUP] Finalizing startup", 1)
    _print_startup_summary()
    log_service_status("STARTUP", "ready", "🚀 FastAPI LLM Backend startup completed successfully!")


def _print_startup_summary():
    """Print a visually distinct summary banner with health status of all services."""
    from database import get_database_health
    health = get_database_health()
    lines = [
        "\n================= SERVICE STATUS SUMMARY =================",
        f"Redis:      {'✅' if health['redis']['available'] else '❌'}",
        f"ChromaDB:   {'✅' if health['chromadb']['available'] else '❌'}",
        f"Embeddings: {'✅' if health['embeddings']['available'] else '❌'}",
        "========================================================\n"
    ]
    for line in lines:
        print(line)

def _log_system_info():
    """Log system information for startup diagnostics."""
    try:
        import platform
        import sys
        import os
        
        log_service_status("SYSTEM", "info", f"Python version: {sys.version.split()[0]}")
        log_service_status("SYSTEM", "info", f"Platform: {platform.system()} {platform.release()}")
        log_service_status("SYSTEM", "info", f"Working directory: {os.getcwd()}")
        
    except Exception as e:
        log_service_status("SYSTEM", "warning", f"Failed to log system info: {e}")

def _log_environment_variables():
    """Log relevant environment variables for startup diagnostics."""
    try:
        import os
        
        env_vars_to_log = [
            "REDIS_HOST", "REDIS_PORT", "CHROMA_HOST", "CHROMA_PORT", 
            "DEFAULT_MODEL", "EMBEDDING_MODEL", "SENTENCE_TRANSFORMERS_HOME",
            "OLLAMA_BASE_URL", "USE_OLLAMA", "USE_HTTP_CHROMA"
        ]
        
        log_service_status("STARTUP", "info", "Environment configuration:")
        for var in env_vars_to_log:
            value = os.getenv(var, "Not set")
            # Mask sensitive values
            if "KEY" in var or "SECRET" in var:
                value = "***" if value != "Not set" else "Not set"
            log_service_status("CONFIG", "info", f"{var}={value}")
            
    except Exception as e:
        log_service_status("CONFIG", "warning", f"Failed to log environment: {e}")

@app.get("/health")
async def health_check():
    """Health check endpoint that includes database status and a human-readable summary."""
    health_status = get_database_health()
    
    # Add cache information
    from database import get_cache_manager
    cache_manager = get_cache_manager()
    cache_info = {}
    if cache_manager:
        cache_info = cache_manager.get_cache_stats()
    
    services = [
        ("Redis", health_status["redis"]["available"]),
        ("ChromaDB", health_status["chromadb"]["available"]),
        ("Embeddings", health_status["embeddings"]["available"])
    ]
    healthy = sum(1 for _, ok in services if ok)
    total = len(services)
    summary = f"Health check: {healthy}/{total} services healthy. " + ", ".join([
        f"{name}: {'✅' if ok else '❌'}" for name, ok in services
    ])
    
    response = {
        "status": "ok" if healthy == total else "degraded",
        "summary": summary,
        "databases": health_status
    }
    
    if cache_info:
        response["cache"] = cache_info
    
    return response

@app.get("/health/simple")
async def simple_health():
    """Simple health check without any dependencies."""
    import time
    return {
        "status": "ok",
        "timestamp": time.time(),
        "message": "Simple health check working"
    }

@app.get("/health/detailed")
async def detailed_health_check():
    """Detailed health check with subsystem monitoring."""
    health_status = await get_health_status() # Correctly call the helper function
    
    # The health_status is now a dictionary of ServiceHealth objects
    # We need to process it for the final response
    
    services = {name: asdict(status) for name, status in health_status.items()}
    healthy_count = sum(1 for s in services.values() if s['status'] == 'healthy')
    degraded_count = sum(1 for s in services.values() if s['status'] == 'degraded')
    unhealthy_count = sum(1 for s in services.values() if s['status'] == 'unhealthy')
    
    overall = "healthy"
    if unhealthy_count > 0:
        overall = "unhealthy"
    elif degraded_count > 0:
        overall = "degraded"

    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "overall_status": overall,
        "services": services,
        "summary": {
            "total_services": len(services),
            "healthy_services": healthy_count,
            "degraded_services": degraded_count,
            "unhealthy_services": unhealthy_count
        }
    }

@app.get("/health/redis")
async def redis_health():
    """Check Redis connectivity specifically."""
    watchdog = get_watchdog()
    redis_monitor = next((m for m in watchdog.monitors if m.name == "Redis"), None)
    if redis_monitor:
        result = await redis_monitor.check_health()
        return {"service": "Redis", "health": result.__dict__}
    return {"service": "Redis", "status": "monitor_not_found"}

@app.get("/health/chromadb")
async def chromadb_health():
    """Check ChromaDB connectivity specifically."""
    watchdog = get_watchdog()
    chroma_monitor = next((m for m in watchdog.monitors if m.name == "ChromaDB"), None)
    if chroma_monitor:
        result = await chroma_monitor.check_health()
        return {"service": "ChromaDB", "health": result.__dict__}
    return {"service": "ChromaDB", "status": "monitor_not_found"}

# Ollama health check disabled - using OpenAI API only
# @app.get("/health/ollama")
# async def ollama_health():
#     """Check Ollama connectivity specifically."""
#     watchdog = get_watchdog()
#     ollama_monitor = next((m for m in watchdog.monitors if m.name == "Ollama"), None)
#     if ollama_monitor:
#         result = await ollama_monitor.check_health()
#         return {"service": "Ollama", "health": result.__dict__}
#     return {"service": "Ollama", "status": "monitor_not_found"}

@app.get("/health/history/{service_name}")
async def service_health_history(service_name: str, hours: int = 24):
    """Get health history for a specific service."""
    watchdog = get_watchdog()
    history = watchdog.get_service_history(service_name, hours)
    return {
        "service": service_name,
        "history_hours": hours,
        "checks": len(history),
        "history": [h.__dict__ for h in history]
    }

@app.get("/health/storage")
async def storage_health():
    """Check storage directory structure and permissions."""
    from storage_manager import StorageManager
    
    # Get storage information
    storage_info = StorageManager.get_storage_info()
    
    # Validate permissions
    permissions = StorageManager.validate_permissions()
    
    # Calculate total storage usage
    total_size_mb = sum(
        dir_info.get('size_mb', 0) 
        for dir_info in storage_info['directories'].values()
    )
    
    # Count directories
    existing_dirs = sum(
        1 for dir_info in storage_info['directories'].values() 
        if dir_info['exists']
    )
    total_dirs = len(storage_info['directories'])
    
    # Determine overall status
    if existing_dirs == total_dirs and all(permissions.values()):
        status = "healthy"
    elif existing_dirs > 0:
        status = "degraded"
    else:
        status = "unhealthy"
    
    return {
        "service": "Storage",
        "status": status,
        "base_path": storage_info['base_path'],
        "directories": {
            "total": total_dirs,
            "existing": existing_dirs,
            "missing": total_dirs - existing_dirs
        },
        "storage_usage": {
            "total_size_mb": total_size_mb,
            "total_files": sum(
                dir_info.get('file_count', 0) 
                for dir_info in storage_info['directories'].values()
            )
        },
        "permissions": permissions,
        "directory_details": storage_info['directories']
    }

# --- LLM call (Ollama or OpenAI API) ---
async def call_llm(messages, model=None, api_url=None, api_key=None):
    model = model or DEFAULT_MODEL
    """
    Calls an LLM API (Ollama or OpenAI) with the provided messages and returns the response.
    This function is asynchronous.
    """
    if USE_OLLAMA:
        return await call_ollama_llm(messages, model)
    else:
        return await call_openai_llm(messages, model, api_url, api_key)

async def call_ollama_llm(messages, model=None):
    """
    Asynchronously calls the Ollama API using the chat endpoint for better control.
    """
    model = model or DEFAULT_MODEL
    
    # Debug logging to see what messages are being sent
    logging.info(f"[DEBUG] Sending {len(messages)} messages to Ollama model {model}")
    
    # Use Ollama's chat endpoint which provides better control over system prompts
    payload = {
        "model": model, 
        "messages": messages, 
        "stream": False,
        "options": {
            "temperature": 0.7,
            "top_p": 0.9
        }
    }
    timeout = int(os.getenv("LLM_TIMEOUT", "180"))

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{OLLAMA_BASE_URL}/api/chat", json=payload, timeout=timeout)
            response.raise_for_status()
            data = response.json()
            return data.get("message", {}).get("content", "")
    except httpx.RequestError as e:
        log_service_status("OLLAMA", "failed", f"Connection to Ollama at {OLLAMA_BASE_URL} failed: {e}")
        raise Exception(f"Cannot connect to Ollama service at {OLLAMA_BASE_URL}") from e
    except httpx.HTTPStatusError as e:
        log_service_status("OLLAMA", "failed", f"Ollama API returned an error: {e.response.status_code} - {e.response.text}")
        raise

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{OLLAMA_BASE_URL}/api/generate", json=payload, timeout=timeout)
            response.raise_for_status()
            data = response.json()
            return data.get("response", "")
    except httpx.RequestError as e:
        log_service_status("OLLAMA", "failed", f"Connection to Ollama at {OLLAMA_BASE_URL} failed: {e}")
        raise Exception(f"Cannot connect to Ollama service at {OLLAMA_BASE_URL}") from e
    except httpx.HTTPStatusError as e:
        log_service_status("OLLAMA", "failed", f"Ollama API returned an error: {e.response.status_code} - {e.response.text}")
        raise

async def call_openai_llm(messages, model=None, api_url=None, api_key=None):
    model = model or DEFAULT_MODEL
    """
    Asynchronously calls an OpenAI-compatible API.
    """
    api_url = api_url or os.getenv("OPENAI_API_BASE_URL", "https://api.openai.com/v1")
    api_key = api_key or os.getenv("OPENAI_API_KEY")
    
    if not api_url.endswith('/chat/completions'):
        api_url = f"{api_url.rstrip('/')}/chat/completions"
    
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}
    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
        "max_tokens": int(os.getenv("OPENAI_API_MAX_TOKENS", "4096")),
        "temperature": 0.7,
    }
    timeout = int(os.getenv("OPENAI_API_TIMEOUT", "180"))

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(api_url, headers=headers, json=payload, timeout=timeout)
            resp.raise_for_status()
            data = resp.json()
            return data.get("choices", [{}])[0].get("message", {}).get("content", "")
    except httpx.RequestError as e:
        log_service_status("OPENAI", "failed", f"Connection to OpenAI API at {api_url} failed: {e}")
        raise Exception(f"Cannot connect to OpenAI service at {api_url}") from e
    except httpx.HTTPStatusError as e:
        log_service_status("OPENAI", "failed", f"OpenAI API returned an error: {e.response.status_code} - {e.response.text}")
        raise

async def call_llm_stream(messages, model=None, api_url=None, api_key=None, stop_event=None, session_id=None):
    model = model or DEFAULT_MODEL
    """
    Streams tokens from an LLM API (Ollama or OpenAI) in real time.
    """
    if USE_OLLAMA:
        return call_ollama_llm_stream(messages, model, stop_event, session_id)
    else:
        return call_openai_llm_stream(messages, model, api_url, api_key, stop_event, session_id)

async def call_ollama_llm_stream(messages, model=None, stop_event=None, session_id=None) -> AsyncGenerator[str, None]:
    """
    Asynchronously streams tokens from the Ollama API.
    """
    model = model or DEFAULT_MODEL
    prompt = "\n".join(f"{msg.get('role', 'user').capitalize()}: {msg.get('content', '')}" for msg in messages)
    payload = {"model": model, "prompt": prompt, "stream": True}
    timeout = int(os.getenv("LLM_TIMEOUT", "180"))

    try:
        async with httpx.AsyncClient() as client:
            async with client.stream("POST", f"{OLLAMA_BASE_URL}/api/generate", json=payload, timeout=timeout) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if (stop_event and stop_event.is_set()) or (session_id and STREAM_SESSION_STOP.get(session_id)):
                        break
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                        if "response" in data:
                            yield data["response"]
                        if data.get("done"):
                            break
                    except json.JSONDecodeError:
                        continue
    except httpx.RequestError as e:
        log_service_status("OLLAMA", "failed", f"Streaming connection to Ollama failed: {e}")
        yield "Error: Cannot connect to Ollama service"
    except Exception as e:
        log_service_status("OLLAMA", "failed", f"Ollama streaming failed: {e}")
        yield f"Error: {str(e)}"

async def call_openai_llm_stream(messages, model=None, api_url=None, api_key=None, stop_event=None, session_id=None) -> AsyncGenerator[str, None]:
    """
    Asynchronously streams tokens from an OpenAI-compatible API.
    """
    model = model or DEFAULT_MODEL
    api_url = api_url or os.getenv("OPENAI_API_BASE_URL", "https://api.openai.com/v1")
    api_key = api_key or os.getenv("OPENAI_API_KEY")

    if not api_url.endswith('/chat/completions'):
        api_url = f"{api_url.rstrip('/')}/chat/completions"

    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}
    payload = {
        "model": model,
        "messages": messages,
        "stream": True,
        "max_tokens": int(os.getenv("OPENAI_API_MAX_TOKENS", "4096")),
        "temperature": 0.7,
    }
    timeout = int(os.getenv("OPENAI_API_TIMEOUT", "180"))

    try:
        async with httpx.AsyncClient() as client:
            async with client.stream("POST", api_url, headers=headers, json=payload, timeout=timeout) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if (stop_event and stop_event.is_set()) or (session_id and STREAM_SESSION_STOP.get(session_id)):
                        break
                    if not line or not line.startswith("data: "):
                        continue
                    
                    line_text = line[6:]
                    if line_text.strip() == "[DONE]":
                        break

                    try:
                        data = json.loads(line_text)
                        if (choices := data.get("choices")) and (delta := choices[0].get("delta")) and (content := delta.get("content")):
                            yield content
                    except json.JSONDecodeError:
                        continue
    except httpx.RequestError as e:
        log_service_status("OPENAI", "failed", f"Streaming connection to OpenAI API failed: {e}")
        yield "Error: Cannot connect to OpenAI API"
    except Exception as e:
        log_service_status("OPENAI", "failed", f"OpenAI streaming failed: {e}")
        yield f"Error: {str(e)}"

# Global dict to track streaming sessions
STREAM_SESSION_STOP: Dict[str, bool] = {}

def stop_streaming_session(session_id: str):
    STREAM_SESSION_STOP[session_id] = True

# --- Chat Endpoint ---
class ChatRequest(BaseModel):
    user_id: str
    message: str

class ChatResponse(BaseModel):
    response: str

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(chat: ChatRequest, request: Request):
    # Generate a unique request ID for tracking
    request_id = str(uuid.uuid4())
    
    try:
        user_message = chat.message
        user_id = chat.user_id
        user_response = None
        
        logging.debug(f"[REQUEST {request_id}] Chat request from user {user_id}: {user_message[:100]}...")
        
        # --- Check cache before tool/LLM logic ---
        cache_key = f"chat:{user_id}:{user_message}"
        cached = None
        logging.debug(f"[CACHE] Checking cache for key: {cache_key}")
          # Bypass cache for time queries to ensure real-time lookup
        is_time_query = False
        timeanddate_pattern = re.compile(r"time(?:\\s*(?:in|for|at))?\\s+([a-zA-Z ]+)", re.IGNORECASE)
        if (
            "timeanddate.com" in user_message.lower() or
            (timeanddate_pattern.search(user_message) and not any(x in user_message.lower() for x in ["weather", "convert", "calculate", "exchange rate", "system info", "news", "search"])) or
            "time" in user_message.lower()
        ):
            is_time_query = True
            
        if not is_time_query:
            cached = get_cache(db_manager, cache_key, user_id=user_id, request_id=request_id)
            if cached:
                return ChatResponse(response=cached)
                
        # --- Retrieve chat history and memory ---
        def get_history():
            return get_chat_history(db_manager, user_id, max_history=10, request_id=request_id)
        
        history = safe_execute(
            get_history,
            fallback_value=[],
            error_handler=lambda e: CacheErrorHandler.handle_cache_error(e, "get_history", f"history:{user_id}", user_id, request_id)
        )
        
        history_msgs = [m["message"] if isinstance(m, dict) and "message" in m else str(m) for m in (history or [])]
        
        # --- Intent/tool detection (tool results take precedence) ---
        tool_used = False
        tool_name = None
        debug_info = []
        
        # --- Robust time query detection ---
        time_query = False
        match = None
        # Match phrases like "time in", "current time in", "what is the time in", etc.
        time_patterns = [
            r"time(?:\s*(?:in|for|at))?\s+([a-zA-Z ]+)",
            r"current time in ([a-zA-Z ]+)",
            r"what(?:'s| is) the time in ([a-zA-Z ]+)",
            r"timeanddate\\.com.*([a-zA-Z ]+)"
        ]
        for pat in time_patterns:
            m = re.search(pat, user_message, re.IGNORECASE)
            if m:
                match = m
                time_query = True
                break
                
        if time_query or "timeanddate.com" in user_message.lower():
            system_msg = f"[TOOL] Robust time lookup (geo+timezone, fallback to timeanddate.com) triggered for user {user_id}"
            logging.debug(system_msg)
            debug_info.append(system_msg)
            country = match.group(1).strip() if match else "netherlands"
            # Clean up extracted location string
            country = re.sub(r"^(is|what|'s|the|current|now|please|tell|me|show|give|provide|can|you|do|does|in|for|at|on|to|of|about|time|current time|the time|\s)+", "", country, flags=re.IGNORECASE)
            country = re.sub(r"\?$", "", country).strip()
            if not country:
                country = "netherlands"            
            def get_timezone_time():
                # Try to get timezone for the country
                country_timezones = {
                    "netherlands": "Europe/Amsterdam",
                    "amsterdam": "Europe/Amsterdam", 
                    "london": "Europe/London",
                    "uk": "Europe/London",
                    "new york": "America/New_York",
                    "tokyo": "Asia/Tokyo",
                    "paris": "Europe/Paris",
                    "berlin": "Europe/Berlin",
                    "moscow": "Europe/Moscow",
                    "sydney": "Australia/Sydney"
                }
                
                tz = country_timezones.get(country.lower(), None)
                if tz:
                    return get_current_time(tz) + f" (timezone: {tz})", "geo_timezone"
                else:
                    from ai_tools import get_time_from_timeanddate
                    return get_time_from_timeanddate(country), "timeanddate.com"
            
            result = safe_execute(
                get_timezone_time,
                fallback_value=(ToolErrorHandler.handle_tool_error(Exception("Time lookup failed"), "time", user_id, country, request_id), "error"),
                error_handler=lambda e: ToolErrorHandler.handle_tool_error(e, "time", user_id, country, request_id)
            )
            
            user_response, tool_name = result
            tool_used = True
            debug_info.append(f"[TOOL] Used {tool_name} for {country}")
            
        elif "weather" in user_message.lower():
            system_msg = f"[TOOL] Weather lookup triggered for user {user_id}"
            logging.debug(system_msg)
            debug_info.append(system_msg)
            match = re.search(r"weather in ([a-zA-Z ]+)", user_message, re.IGNORECASE)
            city = match.group(1).strip() if match else "London"
            
            user_response = safe_execute(
                get_weather,
                city,
                fallback_value=ToolErrorHandler.handle_tool_error(Exception("Weather lookup failed"), "weather", user_id, city, request_id),
                error_handler=lambda e: ToolErrorHandler.handle_tool_error(e, "weather", user_id, city, request_id)
            )
            tool_used = True
            tool_name = "weather"
            
        elif "time" in user_message.lower():
            system_msg = f"[TOOL] Time lookup triggered for user {user_id}"
            logging.debug(system_msg)
            debug_info.append(system_msg)
            match = re.search(r"time in ([a-zA-Z ]+)", user_message, re.IGNORECASE)
            city = match.group(1).strip() if match else None
            city_timezone = {"netherlands": "Europe/Amsterdam", "amsterdam": "Europe/Amsterdam"}
            tz = city_timezone.get(city.lower(), None) if city else None
            
            user_response = safe_execute(
                get_current_time,                tz,
                fallback_value=ToolErrorHandler.handle_tool_error(Exception("Time lookup failed"), "time", user_id, str(city), request_id),
                error_handler=lambda e: ToolErrorHandler.handle_tool_error(e, "time", user_id, str(city), request_id)
            )
            tool_used = True
            tool_name = "time"
            
        elif "convert" in user_message.lower() and "to" in user_message.lower():
            system_msg = f"[TOOL] Unit conversion triggered for user {user_id}"
            logging.debug(system_msg)
            debug_info.append(system_msg)
            match = re.search(r"convert ([\d\.]+) ([a-zA-Z]+) to ([a-zA-Z]+)", user_message, re.IGNORECASE)
            if match:
                value, from_unit, to_unit = float(match.group(1)), match.group(2), match.group(3)
                user_response = safe_execute(
                    convert_units,
                    value, from_unit, to_unit,
                    fallback_value=ToolErrorHandler.handle_tool_error(Exception("Unit conversion failed"), "unit_conversion", user_id, f"{value} {from_unit} to {to_unit}", request_id),
                    error_handler=lambda e: ToolErrorHandler.handle_tool_error(e, "unit_conversion", user_id, f"{value} {from_unit} to {to_unit}", request_id)
                )
            else:
                user_response = "Please specify conversion like 'convert 10 km to m'."
            tool_used = True
            tool_name = "unit_conversion"
            
        elif "news" in user_message.lower():
            system_msg = f"[TOOL] News lookup triggered for user {user_id}"
            logging.debug(system_msg)
            debug_info.append(system_msg)
            
            user_response = "News lookup is currently unavailable."
            tool_used = True
            tool_name = "news"
            
        elif "search" in user_message.lower():
            system_msg = f"[TOOL] Web search triggered for user {user_id}"
            logging.debug(system_msg)
            debug_info.append(system_msg)
            match = re.search(r"search (.+)", user_message, re.IGNORECASE)
            query = match.group(1) if match else user_message
            
            def web_search_safe():
                results = []
                return results[0] if results else "No results found.", results
            
            result = safe_execute(
                web_search_safe,
                fallback_value=(ToolErrorHandler.handle_tool_error(Exception("Web search failed"), "web_search", user_id, query, request_id), []),
                error_handler=lambda e: ToolErrorHandler.handle_tool_error(e, "web_search", user_id, query, request_id)
            )
            
            if isinstance(result, tuple):
                user_response, results = result
            else:
                user_response = result
                results = []
                
            tool_used = True
            tool_name = "web_search"
            
        elif "exchange rate" in user_message.lower():
            system_msg = f"[TOOL] Exchange rate lookup triggered for user {user_id}"
            logging.debug(system_msg)
            debug_info.append(system_msg)
            match = re.search(r"exchange rate ([a-zA-Z]{3}) to ([a-zA-Z]{3})", user_message, re.IGNORECASE)
            if match:
                from_cur, to_cur = match.group(1), match.group(2)
                # user_response = safe_execute(
                #     get_exchange_rate,
                #     from_cur, to_cur,
                #     fallback_value=ToolErrorHandler.handle_tool_error(Exception("Exchange rate lookup failed"), "exchange_rate", user_id, f"{from_cur} to {to_cur}", request_id),
                #     error_handler=lambda e: ToolErrorHandler.handle_tool_error(e, "exchange_rate", user_id, f"{from_cur} to {to_cur}", request_id)
                # )
                user_response = "Exchange rate lookup is currently unavailable."
            tool_used = True
            tool_name = "exchange_rate"
            
        elif "system info" in user_message.lower():
            system_msg = f"[TOOL] System info lookup triggered for user {user_id}"
            logging.debug(system_msg)
            debug_info.append(system_msg)            
            # user_response = safe_execute(
            #     get_system_info,
            #     fallback_value=ToolErrorHandler.handle_tool_error(Exception("System info lookup failed"), "system_info", user_id, "", request_id),
            #     error_handler=lambda e: ToolErrorHandler.handle_tool_error(e, "system_info", user_id, "", request_id)
            # )
            user_response = "System info lookup is currently unavailable."
            tool_used = True
            tool_name = "system_info"
            
        elif "run python" in user_message.lower() or user_message.lower().startswith("python ") or "python code" in user_message.lower():
            system_msg = f"[TOOL] Python code execution triggered for user {user_id}"
            logging.debug(system_msg)
            debug_info.append(system_msg)
            # Extract code after 'run python' or after 'python ' or find code in the message
            if "```python" in user_message:
                # Extract code from code blocks
                code_start = user_message.find("```python") + 9
                code_end = user_message.find("```", code_start)
                code = user_message[code_start:code_end].strip() if code_end != -1 else user_message[code_start:].strip()
            elif "run python" in user_message.lower():
                code = user_message.split("run python",1)[-1].strip()
            elif user_message.lower().startswith("python "):
                code = user_message.split("python ",1)[-1].strip()
            else:
                # Try to extract any code-like text
                code = user_message.strip()
            
            if not code:
                user_response = "Please provide Python code to execute."
            else:
                # user_response = safe_execute(
                #     run_python_code,
                #     code,
                #     fallback_value=ToolErrorHandler.handle_tool_error(Exception("Python code execution failed"), "python_code_execution", user_id, code[:100], request_id),
                #     error_handler=lambda e: ToolErrorHandler.handle_tool_error(e, "python_code_execution", user_id, code[:100], request_id)
                # )
                user_response = "Python code execution is currently unavailable."
            tool_used = True
            tool_name = "python_code_execution"
            
        elif "wikipedia" in user_message.lower() or "wiki" in user_message.lower():
            system_msg = f"[TOOL] Wikipedia search triggered for user {user_id}"
            logging.debug(system_msg)
            debug_info.append(system_msg)
            # Extract search query
            query = user_message.lower().replace("wikipedia", "").replace("wiki", "").replace("search", "").strip()
            if not query:
                query = "artificial intelligence"  # default
                
            # user_response = safe_execute(
            #     wikipedia_search,
            #     query,
            #     fallback_value=ToolErrorHandler.handle_tool_error(Exception("Wikipedia search failed"), "wikipedia", user_id, query, request_id),
            #     error_handler=lambda e: ToolErrorHandler.handle_tool_error(e, "wikipedia", user_id, query, request_id)
            # )
            user_response = "Wikipedia search is currently unavailable."
            tool_used = True
            tool_name = "wikipedia"        # --- If no tool matched, use LLM with memory/context ---        if not tool_used:
            def llm_query():
                # Embed user query and retrieve relevant memory
                query_emb = get_embedding(db_manager, user_message, request_id)
                memory_chunks = retrieve_user_memory(db_manager, user_id, query_emb, n_results=3, request_id=request_id) if query_emb is not None else []
                
                # Compose LLM context with explicit instructions for plain text responses
                system_prompt = "You are a helpful assistant. Use the following memory and chat history to answer. Always respond with plain text only - never use JSON formatting, structured responses, or any special formatting. Just provide direct, natural language answers."
                
                # Check for system prompt changes and invalidate cache if needed
                from database import get_cache_manager
                cache_manager = get_cache_manager()
                if cache_manager:
                    cache_manager.check_system_prompt_change(system_prompt)
                
                # Ensure all memory_chunks and history_msgs are strings and handle None values
                memory_chunks = memory_chunks or []
                current_history_msgs = history_msgs or []
                context = "\n".join([str(m) for m in memory_chunks] + [str(m) for m in current_history_msgs])
                messages = [
                    {"role": "system", "content": system_prompt},
                    *[{"role": "user", "content": m} for m in current_history_msgs],
                    {"role": "user", "content": user_message},
                    {"role": "system", "content": f"Relevant memory: {context}"} if context else None
                ]
                messages = [m for m in messages if m]
                return call_llm(messages)
            
            user_response = safe_execute(
                llm_query,
                fallback_value="I apologize, but I'm having trouble processing your request right now. Please try again.",
                error_handler=lambda e: log_error(e, "LLM query", user_id, request_id)
            )
            logging.debug(f"[RESPONSE] LLM response returned for user {user_id}")
            debug_info.append("[TOOL] Used LLM fallback")
        else:
            logging.debug(f"[RESPONSE] Tool '{tool_name}' response returned for user {user_id}")
            debug_info.append(f"[TOOL] Tool '{tool_name}' response returned")              # --- Store chat in Redis ---
        def store_chat():
            store_chat_history(db_manager, user_id, {"message": user_message, "response": user_response}, request_id=request_id)
        
        safe_execute(
            store_chat,
            error_handler=lambda e: CacheErrorHandler.handle_cache_error(e, "store_chat", f"chat:{user_id}", user_id, request_id)
        )          # --- Cache the response (after generating user_response) ---
        def cache_response():
            if not is_time_query:
                set_cache(db_manager, cache_key, str(user_response), ttl=600, user_id=user_id, request_id=request_id)
                logging.debug(f"[CACHE] Response cached for user {user_id} (key: {cache_key})")
                debug_info.append(f"[CACHE] Response cached (key: {cache_key})")
            else:
                logging.debug("[CACHE] Skipping cache for time-sensitive query")
        
        safe_execute(
            cache_response,
            error_handler=lambda e: CacheErrorHandler.handle_cache_error(e, "set", cache_key, user_id, request_id)
        )
          # --- Automatic knowledge storage: store web search results in ChromaDB ---
        if tool_used and tool_name == "web_search" and user_response and 'results' in locals():
            def store_knowledge():
                # Store the top web result as a new document in ChromaDB for this user
                doc_id = f"web:{user_id}:{abs(hash(query))}"
                name = f"Web search: {query}"
                text = user_response
                chunks_stored = index_user_document(db_manager, user_id, doc_id, name, text, request_id=request_id)
                logging.debug(f"[KNOWLEDGE] Stored web search result ({chunks_stored} chunks) in ChromaDB for user {user_id}, query '{query}'")
            
            safe_execute(
                store_knowledge,
                error_handler=lambda e: MemoryErrorHandler.handle_memory_error(e, "store", user_id, request_id)
            )
            
        # Always log debug info, but do not include in user-facing response
        logging.debug(f"[DEBUG INFO] {' | '.join(debug_info)}")
        logging.debug(f"[REQUEST {request_id}] Successfully processed chat request for user {user_id}")
        
        return ChatResponse(response=str(user_response) if user_response is not None else "")
        
    except Exception as e:
        # Use the specialized chat error handler
        error_response = ChatErrorHandler.handle_chat_error(e, user_id, user_message, request_id)
        return ChatResponse(response=error_response["response"])

@app.get("/v1/models")
async def list_models():
    """
    OpenAI-compatible endpoint for model listing. Dynamically fetches available models from Ollama with caching.
    """
    global _model_cache
    # Check if cache is still valid
    current_time = time.time()
    if current_time - _model_cache["last_updated"] > _model_cache["ttl"]:
        # Cache expired, refresh
        await refresh_model_cache()
      # Temporary workaround: ensure Mistral model is included if it exists in Ollama
    models_data = _model_cache["data"].copy()
    mistral_exists = any(model["id"] == "mistral:7b-instruct-v0.3-q4_k_m" for model in models_data)
    
    logging.info(f"[MODELS DEBUG] Cache has {len(models_data)} models, Mistral exists: {mistral_exists}")
    logging.info(f"[MODELS DEBUG] Using OLLAMA_BASE_URL: {OLLAMA_BASE_URL}")
    
    if not mistral_exists:
        # Check if Mistral model exists in Ollama directly
        try:
            import httpx
            logging.info(f"[MODELS DEBUG] Checking Ollama at {OLLAMA_BASE_URL}/api/tags")
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
                logging.info(f"[MODELS DEBUG] Ollama response status: {resp.status_code}")
                if resp.status_code == 200:
                    ollama_models = resp.json().get("models", [])
                    logging.info(f"[MODELS DEBUG] Found {len(ollama_models)} models in Ollama")
                    for model in ollama_models:
                        logging.info(f"[MODELS DEBUG] Ollama model: {model['name']}")
                        if model["name"] == "mistral:7b-instruct-v0.3-q4_k_m":
                            models_data.append({
                                "id": "mistral:7b-instruct-v0.3-q4_k_m",
                                "object": "model", 
                                "created": int(time.time()),
                                "owned_by": "ollama",
                                "permission": []
                            })
                            logging.info("[MODELS DEBUG] Added Mistral model to response")
                            break
        except Exception as e:
            logging.warning(f"Failed to check Ollama for Mistral model: {e}")
    
    return {
        "object": "list",
        "data": models_data
    }

@app.post("/v1/chat/completions")
async def openai_chat_completions(request: Request, body: dict = Body(...)):
    """
    OpenAI-compatible chat completions endpoint for OpenWebUI, with streaming support.
    Requires authentication via API key.
    """
    import time
    start_time = time.time()
    
    # Extract user_id and message from OpenAI-style request
    user_id = body.get("user", "openwebui")
    messages = body.get("messages", [])
    stream = body.get("stream", False)
    # Use the last user message as the prompt
    user_message = ""
    for m in reversed(messages):
        if m.get("role") == "user":
            user_message = m.get("content", "")
            break
    # Call the existing chat logic
    chat_req = ChatRequest(user_id=user_id, message=user_message)
    # Streaming support
    if stream:
        session_id = f"{user_id}:{body.get('model', DEFAULT_MODEL)}"
        STREAM_SESSION_STOP[session_id] = False
        async def event_stream():
            logging.debug("[STREAM] Streaming response triggered.")
            llm_streamer = await call_llm_stream(messages, model=body.get("model", DEFAULT_MODEL), session_id=session_id)
            async for token in llm_streamer:
                if not token:
                    continue
                data = {
                    "id": f"chatcmpl-1",
                    "object": "chat.completion.chunk",
                    "created": 0,
                    "model": body.get("model", DEFAULT_MODEL),
                    "choices": [
                        {
                            "index": 0,
                            "delta": {"content": token},
                            "finish_reason": None
                        }
                    ]
                }
                logging.debug(f"[STREAM] Sending chunk: {token}")
                yield f"data: {json.dumps(data)}\n\n"
            # End of stream
            logging.debug("[STREAM] Streaming complete.")
            yield "data: [DONE]\n\n"
            STREAM_SESSION_STOP.pop(session_id, None)
        
        return StreamingResponse(event_stream(), media_type="text/event-stream")

    else:
        chat_resp = await chat_endpoint(chat_req, request)
        # Non-streaming response
        end_time = time.time()
        response_time = (end_time - start_time) * 1000
        log_api_request("POST", "/v1/chat/completions", 200, response_time)
        return {
            "id": f"chatcmpl-1",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": body.get("model", DEFAULT_MODEL),
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": chat_resp.response
                    },
                    "finish_reason": "stop"
                }
            ]
        }

# All additional endpoints now handled by missing_endpoints.py router
# This includes: /config, /persona, /learning/*, /session/*, /upload, /rag/query, 
# /adaptive/stats, /cache/*, /storage/*, /database/health
