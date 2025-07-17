#!/usr/bin/env python3
"""
Test script to debug Redis service issue
"""

import asyncio
import sys
import os

# Add project root to path
sys.path.append('/app')
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

async def test_redis_service():
    """Test our Redis service directly."""
    print("Testing Redis service...")
    
    # Use the global database manager
    from services.database_manager import db_manager
    
    if not db_manager:
        print("ERROR: Global database manager not available")
        return
    
    print("Ensuring database manager is initialized...")
    await db_manager.ensure_initialized()
    
    if not db_manager.redis_client:
        print("ERROR: Redis client not initialized")
        return
        
    print(f"Redis client type: {type(db_manager.redis_client)}")
    
    # Test Redis service
    from services.redis_service import RedisService
    redis_service = RedisService(redis_client=db_manager.redis_client)
    
    print("Testing Redis service health check...")
    health_result = await redis_service.health_check()
    print(f"Health check result: {health_result}")
    
    print("Testing Redis service get_stats...")
    try:
        stats_result = await redis_service.get_stats()
        print(f"Stats result: {stats_result}")
    except Exception as e:
        print(f"ERROR in get_stats: {e}")
        import traceback
        traceback.print_exc()
    
    # Test the Redis client directly
    print("\nTesting Redis client directly...")
    try:
        info = await db_manager.redis_client.info()
        print(f"Direct Redis info type: {type(info)}")
        print(f"Has .get() method: {hasattr(info, 'get')}")
        if hasattr(info, 'get'):
            print(f"Used memory: {info.get('used_memory_human', 'unknown')}")
    except Exception as e:
        print(f"ERROR with direct Redis call: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_redis_service())
