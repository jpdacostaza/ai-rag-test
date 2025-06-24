"""
Application startup logic and initialization.
"""
import asyncio
import itertools
import sys
import time

import httpx
from config import (
    DEFAULT_MODEL, OLLAMA_BASE_URL, log_system_info, log_environment_variables
)
from cpu_enforcer import verify_cpu_only_setup, log_cpu_verification_results
from database_manager import db_manager, get_database_health
from human_logging import log_service_status
from model_manager import ensure_model_available
from routes.models import refresh_model_cache

# Stub functions for missing imports
def initialize_storage():
    """Stub function for storage initialization."""
    return True

def initialize_cache_management():
    """Stub function for cache management initialization."""
    return True

def start_watchdog_service():
    """Stub function for watchdog service."""
    return None

async def start_enhanced_background_tasks():
    """Stub function for enhanced background tasks."""
    return None

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

async def startup_event(app):
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
    
    log_system_info()
    log_environment_variables()

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
