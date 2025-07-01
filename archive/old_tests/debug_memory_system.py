#!/usr/bin/env python3
"""
Memory Debug Script
==================
Check what memories are stored and why they're not being retrieved.
"""

import requests
import json

def test_memory_system():
    """Test the memory system"""
    base_url = "http://localhost:8001"
    user_id = "anonymous"
    
    print("🔍 Testing Memory System")
    print("=" * 50)
    
    # Test 1: Try to retrieve with different queries
    queries = [
        "what do you know about me",
        "J.P.",
        "swift",
        "work",
        "name"
    ]
    
    for query in queries:
        try:
            response = requests.post(f"{base_url}/api/memory/retrieve", json={
                "user_id": user_id,
                "query": query,
                "limit": 10
            })
            
            if response.status_code == 200:
                data = response.json()
                print(f"\n🔍 Query: '{query}'")
                print(f"   Status: {data.get('status')}")
                print(f"   Count: {data.get('count')}")
                print(f"   Sources: {data.get('sources')}")
                
                if data.get('memories'):
                    for i, memory in enumerate(data['memories']):
                        print(f"   Memory {i+1}: {memory.get('content', '')[:100]}...")
                        print(f"   Relevance: {memory.get('relevance_score', 'N/A')}")
                else:
                    print("   No memories returned")
            else:
                print(f"❌ Query '{query}' failed: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error with query '{query}': {e}")
    
    # Test 2: Store a test memory
    print(f"\n💾 Storing test memory...")
    try:
        response = requests.post(f"{base_url}/api/learning/process_interaction", json={
            "user_id": user_id,
            "conversation_id": "test-debug",
            "user_message": "My name is TestUser and I love debugging memory systems",
            "assistant_response": "I'll remember that your name is TestUser and you enjoy debugging memory systems",
            "context": {},
            "source": "debug_test"
        })
        
        if response.status_code == 200:
            print("✅ Test memory stored successfully")
        else:
            print(f"❌ Failed to store test memory: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error storing test memory: {e}")
    
    # Test 3: Try retrieving the test memory
    print(f"\n🔍 Retrieving test memory...")
    try:
        response = requests.post(f"{base_url}/api/memory/retrieve", json={
            "user_id": user_id,
            "query": "TestUser debugging",
            "limit": 5
        })
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Status: {data.get('status')}")
            print(f"   Count: {data.get('count')}")
            
            if data.get('memories'):
                for memory in data['memories']:
                    print(f"   Found: {memory.get('content', '')[:100]}...")
                    print(f"   Relevance: {memory.get('relevance_score', 'N/A')}")
            else:
                print("   No test memory found")
        else:
            print(f"❌ Failed to retrieve test memory: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error retrieving test memory: {e}")

if __name__ == "__main__":
    test_memory_system()
