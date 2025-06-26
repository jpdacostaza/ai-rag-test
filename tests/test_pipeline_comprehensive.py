"""
Comprehensive Pipeline Test
Tests the complete memory pipeline functionality end-to-end
"""

import os

import requests
import json
import time

# Configuration
BACKEND_URL = "http://localhost:8001"
API_KEY = os.getenv("API_KEY", "default_test_key")
TEST_USER_ID = "pipeline_test_user"


def test_backend_connection():
    """Test basic backend connectivity"""
    print("🔗 Testing backend connection...")
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Backend is responding")
            return True
        else:
            print(f"❌ Backend returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Backend connection failed: {e}")
        return False


def test_pipeline_discovery():
    """Test pipeline discovery endpoint"""
    print("\n🔍 Testing pipeline discovery...")
    try:
        headers = {"Authorization": f"Bearer {API_KEY}"}
        response = requests.get(f"{BACKEND_URL}/pipelines", headers=headers, timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Pipeline discovery successful: {len(data)} pipelines found")
            print(f"   Pipeline data: {json.dumps(data, indent=2)}")
            return True
        else:
            print(f"❌ Pipeline discovery failed with status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Pipeline discovery error: {e}")
        return False


def test_memory_storage():
    """Test storing memory through learning endpoint"""
    print(f"\n💾 Testing memory storage for user {TEST_USER_ID}...")
    try:
        data = {
            "user_id": TEST_USER_ID,
            "conversation_id": f"test_conv_{int(time.time())}",
            "user_message": "My name is TestUser and I love programming in Python",
            "assistant_response": "Nice to meet you, TestUser! Python is a great programming language.",
            "response_time": 1.0,
            "tools_used": [],
            "source": "pipeline_test",
        }
        headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
        response = requests.post(
            f"{BACKEND_URL}/api/learning/process_interaction", json=data, headers=headers, timeout=10
        )

        if response.status_code == 200:
            result = response.json()
            print(f"✅ Memory stored successfully: {result}")
            return True
        else:
            print(f"❌ Memory storage failed with status {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Memory storage error: {e}")
        return False


def test_memory_retrieval():
    """Test retrieving memory"""
    print(f"\n🧠 Testing memory retrieval for user {TEST_USER_ID}...")
    try:
        data = {"user_id": TEST_USER_ID, "query": "What do you know about this user?", "limit": 5, "threshold": 0.7}
        headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
        response = requests.post(f"{BACKEND_URL}/api/memory/retrieve", json=data, headers=headers, timeout=10)

        if response.status_code == 200:
            result = response.json()
            memories = result.get("memories", [])
            print(f"✅ Memory retrieval successful: {len(memories)} memories found")
            for i, memory in enumerate(memories):
                print(f"   Memory {i+1}: {memory.get('content', 'No content')[:50]}...")
            return len(memories) > 0
        else:
            print(f"❌ Memory retrieval failed with status {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Memory retrieval error: {e}")
        return False


def test_pipeline_inlet():
    """Test pipeline inlet endpoint"""
    print(f"\n⬇️ Testing pipeline inlet for user {TEST_USER_ID}...")
    try:
        data = {
            "body": {"messages": [{"role": "user", "content": "Hi, what do you remember about me?"}]},
            "user": {"id": TEST_USER_ID},
        }
        headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
        response = requests.post(
            f"{BACKEND_URL}/pipelines/memory_pipeline/inlet", json=data, headers=headers, timeout=10
        )

        if response.status_code == 200:
            result = response.json()
            print(f"✅ Pipeline inlet successful")
            print(f"   Result: {json.dumps(result, indent=2)}")

            # Check if memory was injected
            messages = result.get("messages", [])
            memory_injected = any(
                "remember" in msg.get("content", "").lower()
                or "name" in msg.get("content", "").lower()
                or "python" in msg.get("content", "").lower()
                for msg in messages
            )

            if memory_injected:
                print("✅ Memory appears to have been injected into messages")
            else:
                print("⚠️ No clear evidence of memory injection in messages")

            return True
        else:
            print(f"❌ Pipeline inlet failed with status {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Pipeline inlet error: {e}")
        return False


def test_pipeline_outlet():
    """Test pipeline outlet endpoint"""
    print(f"\n⬆️ Testing pipeline outlet for user {TEST_USER_ID}...")
    try:
        data = {
            "body": {
                "messages": [
                    {"role": "user", "content": "I also enjoy machine learning and AI development"},
                    {
                        "role": "assistant",
                        "content": "That's great! Machine learning and AI development are fascinating fields.",
                    },
                ]
            },
            "user": {"id": TEST_USER_ID},
        }
        headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
        response = requests.post(
            f"{BACKEND_URL}/pipelines/memory_pipeline/outlet", json=data, headers=headers, timeout=10
        )

        if response.status_code == 200:
            result = response.json()
            print(f"✅ Pipeline outlet successful")
            print(f"   Result: {json.dumps(result, indent=2)}")
            return True
        else:
            print(f"❌ Pipeline outlet failed with status {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Pipeline outlet error: {e}")
        return False


def run_comprehensive_test():
    """Run all tests"""
    print("🚀 Starting Comprehensive Pipeline Test")
    print("=" * 50)

    tests = [
        ("Backend Connection", test_backend_connection),
        ("Pipeline Discovery", test_pipeline_discovery),
        ("Memory Storage", test_memory_storage),
        ("Memory Retrieval", test_memory_retrieval),
        ("Pipeline Inlet", test_pipeline_inlet),
        ("Pipeline Outlet", test_pipeline_outlet),
    ]

    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()

            # Add extra delay after memory storage to allow indexing
            if test_name == "Memory Storage" and results[test_name]:
                print("   ⏳ Waiting for memory indexing...")
                time.sleep(3)

        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
            results[test_name] = False

        time.sleep(1)  # Small delay between tests

    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"   {test_name}: {status}")

    total_tests = len(results)
    passed_tests = sum(results.values())
    print(f"\nOverall: {passed_tests}/{total_tests} tests passed")

    if all(results.values()):
        print("🎉 All tests passed! Pipeline is working correctly.")
    else:
        print("⚠️ Some tests failed. Check the output above for details.")


if __name__ == "__main__":
    run_comprehensive_test()
