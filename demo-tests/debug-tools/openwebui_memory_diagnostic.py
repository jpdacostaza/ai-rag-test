#!/usr/bin/env python3
"""
OpenWebUI Memory Diagnostic Tool
Checks memory configuration and helps debug cross-chat memory issues.
"""

import requests
import json
import sys

def check_memory_status(base_url, token, user_id):
    """Check OpenWebUI memory system status"""
    print("🔍 OpenWebUI Memory Diagnostic Tool")
    print("=" * 50)
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # 1. Check if memories exist
    print("1. Checking stored memories...")
    try:
        response = requests.get(f"{base_url}/api/v1/memories/", headers=headers)
        if response.status_code == 200:
            memories = response.json()
            print(f"   ✅ Found {len(memories)} stored memories")
            for i, memory in enumerate(memories[:3]):
                print(f"   📝 Memory {i+1}: {memory['content'][:50]}...")
        else:
            print(f"   ❌ Failed to fetch memories: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error fetching memories: {e}")
    
    # 2. Test memory query
    print("\n2. Testing memory query functionality...")
    try:
        query_data = {"content": "what do you remember about me", "k": 3}
        response = requests.post(f"{base_url}/api/v1/memories/query", 
                               headers=headers, json=query_data)
        if response.status_code == 200:
            results = response.json()
            if hasattr(results, 'documents') and results.documents:
                print(f"   ✅ Memory query working - found {len(results.documents[0])} relevant memories")
            else:
                print("   ⚠️ Memory query returns empty results")
        else:
            print(f"   ❌ Memory query failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error testing memory query: {e}")
    
    # 3. Check embeddings function
    print("\n3. Testing embeddings function...")
    try:
        response = requests.get(f"{base_url}/api/v1/memories/ef", headers=headers)
        if response.status_code == 200:
            print("   ✅ Embeddings function working")
        else:
            print(f"   ❌ Embeddings function failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error testing embeddings: {e}")

if __name__ == "__main__":
    # Configuration
    BASE_URL = "http://localhost:3000"  # Your OpenWebUI URL
    TOKEN = input("Enter your OpenWebUI API token: ").strip()
    USER_ID = input("Enter your user ID (or 'auto' to detect): ").strip()
    
    check_memory_status(BASE_URL, TOKEN, USER_ID)
