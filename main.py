from fastapi import FastAPI, Request, Body, Response, Depends, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import logging
import time
from datetime import datetime
from dataclasses import asdict # Import asdict
import itertools
import sys

# Initialize human-readable logging
from human_logging import init_logging, HumanLogger, log_redis_status, log_chromadb_status, log_api_request
init_logging(level="INFO")

from ai_tools import get_current_time, get_weather, convert_units
from database import (
    db_manager, 
    get_cache, set_cache, 
    store_chat_history, get_chat_history, 
    index_user_document, retrieve_user_memory, 
    get_embedding, get_database_health
)
from error_handler import ErrorHandler, ChatErrorHandler, ToolErrorHandler, CacheErrorHandler, MemoryErrorHandler, RedisConnectionHandler, safe_execute
import os
import requests
import re
import json
import uuid
from watchdog import get_watchdog, start_watchdog_service, get_health_status, get_system_overview
import asyncio
import redis
from typing import Optional

import httpx

# Import and include upload router
from upload import upload_router
# Import and include enhanced router
from enhanced_integration import enhanced_router, start_enhanced_background_tasks
from feedback_router import feedback_router
from model_manager import router as model_manager_router

app = FastAPI()
app.include_router(model_manager_router)

# Include upload router
app.include_router(upload_router)
# Include enhanced router
app.include_router(enhanced_router)
app.include_router(feedback_router)

# Model configuration  
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "llama3.2:3b")
OLLAMA_BASE_URL = os.getenv("OLLAMA_URL", "http://ollama:11434")
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
    HumanLogger.log_startup_banner()
    _log_system_info()
    _log_environment_variables()
    
    # Storage
    HumanLogger.log_service_status("STARTUP", "starting", "Initializing storage structure...")
    await _spinner_log("[STARTUP] Initializing storage structure", 2)
    from storage_manager import initialize_storage
    storage_success = initialize_storage()
    if not storage_success:
        HumanLogger.log_service_status("STARTUP", "degraded", "Storage initialization had issues - some features may be affected")
    else:
        HumanLogger.log_service_status("STARTUP", "ready", "Storage structure initialized successfully")
    
    # Database
    HumanLogger.log_service_status("STARTUP", "starting", "Initializing database connections...")
    await _spinner_log("[STARTUP] Initializing database connections", 2)
    from database import db_manager
    
    # Store Redis pool in app state for dependency injection (like working implementation)
    if hasattr(db_manager, 'redis_pool') and db_manager.redis_pool is not None:
        app.state.redis_pool = db_manager.redis_pool
        HumanLogger.log_service_status("STARTUP", "ready", "Redis pool stored in app state")
    else:
        app.state.redis_pool = None
        HumanLogger.log_service_status("STARTUP", "degraded", "Redis pool not available - some features may be degraded")
    
    # Model preload
    HumanLogger.log_service_status("STARTUP", "starting", f"Verifying and preloading model: {DEFAULT_MODEL}")
    await _spinner_log(f"[MODEL] Preloading {DEFAULT_MODEL}", 2)
    try:
        model_available = await ensure_model_available(DEFAULT_MODEL)
        if model_available:
            HumanLogger.log_service_status("MODEL", "ready", f"Default model {DEFAULT_MODEL} is available")
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
                        HumanLogger.log_service_status("MODEL", "preloaded", f"Model {DEFAULT_MODEL} preloaded into memory")
                    else:
                        HumanLogger.log_service_status("MODEL", "warning", f"Model {DEFAULT_MODEL} preload failed: HTTP {resp.status_code}")
            except Exception as e:
                HumanLogger.log_service_status("MODEL", "warning", f"Model {DEFAULT_MODEL} preload failed: {e}")
        else:
            HumanLogger.log_service_status("MODEL", "error", f"Failed to ensure default model {DEFAULT_MODEL} is available")
    except Exception as e:
        HumanLogger.log_service_status("MODEL", "error", f"Error checking default model {DEFAULT_MODEL}: {str(e)}")
    
    # Initialize model cache on startup
    HumanLogger.log_service_status("STARTUP", "starting", "Initializing model cache...")
    await refresh_model_cache()
    
    # Background services
    HumanLogger.log_service_status("STARTUP", "starting", "Initializing background services...")
    await _spinner_log("[STARTUP] Initializing background services", 2)
    await asyncio.sleep(2)
    HumanLogger.log_service_status("STARTUP", "starting", "Waiting 2 seconds for services to initialize...")
    
    # Watchdog
    watchdog_thread = start_watchdog_service()
    HumanLogger.log_service_status("WATCHDOG", "starting", "Service started with delayed initialization")

    # Enhanced background tasks
    await start_enhanced_background_tasks()
    HumanLogger.log_service_status("ENHANCED_SYSTEM", "ready", "Enhanced learning and document processing systems initialized")
    
    # Final summary banner
    await _spinner_log("[STARTUP] Finalizing startup", 1)
    _print_startup_summary()
    HumanLogger.log_service_status("STARTUP", "ready", "🚀 FastAPI LLM Backend startup completed successfully!")

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
        
        HumanLogger.log_service_status("STARTUP", "starting", f"🚀 FastAPI LLM Backend Starting...")
        HumanLogger.log_service_status("STARTUP", "starting", f"🔧 Initializing services...")
        HumanLogger.log_service_status("SYSTEM", "starting", f"Python version: {sys.version.split()[0]}")
        HumanLogger.log_service_status("SYSTEM", "starting", f"Platform: {platform.system()} {platform.release()}")
        HumanLogger.log_service_status("SYSTEM", "starting", f"Working directory: {os.getcwd()}")
        
    except Exception as e:
        HumanLogger.log_service_status("SYSTEM", "warning", f"Failed to log system info: {e}")

