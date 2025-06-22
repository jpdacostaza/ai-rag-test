#!/usr/bin/env python3
"""
Cache hit/miss logging verification test.
Tests that cache is working and logging cache hits/misses properly.
"""

import requests
import json
import time

def test_cache_logging():
    """Test cache hit/miss logging functionality."""
    
    base_url = "http://localhost:8001"
    test_user_id = "cache_test_user"
    test_message = "What is 2 + 2? Please respond with just the number."
    
    print("🔍 CACHE HIT/MISS LOGGING VERIFICATION")
    print("=" * 60)
    
    # Test 1: First request should be a cache MISS
    print("\n📝 Test 1: First request (should be cache MISS)")
    print("-" * 40)
    
    payload_chat = {
        "user_id": test_user_id,
        "message": test_message
    }
    
    print(f"Sending request to /chat endpoint...")
    print(f"User ID: {test_user_id}")
    print(f"Message: {test_message}")
    
    start_time = time.time()
    try:
        response = requests.post(
            f"{base_url}/chat",
            json=payload_chat,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        elapsed = (time.time() - start_time) * 1000
        
        print(f"✅ Status: {response.status_code}")
        print(f"⏱️  Response time: {elapsed:.2f}ms")
        
        if response.status_code == 200:
            result = response.json()
            print(f"📝 Response: {result.get('response', 'No response field')}")
            print("💡 This should show as cache MISS in backend logs")
        else:
            print(f"❌ Failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    # Wait a moment before second request
    print(f"\n⏳ Waiting 2 seconds before next request...")
    time.sleep(2)
    
    # Test 2: Second identical request should be a cache HIT
    print("\n📝 Test 2: Identical request (should be cache HIT)")
    print("-" * 40)
    
    print(f"Sending identical request to /chat endpoint...")
    print(f"User ID: {test_user_id}")
    print(f"Message: {test_message}")
    
    start_time = time.time()
    try:
        response = requests.post(
            f"{base_url}/chat",
            json=payload_chat,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        elapsed = (time.time() - start_time) * 1000
        
        print(f"✅ Status: {response.status_code}")
        print(f"⏱️  Response time: {elapsed:.2f}ms")
        
        if response.status_code == 200:
            result = response.json()
            print(f"📝 Response: {result.get('response', 'No response field')}")
            print("💡 This should show as cache HIT in backend logs")
            print("💡 Response time should be much faster (~ms vs seconds)")
        else:
            print(f"❌ Failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    # Test 3: Different message should be cache MISS
    print("\n📝 Test 3: Different message (should be cache MISS)")
    print("-" * 40)
    
    different_message = "What is 3 + 3? Please respond with just the number."
    payload_different = {
        "user_id": test_user_id,
        "message": different_message
    }
    
    print(f"Sending different request to /chat endpoint...")
    print(f"User ID: {test_user_id}")
    print(f"Message: {different_message}")
    
    start_time = time.time()
    try:
        response = requests.post(
            f"{base_url}/chat",
            json=payload_different,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        elapsed = (time.time() - start_time) * 1000
        
        print(f"✅ Status: {response.status_code}")
        print(f"⏱️  Response time: {elapsed:.2f}ms")
        
        if response.status_code == 200:
            result = response.json()
            print(f"📝 Response: {result.get('response', 'No response field')}")
            print("💡 This should show as cache MISS in backend logs")
        else:
            print(f"❌ Failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    # Test 4: Test with OpenAI endpoint too
    print("\n📝 Test 4: OpenAI endpoint cache test")
    print("-" * 40)
    
    openai_payload = {
        "model": "llama3.2:3b",
        "messages": [
            {"role": "user", "content": "What is 4 + 4? Just the number please."}
        ],
        "stream": False,
        "max_tokens": 10
    }
    
    print(f"Testing /v1/chat/completions endpoint...")
    
    # First request (should be MISS)
    start_time = time.time()
    try:
        response = requests.post(
            f"{base_url}/v1/chat/completions",
            json=openai_payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        elapsed = (time.time() - start_time) * 1000
        
        print(f"✅ First request - Status: {response.status_code}, Time: {elapsed:.2f}ms")
        
        if response.status_code == 200:
            result = response.json()
            content = result['choices'][0]['message']['content']
            print(f"📝 Response: {content}")
        
        # Second identical request (should be HIT if caching is enabled for this endpoint)
        time.sleep(1)
        start_time = time.time()
        response2 = requests.post(
            f"{base_url}/v1/chat/completions",
            json=openai_payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        elapsed2 = (time.time() - start_time) * 1000
        
        print(f"✅ Second request - Status: {response2.status_code}, Time: {elapsed2:.2f}ms")
        
        if response2.status_code == 200:
            result2 = response2.json()
            content2 = result2['choices'][0]['message']['content']
            print(f"📝 Response: {content2}")
            
            # Compare response times
            if elapsed2 < elapsed / 2:
                print("💡 Second request was much faster - likely cache HIT")
            else:
                print("💡 Similar response times - may not be cached or cache miss")
                
    except Exception as e:
        print(f"❌ Error in OpenAI endpoint test: {e}")
    
    print(f"\n🎯 CACHE TEST SUMMARY")
    print("=" * 60)
    print("✅ Cache tests completed")
    print("📋 To verify cache logging, check backend logs for:")
    print("   - '[CACHE] 🟡 Cache miss' messages")
    print("   - '[CACHE] ✅ Cache hit' messages") 
    print("   - Cache key generation and retrieval logs")
    print("\n💡 Expected behavior:")
    print("   - First requests: MISS (slower, calls LLM)")
    print("   - Identical requests: HIT (faster, from cache)")
    print("   - Different requests: MISS (new cache entry)")
    
    return True

if __name__ == "__main__":
    test_cache_logging()
