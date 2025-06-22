#!/usr/bin/env python3
"""
Test script to verify cache hit/miss logging is working properly.
This script will:
1. Make a request that should result in a cache miss
2. Make the same request again that should result in a cache hit
3. Check the backend logs for the explicit cache hit/miss messages
"""

import requests
import json
import time

def test_cache_logging():
    """Test cache hit/miss logging with explicit verification."""
    
    base_url = "http://localhost:8001"
    
    print("🔍 CACHE HIT/MISS LOGGING VERIFICATION")
    print("=" * 50)
    
    # Unique test message to ensure cache behavior
    test_message = f"Hello, what is 2+2? (test at {int(time.time())})"
    
    # Test 1: First request (should be cache miss)
    print(f"\n🟡 Test 1: First request (expecting CACHE MISS)")
    print(f"Message: {test_message}")
    
    payload = {
        "user_id": "cache_test_user",
        "message": test_message
    }
    
    start_time = time.time()
    try:
        response1 = requests.post(
            f"{base_url}/chat",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        duration1 = time.time() - start_time
        
        if response1.status_code == 200:
            result1 = response1.json()
            print(f"✅ First request successful in {duration1:.2f}s")
            print(f"Response: {result1.get('response', 'No response')[:100]}...")
        else:
            print(f"❌ First request failed ({response1.status_code}): {response1.text}")
            return
            
    except Exception as e:
        print(f"❌ First request error: {e}")
        return
    
    # Wait a moment
    time.sleep(2)
    
    # Test 2: Second request (should be cache hit)
    print(f"\n✅ Test 2: Second request (expecting CACHE HIT)")
    print(f"Same message: {test_message}")
    
    start_time = time.time()
    try:
        response2 = requests.post(
            f"{base_url}/chat",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        duration2 = time.time() - start_time
        
        if response2.status_code == 200:
            result2 = response2.json()
            print(f"✅ Second request successful in {duration2:.2f}s")
            print(f"Response: {result2.get('response', 'No response')[:100]}...")
            
            # Compare responses
            if result1.get('response') == result2.get('response'):
                print(f"✅ Responses match (indicating cache working)")
            else:
                print(f"⚠️  Responses differ (cache may not be working)")
                
            # Compare timing
            if duration2 < duration1 * 0.5:  # Cache hit should be much faster
                print(f"✅ Second request significantly faster ({duration2:.2f}s vs {duration1:.2f}s)")
            else:
                print(f"⚠️  Second request not significantly faster (may not be cached)")
                
        else:
            print(f"❌ Second request failed ({response2.status_code}): {response2.text}")
            return
            
    except Exception as e:
        print(f"❌ Second request error: {e}")
        return
    
    # Test 3: Third request with different message (should be cache miss)
    print(f"\n🟡 Test 3: Different message (expecting CACHE MISS)")
    
    different_message = f"What is 3+3? (different test at {int(time.time())})"
    payload_different = {
        "user_id": "cache_test_user",
        "message": different_message
    }
    
    start_time = time.time()
    try:
        response3 = requests.post(
            f"{base_url}/chat",
            json=payload_different,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        duration3 = time.time() - start_time
        
        if response3.status_code == 200:
            result3 = response3.json()
            print(f"✅ Third request successful in {duration3:.2f}s")
            print(f"Response: {result3.get('response', 'No response')[:100]}...")
        else:
            print(f"❌ Third request failed ({response3.status_code}): {response3.text}")
            
    except Exception as e:
        print(f"❌ Third request error: {e}")
    
    print(f"\n📊 TIMING SUMMARY:")
    print(f"   Request 1 (miss): {duration1:.2f}s")
    print(f"   Request 2 (hit):  {duration2:.2f}s")
    print(f"   Request 3 (miss): {duration3:.2f}s")
    
    print(f"\n🔍 EXPECTED LOG MESSAGES:")
    print(f"   Look for these messages in backend logs:")
    print(f"   - [CACHE] 🟡 Cache MISS for key: chat:cache_test_user:...")
    print(f"   - [CACHE] 💾 Cache SET for key: chat:cache_test_user:...")
    print(f"   - [CACHE] ✅ Cache HIT for key: chat:cache_test_user:...")
    print(f"   - [CACHE] 🚀 Returning cached response for user cache_test_user")
    
    print(f"\n📋 NEXT STEPS:")
    print(f"   1. Check backend logs: docker logs backend-llm-backend")
    print(f"   2. Look for the cache hit/miss emoji messages")
    print(f"   3. Verify timing differences indicate cache working")

if __name__ == "__main__":
    test_cache_logging()
