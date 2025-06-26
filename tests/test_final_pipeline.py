#!/usr/bin/env python3
"""
Final Pipeline Integration Test
==============================

This script tests the complete OpenWebUI pipeline integration by:
1. Verifying all services are running
2. Testing the /v1/inlet endpoint (memory injection)
3. Testing the /v1/outlet endpoint (memory storage)
4. Simulating a complete OpenWebUI pipeline workflow
5. Verifying cross-chat memory persistence

Run this to verify the pipeline is ready for production.
"""
import os

import asyncio
import json
import time
import requests
from datetime import datetime
from typing import Dict, List, Optional

# Configuration
BACKEND_URL = "http://localhost:8001"
API_KEY = os.getenv("API_KEY", "default_test_key")
TEST_USER_ID = "test_pipeline_user"


def make_request(method: str, endpoint: str, data: Optional[Dict] = None, timeout: int = 30) -> Dict:
    """Make HTTP request to backend API"""
    url = f"{BACKEND_URL}{endpoint}"
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {API_KEY}"}

    try:
        if method.upper() == "GET":
            response = requests.get(url, headers=headers, timeout=timeout)
        elif method.upper() == "POST":
            response = requests.post(url, headers=headers, json=data, timeout=timeout)
        elif method.upper() == "PUT":
            response = requests.put(url, headers=headers, json=data, timeout=timeout)
        else:
            raise ValueError(f"Unsupported method: {method}")

        return {
            "status_code": response.status_code,
            "data": response.json() if response.content else {},
            "success": response.status_code < 400,
        }
    except requests.exceptions.RequestException as e:
        return {"status_code": 0, "data": {"error": str(e)}, "success": False}


def test_service_health() -> bool:
    """Test if all services are healthy"""
    print("🔍 Testing service health...")

    # Test backend
    result = make_request("GET", "/health")
    if not result["success"]:
        print(f"❌ Backend health check failed: {result['data']}")
        return False
    print(f"✅ Backend health: {result['data'].get('status', 'unknown')}")

    # Test database
    result = make_request("GET", "/health/database")
    if not result["success"]:
        print(f"❌ Database health check failed: {result['data']}")
        return False
    print(f"✅ Database health: {result['data'].get('status', 'unknown')}")

    # Test pipelines endpoint
    result = make_request("GET", "/pipelines")
    if not result["success"]:
        print(f"❌ Pipelines endpoint failed: {result['data']}")
        return False
    print(f"✅ Pipelines endpoint: Available")

    return True


def test_inlet_endpoint() -> bool:
    """Test the /v1/inlet endpoint (memory injection)"""
    print("\n🔍 Testing pipeline inlet (memory injection)...")

    # Create a mock OpenWebUI request
    request_data = {
        "user": {"id": TEST_USER_ID},
        "messages": [{"role": "user", "content": "What's my favorite color?"}],
    }

    result = make_request("POST", "/v1/inlet", request_data)
    if not result["success"]:
        print(f"❌ Inlet endpoint failed: {result['data']}")
        return False

    # Check if the response structure is correct
    response_data = result["data"]
    if "messages" not in response_data:
        print(f"❌ Inlet response missing messages: {response_data}")
        return False

    print(f"✅ Inlet endpoint working")
    print(f"   User ID: {response_data.get('user', {}).get('id', 'unknown')}")
    print(f"   Messages count: {len(response_data.get('messages', []))}")

    return True


def test_outlet_endpoint() -> bool:
    """Test the /v1/outlet endpoint (memory storage)"""
    print("\n🔍 Testing pipeline outlet (memory storage)...")

    # Create a mock conversation to store
    request_data = {
        "user": {"id": TEST_USER_ID},
        "messages": [
            {"role": "user", "content": "My favorite color is blue. Please remember this."},
            {
                "role": "assistant",
                "content": "I'll remember that your favorite color is blue! This information has been stored for future conversations.",
            },
        ],
    }

    result = make_request("POST", "/v1/outlet", request_data)
    if not result["success"]:
        print(f"❌ Outlet endpoint failed: {result['data']}")
        return False

    print(f"✅ Outlet endpoint working")
    print(f"   Stored conversation for user: {TEST_USER_ID}")

    return True


