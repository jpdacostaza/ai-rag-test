#!/usr/bin/env python3
"""
Test explicit memory management (remember/forget commands)
"""
import requests
import json
import time

MEMORY_API_URL = "http://localhost:8003"

def test_explicit_memory():
    print("🧪 Testing Explicit Memory Management")
    
    # Test 1: Explicit remember command
    print("\n1. Testing explicit remember...")
    remember_payload = {
        "user_id": "anonymous",
        "content": "I love pizza, especially pepperoni pizza on Fridays",
        "source": "test_explicit",
        "conversation_id": "test-explicit"
    }
    
    response = requests.post(
        f"{MEMORY_API_URL}/api/memory/remember",
        json=remember_payload
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"   ✅ Remember successful: {result.get('message')}")
        print(f"   📊 Total memories: {result.get('total_memories', {}).get('total', 'unknown')}")
    else:
        print(f"   ❌ Remember failed: {response.status_code}")
        print(f"   Response: {response.text}")
        return
    
    # Wait a moment
    time.sleep(1)
    
    # Test 2: Query to see if memory was stored
    print("\n2. Checking if memory was stored...")
    response = requests.post(
        f"{MEMORY_API_URL}/api/memory/retrieve",
        json={
            "user_id": "anonymous", 
            "query": "pizza",
            "threshold": 0.05,
            "limit": 10
        }
    )
    
    if response.status_code == 200:
        result = response.json()
        memories = result.get('memories', [])
        print(f"   Found {len(memories)} pizza memories:")
        for memory in memories:
            print(f"   • {memory['content'][:50]}...")
    else:
        print(f"   ❌ Retrieval failed: {response.status_code}")
        return
    
    # Test 3: Explicit forget command
    print("\n3. Testing explicit forget...")
    forget_payload = {
        "user_id": "anonymous",
        "forget_query": "pizza",
        "source": "test_explicit"
    }
    
    response = requests.post(
        f"{MEMORY_API_URL}/api/memory/forget",
        json=forget_payload
    )
    
    if response.status_code == 200:
        result = response.json()
        removed_count = result.get('removed_count', 0)
        print(f"   ✅ Forget successful: deleted {removed_count} memories")
    else:
        print(f"   ❌ Forget failed: {response.status_code}")
        return
    
    # Test 4: Verify memories were deleted
    print("\n4. Checking if memories were deleted...")
    response = requests.post(
        f"{MEMORY_API_URL}/api/memory/retrieve",
        json={
            "user_id": "anonymous", 
            "query": "pizza",
            "threshold": 0.05,
            "limit": 10
        }
    )
    
    if response.status_code == 200:
        result = response.json()
        memories = result.get('memories', [])
        print(f"   Found {len(memories)} pizza memories after deletion")
        
        if len(memories) == 0:
            print("   🎉 SUCCESS: Pizza memories were successfully deleted!")
        else:
            print("   ⚠️ WARNING: Some pizza memories still exist")
            for memory in memories:
                print(f"   • {memory['content'][:50]}...")
    else:
        print(f"   ❌ Verification failed: {response.status_code}")

if __name__ == "__main__":
    test_explicit_memory()
