"""
Debug routes for development and monitoring
"""

from fastapi import APIRouter, Request, Depends
from typing import Dict, Any
from datetime import datetime
import psutil
import sys

from services.dependencies import get_cache_service, get_redis_service, get_vector_service

debug_router = APIRouter(prefix="/debug", tags=["debug"])


@debug_router.get("/cache")
async def get_cache_stats(cache_service=Depends(get_cache_service)) -> Dict[str, Any]:
    """Get cache statistics"""
    try:
        if cache_service:
            return cache_service.get_stats()
        else:
            return {
                "size": 0,
                "max_size": 0,
                "hit_count": 0,
                "miss_count": 0,
                "total_requests": 0,
                "hit_rate": "0.0%",
                "hit_rate_numeric": 0,
                "message": "Cache service not available",
            }
    except Exception as e:
        return {"error": str(e), "cache_enabled": False, "message": "Cache service not available"}


@debug_router.post("/cache/clear")
async def clear_cache(cache_service=Depends(get_cache_service)) -> Dict[str, Any]:
    """Clear the cache"""
    try:
        if cache_service and hasattr(cache_service, 'clear'):
            cache_service.clear()
            return {"status": "success", "message": "Cache cleared"}
        else:
            return {"status": "error", "message": "Cache service not available or doesn't support clearing"}
    except Exception as e:
        return {"status": "error", "message": f"Failed to clear cache: {str(e)}"}


@debug_router.get("/redis")
async def get_redis_stats(redis_service=Depends(get_redis_service)) -> Dict[str, Any]:
    """Get Redis statistics"""
    try:
        if redis_service:
            return await redis_service.get_stats()
        else:
            return {"status": "unavailable", "message": "Redis service not available"}
    except Exception as e:
        return {"status": "error", "message": f"Failed to get Redis stats: {str(e)}"}


@debug_router.get("/vector")
async def get_vector_stats(vector_service=Depends(get_vector_service)) -> Dict[str, Any]:
    """Get vector database statistics"""
    try:
        if vector_service:
            return vector_service.get_stats()
        else:
            return {"status": "unavailable", "message": "Vector service not available"}
    except Exception as e:
        return {"status": "error", "message": f"Failed to get vector stats: {str(e)}"}


@debug_router.get("/services")
async def get_all_service_stats(
    cache_service=Depends(get_cache_service),
    redis_service=Depends(get_redis_service),
    vector_service=Depends(get_vector_service)
) -> Dict[str, Any]:
    """Get statistics for all services"""
    try:
        return {
            "cache": cache_service.get_stats() if cache_service else {"status": "unavailable"},
            "redis": await redis_service.get_stats() if redis_service else {"status": "unavailable"},
            "vector": vector_service.get_stats() if vector_service else {"status": "unavailable"},
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {"status": "error", "message": f"Failed to get service stats: {str(e)}"}


@debug_router.get("/memory")
async def get_memory_usage() -> Dict[str, Any]:
    """Get memory usage statistics"""
    try:
        process = psutil.Process()
        memory_info = process.memory_info()

        return {
            "memory_usage_mb": round(memory_info.rss / 1024 / 1024, 2),
            "memory_percent": round(process.memory_percent(), 2),
            "cpu_percent": round(process.cpu_percent(interval=0.1), 2),
            "threads": process.num_threads(),
            "python_version": sys.version,
            "pid": process.pid,
        }
    except Exception as e:
        return {"error": str(e), "message": "Failed to get memory usage"}


@debug_router.get("/alerts")
async def get_alerts() -> Dict[str, Any]:
    """Get current alerts"""
    try:
        # For now, return placeholder alert stats
        return {
            "alerts": {"total_alerts": 0, "active_alerts": 0, "resolved_alerts": 0, "alerts_24h": 0},
            "timestamp": datetime.now().isoformat(),
            "message": "Alert system placeholder",
        }
    except Exception as e:
        return {"error": str(e), "message": "Alert manager not available"}


@debug_router.get("/config")
async def get_config() -> Dict[str, Any]:
    """Get current configuration (sanitized)"""
    try:
        import config

        return {
            "environment": "development",
            "debug_mode": False,
            "redis_url": "redis://***",  # Sanitized
            "chroma_host": getattr(config, "CHROMA_HOST", "localhost"),
            "ollama_url": getattr(config, "OLLAMA_BASE_URL", "http://localhost:11434"),
            "cache_enabled": True,
            "alert_system_enabled": True,
            "default_model": getattr(config, "DEFAULT_MODEL", "llama3.2:3b"),
            "redis_host": getattr(config, "REDIS_HOST", "localhost"),
            "redis_port": getattr(config, "REDIS_PORT", 6379),
        }
    except Exception as e:
        return {"error": str(e), "message": "Configuration not available"}


@debug_router.get("/endpoints")
async def list_endpoints(request: Request) -> Dict[str, Any]:
    """List all available endpoints dynamically"""
    url_list = [
        {"path": route.path, "name": route.name, "methods": list(route.methods)}
        for route in request.app.routes
    ]
    return {"endpoints": url_list}
