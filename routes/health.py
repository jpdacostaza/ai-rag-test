"""
Health check endpoints.
"""

import time
from dataclasses import asdict
from datetime import datetime

from fastapi import APIRouter, Request, Depends
from fastapi.responses import JSONResponse

from config.config_unified import get_app_start_time
from services.database_manager import get_database_health
from services.dependencies import get_redis_service, get_vector_service, get_cache_service
from core.logging_config import log_service_status
from models.models import HealthResponse, DetailedHealthResponse
from utilities.watchdog import get_watchdog, get_health_status
from services.storage_manager import StorageManager
from utilities.simple_error_handling import handle_api_errors, handle_errors

health_router = APIRouter()


@health_router.get("/")
async def root():
    """Root endpoint to verify API is accessible."""
    return {"message": "FastAPI LLM Backend is running", "status": "ok"}


@health_router.get("/health")
async def health_check(
    request: Request = None,
    redis_service=Depends(get_redis_service),
    vector_service=Depends(get_vector_service),
    cache_service=Depends(get_cache_service)
):
    """Enhanced health check endpoint with startup monitoring and service injection."""
    print("[CONSOLE DEBUG] Health endpoint called!")
    
    # Get database health
    health_status = await get_database_health()
    
    # Get app state if available
    app_state = {}
    if request and hasattr(request, 'app') and request.app:
        app_state = {
            "startup_complete": getattr(request.app.state, 'startup_complete', False),
            "startup_time": getattr(request.app.state, 'startup_time', None),
            "startup_error": getattr(request.app.state, 'startup_error', None),
        }
    
    # Add cache information using injected service
    cache_info = {}
    if cache_service:
        try:
            cache_info = cache_service.get_stats()
        except Exception as e:
            cache_info = {"status": "error", "error": str(e)}
    
    # Add Redis service health
    redis_info = {}
    if redis_service:
        try:
            redis_info = redis_service.get_stats()
        except Exception as e:
            redis_info = {"status": "error", "error": str(e)}
    
    # Add Vector service health  
    vector_info = {}
    if vector_service:
        try:
            vector_info = vector_service.get_stats()
        except Exception as e:
            vector_info = {"status": "error", "error": str(e)}

    services = [
        ("Redis", health_status["redis"]["status"] == "healthy"),
        ("ChromaDB", health_status["chromadb"]["status"] == "healthy"),
        ("Embeddings", health_status["embeddings"]["status"] == "healthy"),
    ]
    healthy = sum(1 for _, ok in services if ok)
    total = len(services)
    summary = f"Health check: {healthy}/{total} services healthy. " + ", ".join(
        [f"{name}: {'✅' if ok else '❌'}" for name, ok in services]
    )

    # Determine overall status
    overall_status = "ok"
    if not app_state.get("startup_complete", True):  # Default to True if no app state
        overall_status = "starting"
    elif app_state.get("startup_error"):
        overall_status = "degraded"
    elif healthy < total:
        overall_status = "degraded"

    response = {
        "status": overall_status,
        "summary": summary,
        "databases": health_status,
        "startup": app_state,
        "timestamp": datetime.now().isoformat(),
        "uptime_seconds": time.time() - get_app_start_time()
    }

    if cache_info:
        response["cache"] = cache_info
    if redis_info:
        response["redis_service"] = redis_info
    if vector_info:
        response["vector_service"] = vector_info

    return response


@health_router.get("/health/simple")
async def simple_health():
    """Simple health check without any dependencies."""
    app_start_time = get_app_start_time()
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "uptime_seconds": time.time() - app_start_time,
        "message": "Simple health check working",
    }


@health_router.get("/health/detailed")
async def detailed_health_check():
    """Detailed health check with subsystem monitoring."""
    health_status = await get_health_status()

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


@health_router.get("/health/redis")
async def redis_health():
    """Check Redis connectivity specifically."""
    watchdog = get_watchdog()
    redis_monitor = next((m for m in watchdog.monitors if m.name == "Redis"), None)
    if redis_monitor:
        result = await redis_monitor.check_health()
        return {"service": "Redis", "health": result.__dict__}
    return {"service": "Redis", "status": "monitor_not_found"}


@health_router.get("/health/chromadb")
async def chromadb_health():
    """Check ChromaDB connectivity specifically."""
    watchdog = get_watchdog()
    chroma_monitor = next((m for m in watchdog.monitors if m.name == "ChromaDB"), None)
    if chroma_monitor:
        result = await chroma_monitor.check_health()
        return {"service": "ChromaDB", "health": result.__dict__}
    return {"service": "ChromaDB", "status": "monitor_not_found"}


@health_router.get("/health/history/{service_name}")
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


@health_router.get("/health/storage")
async def storage_health():
    """Check storage directory structure and permissions."""

    # Get storage information
    storage_info = StorageManager.get_storage_info()

    # Validate permissions
    permissions = StorageManager.validate_permissions()

    # Calculate total storage usage
    total_size_mb = sum(dir_info.get("size_mb", 0) for dir_info in storage_info["directories"].values())

    # Count directories
    existing_dirs = sum(1 for dir_info in storage_info["directories"].values() if dir_info["exists"])
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
            "total_files": sum(dir_info.get("file_count", 0) for dir_info in storage_info["directories"].values()),
        },
        "permissions": permissions,
        "directory_details": storage_info["directories"],
    }


