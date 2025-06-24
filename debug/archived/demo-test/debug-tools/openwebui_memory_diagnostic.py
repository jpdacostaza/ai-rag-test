#!/usr/bin/env python3
"""
OpenWebUI Memory Diagnostic Tool
Checks memory configuration and helps debug cross-chat memory issues.
"""

import requests
import json
import sys
import os
from pathlib import Path

# Add parent directory to path to import API key manager
sys.path.append(str(Path(__file__).parent.parent.parent))
from setup.api_key_manager import APIKeyManager

def get_api_credentials(user=None, environment=None):
    """Get API credentials with automatic fallback."""
    key_manager = APIKeyManager(str(Path(__file__).parent.parent.parent / "setup" / "openwebui_api_keys.json"))
    
    # Try to get key with fallback logic
    credentials = key_manager.get_key(user=user, environment=environment)
    
    if credentials:
        print(f"🔑 Using API credentials from: {credentials.get('source', 'unknown')}")
        return credentials["api_key"], credentials["base_url"]
    
    # Manual fallback
    print("⚠️  No API keys found in config. Please enter manually:")
    token = input("Enter your OpenWebUI API token: ").strip()
    base_url = input("Enter base URL [http://localhost:3000]: ").strip() or "http://localhost:3000"
    return token, base_url


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
            print(f"   📋 Query response: {results}")
            if isinstance(results, dict) and 'documents' in results and results['documents']:
                docs = results['documents'][0] if results['documents'] else []
                print(f"   ✅ Memory query working - found {len(docs)} relevant memories")
                for i, doc in enumerate(docs[:2]):
                    print(f"   📝 Memory {i+1}: {doc[:50]}...")
            else:
                print("   ⚠️ Memory query returns empty results")
        else:
            print(f"   ❌ Memory query failed: {response.status_code} - {response.text}")
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
    # Parse command line arguments for user/environment
    user = None
    environment = None
    
    if len(sys.argv) > 1:
        if sys.argv[1].startswith("--user="):
            user = sys.argv[1].split("=", 1)[1]
        elif sys.argv[1].startswith("--env="):
            environment = sys.argv[1].split("=", 1)[1]
    
    # Get API credentials automatically
    try:
        TOKEN, BASE_URL = get_api_credentials(user=user, environment=environment)
        USER_ID = input("Enter your user ID (or 'auto' to detect): ").strip()
        
        check_memory_status(BASE_URL, TOKEN, USER_ID)
    except KeyboardInterrupt:
        print("\n❌ Cancelled by user")
    except Exception as e:
        print(f"❌ Error: {e}")
        print("Usage: python openwebui_memory_diagnostic.py [--user=username] [--env=environment]")
