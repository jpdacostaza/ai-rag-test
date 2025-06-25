"""
Application startup logic and initialization.

This module handles the complete initialization sequence for the FastAPI LLM backend,
including database connections, model loading, service health verification, and
background task setup.
"""

import asyncio
import itertools
import sys
import time
from typing import Optional, Dict, Any, List

import httpx
from config import (
    DEFAULT_MODEL, OLLAMA_BASE_URL, log_system_info, log_environment_variables
)
from utilities.cpu_enforcer import verify_cpu_only_setup, log_cpu_verification_results
from utilities.alert_manager import get_alert_manager
from database_manager import db_manager, get_database_health
from human_logging import log_service_status
from model_manager import ensure_model_available
from routes.models import refresh_model_cache
from watchdog import start_watchdog_service

# Global variable to track watchdog thread
watchdog_thread: Optional[object] = None

# Stub functions for missing imports
def initialize_storage() -> bool:
    """Stub function for storage initialization.
    
    Returns:
        bool: True if storage initialization succeeded, False otherwise.
    """
    return True

def initialize_cache_management() -> bool:
    """Stub function for cache management initialization.
    
    Returns:
        bool: True if cache management initialization succeeded, False otherwise.
    """
    return True

async def start_enhanced_background_tasks() -> None:
    """Stub function for enhanced background tasks.
    
    Returns:
        None: This function currently does nothing but is a placeholder.
    """
    return None

async def _spinner_log(message: str, duration: float = 2, interval: float = 0.2) -> None:
    """Show a spinner/progress animation in the logs for a given duration.
    
    Args:
        message: The message to display with the spinner
        duration: How long to show the spinner in seconds
        interval: Time between spinner frame updates in seconds
    """
    spinner = itertools.cycle(["|", "/", "-", "\\"])
    steps = int(duration / interval)
    for _ in range(steps):
        sys.stdout.write(f"\r{message} {next(spinner)}")
        sys.stdout.flush()
        await asyncio.sleep(interval)
    sys.stdout.write("\r" + " " * (len(message) + 2) + "\r")
    sys.stdout.flush()

async def _print_startup_summary() -> None:
    """Print a visually distinct summary banner with health status of all services."""
    health = await get_database_health()
    # Use ASCII equivalents instead of Unicode emojis for better compatibility
    redis_status = "OK" if health['redis']['status'] == 'healthy' else "FAIL"
    chromadb_status = "OK" if health['chromadb']['status'] == 'healthy' else "FAIL"
    embeddings_status = "OK" if health['embeddings']['status'] == 'healthy' else "FAIL"
    
    lines = [
        "\n================= SERVICE STATUS SUMMARY =================",
        f"Redis:      {redis_status}",
        f"ChromaDB:   {chromadb_status}",
        f"Embeddings: {embeddings_status}",
        "========================================================\n",
    ]
    for line in lines:
        log_service_status("STARTUP", "info", line)

async def startup_event(app) -> None:
    """Initialize services after FastAPI app has started.
    
    Args:
        app: FastAPI application instance
        
    Returns:
        None
    """
    global watchdog_thread

    # Enhanced startup logging
    log_service_status("STARTUP", "starting", "FastAPI LLM Backend Starting...")
    
    try:
        # CPU-only mode verification
        log_service_status("STARTUP", "starting", "Verifying CPU-only mode...")
        cpu_results = verify_cpu_only_setup()
        log_cpu_verification_results(cpu_results)
        
        if cpu_results["status"] == "warning":
            log_service_status("STARTUP", "warning", "CPU-only mode verification has warnings - check logs")
        elif cpu_results["status"] == "cpu_only_verified":
            log_service_status("STARTUP", "ready", "CPU-only mode verified successfully")
        else:
            log_service_status("STARTUP", "degraded", "CPU-only mode verification incomplete")
        
        log_system_info()
        log_environment_variables()

        # Initialize alert manager
        log_service_status("STARTUP", "starting", "Initializing alert management system...")
        try:
            alert_manager = get_alert_manager()
            log_service_status("STARTUP", "ready", "Alert management system initialized successfully")
        except Exception as e:
            log_service_status("STARTUP", "error", f"Alert manager initialization failed: {e}")

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
                    async with httpx.AsyncClient(timeout=60.0) as client:
                        resp = await client.post(
                            f"{OLLAMA_BASE_URL}/api/generate", 
                            json=preload_payload
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
                except httpx.RequestError as e:
                    log_service_status("MODEL", "warning", f"Model {DEFAULT_MODEL} preload failed: Network error - {e}")
                except httpx.TimeoutException:
                    log_service_status("MODEL", "warning", f"Model {DEFAULT_MODEL} preload failed: Timeout")
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
        try:
            await refresh_model_cache()
            log_service_status("STARTUP", "ready", "Model cache initialized successfully")
        except Exception as e:
            log_service_status("STARTUP", "warning", f"Model cache initialization failed: {e}")

        # Initialize cache management system
        log_service_status("STARTUP", "starting", "Initializing cache management...")

        try:
            cache_init_success = initialize_cache_management()
            if cache_init_success:
                log_service_status("CACHE", "ready", "Cache management system initialized successfully")
            else:
                log_service_status("CACHE", "warning", "Cache management initialization had issues")
        except Exception as e:
            log_service_status("CACHE", "error", f"Cache management initialization failed: {e}")

        # Background services
        log_service_status("STARTUP", "starting", "Initializing background services...")
        await _spinner_log("[STARTUP] Initializing background services", 2)
        await asyncio.sleep(2)
        log_service_status("STARTUP", "starting", "Waiting 2 seconds for services to initialize...")

        # Watchdog
        try:
            watchdog_thread = start_watchdog_service()
            log_service_status("WATCHDOG", "starting", "Service started with delayed initialization")
        except Exception as e:
            log_service_status("WATCHDOG", "error", f"Failed to start watchdog service: {e}")

        # Enhanced background tasks
        try:
            await start_enhanced_background_tasks()
            log_service_status(
                "ENHANCED_SYSTEM", "ready", "Enhanced learning and document processing systems initialized"
            )
        except Exception as e:
            log_service_status("ENHANCED_SYSTEM", "error", f"Enhanced background tasks failed: {e}")

        # Final summary banner
        await _spinner_log("[STARTUP] Finalizing startup", 1)
        await _print_startup_summary()
        log_service_status("STARTUP", "ready", "FastAPI LLM Backend startup completed successfully!")
        
    except Exception as e:
        log_service_status("STARTUP", "error", f"Critical startup failure: {e}")
        raise