@health_router.get("/alerts/stats")
@handle_api_errors("get_alert_statistics")
async def get_alert_statistics():
    """Get alert system statistics."""
    try:
        # Import alert manager
        from utilities.alert_manager import get_alert_manager

        alert_manager = get_alert_manager()
        stats = alert_manager.get_alert_stats()
        return {"status": "success", "data": stats}
    except ImportError:
        # Alert manager not available
        return {
            "status": "success",
            "data": {
                "total_alerts": 0,
                "alerts_by_level": {},
                "recent_alerts": [],
                "message": "Alert system not configured",
            },
        }


@health_router.get("/startup-status")
@handle_api_errors("get_startup_status")
async def get_startup_status():
    """Get detailed startup status for debugging ChromaDB and Embeddings issues."""
    from services.database_manager import db_manager
    import httpx
    from config.config_unified import OLLAMA_BASE_URL, EMBEDDING_MODEL, CHROMA_HOST, CHROMA_PORT

    status = {"timestamp": datetime.utcnow().isoformat(), "services": {}, "recommendations": {}, "details": {}}

    # Check Redis using error handling framework
    @handle_errors("redis_health_check", default_value=("Failed", "Redis health check failed"))
    async def check_redis():
        if db_manager and db_manager.redis_client:
            await db_manager.redis_client.ping()
            return ("Connected", f"Connected to Redis at {db_manager.redis_client.connection_pool.connection_kwargs.get('host', 'unknown')}")
        return ("Not initialized", "Redis client not initialized")

    redis_status, redis_details = await check_redis()
    status["services"]["redis"] = redis_status
    status["details"]["redis"] = redis_details
    if redis_status == "Failed":
        status["recommendations"]["redis"] = "Run: docker-compose up -d redis"

    # Check ChromaDB using error handling framework
    @handle_errors("chromadb_health_check", default_value=("Failed", "ChromaDB health check failed"))
    def check_chromadb():
        if db_manager and db_manager.chroma_client:
            db_manager.chroma_client.heartbeat()
            return ("Connected", f"Connected to ChromaDB at {CHROMA_HOST}:{CHROMA_PORT}")
        return ("Not initialized", "ChromaDB client not initialized")

    chromadb_status, chromadb_details = check_chromadb()
    status["services"]["chromadb"] = chromadb_status
    status["details"]["chromadb"] = chromadb_details
    if chromadb_status == "Failed":
        status["recommendations"]["chromadb"] = f"Check: docker-compose ps | grep chroma. Expected port: {CHROMA_PORT}"

    # Check Ollama and Embeddings using error handling framework
    @handle_errors("ollama_embeddings_check", default_value=("Failed", "Ollama embeddings check failed", "Check Ollama service"))
    async def check_ollama_embeddings():
        async with httpx.AsyncClient(timeout=5.0) as client:
            # Check Ollama availability
            response = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
            if response.status_code == 200:
                models = response.json().get("models", [])
                model_names = [model.get("name", "").split(":")[0] for model in models]

                if EMBEDDING_MODEL in model_names:
                    return ("Available", f"Model '{EMBEDDING_MODEL}' found in Ollama. Available models: {model_names}", None)
                else:
                    return ("Model Missing", f"Model '{EMBEDDING_MODEL}' not found. Available: {model_names}", f"Run: ollama pull {EMBEDDING_MODEL}")
            else:
                return ("Ollama Error", f"Ollama returned status {response.status_code}", "Check Ollama service health")

    embeddings_status, embeddings_details, embeddings_recommendation = await check_ollama_embeddings()
    status["services"]["embeddings"] = embeddings_status
    status["details"]["embeddings"] = embeddings_details
    if embeddings_recommendation:
        status["recommendations"]["embeddings"] = embeddings_recommendation

    # Overall status
    all_services_ok = all(
        service_status in ["Connected", "Available"] for service_status in status["services"].values()
    )

    status["overall"] = "Healthy" if all_services_ok else "Degraded"
    status["ready_for_production"] = all_services_ok

    return status


@health_router.get("/health/startup")
async def startup_status(request: Request = None):
    """Get detailed startup status information."""
    app_state = {}
    if request and hasattr(request, 'app') and request.app:
        app_state = {
            "startup_complete": getattr(request.app.state, 'startup_complete', False),
            "startup_time": getattr(request.app.state, 'startup_time', None),
            "startup_error": getattr(request.app.state, 'startup_error', None),
        }
    
    return {
        "startup_complete": app_state.get("startup_complete", False),
        "startup_time_seconds": app_state.get("startup_time"),
        "startup_error": app_state.get("startup_error"),
        "uptime_seconds": time.time() - get_app_start_time(),
        "timestamp": datetime.now().isoformat(),
        "status": "complete" if app_state.get("startup_complete") else "in_progress"
    }


@health_router.get("/health/ready")
async def readiness_check(request: Request = None):
    """Kubernetes-style readiness check."""
    startup_complete = False
    if request and hasattr(request, 'app') and request.app:
        startup_complete = getattr(request.app.state, 'startup_complete', False)
    
    if startup_complete:
        return {"ready": True, "status": "ready"}
    else:
        return JSONResponse(
            status_code=503,
            content={"ready": False, "status": "not_ready", "message": "Service startup not complete"}
        )


@health_router.get("/health/live")
async def liveness_check():
    """Kubernetes-style liveness check - always returns alive if responding."""
    return {
        "alive": True, 
        "timestamp": datetime.now().isoformat(),
        "uptime_seconds": time.time() - get_app_start_time()
    }
