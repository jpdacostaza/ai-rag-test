#!/usr/bin/env python3
"""
Debug ChromaDB Direct Access Test
Test ChromaDB access and collection state directly
"""

import requests
import json

BACKEND_URL = "http://localhost:8001"
API_KEY = "test_api_key_2024"

def test_chromadb_direct():
    """Test ChromaDB access and collection state"""
    
    print("🔬 ChromaDB Direct Access Test")
    print("=" * 50)
    
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    
    # 1. Check overall health
    print("📊 Step 1: Overall health check")
    try:
        health_response = requests.get(f"{BACKEND_URL}/health", timeout=5)
        print(f"Health Status: {health_response.status_code}")
        if health_response.status_code == 200:
            health = health_response.json()
            print(f"Overall Status: {health.get('status')}")
            print(f"Summary: {health.get('summary')}")
            
            db_health = health.get('databases', {})
            chromadb_info = db_health.get('chromadb', {})
            print(f"ChromaDB Available: {chromadb_info.get('available', False)}")
            print(f"ChromaDB Client: {chromadb_info.get('client', False)}")
            print(f"ChromaDB Collection: {chromadb_info.get('collection', False)}")
        
    except Exception as e:
        print(f"❌ Health check error: {e}")
    
    # 2. Check ChromaDB specific endpoint
    print(f"\n📊 Step 2: ChromaDB specific health")
    try:
        chromadb_response = requests.get(f"{BACKEND_URL}/health/chromadb", timeout=5)
        print(f"ChromaDB Health Status: {chromadb_response.status_code}")
        if chromadb_response.status_code == 200:
            result = chromadb_response.json()
            print(f"ChromaDB Health: {json.dumps(result, indent=2)}")
            
    except Exception as e:
        print(f"❌ ChromaDB health error: {e}")
    
    # 3. Test memory retrieval with verbose output
    print(f"\n🔍 Step 3: Test memory retrieval with debug user")
    try:
        retrieval_data = {
            "user_id": "test_debug_user",
            "query": "test query",
            "limit": 5,
            "threshold": 0.1
        }
        
        retrieval_response = requests.post(
            f"{BACKEND_URL}/api/memory/retrieve",
            json=retrieval_data,
            headers=headers,
            timeout=10
        )
        print(f"Memory Retrieval Status: {retrieval_response.status_code}")
        print(f"Memory Retrieval Response: {retrieval_response.text}")
        
    except Exception as e:
        print(f"❌ Memory retrieval error: {e}")

if __name__ == "__main__":
    test_chromadb_direct()
