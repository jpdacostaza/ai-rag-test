"""
FastAPI backend for the AI-powered application.
"""

# CRITICAL: Import and enforce CPU-only mode BEFORE any ML libraries
from cpu_enforcer import enforce_cpu_only_mode, verify_cpu_only_setup, log_cpu_verification_results

# Enforce CPU-only mode immediately
enforce_cpu_only_mode()

import asyncio
import itertools
import json
import logging
import os
import platform
import re
import sys
import time
import uuid
from dataclasses import asdict
from datetime import datetime
from typing import AsyncGenerator
from typing import Dict
from typing import Optional

import httpx
from fastapi import Body
from fastapi import Depends
from fastapi import FastAPI
from fastapi import Request
from fastapi import HTTPException
from fastapi.responses import StreamingResponse
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel
from starlette.exceptions import HTTPException as StarletteHTTPException

from ai_tools import convert_units
from ai_tools import get_current_time
from ai_tools import get_weather
from database_manager import db_manager
from database_manager import get_cache
from database_manager import get_chat_history
from database_manager import get_database_health
from database_manager import get_embedding
from database_manager import index_user_document
from database_manager import retrieve_user_memory
from database_manager import set_cache
from database_manager import store_chat_history
from error_handler import CacheErrorHandler
from error_handler import ChatErrorHandler
from error_handler import MemoryErrorHandler
from error_handler import ToolErrorHandler
from error_handler import log_error
from error_handler import safe_execute
from human_logging import init_logging
from human_logging import log_api_request
from human_logging import log_service_status

# Import routers
from model_manager import router as model_manager_router
from model_manager import ensure_model_available
from upload import upload_router
from enhanced_integration import enhanced_router
from feedback_router import feedback_router
from adaptive_learning import adaptive_learning_system
# from v1_models_fix import v1_router  # Commented out - module not found

# Create stub functions for missing imports
def initialize_storage():
    """Stub function for storage initialization."""
    return True

def initialize_cache_management():
    """Stub function for cache management initialization."""
    return True

def get_cache_manager():
    """Stub function to get cache manager."""
    return None

def start_watchdog_service():
    """Stub function for watchdog service."""
    return None

async def start_enhanced_background_tasks():
    """Stub function for enhanced background tasks."""
    return None

def get_time_from_timeanddate(country: str):
    """Stub function for time from timeanddate."""
    return f"Time in {country}: Not available"

class MockWatchdog:
    """Mock watchdog class."""
    def __init__(self):
        self.monitors = []
    
    def get_service_history(self, service_name: str, hours: int):
        return []

def get_watchdog():
    """Stub function to get watchdog."""
    return MockWatchdog()

# Simple API key verification for pipelines
def verify_api_key(api_key: Optional[str] = None):
    """Simple API key verification - implement proper security as needed"""
    # For now, accept any key for development - replace with proper validation
    return api_key or "development"

async def get_health_status():
    """Stub function for health status."""
    return {}

class StorageManager:
    """Stub class for storage manager."""
    @staticmethod
    def get_storage_info():
        return {"directories": {}}
    
    @staticmethod  
    def validate_permissions():
        return {}

# Model cache stub
_model_cache = {"data": [], "last_updated": 0, "ttl": 300}

async def refresh_model_cache(force: bool = False):
    """Refresh the model cache from Ollama."""
    global _model_cache
    
    current_time = time.time()
    # Check if refresh is needed
    if not force and (current_time - _model_cache["last_updated"]) < _model_cache["ttl"]:
        log_service_status("MODELS", "info", "Model cache is still fresh, skipping refresh")
        return [model["id"] for model in _model_cache["data"]] if _model_cache["data"] else []
    
    try:
        ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{ollama_url}/api/tags")
            
            if response.status_code == 200:
                data = response.json()
                raw_models = data.get("models", [])
                
                # Transform models to OpenAI-compatible format
                models = []
                for model in raw_models:
                    openai_model = {
                        "id": model.get("name", "unknown"),
                        "object": "model",
                        "created": int(time.time()),
                        "owned_by": "ollama",
                        "permission": [],
                        "root": model.get("name", "unknown"),
                        "parent": None,                        # Store original Ollama data for internal use
                        "_ollama_data": model
                    }
                    models.append(openai_model)
                
                # Update cache
                _model_cache["data"] = models
                _model_cache["last_updated"] = current_time
                
                log_service_status("MODELS", "ready", f"Refreshed model cache with {len(models)} models")
                return [model["id"] for model in models]  # Return just the model names for compatibility
            else:
                log_service_status("MODELS", "warning", f"Failed to fetch models: HTTP {response.status_code}")
                return [model["id"] for model in _model_cache["data"]]  # Return cached data on failure
    except Exception as e:
        log_service_status("MODELS", "warning", f"Error refreshing model cache: {e}")
        return [model["id"] for model in _model_cache["data"]] if _model_cache["data"] else []

app = FastAPI()

# Add root endpoint for basic connectivity test
@app.get("/")
async def root():
    """Root endpoint to verify API is accessible."""
    return {"message": "FastAPI LLM Backend is running", "status": "ok"}

