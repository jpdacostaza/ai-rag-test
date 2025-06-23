#!/usr/bin/env python3
"""
Quick Memory Cross-Chat Test
Tests if OpenWebUI memory persists across different chat sessions
"""

import requests
import json
import time

def test_memory_persistence():
    """Test memory across chat sessions"""
    
    # Configuration - Update these for your setup
    OPENWEBUI_URL = "http://localhost:3000"
    API_TOKEN = None  # You'll need to get this from OpenWebUI
    
    if not API_TOKEN:
        print("❌ Please set your OpenWebUI API token in the script")
        print("💡 Get token from: OpenWebUI Settings → Account → API Keys")
        return
    
    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "application/json"
    }
    
    print("🧠 Testing OpenWebUI Memory Persistence Across Chats")
    print("=" * 55)
    
    # Step 1: Add a test memory
    print("1. Adding test memory...")
    memory_content = f"User tested memory system on {time.strftime('%Y-%m-%d %H:%M:%S')}. User likes debugging and problem-solving."
    
    try:
        response = requests.post(
            f"{OPENWEBUI_URL}/api/v1/memories/add",
            headers=headers,
            json={"content": memory_content}
        )
        if response.status_code == 200:
            print(f"   ✅ Memory added successfully")
        else:
            print(f"   ❌ Failed to add memory: {response.status_code} - {response.text}")
            return
    except Exception as e:
        print(f"   ❌ Error adding memory: {e}")
        return
    
    # Step 2: Test memory query
    print("\n2. Testing memory query...")
    try:
        response = requests.post(
            f"{OPENWEBUI_URL}/api/v1/memories/query",
            headers=headers,
            json={"content": "what do you remember about me", "k": 3}
        )
        if response.status_code == 200:
            results = response.json()
            if results and hasattr(results, 'documents') and results.get('documents'):
                docs = results['documents'][0] if results['documents'] else []
                print(f"   ✅ Found {len(docs)} relevant memories")
                for i, doc in enumerate(docs[:2]):
                    print(f"   📝 Memory {i+1}: {doc[:60]}...")
            else:
                print("   ⚠️ Memory query returned no results")
        else:
            print(f"   ❌ Memory query failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error querying memory: {e}")
    
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
            f"{OPENWEBUI_URL}/api/chat/completions",
            headers=headers,
            json=chat_payload
        )
        if response.status_code == 200:
            result = response.json()
            assistant_response = result.get('choices', [{}])[0].get('message', {}).get('content', '')
            if 'debug' in assistant_response.lower() or 'test' in assistant_response.lower():
                print("   ✅ Memory seems to be working - AI referenced stored context")
            else:
                print("   ⚠️ AI response doesn't seem to reference stored memory")
            print(f"   📤 AI Response: {assistant_response[:100]}...")
        else:
            print(f"   ❌ Chat request failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"   ❌ Error testing chat: {e}")
    
    print("\n💡 Next Steps:")
    print("1. If memory query works but chat doesn't reference it:")
    print("   - Check that memory feature is enabled in OpenWebUI settings")
    print("   - Verify backend logs for memory injection")
    print("2. If memory query returns no results:")
    print("   - Check ChromaDB is running and accessible")
    print("   - Verify embeddings model is loaded")
    print("3. Check backend logs: docker logs backend-llm-backend --tail 20")

if __name__ == "__main__":
    test_memory_persistence()
