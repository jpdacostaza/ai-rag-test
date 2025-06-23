#!/usr/bin/env python3
"""
Focused test to specifically trigger and verify cache hit logging.
"""

import requests
import json
import time

def test_explicit_cache_hit():
    """Test specifically for cache hit logging."""
    
    base_url = "http://localhost:8001"
    
    print("🎯 FOCUSED CACHE HIT TEST")
    print("=" * 40)
    
    # Use a very simple, predictable message
    test_message = "What is 1+1?"
    
    payload = {
        "user_id": "cache_hit_test",
        "message": test_message
    }
    
    # First request
    print(f"\n1️⃣ First request: {test_message}")
    start1 = time.time()
    response1 = requests.post(f"{base_url}/chat", json=payload, timeout=30)
    time1 = time.time() - start1
    print(f"   ✅ Response in {time1:.2f}s: {response1.json().get('response', '')[:50]}...")
    
    # Short delay
    time.sleep(1)
    
    # Second request (should hit cache)
    print(f"\n2️⃣ Second request (same): {test_message}")
    start2 = time.time()
    response2 = requests.post(f"{base_url}/chat", json=payload, timeout=30)
    time2 = time.time() - start2
    print(f"   ✅ Response in {time2:.2f}s: {response2.json().get('response', '')[:50]}...")
    
    # Verify responses match
    if response1.json().get('response') == response2.json().get('response'):
        print(f"   ✅ Responses identical")
    else:
        print(f"   ❌ Responses differ!")
    
    print(f"\n📊 Timing: First={time1:.2f}s, Second={time2:.2f}s")
    if time2 < time1 * 0.3:
        print(f"   🚀 Cache hit detected (much faster)")
    elif time2 < time1 * 0.7:
        print(f"   ⚡ Possible cache hit (faster)")
    else:
        print(f"   ⚠️  No significant speedup (cache miss?)")

if __name__ == "__main__":
    test_explicit_cache_hit()
