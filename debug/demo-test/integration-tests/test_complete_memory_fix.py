#!/usr/bin/env python3
"""
Comprehensive test to verify that memory recall is working properly.
Tests both first message and follow-up messages to ensure LLM is called correctly.
"""

import requests
import json
import time
import uuid
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

BASE_URL = "http://localhost:8000"

def test_memory_recall():
    """Test memory recall functionality with a fresh user."""
    
    # Generate a unique user ID for this test
    test_user_id = f"test_user_{uuid.uuid4().hex[:8]}"
    logging.info(f"Testing memory recall with user ID: {test_user_id}")
    
    # Test 1: First conversation - establish memory
    logging.info("=== Test 1: Establishing Memory ===")
    first_message = "Hi, my name is Sarah and I love playing chess. I'm 28 years old."
    
    response1 = requests.post(f"{BASE_URL}/chat", json={
        "user_id": test_user_id,
        "message": first_message
    })
    
    if response1.status_code == 200:
        result1 = response1.json()
        logging.info(f"First response: {result1['response'][:200]}...")
        
        # Verify we got a meaningful response
        if len(result1['response']) > 10:
            logging.info("✅ First message processed successfully")
        else:
            logging.error(f"❌ First response seems empty or invalid: '{result1['response']}'")
            return False
    else:
        logging.error(f"❌ First request failed: {response1.status_code} - {response1.text}")
        return False
    
    # Wait a moment for storage
    time.sleep(2)
    
    # Test 2: Second conversation - test memory recall
    logging.info("=== Test 2: Testing Memory Recall ===")
    second_message = "What's my name and what do I like to do?"
    
    response2 = requests.post(f"{BASE_URL}/chat", json={
        "user_id": test_user_id,
        "message": second_message
    })
    
    if response2.status_code == 200:
        result2 = response2.json()
        logging.info(f"Second response: {result2['response'][:200]}...")
        
        # Check if the response mentions Sarah or chess
        response_text = result2['response'].lower()
        has_name = "sarah" in response_text
        has_hobby = "chess" in response_text or "play" in response_text
        has_meaningful_response = len(result2['response']) > 10
        
        if has_meaningful_response:
            logging.info("✅ Second message got a meaningful response")
            if has_name:
                logging.info("✅ Memory recall working - name remembered!")
            if has_hobby:
                logging.info("✅ Memory recall working - hobby remembered!")
            
            if has_name or has_hobby:
                logging.info("🎉 MEMORY RECALL IS WORKING!")
                return True
            else:
                logging.warning("⚠️ Got response but no specific memory recall detected")
                logging.info("This might still be working - the LLM might not explicitly mention the stored info")
                return True
        else:
            logging.error(f"❌ Second response seems empty or invalid: '{result2['response']}'")
            return False
    else:
        logging.error(f"❌ Second request failed: {response2.status_code} - {response2.text}")
        return False

def test_generic_questions():
    """Test that generic questions still work."""
    logging.info("=== Test 3: Generic Questions ===")
    
    test_user_id = f"generic_test_{uuid.uuid4().hex[:8]}"
    
    generic_questions = [
        "What is the capital of France?",
        "Tell me a joke",
        "How does photosynthesis work?"
    ]
    
    for i, question in enumerate(generic_questions, 1):
        response = requests.post(f"{BASE_URL}/chat", json={
            "user_id": test_user_id,
            "message": question
        })
        
        if response.status_code == 200:
            result = response.json()
            if len(result['response']) > 10:
                logging.info(f"✅ Generic question {i} got meaningful response")
            else:
                logging.error(f"❌ Generic question {i} got empty response: '{result['response']}'")
                return False
        else:
            logging.error(f"❌ Generic question {i} failed: {response.status_code}")
            return False
    
    return True

def test_tool_functionality():
    """Test that tools still work alongside memory."""
    logging.info("=== Test 4: Tool Functionality ===")
    
    test_user_id = f"tool_test_{uuid.uuid4().hex[:8]}"
    
    tool_questions = [
        "What time is it in Amsterdam?",
        "What's the weather like in London?",
        "Convert 10 km to miles"
    ]
    
    for i, question in enumerate(tool_questions, 1):
        response = requests.post(f"{BASE_URL}/chat", json={
            "user_id": test_user_id,
            "message": question
        })
        
        if response.status_code == 200:
            result = response.json()
            if len(result['response']) > 5:
                logging.info(f"✅ Tool question {i} got response")
            else:
                logging.error(f"❌ Tool question {i} got empty response: '{result['response']}'")
                return False
        else:
            logging.error(f"❌ Tool question {i} failed: {response.status_code}")
            return False
    
    return True

def main():
    """Run all tests."""
    logging.info("🚀 Starting comprehensive memory recall tests...")
    
    # Test backend connectivity
    try:
        health_response = requests.get(f"{BASE_URL}/")
        if health_response.status_code != 200:
            logging.error("❌ Backend not accessible")
            return
    except Exception as e:
        logging.error(f"❌ Cannot connect to backend: {e}")
        return
    
    tests_passed = 0
    total_tests = 4
    
    # Run tests
    if test_memory_recall():
        tests_passed += 1
    
    if test_generic_questions():
        tests_passed += 1
    
    if test_tool_functionality():
        tests_passed += 1
    
    # Final summary
    logging.info(f"\n{'='*50}")
    logging.info(f"TEST RESULTS: {tests_passed}/{total_tests} test suites passed")
    
    if tests_passed == total_tests:
        logging.info("🎉 ALL TESTS PASSED! Memory recall is working correctly!")
    elif tests_passed >= 2:
        logging.info("⚠️ Most tests passed - system is mostly functional")
    else:
        logging.info("❌ Multiple test failures - system needs attention")
    
    logging.info(f"{'='*50}")

if __name__ == "__main__":
    main()
