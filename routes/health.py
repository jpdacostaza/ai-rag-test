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
        self.monitors = []
    
    def get_service_history(self, service_name: str, hours: int):
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
        return {"directories": {}}
    
    @staticmethod  
    def validate_permissions():
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
        "message": "Simple health check working"
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
