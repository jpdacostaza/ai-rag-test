"""
Test cache functionality to ensure hits are happening properly
"""
import requests
import time
import json
import hashlib

BASE_URL = "http://localhost:9099"

def generate_cache_key(user_id: str, message: str) -> str:
    """Generate the same cache key as the backend."""
    message_hash = hashlib.md5(message.encode()).hexdigest()[:8]
    return f"chat:{user_id}:{message_hash}"

def test_cache_functionality():
    """Test if cache hits are working properly after fixes"""
    print("🔧 Testing Fixed Cache Functionality")
    print("=" * 60)
    
    # Reset cache stats baseline
    initial_stats = requests.get(f"{BASE_URL}/debug/cache").json()
    print(f"📊 Initial Cache Stats: {initial_stats['hit_count']} hits, {initial_stats['miss_count']} misses")
    
    # Test 1: Simple repeated chat message
    print("\n1️⃣ Testing Simple Repeated Message:")
    
    test_payload = {
        "user_id": "cache_test_001",
        "message": "What is 2+2?",
        "model": "llama3.2:3b"
    }
    
    expected_key = generate_cache_key(test_payload["user_id"], test_payload["message"])
    print(f"   Expected cache key: {expected_key}")
    
    # First request (should be cache miss)
    print("   🟡 First request (expecting cache miss)...")
    start1 = time.time()
    try:
        response1 = requests.post(f"{BASE_URL}/chat", json=test_payload, timeout=30)
        time1 = (time.time() - start1) * 1000
        if response1.status_code == 200:
            print(f"   ✅ First request: {response1.status_code} - {time1:.2f}ms")
            result1 = response1.json()['response'][:50] + "..."
            print(f"   📝 Response: {result1}")
        else:
            print(f"   ❌ First request failed: {response1.status_code}")
            return
    except Exception as e:
        print(f"   ❌ First request error: {e}")
        return
    
    # Wait a moment then check cache stats
    time.sleep(2)
    stats_after_first = requests.get(f"{BASE_URL}/debug/cache").json()
    print(f"   📊 After first request: {stats_after_first['hit_count']} hits, {stats_after_first['miss_count']} misses")
    
    # Second request (should be cache hit)
    print("   🟢 Second request (expecting cache hit)...")
    start2 = time.time()
    try:
        response2 = requests.post(f"{BASE_URL}/chat", json=test_payload, timeout=30)
        time2 = (time.time() - start2) * 1000
        if response2.status_code == 200:
            print(f"   ✅ Second request: {response2.status_code} - {time2:.2f}ms")
            result2 = response2.json()['response'][:50] + "..."
            print(f"   📝 Response: {result2}")
            
            # Check if responses are the same (cache hit indicator)
            if result1 == result2:
                print("   ✅ Responses match (good sign for caching)")
            else:
                print("   ⚠️  Responses differ (might not be cached)")
            
            # Check speed improvement
            if time2 < time1 * 0.3:  # Should be much faster
                print(f"   ✅ Speed improved significantly ({time1:.0f}ms → {time2:.0f}ms)")
            else:
                print(f"   ⚠️  Speed improvement unclear ({time1:.0f}ms → {time2:.0f}ms)")
        else:
            print(f"   ❌ Second request failed: {response2.status_code}")
    except Exception as e:
        print(f"   ❌ Second request error: {e}")
    
    # Check final cache stats
    time.sleep(2)
    stats_after_second = requests.get(f"{BASE_URL}/debug/cache").json()
    print(f"   📊 After second request: {stats_after_second['hit_count']} hits, {stats_after_second['miss_count']} misses")
    
    # Calculate improvement
    hits_gained = stats_after_second['hit_count'] - initial_stats['hit_count']
    misses_gained = stats_after_second['miss_count'] - initial_stats['miss_count']
    
    print(f"\n📈 Test Results:")
    print(f"   Cache Hits Gained: {hits_gained}")
    print(f"   Cache Misses Gained: {misses_gained}")
    
    if hits_gained > 0:
        print("   ✅ Cache is working! Hits are being recorded.")
    else:
        print("   ❌ Cache may not be working - no hits recorded.")
    
    # Test 2: Different users should not share cache
    print("\n2️⃣ Testing Cache Isolation Between Users:")
    
    user1_payload = {
        "user_id": "user_001",
        "message": "Hello world",
        "model": "llama3.2:3b"
    }
    
    user2_payload = {
        "user_id": "user_002", 
        "message": "Hello world",  # Same message, different user
        "model": "llama3.2:3b"
    }
    
    print("   🔄 Testing user1...")
    try:
        resp1 = requests.post(f"{BASE_URL}/chat", json=user1_payload, timeout=30)
        if resp1.status_code == 200:
            print("   ✅ User1 request successful")
    except Exception as e:
        print(f"   ❌ User1 error: {e}")
    
    print("   🔄 Testing user2...")
    try:
        resp2 = requests.post(f"{BASE_URL}/chat", json=user2_payload, timeout=30)
        if resp2.status_code == 200:
            print("   ✅ User2 request successful")
    except Exception as e:
        print(f"   ❌ User2 error: {e}")
    
    print("   🔄 Testing user1 again (should hit cache)...")
    try:
        start_cached = time.time()
        resp1_again = requests.post(f"{BASE_URL}/chat", json=user1_payload, timeout=30)
        time_cached = (time.time() - start_cached) * 1000
        if resp1_again.status_code == 200:
            print(f"   ✅ User1 repeat request: {time_cached:.2f}ms")
    except Exception as e:
        print(f"   ❌ User1 repeat error: {e}")
    
    # Final stats
    final_stats = requests.get(f"{BASE_URL}/debug/cache").json()
    print(f"\n📊 Final Cache Statistics:")
    print(f"   Total Hits: {final_stats['hit_count']}")
    print(f"   Total Misses: {final_stats['miss_count']}")
    print(f"   Hit Rate: {final_stats['hit_rate']}")
    print(f"   Cache Size: {final_stats['size']}")
    
    overall_hits = final_stats['hit_count'] - initial_stats['hit_count']
    overall_misses = final_stats['miss_count'] - initial_stats['miss_count']
    
    if overall_hits > 0:
        hit_ratio = overall_hits / (overall_hits + overall_misses) * 100
        print(f"\n✅ CACHE TEST SUCCESS!")
        print(f"   This session: {overall_hits} hits, {overall_misses} misses")
        print(f"   This session hit rate: {hit_ratio:.1f}%")
    else:
        print(f"\n❌ CACHE TEST FAILED!")
        print(f"   No cache hits recorded during testing")
        print(f"   Debug: Check cache key generation and storage logic")

if __name__ == "__main__":
    test_cache_functionality()
