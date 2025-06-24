#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Windows-compatible debug tool with Unicode fixes applied
"""
import sys
import os

# Set UTF-8 encoding for Windows compatibility
if sys.platform.startswith('win'):
    import io
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
    except AttributeError:
        pass  # Already wrapped or not available

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
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

# Create a simple APIKeyManager class if import fails
class SimpleAPIKeyManager:
    def __init__(self, config_path):
        self.config_path = config_path
    
    def get_key(self, user=None, environment=None):
        return {
            "api_key": "f2b985dd-219f-45b1-a90e-170962cc7082",  # Default test key
            "base_url": "http://localhost:3000",
            "source": "fallback"
        }

try:
    from setup.api_key_manager import APIKeyManager
except ImportError:
    try:
        from api_key_manager import APIKeyManager
    except ImportError:
        APIKeyManager = SimpleAPIKeyManager

def get_api_credentials(user=None, environment=None):
    """Get API credentials with automatic fallback."""
    # Try multiple possible paths for the API keys file
    possible_paths = [
        Path(__file__).parent.parent.parent.parent / "setup" / "openwebui_api_keys.json",
        Path(__file__).parent.parent.parent / "setup" / "openwebui_api_keys.json", 
        Path(__file__).parent / "openwebui_api_keys.json",
        Path("setup/openwebui_api_keys.json"),
        Path("openwebui_api_keys.json")    ]
    key_manager = None
    for path in possible_paths:
        if path.exists():
            key_manager = APIKeyManager(str(path))
            break
    
    if not key_manager:
        # Create a simple fallback if no API key manager file found
        print("[SEARCH] No API key manager file found, using fallback credentials")
        return "f2b985dd-219f-45b1-a90e-170962cc7082", "http://localhost:3000"
    
    # Try to get key with fallback logic
    credentials = key_manager.get_key(user=user, environment=environment)
    
    if credentials and isinstance(credentials, dict):
        print(f"[SEARCH] Using API credentials from: {credentials.get('source', 'unknown')}")
        return credentials["api_key"], credentials["base_url"]
    
    # Manual fallback
    print("[SEARCH] No API keys found in config, using default test credentials")
    return "f2b985dd-219f-45b1-a90e-170962cc7082", "http://localhost:3000"


def check_memory_status(base_url, token, user_id):
    """Check OpenWebUI memory system status"""
    print("[SEARCH] OpenWebUI Memory Diagnostic Tool")
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
            print(f"   [OK] Found {len(memories)} stored memories")
            for i, memory in enumerate(memories[:3]):
                print(f"   [NOTE] Memory {i+1}: {memory['content'][:50]}...")
        else:
            print(f"   [FAIL] Failed to fetch memories: {response.status_code}")
    except Exception as e:
        print(f"   [FAIL] Error fetching memories: {e}")
      # 2. Test memory query
    print("\n2. Testing memory query functionality...")
    try:
        query_data = {"content": "what do you remember about me", "k": 3}
        response = requests.post(f"{base_url}/api/v1/memories/query", 
                               headers=headers, json=query_data)
        if response.status_code == 200:
            results = response.json()
            print(f"   [CLIPBOARD] Query response: {results}")
            if isinstance(results, dict) and 'documents' in results and results['documents']:
                docs = results['documents'][0] if results['documents'] else []
                print(f"   [OK] Memory query working - found {len(docs)} relevant memories")
                for i, doc in enumerate(docs[:2]):
                    print(f"   [NOTE] Memory {i+1}: {doc[:50]}...")
            else:
                print("   ⚠️ Memory query returns empty results")
        else:
            print(f"   [FAIL] Memory query failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"   [FAIL] Error testing memory query: {e}")
    
    # 3. Check embeddings function
    print("\n3. Testing embeddings function...")
    try:
        response = requests.get(f"{base_url}/api/v1/memories/ef", headers=headers)
        if response.status_code == 200:
            print("   [OK] Embeddings function working")
        else:
            print(f"   [FAIL] Embeddings function failed: {response.status_code}")
    except Exception as e:
        print(f"   [FAIL] Error testing embeddings: {e}")

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
        print("\n[FAIL] Cancelled by user")
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        print("Usage: python openwebui_memory_diagnostic.py [--user=username] [--env=environment]")