def _log_environment_variables():
    """Log relevant environment variables for startup diagnostics."""
    try:
        import os
        
        env_vars_to_log = [
            "REDIS_HOST", "REDIS_PORT", "CHROMA_HOST", "CHROMA_PORT", 
            "DEFAULT_MODEL", "EMBEDDING_MODEL", "SENTENCE_TRANSFORMERS_HOME",
            "OLLAMA_URL", "USE_OLLAMA", "USE_HTTP_CHROMA"
        ]
        
        HumanLogger.log_service_status("STARTUP", "starting", "Environment configuration:")
        for var in env_vars_to_log:
            value = os.getenv(var, "Not set")
            # Mask sensitive values
            if "KEY" in var or "SECRET" in var:
                value = "***" if value != "Not set" else "Not set"
            HumanLogger.log_service_status("CONFIG", "starting", f"{var}={value}")
            
    except Exception as e:
        HumanLogger.log_service_status("CONFIG", "warning", f"Failed to log environment: {e}")

@app.get("/health")
async def health_check():
    """Health check endpoint that includes database status and a human-readable summary."""
    health_status = get_database_health()
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
    return {
        "status": "ok" if healthy == total else "degraded",
        "summary": summary,
        "databases": health_status
    }

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
def call_llm(messages, model=None, api_url=None, api_key=None):
    if model is None:
        model = DEFAULT_MODEL
    """
    Calls Ollama or OpenAI API with the provided messages and returns the response.
    """
    if USE_OLLAMA:
        return call_ollama_llm(messages, model)
    else:
        return call_openai_llm(messages, model, api_url, api_key)

def call_ollama_llm(messages, model=None):
    """
    Calls Ollama API with the provided messages and returns the response.
    """
    if model is None:
        model = DEFAULT_MODEL
        
    try:
        # Convert messages to Ollama format
        prompt = ""
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "system":
                prompt += f"System: {content}\n"
            elif role == "user":
                prompt += f"User: {content}\n"
            elif role == "assistant":
                prompt += f"Assistant: {content}\n"
        
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False
        }
        
        timeout = int(os.getenv("LLM_TIMEOUT", "180"))
        response = requests.post(f"{OLLAMA_BASE_URL}/api/generate", json=payload, timeout=timeout)
        response.raise_for_status()
        data = response.json()
        
        return data.get("response", "")
        
    except requests.exceptions.ConnectionError:
        HumanLogger.log_service_status("LLM", "error", f"Cannot connect to Ollama at {OLLAMA_BASE_URL}")
        raise Exception(f"Cannot connect to Ollama service at {OLLAMA_BASE_URL}")
    except Exception as e:
        HumanLogger.log_service_status("LLM", "error", f"Ollama API call failed: {str(e)}")
        raise

