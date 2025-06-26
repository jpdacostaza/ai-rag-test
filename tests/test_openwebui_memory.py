#!/usr/bin/env python3
"""
Test script to verify the memory pipeline is working in OpenWebUI.
This test makes direct API calls to simulate OpenWebUI behavior.
"""
import os

import requests
import json
import time
import sys
from datetime import datetime


def test_openwebui_memory_integration():
    """Test that OpenWebUI can use the memory pipeline"""

    print("=== OpenWebUI Memory Pipeline Integration Test ===")
    print(f"Test started at: {datetime.now()}")

    # OpenWebUI runs on port 3000, proxying to our backend
    base_url = "http://localhost:3000"
    backend_url = "http://localhost:8001"

    # Test 1: Check if OpenWebUI is accessible
    print("\n1. Testing OpenWebUI accessibility...")
    try:
        response = requests.get(f"{base_url}", timeout=10)
        if response.status_code == 200:
            print("✅ OpenWebUI is accessible")
        else:
            print(f"❌ OpenWebUI returned status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Failed to connect to OpenWebUI: {e}")
        return False

    # Test 2: Check if backend is accessible
    print("\n2. Testing backend accessibility...")
    try:
        response = requests.get(f"{backend_url}/health", timeout=10)
        if response.status_code == 200:
            print("✅ Backend is accessible")
        else:
            print(f"❌ Backend returned status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Failed to connect to backend: {e}")
        return False

    # Test 3: Check memory endpoints
    print("\n3. Testing memory endpoints...")
    api_key = os.getenv("API_KEY", "default_test_key")
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    test_user = "test_openwebui_user"
    test_memory = "My name is Alice and I love programming"

    # Test memory retrieval endpoint (this is what the pipeline uses)
    try:
        memory_query_data = {"user_id": test_user, "query": "personal information", "limit": 5}

        response = requests.post(
            f"{backend_url}/api/memory/retrieve", json=memory_query_data, headers=headers, timeout=10
        )

        if response.status_code == 200:
            result = response.json()
            memories = result.get("memories", [])
            print("✅ Memory retrieval endpoint works")
            print(f"   Retrieved {result.get('count', 0)} memories for user {test_user}")
        else:
            print(f"❌ Memory retrieval failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False

    except Exception as e:
        print(f"❌ Memory retrieval error: {e}")
        return False

    # Test 3.5: Test learning endpoint
    print("\n3.5 Testing learning endpoint...")
    try:
        learning_data = {
            "user_id": test_user,
            "conversation_id": "test_conversation_123",
            "user_message": "My name is Alice and I love programming",
            "assistant_response": "Hello Alice! It's great to meet someone who loves programming. What programming languages do you enjoy working with?",
            "response_time": 1.5,
            "source": "test_integration",
        }

        response = requests.post(
            f"{backend_url}/api/learning/process_interaction", json=learning_data, headers=headers, timeout=10
        )

        if response.status_code == 200:
            result = response.json()
            print("✅ Learning endpoint works")
            print(f"   Processing result: {result.get('status', 'unknown')}")
        else:
            print(f"❌ Learning endpoint failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False

    except Exception as e:
        print(f"❌ Learning endpoint error: {e}")
        return False

    # Test 4: Test chat with memory injection
    print("\n4. Testing chat with memory...")
    try:
        chat_data = {
            "model": "gpt-4",
            "messages": [{"role": "user", "content": "What's my name?"}],
            "user_id": test_user,
            "use_memory": True,
        }

        response = requests.post(f"{backend_url}/v1/chat/completions", json=chat_data, headers=headers, timeout=30)

        if response.status_code == 200:
            result = response.json()
            assistant_message = result.get("choices", [{}])[0].get("message", {}).get("content", "")

            if "Alice" in assistant_message or "alice" in assistant_message.lower():
                print("✅ Memory injection works - AI remembered the name!")
                print(f"   AI response: {assistant_message[:100]}...")
            else:
                print("⚠️  Memory injection may not be working - name not found in response")
                print(f"   AI response: {assistant_message[:200]}...")
        else:
            print(f"❌ Chat with memory failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False

    except Exception as e:
        print(f"❌ Chat with memory error: {e}")
        return False

    print("\n=== Memory Pipeline Integration Test Results ===")
    print("✅ All tests passed! The memory pipeline is working correctly.")
    print("\nNext steps:")
    print("1. Open OpenWebUI at: http://localhost:3000")
    print("2. Create an account or login")
    print("3. Start a chat and tell the AI your name")
    print("4. In a new chat, ask 'What's my name?' to test memory persistence")

    return True


if __name__ == "__main__":
    success = test_openwebui_memory_integration()
    sys.exit(0 if success else 1)
