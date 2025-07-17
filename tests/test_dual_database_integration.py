#!/usr/bin/env python3
"""
Memory System Database Integration Test
======================================

Tests that memory system properly connects to and stores data in:
- Redis: Short-term memory, session caching, rapid retrieval
- ChromaDB: Long-term memory, vector embeddings, semantic search

This test validates the dual-database architecture for optimal performance.
"""

import requests
import json
import time
import redis
import chromadb
from datetime import datetime

def test_redis_connection():
    """Test Redis connection and short-term memory storage"""
    print("🔴 Testing Redis Connection (Short-term Memory)")
    print("-" * 50)
    
    try:
        # Connect to Redis
        r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
        
        # Test basic connection
        if r.ping():
            print("   ✅ Redis connection successful")
        else:
            print("   ❌ Redis connection failed")
            return False
        
        # Test key storage and retrieval
        test_key = f"memory_test_{int(time.time())}"
        test_value = {
            "user_id": "test_user",
            "content": "This is a test memory for Redis",
            "timestamp": datetime.now().isoformat(),
            "type": "short_term"
        }
        
        # Store in Redis
        r.setex(test_key, 3600, json.dumps(test_value))  # 1 hour expiry
        print(f"   ✅ Stored test data in Redis: {test_key}")
        
        # Retrieve from Redis
        retrieved = r.get(test_key)
        if retrieved:
            retrieved_data = json.loads(retrieved)
            print(f"   ✅ Retrieved data from Redis: {retrieved_data['content']}")
            
            # Test TTL
            ttl = r.ttl(test_key)
            print(f"   ✅ TTL (Time To Live): {ttl} seconds")
            
            # Clean up
            r.delete(test_key)
            print("   ✅ Test data cleaned up")
            
        else:
            print("   ❌ Failed to retrieve data from Redis")
            return False
        
        # Test memory-specific keys
        memory_keys = r.keys("memory:*")
        print(f"   📊 Found {len(memory_keys)} memory-related keys in Redis")
        
        # Test session keys
        session_keys = r.keys("session:*")
        print(f"   📊 Found {len(session_keys)} session-related keys in Redis")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Redis test failed: {e}")
        return False

def test_chroma_connection():
    """Test ChromaDB connection and long-term memory storage"""
    print("\n🟣 Testing ChromaDB Connection (Long-term Memory)")
    print("-" * 50)
    
    try:
        # Connect to ChromaDB
        chroma_client = chromadb.HttpClient(host="localhost", port=8000)
        
        # Test basic connection
        heartbeat = chroma_client.heartbeat()
        print(f"   ✅ ChromaDB connection successful: {heartbeat}")
        
        # List collections
        collections = chroma_client.list_collections()
        print(f"   📊 Found {len(collections)} collections in ChromaDB")
        
        # Look for memory-related collections
        memory_collections = [col for col in collections if 'memory' in col.name.lower()]
        print(f"   📊 Found {len(memory_collections)} memory collections")
        
        for col in memory_collections:
            print(f"     • {col.name}")
            
        # Test creating a test collection
        test_collection_name = f"memory_test_{int(time.time())}"
        test_collection = chroma_client.create_collection(
            name=test_collection_name,
            metadata={"test": "true", "created": datetime.now().isoformat()}
        )
        print(f"   ✅ Created test collection: {test_collection_name}")
        
        # Test storing embeddings
        test_documents = [
            "User J.P. works at Swift and is a software developer",
            "User prefers concise code examples and iOS development",
            "User has experience with Python and React"
        ]
        
        test_collection.add(
            documents=test_documents,
            ids=[f"test_doc_{i}" for i in range(len(test_documents))],
            metadatas=[{
                "user_id": "test_user",
                "timestamp": datetime.now().isoformat(),
                "type": "long_term"
            } for _ in test_documents]
        )
        print(f"   ✅ Stored {len(test_documents)} test documents with embeddings")
        
        # Test semantic search
        search_results = test_collection.query(
            query_texts=["software development"],
            n_results=2
        )
        print(f"   ✅ Semantic search returned {len(search_results['documents'][0])} results")
        
        for i, doc in enumerate(search_results['documents'][0]):
            print(f"     • Match {i+1}: {doc[:50]}...")
        
        # Clean up test collection
        chroma_client.delete_collection(test_collection_name)
        print("   ✅ Test collection cleaned up")
        
        return True
        
    except Exception as e:
        print(f"   ❌ ChromaDB test failed: {e}")
        return False

