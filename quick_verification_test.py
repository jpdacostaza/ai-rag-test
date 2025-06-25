#!/usr/bin/env python3
"""
Quick Verification Test - Post-Cleanup
=====================================

Simple test script to verify all critical endpoints are working
after the codebase cleanup.
"""

import requests
import json
import time
from datetime import datetime

def test_endpoint(name, url, method="GET", data=None, expected_status=200):
    """Test a single endpoint with proper connection handling."""
    try:
        session = requests.Session()
        session.headers.update({'Connection': 'close'})
        
        if method == "GET":
            response = session.get(url, timeout=30)
        elif method == "POST":
            response = session.post(url, json=data, timeout=30)
        
        success = response.status_code == expected_status
        
        print(f"{'✅' if success else '❌'} {name}: {response.status_code}")
        if not success:
            print(f"   Expected: {expected_status}, Got: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
        
        session.close()
        return success
        
    except Exception as e:
        print(f"❌ {name}: ERROR - {str(e)}")
        return False

def main():
    print("🧪 QUICK VERIFICATION TEST")
    print("=" * 50)
    print(f"Test started at: {datetime.now()}")
    print()
    
    base_url = "http://localhost:9099"
    tests_passed = 0
    total_tests = 0
    
    # Test basic endpoints
    endpoints = [
        ("Root Endpoint", f"{base_url}/"),
        ("Health Check", f"{base_url}/health"),
        ("Models List", f"{base_url}/v1/models"),
        ("Pipeline List", f"{base_url}/api/v1/pipelines/list"),
    ]
    
    for name, url in endpoints:
        total_tests += 1
        if test_endpoint(name, url):
            tests_passed += 1
        time.sleep(0.5)  # Small delay between requests
    
    # Test chat endpoint
    total_tests += 1
    chat_data = {
        "user_id": "test_user",
        "message": "Hello! Can you say 'Test successful' to verify the connection?"
    }
    if test_endpoint("Chat Completion", f"{base_url}/chat", "POST", chat_data):
        tests_passed += 1
    
    print()
    print("=" * 50)
    print(f"📊 RESULTS: {tests_passed}/{total_tests} tests passed")
    print(f"Success Rate: {(tests_passed/total_tests)*100:.1f}%")
    
    if tests_passed == total_tests:
        print("🎉 ALL TESTS PASSED! System is fully operational.")
        return True
    else:
        print("⚠️ Some tests failed. Check the output above.")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
