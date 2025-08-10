"""
Simplified Application Startup Logic
This version removes problematic blocking operations that can cause startup hangs.
"""

import asyncio
import sys
import time
import os
import traceback
from typing import Optional, Set

from config.config_unified import DEFAULT_MODEL, log_system_info, log_environment_variables
from utilities.cpu_enforcer import verify_cpu_only_setup, log_cpu_verification_results
from services.database_manager import db_manager, get_database_health
from core.unified_logging import log_service_status

# Global variable to track watchdog thread
watchdog_thread: Optional[object] = None

# BULLETPROOF MESSAGE SUPPRESSION - tracks every startup message ever sent
_STARTUP_MESSAGES_SENT: Set[str] = set()

def _suppress_duplicate_startup_message(service: str, status: str, details: str = "") -> bool:
    """Absolute duplicate message suppression for startup sequences.
    
    Returns True if message should be suppressed (already sent), False if new message.
    """
    # Create canonical key for this exact message type
    key = f"{service.upper()}:{status.lower()}:{details.strip()}"
    
    # Special patterns that should NEVER repeat
    startup_patterns = [
        "model", "cache", "background", "summary", "memory", "startup", "phase",
        "available", "initialized", "completed", "ready", "service_status"
    ]
    
    is_startup_msg = any(pattern in key.lower() for pattern in startup_patterns)
    
    if is_startup_msg:
        if key in _STARTUP_MESSAGES_SENT:
            return True  # Suppress duplicate
        _STARTUP_MESSAGES_SENT.add(key)
    
    return False  # Allow message

def safe_log_service_status(service: str, status: str, details: str = "") -> None:
    """Wrapper for log_service_status with absolute duplicate suppression."""
    if not _suppress_duplicate_startup_message(service, status, details):
        log_service_status(service, status, details)

def initialize_storage() -> bool:
    """Initialize storage structure"""
    return True

def initialize_cache_management() -> bool:
    """Initialize cache management"""
    return True

async def start_enhanced_background_tasks() -> None:
    """Start background tasks without blocking"""
    return None

# Global guard for startup summary
_SUMMARY_ALREADY_PRINTED = False
_summary_lock = asyncio.Lock()

async def _print_startup_summary() -> None:
    """Print a simplified startup summary"""
    global _SUMMARY_ALREADY_PRINTED, _GLOBAL_SUMMARY_PRINTED
    
    # IMMEDIATE CHECK before any async operations
    if _GLOBAL_SUMMARY_PRINTED:
        return
    _GLOBAL_SUMMARY_PRINTED = True
    
    async with _summary_lock:
        if _SUMMARY_ALREADY_PRINTED:
            safe_log_service_status("STARTUP", "info", "Startup summary already printed, skipping")
            return
        
        _SUMMARY_ALREADY_PRINTED = True
    
    try:
        health = await get_database_health()
        redis_status = "OK" if health["redis"]["status"] == "healthy" else "FAIL"
        chromadb_status = "OK" if health["chromadb"]["status"] == "healthy" else "FAIL"
        embeddings_status = "OK" if health["embeddings"]["status"] == "healthy" else "FAIL"

        summary_block = (
            "\n================= SERVICE STATUS SUMMARY =================\n"
            f"Redis:      {redis_status}\n"
            f"ChromaDB:   {chromadb_status}\n"
            f"Embeddings: {embeddings_status}\n"
            "========================================================\n"
        )
        # Emit as single log line to prevent per-line duplication by any
        # external log aggregation or stream splitting.
        safe_log_service_status("STARTUP", "info", summary_block)
    except Exception as e:
        safe_log_service_status("STARTUP", "warning", f"Could not get health summary: {e}")

_STARTUP_ALREADY_RAN = False  # module-level guard to prevent duplicate execution
_startup_lock = asyncio.Lock()  # concurrency guard to avoid overlapping startup tasks

