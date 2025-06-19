"""
Enhanced Memory and Cache Health Check for Startup
Validates Redis and ChromaDB connectivity during application initialization.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import asyncio
import time
from typing import Dict, Any, Optional
from human_logging import log_service_status

def quick_redis_check() -> Dict[str, Any]:
    """Quick Redis connectivity and basic functionality test."""
    try:
        from database import get_cache_manager
        
        cache_manager = get_cache_manager()
        if not cache_manager:
            return {
                "status": "failed",
                "error": "Cache manager not available",
                "details": {}
            }
        
        # Test basic operations
        test_key = "startup_health_test"
        test_value = f"test_{int(time.time())}"
          # Set test value
        cache_manager.set_with_validation(test_key, test_value, ttl=10)
        
        # Get test value
        retrieved = cache_manager.get_with_validation(test_key)
        
        # Clean up
        cache_manager.redis_client.delete(test_key)
        
        # Verify operation worked
        if retrieved != test_value:
            return {
                "status": "failed",
                "error": "Cache set/get operation failed",
                "details": {"expected": test_value, "got": retrieved}
            }
        
        # Get basic stats
        stats = cache_manager.get_cache_stats()
        
        return {
            "status": "healthy",
            "error": None,
            "details": {
                "cache_keys": stats.get("total_keys", 0),
                "version": stats.get("version", "unknown"),
                "test_passed": True
            }
        }
        
    except Exception as e:
        return {
            "status": "failed",
            "error": str(e),
            "details": {}
        }

def quick_chromadb_check() -> Dict[str, Any]:
    """Quick ChromaDB connectivity test."""
    try:
        from database import db_manager
        
        if not hasattr(db_manager, 'chroma_client') or db_manager.chroma_client is None:
            return {
                "status": "failed",
                "error": "ChromaDB client not available",
                "details": {}
            }
        
        # Test basic ChromaDB operations
        try:
            # Try to list collections (basic connectivity test)
            collections = db_manager.chroma_client.list_collections()
            collection_count = len(collections)
            
            # Try to get or create a test collection
            test_collection_name = "startup_health_test"
            try:
                test_collection = db_manager.chroma_client.get_or_create_collection(test_collection_name)
                # Clean up immediately
                db_manager.chroma_client.delete_collection(test_collection_name)
                
                return {
                    "status": "healthy",
                    "error": None,
                    "details": {
                        "collections": collection_count,
                        "test_passed": True,
                        "operations": "list_collections, get_or_create_collection, delete_collection"
                    }
                }
            except Exception as e:
                # Collection operations failed, but we can still list
                return {
                    "status": "degraded",
                    "error": f"Collection operations failed: {str(e)}",
                    "details": {
                        "collections": collection_count,
                        "test_passed": False,
                        "operations": "list_collections only"
                    }
                }
                
        except Exception as e:
            return {
                "status": "failed",
                "error": f"ChromaDB connectivity failed: {str(e)}",
                "details": {}
            }
            
    except Exception as e:
        return {
            "status": "failed", 
            "error": str(e),
            "details": {}
        }

def startup_memory_health_check() -> Dict[str, Any]:
    """
    Perform a quick memory/cache health check suitable for startup.
    Returns summary of Redis and ChromaDB status.
    """
    log_service_status("MEMORY_HEALTH", "starting", "Performing startup memory/cache health check...")
    
    start_time = time.time()
    
    # Check Redis (cache + chat history)
    redis_result = quick_redis_check()
    
    # Check ChromaDB (long-term memory)
    chromadb_result = quick_chromadb_check()
      # Summary
    redis_ok = redis_result["status"] == "healthy"
    chromadb_ok = chromadb_result["status"] in ["healthy", "degraded"]
    
    overall_status = "healthy"
    if not redis_ok and not chromadb_ok:
        overall_status = "failed"
    elif not redis_ok or not chromadb_ok:
        overall_status = "degraded"
    
    duration = time.time() - start_time
    
    result = {
        "overall_status": overall_status,
        "duration_ms": round(duration * 1000, 2),
        "redis": redis_result,
        "chromadb": chromadb_result,
        "summary": {
            "redis_healthy": redis_ok,
            "chromadb_healthy": chromadb_ok,
            "cache_available": redis_ok,
            "long_term_memory_available": chromadb_ok
        }
    }
    
    # Log results
    if overall_status == "healthy":
        log_service_status("MEMORY_HEALTH", "ready", f"Memory systems healthy (Redis: ✅, ChromaDB: ✅) - {duration:.2f}s")
    elif overall_status == "degraded":
        redis_status = "✅" if redis_ok else "❌"
        chromadb_status = "✅" if chromadb_ok else "❌"
        log_service_status("MEMORY_HEALTH", "degraded", f"Memory systems degraded (Redis: {redis_status}, ChromaDB: {chromadb_status}) - {duration:.2f}s")
    else:
        log_service_status("MEMORY_HEALTH", "failed", f"Memory systems failed (Redis: ❌, ChromaDB: ❌) - {duration:.2f}s")
    
    return result

def initialize_memory_systems() -> bool:
    """
    Initialize and validate memory systems during startup.
    This combines cache initialization with health checking.
    """
    try:
        # First run the existing cache initialization
        from init_cache import initialize_cache_management
        cache_init_success = initialize_cache_management()
        
        # Then run the health check
        health_result = startup_memory_health_check()
        
        # Determine overall success
        overall_success = cache_init_success and health_result["overall_status"] in ["healthy", "degraded"]
        
        if overall_success:
            log_service_status("MEMORY_INIT", "ready", "Memory systems initialized and validated successfully")
        else:
            log_service_status("MEMORY_INIT", "warning", "Memory systems initialization completed with issues")
        
        return overall_success
        
    except Exception as e:
        log_service_status("MEMORY_INIT", "failed", f"Memory systems initialization failed: {e}")
        return False

if __name__ == "__main__":
    # Run as standalone script for testing
    from human_logging import init_logging
    init_logging(level="INFO")
    
    print("=== Startup Memory Health Check ===")
    result = startup_memory_health_check()
    
    print("\nResults:")
    print(f"Overall Status: {result['overall_status']}")
    print(f"Duration: {result['duration_ms']}ms")
    print(f"Redis: {result['redis']['status']} - {result['redis'].get('error', 'OK')}")
    print(f"ChromaDB: {result['chromadb']['status']} - {result['chromadb'].get('error', 'OK')}")
    
    if result['redis']['status'] == 'healthy':
        details = result['redis']['details']
        print(f"  - Cache keys: {details.get('cache_keys', 'unknown')}")
        print(f"  - Version: {details.get('version', 'unknown')}")
    
    if result['chromadb']['status'] in ['healthy', 'degraded']:
        details = result['chromadb']['details']
        print(f"  - Collections: {details.get('collections', 'unknown')}")
        print(f"  - Operations: {details.get('operations', 'unknown')}")
    
    success = result['overall_status'] in ['healthy', 'degraded']
    sys.exit(0 if success else 1)
