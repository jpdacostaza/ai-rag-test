#!/usr/bin/env python3
"""
Test Memory Retrieval API
Test why the memory retrieval API isn't finding stored documents
"""

import requests
import json

BACKEND_URL = "http://localhost:8001"
API_KEY = "test_api_key_2024"

def test_memory_retrieval_api():
    """Test the memory retrieval API with known stored data"""
    
    print("🔍 Memory Retrieval API Test")
    print("=" * 50)
    
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    
    # We know that direct_chromadb_user has a document stored
    user_id = "direct_chromadb_user"
    test_queries = ["David", "machine learning", "AITech", "PyTorch"]
    
    for query in test_queries:
        print(f"\n🔍 Testing memory retrieval for: '{query}'")
        retrieval_data = {
            "user_id": user_id,
            "query": query,
            "limit": 5,
            "threshold": 0.1
        }
        
        try:
            retrieval_response = requests.post(
                f"{BACKEND_URL}/api/memory/retrieve",
                json=retrieval_data,
                headers=headers,
                timeout=10
            )
            
            print(f"  Status: {retrieval_response.status_code}")
            
            if retrieval_response.status_code == 200:
                result = retrieval_response.json()
                count = result.get('count', 0)
                print(f"  Memories found: {count}")
                
                if count > 0:
                    for i, memory in enumerate(result.get('memories', [])):
                        content = memory.get('content', 'No content')
                        similarity = memory.get('similarity', 'N/A')
                        metadata = memory.get('metadata', {})
                        print(f"    Memory {i+1}:")
                        print(f"      Content: {content[:100]}...")
                        print(f"      Similarity: {similarity}")
                        print(f"      Metadata: {metadata}")
                    break
                else:
                    print(f"  No memories found")
            else:
                print(f"  Error: {retrieval_response.text}")
                
        except Exception as e:
            print(f"  ❌ Error: {e}")
    
    # Also test with different user_id to see if it's user-specific
    print(f"\n🔍 Testing with different user_id (should find 0)")
    retrieval_data = {
        "user_id": "different_user_test",
        "query": "David",
        "limit": 5,
        "threshold": 0.1
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
            print(f"  Different user found: {count} memories (should be 0)")
        else:
            print(f"  Error: {retrieval_response.text}")
            
    except Exception as e:
        print(f"  ❌ Error: {e}")

if __name__ == "__main__":
    test_memory_retrieval_api()
