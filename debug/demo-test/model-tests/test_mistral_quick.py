#!/usr/bin/env python3
"""
Quick test for Mistral 7B Instruct model endpoints.
"""

import json
import time
import requests
from datetime import datetime

# Configuration
BACKEND_URL = "http://localhost:8001"
MODEL_NAME = "mistral:7b-instruct-v0.3-q4_k_m"

def test_chat_endpoint():
    """Test the /chat endpoint with required user_id"""
    print("Testing /chat endpoint...")
    
    payload = {
        "message": "Hello! Please introduce yourself briefly.",
        "user_id": "test_user_001"
    }
    
    try:
        start_time = time.time()
        response = requests.post(f"{BACKEND_URL}/chat", json=payload, timeout=60)
        response_time = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            response_text = data.get("response", "")
            print(f"✅ PASSED - Response time: {response_time:.2f}s")
            print(f"Response preview: {response_text[:200]}...")
            return True
        else:
            print(f"❌ FAILED - Status: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ ERROR - {str(e)}")
        return False

def test_openai_completions():
    """Test the OpenAI-compatible completions endpoint"""
    print("\nTesting /v1/chat/completions endpoint...")
    
    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "user", "content": "Write a haiku about artificial intelligence."}
        ],
        "max_tokens": 100,
        "temperature": 0.7
    }
    
    try:
        start_time = time.time()
        response = requests.post(f"{BACKEND_URL}/v1/chat/completions", json=payload, timeout=60)
        response_time = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            print(f"✅ PASSED - Response time: {response_time:.2f}s")
            print(f"Response: {content}")
            return True
        else:
            print(f"❌ FAILED - Status: {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ ERROR - {str(e)}")
        return False

def test_streaming():
    """Test streaming completions"""
    print("\nTesting streaming completions...")
    
    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "user", "content": "Tell me a very short joke."}
        ],
        "stream": True,
        "max_tokens": 50
    }
    
    try:
        start_time = time.time()
        response = requests.post(f"{BACKEND_URL}/v1/chat/completions", json=payload, stream=True, timeout=60)
        
        if response.status_code == 200:
            chunks = []
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    if line_str.startswith('data: '):
                        data_str = line_str[6:]
                        if data_str.strip() != '[DONE]':
                            try:
                                chunk_data = json.loads(data_str)
                                delta = chunk_data.get("choices", [{}])[0].get("delta", {})
                                if "content" in delta:
                                    chunks.append(delta["content"])
                            except json.JSONDecodeError:
                                continue
            
            response_time = time.time() - start_time
            full_content = "".join(chunks)
            print(f"✅ PASSED - Response time: {response_time:.2f}s")
            print(f"Streamed content: {full_content}")
            print(f"Chunks received: {len(chunks)}")
            return True
        else:
            print(f"❌ FAILED - Status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ ERROR - {str(e)}")
        return False

def test_model_listing():
    """Test model listing"""
    print("\nTesting model listing...")
    
    try:
        response = requests.get(f"{BACKEND_URL}/v1/models", timeout=10)
        if response.status_code == 200:
            data = response.json()
            models = [model["id"] for model in data.get("data", [])]
            mistral_found = MODEL_NAME in models
            print(f"✅ Models available: {models}")
            print(f"✅ Mistral found: {mistral_found}")
            return mistral_found
        else:
            print(f"❌ FAILED - Status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ ERROR - {str(e)}")
        return False

def main():
    print(f"🚀 Testing Mistral 7B Instruct model: {MODEL_NAME}")
    print(f"Backend URL: {BACKEND_URL}")
    print("=" * 60)
    
    tests = [
        ("Model Listing", test_model_listing),
        ("Chat Endpoint", test_chat_endpoint),
        ("OpenAI Completions", test_openai_completions),
        ("Streaming", test_streaming)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🧪 Running: {test_name}")
        if test_func():
            passed += 1
        time.sleep(2)  # Small delay between tests
    
    print("\n" + "=" * 60)
    print(f"🎯 Test Results:")
    print(f"   Passed: {passed}/{total}")
    print(f"   Success Rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("🎉 All tests passed! Mistral model is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")

if __name__ == "__main__":
    main()
