#!/usr/bin/env python3
"""
Quick API Test
==============
Simple test to verify the API is working before running comprehensive tests.
"""

import requests
import time

def test_api():
    base_url = "http://localhost:8001"
    api_key = "f2b985dd-219f-45b1-a90e-170962cc7082"
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": api_key
    }
    
    print("🧪 Quick API Test")
    print("=" * 40)
    
    # Test 1: Health check
    print("1. Testing health endpoint...")
    try:
        response = requests.get(f"{base_url}/health/simple", timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ Health check passed")
        else:
            print("   ❌ Health check failed")
    except Exception as e:
        print(f"   ❌ Health check error: {e}")
    
    # Test 2: Models endpoint
    print("\n2. Testing models endpoint...")
    try:
        response = requests.get(f"{base_url}/models", headers=headers, timeout=10)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            model_count = len(data.get("data", []))
            print(f"   ✅ Models endpoint passed - Found {model_count} models")
        else:
            print("   ❌ Models endpoint failed")
    except Exception as e:
        print(f"   ❌ Models endpoint error: {e}")
    
    # Test 3: Simple chat
    print("\n3. Testing chat endpoint...")
    try:
        chat_data = {
            "user_id": "quick_test_user",
            "message": "Hello, what is 2+2?"
        }
        response = requests.post(f"{base_url}/chat", headers=headers, json=chat_data, timeout=30)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            response_text = data.get("response", "")
            print(f"   ✅ Chat endpoint passed - Response length: {len(response_text)} chars")
            if len(response_text) > 0:
                print(f"   📝 Response preview: {response_text[:100]}...")
        else:
            print(f"   ❌ Chat endpoint failed - Response: {response.text[:200]}")
    except Exception as e:
        print(f"   ❌ Chat endpoint error: {e}")
    
    print("\n🏁 Quick test completed!")

if __name__ == "__main__":
    test_api()
