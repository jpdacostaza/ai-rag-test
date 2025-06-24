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
Quick Memory Cross-Chat Test
Tests if OpenWebUI memory persists across different chat sessions
"""

import requests
import json
import time
import sys
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

def test_memory_persistence(api_token, base_url):
    """Test memory across chat sessions"""
    
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }
    
    print("[BRAIN] Testing OpenWebUI Memory Persistence Across Chats")
    print("=" * 55)
    
    # Step 1: Add a test memory
    print("1. Adding test memory...")
    memory_content = f"User tested memory system on {time.strftime('%Y-%m-%d %H:%M:%S')}. User likes debugging and problem-solving."
    
    try:
        response = requests.post(
            f"{base_url}/api/v1/memories/add",
            headers=headers,
            json={"content": memory_content}
        )
        if response.status_code == 200:
            print(f"   [OK] Memory added successfully")
        else:
            print(f"   [FAIL] Failed to add memory: {response.status_code} - {response.text}")
            return
    except Exception as e:
        print(f"   [FAIL] Error adding memory: {e}")
        return
    
    # Step 2: Test memory query
    print("\n2. Testing memory query...")
    try:
        response = requests.post(
            f"{base_url}/api/v1/memories/query",
            headers=headers,
            json={"content": "what do you remember about me", "k": 3}
        )
        if response.status_code == 200:
            results = response.json()
            if results and hasattr(results, 'documents') and results.get('documents'):
                docs = results['documents'][0] if results['documents'] else []
                print(f"   [OK] Found {len(docs)} relevant memories")
                for i, doc in enumerate(docs[:2]):
                    print(f"   [NOTE] Memory {i+1}: {doc[:60]}...")
            else:
                print("   ⚠️ Memory query returned no results")
        else:
            print(f"   [FAIL] Memory query failed: {response.status_code}")
    except Exception as e:
        print(f"   [FAIL] Error querying memory: {e}")
    
    # Step 3: Simulate chat request with memory
    print("\n3. Testing chat with memory injection...")
    chat_payload = {
        "model": "llama3.2:3b",  # Adjust to your model
        "messages": [
            {"role": "user", "content": "What do you remember about me?"}
        ],
        "stream": False,
        "features": {
            "memory": True  # This is crucial!
        }
    }
    
    try:
        response = requests.post(
            f"{base_url}/api/chat/completions",
            headers=headers,
            json=chat_payload
        )
        if response.status_code == 200:
            result = response.json()
            assistant_response = result.get('choices', [{}])[0].get('message', {}).get('content', '')
            if 'debug' in assistant_response.lower() or 'test' in assistant_response.lower():
                print("   [OK] Memory seems to be working - AI referenced stored context")
            else:
                print("   ⚠️ AI response doesn't seem to reference stored memory")
            print(f"   📤 AI Response: {assistant_response[:100]}...")
        else:
            print(f"   [FAIL] Chat request failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"   [FAIL] Error testing chat: {e}")
    
    print("\n[IDEA] Next Steps:")
    print("1. If memory query works but chat doesn't reference it:")
    print("   - Check that memory feature is enabled in OpenWebUI settings")
    print("   - Verify backend logs for memory injection")
    print("2. If memory query returns no results:")
    print("   - Check ChromaDB is running and accessible")
    print("   - Verify embeddings model is loaded")
    print("3. Check backend logs: docker logs backend-llm-backend --tail 20")


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
        api_token, base_url = get_api_credentials(user=user, environment=environment)
        
        if not api_token:
            print("[FAIL] Please provide your OpenWebUI API token")
            print("[IDEA] Get token from: OpenWebUI Settings → Account → API Keys")
        else:
            test_memory_persistence(api_token, base_url)
    except KeyboardInterrupt:
        print("\n[FAIL] Cancelled by user")
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        print("Usage: python test_memory_cross_chat.py [--user=username] [--env=environment]")
