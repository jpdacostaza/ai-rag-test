#!/usr/bin/env python3
"""
Comprehensive test for explicit memory commands
"""
import requests
import json
import time

MEMORY_API_URL = "http://localhost:8003"

def test_complete_explicit_memory():
    print("🧪 Comprehensive Explicit Memory Test")
    print("=" * 50)
    
    # Test data
    user_id = "test_user_comprehensive"
    
    print(f"\n📋 Testing with user: {user_id}")
    
    # Test 1: Multiple explicit remember commands
    print("\n1. Testing multiple remember commands...")
    memories_to_store = [
        "I love playing guitar in my free time",
        "I work as a data scientist at a tech company",
        "My favorite programming language is Python",
        "I live in Seattle and enjoy hiking on weekends",
        "I have a cat named Whiskers"
    ]
    
    for i, memory in enumerate(memories_to_store, 1):
        print(f"   {i}. Storing: {memory[:50]}...")
        response = requests.post(
            f"{MEMORY_API_URL}/api/memory/remember",
            json={
                "user_id": user_id,
                "content": memory,
                "source": "comprehensive_test"
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"      ✅ Stored successfully (Total: {result['total_memories']['total']})")
        else:
            print(f"      ❌ Failed: {response.status_code}")
    
    # Wait for storage
    time.sleep(1)
    
    # Test 2: Query for different types of memories
    print("\n2. Testing memory retrieval...")
    test_queries = [
        "guitar",
        "work",
        "programming",
        "Seattle",
        "cat"
    ]
    
    for query in test_queries:
        print(f"   Querying: {query}...")
        response = requests.post(
            f"{MEMORY_API_URL}/api/memory/retrieve",
            json={
                "user_id": user_id,
                "query": query,
                "threshold": 0.05,
                "limit": 10
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            count = len(result.get('memories', []))
            print(f"      ✅ Found {count} memories")
            if count > 0:
                print(f"         Example: {result['memories'][0]['content'][:60]}...")
        else:
            print(f"      ❌ Query failed: {response.status_code}")
    
    # Test 3: Selective forgetting
    print("\n3. Testing selective forget...")
    forget_queries = [
        "guitar",
        "cat"
    ]
    
    for forget_query in forget_queries:
        print(f"   Forgetting: {forget_query}...")
        response = requests.post(
            f"{MEMORY_API_URL}/api/memory/forget",
            json={
                "user_id": user_id,
                "forget_query": forget_query,
                "source": "comprehensive_test"
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            count = result.get('removed_count', 0)
            print(f"      ✅ Removed {count} memories")
            print(f"         Remaining: {result['total_memories']['total']} total")
        else:
            print(f"      ❌ Forget failed: {response.status_code}")
    
    # Test 4: Verify selective forgetting worked
    print("\n4. Verifying selective forgetting...")
    for query in ["guitar", "work", "cat"]:
        response = requests.post(
            f"{MEMORY_API_URL}/api/memory/retrieve",
            json={
                "user_id": user_id,
                "query": query,
                "threshold": 0.05,
                "limit": 10
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            count = len(result.get('memories', []))
            if query in ["guitar", "cat"]:
                if count == 0:
                    print(f"   ✅ {query}: Successfully forgotten (0 memories)")
                else:
                    print(f"   ⚠️ {query}: Expected 0, found {count} memories")
            else:
                print(f"   ✅ {query}: Preserved ({count} memories)")
        else:
            print(f"   ❌ Verification query failed for {query}")
    
    # Test 5: Memory statistics
    print("\n5. Final memory statistics...")
    response = requests.post(
        f"{MEMORY_API_URL}/api/memory/retrieve",
        json={
            "user_id": user_id,
            "query": "",  # Empty query to get general stats
            "threshold": 0.0,
            "limit": 100
        }
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"   📊 Memory Statistics:")
        if 'stats' in result:
            print(f"      Short-term: {result['stats']['short_term']}")
            print(f"      Long-term: {result['stats']['long_term']}")
            print(f"      Total: {result['stats']['total']}")
        else:
            memories = result.get('memories', [])
            print(f"      Found {len(memories)} total retrievable memories")
    
    print("\n🎉 Comprehensive test completed!")

if __name__ == "__main__":
    test_complete_explicit_memory()
