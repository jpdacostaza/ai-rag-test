#!/usr/bin/env python3
"""
Debug memory recall issue in detail
"""

import requests
import json
import time

BASE_URL = "http://localhost:8001"

def debug_memory_recall():
    """Debug the memory recall issue step by step"""
    print("🔍 DEBUGGING MEMORY RECALL ISSUE")
    print("=" * 60)
    
    user_id = "debug_user_001"
    
    # Clear any existing cache/history first
    print("1. Starting fresh test...")
    
    # First message
    print("\n2. Sending first message...")
    first_msg = "My name is John and I live in New York"
    
    response1 = requests.post(f"{BASE_URL}/chat", json={
        "user_id": user_id,
        "message": first_msg
    })
    
    if response1.status_code == 200:
        result1 = response1.json()
        print(f"   ✅ Response: '{result1['response'][:150]}{'...' if len(result1['response']) > 150 else ''}'")
        print(f"   📏 Length: {len(result1['response'])} chars")
    else:
        print(f"   ❌ Failed: {response1.status_code} - {response1.text}")
        return
    
    # Wait a moment
    print("\n3. Waiting 3 seconds...")
    time.sleep(3)
    
    # Second message - test memory recall
    print("\n4. Sending follow-up message...")
    second_msg = "What is my name and where do I live?"
    
    response2 = requests.post(f"{BASE_URL}/chat", json={
        "user_id": user_id,
        "message": second_msg
    })
    
    if response2.status_code == 200:
        result2 = response2.json()
        print(f"   📝 Response: '{result2['response']}'")
        print(f"   📏 Length: {len(result2['response'])} chars")
        print(f"   🔍 Is empty: {len(result2['response'].strip()) == 0}")
        
        if len(result2['response'].strip()) > 0:
            print("   ✅ Memory recall working!")
        else:
            print("   ❌ Memory recall failed - empty response")
            
        # Let's try another different follow-up
        print("\n5. Trying a different follow-up...")
        third_msg = "Tell me something interesting"
        
        response3 = requests.post(f"{BASE_URL}/chat", json={
            "user_id": user_id,
            "message": third_msg
        })
        
        if response3.status_code == 200:
            result3 = response3.json()
            print(f"   📝 Response: '{result3['response']}'")
            print(f"   📏 Length: {len(result3['response'])} chars")
        else:
            print(f"   ❌ Failed: {response3.status_code}")
            
    else:
        print(f"   ❌ Failed: {response2.status_code} - {response2.text}")

def test_with_different_user():
    """Test with a completely different user"""
    print("\n\n🔍 TESTING WITH DIFFERENT USER")
    print("=" * 60)
    
    user_id = "debug_user_002"
    
    # First message
    print("1. First message...")
    response1 = requests.post(f"{BASE_URL}/chat", json={
        "user_id": user_id,
        "message": "Hello there!"
    })
    
    if response1.status_code == 200:
        result1 = response1.json()
        print(f"   ✅ Response: '{result1['response'][:100]}...'")
    
    time.sleep(2)
    
    # Second message
    print("2. Second message...")
    response2 = requests.post(f"{BASE_URL}/chat", json={
        "user_id": user_id,
        "message": "How are you today?"
    })
    
    if response2.status_code == 200:
        result2 = response2.json()
        print(f"   📝 Response: '{result2['response']}'")
        print(f"   📏 Length: {len(result2['response'])} chars")

if __name__ == "__main__":
    debug_memory_recall()
    test_with_different_user()