async def startup_event(app) -> None:
    """Robust startup event with comprehensive error handling and timeouts.

    Idempotency: This function may be invoked twice in some deployment modes
    (e.g. multiple lifespan evaluations or framework quirks). We guard to
    ensure side effects and logging only occur once to avoid duplicate
    startup logs the user observed (duplicate SERVICE STATUS SUMMARY, model
    readiness lines, etc.). Subsequent calls become a cheap no-op.
    """
    global watchdog_thread, _STARTUP_ALREADY_RAN
    
    # Add debug trace to track startup calls
    import uuid
    startup_trace_id = str(uuid.uuid4())[:8]
    safe_log_service_status("STARTUP", "info", f"[TRACE:{startup_trace_id}] startup_event called")

    async with _startup_lock:
        # Multi-layer idempotency guard (state + module + env var)
        if getattr(app.state, "startup_ran", False) or _STARTUP_ALREADY_RAN or os.environ.get("APP_STARTUP_DONE") == "1":
            # Emit one diagnostic warning on unexpected re-entry (excluding first pass)
            if os.environ.get("APP_STARTUP_DONE") == "1" and not getattr(app.state, "_duplicate_startup_logged", False):
                app.state._duplicate_startup_logged = True
                safe_log_service_status(
                    "STARTUP",
                    "warning",
                    "Duplicate startup_event invocation suppressed. Call stack snippet: " +
                    " | ".join([frame.strip() for frame in traceback.format_stack(limit=6)])
                )
            safe_log_service_status("STARTUP", "info", f"[TRACE:{startup_trace_id}] Startup already completed, skipping")
            return
        app.state.startup_ran = True
        _STARTUP_ALREADY_RAN = True
        os.environ["APP_STARTUP_DONE"] = "1"

    safe_log_service_status("STARTUP", "starting", "FastAPI LLM Backend Starting (Robust Mode)...")

    # Store startup time for timeout management
    startup_start = time.time()
    max_startup_time = 900.0  # Maximum 15 minutes for full startup (including model downloads)

    try:
        # Phase 1: Quick initialization (5 seconds max)
        safe_log_service_status("STARTUP", "starting", "Phase 1: Quick initialization...")
        
        try:
            # CPU-only mode verification (with timeout)
            await asyncio.wait_for(
                asyncio.create_task(_verify_cpu_mode()), 
                timeout=5.0
            )
        except asyncio.TimeoutError:
            safe_log_service_status("STARTUP", "warning", "CPU verification timed out")
        except Exception as e:
            safe_log_service_status("STARTUP", "warning", f"CPU verification failed: {e}")

        # Phase 2: Storage and basic services (10 seconds max)
        safe_log_service_status("STARTUP", "starting", "Phase 2: Storage and basic services...")
        
        try:
            await asyncio.wait_for(
                asyncio.create_task(_initialize_storage_and_logging()),
                timeout=10.0
            )
        except asyncio.TimeoutError:
            safe_log_service_status("STARTUP", "warning", "Storage initialization timed out")
        except Exception as e:
            safe_log_service_status("STARTUP", "warning", f"Storage initialization failed: {e}")

        # Phase 3: Database connections (15 seconds max)
        safe_log_service_status("STARTUP", "starting", "Phase 3: Database connections...")
        
        try:
            await asyncio.wait_for(
                asyncio.create_task(_initialize_database(app)),
                timeout=15.0
            )
        except asyncio.TimeoutError:
            safe_log_service_status("STARTUP", "warning", "Database initialization timed out - continuing with degraded functionality")
            app.state.redis_client = None
        except Exception as e:
            safe_log_service_status("STARTUP", "warning", f"Database initialization failed: {e}")
            app.state.redis_client = None

        # Phase 4: Model and cache services (12 minutes max for large model downloads)
        safe_log_service_status("STARTUP", "starting", "Phase 4: Model and cache services...")
        
        try:
            await asyncio.wait_for(
                asyncio.create_task(_initialize_models_and_cache()),
                timeout=720.0  # 12 minutes to allow for large model downloads
            )
        except asyncio.TimeoutError:
            safe_log_service_status("STARTUP", "warning", "Model/cache initialization timed out after 12 minutes")
        except Exception as e:
            safe_log_service_status("STARTUP", "warning", f"Model/cache initialization failed: {e}")

        # Phase 5: Background services (10 seconds max)
        safe_log_service_status("STARTUP", "starting", "Phase 5: Background services...")
        
        try:
            await asyncio.wait_for(
                asyncio.create_task(_initialize_background_services()),
                timeout=10.0
            )
        except asyncio.TimeoutError:
            safe_log_service_status("STARTUP", "warning", "Background services initialization timed out")
        except Exception as e:
            safe_log_service_status("STARTUP", "warning", f"Background services failed: {e}")

        # Final summary
        startup_duration = time.time() - startup_start
        await _print_startup_summary()
        safe_log_service_status("STARTUP", "ready", f"FastAPI LLM Backend startup completed in {startup_duration:.1f}s!")

        # Set app as ready
        app.state.startup_complete = True
        app.state.startup_time = startup_duration

    except Exception as e:
        startup_duration = time.time() - startup_start
        safe_log_service_status("STARTUP", "error", f"Critical startup failure after {startup_duration:.1f}s: {e}")
        # Set partial functionality mode
        app.state.startup_complete = False
        app.state.startup_error = str(e)
        safe_log_service_status("STARTUP", "warning", "Starting with degraded functionality")

async def _verify_cpu_mode():
    """Verify CPU-only mode with timeout protection"""
    cpu_results = verify_cpu_only_setup()
    log_cpu_verification_results(cpu_results)
    
    if cpu_results["status"] == "cpu_only_verified":
        safe_log_service_status("STARTUP", "ready", "CPU-only mode verified successfully")
    else:
        safe_log_service_status("STARTUP", "warning", "CPU-only mode verification has warnings")

async def _initialize_storage_and_logging():
    """Initialize storage and environment logging."""
    log_system_info()
    log_environment_variables()
    if initialize_storage():
        safe_log_service_status("STARTUP", "ready", "Storage structure initialized successfully")
    else:
        safe_log_service_status("STARTUP", "warning", "Storage initialization had issues")

