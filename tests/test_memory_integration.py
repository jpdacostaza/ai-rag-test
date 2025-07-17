#!/usr/bin/env python3
"""
Memory System Test - Prompt & Pipeline Integration
Test memory functionality through both direct prompt and pipeline interfaces
"""

import asyncio
import json
import sys
import os
from datetime import datetime

# Add the project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.memory_service import get_memory_service
from services.database_manager import db_manager

async def test_memory_through_prompt():
    """Test memory system through direct prompt interface"""
    print("🧠 Testing Memory System Through Direct Prompt Interface")
    print("=" * 60)
    
    # Initialize memory service
    memory_service = get_memory_service()
    
    # Test user (Juan-Pierre from handover documentation)
    user_id = "4b00c25b-e55e-4931-a29e-07fc94deebfc"
    
    # Test storage (regular memories)
    print("📝 Testing Regular Memory Storage...")
    test_memories = [
        {
            "content": "I prefer working with Python for data analysis and machine learning projects",
            "context": "Programming preferences discussion",
            "importance": 0.8,
            "explicit": False  # Regular memory, not explicit command
        },
        {
            "content": "My favorite AI framework is TensorFlow, but I also use PyTorch for research",
            "context": "AI frameworks conversation",
            "importance": 0.7,
            "explicit": False  # Regular memory, not explicit command
        },
        {
            "content": "I usually work in VS Code with the Python extension and Copilot",
            "context": "Development environment setup",
            "importance": 0.6,
            "explicit": False  # Regular memory, not explicit command
        }
    ]
    
    stored_count = 0
    for memory in test_memories:
        try:
            success = await memory_service.store_memory(
                user_id=user_id,
                content=memory["content"],
                context=memory["context"],
                importance=memory["importance"],
                explicit=memory["explicit"],
                source="prompt_test"
            )
            if success:
                stored_count += 1
                print(f"  ✅ Stored: {memory['content'][:50]}...")
            else:
                print(f"  ❌ Failed to store: {memory['content'][:50]}...")
        except Exception as e:
            print(f"  ❌ Error storing memory: {str(e)}")
    
    print(f"📊 Regular Storage Results: {stored_count}/{len(test_memories)} memories stored")
    
    # Test explicit memory storage
    print("\n📝 Testing Explicit Memory Storage...")
    explicit_memory = {
        "content": "Remember: I always prefer using async/await patterns in Python code",
        "context": "Explicit memory command from user",
        "importance": 0.9,
        "explicit": True  # This is an explicit memory command
    }
    
    try:
        success = await memory_service.store_memory(
            user_id=user_id,
            content=explicit_memory["content"],
            context=explicit_memory["context"],
            importance=explicit_memory["importance"],
            explicit=explicit_memory["explicit"],
            source="explicit_command"
        )
        if success:
            print(f"  ✅ Explicit memory stored: {explicit_memory['content'][:50]}...")
        else:
            print(f"  ❌ Failed to store explicit memory")
    except Exception as e:
        print(f"  ❌ Error storing explicit memory: {str(e)}")
    
    total_stored = stored_count + (1 if success else 0)
    print(f"📊 Total Storage Results: {total_stored}/{len(test_memories) + 1} memories stored")
    
    # Test retrieval
    print("\n🔍 Testing Memory Retrieval...")
    test_queries = [
        "What programming language do you prefer?",
        "Which AI framework do you use?",
        "What's your development environment?",
        "Tell me about your coding setup"
    ]
    
    for query in test_queries:
        try:
            memories = await memory_service.get_memories(
                user_id=user_id,
                query=query,
                limit=3
            )
            print(f"  📝 Query: {query}")
            print(f"  📊 Found {len(memories)} memories")
            for i, memory in enumerate(memories[:2]):  # Show top 2
                print(f"    {i+1}. {memory.content[:60]}...")
                if hasattr(memory, 'distance') and memory.distance:
                    print(f"       Distance: {memory.distance:.3f}")
            print()
        except Exception as e:
            print(f"  ❌ Error retrieving memories for '{query}': {str(e)}")
    
    # Test conversation tracking
    print("💬 Testing Conversation Tracking...")
    try:
        conversation_success = await memory_service.track_conversation(
            user_id=user_id,
            user_message="How can I improve my Python skills?",
            assistant_response="To improve your Python skills, I recommend practicing with data analysis projects using pandas and numpy, since you mentioned preferring Python for data analysis. You could also explore advanced TensorFlow features since that's your favorite framework.",
            conversation_id="test_conversation_001"
        )
        if conversation_success:
            print("  ✅ Conversation tracked successfully")
        else:
            print("  ❌ Failed to track conversation")
    except Exception as e:
        print(f"  ❌ Error tracking conversation: {str(e)}")
    
    # Test memory stats
    print("\n📊 Testing Memory Statistics...")
    try:
        stats = await memory_service.get_stats(user_id)
        print(f"  Total memories: {stats.total_memories}")
        print(f"  Memory types: {stats.memory_types}")
        if stats.oldest_memory:
            print(f"  Oldest memory: {stats.oldest_memory}")
        if stats.newest_memory:
            print(f"  Newest memory: {stats.newest_memory}")
    except Exception as e:
        print(f"  ❌ Error getting memory stats: {str(e)}")

