#!/usr/bin/env python3
"""
Simple Memory Service Connection Test
===================================

Test basic connectivity and identify the root cause of storage failures.
"""

import asyncio
import requests
import json

async def test_basic_connectivity():
    """Test basic service connectivity."""
    print("🔍 Testing Basic Memory Service Connectivity")
    print("=" * 50)
    
    # Test Memory API Health
    try:
        response = requests.get("http://localhost:5001/health")
        print(f"✅ Memory API Health: {response.status_code}")
        if response.status_code == 200:
            health_data = response.json()
            print(f"   Service: {health_data.get('service')}")
            print(f"   Memory Service Available: {health_data.get('memory_service_available')}")
    except Exception as e:
        print(f"❌ Memory API Health Failed: {e}")
    
    # Test Memory Storage
    test_data = {
        "user_id": "test-connectivity",
        "content": "Simple connectivity test",
        "context": "connectivity check",
        "importance": 0.5,
        "source": "connectivity_test",
        "forced": False
    }
    
    try:
        response = requests.post(
            "http://localhost:5001/api/memory/store",
            json=test_data
        )
        print(f"✅ Memory Storage Endpoint: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"   Success: {result.get('success')}")
            print(f"   Storage Location: {result.get('storage_location')}")
            print(f"   Memory ID: {result.get('memory_id')}")
            if 'error' in result:
                print(f"   Error: {result.get('error')}")
    except Exception as e:
        print(f"❌ Memory Storage Failed: {e}")
    
    # Test Memory Retrieval
    try:
        response = requests.post(
            "http://localhost:5001/api/memory/retrieve",
            json={"user_id": "test-connectivity", "query": "connectivity", "limit": 5}
        )
        print(f"✅ Memory Retrieval Endpoint: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"   Memories Found: {result.get('count', 0)}")
    except Exception as e:
        print(f"❌ Memory Retrieval Failed: {e}")
    
    # Test Ollama Connection
    try:
        response = requests.get("http://localhost:11434/api/tags")
        print(f"✅ Ollama API: {response.status_code}")
        if response.status_code == 200:
            tags = response.json()
            models = [model['name'] for model in tags.get('models', [])]
            print(f"   Available Models: {models[:3]}...")
    except Exception as e:
        print(f"❌ Ollama API Failed: {e}")
    
    # Test ChromaDB
    try:
        response = requests.get("http://localhost:8000/api/v2/heartbeat")
        print(f"✅ ChromaDB v2: {response.status_code}")
        if response.status_code != 200:
            # Try collections endpoint
            response = requests.get("http://localhost:8000/api/v2/collections")
            print(f"   Collections endpoint: {response.status_code}")
    except Exception as e:
        print(f"❌ ChromaDB Failed: {e}")
    
    # Test Redis
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, decode_responses=True)
        ping_result = r.ping()
        print(f"✅ Redis: Connected ({ping_result})")
    except Exception as e:
        print(f"❌ Redis Failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_basic_connectivity())
