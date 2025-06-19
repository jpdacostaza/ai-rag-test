#!/usr/bin/env python3
"""
Direct Cache Logging Test
Tests the enhanced cache hit/miss logging directly with the cache manager
used by the backend.
"""

import redis
import time
from cache_manager import CacheManager
from database import get_cache_manager, get_cache, set_cache
from database_manager import DatabaseManager

def test_backend_cache_integration():
    """Test the cache manager as used by the backend."""
    print("🧪 Backend Cache Integration Test")
    print("=" * 50)
    
    try:
        # Initialize database manager (same as backend)
        db_manager = DatabaseManager()
        print("✅ DatabaseManager initialized")
        
        # Get cache manager (same as backend uses)
        cache_manager = get_cache_manager()
        if not cache_manager:
            print("❌ Cache manager not available")
            return False
        
        print("✅ Cache manager obtained")
        
        # Test cache operations as the backend does
        user_id = "backend_test_user"
        
        # Test 1: Cache miss scenario (similar to main.py)
        print("\n🔍 Test 1: Backend-style cache operations")
        
        cache_key = f"chat:{user_id}:test_message_hash"
        print(f"Cache key: {cache_key}")
        
        # Check cache (this should be a miss and will log)
        print("Checking cache with get_cache()...")
        cached_response = get_cache(db_manager, cache_key, user_id, "test_request_1")
        
        if cached_response:
            print(f"✅ Cache hit: {cached_response[:50]}...")
        else:
            print("❌ Cache miss - generating response")
            
            # Simulate response generation
            new_response = "This is a test response about artificial intelligence and machine learning concepts."
            
            # Cache the response (this should log the SET operation)
            print("Setting cache with set_cache()...")
            success = set_cache(db_manager, cache_key, new_response, 600, user_id, "test_request_1")
            
            if success:
                print("✅ Response cached successfully")
            else:
                print("❌ Failed to cache response")
        
        # Test 2: Cache hit scenario
        print("\n🔍 Test 2: Cache hit scenario")
        
        # This should now be a cache hit
        print("Checking cache again (should be hit)...")
        cached_response = get_cache(db_manager, cache_key, user_id, "test_request_2")
        
        if cached_response:
            print(f"✅ Cache hit: {cached_response[:50]}...")
        else:
            print("❌ Unexpected cache miss")
        
        # Test 3: Multiple cache operations
        print("\n🔍 Test 3: Multiple cache operations")
        
        test_data = [
            ("What is Python?", "Python is a programming language..."),
            ("Explain databases", "Databases store and organize data..."),
            ("What is web development?", "Web development involves creating websites...")
        ]
        
        for i, (question, answer) in enumerate(test_data, 1):
            print(f"\nOperation {i}: {question}")
            test_key = f"chat:{user_id}:question_{i}"
            
            # Check cache first
            cached = get_cache(db_manager, test_key, user_id, f"test_request_{i}_get")
            if not cached:
                # Set cache
                set_cache(db_manager, test_key, answer, 300, user_id, f"test_request_{i}_set")
            
            # Verify it's now cached
            get_cache(db_manager, test_key, user_id, f"test_request_{i}_verify")
        
        print("\n✅ All cache operations completed")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_system_prompt_logging():
    """Test system prompt change detection with logging."""
    print("\n🧪 System Prompt Change Test")
    print("=" * 50)
    
    try:
        cache_manager = get_cache_manager()
        if not cache_manager:
            print("❌ Cache manager not available")
            return False
        
        # Test system prompt change (this should log the invalidation)
        print("Testing system prompt change detection...")
        
        current_prompt = "You are a helpful assistant that provides detailed explanations with examples."
        cache_manager.check_system_prompt_change(current_prompt)
        
        print("✅ System prompt check completed")
        return True
        
    except Exception as e:
        print(f"❌ System prompt test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Direct Cache Logging Test Suite")
    print("Testing enhanced cache hit/miss logging as used by backend")
    print("=" * 60)
    
    success1 = test_backend_cache_integration()
    success2 = test_system_prompt_logging()
    
    if success1 and success2:
        print("\n🎉 All tests completed successfully!")
        print("Check the logs above to see cache hit/miss logging in action")
    else:
        print("\n❌ Some tests failed")