# Global Exception Handlers (FastAPI Best Practice)
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Handle HTTP exceptions with structured responses."""
    log_service_status("HTTP_ERROR", "warning", f"HTTP {exc.status_code}: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "type": "http_error",
                "code": exc.status_code,
                "message": exc.detail,
                "timestamp": datetime.now().isoformat()
            }
        }
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle request validation errors with detailed information."""
    request_id = getattr(request.state, 'request_id', str(uuid.uuid4()))
    log_service_status("VALIDATION_ERROR", "warning", f"Validation error: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "type": "validation_error",
                "code": 422,
                "message": "Request validation failed",
                "details": exc.errors(),
                "request_id": request_id,
                "timestamp": datetime.now().isoformat()
            }
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected errors with proper logging."""
    request_id = getattr(request.state, 'request_id', str(uuid.uuid4()))
    log_service_status("INTERNAL_ERROR", "error", f"Unhandled exception [{request_id}]: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "type": "internal_error",
                "code": 500,
                "message": "An internal server error occurred",
                "request_id": request_id,
                "timestamp": datetime.now().isoformat()
            }
        }
    )

app.include_router(model_manager_router)
# app.include_router(v1_router)  # Working /v1/models endpoint - commented out

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

# Track application startup time
_app_start_time = time.time()


async def _spinner_log(message, duration=2, interval=0.2):
    """Show a spinner/progress animation in the logs for a given duration."""
    spinner = itertools.cycle(["|", "/", "-", "\\"])
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
    
    # CPU-only mode verification
    log_service_status("STARTUP", "starting", "Verifying CPU-only mode...")
    cpu_results = verify_cpu_only_setup()
    log_cpu_verification_results(cpu_results)
    
    if cpu_results["status"] == "warning":
        log_service_status("STARTUP", "warning", "CPU-only mode verification has warnings - check logs")
    elif cpu_results["status"] == "cpu_only_verified":
        log_service_status("STARTUP", "ready", "✅ CPU-only mode verified successfully")
    else:
        log_service_status("STARTUP", "degraded", "CPU-only mode verification incomplete")
    
    _log_system_info()
    _log_environment_variables()

    # Storage
    log_service_status("STARTUP", "starting", "Initializing storage structure...")
    await _spinner_log("[STARTUP] Initializing storage structure", 2)

    storage_success = initialize_storage()
    if not storage_success:
        log_service_status(
            "STARTUP",
            "degraded",
            "Storage initialization had issues - some features may be affected",
        )
    else:
        log_service_status("STARTUP", "ready", "Storage structure initialized successfully")

    # Database
    log_service_status("STARTUP", "starting", "Initializing database connections...")
    await _spinner_log("[STARTUP] Initializing database connections", 2)

    # Store Redis pool in app state for dependency injection (like working implementation)
    if hasattr(db_manager, "redis_pool") and db_manager.redis_pool is not None:
        app.state.redis_pool = db_manager.redis_pool
        log_service_status("STARTUP", "ready", "Redis pool stored in app state")
    else:
        app.state.redis_pool = None
        log_service_status(
            "STARTUP", "degraded", "Redis pool not available - some features may be degraded"
        )
      # Model verification and auto-pull
    log_service_status("STARTUP", "starting", f"Ensuring model availability: {DEFAULT_MODEL}")
    await _spinner_log(f"[MODEL] Checking/downloading {DEFAULT_MODEL}", 2)
    try:
        model_available = await ensure_model_available(DEFAULT_MODEL, auto_pull=True)
        if model_available:
            log_service_status("MODEL", "ready", f"Default model {DEFAULT_MODEL} is available")
            # Preload model into memory by running a dummy inference
            try:
                preload_payload = {"model": DEFAULT_MODEL, "prompt": "Hello!", "stream": False}
                async with httpx.AsyncClient() as client:
                    resp = await client.post(
                        f"{OLLAMA_BASE_URL}/api/generate", json=preload_payload, timeout=60
                    )
                    if resp.status_code == 200:
                        log_service_status(
                            "MODEL", "preloaded", f"Model {DEFAULT_MODEL} preloaded into memory"
                        )
                    else:
                        log_service_status(
                            "MODEL",
                            "warning",
                            f"Model {DEFAULT_MODEL} preload failed: HTTP {resp.status_code}",
                        )
            except Exception as e:
                log_service_status("MODEL", "warning", f"Model {DEFAULT_MODEL} preload failed: {e}")
        else:
            log_service_status(
                "MODEL", "error", f"Failed to ensure default model {DEFAULT_MODEL} is available"
            )
    except Exception as e:
        log_service_status(
            "MODEL", "error", f"Error ensuring default model {DEFAULT_MODEL}: {str(e)}"
        )
    # Initialize model cache on startup
    log_service_status("STARTUP", "starting", "Initializing model cache...")
    await refresh_model_cache()

    # Initialize cache management system
    log_service_status("STARTUP", "starting", "Initializing cache management...")

    cache_init_success = initialize_cache_management()
    if cache_init_success:
        log_service_status("CACHE", "ready", "Cache management system initialized successfully")
    else:
        log_service_status("CACHE", "warning", "Cache management initialization had issues")

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
    log_service_status(
        "ENHANCED_SYSTEM", "ready", "Enhanced learning and document processing systems initialized"
    )

    # Final summary banner
    await _spinner_log("[STARTUP] Finalizing startup", 1)
    _print_startup_summary()
    log_service_status("STARTUP", "ready", "🚀 FastAPI LLM Backend startup completed successfully!")


def _print_startup_summary():
    """Print a visually distinct summary banner with health status of all services."""

    health = get_database_health()
    lines = [
        "\n================= SERVICE STATUS SUMMARY =================",
        f"Redis:      {'✅' if health['redis']['available'] else '❌'}",
        f"ChromaDB:   {'✅' if health['chromadb']['available'] else '❌'}",
        f"Embeddings: {'✅' if health['embeddings']['available'] else '❌'}",
        "========================================================\n",
    ]
    for line in lines:
        print(line)


def _log_system_info():
    """Log system information for startup diagnostics."""
    try:
        log_service_status("SYSTEM", "info", f"Python version: {sys.version.split()[0]}")
        log_service_status("SYSTEM", "info", f"Platform: {platform.system()} {platform.release()}")
        log_service_status("SYSTEM", "info", f"Working directory: {os.getcwd()}")

    except Exception as e:
        log_service_status("SYSTEM", "warning", f"Failed to log system info: {e}")


def _log_environment_variables():
    """Log relevant environment variables for startup diagnostics."""
    try:

        env_vars_to_log = [
            "REDIS_HOST",
            "REDIS_PORT",
            "CHROMA_HOST",
            "CHROMA_PORT",
            "DEFAULT_MODEL",
            "EMBEDDING_MODEL",
            "SENTENCE_TRANSFORMERS_HOME",
            "OLLAMA_BASE_URL",
            "USE_OLLAMA",
            "USE_HTTP_CHROMA",
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
    print("[CONSOLE DEBUG] Health endpoint called!")
    health_status = get_database_health()

    # Add cache information

    cache_manager = get_cache_manager()
    cache_info = {}
    if cache_manager:
        cache_info = cache_manager.get_cache_stats()

    services = [
        ("Redis", health_status["redis"]["available"]),
        ("ChromaDB", health_status["chromadb"]["available"]),
        ("Embeddings", health_status["embeddings"]["available"]),
    ]
    healthy = sum(1 for _, ok in services if ok)
    total = len(services)
    summary = f"Health check: {healthy}/{total} services healthy. " + ", ".join(
        [f"{name}: {'✅' if ok else '❌'}" for name, ok in services]
    )

    response = {
        "status": "ok" if healthy == total else "degraded",
        "summary": summary,
        "databases": health_status,
    }

    if cache_info:
        response["cache"] = cache_info

    return response


@app.get("/health/simple")
async def simple_health():
    """Simple health check without any dependencies."""
    return {
        "status": "ok", 
        "timestamp": datetime.now().isoformat(),
        "uptime_seconds": time.time() - _app_start_time,
        "message": "Simple health check working"
    }


@app.get("/health/detailed")
async def detailed_health_check():
    """Detailed health check with subsystem monitoring."""
    health_status = await get_health_status()  # Correctly call the helper function

    # The health_status is now a dictionary of ServiceHealth objects
    # We need to process it for the final response

    services = {name: asdict(status) for name, status in health_status.items()}
    healthy_count = sum(1 for s in services.values() if s["status"] == "healthy")
    degraded_count = sum(1 for s in services.values() if s["status"] == "degraded")
    unhealthy_count = sum(1 for s in services.values() if s["status"] == "unhealthy")

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
            "unhealthy_services": unhealthy_count,
        },
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
        "history": [h.__dict__ for h in history],
    }


@app.get("/health/storage")
async def storage_health():
    """Check storage directory structure and permissions."""

    # Get storage information
    storage_info = StorageManager.get_storage_info()

    # Validate permissions
    permissions = StorageManager.validate_permissions()

    # Calculate total storage usage
    total_size_mb = sum(
        dir_info.get("size_mb", 0) for dir_info in storage_info["directories"].values()
    )

    # Count directories
    existing_dirs = sum(
        1 for dir_info in storage_info["directories"].values() if dir_info["exists"]
    )
    total_dirs = len(storage_info["directories"])

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
        "base_path": storage_info["base_path"],
        "directories": {
            "total": total_dirs,
            "existing": existing_dirs,
            "missing": total_dirs - existing_dirs,
        },
        "storage_usage": {
            "total_size_mb": total_size_mb,
            "total_files": sum(
                dir_info.get("file_count", 0) for dir_info in storage_info["directories"].values()
            ),
        },
        "permissions": permissions,
        "directory_details": storage_info["directories"],
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
    model = model or DEFAULT_MODEL    # Debug logging to see what messages are being sent
    logging.info(f"[DEBUG] Sending {len(messages)} messages to Ollama model {model}")
    for i, msg in enumerate(messages):
        logging.info(f"[DEBUG] Message {i}: role='{msg.get('role')}', content='{msg.get('content', '')[:100]}...'")

    # Use Ollama's chat endpoint which provides better control over system prompts
    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
        "options": {"temperature": 0.7, "top_p": 0.9},
    }
    timeout = int(os.getenv("LLM_TIMEOUT", "180"))

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{OLLAMA_BASE_URL}/api/chat", json=payload, timeout=timeout
            )
            response.raise_for_status()
            data = response.json()
            llm_response = data.get("message", {}).get("content", "")
            logging.info(f"[DEBUG] Ollama response length: {len(llm_response)} chars")
            logging.info(f"[DEBUG] Ollama response content: '{llm_response[:200]}...'")
            return llm_response
    except httpx.RequestError as e:
        log_service_status(
            "OLLAMA", "failed", f"Connection to Ollama at {OLLAMA_BASE_URL} failed: {e}"
        )
        raise Exception(f"Cannot connect to Ollama service at {OLLAMA_BASE_URL}") from e
    except httpx.HTTPStatusError as e:
        log_service_status(
            "OLLAMA",
            "failed",
            f"Ollama API returned an error: {e.response.status_code} - {e.response.text}",
        )
        raise


async def call_openai_llm(messages, model=None, api_url=None, api_key=None):
    """
    Asynchronously calls an OpenAI-compatible API.
    """
    model = model or DEFAULT_MODEL
    api_url = api_url or os.getenv("OPENAI_API_BASE_URL", "https://api.openai.com/v1")
    api_key = api_key or os.getenv("OPENAI_API_KEY")

    if not api_url.endswith("/chat/completions"):
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
        log_service_status(
            "OPENAI",
            "failed",
            f"OpenAI API returned an error: {e.response.status_code} - {e.response.text}",
        )
        raise


async def call_llm_stream(
    messages, model=None, api_url=None, api_key=None, stop_event=None, session_id=None
):
    """
    Streams tokens from an LLM API (Ollama or OpenAI) in real time.
    """
    model = model or DEFAULT_MODEL
    if USE_OLLAMA:
        return call_ollama_llm_stream(messages, model, stop_event, session_id)
    else:
        return call_openai_llm_stream(messages, model, api_url, api_key, stop_event, session_id)


async def call_ollama_llm_stream(
    messages, model=None, stop_event=None, session_id=None
) -> AsyncGenerator[str, None]:
    """
    Asynchronously streams tokens from the Ollama API with proper resource management.
    """
    model = model or DEFAULT_MODEL
    prompt = "\n".join(
        f"{msg.get('role', 'user').capitalize()}: {msg.get('content', '')}" for msg in messages
    )
    payload = {"model": model, "prompt": prompt, "stream": True}
    timeout = int(os.getenv("LLM_TIMEOUT", "180"))

    client = None
    try:
        client = httpx.AsyncClient(timeout=timeout)
        async with client.stream(
            "POST", f"{OLLAMA_BASE_URL}/api/generate", json=payload
        ) as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                # Check stop conditions
                if (stop_event and stop_event.is_set()) or (
                    session_id and STREAM_SESSION_STOP.get(session_id)
                ):
                    log_service_status("OLLAMA", "info", f"Stream stopped for session {session_id}")
                    break
                    
                if not line:
                    continue
                    
                try:
                    data = json.loads(line)
                    if "response" in data:
                        yield data["response"]
                    if data.get("done"):
                        log_service_status("OLLAMA", "info", "Stream completed successfully")
                        break
                except json.JSONDecodeError:
                    continue
                    
    except httpx.RequestError as e:
        log_service_status("OLLAMA", "failed", f"Streaming connection to Ollama failed: {e}")
        yield "Error: Cannot connect to Ollama service"
    except Exception as e:
        log_service_status("OLLAMA", "failed", f"Ollama streaming failed: {e}")
        yield f"Error: {str(e)}"
    finally:
        # Ensure proper cleanup
        if client:
            await client.aclose()
        if session_id and session_id in STREAM_SESSION_STOP:
            STREAM_SESSION_STOP.pop(session_id, None)


async def call_openai_llm_stream(
    messages, model=None, api_url=None, api_key=None, stop_event=None, session_id=None
) -> AsyncGenerator[str, None]:
    """
    Asynchronously streams tokens from an OpenAI-compatible API with proper resource management.
    """
    model = model or DEFAULT_MODEL
    api_url = api_url or os.getenv("OPENAI_API_BASE_URL", "https://api.openai.com/v1")
    api_key = api_key or os.getenv("OPENAI_API_KEY")

    if not api_url.endswith("/chat/completions"):
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

    client = None
    try:
        client = httpx.AsyncClient(timeout=timeout)
        async with client.stream(
            "POST", api_url, headers=headers, json=payload
        ) as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                # Check stop conditions
                if (stop_event and stop_event.is_set()) or (
                    session_id and STREAM_SESSION_STOP.get(session_id)
                ):
                    log_service_status("OPENAI", "info", f"Stream stopped for session {session_id}")
                    break
                    
                if not line or not line.startswith("data: "):
                    continue

                line_text = line[6:]
                if line_text.strip() == "[DONE]":
                    log_service_status("OPENAI", "info", "Stream completed successfully")
                    break

                try:
                    data = json.loads(line_text)
                    if (
                        (choices := data.get("choices"))
                        and (delta := choices[0].get("delta"))
                        and (content := delta.get("content"))
                    ):
                        yield content
                except json.JSONDecodeError:
                    continue
                    
    except httpx.RequestError as e:
        log_service_status("OPENAI", "failed", f"Streaming connection to OpenAI API failed: {e}")
        yield "Error: Cannot connect to OpenAI API"
    except Exception as e:
        log_service_status("OPENAI", "failed", f"OpenAI streaming failed: {e}")
        yield f"Error: {str(e)}"
    finally:
        # Ensure proper cleanup
        if client:
            await client.aclose()
        if session_id and session_id in STREAM_SESSION_STOP:
            STREAM_SESSION_STOP.pop(session_id, None)


# Global dict to track streaming sessions with enhanced management
STREAM_SESSION_STOP: Dict[str, bool] = {}
STREAM_SESSION_METADATA: Dict[str, dict] = {}


def stop_streaming_session(session_id: str):
    """Stop a streaming session and cleanup metadata."""
    STREAM_SESSION_STOP[session_id] = True
    if session_id in STREAM_SESSION_METADATA:
        STREAM_SESSION_METADATA[session_id]["stopped_at"] = time.time()


def cleanup_old_sessions(max_age_seconds: int = 3600):
    """Clean up old streaming sessions to prevent memory leaks."""
    current_time = time.time()
    sessions_to_remove = []
    
    for session_id, metadata in STREAM_SESSION_METADATA.items():
        if current_time - metadata.get("created_at", 0) > max_age_seconds:
            sessions_to_remove.append(session_id)
    
    for session_id in sessions_to_remove:
        STREAM_SESSION_STOP.pop(session_id, None)
        STREAM_SESSION_METADATA.pop(session_id, None)
    
    if sessions_to_remove:
        log_service_status("SESSION_CLEANUP", "info", f"Cleaned up {len(sessions_to_remove)} old streaming sessions")


# --- Chat Endpoint ---
class ChatRequest(BaseModel):
    user_id: str
    message: str


class ChatResponse(BaseModel):
    response: str


@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(chat: ChatRequest, request: Request):
    # Use request ID from middleware
    request_id = getattr(request.state, 'request_id', str(uuid.uuid4()))
    print(f"[CONSOLE DEBUG] Chat endpoint called for user {chat.user_id}, message: {chat.message[:50]}...")
    logging.info(f"[DEBUG] Chat endpoint called for user {chat.user_id}")

    try:
        user_message = chat.message
        user_id = chat.user_id
        user_response = None

        # Validate input
        if not user_message.strip():
            raise HTTPException(
                status_code=400, 
                detail="Message cannot be empty"
            )

        logging.debug(
            f"[REQUEST {request_id}] Chat request from user {user_id}: {user_message[:100]}..."
        )

        # --- Check cache before tool/LLM logic ---
        cache_key = f"chat:{user_id}:{user_message}"
        cached = None
        logging.debug(f"[CACHE] Checking cache for key: {cache_key}")        # Bypass cache for time queries to ensure real-time lookup
        is_time_query = False
        timeanddate_pattern = re.compile(
            r"time(?:\\s*(?:in|for|at))?\\s+([a-zA-Z ]+)", re.IGNORECASE
        )
        if (
            "timeanddate.com" in user_message.lower()
            or (
                timeanddate_pattern.search(user_message)
                and not any(
                    x in user_message.lower()
                    for x in [
                        "weather",
                        "convert",
                        "calculate",
                        "exchange rate",
                        "system info",
                        "news",
                        "search",
                    ]
                )
            )
            or "time" in user_message.lower()
        ):
            is_time_query = True
        
        if not is_time_query:
            cached = get_cache(db_manager, cache_key)
            if cached and str(cached).strip():  # Only return non-empty cached responses
                logging.info(f"[CACHE] Returning cached response for user {user_id}")
                return ChatResponse(response=str(cached))

        # --- Retrieve chat history and memory ---
        def get_history():
            return get_chat_history(user_id, limit=10)

        history = safe_execute(
            get_history,
            fallback_value=[],
            error_handler=lambda e: CacheErrorHandler.handle_cache_error(
                e, "get_history", f"history:{user_id}", user_id, request_id
            ),
        )
        
        logging.debug(f"[CHAT_HISTORY] Retrieved {len(history or [])} history entries for user {user_id}")
        
        # --- Intent/tool detection (tool results take precedence) ---
        tool_used = False
        tool_name = None
        debug_info = []
        
        # Debug logging for tool detection
        logging.debug(f"[TOOL_DEBUG] Analyzing message: '{user_message}'")
          # --- Robust time query detection ---
        time_query = False
        match = None
        # Match phrases like "time in", "current time in", "what is the time in", etc.
        time_patterns = [
            r"time(?:\s*(?:in|for|at))?\s+([a-zA-Z ]+)",
            r"current time in ([a-zA-Z ]+)",
            r"what(?:'s| is) the time in ([a-zA-Z ]+)",
            r"timeanddate\\.com.*([a-zA-Z ]+)",
        ]
        for pat in time_patterns:
            m = re.search(pat, user_message, re.IGNORECASE)
            if m:
                match = m
                time_query = True
                break
                
        if time_query or "timeanddate.com" in user_message.lower():
            logging.debug(f"[TOOL_DEBUG] Time query detected!")
            system_msg = f"[TOOL] Robust time lookup (geo+timezone, fallback to timeanddate.com) triggered for user {user_id}"
            logging.debug(system_msg)
            debug_info.append(system_msg)
            country = match.group(1).strip() if match else "netherlands"            # Clean up extracted location string - avoid removing "to" from middle of words like "Tokyo"
            logging.debug(f"[TIME_DEBUG] Original country: '{country}'")
            # Only remove words at word boundaries, not parts of words
            country = re.sub(
                r"^(is|what|'s|the|current|now|please|tell|me|show|give|provide|can|you|do|does|in|for|at|on|of|about|time|current time|the time)\s+",
                "",
                country,
                flags=re.IGNORECASE,
            )
            # Remove leading/trailing whitespace
            country = country.strip()
            logging.debug(f"[TIME_DEBUG] After cleaning: '{country}'")
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
                    "sydney": "Australia/Sydney",
                }

                tz = country_timezones.get(country.lower(), None)
                if tz:
                    return get_current_time(tz) + f" (timezone: {tz})", "geo_timezone"
                else:
                    return get_time_from_timeanddate(country), "timeanddate.com"

            result = safe_execute(
                get_timezone_time,
                fallback_value=(
                    ToolErrorHandler.handle_tool_error(
                        Exception("Time lookup failed"), "time", user_id, country, request_id
                    ),
                    "error",
                ),
                error_handler=lambda e: ToolErrorHandler.handle_tool_error(
                    e, "time", user_id, country, request_id
                ),
            )

            user_response, tool_name = result
            tool_used = True
            debug_info.append(f"[TOOL] Used {tool_name} for {country}")
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
                fallback_value=ToolErrorHandler.handle_tool_error(
                    Exception("Weather lookup failed"), "weather", user_id, city, request_id
                ),
                error_handler=lambda e: ToolErrorHandler.handle_tool_error(
                    e, "weather", user_id, city, request_id
                ),
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
                get_current_time,
                tz,
                fallback_value=ToolErrorHandler.handle_tool_error(
                    Exception("Time lookup failed"), "time", user_id, str(city), request_id
                ),
                error_handler=lambda e: ToolErrorHandler.handle_tool_error(
                    e, "time", user_id, str(city), request_id                ),
            )
            tool_used = True
            tool_name = "time"

        elif "convert" in user_message.lower() and "to" in user_message.lower():
            system_msg = f"[TOOL] Unit conversion triggered for user {user_id}"
            logging.debug(system_msg)
            debug_info.append(system_msg)
            match = re.search(
                r"convert ([\d\.]+) ([a-zA-Z]+(?:s)?) to ([a-zA-Z]+(?:s)?)", user_message, re.IGNORECASE
            )
            if match:
                value, from_unit, to_unit = float(match.group(1)), match.group(2), match.group(3)
                user_response = safe_execute(
                    convert_units,
                    value,
                    from_unit,
                    to_unit,
                    fallback_value=ToolErrorHandler.handle_tool_error(
                        Exception("Unit conversion failed"),
                        "unit_conversion",
                        user_id,
                        f"{value} {from_unit} to {to_unit}",
                        request_id,
                    ),
                    error_handler=lambda e: ToolErrorHandler.handle_tool_error(
                        e,
                        "unit_conversion",
                        user_id,
                        f"{value} {from_unit} to {to_unit}",
                        request_id,
                    ),
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
                fallback_value=(
                    ToolErrorHandler.handle_tool_error(
                        Exception("Web search failed"), "web_search", user_id, query, request_id
                    ),
                    [],
                ),
                error_handler=lambda e: ToolErrorHandler.handle_tool_error(
                    e, "web_search", user_id, query, request_id
                ),
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
            match = re.search(
                r"exchange rate ([a-zA-Z]{3}) to ([a-zA-Z]{3})", user_message, re.IGNORECASE
            )
            if match:
                from_cur, to_cur = match.group(1), match.group(2)
                user_response = (
                    f"Exchange rate lookup from {from_cur} to {to_cur} is currently unavailable."
                )
            else:
                user_response = "Exchange rate lookup is currently unavailable."
            tool_used = True
            tool_name = "exchange_rate"

        elif "system info" in user_message.lower():
            system_msg = f"[TOOL] System info lookup triggered for user {user_id}"
            logging.debug(system_msg)
            debug_info.append(system_msg)
            user_response = "System info lookup is currently unavailable."
            tool_used = True
            tool_name = "system_info"

        elif (
            "run python" in user_message.lower()
            or user_message.lower().startswith("python ")
            or "python code" in user_message.lower()
        ):
            system_msg = f"[TOOL] Python code execution triggered for user {user_id}"
            logging.debug(system_msg)
            debug_info.append(system_msg)
            # Extract code after 'run python' or after 'python ' or find code in the message
            if "```python" in user_message:
                # Extract code from code blocks
                code_start = user_message.find("```python") + 9
                code_end = user_message.find("```", code_start)
                code = (
                    user_message[code_start:code_end].strip()
                    if code_end != -1
                    else user_message[code_start:].strip()
                )
            elif "run python" in user_message.lower():
                code = user_message.split("run python", 1)[-1].strip()
            elif user_message.lower().startswith("python "):
                code = user_message.split("python ", 1)[-1].strip()
            else:
                # Try to extract any code-like text
                code = user_message.strip()

            if not code:
                user_response = "Please provide Python code to execute."
            else:
                user_response = "Python code execution is currently unavailable."
            tool_used = True
            tool_name = "python_code_execution"

        elif "wikipedia" in user_message.lower() or "wiki" in user_message.lower():
            system_msg = f"[TOOL] Wikipedia search triggered for user {user_id}"
            logging.debug(system_msg)
            debug_info.append(system_msg)
            # Extract search query
            query = (
                user_message.lower()
                .replace("wikipedia", "")
                .replace("wiki", "")
                .replace("search", "")
                .strip()
            )
            if not query:
                query = "artificial intelligence"  # default
            user_response = "Wikipedia search is currently unavailable."
            tool_used = True
            tool_name = "wikipedia"        
        # If no tool matched, use LLM with memory/context
        print(f"[CONSOLE DEBUG] About to check tool_used: {tool_used}")  # This will show in console
        logging.info(f"[DEBUG] Tool detection complete: tool_used={tool_used}")
        logging.info(f"[DEBUG] About to check if tool_used is False to call LLM")
        if not tool_used:
            logging.info(f"[DEBUG] No tool used, proceeding with LLM query for user {user_id}")

            async def llm_query():
                print(f"[CONSOLE DEBUG] LLM query function called for user {user_id}")
                logging.info(f"[DEBUG] LLM query function called for user {user_id}")
                # Embed user query and retrieve relevant memory
                query_emb = get_embedding(user_message)
                print(f"[CONSOLE DEBUG] Generated embedding for user {user_id}: {query_emb is not None}")
                logging.info(f"[DEBUG] Generated embedding for user {user_id}: {query_emb is not None}")
                memory_chunks = (
                    retrieve_user_memory(user_id, user_message, limit=3)
                    if query_emb is not None
                    else []
                )
                logging.info(f"[DEBUG] Retrieved {len(memory_chunks) if memory_chunks else 0} memory chunks for user {user_id}")

                # Compose LLM context with explicit instructions for plain text responses
                system_prompt = "You are a helpful assistant. Use the following memory and chat history to answer. \
                    Always respond with plain text only - never use JSON formatting, structured responses, or any special formatting. Just provide direct, natural language answers."

                # Check for system prompt changes and invalidate cache if needed
                cache_manager = get_cache_manager()
                if cache_manager:
                    cache_manager.check_system_prompt_change(system_prompt)                # Ensure memory_chunks is a list and handle None values
                memory_chunks = memory_chunks or []
                
                # Build conversation context from history
                conversation_context = ""
                if history:
                    # Format chat history as conversation for context
                    for entry in history[-5:]:  # Last 5 entries
                        if isinstance(entry, dict):
                            user_msg = entry.get("message", "")
                            assistant_msg = entry.get("response", "")
                            if user_msg:
                                conversation_context += f"User: {user_msg}\n"
                            if assistant_msg:
                                conversation_context += f"Assistant: {assistant_msg}\n"
                
                # Combine memory and conversation context
                full_context = ""
                if memory_chunks:
                    full_context += "Relevant memories:\n" + "\n".join([str(m) for m in memory_chunks]) + "\n\n"
                if conversation_context:
                    full_context += "Previous conversation:\n" + conversation_context + "\n"
                
                # Build messages for LLM
                messages = [
                    {"role": "system", "content": system_prompt}
                ]
                
                # Add context as system message if we have any
                if full_context:
                    messages.append({"role": "system", "content": full_context})
                  # Add current user message
                messages.append({"role": "user", "content": user_message})
                
                # Debug logging
                logging.debug(f"[LLM] Calling LLM with {len(messages)} messages for user {user_id}")
                if full_context:
                    logging.debug(f"[LLM] Including context: memory_chunks={len(memory_chunks)}, conversation_entries={len(history) if history else 0}")
                return await call_llm(messages)

            try:
                logging.info(f"[DEBUG] Calling LLM query function for user {user_id}")
                user_response = await llm_query()
                logging.info(f"[DEBUG] LLM returned response for user {user_id}: {repr(user_response)}")
                logging.debug(f"[LLM] Received response for user {user_id}: {len(str(user_response)) if user_response else 0} chars")
            except Exception as e:
                logging.error(f"[DEBUG] LLM query failed for user {user_id}: {e}")
                log_error(e, "LLM query", user_id, request_id)
                user_response = "I apologize, but I'm having trouble processing your request right now. Please try again."            
            debug_info.append("[LLM] Used LLM with memory and conversation context")
        else:
            logging.debug(f"[TOOL] Tool '{tool_name}' returned response for user {user_id}")
            debug_info.append(f"[TOOL] Used {tool_name} tool")
          # --- Store chat in Redis ---
        def store_chat():
            store_chat_history(user_id, user_message, str(user_response))

        safe_execute(
            store_chat,
            error_handler=lambda e: CacheErrorHandler.handle_cache_error(
                e, "store_chat", f"chat:{user_id}", user_id, request_id
            ),
        )
        
        # --- Automatic memory storage for important conversations ---
        print(f"[CONSOLE DEBUG] Checking if conversation should be stored as memory...")
        def should_store_as_memory(message, response):
            """Determine if a conversation should be stored as long-term memory."""
            memory_keywords = [
                "my name is", "i am", "i'm", "call me", 
                "i live in", "i work", "i study", "my job",
                "my favorite", "i like", "i love", "i hate",
                "i prefer", "remember that", "don't forget",
                "important:", "note:", "my birthday",
                "my age", "years old", "from", "born in"
            ]
            
            # Check if user is sharing personal information
            message_lower = message.lower()
            for keyword in memory_keywords:
                if keyword in message_lower:
                    return True
                    
            # Store responses to "who am i" or "what do you know about me" type questions
            if any(phrase in message_lower for phrase in ["who am i", "about me", "know about me"]):
                return True
                
            return False
        
        if should_store_as_memory(user_message, str(user_response)):
            print(f"[CONSOLE DEBUG] Storing conversation as long-term memory for user {user_id}")
            def store_memory():
                # Create a memory document from the conversation
                memory_text = f"User: {user_message}\nAssistant: {str(user_response)}"
                chunks_stored = index_user_document(user_id, memory_text)
                logging.info(f"[MEMORY] Stored conversation as memory ({chunks_stored} chunks) for user {user_id}")
                debug_info.append(f"[MEMORY] Stored as long-term memory ({chunks_stored} chunks)")

            safe_execute(
                store_memory,
                error_handler=lambda e: MemoryErrorHandler.handle_memory_error(
                    e, "store_conversation", user_id, request_id
                ),
            )
        else:
            print(f"[CONSOLE DEBUG] Conversation not stored as memory (no personal info detected)")# --- Cache the response (after generating user_response) ---
        def cache_response():
            if not is_time_query and user_response and str(user_response).strip():  # Only cache non-empty responses
                set_cache(
                    db_manager,
                    cache_key,
                    str(user_response),
                    expire=600
                )
                logging.info(f"[CACHE] Response cached for user {user_id} (key: {cache_key})")
                debug_info.append(f"[CACHE] Response cached (key: {cache_key})")
            else:
                if is_time_query:
                    logging.info("[CACHE] Skipping cache for time-sensitive query")
                else:
                    logging.info("[CACHE] Skipping cache for empty response")

        safe_execute(
            cache_response,
            error_handler=lambda e: CacheErrorHandler.handle_cache_error(
                e, "set", cache_key, user_id, request_id
            ),
        )# --- Automatic knowledge storage: store web search results in ChromaDB ---
        if tool_used and tool_name == "web_search" and user_response and "results" in locals():

            def store_knowledge():
                # Store the top web result as a new document in ChromaDB for this user
                doc_id = f"web:{user_id}:{abs(hash(query))}"
                name = f"Web search: {query}"
                text = str(user_response)
                chunks_stored = index_user_document(user_id, text)
                logging.debug(
                    f"[KNOWLEDGE] Stored web search result ({chunks_stored} chunks) in ChromaDB for user {user_id}, query '{query}'"
                )

            safe_execute(
                store_knowledge,
                error_handler=lambda e: MemoryErrorHandler.handle_memory_error(
                    e, "store", user_id, request_id
                ),
            )

        # Always log debug info, but do not include in user-facing response
        logging.debug(f"[DEBUG INFO] {' | '.join(debug_info)}")
        logging.debug(
            f"[REQUEST {request_id}] Successfully processed chat request for user {user_id}"
        )

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
    # Check if cache is still valid
    current_time = time.time()
    if current_time - _model_cache["last_updated"] > _model_cache["ttl"]:
        # Cache expired, refresh
        await refresh_model_cache()
    # Temporary workaround: ensure Mistral model is included if it exists in Ollama
    models_data = _model_cache["data"].copy()
    mistral_exists = any(model["id"] == "mistral:7b-instruct-v0.3-q4_k_m" for model in models_data)
    logging.info(
        f"[MODELS DEBUG] Cache has {len(models_data)} models, Mistral exists: {mistral_exists}"
    )
    logging.info(f"[MODELS DEBUG] Using OLLAMA_BASE_URL: {OLLAMA_BASE_URL}")

    if not mistral_exists:
        # Check if Mistral model exists in Ollama directly
        try:
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
                            models_data.append(
                                {
                                    "id": "mistral:7b-instruct-v0.3-q4_k_m",
                                    "object": "model",
                                    "created": int(time.time()),
                                    "owned_by": "ollama",
                                    "permission": [],                                }
                            )
                            logging.info("[MODELS DEBUG] Added Mistral model to response")
                            break
        except Exception as e:
            logging.warning(f"Failed to check Ollama for Mistral model: {e}")

    return {"object": "list", "data": models_data}


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
        raise HTTPException(status_code=400, detail="Missing or invalid required field: 'messages' (must be a non-empty list)")
    
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
            else:                # Handle other content types by converting to string
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
        STREAM_SESSION_STOP[session_id] = False
        STREAM_SESSION_METADATA[session_id] = {
            "created_at": time.time(),
            "user_id": user_id,
            "model": body.get('model', DEFAULT_MODEL)
        }

        async def event_stream():
            """Enhanced event stream with proper error handling and cleanup."""
            try:
                logging.debug(f"[STREAM] Starting stream for session {session_id}")
                
                # --- Retrieve chat history and memory for streaming ---
                def get_history():
                    return get_chat_history(user_id, limit=10)

                history = safe_execute(
                    get_history,
                    fallback_value=[],
                    error_handler=lambda e: CacheErrorHandler.handle_cache_error(
                        e, "get_history", f"history:{user_id}", user_id, getattr(request.state, 'request_id', 'unknown')
                    ),
                )

                # Build enhanced message format with chat history for streaming
                stream_messages = []
                
                # Add system message first (if any)
                system_messages = [m for m in messages if m.get("role") == "system"]
                if system_messages:
                    stream_messages.extend(system_messages)
                else:
                    # Add default persona system message if none provided
                    try:
                        with open("persona.json", "r", encoding="utf-8") as f:
                            persona = json.load(f)
                            system_prompt = persona.get("system_prompt", "You are a helpful AI assistant with access to tools and memory.")
                    except Exception:
                        system_prompt = "You are a helpful AI assistant with access to tools and memory."
                        
                    stream_messages.append({
                        "role": "system", 
                        "content": system_prompt
                    })
                
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
                
                llm_streamer = await call_llm_stream(
                    stream_messages, model=body.get("model", DEFAULT_MODEL), session_id=session_id
                )
                
                token_count = 0
                full_response = ""  # Collect the full response for storage
                async for token in llm_streamer:
                    if not token:
                        continue
                        
                    # Check if stream was stopped
                    if STREAM_SESSION_STOP.get(session_id, False):
                        logging.debug(f"[STREAM] Stream {session_id} stopped by client")
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
                        logging.error(f"[STREAM] Error yielding token: {e}")
                        break
                
                # Store the complete streaming response in chat history
                if full_response:
                    def store_streaming_chat():
                        store_chat_history(user_id, user_message, str(full_response))
                    
                    safe_execute(
                        store_streaming_chat,
                        error_handler=lambda e: CacheErrorHandler.handle_cache_error(
                            e, "store_streaming_chat", f"chat:{user_id}", user_id, session_id
                        ),
                    )
                    logging.debug(f"[STREAM] Stored streaming response for user {user_id}: {len(full_response)} chars")
                
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
                
                logging.debug(f"[STREAM] Stream {session_id} completed with {token_count} tokens")
                
            except Exception as e:
                logging.error(f"[STREAM] Stream {session_id} failed: {e}")
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
                logging.debug(f"[STREAM] Cleaned up session {session_id}")

        return StreamingResponse(
            event_stream(), 
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Session-ID": session_id
            }        )

    else:
        # Non-streaming response - call LLM directly with specified model
        try:
            # --- Retrieve chat history and memory for OpenWebUI integration ---
            def get_history():
                return get_chat_history(user_id, limit=10)

            history = safe_execute(
                get_history,
                fallback_value=[],
                error_handler=lambda e: CacheErrorHandler.handle_cache_error(
                    e, "get_history", f"history:{user_id}", user_id, getattr(request.state, 'request_id', 'unknown')
                ),
            )

            # Build enhanced message format with chat history
            llm_messages = []
            
            # Add system message first (if any)
            system_messages = [m for m in messages if m.get("role") == "system"]
            if system_messages:
                llm_messages.extend(system_messages)
            else:
                # Add default persona system message if none provided
                try:
                    with open("persona.json", "r", encoding="utf-8") as f:
                        persona = json.load(f)
                        system_prompt = persona.get("system_prompt", "You are a helpful AI assistant with access to tools and memory.")
                except Exception:
                    system_prompt = "You are a helpful AI assistant with access to tools and memory."
                    
                llm_messages.append({
                    "role": "system", 
                    "content": system_prompt
                })
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
            
            # Debug logging
            model_to_use = body.get("model", DEFAULT_MODEL)
            logging.info(f"[DEBUG] v1/chat/completions calling LLM with model: {model_to_use}")
            logging.info(f"[DEBUG] v1/chat/completions messages count: {len(llm_messages)}")
            
            # Call LLM directly with the specified model
            llm_response = await call_llm(llm_messages, model=model_to_use)
            
            # Debug logging for response
            logging.info(f"[DEBUG] v1/chat/completions LLM response: '{llm_response}'")
            logging.info(f"[DEBUG] v1/chat/completions LLM response type: {type(llm_response)}")
            logging.info(f"[DEBUG] v1/chat/completions LLM response length: {len(llm_response) if llm_response else 0}")
            
            # Store chat history using the existing logic but with the actual response
            if llm_response:
                def store_chat():
                    store_chat_history(user_id, user_message, str(llm_response))
                
                safe_execute(
                    store_chat,
                    error_handler=lambda e: CacheErrorHandler.handle_cache_error(
                        e, "store_chat", f"chat:{user_id}", user_id, getattr(request.state, 'request_id', 'unknown')
                    ),
                )
            
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
            log_error(e, "OpenAI chat completions", user_id, getattr(request.state, 'request_id', 'unknown'))
            raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")


@app.middleware("http")
async def request_middleware(request: Request, call_next):
    """Enhanced middleware with request tracking and timing."""
    # Generate unique request ID
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    
    # Start timing
    start_time = time.time()
    
    # Log request start
    log_service_status(
        "REQUEST", 
        "info", 
        f"[{request_id}] {request.method} {request.url.path} - Started"
    )
    
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
            f"Completed {response.status_code} in {response_time_ms:.2f}ms"
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
            f"[{request_id}] {request.method} {request.url.path} - "
            f"Failed after {response_time_ms:.2f}ms: {str(e)}"
        )
        
        # Re-raise to let exception handlers deal with it
        raise


# Cache Management Endpoints
@app.get("/admin/cache/status")
async def get_cache_status():
    """Get cache status and statistics."""

    cache_manager = get_cache_manager()
    if cache_manager:
        stats = cache_manager.get_cache_stats()
        return {"status": "ok", "cache_stats": stats}
    else:
        return {"status": "error", "message": "Cache manager not available"}


@app.post("/admin/cache/invalidate")
async def invalidate_cache(cache_type: str = "chat"):
    """Invalidate cache entries."""

    cache_manager = get_cache_manager()
    if not cache_manager:
        return {"status": "error", "message": "Cache manager not available"}

    if cache_type == "chat":
        cache_manager.invalidate_chat_cache()
        return {"status": "ok", "message": "Chat cache invalidated"}
    elif cache_type == "all":
        cache_manager.invalidate_all_cache()
        return {"status": "ok", "message": "All cache invalidated"}
    else:
        return {"status": "error", "message": "Invalid cache_type. Use 'chat' or 'all'"}


@app.post("/admin/cache/check-prompt")
async def check_system_prompt():
    """Force check system prompt and invalidate cache if needed."""

    cache_manager = get_cache_manager()
    if not cache_manager:
        return {"status": "error", "message": "Cache manager not available"}

    # Use the current system prompt
    current_prompt = "You are a helpful assistant. Use the following memory and chat history to answer. Always respond \
        with plain text only - never use JSON formatting, structured responses, or any special formatting. Just provide direct, natural language answers."
    cache_manager.check_system_prompt_change(current_prompt)
    return {"status": "ok", "message": "System prompt check completed"}


@app.post("/admin/sessions/cleanup")
async def cleanup_streaming_sessions():
    """Clean up old streaming sessions."""
    before_count = len(STREAM_SESSION_METADATA)
    cleanup_old_sessions()
    after_count = len(STREAM_SESSION_METADATA)
    cleaned_count = before_count - after_count
    
    return {
        "status": "ok",
        "message": f"Cleaned up {cleaned_count} old sessions",
        "active_sessions": after_count,
        "timestamp": datetime.now().isoformat()
    }


@app.get("/admin/sessions/status")
async def get_streaming_sessions_status():
    """Get status of active streaming sessions."""
    current_time = time.time()
    active_sessions = []
    
    for session_id, metadata in STREAM_SESSION_METADATA.items():
        session_info = {
            "session_id": session_id,
            "created_at": metadata.get("created_at"),
            "age_seconds": current_time - metadata.get("created_at", current_time),
            "is_stopped": STREAM_SESSION_STOP.get(session_id, False),
            "stopped_at": metadata.get("stopped_at")
        }
        active_sessions.append(session_info)
    
    return {
        "status": "ok",
        "total_sessions": len(active_sessions),
        "active_sessions": active_sessions,
        "timestamp": datetime.now().isoformat()
    }


# Model cache testing endpoints
@app.post("/test/refresh_models")
async def test_refresh_models():
    """Test endpoint for refreshing model cache."""
    try:
        models = await refresh_model_cache(force=True)
        return {
            "status": "success",
            "models_cached": len(models),
            "models": models,
            "timestamp": time.time()
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "timestamp": time.time()
        }


@app.post("/test/check_model")
async def test_check_model(request: dict):
    """Test endpoint for checking model availability."""
    try:
        model_name = request.get("model")
        if not model_name:
            return {"status": "error", "error": "Model name required"}
        
        available = await ensure_model_available(model_name, auto_pull=False)
        return {
            "status": "success",
            "model": model_name,
            "available": available,
            "timestamp": time.time()
        }
    except Exception as e:
        return {
            "status": "error",
            "model": request.get("model", "unknown"),
            "error": str(e),
            "timestamp": time.time()
        }


@app.get("/test/model_cache_status")
async def test_model_cache_status():
    """Get current model cache status."""
    return {
        "status": "success",
        "cache": {
            "data": _model_cache["data"],
            "last_updated": _model_cache["last_updated"],
            "ttl": _model_cache["ttl"],
            "age": time.time() - _model_cache["last_updated"],
            "valid": time.time() - _model_cache["last_updated"] < _model_cache["ttl"]
        },
        "timestamp": time.time()
    }


# Pipeline Integration API Endpoints
# These endpoints support OpenWebUI Pipelines integration

@app.post("/api/memory/retrieve")
async def retrieve_memory_for_pipeline(
    request: dict = Body(...),
    api_key: str = Depends(verify_api_key)
):
    """Retrieve user memory for Pipeline integration"""
    try:
        user_id = request.get("user_id", "default")
        query = request.get("query", "")
        limit = request.get("limit", 3)
        threshold = request.get("threshold", 0.7)
        
        log_service_status("PIPELINE_MEMORY", "info", f"Memory retrieval request for user {user_id}")
        
        # Use your existing memory retrieval
        query_embedding = get_embedding(query)
        if query_embedding is not None:
            memories = retrieve_user_memory(user_id, query, limit)
            
            # Filter by relevance threshold if needed
            filtered_memories = []
            for memory in memories:
                # Add relevance scoring logic here if available
                filtered_memories.append(memory)
            
            log_service_status("PIPELINE_MEMORY", "ready", f"Retrieved {len(filtered_memories)} memories for {user_id}")
            return {
                "memories": filtered_memories, 
                "count": len(filtered_memories),
                "user_id": user_id,
                "query": query
            }
        else:
            log_service_status("PIPELINE_MEMORY", "warning", f"Could not generate embedding for query: {query}")
            return {"memories": [], "count": 0, "user_id": user_id, "query": query}
            
    except Exception as e:
        log_error(e, "pipeline_memory_retrieval", user_id, "pipeline")
        raise HTTPException(status_code=500, detail=f"Memory retrieval failed: {str(e)}")

@app.post("/api/learning/process_interaction")
async def process_interaction_for_pipeline(
    request: dict = Body(...),
    api_key: str = Depends(verify_api_key)
):
    """Process interaction for adaptive learning from Pipeline"""
    try:
        # Extract request data
        user_id = request.get("user_id", "default")
        conversation_id = request.get("conversation_id", f"pipeline_{user_id}")
        user_message = request.get("user_message", "")
        assistant_response = request.get("assistant_response", "")
        response_time = request.get("response_time", 1.0)
        tools_used = request.get("tools_used", [])
        source = request.get("source", "pipeline")
        
        log_service_status("PIPELINE_LEARNING", "info", f"Learning request for user {user_id} from {source}")
        
        # Use your existing adaptive learning system
        result = await adaptive_learning_system.process_interaction(
            user_id=user_id,
            conversation_id=conversation_id,
            user_message=user_message,
            assistant_response=assistant_response,
            response_time=response_time,
            tools_used=tools_used
        )
        
        log_service_status("PIPELINE_LEARNING", "ready", f"Processed learning interaction for {user_id}")
        return {
            "status": "success", 
            "result": result,
            "user_id": user_id,
            "source": source
        }
        
    except Exception as e:
        log_error(e, "pipeline_learning", user_id, "pipeline")
        raise HTTPException(status_code=500, detail=f"Learning processing failed: {str(e)}")

@app.get("/api/pipeline/status")
async def get_pipeline_status():
    """Get current backend status for Pipeline integration"""
    try:
        # Get database health
        health = get_database_health()
        
        # Get cache stats
        cache_manager = get_cache_manager()
        cache_info = cache_manager.get_cache_stats() if cache_manager else {}
        
        # Get adaptive learning stats
        learning_stats = {
            "learning_system": "available",
            "feedback_types": ["positive", "negative", "neutral", "correction", "clarification"],
            "active": True
        }
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "services": {
                "redis": health["redis"]["available"],
                "chromadb": health["chromadb"]["available"],
                "embeddings": health["embeddings"]["available"],
                "adaptive_learning": True,
                "memory_system": True
            },
            "cache": cache_info,            "learning": learning_stats,
            "api_version": "1.0.0",
            "pipeline_support": True
        }
        
    except Exception as e:
        log_error(e, "pipeline_status", "system", "pipeline")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


# Simple test endpoint to verify endpoint loading
@app.get("/api/test/hello")
async def test_hello():
    """Simple test endpoint"""
    return {"message": "Hello from test endpoint", "status": "working"}