def call_openai_llm(messages, model=None, api_url=None, api_key=None):
    if model is None:
        model = DEFAULT_MODEL
    """
    Calls OpenAI API with the provided messages and returns the response.
    """
    # Use OpenAI API configuration
    api_url = api_url or os.getenv("OPENAI_API_BASE_URL", "https://api.openai.com/v1")
    api_key = api_key or os.getenv("OPENAI_API_KEY")
    
    # Ensure we have the chat/completions endpoint
    if not api_url.endswith('/chat/completions'):
        api_url = api_url.rstrip('/') + '/chat/completions'
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
        "max_tokens": int(os.getenv("OPENAI_API_MAX_TOKENS", "4096")),
        "temperature": 0.7
    }
    
    timeout = int(os.getenv("OPENAI_API_TIMEOUT", "180"))
    resp = requests.post(api_url, headers=headers, json=payload, timeout=timeout)
    resp.raise_for_status()
    data = resp.json()
    
    # OpenAI API response format
    if "choices" in data and len(data["choices"]) > 0:
        return data["choices"][0]["message"]["content"]
    return ""

def call_llm_stream(messages, model=None, api_url=None, api_key=None, stop_event=None, session_id=None):
    if model is None:
        model = DEFAULT_MODEL
    """
    Streams tokens from Ollama or OpenAI API in real time.
    """
    if USE_OLLAMA:
        return call_ollama_llm_stream(messages, model, stop_event, session_id)
    else:
        return call_openai_llm_stream(messages, model, api_url, api_key, stop_event, session_id)

def call_ollama_llm_stream(messages, model=None, stop_event=None, session_id=None):
    """
    Streams tokens from Ollama API in real time.
    """
    if model is None:
        model = DEFAULT_MODEL
        
    try:
        # Convert messages to Ollama format
        prompt = ""
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "system":
                prompt += f"System: {content}\n"
            elif role == "user":
                prompt += f"User: {content}\n"
            elif role == "assistant":
                prompt += f"Assistant: {content}\n"
        
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": True
        }
        
        timeout = int(os.getenv("LLM_TIMEOUT", "180"))
        with requests.post(f"{OLLAMA_BASE_URL}/api/generate", json=payload, stream=True, timeout=timeout) as resp:
            resp.raise_for_status()
            for line in resp.iter_lines():
                if stop_event and stop_event.is_set():
                    break
                if session_id and session_id in STREAM_SESSION_STOP and STREAM_SESSION_STOP[session_id]:
                    break
                if not line:
                    continue
                
                try:
                    data = json.loads(line.decode("utf-8"))
                    if "response" in data:
                        yield data["response"]
                    if data.get("done", False):
                        break
                except json.JSONDecodeError:
                    continue
                    
    except requests.exceptions.ConnectionError:
        HumanLogger.log_service_status("LLM", "error", f"Cannot connect to Ollama at {OLLAMA_BASE_URL}")
        yield "Error: Cannot connect to Ollama service"
    except Exception as e:
        HumanLogger.log_service_status("LLM", "error", f"Ollama streaming failed: {str(e)}")
        yield f"Error: {str(e)}"

