#!/usr/bin/env python3
"""
Test cache hit/miss logging on OpenAI endpoints.
"""

import requests
import json
import time

def test_openai_cache_logging():
    """Test cache logging on OpenAI endpoints."""
    
    base_url = "http://localhost:8001"
    
    print("🤖 OPENAI ENDPOINT CACHE TEST")
    print("=" * 40)
    
    test_message = "What is 5+5?"
    
    payload = {
        "model": "llama3.2:3b",
        "messages": [
            {"role": "user", "content": test_message}
        ],
        "stream": False,
        "max_tokens": 50
    }
    
    # First request
    print(f"\n1️⃣ First OpenAI request: {test_message}")
    start1 = time.time()
    response1 = requests.post(f"{base_url}/v1/chat/completions", json=payload, timeout=30)
    time1 = time.time() - start1
    if response1.status_code == 200:
        content1 = response1.json()['choices'][0]['message']['content']
        print(f"   ✅ Response in {time1:.2f}s: {content1[:50]}...")
    else:
        print(f"   ❌ Failed: {response1.status_code}")
        return
    
    # Short delay
    time.sleep(1)
    
    # Second request (should hit cache if cache is implemented for OpenAI endpoint)
    print(f"\n2️⃣ Second OpenAI request (same): {test_message}")
    start2 = time.time()
    response2 = requests.post(f"{base_url}/v1/chat/completions", json=payload, timeout=30)
    time2 = time.time() - start2
    if response2.status_code == 200:
        content2 = response2.json()['choices'][0]['message']['content']
        print(f"   ✅ Response in {time2:.2f}s: {content2[:50]}...")
        
        if content1 == content2:
            print(f"   ✅ Responses identical")
        else:
            print(f"   ⚠️  Responses differ")
    else:
        print(f"   ❌ Failed: {response2.status_code}")
        return
    
    print(f"\n📊 Timing: First={time1:.2f}s, Second={time2:.2f}s")
    if time2 < time1 * 0.3:
        print(f"   🚀 Cache hit detected")
    else:
        print(f"   ⚠️  No cache speedup (OpenAI endpoint may not use cache)")

if __name__ == "__main__":
    test_openai_cache_logging()
