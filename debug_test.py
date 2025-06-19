#!/usr/bin/env python3
"""
Debug Test Runner
================
Debug version to troubleshoot the comprehensive test.
"""

print("🔍 Debug Test Runner Starting...")

try:
    pass

    import requests

    print("✅ All imports successful")

    class DebugTest:
        def __init__(self):
            self.base_url = "http://localhost:8001"
            self.api_key = "f2b985dd-219f-45b1-a90e-170962cc7082"
            print(f"✅ Test class initialized - URL: {self.base_url}")

        def run_debug_tests(self):
            print("🧪 Running debug tests...")

            # Test 1: Simple health check
            print("1. Health check...")
            try:
                response = requests.get(f"{self.base_url}/health/simple", timeout=5)
                print(f"   Health status: {response.status_code}")
            except Exception as e:
                print(f"   Health error: {e}")

            # Test 2: Test with authentication
            print("2. Authentication test...")
            try:
                headers = {
                    "X-API-Key": self.api_key,
                    "Content-Type": "application/json",
                }
                response = requests.get(
                    f"{self.base_url}/models", headers=headers, timeout=5
                )
                print(f"   Models status: {response.status_code}")
                if response.status_code == 200:
                    data = response.json()
                    print(f"   Found {len(data.get('data', []))} models")
            except Exception as e:
                print(f"   Models error: {e}")

            print("🏁 Debug tests completed")

    # Run the debug test
    debug_test = DebugTest()
    debug_test.run_debug_tests()

except Exception as e:
    print(f"❌ Error during debug test: {e}")
    import traceback

    traceback.print_exc()

print("👋 Debug test runner finished")