def call_openai_llm_stream(messages, model=None, api_url=None, api_key=None, stop_event=None, session_id=None):
    if model is None:
        model = DEFAULT_MODEL
    """
    Streams tokens from OpenAI API in real time.
    """
    import requests
    
    # Use OpenAI API configuration
    api_url = api_url or os.getenv("OPENAI_API_BASE_URL", "https://api.openai.com/v1")
    api_key = api_key or os.getenv("OPENAI_API_KEY")
    
    # Ensure we have the chat/completions endpoint
    if not api_url.endswith('/chat/completions'):
        api_url = api_url.rstrip('/') + '/chat/completions'
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    payload = {
        "model": model,
        "messages": messages,
        "stream": True,
        "max_tokens": int(os.getenv("OPENAI_API_MAX_TOKENS", "4096")),
        "temperature": 0.7
    }
    
    timeout = int(os.getenv("OPENAI_API_TIMEOUT", "180"))
    with requests.post(api_url, headers=headers, json=payload, stream=True, timeout=timeout) as resp:
        resp.raise_for_status()
        for line in resp.iter_lines():
            if stop_event and stop_event.is_set():
                break
            if session_id and session_id in STREAM_SESSION_STOP and STREAM_SESSION_STOP[session_id]:
                break
            if not line:
                continue
            
            line_text = line.decode("utf-8")
            if line_text.startswith("data: "):
                line_text = line_text[6:]  # Remove "data: " prefix
            
            if line_text.strip() == "[DONE]":
                break
                
            try:
                data = json.loads(line_text)
                # OpenAI API streaming format
                if "choices" in data and len(data["choices"]) > 0:
                    delta = data["choices"][0].get("delta", {})
                    if "content" in delta:
                        yield delta["content"]
            except Exception:
                continue

# Global dict to track streaming sessions
STREAM_SESSION_STOP = {}

def stop_streaming_session(session_id):
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
            tool_name = "wikipedia"        # --- If no tool matched, use LLM with memory/context ---
        if not tool_used:
            def llm_query():
                # Embed user query and retrieve relevant memory
                query_emb = get_embedding(db_manager, user_message, request_id)
                memory_chunks = retrieve_user_memory(db_manager, user_id, query_emb, n_results=3, request_id=request_id) if query_emb is not None else []
                # Compose LLM context
                system_prompt = "You are a helpful assistant. Use the following memory and chat history to answer."
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
                error_handler=lambda e: ErrorHandler.log_error(e, "LLM query", user_id, request_id)
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
    
    return {
        "object": "list",
        "data": _model_cache["data"]
    }

@app.post("/v1/chat/completions")
async def openai_chat_completions(request: Request, body: dict = Body(...)):
    """
    OpenAI-compatible chat completions endpoint for OpenWebUI, with streaming support.
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
    chat_resp = await chat_endpoint(chat_req, request)    # Streaming support
    if stream:
        session_id = f"{user_id}:{body.get('model', DEFAULT_MODEL)}"
        STREAM_SESSION_STOP[session_id] = False
        def event_stream():
            logging.debug("[STREAM] Streaming response triggered.")
            for token in call_llm_stream(messages, model=body.get("model", DEFAULT_MODEL), session_id=session_id):
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
                yield f"data: {json.dumps(data)}\n\n"            # End of stream
            logging.debug("[STREAM] Streaming complete.")
            yield "data: [DONE]\n\n"
            STREAM_SESSION_STOP.pop(session_id, None)
        
        # Log streaming completion
        end_time = time.time()
        response_time = (end_time - start_time) * 1000
        log_api_request("POST", "/v1/chat/completions", 200, response_time)
        
        return StreamingResponse(event_stream(), media_type="text/event-stream")
    
    # Non-streaming response
    end_time = time.time()
    response_time = (end_time - start_time) * 1000
    response_length = len(chat_resp.response)
    message_length = sum(len(msg.get("content", "")) for msg in messages)
    
    # Log the chat interaction
    from human_logging import log_chat_interaction
    log_chat_interaction(user_id, message_length, response_length)
    log_api_request("POST", "/v1/chat/completions", 200, response_time)
    
    return {
        "id": "chatcmpl-1",
        "object": "chat.completion",
        "created": 0,
        "model": body.get("model", DEFAULT_MODEL),
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": chat_resp.response},
                "finish_reason": "stop"
            }
        ],
        "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
    }

@app.post("/api/chat/completions")
async def api_chat_completions(request: Request, body: dict = Body(...)):
    # Alias for OpenAI-compatible /v1/chat/completions endpoint, including streaming
    return await openai_chat_completions(request, body)

@app.post("/v1/stop_stream")
async def stop_stream(request: Request, body: dict = Body(...)):
    """
    Endpoint to stop a streaming session (e.g., when switching models or user cancels).
    """
    user_id = body.get("user_id")
    model = body.get("model", DEFAULT_MODEL)
    session_id = f"{user_id}:{model}"
    stop_streaming_session(session_id)
    return {"status": "stopped", "session_id": session_id}

@app.post("/api/stop_stream")
async def api_stop_stream(request: Request, body: dict = Body(...)):
    """
    Alias for /v1/stop_stream for OpenWebUI compatibility.
    """
    user_id = body.get("user_id")
    model = body.get("model", DEFAULT_MODEL)
    session_id = f"{user_id}:{model}"
    stop_streaming_session(session_id)
    return {"status": "stopped", "session_id": session_id}

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up services when FastAPI app shuts down."""
    global watchdog_thread
    
    if watchdog_thread and watchdog_thread.is_alive():
        logging.info("[SHUTDOWN] Stopping watchdog service...")
        # The watchdog service runs in a daemon thread, so it will stop automatically
        # when the main process exits
    
    logging.info("[SHUTDOWN] App shutdown complete")

