"""
Health Check Manager for FastAPI LLM Backend
Centralized health monitoring and status endpoints
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import time
from datetime import datetime
from dataclasses import asdict

from core.schemas import HealthStatus, ServiceHealth, DetailedHealthResponse
from core.database import get_database_health
from utils.watchdog import get_watchdog, get_health_status
from managers.storage_manager import StorageManager
from utils.human_logging import log_service_status

# Create router for health endpoints
health_router = APIRouter(prefix="/health", tags=["health"])

@health_router.get("/")
async def health_check():
    """Main health check endpoint that includes database status and a human-readable summary."""
    health_status = get_database_health()
    
    # Add cache information
    from core.database import get_cache_manager
    cache_manager = get_cache_manager()
    cache_info = {}
    if cache_manager:
        cache_info = cache_manager.get_cache_stats()
    
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
    
    response = {
        "status": "ok" if healthy == total else "degraded",
        "summary": summary,
        "databases": health_status
    }
    
    if cache_info:
        response["cache"] = cache_info
    
    log_service_status("HEALTH", "checked", f"Health check completed: {healthy}/{total} services healthy")
    return response

@health_router.get("/simple")
async def simple_health():
    """Simple health check without any dependencies."""
    return {
        "status": "ok",
        "timestamp": time.time(),
        "message": "Simple health check working"
    }

@health_router.get("/detailed")
async def detailed_health_check():
    """Detailed health check with subsystem monitoring."""
    try:
        health_status = await get_health_status()
        
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

        log_service_status("HEALTH", "detailed", f"Detailed health check: {overall} ({healthy_count} healthy, {degraded_count} degraded, {unhealthy_count} unhealthy)")
        
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
    except Exception as e:
        log_service_status("HEALTH", "error", f"Detailed health check failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

@health_router.get("/redis")
async def redis_health():
    """Check Redis connectivity specifically."""
    try:
        watchdog = get_watchdog()
        redis_monitor = next((m for m in watchdog.monitors if m.name == "Redis"), None)
        if redis_monitor:
            result = await redis_monitor.check_health()
            log_service_status("HEALTH", "redis", f"Redis health check: {result.status}")
            return {"service": "Redis", "health": result.__dict__}
        
        log_service_status("HEALTH", "warning", "Redis monitor not found")
        return {"service": "Redis", "status": "monitor_not_found"}
    except Exception as e:
        log_service_status("HEALTH", "error", f"Redis health check failed: {str(e)}")
        return {"service": "Redis", "status": "error", "error": str(e)}

@health_router.get("/chromadb")
async def chromadb_health():
    """Check ChromaDB connectivity specifically."""
    try:
        watchdog = get_watchdog()
        chroma_monitor = next((m for m in watchdog.monitors if m.name == "ChromaDB"), None)
        if chroma_monitor:
            result = await chroma_monitor.check_health()
            log_service_status("HEALTH", "chromadb", f"ChromaDB health check: {result.status}")
            return {"service": "ChromaDB", "health": result.__dict__}
        
        log_service_status("HEALTH", "warning", "ChromaDB monitor not found")
        return {"service": "ChromaDB", "status": "monitor_not_found"}
    except Exception as e:
        log_service_status("HEALTH", "error", f"ChromaDB health check failed: {str(e)}")
        return {"service": "ChromaDB", "status": "error", "error": str(e)}

@health_router.get("/history/{service_name}")
async def service_health_history(service_name: str, hours: int = 24):
    """Get health history for a specific service."""
    try:
        watchdog = get_watchdog()
        history = watchdog.get_service_history(service_name, hours)
        
        log_service_status("HEALTH", "history", f"Retrieved {len(history)} health records for {service_name} (last {hours}h)")
        
        return {
            "service": service_name,
            "history_hours": hours,
            "checks": len(history),
            "history": [h.__dict__ for h in history]
        }
    except Exception as e:
        log_service_status("HEALTH", "error", f"Failed to get health history for {service_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get health history: {str(e)}")

@health_router.get("/storage")
async def storage_health():
    """Check storage directory structure and permissions."""
    try:
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
        
        log_service_status("HEALTH", "storage", f"Storage health: {status} ({existing_dirs}/{total_dirs} dirs, {total_size_mb:.1f}MB)")
        
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
    except Exception as e:
        log_service_status("HEALTH", "error", f"Storage health check failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Storage health check failed: {str(e)}")

def get_overall_system_health() -> Dict[str, Any]:
    """Get a summary of overall system health for internal use."""
    try:
        # Quick health check of major components
        db_health = get_database_health()
        
        components = {
            "redis": db_health["redis"]["available"],
            "chromadb": db_health["chromadb"]["available"], 
            "embeddings": db_health["embeddings"]["available"]
        }
        
        healthy_count = sum(1 for status in components.values() if status)
        total_count = len(components)
        
        overall_status = "healthy" if healthy_count == total_count else (
            "degraded" if healthy_count > 0 else "unhealthy"
        )
        
        return {
            "status": overall_status,
            "healthy_components": healthy_count,
            "total_components": total_count,
            "components": components,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        log_service_status("HEALTH", "error", f"Failed to get overall system health: {str(e)}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
