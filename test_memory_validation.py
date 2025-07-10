#!/usr/bin/env python3
"""
Test memory service integration to verify MemoryRecord validation fix
"""
import asyncio
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, '/app')

from memory.core.client import MemoryClient
from memory.core.models import MemoryConfig, MemoryQuery, MemoryRecord

async def test_memory_integration():
    """Test the memory service integration"""
    print("🧪 Testing memory service integration...")
    
    # Create memory client
    config = MemoryConfig(
        api_url="http://memory_api:8080",
        timeout=10.0
    )
    client = MemoryClient(config)
    
    # Test memory retrieval for J.P.
    print("🔍 Testing memory retrieval for user J.P....")
    query = MemoryQuery(
        user_id="J.P.",
        query_text="Swift developer Apple",
        limit=5,
        threshold=0.01
    )
    
    try:
        response = await client.get_memories(query)
        print(f"✅ Memory retrieval successful: {response.success}")
        print(f"📝 Retrieved {len(response.memories)} memories")
        
        for i, memory in enumerate(response.memories):
            print(f"  {i+1}. {memory.user_id}: {memory.content[:50]}...")
            
        if response.error:
            print(f"⚠️ Error: {response.error}")
            
    except Exception as e:
        print(f"❌ Memory retrieval failed: {e}")
        
    print("🧪 Test completed")

if __name__ == "__main__":
    asyncio.run(test_memory_integration())