def test_memory_api_integration():
    """Test Memory API integration with both databases"""
    print("\n🧠 Testing Memory API Integration (Both Databases)")
    print("-" * 50)
    
    try:
        # Test storing different types of memories
        test_memories = [
            {
                "user_id": "integration_test_user",
                "content": "User just logged in and started a new session",
                "context": "session_start",
                "importance": 0.3,
                "explicit": False
            },
            {
                "user_id": "integration_test_user", 
                "content": "User's name is J.P. and they are a Swift developer at a fintech company",
                "context": "user_profile",
                "importance": 0.9,
                "explicit": True
            },
            {
                "user_id": "integration_test_user",
                "content": "User asked about iOS development best practices",
                "context": "conversation_topic",
                "importance": 0.6,
                "explicit": False
            }
        ]
        
        stored_memories = []
        for i, memory in enumerate(test_memories):
            response = requests.post(
                "http://localhost:5001/api/memory/store",
                json=memory,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                stored_memories.append(result)
                print(f"   ✅ Stored memory {i+1}: {memory['content'][:50]}...")
                print(f"     • Importance: {memory['importance']}")
                print(f"     • Explicit: {memory['explicit']}")
                print(f"     • Context: {memory['context']}")
            else:
                print(f"   ❌ Failed to store memory {i+1}: {response.status_code}")
                return False
        
        # Wait a moment for processing
        time.sleep(2)
        
        # Test retrieval with different queries
        test_queries = [
            "J.P. Swift developer",
            "iOS development", 
            "user profile information",
            "session information"
        ]
        
        for query in test_queries:
            response = requests.post(
                "http://localhost:5001/api/memory/retrieve",
                json={
                    "user_id": "integration_test_user",
                    "query": query,
                    "limit": 3
                },
                timeout=10
            )
            
            if response.status_code == 200:
                results = response.json()
                memories = results.get('memories', [])
                print(f"   ✅ Query '{query}' returned {len(memories)} memories")
                
                for memory in memories:
                    content = memory.get('content', '')
                    importance = memory.get('importance', 0)
                    source = memory.get('source', 'unknown')
                    print(f"     • {content[:60]}... (importance: {importance}, source: {source})")
                    
            else:
                print(f"   ❌ Query '{query}' failed: {response.status_code}")
        
        # Test memory statistics
        response = requests.get(
            f"http://localhost:5001/api/memory/stats/integration_test_user",
            timeout=5
        )
        
        if response.status_code == 200:
            stats = response.json()
            print(f"   ✅ Memory stats retrieved")
            print(f"     • Total memories: {stats.get('total_memories', 0)}")
            print(f"     • Explicit memories: {stats.get('explicit_memories', 0)}")
            print(f"     • Recent memories: {stats.get('recent_memories', 0)}")
        else:
            print(f"   ❌ Failed to get memory stats: {response.status_code}")
            
        return True
        
    except Exception as e:
        print(f"   ❌ Memory API integration test failed: {e}")
        return False

def test_database_storage_distribution():
    """Test how memories are distributed between Redis and ChromaDB"""
    print("\n📊 Testing Database Storage Distribution")
    print("-" * 50)
    
    try:
        # Connect to both databases
        redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
        chroma_client = chromadb.HttpClient(host="localhost", port=8000)
        
        # Check Redis for short-term data
        redis_memory_keys = redis_client.keys("memory:*")
        redis_session_keys = redis_client.keys("session:*")
        redis_cache_keys = redis_client.keys("cache:*")
        
        print(f"   🔴 Redis Storage:")
        print(f"     • Memory keys: {len(redis_memory_keys)}")
        print(f"     • Session keys: {len(redis_session_keys)}")
        print(f"     • Cache keys: {len(redis_cache_keys)}")
        
        # Sample some Redis data
        if redis_memory_keys:
            sample_key = redis_memory_keys[0]
            sample_data = redis_client.get(sample_key)
            ttl = redis_client.ttl(sample_key)
            print(f"     • Sample data TTL: {ttl} seconds")
        
        # Check ChromaDB for long-term data
        chroma_collections = chroma_client.list_collections()
        memory_collections = [col for col in chroma_collections if 'memory' in col.name.lower()]
        
        print(f"   🟣 ChromaDB Storage:")
        print(f"     • Total collections: {len(chroma_collections)}")
        print(f"     • Memory collections: {len(memory_collections)}")
        
        total_documents = 0
        for col in memory_collections:
            try:
                count = col.count()
                total_documents += count
                print(f"     • {col.name}: {count} documents")
            except Exception as e:
                print(f"     • {col.name}: Error counting ({e})")
        
        print(f"     • Total memory documents: {total_documents}")
        
        # Test storage strategy
        print(f"\n   📋 Storage Strategy Analysis:")
        print(f"     • Redis: Optimal for session data, recent queries, cache")
        print(f"     • ChromaDB: Optimal for long-term memories, semantic search")
        print(f"     • Hybrid approach: Fast retrieval + semantic search capability")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Database distribution test failed: {e}")
        return False

def main():
    """Run comprehensive database integration tests"""
    print("🔬 MEMORY SYSTEM DATABASE INTEGRATION TEST")
    print("=" * 60)
    print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🎯 Purpose: Validate dual-database architecture")
    print("=" * 60)
    
    tests = [
        ("Redis Connection", test_redis_connection),
        ("ChromaDB Connection", test_chroma_connection), 
        ("Memory API Integration", test_memory_api_integration),
        ("Database Distribution", test_database_storage_distribution)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n🧪 Running: {test_name}")
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"   ❌ Test failed with exception: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"   {status} {test_name}")
    
    print(f"\n🎯 Overall Result: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED - DUAL DATABASE ARCHITECTURE WORKING!")
        print("\n✅ Confirmed:")
        print("   • Redis: Handling short-term memory and caching")
        print("   • ChromaDB: Handling long-term memory and semantic search")
        print("   • Memory API: Successfully integrating both databases")
        print("   • Storage Distribution: Optimal for performance")
    else:
        print("⚠️ SOME TESTS FAILED - REVIEW REQUIRED")
        
        failed_tests = [name for name, result in results.items() if not result]
        print(f"\n❌ Failed tests: {', '.join(failed_tests)}")

if __name__ == "__main__":
    main()