def test_memory_persistence() -> bool:
    """Test memory persistence by storing and retrieving"""
    print("\n🔍 Testing memory persistence...")

    # Wait for indexing
    print("   Waiting 3 seconds for memory indexing...")
    time.sleep(3)

    # Now test inlet again to see if memory is retrieved
    request_data = {
        "user": {"id": TEST_USER_ID},
        "messages": [{"role": "user", "content": "What's my favorite color?"}],
    }

    result = make_request("POST", "/v1/inlet", request_data)
    if not result["success"]:
        print(f"❌ Memory persistence test failed: {result['data']}")
        return False

    # Check if memory was injected into the message
    messages = result["data"].get("messages", [])
    if not messages:
        print(f"❌ No messages in response")
        return False

    user_message = messages[-1].get("content", "")
    if "blue" in user_message.lower() or "previous conversations" in user_message.lower():
        print(f"✅ Memory successfully injected!")
        print(f"   Enhanced message length: {len(user_message)} characters")
        return True
    else:
        print(f"⚠️  Memory not found in enhanced message")
        print(f"   Message: {user_message[:200]}...")
        return False


def test_cross_user_isolation() -> bool:
    """Test that user memories are properly isolated"""
    print("\n🔍 Testing cross-user memory isolation...")

    # Test with a different user
    different_user_id = "different_test_user"
    request_data = {
        "user": {"id": different_user_id},
        "messages": [{"role": "user", "content": "What's my favorite color?"}],
    }

    result = make_request("POST", "/v1/inlet", request_data)
    if not result["success"]:
        print(f"❌ Cross-user test failed: {result['data']}")
        return False

    # Check that the different user doesn't get the first user's memories
    messages = result["data"].get("messages", [])
    if not messages:
        print(f"❌ No messages in response")
        return False

    user_message = messages[-1].get("content", "")
    if "blue" not in user_message.lower():
        print(f"✅ User isolation working correctly")
        return True
    else:
        print(f"❌ Memory leak detected between users!")
        print(f"   Message: {user_message[:200]}...")
        return False


def run_complete_simulation() -> bool:
    """Run a complete OpenWebUI pipeline simulation"""
    print("\n🔍 Running complete pipeline simulation...")

    simulation_user = "simulation_user"

    # Simulate first conversation
    print("   Step 1: First conversation (learning phase)")

    # Inlet for first message (should have no memories)
    inlet_request = {
        "user": {"id": simulation_user},
        "messages": [{"role": "user", "content": "Hello! My name is Alice and I love programming in Python."}],
    }

    inlet_result = make_request("POST", "/v1/inlet", inlet_request)
    if not inlet_result["success"]:
        print(f"❌ Simulation inlet 1 failed: {inlet_result['data']}")
        return False

    # Outlet for first conversation (storing the interaction)
    outlet_request = {
        "user": {"id": simulation_user},
        "messages": [
            {"role": "user", "content": "Hello! My name is Alice and I love programming in Python."},
            {
                "role": "assistant",
                "content": "Nice to meet you, Alice! It's great to hear you love Python programming. I'll remember that about you.",
            },
        ],
    }

    outlet_result = make_request("POST", "/v1/outlet", outlet_request)
    if not outlet_result["success"]:
        print(f"❌ Simulation outlet 1 failed: {outlet_result['data']}")
        return False

    # Wait for indexing
    print("   Step 2: Waiting for memory indexing...")
    time.sleep(3)

    # Simulate second conversation (should retrieve memories)
    print("   Step 3: Second conversation (memory retrieval)")

    inlet_request2 = {
        "user": {"id": simulation_user},
        "messages": [{"role": "user", "content": "What programming language do I like?"}],
    }

    inlet_result2 = make_request("POST", "/v1/inlet", inlet_request2)
    if not inlet_result2["success"]:
        print(f"❌ Simulation inlet 2 failed: {inlet_result2['data']}")
        return False

    # Check if memory was retrieved
    messages = inlet_result2["data"].get("messages", [])
    if messages:
        enhanced_content = messages[-1].get("content", "")
        if "python" in enhanced_content.lower() or "alice" in enhanced_content.lower():
            print(f"✅ Complete simulation successful!")
            print(f"   Memory correctly retrieved in second conversation")
            return True

    print(f"⚠️  Simulation partially successful - memory not retrieved")
    return False


def main():
    """Run all pipeline integration tests"""
    print("🚀 OpenWebUI Pipeline Integration Test")
    print("=" * 50)

    tests = [
        ("Service Health", test_service_health),
        ("Inlet Endpoint", test_inlet_endpoint),
        ("Outlet Endpoint", test_outlet_endpoint),
        ("Memory Persistence", test_memory_persistence),
        ("User Isolation", test_cross_user_isolation),
        ("Complete Simulation", run_complete_simulation),
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        try:
            print(f"\n📋 Running: {test_name}")
            if test_func():
                passed += 1
                print(f"✅ {test_name}: PASSED")
            else:
                print(f"❌ {test_name}: FAILED")
        except Exception as e:
            print(f"💥 {test_name}: ERROR - {str(e)}")

    print(f"\n📊 Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! Pipeline integration is ready for production.")
        return True
    else:
        print("⚠️  Some tests failed. Please check the issues above.")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
