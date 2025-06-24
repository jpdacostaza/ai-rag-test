#!/usr/bin/env python3
"""
Direct test of the call_llm function to debug the issue.
"""

import json
import requests
import time

BACKEND_URL = "http://localhost:8001"
OLLAMA_URL = "http://localhost:11434"
MODEL_NAME = "mistral:7b-instruct-v0.3-q4_k_m"

def test_direct_ollama_with_chat_api():
    """Test Ollama directly using the chat API to see what should work"""
    print("🔍 Testing Ollama chat API directly...")
    
    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "user", "content": "Say 'DIRECT OLLAMA WORKING' and nothing else."}
        ],
        "stream": False
    }
    
    try:
        response = requests.post(f"{OLLAMA_URL}/api/chat", json=payload, timeout=30)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            content = data.get("message", {}).get("content", "")
            print(f"✅ Direct Ollama response: '{content}'")
            return content
        else:
            print(f"❌ Direct Ollama failed: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Direct Ollama error: {e}")
        return None

def test_backend_openai_with_default_model():
    """Test the backend with the default model to see if it works"""
    print("\n🔍 Testing backend with default model (llama3.2:3b)...")
    
    payload = {
        "model": "llama3.2:3b",  # Use default model
        "messages": [
            {"role": "user", "content": "Say 'DEFAULT MODEL WORKING' and nothing else."}
        ],
        "max_tokens": 50
    }
    
    try:
        response = requests.post(f"{BACKEND_URL}/v1/chat/completions", json=payload, timeout=60)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            print(f"✅ Backend default model response: '{content}'")
            return content
        else:
            print(f"❌ Backend default model failed: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Backend default model error: {e}")
        return None

def test_backend_openai_with_mistral():
    """Test the backend with Mistral model"""
    print(f"\n🔍 Testing backend with Mistral model ({MODEL_NAME})...")
    
    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "user", "content": "Say 'MISTRAL MODEL WORKING' and nothing else."}
        ],
        "max_tokens": 50
    }
    
    try:
        response = requests.post(f"{BACKEND_URL}/v1/chat/completions", json=payload, timeout=60)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            print(f"Content: '{content}'")
            print(f"Content length: {len(content)}")
            if content:
                print("✅ Backend Mistral response received")
            else:
                print("❌ Backend Mistral response is empty")
            return content
        else:
            print(f"❌ Backend Mistral failed: {response.text}")
            return None
    except Exception as e:
        print(f"❌ Backend Mistral error: {e}")
        return None

def compare_models():
    """Compare responses from different models"""
    print("\n🔍 Comparing model responses...")
    
    test_message = "What is 2+2? Answer with just the number."
    
    # Test with default model
    payload_default = {
        "model": "llama3.2:3b",
        "messages": [{"role": "user", "content": test_message}],
        "max_tokens": 10
    }
    
    # Test with Mistral
    payload_mistral = {
        "model": MODEL_NAME,
        "messages": [{"role": "user", "content": test_message}],
        "max_tokens": 10
    }
    
    print(f"\n📤 Testing default model...")
    try:
        response = requests.post(f"{BACKEND_URL}/v1/chat/completions", json=payload_default, timeout=30)
        if response.status_code == 200:
            data = response.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            print(f"Default model response: '{content}'")
        else:
            print(f"Default model failed: {response.status_code}")
    except Exception as e:
        print(f"Default model error: {e}")
    
    print(f"\n📤 Testing Mistral model...")
    try:
        response = requests.post(f"{BACKEND_URL}/v1/chat/completions", json=payload_mistral, timeout=30)
        if response.status_code == 200:
            data = response.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            print(f"Mistral model response: '{content}'")
        else:
            print(f"Mistral model failed: {response.status_code}")
    except Exception as e:
        print(f"Mistral model error: {e}")

if __name__ == "__main__":
    print("🚀 Debugging Model Selection in OpenWebUI")
    print("=" * 50)
    
    # Test direct Ollama connection
    direct_result = test_direct_ollama_with_chat_api()
    time.sleep(2)
    
    # Test backend with default model
    default_result = test_backend_openai_with_default_model()
    time.sleep(2)
    
    # Test backend with Mistral
    mistral_result = test_backend_openai_with_mistral()
    time.sleep(2)
    
    # Compare models
    compare_models()
    
    print("\n" + "=" * 50)
    print("🎯 Summary:")
    print(f"Direct Ollama: {'✅ Working' if direct_result else '❌ Failed'}")
    print(f"Backend Default: {'✅ Working' if default_result else '❌ Failed'}")
    print(f"Backend Mistral: {'✅ Working' if mistral_result else '❌ Failed'}")
    
    if direct_result and not mistral_result:
        print("\n💡 Issue: Ollama works directly but backend doesn't use Mistral properly")
    elif default_result and not mistral_result:
        print("\n💡 Issue: Default model works but Mistral model doesn't")
    elif not default_result and not mistral_result:
        print("\n💡 Issue: Backend /v1/chat/completions endpoint is broken for all models")