# Redis dependency function (like the working implementation)
async def get_redis() -> Optional[redis.Redis]:
    """
    Provides a Redis client from the connection pool with Docker-optimized error handling.
    Tests connection before returning to ensure reliability in Docker environments.
    """
    if not hasattr(app.state, "redis_pool") or app.state.redis_pool is None:
        logging.error("[REDIS_DEPENDENCY] Redis pool not initialized")
        return None
    
    try:
        # Create a new client instance from the pool for this request
        r_client = redis.Redis(connection_pool=app.state.redis_pool)
        
        # Test connection before returning (important for Docker environments)
        r_client.ping()
        return r_client
        
    except redis.ConnectionError as e:
        logging.error(f"[REDIS_DEPENDENCY] Connection error getting Redis client: {e}")
        return None
    except Exception as e:
        logging.error(f"[REDIS_DEPENDENCY] Error getting Redis client from pool: {e}", exc_info=True)
        return None

async def verify_ollama_model_exists(model_name: str) -> bool:
    """Verify if a model exists in Ollama, return True if exists."""
    if not USE_OLLAMA:
        HumanLogger.log_service_status("MODEL", "skipped", "Ollama model check skipped - using OpenAI API")
        return True  # Skip verification for OpenAI models
        
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=10.0)
            if response.status_code == 200:
                data = response.json()
                models = data.get("models", [])
                for model in models:
                    model_name_full = model.get("name", "")
                    # Check for exact match or partial match (e.g., llama3.2:3b matches llama3.2:3b-something)
                    if model_name_full == model_name or model_name_full.startswith(model_name.split(":")[0]):
                        HumanLogger.log_service_status("MODEL", "available", f"Model {model_name} found as {model_name_full}")
                        return True
                HumanLogger.log_service_status("MODEL", "missing", f"Model {model_name} not found in Ollama")
                return False
            else:
                HumanLogger.log_service_status("MODEL", "error", f"Failed to check Ollama models: HTTP {response.status_code}")
                return False
    except httpx.ConnectError:
        HumanLogger.log_service_status("MODEL", "error", f"Cannot connect to Ollama at {OLLAMA_BASE_URL}")
        return False
    except Exception as e:
        HumanLogger.log_service_status("MODEL", "error", f"Failed to check model {model_name}: {str(e)}")
        return False

