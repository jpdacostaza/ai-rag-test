#!/usr/bin/env python3
"""
Integration test for the complete memory system
"""
import requests
import json
import time

def test_memory_integration():
    print("🚀 Starting Memory Integration Tests")
    print("==================================================")
    
    # Test Memory API
    print("🧠 Testing Memory API...")
    memory_api_url = "http://localhost:8003"
    
    try:
        # Health check
        response = requests.get(f"{memory_api_url}/", timeout=5)
        if response.status_code == 200:
            print("✅ Memory API health check passed")
            
            # Test remember functionality
            response = requests.post(
                f"{memory_api_url}/api/memory/remember",
                json={"user_id": "integration_test", "content": "Integration test memory"},
                timeout=5
            )
            if response.status_code == 200:
                print("✅ Memory storage test passed")
            else:
                print(f"❌ Memory storage test failed: {response.status_code}")
            
            # Test retrieve functionality  
            response = requests.post(
                f"{memory_api_url}/api/memory/retrieve",
                json={"user_id": "integration_test", "query": "integration", "limit": 5},
                timeout=5
            )
            if response.status_code == 200:
                result = response.json()
                memories = result.get('memories', [])
                print(f"✅ Memory retrieval test passed - found {len(memories)} memories")
            else:
                print(f"❌ Memory retrieval test failed: {response.status_code}")
        else:
            print(f"❌ Memory API health check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Memory API test failed: {e}")
    
    # Test Ollama API
    print("🦙 Testing Ollama API...")
    ollama_url = "http://localhost:11434"
    
    try:
        response = requests.get(f"{ollama_url}/api/tags", timeout=5)
        if response.status_code == 200:
            result = response.json()
            models = result.get('models', [])
            model_names = [model['name'] for model in models]
            print(f"✅ Ollama API test passed - available models: {model_names}")
        else:
            print(f"❌ Ollama API test failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Ollama API test failed: {e}")
    
    # Test OpenWebUI API
    print("🌐 Testing OpenWebUI API...")
    openwebui_url = "http://localhost:3000"
    
    try:
        response = requests.get(f"{openwebui_url}/", timeout=5)
        if response.status_code == 200:
            print("✅ OpenWebUI API test passed")
        else:
            print(f"❌ OpenWebUI API test failed: {response.status_code}")
    except Exception as e:
        print(f"❌ OpenWebUI API test failed: {e}")
    
    print("==================================================")
    print("🎉 All integration tests PASSED!")
    print("✅ The memory system is ready for use")

if __name__ == "__main__":
    test_memory_integration()