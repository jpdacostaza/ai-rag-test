#!/usr/bin/env python3
"""Test current authentication enforcement"""


import requests

BASE_URL = "http://localhost:8001"


def test_protected_endpoint():
    """Test that protected endpoints require authentication"""
    print("🔍 Testing authentication enforcement...")
    # Test 1: Protected endpoint without API key
    print("\n1. Testing /chat without API key (should be 401):")
    try:
        response = requests.post(
            f"{BASE_URL}/chat",
            json={"user_id": "test_user", "message": "Hello, how are you?"},
            timeout=5,
        )
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text[:200]}")

        if response.status_code == 401:
            print("   ✅ PASS: Protected endpoint correctly requires authentication")
        else:
            print("   ❌ FAIL: Protected endpoint allowed unauthorized access")
    except Exception as e:
        print(f"   Error: {e}")

    # Test 2: Health endpoint (should be allowed)
    print("\n2. Testing /health without API key (should be 200):")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text[:100]}")

        if response.status_code == 200:
            print("   ✅ PASS: Health endpoint accessible without auth")
        else:
            print("   ❌ FAIL: Health endpoint blocked")
    except Exception as e:
        print(f"   Error: {e}")
        # Test 3: Protected endpoint with invalid API key
    print("\n3. Testing /chat with invalid API key (should be 401):")
    try:
        response = requests.post(
            f"{BASE_URL}/chat",
            json={"user_id": "test_user", "message": "Hello, how are you?"},
            headers={"X-API-Key": "invalid-key"},
            timeout=5,
        )
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text[:200]}")

        if response.status_code == 401:
            print("   ✅ PASS: Protected endpoint correctly rejected invalid API key")
        else:
            print("   ❌ FAIL: Protected endpoint accepted invalid API key")
    except Exception as e:
        print(f"   Error: {e}")


if __name__ == "__main__":
    test_protected_endpoint()
