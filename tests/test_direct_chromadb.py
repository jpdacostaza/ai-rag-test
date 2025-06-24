#!/usr/bin/env python3
"""
Direct ChromaDB Storage Test
Test direct storage to ChromaDB to isolate the issue
"""

import requests
import json
import time

BACKEND_URL = "http://localhost:8001"
API_KEY = "test_api_key_2024"

def test_direct_chromadb_storage():
    """Test direct storage to ChromaDB via document indexing"""
    
    print("🔬 Direct ChromaDB Storage Test")
    print("=" * 50)
    
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    
    user_id = "direct_chromadb_user"
    test_content = "My name is David and I am a machine learning engineer at AITech. I specialize in deep learning and PyTorch."
      # 1. Use the document upload endpoint to store directly in ChromaDB
    print(f"📝 Step 1: Storing document directly via /upload/document")
    
    # Prepare file upload (the endpoint expects multipart form data)
    files = {
        'file': ('memory.txt', test_content, 'text/plain')
    }
    data = {
        'user_id': user_id,
        'description': 'Memory content for testing'
    }
    
    try:
        upload_response = requests.post(
            f"{BACKEND_URL}/upload/document",
            files=files,
            data=data,
            headers={"Authorization": f"Bearer {API_KEY}"},  # Remove Content-Type for multipart
            timeout=15
        )
        print(f"Upload Response Status: {upload_response.status_code}")
        print(f"Upload Response: {upload_response.text}")
        
        if upload_response.status_code == 200:
            print("✅ Direct document storage successful")
        else:
            print("❌ Direct document storage failed")
            
    except Exception as e:
        print(f"❌ Upload error: {e}")
    
    # 2. Wait for ChromaDB indexing
    print("\n⏳ Waiting 8 seconds for ChromaDB indexing...")
    time.sleep(8)
    
    # 3. Test memory retrieval
    print(f"\n🔍 Step 2: Testing memory retrieval")
    test_queries = ["David", "machine learning", "AITech", "PyTorch", "deep learning"]
    
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
                    print("✅ SUCCESS: Memory storage and retrieval working!")
                    break
                else:
                    print(f"  No memories found for '{query}'")
            else:
                print(f"  Retrieval failed: {retrieval_response.text}")
                
        except Exception as e:
            print(f"  ❌ Retrieval error: {e}")
      # 4. Also test upload search endpoint
    print(f"\n🔍 Step 3: Testing upload search endpoint")
    try:
        search_response = requests.post(
            f"{BACKEND_URL}/upload/search",
            json={"query": "machine learning engineer", "user_id": user_id, "limit": 5},
            headers=headers,
            timeout=10        )
        print(f"Upload Search Status: {search_response.status_code}")
        if search_response.status_code == 200:
            result = search_response.json()
            print(f"Upload Search Results: {len(result.get('results', []))} found")
        else:
            print(f"Upload Search Response: {search_response.text}")
            
    except Exception as e:
        print(f"❌ Upload search error: {e}")

if __name__ == "__main__":
    test_direct_chromadb_storage()
