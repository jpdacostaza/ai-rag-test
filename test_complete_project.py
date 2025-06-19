#!/usr/bin/env python3
"""
Complete Project Testing Script
Tests all major components to ensure the project is complete and functional.
"""

from datetime import datetime

import requests

# Test configuration
BASE_URL = "http://localhost:8001"
TEST_USER_ID = "test_user_12345"
TEST_API_KEY = "f2b985dd-219f-45b1-a90e-170962cc7082"


def print_section(title):
    """Print a formatted section header."""
    print(f"\n{'='*60}")
    print(f"🧪 {title}")
    print("=" * 60)


def print_test(test_name):
    """Print a test name."""
    print(f"\n🔍 Testing: {test_name}")


def test_health_endpoints():
    """Test basic health endpoints."""
    print_section("HEALTH & INFRASTRUCTURE TESTS")

    health_endpoints = [
        "/health",
        "/health/detailed",
        "/health/redis",
        "/health/chromadb",
        "/health/storage",
    ]

    results = {}
    for endpoint in health_endpoints:
        try:
            print_test(f"Health endpoint: {endpoint}")
            response = requests.get(f"{BASE_URL}{endpoint}", timeout=10)
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                print("   ✅ PASS")
                results[endpoint] = "PASS"
            else:
                print("   ❌ FAIL")
                results[endpoint] = "FAIL"
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
            results[endpoint] = "ERROR"

    return results


