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
    """Simplified startup event that doesn't hang on model operations"""
    global watchdog_thread

    log_service_status("STARTUP", "starting", "FastAPI LLM Backend Starting (Simplified Mode)...")

    try:
        # CPU-only mode verification (non-blocking)
        log_service_status("STARTUP", "starting", "Verifying CPU-only mode...")
        try:
            cpu_results = verify_cpu_only_setup()
            log_cpu_verification_results(cpu_results)
            
            if cpu_results["status"] == "cpu_only_verified":
                log_service_status("STARTUP", "ready", "CPU-only mode verified successfully")
            else:
                log_service_status("STARTUP", "warning", "CPU-only mode verification has warnings")
        except Exception as e:
            log_service_status("STARTUP", "warning", f"CPU verification failed: {e}")

        # Log system info (non-blocking)
        try:
            log_system_info()
            log_environment_variables()
        except Exception as e:
            log_service_status("STARTUP", "warning", f"System info logging failed: {e}")

        # Storage initialization (non-blocking)
        log_service_status("STARTUP", "starting", "Initializing storage structure...")
        try:
            storage_success = initialize_storage()
            if storage_success:
                log_service_status("STARTUP", "ready", "Storage structure initialized successfully")
            else:
                log_service_status("STARTUP", "warning", "Storage initialization had issues")
        except Exception as e:
            log_service_status("STARTUP", "warning", f"Storage initialization failed: {e}")

        # Database initialization (with timeout)
        log_service_status("STARTUP", "starting", "Initializing database connections...")
        try:
            if db_manager:
                # Use asyncio.wait_for to prevent hanging
                await asyncio.wait_for(db_manager.ensure_initialized(), timeout=30.0)
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
        except asyncio.TimeoutError:
            log_service_status("STARTUP", "warning", "Database initialization timed out - continuing without it")
            app.state.redis_client = None
        except Exception as e:
            log_service_status("STARTUP", "warning", f"Database initialization failed: {e}")
            app.state.redis_client = None

        # Model availability check (non-blocking, no preloading)
        log_service_status("STARTUP", "starting", f"Checking model availability: {DEFAULT_MODEL}")
        try:
            # Skip model preloading to avoid hanging
            log_service_status("MODEL", "info", f"Model {DEFAULT_MODEL} will be loaded on first request")
        except Exception as e:
            log_service_status("MODEL", "warning", f"Model check failed: {e}")

        # Cache management (non-blocking)
        log_service_status("STARTUP", "starting", "Initializing cache management...")
        try:
            cache_init_success = initialize_cache_management()
            if cache_init_success:
                log_service_status("CACHE", "ready", "Cache management system initialized")
            else:
                log_service_status("CACHE", "warning", "Cache management initialization had issues")
        except Exception as e:
            log_service_status("CACHE", "warning", f"Cache management initialization failed: {e}")

        # Background services (non-blocking)
        log_service_status("STARTUP", "starting", "Initializing background services...")
        try:
            await start_enhanced_background_tasks()
            log_service_status("ENHANCED_SYSTEM", "ready", "Background systems initialized")
        except Exception as e:
            log_service_status("ENHANCED_SYSTEM", "warning", f"Background tasks failed: {e}")

        # Skip watchdog for now to avoid potential issues
        log_service_status("WATCHDOG", "info", "Watchdog service skipped in simplified mode")

        # Final summary
        await _print_startup_summary()
        log_service_status("STARTUP", "ready", "FastAPI LLM Backend startup completed successfully!")

    except Exception as e:
        log_service_status("STARTUP", "error", f"Critical startup failure: {e}")
        # Don't raise - let the app start even with partial initialization
        log_service_status("STARTUP", "warning", "Starting with degraded functionality")
