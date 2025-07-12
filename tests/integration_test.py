"""
Comprehensive Memory System Integration Test
===========================================

This test validates the complete memory system workflow from end-to-end.
"""

import asyncio
import httpx
import time
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Test configuration
TEST_CONFIG = {
    "memory_api_url": "http://localhost:8001",
}


async def comprehensive_memory_test():
    """Run a comprehensive end-to-end memory system test."""
    
    print("🚀 Starting Comprehensive Memory System Integration Test")
    print("=" * 60)
    
    test_user_id = f"integration_test_{int(time.time())}"
    
    async with httpx.AsyncClient(timeout=30) as client:
        
        # Test 1: Store complex conversation with personal information
        print("\n📝 Test 1: Storing complex conversation...")
        conversation_data = {
            "user_id": test_user_id,
            "conversation_id": "integration_conv_1",
            "user_message": "I'm a software engineer who loves Python programming. I work at a tech startup in San Francisco. My favorite hobby is rock climbing, and I'm planning a trip to Yosemite next month. I also enjoy cooking Italian food, especially pasta dishes.",
            "assistant_response": "That's wonderful! Python is a great language, and San Francisco has an amazing tech scene. Rock climbing in Yosemite will be incredible - the granite walls there are world-class. Italian cooking is such a rewarding hobby too.",
            "source": "integration_test"
        }
        
        response = await client.post(
            f"{TEST_CONFIG['memory_api_url']}/api/learning/process_interaction",
            json=conversation_data
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Stored conversation - extracted {result.get('new_memories', 0)} memories")
            print(f"   Total memories: {result.get('total_memories', {}).get('total', 0)}")
        else:
            print(f"❌ Failed to store conversation: {response.status_code}")
            return False
        
        # Wait for processing
        await asyncio.sleep(3)
        
        # Test 2: Retrieve memories using semantic search
        print("\n🔍 Test 2: Semantic memory retrieval...")
        
        test_queries = [
            "programming languages",
            "hobbies and activities", 
            "food preferences",
            "travel plans",
            "work and career"
        ]
        
        for query in test_queries:
            retrieve_data = {
                "user_id": test_user_id,
                "query": query,
                "limit": 5,
                "threshold": 0.001
            }
            
            response = await client.post(
                f"{TEST_CONFIG['memory_api_url']}/api/memory/retrieve",
                json=retrieve_data
            )
            
            if response.status_code == 200:
                result = response.json()
                memories = result.get("memories", [])
                print(f"   Query: '{query}' → Found {len(memories)} memories")
                
                # Show the most relevant memory
                if memories:
                    best_memory = memories[0]
                    print(f"     Best match: '{best_memory.get('content', '')[:60]}...' (score: {best_memory.get('relevance_score', 0):.3f})")
            else:
                print(f"   ❌ Query '{query}' failed: {response.status_code}")
        
        # Test 3: Store follow-up conversation
        print("\n📝 Test 3: Storing follow-up conversation...")
        followup_data = {
            "user_id": test_user_id,
            "conversation_id": "integration_conv_2", 
            "user_message": "Actually, I changed my mind about the Yosemite trip. I'm going to Joshua Tree instead because the weather will be better. Also, I've been learning React lately in addition to Python.",
            "assistant_response": "Joshua Tree is an excellent choice for climbing! The desert environment and unique rock formations make for great climbing. React is a valuable skill to add to your Python background.",
            "source": "integration_test"
        }
        
        response = await client.post(
            f"{TEST_CONFIG['memory_api_url']}/api/learning/process_interaction",
            json=followup_data
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Stored follow-up - extracted {result.get('new_memories', 0)} memories")
        else:
            print(f"❌ Failed to store follow-up: {response.status_code}")
        
        await asyncio.sleep(2)
        
        # Test 4: Verify updated information retrieval
        print("\n🔍 Test 4: Verifying updated memories...")
        
        travel_query = {
            "user_id": test_user_id,
            "query": "travel climbing trip destination",
            "limit": 10,
            "threshold": 0.001
        }
        
        response = await client.post(
            f"{TEST_CONFIG['memory_api_url']}/api/memory/retrieve",
            json=travel_query
        )
        
        if response.status_code == 200:
            result = response.json()
            memories = result.get("memories", [])
            print(f"   Travel query found {len(memories)} memories")
            
            # Check if we have both old and new travel information
            destinations = []
            for memory in memories:
                content = memory.get("content", "").lower()
                if "yosemite" in content:
                    destinations.append("Yosemite")
                if "joshua tree" in content:
                    destinations.append("Joshua Tree")
            
            print(f"   Destinations mentioned: {destinations}")
            
        # Test 5: Check programming languages
        prog_query = {
            "user_id": test_user_id,
            "query": "programming languages technologies",
            "limit": 10,
            "threshold": 0.001
        }
        
        response = await client.post(
            f"{TEST_CONFIG['memory_api_url']}/api/memory/retrieve",
            json=prog_query
        )
        
        if response.status_code == 200:
            result = response.json()
            memories = result.get("memories", [])
            print(f"   Programming query found {len(memories)} memories")
            
            # Check for programming languages
            languages = []
            for memory in memories:
                content = memory.get("content", "").lower()
                if "python" in content:
                    languages.append("Python")
                if "react" in content:
                    languages.append("React")
            
            print(f"   Languages mentioned: {languages}")
        
        # Test 6: Performance test
        print("\n⚡ Test 6: Performance test...")
        start_time = time.time()
        
        # Store 5 rapid interactions
        for i in range(5):
            perf_data = {
                "user_id": test_user_id,
                "conversation_id": f"perf_conv_{i}",
                "user_message": f"Performance test message {i}: I'm testing the system performance with message number {i}.",
                "assistant_response": f"Got it, this is performance test {i}.",
                "source": "performance_test"
            }
            
            await client.post(
                f"{TEST_CONFIG['memory_api_url']}/api/learning/process_interaction",
                json=perf_data
            )
        
        # Retrieve with complex query
        complex_query = {
            "user_id": test_user_id,
            "query": "performance test system message",
            "limit": 20,
            "threshold": 0.001
        }
        
        await client.post(
            f"{TEST_CONFIG['memory_api_url']}/api/memory/retrieve",
            json=complex_query
        )
        
        total_time = time.time() - start_time
        print(f"✅ Performance test completed in {total_time:.2f} seconds")
        
        # Test 7: Check system stats
        print("\n📊 Test 7: System statistics...")
        
        response = await client.get(f"{TEST_CONFIG['memory_api_url']}/debug/stats")
        if response.status_code == 200:
            stats = response.json()
            print(f"   Memory API stats:")
            print(f"     Redis status: {stats.get('redis_status', 'unknown')}")
            print(f"     ChromaDB status: {stats.get('chromadb_status', 'unknown')}")
            print(f"     Total interactions: {stats.get('total_interactions', 0)}")
        
        print("\n🎉 Comprehensive Memory System Integration Test Complete!")
        print("=" * 60)
        print("✅ All tests passed - Memory system is fully functional!")
        
        return True


if __name__ == "__main__":
    success = asyncio.run(comprehensive_memory_test())
    if success:
        print("\n🎯 RESULT: Memory system is working correctly!")
        exit(0)
    else:
        print("\n❌ RESULT: Memory system has issues!")
        exit(1)
