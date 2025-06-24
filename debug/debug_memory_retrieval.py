#!/usr/bin/env python3
"""
Debug Memory Retrieval Script
Test memory storage and retrieval with detailed logging
"""

import requests
import json
import time

BACKEND_URL = "http://localhost:8001"
API_KEY = "test_api_key_2024"

def test_memory_storage_and_retrieval():
    """Test memory storage and retrieval with debug output"""
    
    print("🔬 Debug Memory Storage and Retrieval Test")
    print("=" * 50)
    
    # Test user and data
    user_id = "debug_user_001"
    test_message = "My name is John Smith and I work as a software engineer at TechCorp"
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    
    # 1. Store memory
    print(f"📝 Step 1: Storing memory for user {user_id}")
    storage_data = {
        "user_id": user_id,
        "message": test_message,
        "conversation_id": "debug_conv_001",
        "timestamp": time.time(),
        "metadata": {"test": "debug", "source": "manual"}
    }
    
    try:
        storage_response = requests.post(
            f"{BACKEND_URL}/api/learning/process_interaction",
            json=storage_data,
            headers=headers,
            timeout=10
        )
        print(f"Storage Response Status: {storage_response.status_code}")
        print(f"Storage Response: {storage_response.text}")
        
        if storage_response.status_code != 200:
            print("❌ Storage failed!")
            return
            
    except Exception as e:
        print(f"❌ Storage error: {e}")
        return
    
    # 2. Wait for indexing
    print("\n⏳ Waiting 3 seconds for ChromaDB indexing...")
    time.sleep(3)
    
    # 3. Test retrieval
    print(f"\n🔍 Step 2: Retrieving memory for user {user_id}")
    retrieval_queries = [
        "What is my name?",
        "Where do I work?", 
        "John Smith",
        "TechCorp",
        "software engineer"
    ]
    
    for query in retrieval_queries:
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
            print(f"Retrieval Response Status: {retrieval_response.status_code}")
            
            if retrieval_response.status_code == 200:
                result = retrieval_response.json()
                print(f"Memories found: {result.get('count', 0)}")
                
                if result.get('memories'):
                    for i, memory in enumerate(result['memories'][:3]):
                        print(f"  Memory {i+1}: {memory.get('content', 'No content')[:100]}...")
                        print(f"    Similarity: {memory.get('similarity', 'N/A')}")
                        print(f"    Metadata: {memory.get('metadata', {})}")
                else:
                    print("  No memories returned")
            else:
                print(f"Retrieval failed: {retrieval_response.text}")
                
        except Exception as e:
            print(f"❌ Retrieval error for '{query}': {e}")
    
    # 4. Direct ChromaDB check
    print(f"\n🔍 Step 3: Direct ChromaDB health check")
    try:
        health_response = requests.get(f"{BACKEND_URL}/health", timeout=5)
        print(f"Health Response: {health_response.status_code}")
        if health_response.status_code == 200:
            health = health_response.json()
            print(f"ChromaDB Available: {health.get('chromadb', {}).get('available', False)}")
            print(f"ChromaDB Status: {health.get('chromadb', {}).get('status', 'unknown')}")
        
    except Exception as e:
        print(f"❌ Health check error: {e}")

if __name__ == "__main__":
    test_memory_storage_and_retrieval()
