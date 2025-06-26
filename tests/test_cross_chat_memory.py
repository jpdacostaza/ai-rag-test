#!/usr/bin/env python3

"""
Cross-Chat Memory Test
Tests the persistent memory functionality across different chat sessions
"""
import os

import requests
import json
import time

# Configuration
BACKEND_URL = "http://localhost:8001"
API_KEY = os.getenv("API_KEY", "default_test_key")
TEST_USER_ID = "test_user_123"


def test_memory_storage():
    """Test storing user information"""
    print("🧪 Testing memory storage...")

    # Store user information
    interaction_data = {
        "user_id": TEST_USER_ID,
        "conversation_id": f"global_{TEST_USER_ID}",
        "user_message": "My name is Alice and I work as a software engineer at TechCorp. I love Python programming.",
        "context": {"type": "user_profile", "filter": "cross_chat_memory_filter", "persistent": True},
    }

    response = requests.post(
        f"{BACKEND_URL}/api/learning/process_interaction",
        json=interaction_data,
        headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
        timeout=15,
    )

    print(f"Storage response: {response.status_code}")
    if response.status_code == 200:
        print("✅ Successfully stored user information")
        return True
    else:
        print(f"❌ Failed to store user information: {response.text}")
        return False


def test_memory_retrieval():
    """Test retrieving user information"""
    print("\n🔍 Testing memory retrieval...")

    # Retrieve memories
    query_data = {"user_id": TEST_USER_ID, "query": "What do you know about me?", "limit": 5, "global_search": True}

    response = requests.post(
        f"{BACKEND_URL}/api/memory/retrieve",
        json=query_data,
        headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
        timeout=15,
    )

    print(f"Retrieval response: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        memories = data.get("memories", [])
        print(f"✅ Retrieved {len(memories)} memories")

        for i, memory in enumerate(memories, 1):
            content = memory.get("content", "")
            print(f"  {i}. {content[:100]}{'...' if len(content) > 100 else ''}")

        return len(memories) > 0
    else:
        print(f"❌ Failed to retrieve memories: {response.text}")
        return False


def test_cross_chat_scenario():
    """Test the cross-chat memory scenario"""
    print("\n🔄 Testing cross-chat memory scenario...")

    # Simulate first chat - user introduces themselves
    print("1. Simulating first chat - user introduction...")
    first_chat_data = {
        "user_id": TEST_USER_ID,
        "conversation_id": f"global_{TEST_USER_ID}",
        "user_message": "Hi! My name is Bob and I'm learning about AI. I'm particularly interested in machine learning.",
        "context": {"original_chat_id": "chat_001", "filter": "cross_chat_memory_filter", "global_memory": True},
    }

    response1 = requests.post(
        f"{BACKEND_URL}/api/learning/process_interaction",
        json=first_chat_data,
        headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
        timeout=15,
    )

    print(f"First chat storage: {response1.status_code}")

    # Wait a moment for indexing
    time.sleep(2)

    # Simulate second chat - new conversation, should remember user
    print("2. Simulating second chat - should remember user...")
    memory_query = {
        "user_id": TEST_USER_ID,
        "query": "Hello, can you help me with something?",
        "limit": 3,
        "global_search": True,
    }

    response2 = requests.post(
        f"{BACKEND_URL}/api/memory/retrieve",
        json=memory_query,
        headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
        timeout=15,
    )

    print(f"Second chat memory retrieval: {response2.status_code}")
    if response2.status_code == 200:
        data = response2.json()
        memories = data.get("memories", [])
        print(f"✅ Cross-chat memory working! Retrieved {len(memories)} memories")

        # Check if the user's name and interests are remembered
        all_content = " ".join([m.get("content", "") for m in memories]).lower()
        name_remembered = "bob" in all_content
        interest_remembered = any(word in all_content for word in ["ai", "machine learning", "learning"])

        print(f"  Name remembered: {'✅' if name_remembered else '❌'}")
        print(f"  Interests remembered: {'✅' if interest_remembered else '❌'}")

        return name_remembered or interest_remembered
    else:
        print(f"❌ Cross-chat memory failed: {response2.text}")
        return False


def test_backend_health():
    """Test if backend is healthy"""
    print("🏥 Testing backend health...")

    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=10)
        if response.status_code == 200:
            print("✅ Backend is healthy")
            return True
        else:
            print(f"❌ Backend health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Backend health check error: {e}")
        return False


def main():
    """Run all tests"""
    print("🚀 Starting Cross-Chat Memory Tests")
    print("=" * 50)

    # Test backend health first
    if not test_backend_health():
        print("❌ Backend is not healthy, stopping tests")
        return False

    # Run memory tests
    tests = [
        ("Memory Storage", test_memory_storage),
        ("Memory Retrieval", test_memory_retrieval),
        ("Cross-Chat Scenario", test_cross_chat_scenario),
    ]

    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with error: {e}")
            results.append((test_name, False))

    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")

    passed = 0
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {test_name}: {status}")
        if result:
            passed += 1

    print(f"\nOverall: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! Cross-chat memory is working correctly.")
        return True
    else:
        print("⚠️  Some tests failed. Check the logs above for details.")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
