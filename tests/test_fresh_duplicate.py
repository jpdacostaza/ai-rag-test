#!/usr/bin/env python3
"""
Fresh Duplicate Test
===================

Test duplicate detection with a completely fresh user.
"""

import httpx
import asyncio

async def fresh_test():
    """Test with a brand new user."""
    print("🔧 Fresh Duplicate Detection Test...")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        user_id = "fresh_test_user_999"
        
        # Test 1: Store first memory
        print("\n📝 Storing first memory...")
        payload1 = {
            "user_id": user_id,
            "content": "Test content for duplicate detection",
            "source": "test"
        }
        
        response1 = await client.post(
            "http://localhost:8001/api/memory/store_explicit",
            json=payload1
        )
        
        print(f"Response 1: {response1.status_code}")
        if response1.status_code == 200:
            result1 = response1.json()
            print(f"Result 1: {result1}")
        
        # Wait a moment
        await asyncio.sleep(3)
        
        # Test 2: Store exact duplicate
        print("\n📝 Storing exact duplicate...")
        response2 = await client.post(
            "http://localhost:8001/api/memory/store_explicit",
            json=payload1  # Exact same payload
        )
        
        print(f"Response 2: {response2.status_code}")
        if response2.status_code == 200:
            result2 = response2.json()
            print(f"Result 2: {result2}")

if __name__ == "__main__":
    asyncio.run(fresh_test())