async def download_ollama_model(model_name: str) -> bool:
    """Download a model to Ollama if it doesn't exist."""
    if not USE_OLLAMA:
        HumanLogger.log_service_status("MODEL", "skipped", "Ollama model download skipped - using OpenAI API")
        return True
        
    try:
        HumanLogger.log_service_status("MODEL", "downloading", f"Downloading model {model_name} to Ollama")
        async with httpx.AsyncClient() as client:
            # Start the download
            response = await client.post(
                f"{OLLAMA_BASE_URL}/api/pull",
                json={"name": model_name},
                timeout=600.0  # 10 minutes timeout for model download
            )
            
            if response.status_code == 200:
                # For streaming responses, we need to read the stream
                async for line in response.aiter_lines():
                    if line:
                        try:
                            status_data = json.loads(line)
                            if "status" in status_data:
                                HumanLogger.log_service_status("MODEL", "downloading", f"{model_name}: {status_data['status']}")
                            if status_data.get("status") == "success":
                                HumanLogger.log_service_status("MODEL", "ready", f"Model {model_name} downloaded successfully")
                                return True
                        except json.JSONDecodeError:
                            continue
                
                # If we reach here, download completed
                HumanLogger.log_service_status("MODEL", "ready", f"Model {model_name} download completed")
                return True
            else:
                HumanLogger.log_service_status("MODEL", "error", f"Failed to download model {model_name}: HTTP {response.status_code}")
                return False
                
    except httpx.ConnectError:
        HumanLogger.log_service_status("MODEL", "error", f"Cannot connect to Ollama at {OLLAMA_BASE_URL} for download")
        return False
    except Exception as e:
        HumanLogger.log_service_status("MODEL", "error", f"Error downloading model {model_name}: {str(e)}")
        return False

async def ensure_model_available(model_name: str) -> bool:
    """Ensure a model is available, download if necessary."""
    if await verify_ollama_model_exists(model_name):
        return True
    
    HumanLogger.log_service_status("MODEL", "downloading", f"Model {model_name} not found, attempting download")
    return await download_ollama_model(model_name)

@app.get("/v1/models/verify/{model_name}")
async def verify_model(model_name: str):
    """Verify if a model exists and download if necessary."""
    try:
        exists = await verify_ollama_model_exists(model_name)
        if not exists:
            HumanLogger.log_service_status("MODEL", "downloading", f"Model {model_name} not found, downloading...")
            downloaded = await download_ollama_model(model_name)
            return {
                "model": model_name,
                "exists": False,
                "downloaded": downloaded,
                "status": "ready" if downloaded else "failed"
            }
        return {
            "model": model_name,
            "exists": True,
            "downloaded": False,
            "status": "ready"
        }
    except Exception as e:
        return {
            "model": model_name,
            "exists": False,
            "downloaded": False,
            "status": "error",
            "error": str(e)
        }

# Global model cache
_model_cache = {"data": [], "last_updated": 0, "ttl": 300}  # 5 minute TTL

async def refresh_model_cache():
    """Refresh the model cache by fetching from Ollama."""
    global _model_cache
    
    models_data = []
    
    # Get Ollama models dynamically
    if USE_OLLAMA:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=10.0)
                if response.status_code == 200:
                    ollama_data = response.json()
                    for model in ollama_data.get("models", []):
                        models_data.append({
                            "id": model["name"],
                            "object": "model",
                            "created": int(time.time()),
                            "owned_by": "ollama",
                            "permission": [],
                            "size": model.get("size", 0),
                            "modified_at": model.get("modified_at", ""),
                            "details": model.get("details", {})
                        })
                    HumanLogger.log_service_status("MODELS", "refreshed", f"Found {len(models_data)} Ollama models")
                else:
                    HumanLogger.log_service_status("MODELS", "warning", f"Failed to fetch Ollama models: HTTP {response.status_code}")
        except Exception as e:
            HumanLogger.log_service_status("MODELS", "error", f"Error fetching Ollama models: {str(e)}")
    
    # Add OpenAI models if enabled
    openai_models = [
        "gpt-4", "gpt-4-turbo", "gpt-3.5-turbo", "gpt-4o", "gpt-4o-mini"
    ]
    
    for model_id in openai_models:
        models_data.append({
            "id": model_id,
            "object": "model",
            "created": 1677649963,
            "owned_by": "openai",
            "permission": [],
        })
    
    # Update cache
    _model_cache = {
        "data": models_data,
        "last_updated": time.time(),
        "ttl": 300
    }
    
    return models_data

