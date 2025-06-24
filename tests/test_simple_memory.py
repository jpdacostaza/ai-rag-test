#!/usr/bin/env python3
"""
Simple Direct Memory Test
Test memory storage bypassing adaptive learning
"""

import requests
import json
import time

BACKEND_URL = "http://localhost:8001"
API_KEY = "test_api_key_2024"

def test_simple_memory_storage():
    """Test simple memory storage using learn endpoint"""
    
    print("🔬 Simple Direct Memory Test")
    print("=" * 50)
    
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    
    # Test user and data
    user_id = "simple_test_user"
    test_content = "My name is Charlie and I am a software engineer at TechStart. I enjoy coding in JavaScript and React."
      # 1. Store memory using the working process_interaction endpoint
    print(f"📝 Step 1: Storing memory using /api/learning/process_interaction endpoint")
    storage_data = {
        "user_id": user_id,
        "user_message": test_content + " Please remember this information.",  # Add remember keyword
        "assistant_response": "I'll remember that information for you.",
        "response_time": 1.0,
        "conversation_id": f"test_{int(time.time())}",        "source": "test"
    }
    
    try:
        storage_response = requests.post(
            f"{BACKEND_URL}/api/learning/process_interaction",
            json=storage_data,
            headers=headers,
            timeout=10
        )
        print(f"Process Interaction Response Status: {storage_response.status_code}")
        print(f"Process Interaction Response: {storage_response.text}")
        
        if storage_response.status_code == 200:
            print("✅ Memory storage via /api/learning/process_interaction successful")
        else:
            print("❌ Memory storage via /api/learning/process_interaction failed")
            
    except Exception as e:
        print(f"❌ Process interaction endpoint error: {e}")
    
    # 2. Wait for indexing
    print("\n⏳ Waiting 5 seconds for ChromaDB indexing...")
    time.sleep(5)
    
    # 3. Test retrieval
    print(f"\n🔍 Step 2: Testing memory retrieval")
    test_queries = ["Charlie", "software engineer", "TechStart", "JavaScript", "React"]
    
    for query in test_queries:
        print(f"\n🔍 Testing query: '{query}'")
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
            
            if retrieval_response.status_code == 200:
                result = retrieval_response.json()
                count = result.get('count', 0)
                print(f"  Found {count} memories")
                
                if count > 0:
                    for i, memory in enumerate(result.get('memories', [])[:2]):
                        content = memory.get('content', 'No content')
                        similarity = memory.get('similarity', 'N/A')
                        print(f"    Memory {i+1}: {content[:80]}...")
                        print(f"    Similarity: {similarity}")
                    break  # Found memories, stop testing other queries
                else:
                    print(f"  No memories found for '{query}'")
            else:
                print(f"  Retrieval failed: {retrieval_response.text}")
                
        except Exception as e:
            print(f"  ❌ Retrieval error: {e}")

if __name__ == "__main__":
    test_simple_memory_storage()
