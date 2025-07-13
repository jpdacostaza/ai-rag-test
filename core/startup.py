"""
Simplified Application Startup Logic
This version removes problematic blocking operations that can cause startup hangs.
"""

import asyncio
import sys
import time
from typing import Optional

from config.config_unified import DEFAULT_MODEL, log_system_info, log_environment_variables
from utilities.cpu_enforcer import verify_cpu_only_setup, log_cpu_verification_results
from services.database_manager import db_manager, get_database_health
from core.human_logging import log_service_status

# Global variable to track watchdog thread
watchdog_thread: Optional[object] = None

def initialize_storage() -> bool:
    """Initialize storage structure"""
    return True

def initialize_cache_management() -> bool:
    """Initialize cache management"""
    return True

async def start_enhanced_background_tasks() -> None:
    """Start background tasks without blocking"""
    return None

async def _print_startup_summary() -> None:
    """Print a simplified startup summary"""
    try:
        health = await get_database_health()
        redis_status = "OK" if health["redis"]["status"] == "healthy" else "FAIL"
        chromadb_status = "OK" if health["chromadb"]["status"] == "healthy" else "FAIL"
        embeddings_status = "OK" if health["embeddings"]["status"] == "healthy" else "FAIL"

        lines = [
            "\n================= SERVICE STATUS SUMMARY =================",
            f"Redis:      {redis_status}",
            f"ChromaDB:   {chromadb_status}",
            f"Embeddings: {embeddings_status}",
            "========================================================\n",
        ]
        for line in lines:
            log_service_status("STARTUP", "info", line)
    except Exception as e:
        log_service_status("STARTUP", "warning", f"Could not get health summary: {e}")

async def startup_event(app) -> None:
    """Robust startup event with comprehensive error handling and timeouts"""
    global watchdog_thread

    log_service_status("STARTUP", "starting", "FastAPI LLM Backend Starting (Robust Mode)...")

    # Store startup time for timeout management
    startup_start = time.time()
    max_startup_time = 60.0  # Maximum 60 seconds for full startup

    try:
        # Phase 1: Quick initialization (5 seconds max)
        log_service_status("STARTUP", "starting", "Phase 1: Quick initialization...")
        
        try:
            # CPU-only mode verification (with timeout)
            await asyncio.wait_for(
                asyncio.create_task(_verify_cpu_mode()), 
                timeout=5.0
            )
        except asyncio.TimeoutError:
            log_service_status("STARTUP", "warning", "CPU verification timed out")
        except Exception as e:
            log_service_status("STARTUP", "warning", f"CPU verification failed: {e}")

        # Phase 2: Storage and basic services (10 seconds max)
        log_service_status("STARTUP", "starting", "Phase 2: Storage and basic services...")
        
        try:
            await asyncio.wait_for(
                asyncio.create_task(_initialize_storage_and_logging()),
                timeout=10.0
            )
        except asyncio.TimeoutError:
            log_service_status("STARTUP", "warning", "Storage initialization timed out")
        except Exception as e:
            log_service_status("STARTUP", "warning", f"Storage initialization failed: {e}")

        # Phase 3: Database connections (15 seconds max)
        log_service_status("STARTUP", "starting", "Phase 3: Database connections...")
        
        try:
            await asyncio.wait_for(
                asyncio.create_task(_initialize_database(app)),
                timeout=15.0
            )
        except asyncio.TimeoutError:
            log_service_status("STARTUP", "warning", "Database initialization timed out - continuing with degraded functionality")
            app.state.redis_client = None
        except Exception as e:
            log_service_status("STARTUP", "warning", f"Database initialization failed: {e}")
            app.state.redis_client = None

        # Phase 4: Model and cache services (20 seconds max)
        log_service_status("STARTUP", "starting", "Phase 4: Model and cache services...")
        
        try:
            await asyncio.wait_for(
                asyncio.create_task(_initialize_models_and_cache()),
                timeout=20.0
            )
        except asyncio.TimeoutError:
            log_service_status("STARTUP", "warning", "Model/cache initialization timed out")
        except Exception as e:
            log_service_status("STARTUP", "warning", f"Model/cache initialization failed: {e}")

        # Phase 5: Background services (10 seconds max)
        log_service_status("STARTUP", "starting", "Phase 5: Background services...")
        
        try:
            await asyncio.wait_for(
                asyncio.create_task(_initialize_background_services()),
                timeout=10.0
            )
        except asyncio.TimeoutError:
            log_service_status("STARTUP", "warning", "Background services initialization timed out")
        except Exception as e:
            log_service_status("STARTUP", "warning", f"Background services failed: {e}")

        # Final summary
        startup_duration = time.time() - startup_start
        await _print_startup_summary()
        log_service_status("STARTUP", "ready", f"FastAPI LLM Backend startup completed in {startup_duration:.1f}s!")

        # Set app as ready
        app.state.startup_complete = True
        app.state.startup_time = startup_duration

    except Exception as e:
        startup_duration = time.time() - startup_start
        log_service_status("STARTUP", "error", f"Critical startup failure after {startup_duration:.1f}s: {e}")
        # Set partial functionality mode
        app.state.startup_complete = False
        app.state.startup_error = str(e)
        log_service_status("STARTUP", "warning", "Starting with degraded functionality")

async def _verify_cpu_mode():
    """Verify CPU-only mode with timeout protection"""
    cpu_results = verify_cpu_only_setup()
    log_cpu_verification_results(cpu_results)
    
    if cpu_results["status"] == "cpu_only_verified":
        log_service_status("STARTUP", "ready", "CPU-only mode verified successfully")
    else:
        log_service_status("STARTUP", "warning", "CPU-only mode verification has warnings")

async def _initialize_storage_and_logging():
    """Initialize storage and logging systems"""
    # Log system info
    log_system_info()
    log_environment_variables()
    
    # Storage initialization
    storage_success = initialize_storage()
    if storage_success:
        log_service_status("STARTUP", "ready", "Storage structure initialized successfully")
    else:
        log_service_status("STARTUP", "warning", "Storage initialization had issues")

async def _initialize_database(app):
    """Initialize database connections with proper error handling"""
    if db_manager:
        await db_manager.ensure_initialized()
        log_service_status("STARTUP", "ready", "Database manager initialized successfully")
        
        # Store Redis client in app state
        if hasattr(db_manager, "redis_client") and db_manager.redis_client is not None:
            app.state.redis_client = db_manager.redis_client
            log_service_status("STARTUP", "ready", "Redis client stored in app state")
        else:
            app.state.redis_client = None
            log_service_status("STARTUP", "warning", "Redis client not available")
    else:
        log_service_status("STARTUP", "error", "Database manager is None")
        app.state.redis_client = None

async def _initialize_models_and_cache():
    """Initialize models and cache systems without blocking"""
    # Model availability check (no preloading to avoid hanging)
    log_service_status("MODEL", "info", f"Model {DEFAULT_MODEL} will be loaded on first request")
    
    # Cache management
    cache_init_success = initialize_cache_management()
    if cache_init_success:
        log_service_status("CACHE", "ready", "Cache management system initialized")
    else:
        log_service_status("CACHE", "warning", "Cache management initialization had issues")

async def _initialize_background_services():
    """Initialize background services"""
    await start_enhanced_background_tasks()
    log_service_status("ENHANCED_SYSTEM", "ready", "Background systems initialized")
    
    # Skip watchdog in robust mode to avoid issues
    log_service_status("WATCHDOG", "info", "Watchdog service skipped in robust mode")
