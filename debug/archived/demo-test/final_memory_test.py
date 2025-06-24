#!/usr/bin/env python3
"""
Final test to verify memory integration after implementing the proper fix.
"""

import asyncio
import httpx
import time

async def final_memory_test():
    """Test the memory integration after the fix."""
    
    print("=" * 60)
    print("FINAL MEMORY INTEGRATION TEST")
    print("=" * 60)
    
    base_url = "http://localhost:8001"
    test_user_id = f"final_test_{int(time.time())}"
    
    try:
        # Test 1: Store context
        print(f"\n1. Storing context for user: {test_user_id}")
        response1 = await send_chat_message(base_url, test_user_id, "Hello, my name is Sarah and I'm a teacher.")
        print(f"   Response: {response1[:100]}...")
        
        # Test 2: Memory recall
        print(f"\n2. Testing memory recall...")
        response2 = await send_chat_message(base_url, test_user_id, "What is my name and profession?")
        print(f"   Response: {response2}")
        
        # Check if memory works
        name_recalled = "Sarah" in response2
        profession_recalled = "teacher" in response2.lower()
        
        print(f"\n   ✅ Name recalled: {name_recalled}")
        print(f"   ✅ Profession recalled: {profession_recalled}")
        
        if name_recalled and profession_recalled:
            print("\n🎉 MEMORY INTEGRATION IS WORKING!")
            return True
        else:
            print("\n⚠️  Memory integration still needs work")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

async def send_chat_message(base_url: str, user_id: str, message: str) -> str:
    """Send a chat message and return the response."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{base_url}/chat",
            json={"user_id": user_id, "message": message},
            timeout=30.0
        )
        if response.status_code == 200:
            return response.json()["response"]
        else:
            raise Exception(f"Request failed: {response.status_code}")

if __name__ == "__main__":
    success = asyncio.run(final_memory_test())
    if success:
        print("\n✅ ALL TESTS PASSED - Memory integration is working correctly!")
    else:
        print("\n❌ TESTS FAILED - Memory integration needs more work")