async def test_memory_through_pipeline():
    """Test memory system through pipeline interface"""
    print("\n🔧 Testing Memory System Through Pipeline Interface")
    print("=" * 60)
    
    # Initialize pipeline memory provider
    from services.memory_service import PipelineMemoryProvider
    pipeline_provider = PipelineMemoryProvider()
    
    # Test pipeline initialization
    print("🚀 Testing Pipeline Initialization...")
    try:
        pipeline = await pipeline_provider._get_pipeline()
        if pipeline:
            print("  ✅ Pipeline initialized successfully")
            
            # Check available methods
            methods = [method for method in dir(pipeline) if not method.startswith('_')]
            print(f"  📝 Available methods: {len(methods)}")
            
            # Look for memory-related methods
            memory_methods = [m for m in methods if 'memory' in m.lower()]
            print(f"  🧠 Memory methods: {memory_methods}")
            
        else:
            print("  ❌ Pipeline initialization failed")
            return
    except Exception as e:
        print(f"  ❌ Error initializing pipeline: {str(e)}")
        return
    
    # Test pipeline storage
    print("\n📝 Testing Pipeline Memory Storage...")
    user_id = "4b00c25b-e55e-4931-a29e-07fc94deebfc"
    
    from services.memory_service import MemoryEntry, MemoryMetadata
    
    pipeline_memory = MemoryEntry(
        content="I enjoy working on memory system architecture and testing different storage providers",
        metadata=MemoryMetadata(
            user_id=user_id,
            timestamp=datetime.now().isoformat(),
            source="pipeline_test",
            importance=0.9,
            memory_type="technical_preference",
            context="Memory system testing"
        )
    )
    
    try:
        success = await pipeline_provider.store_memory(pipeline_memory)
        if success:
            print("  ✅ Pipeline memory storage successful")
        else:
            print("  ❌ Pipeline memory storage failed")
    except Exception as e:
        print(f"  ❌ Error storing memory through pipeline: {str(e)}")
    
    # Test pipeline retrieval
    print("\n🔍 Testing Pipeline Memory Retrieval...")
    from services.memory_service import MemoryQuery
    
    query = MemoryQuery(
        user_id=user_id,
        query="memory system architecture",
        limit=5
    )
    
    try:
        memories = await pipeline_provider.get_memories(query)
        print(f"  📊 Retrieved {len(memories)} memories from pipeline")
        for i, memory in enumerate(memories[:3]):  # Show top 3
            print(f"    {i+1}. {memory.content[:60]}...")
            print(f"       Source: {memory.metadata.source}")
    except Exception as e:
        print(f"  ❌ Error retrieving memories through pipeline: {str(e)}")
    
    # Test pipeline health
    print("\n⚡ Testing Pipeline Health...")
    try:
        health = await pipeline_provider.health_check()
        if health:
            print("  ✅ Pipeline health check passed")
        else:
            print("  ❌ Pipeline health check failed")
    except Exception as e:
        print(f"  ❌ Error checking pipeline health: {str(e)}")

async def test_cross_provider_consistency():
    """Test consistency between different memory providers"""
    print("\n🔄 Testing Cross-Provider Consistency")
    print("=" * 60)
    
    from services.memory_service import APIMemoryProvider, DatabaseMemoryProvider, PipelineMemoryProvider
    
    user_id = "4b00c25b-e55e-4931-a29e-07fc94deebfc"
    test_query = "Python programming"
    
    providers = {
        "API": APIMemoryProvider(),
        "Database": DatabaseMemoryProvider(),
        "Pipeline": PipelineMemoryProvider()
    }
    
    for name, provider in providers.items():
        print(f"\n🔍 Testing {name} Provider...")
        try:
            # Test health
            health = await provider.health_check()
            print(f"  Health: {'✅ OK' if health else '❌ Failed'}")
            
            # Test retrieval
            from services.memory_service import MemoryQuery
            query = MemoryQuery(user_id=user_id, query=test_query, limit=3)
            memories = await provider.get_memories(query)
            print(f"  Memories found: {len(memories)}")
            
            # Test stats
            stats = await provider.get_stats(user_id)
            print(f"  Total memories: {stats.total_memories}")
            
        except Exception as e:
            print(f"  ❌ Error testing {name} provider: {str(e)}")

async def main():
    """Main test function"""
    print("🚀 Memory System Integration Test")
    print("Date:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("=" * 60)
    
    try:
        # Test through prompt interface
        await test_memory_through_prompt()
        
        # Test through pipeline interface
        await test_memory_through_pipeline()
        
        # Test cross-provider consistency
        await test_cross_provider_consistency()
        
        print("\n✅ Memory System Integration Test Completed")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
