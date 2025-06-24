#!/usr/bin/env python3
"""
ChromaDB Collection Inspector
Direct inspection of ChromaDB collection contents
"""

import requests
import json
import time

BACKEND_URL = "http://localhost:8001"
API_KEY = "test_api_key_2024"

def inspect_chromadb_collection():
    """Inspect ChromaDB collection contents directly"""
    
    print("🔍 ChromaDB Collection Inspector")
    print("=" * 50)
    
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    
    # 1. First store a memory to ensure we have something
    print("📝 Step 1: Store a test memory")
    user_id = "inspector_test_user"
    test_message = "Please remember: my name is Alice and I love programming in Python."
    
    storage_data = {
        "user_id": user_id,
        "message": test_message,
        "conversation_id": "inspect_test_001",
        "timestamp": time.time(),
        "metadata": {"test": "inspector", "source": "direct"}
    }
    
    try:
        storage_response = requests.post(
            f"{BACKEND_URL}/api/learning/process_interaction",
            json=storage_data,
            headers=headers,
            timeout=10
        )
        print(f"Storage Response: {storage_response.status_code}")
        if storage_response.status_code == 200:
            result = storage_response.json()
            print(f"Storage successful: {result.get('status')}")
        else:
            print(f"Storage failed: {storage_response.text}")
            
    except Exception as e:
        print(f"❌ Storage error: {e}")
        return
    
    # 2. Wait for indexing
    print("\n⏳ Waiting 5 seconds for indexing...")
    time.sleep(5)
    
    # 3. Try to retrieve with exact match
    print(f"\n🔍 Step 2: Try exact keyword retrieval")
    exact_queries = ["Alice", "Python", "programming", "Hello"]
    
    for query in exact_queries:
        print(f"\n🔍 Testing exact query: '{query}'")
        retrieval_data = {
            "user_id": user_id,
            "query": query,
            "limit": 10,
            "threshold": 0.0  # Very low threshold to catch anything
        }
        
        try:
            retrieval_response = requests.post(
                f"{BACKEND_URL}/api/memory/retrieve",
                json=retrieval_data,
                headers=headers,
                timeout=10
            )
            
            if retrieval_response.status_code == 200:
                result = retrieval_response.json()
                count = result.get('count', 0)
                print(f"  Found {count} memories")
                
                if count > 0:
                    for i, memory in enumerate(result.get('memories', [])[:3]):
                        content = memory.get('content', 'No content')
                        similarity = memory.get('similarity', 'N/A')
                        print(f"    Memory {i+1}: {content[:100]}...")
                        print(f"    Similarity: {similarity}")
                else:
                    print(f"  No memories found for '{query}'")
            else:
                print(f"  Retrieval failed: {retrieval_response.text}")
                
        except Exception as e:
            print(f"  ❌ Retrieval error: {e}")
    
    # 4. Test with different user to see if it's user-specific
    print(f"\n🔍 Step 3: Test with different user_id")
    retrieval_data = {
        "user_id": "different_user",
        "query": "Alice",
        "limit": 10,
        "threshold": 0.0
    }
    
    try:
        retrieval_response = requests.post(
            f"{BACKEND_URL}/api/memory/retrieve",
            json=retrieval_data,
            headers=headers,
            timeout=10
        )
        
        if retrieval_response.status_code == 200:
            result = retrieval_response.json()
            count = result.get('count', 0)
            print(f"Different user query found {count} memories (should be 0)")
        else:
            print(f"Different user query failed: {retrieval_response.text}")
            
    except Exception as e:
        print(f"❌ Different user query error: {e}")

if __name__ == "__main__":
    inspect_chromadb_collection()
