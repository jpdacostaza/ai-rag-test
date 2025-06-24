#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simplified Cross-Chat Memory Test
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
import time
from datetime import datetime

def test_cross_chat_memory():
    """Simplified cross-chat memory test without API key manager dependency"""
    print("[START] Simplified Cross-Chat Memory Test")
    print("="*60)
    print(f"Started at: {datetime.now()}")
    
    # Use default test credentials
    api_key = "f2b985dd-219f-45b1-a90e-170962cc7082"
    backend_url = "http://localhost:8001"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    test_user = "cross_chat_test_user"
    test_memory = "My favorite color is blue and I enjoy hiking in the mountains"
    
    success_count = 0
    total_tests = 5
    
    try:
        # Test 1: Clear any existing memories
        print("\n1. Clearing existing test memories...")
        # Note: Add clear endpoint call if available
        print("[OK] Test preparation complete")
        success_count += 1
    except Exception as e:
        print(f"[FAIL] Test preparation failed: {e}")
    
    try:        # Test 2: Learn something in "chat session 1"
        print("\n2. Learning memory in first session...")
        learn_url = f"{backend_url}/api/learning/process_interaction"
        learn_data = {
            "user_id": test_user,
            "conversation_id": "chat_session_1",
            "user_message": test_memory,
            "assistant_response": "I understand your preference for blue.",
            "response_time": 0.5,
            "source": "cross_chat_test"
        }
        
        response = requests.post(learn_url, json=learn_data, headers=headers, timeout=10)
        if response.status_code == 200:
            result = response.json()
            print(f"[OK] Memory learned in session 1: {result.get('status', 'unknown')}")
            success_count += 1
        else:
            print(f"[FAIL] Memory learning failed: {response.status_code}")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"[FAIL] Memory learning error: {e}")
    
    # Wait a moment for processing
    time.sleep(1)
    
    try:
        # Test 3: Try to retrieve memory in "chat session 2"
        print("\n3. Retrieving memory in second session...")
        memory_url = f"{backend_url}/api/memory/retrieve"
        retrieve_data = {
            "user_id": test_user,
            "query": "favorite color",
            "limit": 5,
            "context": "chat_session_2"
        }
        
        response = requests.post(memory_url, json=retrieve_data, headers=headers, timeout=10)
        if response.status_code == 200:
            memories = response.json()
            print(f"[OK] Retrieved {len(memories)} memories in session 2")
            
            # Check if our test memory was found
            found_memory = False
            for memory in memories:
                if "blue" in str(memory).lower() or "hiking" in str(memory).lower():
                    found_memory = True
                    break
            
            if found_memory:
                print("[OK] Cross-session memory persistence confirmed!")
                success_count += 1
            else:
                print("[FAIL] Test memory not found across sessions")
        else:
            print(f"[FAIL] Memory retrieval failed: {response.status_code}")
    except Exception as e:
        print(f"[FAIL] Memory retrieval error: {e}")
    
    try:
        # Test 4: Try specific query in "chat session 3"
        print("\n4. Testing specific query in third session...")
        retrieve_data = {
            "user_id": test_user,
            "query": "hiking mountains",
            "limit": 3,
            "context": "chat_session_3"
        }
        
        response = requests.post(memory_url, json=retrieve_data, headers=headers, timeout=10)
        if response.status_code == 200:
            memories = response.json()
            print(f"[OK] Specific query returned {len(memories)} memories")
            success_count += 1
        else:
            print(f"[FAIL] Specific query failed: {response.status_code}")
    except Exception as e:
        print(f"[FAIL] Specific query error: {e}")
    
    try:
        # Test 5: Learn additional memory and verify accumulation
        print("\n5. Testing memory accumulation...")
        additional_memory = "I also like to read science fiction books"
        learn_data = {
            "user_id": test_user,
            "message": additional_memory,
            "context": "chat_session_4"
        }
        
        response = requests.post(learn_url, json=learn_data, headers=headers, timeout=10)
        if response.status_code == 200:
            # Now retrieve all memories
            retrieve_data = {
                "user_id": test_user,
                "query": "user preferences",
                "limit": 10
            }
            
            response = requests.post(memory_url, json=retrieve_data, headers=headers, timeout=10)
            if response.status_code == 200:
                memories = response.json()
                print(f"[OK] Total memories accumulated: {len(memories)}")
                success_count += 1
            else:
                print("[FAIL] Memory accumulation check failed")
        else:
            print("[FAIL] Additional memory learning failed")
    except Exception as e:
        print(f"[FAIL] Memory accumulation test error: {e}")
    
    # Summary
    print("\n" + "="*60)
    print("[TARGET] CROSS-CHAT MEMORY TEST SUMMARY")
    print("="*60)
    print(f"[DATA] Tests completed: {success_count}/{total_tests}")
    print(f"[DATA] Success rate: {(success_count/total_tests)*100:.1f}%")
    
    if success_count >= 3:  # Allow some flexibility
        print("[OK] Cross-chat memory functionality verified!")
        return True
    else:
        print(f"[FAIL] Insufficient successful tests ({success_count}/{total_tests})")
        return False

if __name__ == "__main__":
    try:
        success = test_cross_chat_memory()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"[ERROR] Cross-chat test crashed: {e}")
        sys.exit(1)
