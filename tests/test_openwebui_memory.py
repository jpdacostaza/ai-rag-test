#!/usr/bin/env python3
"""
Test OpenWebUI Memory Integration
Test to simulate OpenWebUI memory function integration and verify functionality.
"""

import requests
import json
import time

# Configuration
MEMORY_API_URL = "http://localhost:5001"
USER_ID = "test_user"

def test_memory_store(content, context=""):
    """Test memory storage"""
    print(f"🔄 Storing memory: {content[:50]}...")
    
    memory_data = {
        "content": content,
        "user_id": USER_ID,
        "context": context
    }
    
    try:
        response = requests.post(
            f"{MEMORY_API_URL}/api/memory/store",
            json=memory_data,
            timeout=5
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Memory stored successfully: {result.get('memory_id')}")
            return True
        else:
            print(f"❌ Memory storage failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Memory storage error: {str(e)}")
        return False

def test_memory_retrieve(query):
    """Test memory retrieval"""
    print(f"🔍 Retrieving memories for query: {query}")
    
    memory_request = {
        "query": query,
        "user_id": USER_ID,
        "limit": 5
    }
    
    try:
        response = requests.post(
            f"{MEMORY_API_URL}/api/memory/retrieve",
            json=memory_request,
            timeout=5
        )
        
        if response.status_code == 200:
            result = response.json()
            memories = result.get("memories", [])
            print(f"✅ Retrieved {len(memories)} memories")
            
            for i, memory in enumerate(memories, 1):
                content = memory.get("content", "")[:60]
                similarity = memory.get("similarity", 0)
                print(f"   {i}. {content}... (similarity: {similarity:.3f})")
            
            return memories
        else:
            print(f"❌ Memory retrieval failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return []
            
    except Exception as e:
        print(f"❌ Memory retrieval error: {str(e)}")
        return []

def main():
    print("🚀 Testing OpenWebUI Memory Integration")
    print("=" * 50)
    
    # Test storing various types of memories
    test_memories = [
        "My name is Alice and I work as a software engineer",
        "I enjoy hiking and outdoor activities on weekends",  
        "My favorite programming language is Python",
        "I have a cat named Whiskers",
        "I live in Seattle and love the coffee culture here"
    ]
    
    print("\n📝 Testing Memory Storage:")
    success_count = 0
    for memory in test_memories:
        if test_memory_store(memory):
            success_count += 1
        time.sleep(0.1)  # Small delay between requests
    
    print(f"\n📊 Storage Results: {success_count}/{len(test_memories)} successful")
    
    if success_count == 0:
        print("❌ No memories stored successfully. Cannot test retrieval.")
        return
    
    print("\n🔍 Testing Memory Retrieval:")
    test_queries = [
        "What is my name?",
        "What do I do for work?",
        "What are my hobbies?",
        "Do I have any pets?",
        "Where do I live?",
        "What is my favorite programming language?"
    ]
    
    retrieval_count = 0
    for query in test_queries:
        memories = test_memory_retrieve(query)
        if memories:
            retrieval_count += 1
        print()  # Add spacing
        time.sleep(0.1)  # Small delay between requests
    
    print(f"📊 Retrieval Results: {retrieval_count}/{len(test_queries)} successful")
    
    # Summary
    print("\n" + "=" * 50)
    if success_count > 0 and retrieval_count > 0:
        print("🎉 OpenWebUI Memory Integration: WORKING!")
        print("✅ Memory storage: SUCCESS")
        print("✅ Memory retrieval: SUCCESS")
        print("✅ The memory system should now work in OpenWebUI")
    else:
        print("❌ OpenWebUI Memory Integration: FAILED")
        if success_count == 0:
            print("❌ Memory storage issues detected")
        if retrieval_count == 0:
            print("❌ Memory retrieval issues detected")

if __name__ == "__main__":
    main()
