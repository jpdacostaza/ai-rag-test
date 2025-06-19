#!/usr/bin/env python3
"""
Authentication Test Script
Tests if the authentication middleware is properly enforcing API key validation
"""


import requests

BASE_URL = "http://localhost:8001"
VALID_API_KEY = "f2b985dd-219f-45b1-a90e-170962cc7082"
INVALID_API_KEY = "invalid-key-12345"


def test_auth_enforcement():
    """Test authentication enforcement on protected endpoints"""

    print("🔐 Authentication Enforcement Test")
    print("=" * 50)

    # Test endpoints that should require authentication
    protected_endpoints = ["/models", "/v1/models", "/chat", "/v1/chat/completions"]

    for endpoint in protected_endpoints:
        print(f"\n📋 Testing {endpoint}")

        # Test 1: No API key
        print("   🚫 Test without API key...")
        try:
            response = requests.get(f"{BASE_URL}{endpoint}", timeout=5)
            if response.status_code == 401:
                print("   ✅ Correctly rejected (401)")
            else:
                print(f"   ❌ Should be 401, got {response.status_code}")
        except Exception as e:
            print(f"   ❌ Error: {e}")

        # Test 2: Invalid API key
        print("   🔑 Test with invalid API key...")
        try:
            headers = {"X-API-Key": INVALID_API_KEY}
            response = requests.get(f"{BASE_URL}{endpoint}", headers=headers, timeout=5)
            if response.status_code == 401:
                print("   ✅ Correctly rejected invalid key (401)")
            else:
                print(f"   ❌ Should be 401, got {response.status_code}")
        except Exception as e:
            print(f"   ❌ Error: {e}")

        # Test 3: Valid API key
        print("   ✅ Test with valid API key...")
        try:
            headers = {"X-API-Key": VALID_API_KEY}
            response = requests.get(f"{BASE_URL}{endpoint}", headers=headers, timeout=5)
            if response.status_code in [
                200,
                404,
                405,
            ]:  # 405 for POST endpoints tested with GET
                print(f"   ✅ Correctly allowed valid key ({response.status_code})")
            else:
                print(f"   ⚠️  Unexpected status: {response.status_code}")
        except Exception as e:
            print(f"   ❌ Error: {e}")


if __name__ == "__main__":
    test_auth_enforcement()
