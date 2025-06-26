"""
Health check endpoints.
"""

import time
from dataclasses import asdict
from datetime import datetime

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from config import get_app_start_time
from database_manager import get_database_health
from human_logging import log_service_status
from models import HealthResponse, DetailedHealthResponse

health_router = APIRouter()

# Import the get_cache function from database_manager
from database_manager import get_cache


def get_cache_manager():
    """Get cache manager from database manager."""
    try:
        return get_cache()
    except Exception as e:
        log_service_status("cache", "error", f"Failed to get cache manager: {str(e)}")
        return None


class MockWatchdog:
    """Mock watchdog class."""

    def __init__(self):
        """TODO: Add proper docstring for __init__."""
        self.monitors = []

    def get_service_history(self, service_name: str, hours: int):
        """TODO: Add proper docstring for get_service_history."""
        return []


def get_watchdog():
    """Stub function to get watchdog."""
    return MockWatchdog()


async def get_health_status():
    """Stub function for health status."""
    return {}


class StorageManager:
    """Stub class for storage manager."""

    @staticmethod
    def get_storage_info():
        """TODO: Add proper docstring for get_storage_info."""
        return {"directories": {}}

    @staticmethod
    def validate_permissions():
        """TODO: Add proper docstring for validate_permissions."""
        return {}


@health_router.get("/")
async def root():
    """Root endpoint to verify API is accessible."""
    return {"message": "FastAPI LLM Backend is running", "status": "ok"}


@health_router.get("/health")
async def health_check():
    """Health check endpoint that includes database status and a human-readable summary."""
    print("[CONSOLE DEBUG] Health endpoint called!")
    health_status = await get_database_health()

    # Add cache information
    cache_manager = get_cache_manager()
    cache_info = {}
    if cache_manager:
        cache_info = cache_manager.get_stats()

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

    response = {
        "status": "ok" if healthy == total else "degraded",
        "summary": summary,
        "databases": health_status,
    }

    if cache_info:
        response["cache"] = cache_info

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
    except Exception as e:
        log_service_status("health", "error", f"Failed to get alert stats: {str(e)}")
        return {"status": "error", "message": "Failed to retrieve alert statistics", "error": str(e)}


@health_router.get("/startup-status")
async def get_startup_status():
    """Get detailed startup status for debugging ChromaDB and Embeddings issues."""
    from database_manager import db_manager
    import httpx
    from config import OLLAMA_BASE_URL, EMBEDDING_MODEL, CHROMA_HOST, CHROMA_PORT

    status = {"timestamp": datetime.utcnow().isoformat(), "services": {}, "recommendations": {}, "details": {}}

    # Check Redis
    try:
        if db_manager and db_manager.redis_client:
            await db_manager.redis_client.ping()
            status["services"]["redis"] = "Connected"
            status["details"][
                "redis"
            ] = f"Connected to Redis at {db_manager.redis_client.connection_pool.connection_kwargs.get('host', 'unknown')}"
        else:
            status["services"]["redis"] = "Not initialized"
            status["details"]["redis"] = "Redis client not initialized"
    except Exception as e:
        status["services"]["redis"] = "Failed"
        status["details"]["redis"] = f"Redis error: {str(e)}"
        status["recommendations"]["redis"] = "Run: docker-compose up -d redis"

    # Check ChromaDB
    try:
        if db_manager and db_manager.chroma_client:
            db_manager.chroma_client.heartbeat()
            status["services"]["chromadb"] = "Connected"
            status["details"]["chromadb"] = f"Connected to ChromaDB at {CHROMA_HOST}:{CHROMA_PORT}"
        else:
            status["services"]["chromadb"] = "Not initialized"
            status["details"]["chromadb"] = "ChromaDB client not initialized"
    except Exception as e:
        status["services"]["chromadb"] = "Failed"
        status["details"]["chromadb"] = f"ChromaDB error: {str(e)}"
        status["recommendations"]["chromadb"] = f"Check: docker-compose ps | grep chroma. Expected port: {CHROMA_PORT}"

    # Check Ollama and Embeddings
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            # Check Ollama availability
            response = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
            if response.status_code == 200:
                models = response.json().get("models", [])
                model_names = [model.get("name", "").split(":")[0] for model in models]

                if EMBEDDING_MODEL in model_names:
                    status["services"]["embeddings"] = "Available"
                    status["details"][
                        "embeddings"
                    ] = f"Model '{EMBEDDING_MODEL}' found in Ollama. Available models: {model_names}"
                else:
                    status["services"]["embeddings"] = "Model Missing"
                    status["details"]["embeddings"] = f"Model '{EMBEDDING_MODEL}' not found. Available: {model_names}"
                    status["recommendations"]["embeddings"] = f"Run: ollama pull {EMBEDDING_MODEL}"
            else:
                status["services"]["embeddings"] = "Ollama Error"
                status["details"]["embeddings"] = f"Ollama returned status {response.status_code}"
                status["recommendations"]["embeddings"] = "Check Ollama service health"
    except Exception as e:
        status["services"]["embeddings"] = "Failed"
        status["details"]["embeddings"] = f"Cannot connect to Ollama at {OLLAMA_BASE_URL}: {str(e)}"
        status["recommendations"]["embeddings"] = "Run: docker-compose up -d ollama"

    # Overall status
    all_services_ok = all(
        service_status in ["Connected", "Available"] for service_status in status["services"].values()
    )

    status["overall"] = "Healthy" if all_services_ok else "Degraded"
    status["ready_for_production"] = all_services_ok

    return status
