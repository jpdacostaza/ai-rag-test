"""Cache Manager Test Suite"""
import redis
import json
import time
from datetime import datetime

def test_cache_manager():
    print("🧪 Cache Manager Test Suite")
    print("=" * 40)
    
    try:
        # Import cache manager
        from cache_manager import CacheManager
        print("✅ CacheManager imported successfully")
        
        # Connect to Redis
        redis_client = redis.Redis(
            host='localhost',
            port=6379,
            db=1,
            decode_responses=True,
            socket_timeout=5
        )
        redis_client.ping()
        redis_client.flushdb()
        print("✅ Redis connection successful")
        
        # Initialize CacheManager
        cache_manager = CacheManager(redis_client)
        print("✅ CacheManager initialized")
        
        # Test 1: Basic functionality
        print("\n🧪 Test 1: Basic Cache Operations")
        key = "test:basic"
        value = "This is a test response"
        
        # Set cache
        result = cache_manager.set_with_validation(key, value, 60)
        print(f"   Set cache: {result}")
        
        # Get cache
        retrieved = cache_manager.get_with_validation(key)
        print(f"   Retrieved: {retrieved}")
        
        if retrieved == value:
            print("✅ PASS: Basic cache operations")
        else:
            print("❌ FAIL: Basic cache operations")
            return False
        
        # Test 2: JSON rejection
        print("\n🧪 Test 2: JSON Response Rejection")
        json_key = "test:json"
        json_value = '{"response": "This should be rejected"}'
        
        result = cache_manager.set_with_validation(json_key, json_value)
        print(f"   JSON cache attempt: {result}")
        
        if not result:
            print("✅ PASS: JSON rejection")
        else:
            print("❌ FAIL: JSON was incorrectly cached")
            return False
        
        # Test 3: Cache statistics
        print("\n🧪 Test 3: Cache Statistics")
        redis_client.set("chat:user1", "response1")
        redis_client.set("other:data", "data1")
        
        stats = cache_manager.get_cache_stats()
        print(f"   Stats: {stats}")
        
        if "cache_counts" in stats and "total_keys" in stats:
            print("✅ PASS: Cache statistics")
        else:
            print("❌ FAIL: Cache statistics")
            return False
        
        # Test 4: System prompt detection
        print("\n🧪 Test 4: System Prompt Detection")
        
        # Add chat cache
        redis_client.set("chat:test1", "cached1")
        redis_client.set("chat:test2", "cached2")
        redis_client.set("other:keep", "keep_this")
        
        # Change system prompt
        cache_manager.check_system_prompt_change("New prompt")
        
        # Check results
        chat_exists = redis_client.exists("chat:test1")
        other_exists = redis_client.exists("other:keep")
        
        if not chat_exists and other_exists:
            print("✅ PASS: System prompt detection")
        else:
            print(f"❌ FAIL: Chat exists: {chat_exists}, Other exists: {other_exists}")
            return False
        
        print("\n" + "=" * 40)
        print("🎉 ALL TESTS PASSED!")
        print("✅ Basic cache operations")
        print("✅ JSON response rejection")
        print("✅ Cache statistics")
        print("✅ System prompt detection")
        print("=" * 40)
        
        # Save results
        results = {
            "timestamp": datetime.utcnow().isoformat(),
            "status": "SUCCESS",
            "tests_passed": 4,
            "cache_version": cache_manager.CACHE_VERSION
        }
        
        with open("cache_test_results.json", "w") as f:
            json.dump(results, f, indent=2)
        
        print(f"📄 Results saved to: cache_test_results.json")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_cache_manager()
