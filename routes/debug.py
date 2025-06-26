"""
Debug routes for development and monitoring
"""

from fastapi import APIRouter
from typing import Dict, Any
from datetime import datetime
import psutil
import sys

debug_router = APIRouter(prefix="/debug", tags=["debug"])


@debug_router.get("/cache")
async def get_cache_stats() -> Dict[str, Any]:
    """Get cache statistics"""
    try:
        from database_manager import db_manager

        if hasattr(db_manager, "cache_manager") and db_manager.cache_manager:
            return db_manager.cache_manager.get_stats()
        else:
            return {
                "size": 0,
                "max_size": 0,
                "hit_count": 0,
                "miss_count": 0,
                "total_requests": 0,
                "hit_rate": "0.0%",
                "hit_rate_numeric": 0,
                "message": "Cache manager not available",
            }
    except Exception as e:
        return {"error": str(e), "cache_enabled": False, "message": "Cache manager not available"}


@debug_router.post("/cache/clear")
async def clear_cache() -> Dict[str, Any]:
    """Clear the cache"""
    try:
        from database_manager import db_manager

        if hasattr(db_manager, "cache_manager") and db_manager.cache_manager:
            db_manager.cache_manager.clear()
            return {"status": "success", "message": "Cache cleared"}
        else:
            return {"status": "error", "message": "Cache manager not available"}
    except Exception as e:
        return {"status": "error", "message": f"Failed to clear cache: {str(e)}"}


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
async def list_endpoints() -> Dict[str, Any]:
    """List all available endpoints"""
    return {
        "endpoints": {
            "health": ["GET /health", "GET /"],
            "chat": ["POST /chat"],
            "upload": [
                "POST /upload/document",
                "POST /upload/search",
                "POST /upload/file",
                "GET /upload/health",
                "GET /upload/formats",
            ],
            "models": ["GET /v1/models"],
            "pipelines": ["GET /pipelines", "GET /pipelines/{pipeline_id}", "POST /pipelines/{pipeline_id}/execute"],
            "debug": [
                "GET /debug/cache",
                "POST /debug/cache/clear",
                "GET /debug/memory",
                "GET /debug/alerts",
                "GET /debug/config",
                "GET /debug/endpoints",
            ],
        },
        "total_endpoints": 17,
    }
