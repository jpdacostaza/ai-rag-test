#!/usr/bin/env python3
"""
Simple Redis Test - No Boolean Metadata
========================================

Test explicit memory storage without any boolean values in metadata.
"""

import httpx
import time
import asyncio

# Test configuration
MEMORY_API_URL = "http://localhost:8001"
TEST_USER_ID = "test_simple_redis"

async def test_simple_explicit_storage():
    """Test explicit memory storage without boolean metadata."""
    print("🔧 Testing Simple Explicit Memory Storage (No Booleans)...")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Test explicit memory storage WITHOUT boolean metadata
        payload = {
            "user_id": TEST_USER_ID,
            "content": "Simple test: I like machine learning and data science!",
            "source": "simple_test",
            # NO metadata to avoid any boolean issues
        }
        
        print(f"📝 Storing simple explicit memory...")
        response = await client.post(
            f"{MEMORY_API_URL}/api/memory/store_explicit",
            json=payload
        )
        
        if response.status_code == 200:
            print("✅ Simple explicit memory storage successful!")
            result = response.json()
            print(f"📄 Result: {result}")
            return True
        else:
            print(f"❌ Simple explicit memory storage failed: HTTP {response.status_code}")
            print(f"📄 Response: {response.text}")
            return False

async def main():
    """Run simple test."""
    print("🚀 Starting Simple Redis Test (No Boolean Metadata)...\n")
    
    result = await test_simple_explicit_storage()
    
    print(f"\n📊 Result: {'✅ SUCCESS' if result else '❌ FAILED'}")
    
    if result:
        print("\n🎉 Simple test passed! No boolean metadata issues.")
    else:
        print("\n⚠️ Simple test failed. Check logs for details.")

if __name__ == "__main__":
    asyncio.run(main())
