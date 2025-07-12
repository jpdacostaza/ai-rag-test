#!/usr/bin/env python3
"""
Test Redis Storage Fix
======================

Test to verify that the Redis storage boolean issue has been resolved.
"""

import httpx
import time
import asyncio
import json

# Test configuration
MEMORY_API_URL = "http://localhost:8001"
TEST_USER_ID = "test_user_redis_fix"

async def test_explicit_memory_storage():
    """Test explicit memory storage with boolean values."""
    print("🔧 Testing Redis Boolean Storage Fix...")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Test explicit memory storage
        payload = {
            "user_id": TEST_USER_ID,
            "content": "Remember this test: I love Python programming and AI development!",
            "source": "test_explicit_command",
            "metadata": {
                "priority": "high",
                "explicit": True,
                "test": True,
                "timestamp": time.time()
            }
        }
        
        print(f"📝 Storing explicit memory for user {TEST_USER_ID}...")
        response = await client.post(
            f"{MEMORY_API_URL}/api/memory/store_explicit",
            json=payload
        )
        
        if response.status_code == 200:
            print("✅ Explicit memory storage successful!")
            result = response.json()
            print(f"📄 Storage result: {result}")
        else:
            print(f"❌ Explicit memory storage failed: HTTP {response.status_code}")
            print(f"📄 Response: {response.text}")
            return False
        
        # Wait a moment for storage to complete
        await asyncio.sleep(2)
        
        # Test memory retrieval
        retrieve_payload = {
            "user_id": TEST_USER_ID,
            "query": "Python programming AI development",
            "limit": 10,
            "threshold": 0.0
        }
        
        print(f"🔍 Retrieving memories for user {TEST_USER_ID}...")
        response = await client.post(
            f"{MEMORY_API_URL}/api/memory/retrieve",
            json=retrieve_payload
        )
        
        if response.status_code == 200:
            result = response.json()
            memories = result.get("memories", [])
            print(f"✅ Memory retrieval successful! Found {len(memories)} memories")
            
            # Check if our explicit memory is there
            for memory in memories:
                if "Python programming" in memory.get("content", ""):
                    print(f"🎯 Found our explicit memory: {memory.get('content', '')}")
                    metadata = memory.get("metadata", {})
                    print(f"📊 Memory metadata: {metadata}")
                    
                    # Check if explicit flag is preserved
                    if metadata.get("explicit") or metadata.get("type") == "explicit":
                        print("✅ Explicit flag preserved correctly!")
                        return True
                    else:
                        print("⚠️ Explicit flag not found in metadata")
            
            print("⚠️ Test memory not found in retrieval results")
            return False
        else:
            print(f"❌ Memory retrieval failed: HTTP {response.status_code}")
            print(f"📄 Response: {response.text}")
            return False

async def test_regular_memory_storage():
    """Test regular memory storage."""
    print("\n🔧 Testing Regular Memory Storage...")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Test regular interaction processing
        payload = {
            "user_id": TEST_USER_ID,
            "conversation_id": "test_conv_redis_fix",
            "user_message": "I work as a software engineer at TechCorp",
            "assistant_response": "That's great! I'll remember that you work as a software engineer at TechCorp.",
            "source": "test_interaction"
        }
        
        print(f"📝 Processing interaction for user {TEST_USER_ID}...")
        response = await client.post(
            f"{MEMORY_API_URL}/api/learning/process_interaction",
            json=payload
        )
        
        if response.status_code == 200:
            print("✅ Interaction processing successful!")
            result = response.json()
            print(f"📄 Processing result: {result}")
            return True
        else:
            print(f"❌ Interaction processing failed: HTTP {response.status_code}")
            print(f"📄 Response: {response.text}")
            return False

async def main():
    """Run all tests."""
    print("🚀 Starting Redis Storage Fix Tests...\n")
    
    explicit_test = await test_explicit_memory_storage()
    regular_test = await test_regular_memory_storage()
    
    print(f"\n📊 Test Results:")
    print(f"   Explicit Memory Storage: {'✅ PASS' if explicit_test else '❌ FAIL'}")
    print(f"   Regular Memory Storage:  {'✅ PASS' if regular_test else '❌ FAIL'}")
    
    if explicit_test and regular_test:
        print("\n🎉 All tests passed! Redis storage boolean issue has been fixed!")
    else:
        print("\n⚠️ Some tests failed. Please check the logs for more details.")

if __name__ == "__main__":
    asyncio.run(main())
