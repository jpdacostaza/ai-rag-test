#!/usr/bin/env python3
"""
Test script to verify memory integration is working properly.
"""

import requests
import json
import time

# Configuration
MEMORY_API_URL = "http://localhost:8001"
OLLAMA_API_URL = "http://localhost:11434"
OPENWEBUI_URL = "http://localhost:3000"

def test_memory_api():
    """Test memory API endpoints."""
    print("🧠 Testing Memory API...")
    
    try:
        # Test health endpoint
        response = requests.get(f"{MEMORY_API_URL}/health")
        if response.status_code == 200:
            print("✅ Memory API health check passed")
        else:
            print(f"❌ Memory API health check failed: {response.status_code}")
            return False
        
        # Test memory storage via learning API
        test_user = "test_integration_user"
        test_interaction = {
            "user_id": test_user,
            "conversation_id": "test_conversation",
            "user_message": "Test message for integration testing",
            "assistant_response": "This is a test response",
            "source": "integration_test"
        }
        
        response = requests.post(f"{MEMORY_API_URL}/api/learning/process_interaction", json=test_interaction)
        if response.status_code == 200:
            print("✅ Memory storage test passed")
        else:
            print(f"❌ Memory storage test failed: {response.status_code} - {response.text}")
            return False
        
        # Test memory retrieval
        memory_query = {
            "user_id": test_user,
            "query": "integration testing",
            "limit": 3
        }
        response = requests.post(f"{MEMORY_API_URL}/api/memory/retrieve", json=memory_query)
        if response.status_code == 200:
            result = response.json()
            memories = result.get("memories", [])
            print(f"✅ Memory retrieval test passed - found {len(memories)} memories")
        else:
            print(f"❌ Memory retrieval test failed: {response.status_code} - {response.text}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Memory API test failed with exception: {e}")
        return False

def test_ollama_api():
    """Test Ollama API."""
    print("🦙 Testing Ollama API...")
    
    try:
        # Test model list
        response = requests.get(f"{OLLAMA_API_URL}/api/tags")
        if response.status_code == 200:
            models = response.json()
            model_names = [model['name'] for model in models.get('models', [])]
            print(f"✅ Ollama API test passed - available models: {model_names}")
            return len(model_names) > 0
        else:
            print(f"❌ Ollama API test failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Ollama API test failed with exception: {e}")
        return False

def test_openwebui_api():
    """Test OpenWebUI API."""
    print("🌐 Testing OpenWebUI API...")
    
    try:
        # Test config endpoint
        response = requests.get(f"{OPENWEBUI_URL}/api/config")
        if response.status_code == 200:
            print("✅ OpenWebUI API test passed")
            return True
        else:
            print(f"❌ OpenWebUI API test failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ OpenWebUI API test failed with exception: {e}")
        return False

def main():
    """Run all integration tests."""
    print("🚀 Starting Memory Integration Tests")
    print("=" * 50)
    
    all_tests_passed = True
    
    # Test each component
    all_tests_passed &= test_memory_api()
    all_tests_passed &= test_ollama_api()
    all_tests_passed &= test_openwebui_api()
    
    print("\n" + "=" * 50)
    if all_tests_passed:
        print("🎉 All integration tests PASSED!")
        print("✅ The memory system is ready for use")
    else:
        print("❌ Some integration tests FAILED!")
        print("🔧 Please check the logs and fix any issues")
    
    return all_tests_passed

if __name__ == "__main__":
    main()
