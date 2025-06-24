#!/usr/bin/env python3
"""
Simple test to verify which model is being used and response content.
"""

import json
import requests
import time

BACKEND_URL = "http://localhost:8001"
MODEL_NAME = "mistral:7b-instruct-v0.3-q4_k_m"

def test_model_response():
    """Test response and verify model"""
    print("🔍 Testing model response verification...")
    
    # Test with explicit model specification
    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "user", "content": "Please tell me your name and which model you are. Also say 'WORKING' at the end."}
        ],
        "max_tokens": 100
    }
    
    print(f"📤 Sending request to: /v1/chat/completions")
    print(f"📤 Payload: {json.dumps(payload, indent=2)}")
    
    start_time = time.time()
    response = requests.post(f"{BACKEND_URL}/v1/chat/completions", json=payload, timeout=120)
    response_time = time.time() - start_time
    
    print(f"\n📥 Response Status: {response.status_code}")
    print(f"📥 Response Time: {response_time:.2f}s")
    print(f"📥 Response Headers: {dict(response.headers)}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n📥 Full Response:")
        print(json.dumps(data, indent=2))
        
        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        print(f"\n📝 Content: '{content}'")
        print(f"📝 Content Length: {len(content)}")
        print(f"📝 Content Type: {type(content)}")
        
        # Check if response indicates working
        if "WORKING" in content.upper():
            print("✅ Model is responding correctly")
        elif content.strip() == "":
            print("❌ Empty response received")
        else:
            print("⚠️ Response received but doesn't contain expected content")
            
        return True
    else:
        print(f"❌ Request failed: {response.text}")
        return False

def test_chat_endpoint():
    """Test the chat endpoint"""
    print("\n🔍 Testing chat endpoint...")
    
    payload = {
        "message": "Say 'HELLO CHAT WORKING' and nothing else.",
        "user_id": "test_user_model_verification"
    }
    
    print(f"📤 Sending request to: /chat")
    print(f"📤 Payload: {json.dumps(payload, indent=2)}")
    
    start_time = time.time()
    response = requests.post(f"{BACKEND_URL}/chat", json=payload, timeout=120)
    response_time = time.time() - start_time
    
    print(f"\n📥 Response Status: {response.status_code}")
    print(f"📥 Response Time: {response_time:.2f}s")
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n📥 Full Response:")
        print(json.dumps(data, indent=2))
        
        content = data.get("response", "")
        print(f"\n📝 Content: '{content}'")
        print(f"📝 Content Length: {len(content)}")
        
        if "HELLO CHAT WORKING" in content.upper():
            print("✅ Chat endpoint is working correctly")
        elif content.strip() == "":
            print("❌ Empty response from chat endpoint")
        else:
            print("⚠️ Chat response received but doesn't contain expected content")
            
        return True
    else:
        print(f"❌ Chat request failed: {response.text}")
        return False

if __name__ == "__main__":
    print("🚀 Model Response Verification Test")
    print("=" * 50)
    
    test_model_response()
    time.sleep(2)
    test_chat_endpoint()
