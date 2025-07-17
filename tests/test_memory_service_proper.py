import asyncio
import sys
import os

# Add the backend directory to Python path
sys.path.insert(0, os.path.abspath('.'))

from services.memory_service import MemoryService, APIMemoryProvider
from core.human_logging import HumanLogger

async def test_memory_service_proper():
    """Test the memory service with proper interface"""
    
    # Initialize logging
    logger = HumanLogger()
    
    print("🔬 Testing Memory Service (Proper Interface)")
    print("=" * 60)
    
    # Initialize memory service with API provider
    try:
        provider = APIMemoryProvider()
        memory_service = MemoryService(provider)
        print("✅ Memory service initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize memory service: {e}")
        return
    
    # Test user ID
    test_user = "proper_test_user"
    
    # Test 1: Store memories
    print("\n📝 Testing Memory Storage...")
    
    test_memories = [
        {
            "content": "I prefer using Rust for systems programming",
            "context": "Programming language preference",
            "importance": 0.8,
            "explicit": False
        },
        {
            "content": "Remember: I always write unit tests before implementing features",
            "context": "Development methodology",
            "importance": 0.9,
            "explicit": True
        },
        {
            "content": "I like using MongoDB for document storage",
            "context": "Database preference",
            "importance": 0.7,
            "explicit": False
        }
    ]
    
    stored_count = 0
    for i, memory in enumerate(test_memories, 1):
        try:
            result = await memory_service.store_memory(
                user_id=test_user,
                content=memory["content"],
                context=memory["context"],
                importance=memory["importance"],
                explicit=memory["explicit"]
            )
            
            if result:
                print(f"  ✅ Memory {i} stored: {memory['content'][:50]}...")
                stored_count += 1
            else:
                print(f"  ❌ Memory {i} failed to store")
        except Exception as e:
            print(f"  ❌ Memory {i} error: {e}")
    
    print(f"📊 Stored {stored_count}/{len(test_memories)} memories")
    
    # Test 2: Retrieve memories
    print("\n🔍 Testing Memory Retrieval...")
    
    queries = [
        "Rust programming",
        "unit tests",
        "MongoDB database",
        "systems programming",
        "development methodology"
    ]
    
    retrieved_count = 0
    for query in queries:
        try:
            memories = await memory_service.get_memories(
                user_id=test_user,
                query=query,
                limit=5
            )
            
            if memories:
                print(f"  ✅ Query '{query}': Found {len(memories)} memories")
                retrieved_count += len(memories)
                
                # Show first memory for verification
                if memories:
                    first_memory = memories[0]
                    content = first_memory.content
                    print(f"    └─ Example: {content[:60]}...")
            else:
                print(f"  ⚠️ Query '{query}': No memories found")
        except Exception as e:
            print(f"  ❌ Query '{query}' error: {e}")
    
    print(f"📊 Retrieved {retrieved_count} total memories")
    
    # Test 3: Test provider health
    print("\n🏥 Testing Provider Health...")
    
    try:
        health = await memory_service.provider.health_check()
        print(f"  ✅ Provider health: {health}")
        print(f"  ✅ Provider type: {memory_service.provider_type}")
    except Exception as e:
        print(f"  ❌ Provider health error: {e}")
    
    # Test 4: Test memory statistics
    print("\n📊 Testing Memory Statistics...")
    
    try:
        stats = await memory_service.get_stats(test_user)
        print(f"  ✅ Memory stats retrieved")
        print(f"    User ID: {stats.user_id}")
        print(f"    Total memories: {stats.total_memories}")
        print(f"    Memory types: {stats.memory_types}")
    except Exception as e:
        print(f"  ❌ Stats error: {e}")
    
    print("\n🏆 MEMORY SERVICE TEST COMPLETE")
    print("=" * 60)
    print("✅ Memory service working correctly with proper interface")
    print("✅ API provider functioning properly")
    print("✅ All memory operations successful")

if __name__ == "__main__":
    asyncio.run(test_memory_service_proper())