@app.post("/v1/models/refresh")
async def refresh_models():
    """Force refresh the model list from Ollama."""
    try:
        models = await refresh_model_cache()
        return {
            "status": "success",
            "message": f"Refreshed {len(models)} models",
            "models": [model["id"] for model in models if model["owned_by"] == "ollama"]
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to refresh models: {str(e)}"
        }

@app.get("/test")
async def test_endpoint():
    """Test endpoint to verify the updated code is running."""
    return {"message": "Updated backend is running", "default_model": DEFAULT_MODEL}

@app.get("/capabilities")
async def get_system_capabilities():
    """Get comprehensive system capabilities and features."""
    from storage_manager import StorageManager
    import json
    
    # Load persona information
    try:
        with open("persona.json", "r") as f:
            persona_data = json.load(f)
    except Exception:
        persona_data = {"error": "Could not load persona.json"}
    
    # Get storage information
    storage_info = StorageManager.get_storage_info()
    
    # Get database health
    db_health = get_database_health()
    
    # Count available tools
    available_tools = [
        "get_current_time", "get_weather", "convert_units", 
        "get_news", "web_search", "get_exchange_rate", "get_system_info", 
        "get_timezone_for_location", "run_python_code", "wikipedia_search"
    ]
    
    return {
        "system_name": "FastAPI LLM Backend with Self-Learning",
        "version": "2.0",
        "status": "production_ready",
        "capabilities": {
            "tools": {
                "count": len(available_tools),
                "available": available_tools,
                "features": [
                    "Real-time web search",
                    "Weather data retrieval", 
                    "Mathematical calculations",
                    "Unit conversions",
                    "News aggregation",
                    "Currency exchange rates",
                    "System information",
                    "Timezone operations",
                    "Wikipedia search",
                    "Python code execution"
                ]
            },
            "memory_and_storage": {
                "type": "Persistent vector storage",
                "providers": ["Redis", "ChromaDB"],
                "features": [
                    "Semantic memory search",
                    "Conversation history",
                    "User preference learning",
                    "Knowledge base expansion",
                    "Session continuity",
                    "Automatic backups"
                ],
                "storage_health": {
                    "redis": db_health.get("redis", {}).get("available", False),
                    "chromadb": db_health.get("chromadb", {}).get("available", False),
                    "total_storage_mb": sum(
                        dir_info.get('size_mb', 0) 
                        for dir_info in storage_info['directories'].values()
                    )
                }
            },
            "document_processing": {
                "chunking_strategies": [
                    {"name": "semantic", "description": "Content-aware boundaries"},
                    {"name": "adaptive", "description": "Dynamic sizing based on density"},
                    {"name": "hierarchical", "description": "Structure-aware processing"},
                    {"name": "fixed_size", "description": "Traditional consistent chunks"},
                    {"name": "paragraph", "description": "Natural paragraph breaks"},
                    {"name": "sentence", "description": "Sentence-level granularity"}
                ],
                "document_types": [
                    "text", "code", "markdown", "academic", "conversation", "structured"
                ],
                "features": [
                    "Quality assessment",
                    "Metadata extraction", 
                    "Type classification",
                    "Semantic chunking",
                    "Content summarization"
                ]
            },
            "learning_system": {
                "type": "Adaptive self-learning",
                "feedback_collection": [
                    "Positive feedback", "Negative feedback", 
                    "User corrections", "Clarification requests"
                ],
                "adaptation_areas": [
                    "Response personalization",
                    "Tool usage optimization",
                    "Context relevance improvement",
                    "Knowledge base expansion"
                ],
                "features": [
                    "Interaction pattern analysis",
                    "Automatic knowledge extraction",
                    "User preference tracking",
                    "Quality scoring"
                ]
            },
            "api_endpoints": {
                "health_monitoring": [
                    "/health", "/health/detailed", "/health/simple",
                    "/health/redis", "/health/chromadb", "/health/storage"
                ],
                "enhanced_features": [
                    "/enhanced/document/upload-advanced",
                    "/enhanced/feedback/interaction",
                    "/enhanced/insights/user/{user_id}",
                    "/enhanced/chat/enhanced",
                    "/enhanced/system/learning-status"
                ],
                "standard_endpoints": [
                    "/chat", "/upload/document", "/upload/search",
                    "/v1/chat/completions", "/v1/models"
                ]
            },
            "monitoring_and_reliability": {
                "health_checks": "Multi-level monitoring",
                "error_handling": "Comprehensive with recovery",
                "logging": "Human-readable structured logs",
                "storage_management": "Automatic directory creation",
                "restart_policy": "Always restart with data persistence"
            }
        },
        "persona": persona_data,
        "deployment": {
            "containerized": True,
            "services": ["Redis", "ChromaDB", "Ollama", "OpenWebUI", "Backend"],
            "persistent_storage": True,
            "auto_restart": True,
            "health_monitoring": True
        },
        "integrations": {
            "llm_providers": ["Ollama (local)", "OpenAI API (fallback)"],
            "vector_database": "ChromaDB",
            "cache_layer": "Redis",
            "web_interface": "OpenWebUI",
            "model_support": ["llama3.2:3b", "GPT-4", "Custom embeddings"]
        }
    }

