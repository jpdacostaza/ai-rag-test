#!/usr/bin/env python3
"""
Test to add memory for a user and then verify memory pipeline works
"""

import requests
import json

def test_memory_pipeline_flow():
    """Test the complete memory pipeline flow"""
    
    base_url = "http://localhost:8001"
    api_key = "f2b985dd-219f-45b1-a90e-170962cc7082"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    
    user_id = "test_user_123"
    
    print("=== Memory Pipeline Flow Test ===")
    
    # Step 1: Add some memory for the user
    print(f"\n1. Adding memory for user: {user_id}")
    
    # Test if we have an add memory endpoint
    memory_data = {
        "user_id": user_id,
        "content": "My name is John and I love Python programming",
        "memory_type": "personal_info"
    }
    
    # Try to find an add memory endpoint
    endpoints_to_try = [
        "/api/memory/add",
        "/api/memory/store", 
        "/api/learning/process_interaction"
    ]
    
    stored = False
    for endpoint in endpoints_to_try:
        try:
            print(f"   Trying {endpoint}...")
            response = requests.post(f"{base_url}{endpoint}", json=memory_data, headers=headers, timeout=10)
            if response.status_code == 200:
                print(f"   ✅ Memory stored via {endpoint}")
                stored = True
                break
            else:
                print(f"   ❌ {endpoint} failed: {response.status_code}")
        except Exception as e:
            print(f"   ❌ {endpoint} error: {e}")
    
    if not stored:
        # Try the learning endpoint with proper format
        print("   Trying learning endpoint with interaction format...")
        try:
            interaction_data = {
                "user_id": user_id,
                "conversation_id": "test_conv_123",
                "user_message": "My name is John and I love Python programming",
                "assistant_response": "Nice to meet you John! I'll remember that you love Python programming."
            }
            
            response = requests.post(f"{base_url}/api/learning/process_interaction", 
                                   json=interaction_data, headers=headers, timeout=10)
            if response.status_code == 200:
                print("   ✅ Memory stored via learning endpoint")
                stored = True
            else:
                print(f"   ❌ Learning endpoint failed: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"   ❌ Learning endpoint error: {e}")
    
    if not stored:
        print("   ⚠️ Could not store memory, pipeline test may not work correctly")
        return False
    
    # Step 2: Retrieve memory
    print(f"\n2. Retrieving memory for user: {user_id}")
    
    try:
        retrieve_data = {
            "user_id": user_id,
            "query": "what is my name",
            "limit": 3,
            "threshold": 0.5
        }
        
        response = requests.post(f"{base_url}/api/memory/retrieve", 
                               json=retrieve_data, headers=headers, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            memories = result.get("memories", [])
            print(f"   ✅ Retrieved {len(memories)} memories")
            
            if memories:
                for i, memory in enumerate(memories, 1):
                    content = memory.get("content", memory.get("text", ""))
                    print(f"     {i}. {content[:100]}...")
                return True
            else:
                print("   ⚠️ No memories found")
                return False
        else:
            print(f"   ❌ Memory retrieval failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Memory retrieval error: {e}")
        return False

if __name__ == "__main__":
    success = test_memory_pipeline_flow()
    print(f"\n=== Test Result: {'PASS' if success else 'FAIL'} ===")
