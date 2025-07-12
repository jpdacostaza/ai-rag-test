#!/usr/bin/env python3
"""
Simple Duplicate Test
====================

Test duplicate detection with debug logging.
"""

import httpx
import asyncio

async def simple_duplicate_test():
    """Test duplicate detection with debug output."""
    print("🔧 Simple Duplicate Detection Test...")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        user_id = "debug_user_001"
        
        # Test 1: Store first memory
        print("\n📝 Storing first memory...")
        payload1 = {
            "user_id": user_id,
            "content": "My name is Alice and I work as a data scientist",
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
        await asyncio.sleep(2)
        
        # Test 2: Store exact duplicate
        print("\n📝 Storing exact duplicate...")
        payload2 = {
            "user_id": user_id,
            "content": "My name is Alice and I work as a data scientist",  # Exact same
            "source": "test"
        }
        
        response2 = await client.post(
            "http://localhost:8001/api/memory/store_explicit",
            json=payload2
        )
        
        print(f"Response 2: {response2.status_code}")
        if response2.status_code == 200:
            result2 = response2.json()
            print(f"Result 2: {result2}")

if __name__ == "__main__":
    asyncio.run(simple_duplicate_test())
