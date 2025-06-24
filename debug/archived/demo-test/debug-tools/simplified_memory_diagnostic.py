#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simplified Memory Diagnostic Tool
Windows-compatible debug tool with minimal dependencies
"""
import sys
import os

# Set UTF-8 encoding for Windows compatibility
if sys.platform.startswith('win'):
    import io
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
    except AttributeError:
        pass  # Already wrapped or not available

import requests
import json
from datetime import datetime

def test_memory_diagnostic():
    """Simplified memory diagnostic test without API key manager dependency"""
    print("[START] Simplified Memory Diagnostic Tool")
    print("="*60)
    print(f"Started at: {datetime.now()}")
    
    # Use default test credentials
    api_key = "f2b985dd-219f-45b1-a90e-170962cc7082"
    base_url = "http://localhost:3000"
    backend_url = "http://localhost:8001"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    success_count = 0
    total_tests = 4
    
    try:
        # Test 1: Check OpenWebUI accessibility
        print("\n1. Testing OpenWebUI accessibility...")
        response = requests.get(f"{base_url}/", timeout=10)
        if response.status_code == 200:
            print("[OK] OpenWebUI is accessible")
            success_count += 1
        else:
            print(f"[FAIL] OpenWebUI returned status {response.status_code}")
    except Exception as e:
        print(f"[FAIL] OpenWebUI connection failed: {e}")
    
    try:
        # Test 2: Check Backend accessibility
        print("\n2. Testing backend accessibility...")
        response = requests.get(f"{backend_url}/health", timeout=10)
        if response.status_code == 200:
            print("[OK] Backend is accessible")
            success_count += 1
        else:
            print(f"[FAIL] Backend returned status {response.status_code}")
    except Exception as e:
        print(f"[FAIL] Backend connection failed: {e}")
    
    try:
        # Test 3: Test memory retrieval endpoint
        print("\n3. Testing memory retrieval...")
        test_user = "diagnostic_test_user"
        memory_url = f"{backend_url}/api/memory/retrieve"
        data = {"user_id": test_user, "query": "test query", "limit": 5}
        
        response = requests.post(memory_url, json=data, headers=headers, timeout=10)
        if response.status_code == 200:
            memories = response.json()
            print(f"[OK] Memory retrieval works - retrieved {len(memories)} memories")
            success_count += 1
        else:
            print(f"[FAIL] Memory retrieval failed: {response.status_code}")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"[FAIL] Memory retrieval error: {e}")
    
    try:        # Test 4: Test memory learning endpoint
        print("\n4. Testing memory learning...")
        learn_url = f"{backend_url}/api/learning/process_interaction"
        learn_data = {
            "user_id": test_user,
            "conversation_id": "diagnostic_test_123",
            "user_message": "This is a diagnostic test message for memory learning",
            "assistant_response": "I understand this is a diagnostic test.",
            "response_time": 0.5,
            "source": "diagnostic"
        }
        
        response = requests.post(learn_url, json=learn_data, headers=headers, timeout=10)
        if response.status_code == 200:
            result = response.json()
            print(f"[OK] Memory learning works - result: {result.get('status', 'unknown')}")
            success_count += 1
        else:
            print(f"[FAIL] Memory learning failed: {response.status_code}")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"[FAIL] Memory learning error: {e}")
    
    # Summary
    print("\n" + "="*60)
    print("[TARGET] MEMORY DIAGNOSTIC SUMMARY")
    print("="*60)
    print(f"[DATA] Tests completed: {success_count}/{total_tests}")
    print(f"[DATA] Success rate: {(success_count/total_tests)*100:.1f}%")
    
    if success_count == total_tests:
        print("[OK] All memory diagnostic tests passed!")
        return True
    else:
        print(f"[FAIL] {total_tests - success_count} tests failed")
        return False

if __name__ == "__main__":
    try:
        success = test_memory_diagnostic()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"[ERROR] Diagnostic tool crashed: {e}")
        sys.exit(1)
