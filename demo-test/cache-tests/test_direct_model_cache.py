#!/usr/bin/env python3
"""
Direct test of model cache functions by importing them directly.
"""

import sys
import os
import asyncio
import time

# Add the backend directory to the path
sys.path.insert(0, '/Projects/opt/backend')

# Test the model cache functions directly
async def test_model_cache_functions():
    print("🧪 Testing Model Cache Functions Directly")
    print("=" * 50)
    
    try:
        # Import the functions from main.py
        from main import refresh_model_cache, ensure_model_available, _model_cache
        
        print("✅ Successfully imported model cache functions")
        
        # Test 1: Check initial cache state
        print(f"\n📊 Initial cache state:")
        print(f"   - Cache data length: {len(_model_cache['data'])}")
        print(f"   - Last updated: {_model_cache['last_updated']}")
        print(f"   - TTL: {_model_cache['ttl']}")
        print(f"   - Age: {time.time() - _model_cache['last_updated']:.2f}s")
        
        # Test 2: Refresh model cache
        print(f"\n🔄 Testing refresh_model_cache...")
        models = await refresh_model_cache(force=True)
        print(f"✅ Refresh successful - found {len(models)} models:")
        for model in models[:3]:
            print(f"   - {model}")
        
        # Test 3: Check cache state after refresh
        print(f"\n📊 Cache state after refresh:")
        print(f"   - Cache data length: {len(_model_cache['data'])}")
        print(f"   - Last updated: {_model_cache['last_updated']}")
        print(f"   - Age: {time.time() - _model_cache['last_updated']:.2f}s")
        
        # Test 4: Test model availability
        if models:
            test_model = models[0]
            print(f"\n🔍 Testing ensure_model_available with: {test_model}")
            available = await ensure_model_available(test_model)
            print(f"✅ Model availability check: {available}")
        
        print(f"\n🎉 All model cache function tests completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error during model cache function test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(test_model_cache_functions())
    if result:
        print("\n✅ Model cache implementation is working!")
    else:
        print("\n❌ Model cache implementation has issues.")
