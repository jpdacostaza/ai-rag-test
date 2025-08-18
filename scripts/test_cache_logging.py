#!/usr/bin/env python3
"""
Simple test to demonstrate prompt cache logging.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from services.prompt_cache_service import prompt_cache_service
from core.unified_logging import get_logger

logger = get_logger(__name__)

async def test_cache_logging():
    """Test cache operations with logging."""
    print("🧪 Testing Cache Logging...")
    print("=" * 40)
    
    # Test data
    test_prompt = "What is the capital of France?"
    test_response = "The capital of France is Paris. It's a beautiful city known for its art, culture, and architecture."
    test_model = "test-model"
    cache_type = "educational"
    
    print("🔧 Step 1: Clearing any existing cache...")
    await prompt_cache_service.clear_cache()
    
    print("\n📝 Step 2: First request (should be cache miss)...")
    # First request - should miss
    cached_result = await prompt_cache_service.get_cached_prompt(
        test_prompt, test_model, cache_type
    )
    if cached_result:
        print(f"❌ Unexpected cache hit!")
    else:
        print(f"✅ Cache miss as expected")
    
    print("\n💾 Step 3: Caching the response...")
    # Cache the response
    success = await prompt_cache_service.cache_prompt(
        test_prompt, test_response, test_model, cache_type
    )
    if success:
        print(f"✅ Response cached successfully")
    else:
        print(f"❌ Failed to cache response")
    
    print("\n🚀 Step 4: Second request (should be cache hit)...")
    # Second request - should hit
    cached_result = await prompt_cache_service.get_cached_prompt(
        test_prompt, test_model, cache_type
    )
    if cached_result:
        print(f"✅ Cache hit! Retrieved {len(cached_result.content)} characters")
        print(f"   Content preview: {cached_result.content[:100]}...")
    else:
        print(f"❌ Unexpected cache miss!")
    
    print("\n📊 Step 5: Cache statistics...")
    stats = prompt_cache_service.get_cache_stats()
    print(f"   Hit Rate: {stats['hit_rate']:.1f}%")
    print(f"   Total Hits: {stats['total_hits']}")
    print(f"   Total Misses: {stats['total_misses']}")
    
    print(f"\n✅ Cache logging test completed!")

if __name__ == "__main__":
    asyncio.run(test_cache_logging())