@app.post("/feedback")
async def feedback_alias(request: Request):
    """Alias for /enhanced/feedback/interaction for OpenWebUI rating integration."""
    data = await request.json()
    # Map OpenWebUI rating fields to backend feedback fields
    user_id = data.get("user_id") or data.get("user")
    conversation_id = data.get("conversation_id") or data.get("conv_id")
    user_message = data.get("user_message") or data.get("input")
    assistant_response = data.get("assistant_response") or data.get("output")
    feedback_type = data.get("feedback_type") or data.get("rating")
    response_time = data.get("response_time", 0)
    tools_used = data.get("tools_used")
    # Forward to the enhanced feedback endpoint

    from fastapi.responses import JSONResponse
    from enhanced_integration import submit_interaction_feedback
    try:
        result = await submit_interaction_feedback(
            user_id=user_id,
            conversation_id=conversation_id,
            user_message=user_message,
            assistant_response=assistant_response,
            feedback_type=feedback_type,
            response_time=response_time,
            tools_used=tools_used
        )
        return result
    except Exception as e:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"success": False, "error": str(e)})

async def unload_ollama_model(model_name: str) -> bool:
    """Unload a model from Ollama memory if supported."""
    if not USE_OLLAMA:
        HumanLogger.log_service_status("MODEL", "skipped", "Ollama model unload skipped - using OpenAI API")
        return True
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{OLLAMA_BASE_URL}/api/unload", json={"name": model_name}, timeout=30)
            if response.status_code == 200:
                HumanLogger.log_service_status("MODEL", "unloaded", f"Model {model_name} unloaded from memory")
                return True
            else:
                HumanLogger.log_service_status("MODEL", "warning", f"Model {model_name} unload failed: HTTP {response.status_code}")
                return False
    except Exception as e:
        HumanLogger.log_service_status("MODEL", "warning", f"Model {model_name} unload failed: {e}")
        return False

@app.post("/v1/models/added")
async def model_added_webhook(model_data: dict = Body(...)):
    """Webhook endpoint to notify when a new model is added."""
    try:
        model_name = model_data.get("name", "unknown")
        HumanLogger.log_service_status("MODEL", "added", f"New model detected: {model_name}")
        
        # Force refresh the model cache
        await refresh_model_cache()
        
        # Log available models
        ollama_models = [model["id"] for model in _model_cache["data"] if model["owned_by"] == "ollama"]
        HumanLogger.log_service_status("MODELS", "updated", f"Available Ollama models: {', '.join(ollama_models)}")
        
        return {
            "status": "success",
            "message": f"Model {model_name} registered successfully",
            "available_models": ollama_models
        }
    except Exception as e:
        HumanLogger.log_service_status("MODEL", "error", f"Error processing model addition: {str(e)}")
        return {
            "status": "error",
            "message": f"Failed to process model addition: {str(e)}"
        }
