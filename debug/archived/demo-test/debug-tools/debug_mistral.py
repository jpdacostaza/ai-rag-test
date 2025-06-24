#!/usr/bin/env python3
"""
Debug test for Mistral 7B Instruct model to identify response issues.
"""

import json
import requests
import time

BACKEND_URL = "http://localhost:8001"
MODEL_NAME = "mistral:7b-instruct-v0.3-q4_k_m"

def debug_test():
    """Debug test to see what's happening with responses"""
    print("🔍 Debug test for Mistral model responses...")
    
    # Test 1: Simple completion
    print("\n1. Testing simple completion...")
    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "user", "content": "Say hello and introduce yourself in one sentence."}
        ],
        "max_tokens": 50
    }
    
    response = requests.post(f"{BACKEND_URL}/v1/chat/completions", json=payload, timeout=30)
    print(f"Status: {response.status_code}")
    print(f"Response headers: {dict(response.headers)}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Full response: {json.dumps(data, indent=2)}")
        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        print(f"Content: '{content}'")
        print(f"Content length: {len(content)}")
    else:
        print(f"Error response: {response.text}")
    
    # Test 2: Chat endpoint
    print("\n2. Testing chat endpoint...")
    payload = {
        "message": "What is 2+2?",
        "user_id": "debug_user"
    }
    
    response = requests.post(f"{BACKEND_URL}/chat", json=payload, timeout=30)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Chat response: {json.dumps(data, indent=2)}")
    else:
        print(f"Error response: {response.text}")
    
    # Test 3: Check if model is using Mistral specifically
    print("\n3. Testing model availability...")
    response = requests.get(f"{BACKEND_URL}/v1/models", timeout=10)
    if response.status_code == 200:
        data = response.json()
        models = [model["id"] for model in data.get("data", [])]
        print(f"Available models: {models}")
        print(f"Mistral in list: {MODEL_NAME in models}")
    
    # Test 4: Direct Ollama test
    print("\n4. Testing direct Ollama connection...")
    try:
        ollama_payload = {
            "model": MODEL_NAME,
            "prompt": "Hello, who are you?",
            "stream": False
        }
        response = requests.post("http://localhost:11434/api/generate", json=ollama_payload, timeout=30)
        print(f"Ollama status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Ollama response preview: {data.get('response', '')[:100]}...")
        else:
            print(f"Ollama error: {response.text}")
    except Exception as e:
        print(f"Ollama connection error: {e}")

if __name__ == "__main__":
    debug_test()