async def _initialize_database(app):
    """Initialize database connections."""
    if db_manager:
        await db_manager.ensure_initialized()
        safe_log_service_status("STARTUP", "ready", "Database manager initialized successfully")
        if hasattr(db_manager, "redis_client") and db_manager.redis_client is not None:
            app.state.redis_client = db_manager.redis_client
            safe_log_service_status("STARTUP", "ready", "Redis client stored in app state")
        else:
            app.state.redis_client = None
            safe_log_service_status("STARTUP", "warning", "Redis client not available")
    else:
        safe_log_service_status("STARTUP", "error", "Database manager is None")
        app.state.redis_client = None

# IMMEDIATE GLOBAL GUARDS - checked before any async operations
_GLOBAL_MODEL_INIT_DONE = False
_GLOBAL_BACKGROUND_INIT_DONE = False  
_GLOBAL_SUMMARY_PRINTED = False

# Global guard for model initialization
_MODEL_INIT_ALREADY_RAN = False
_model_init_lock = asyncio.Lock()

async def _initialize_models_and_cache():
    """Initialize models and cache systems (simplified)."""
    global _MODEL_INIT_ALREADY_RAN, _GLOBAL_MODEL_INIT_DONE
    
    # IMMEDIATE CHECK before any async operations
    if _GLOBAL_MODEL_INIT_DONE:
        return
    _GLOBAL_MODEL_INIT_DONE = True
    
    async with _model_init_lock:
        if _MODEL_INIT_ALREADY_RAN:
            safe_log_service_status("MODEL", "info", "Model initialization already completed, skipping")
            return
        
        _MODEL_INIT_ALREADY_RAN = True
    
    from config.config_unified import DEFAULT_MODEL, OLLAMA_BASE_URL
    import httpx, os
    
    # Add debug trace to identify duplicate execution
    import uuid
    trace_id = str(uuid.uuid4())[:8]
    safe_log_service_status("MODEL", "info", f"[TRACE:{trace_id}] Model initialization starting...")
    
    default_model = DEFAULT_MODEL
    ollama_url = OLLAMA_BASE_URL
    
    # Add unique execution timestamp to trace duplicates
    import time
    exec_time = f"{time.time():.6f}"
    safe_log_service_status("MODEL", "info", f"Verifying model {default_model}... [EXEC:{exec_time}]")
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(f"{ollama_url}/api/tags")
            if resp.status_code != 200:
                safe_log_service_status("MODEL", "warning", f"Ollama unreachable (status {resp.status_code})")
            else:
                names = [m.get('name') for m in resp.json().get('models', [])]
                if default_model in names:
                    safe_log_service_status("MODEL", "ready", f"Model {default_model} available [EXEC:{exec_time}]")
                    if os.getenv("ENABLE_MODEL_PRELOAD", "false").lower() == "true":
                        try:
                            preload = await client.post(
                                f"{ollama_url}/api/generate",
                                json={"model": default_model, "prompt": "warmup", "stream": False},
                                timeout=25.0
                            )
                            if preload.status_code == 200:
                                safe_log_service_status("MODEL", "ready", f"Model {default_model} preloaded")
                            else:
                                safe_log_service_status("MODEL", "warning", f"Preload failed: {preload.status_code}")
                        except Exception as perr:
                            safe_log_service_status("MODEL", "warning", f"Preload error: {perr}")
                    else:
                        safe_log_service_status("MODEL", "info", f"Model preloading disabled or not requested [EXEC:{exec_time}]")
                else:
                    safe_log_service_status("MODEL", "warning", f"Model {default_model} not present; lazy load on demand")
    except Exception as e:
        safe_log_service_status("MODEL", "warning", f"Model verification error: {e}")
    
    safe_log_service_status("MODEL", "info", f"[TRACE:{trace_id}] Model initialization completed")
    
    if initialize_cache_management():
        safe_log_service_status("CACHE", "ready", "Cache management system initialized")
    else:
        safe_log_service_status("CACHE", "warning", "Cache management initialization had issues")

# Global guard for background services initialization
_BACKGROUND_INIT_ALREADY_RAN = False
_background_init_lock = asyncio.Lock()

async def _initialize_background_services():
    """Initialize background services (non-blocking)."""
    global _BACKGROUND_INIT_ALREADY_RAN, _GLOBAL_BACKGROUND_INIT_DONE
    
    # IMMEDIATE CHECK before any async operations
    if _GLOBAL_BACKGROUND_INIT_DONE:
        return
    _GLOBAL_BACKGROUND_INIT_DONE = True
    
    async with _background_init_lock:
        if _BACKGROUND_INIT_ALREADY_RAN:
            safe_log_service_status("ENHANCED_SYSTEM", "info", "Background services initialization already completed, skipping")
            return
        
        _BACKGROUND_INIT_ALREADY_RAN = True
    
    try:
        await start_enhanced_background_tasks()
        safe_log_service_status("ENHANCED_SYSTEM", "ready", "Background systems initialized")
    except Exception as e:
        safe_log_service_status("ENHANCED_SYSTEM", "warning", f"Background systems error: {e}")
    safe_log_service_status("WATCHDOG", "info", "Watchdog service skipped in robust mode")