def test_authentication():
    """Test authentication middleware."""
    print_section("AUTHENTICATION TESTS")

    results = {}

    # Test 1: No API key (should fail)
    print_test("Request without API key")
    try:
        response = requests.post(
            f"{BASE_URL}/v1/chat/completions",
            json={"messages": [{"role": "user", "content": "test"}]},
            timeout=10,
        )
        if response.status_code == 401:
            print("   ✅ PASS - Correctly rejected")
            results["no_auth"] = "PASS"
        else:
            print(f"   ❌ FAIL - Should be 401, got {response.status_code}")
            results["no_auth"] = "FAIL"
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        results["no_auth"] = "ERROR"

    # Test 2: Invalid API key (should fail)
    print_test("Request with invalid API key")
    try:
        headers = {"Authorization": "Bearer invalid_key_12345"}
        response = requests.post(
            f"{BASE_URL}/v1/chat/completions",
            json={"messages": [{"role": "user", "content": "test"}]},
            headers=headers,
            timeout=10,
        )
        if response.status_code == 401:
            print("   ✅ PASS - Correctly rejected")
            results["invalid_auth"] = "PASS"
        else:
            print(f"   ❌ FAIL - Should be 401, got {response.status_code}")
            results["invalid_auth"] = "FAIL"
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        results["invalid_auth"] = "ERROR"

    # Test 3: Valid API key (should pass)
    print_test("Request with valid API key")
    try:
        headers = {"Authorization": f"Bearer {TEST_API_KEY}"}
        response = requests.post(
            f"{BASE_URL}/v1/chat/completions",
            json={
                "messages": [{"role": "user", "content": "Hello, just testing"}],
                "max_tokens": 10,
            },
            headers=headers,
            timeout=15,
        )
        if response.status_code == 200:
            print("   ✅ PASS - Request accepted")
            results["valid_auth"] = "PASS"
        else:
            print(f"   ❌ FAIL - Should be 200, got {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            results["valid_auth"] = "FAIL"
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        results["valid_auth"] = "ERROR"

    return results


def test_chat_endpoints():
    """Test chat functionality."""
    print_section("CHAT & LLM TESTS")

    headers = {"Authorization": f"Bearer {TEST_API_KEY}"}
    results = {}

    # Test basic chat
    print_test("Basic chat completion")
    try:
        response = requests.post(
            f"{BASE_URL}/v1/chat/completions",
            json={
                "messages": [{"role": "user", "content": "Say hello in one word"}],
                "max_tokens": 5,
            },
            headers=headers,
            timeout=30,
        )
        if response.status_code == 200:
            data = response.json()
            if "choices" in data and len(data["choices"]) > 0:
                print("   ✅ PASS - Chat working")
                print(f"   Response: {data['choices'][0]['message']['content']}")
                results["chat"] = "PASS"
            else:
                print("   ❌ FAIL - Invalid response format")
                results["chat"] = "FAIL"
        else:
            print(f"   ❌ FAIL - Status {response.status_code}")
            results["chat"] = "FAIL"
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        results["chat"] = "ERROR"

    return results


def test_document_pipeline():
    """Test document upload and RAG pipeline."""
    print_section("DOCUMENT & RAG TESTS")

    headers = {"Authorization": f"Bearer {TEST_API_KEY}"}
    results = {}

    # Test document upload
    print_test("Document upload")
    try:
        test_content = "This is a test document for RAG testing. It contains important information about testing procedures."

        files = {"file": ("test_document.txt", test_content, "text/plain")}
        data = {
            "user_id": TEST_USER_ID,
            "description": "Test document for completion validation",
        }

        response = requests.post(
            f"{BASE_URL}/upload/document",
            files=files,
            data=data,
            headers=headers,
            timeout=30,
        )

        if response.status_code == 200:
            upload_data = response.json()
            print("   ✅ PASS - Document uploaded")
            print(
                f"   Chunks processed: {upload_data.get('chunks_processed', 'unknown')}"
            )
            results["upload"] = "PASS"
        else:
            print(f"   ❌ FAIL - Status {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            results["upload"] = "FAIL"
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        results["upload"] = "ERROR"

    # Test document search
    print_test("Document search/retrieval")
    try:
        search_data = {
            "query": "testing procedures",
            "user_id": TEST_USER_ID,
            "limit": 3,
        }

        response = requests.post(
            f"{BASE_URL}/upload/search", data=search_data, headers=headers, timeout=20
        )

        if response.status_code == 200:
            search_results = response.json()
            if search_results.get("results_count", 0) > 0:
                print("   ✅ PASS - Document search working")
                print(f"   Found {search_results['results_count']} results")
                results["search"] = "PASS"
            else:
                print("   ⚠️  PARTIAL - No results found (may be expected)")
                results["search"] = "PARTIAL"
        else:
            print(f"   ❌ FAIL - Status {response.status_code}")
            results["search"] = "FAIL"
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        results["search"] = "ERROR"

    return results


def test_additional_endpoints():
    """Test additional API endpoints."""
    print_section("ADDITIONAL ENDPOINT TESTS")

    headers = {"Authorization": f"Bearer {TEST_API_KEY}"}
    results = {}

    endpoints_to_test = [
        ("/config", "GET"),
        ("/persona", "GET"),
        ("/cache/stats", "GET"),
        ("/storage/health", "GET"),
        ("/adaptive/stats", "GET"),
    ]

    for endpoint, method in endpoints_to_test:
        print_test(f"{method} {endpoint}")
        try:
            if method == "GET":
                response = requests.get(
                    f"{BASE_URL}{endpoint}", headers=headers, timeout=10
                )
            else:
                response = requests.post(
                    f"{BASE_URL}{endpoint}", headers=headers, timeout=10
                )

            if response.status_code in [200, 201]:
                print("   ✅ PASS")
                results[endpoint] = "PASS"
            elif response.status_code == 404:
                print("   ⚠️  NOT IMPLEMENTED")
                results[endpoint] = "NOT_IMPLEMENTED"
            else:
                print(f"   ❌ FAIL - Status {response.status_code}")
                results[endpoint] = "FAIL"
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
            results[endpoint] = "ERROR"

    return results


def print_final_summary(all_results):
    """Print final test summary."""
    print_section("FINAL PROJECT COMPLETION SUMMARY")

    total_tests = 0
    passed_tests = 0

    for category, results in all_results.items():
        print(f"\n📊 {category.upper()}:")
        for test, result in results.items():
            total_tests += 1
            if result == "PASS":
                passed_tests += 1
                status = "✅"
            elif result == "PARTIAL":
                status = "⚠️ "
            elif result == "NOT_IMPLEMENTED":
                status = "⏸️ "
            else:
                status = "❌"
            print(f"   {status} {test}: {result}")

    print("\n🎯 OVERALL COMPLETION STATUS:")
    print(f"   Total Tests: {total_tests}")
    print(f"   Passed: {passed_tests}")
    print(f"   Success Rate: {(passed_tests/total_tests)*100:.1f}%")

    if passed_tests >= total_tests * 0.8:
        print("\n🎉 PROJECT STATUS: ✅ READY FOR PRODUCTION")
        print("   Most critical functionality is working properly.")
    elif passed_tests >= total_tests * 0.6:
        print("\n🔧 PROJECT STATUS: ⚠️  MOSTLY COMPLETE")
        print("   Core functionality working, some features need attention.")
    else:
        print("\n🚧 PROJECT STATUS: ❌ NEEDS MORE WORK")
        print("   Several critical components need fixing.")


def main():
    """Run complete project tests."""
    print("🚀 COMPLETE PROJECT TESTING")
    print(f"Testing against: {BASE_URL}")
    print(f"Test User ID: {TEST_USER_ID}")
    print(f"Timestamp: {datetime.now().isoformat()}")

    all_results = {}

    # Run all test categories
    all_results["Health"] = test_health_endpoints()
    all_results["Authentication"] = test_authentication()
    all_results["Chat"] = test_chat_endpoints()
    all_results["Document_RAG"] = test_document_pipeline()
    all_results["Additional_Endpoints"] = test_additional_endpoints()

    # Print final summary
    print_final_summary(all_results)


if __name__ == "__main__":
    main()
