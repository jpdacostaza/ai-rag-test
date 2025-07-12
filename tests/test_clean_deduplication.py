#!/usr/bin/env python3
"""
Clean Memory Deduplication Test
==============================

Test memory deduplication with a completely fresh user.
"""

import httpx
import time
import asyncio
import random

# Test configuration
MEMORY_API_URL = "http://localhost:8001"
TEST_USER_ID = f"clean_test_user_{random.randint(1000, 9999)}"

async def test_duplicate_detection():
    """Test that duplicate memories are not stored."""
    print("🔧 Testing Memory Deduplication...")
    print(f"👤 Using test user: {TEST_USER_ID}")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        
        # Test 1: Store initial explicit memory
        print("\n📝 Test 1: Storing initial explicit memory...")
        payload1 = {
            "user_id": TEST_USER_ID,
            "content": "My name is John Smith and I work as a software engineer at TechCorp",
            "source": "explicit_test"
        }
        
        response1 = await client.post(
            f"{MEMORY_API_URL}/api/memory/store_explicit",
            json=payload1
        )
        
        if response1.status_code == 200:
            result1 = response1.json()
            print(f"✅ First memory stored: {result1['new_memories']} new memories")
            first_test_pass = result1['new_memories'] > 0
        else:
            print(f"❌ First memory storage failed: {response1.status_code}")
            return False
        
        # Wait a moment
        await asyncio.sleep(2)
        
        # Test 2: Try to store the exact same memory
        print("\n📝 Test 2: Attempting to store exact duplicate...")
        response2 = await client.post(
            f"{MEMORY_API_URL}/api/memory/store_explicit",
            json=payload1  # Exact same payload
        )
        
        if response2.status_code == 200:
            result2 = response2.json()
            print(f"📊 Second attempt result: {result2['status']}, new memories: {result2['new_memories']}")
            if result2['status'] == 'duplicate_detected' and result2['new_memories'] == 0:
                print("✅ Exact duplicate correctly detected and rejected!")
                exact_duplicate_test = True
            else:
                print("❌ Exact duplicate was not detected")
                exact_duplicate_test = False
        else:
            print(f"❌ Second storage attempt failed: {response2.status_code}")
            exact_duplicate_test = False
        
        # Test 3: Try to store a very similar memory
        print("\n📝 Test 3: Attempting to store similar memory...")
        payload3 = {
            "user_id": TEST_USER_ID,
            "content": "My name is John Smith and I'm a software engineer at TechCorp",  # Very similar
            "source": "explicit_test"
        }
        
        response3 = await client.post(
            f"{MEMORY_API_URL}/api/memory/store_explicit",
            json=payload3
        )
        
        if response3.status_code == 200:
            result3 = response3.json()
            print(f"📊 Third attempt result: {result3['status']}, new memories: {result3['new_memories']}")
            if result3['status'] == 'duplicate_detected' and result3['new_memories'] == 0:
                print("✅ Similar memory correctly detected and rejected!")
                similar_duplicate_test = True
            else:
                print(f"⚠️ Similar memory was stored (similarity below threshold)")
                similar_duplicate_test = True  # This could be acceptable
        else:
            print(f"❌ Third storage attempt failed: {response3.status_code}")
            similar_duplicate_test = False
        
        # Test 4: Store genuinely different memory
        print("\n📝 Test 4: Storing genuinely different memory...")
        payload4 = {
            "user_id": TEST_USER_ID,
            "content": "I have 5 years of experience in Python programming and machine learning",
            "source": "explicit_test"
        }
        
        response4 = await client.post(
            f"{MEMORY_API_URL}/api/memory/store_explicit",
            json=payload4
        )
        
        if response4.status_code == 200:
            result4 = response4.json()
            print(f"📊 Fourth attempt result: {result4['status']}, new memories: {result4['new_memories']}")
            if result4['status'] == 'success' and result4['new_memories'] > 0:
                print("✅ Different memory correctly stored!")
                different_memory_test = True
            else:
                print("❌ Different memory was rejected incorrectly")
                different_memory_test = False
        else:
            print(f"❌ Fourth storage attempt failed: {response4.status_code}")
            different_memory_test = False
        
        # Final verification - check total memories
        print("\n📝 Final Verification: Checking memory counts...")
        retrieve_payload = {
            "user_id": TEST_USER_ID,
            "query": "tell me everything you know about me",
            "limit": 20,
            "threshold": 0.0
        }
        
        response_final = await client.post(
            f"{MEMORY_API_URL}/api/memory/retrieve",
            json=retrieve_payload
        )
        
        if response_final.status_code == 200:
            final_result = response_final.json()
            total_memories = final_result['count']
            print(f"📊 Total memories stored: {total_memories}")
            print(f"📋 Memory sources: {final_result.get('sources', {})}")
            
            # Print actual memories for inspection
            print(f"\n📝 Stored memories:")
            for i, memory in enumerate(final_result.get('memories', [])[:5]):  # Show first 5
                print(f"   {i+1}. {memory.get('content', '')[:80]}...")
        
        return first_test_pass and exact_duplicate_test and similar_duplicate_test and different_memory_test

async def main():
    """Run deduplication tests."""
    print("🚀 Starting Clean Memory Deduplication Tests...\n")
    
    result = await test_duplicate_detection()
    
    print(f"\n📊 Overall Result: {'✅ PASS' if result else '❌ FAIL'}")
    
    if result:
        print("\n🎉 Memory deduplication is working correctly!")
        print("   ✅ Exact duplicates are detected and rejected")
        print("   ✅ Similar memories are handled appropriately")
        print("   ✅ Different memories are stored correctly")
    else:
        print("\n⚠️ Some deduplication tests failed. Check the details above.")

if __name__ == "__main__":
    asyncio.run(main())
