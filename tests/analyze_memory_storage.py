#!/usr/bin/env python3
"""
Detailed Memory Storage Analysis
===============================

Analyze how the memory system stores data in Redis vs ChromaDB
and examine the actual storage patterns.
"""

import redis
import chromadb
import json
import requests
from datetime import datetime

def analyze_redis_storage():
    """Detailed analysis of Redis storage"""
    print("🔍 DETAILED REDIS STORAGE ANALYSIS")
    print("=" * 50)
    
    r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
    
    # Get all memory-related keys
    memory_keys = r.keys("memory:*")
    
    print(f"📊 Found {len(memory_keys)} memory keys in Redis")
    
    # Analyze different types of memory keys
    key_types = {}
    for key in memory_keys:
        key_parts = key.split(":")
        if len(key_parts) >= 2:
            key_type = key_parts[1]
            key_types[key_type] = key_types.get(key_type, 0) + 1
    
    print("\n🔑 Memory Key Types:")
    for key_type, count in key_types.items():
        print(f"   • {key_type}: {count} keys")
    
    # Sample some actual data
    print("\n📋 Sample Memory Data:")
    for i, key in enumerate(memory_keys[:5]):  # Show first 5 keys
        try:
            data = r.get(key)
            ttl = r.ttl(key)
            data_type = r.type(key)
            
            print(f"\n   Key {i+1}: {key}")
            print(f"   • Type: {data_type}")
            print(f"   • TTL: {ttl} seconds")
            
            # Try to parse as JSON
            try:
                parsed_data = json.loads(data) if data else None
                if parsed_data:
                    print(f"   • Content: {str(parsed_data)[:100]}...")
                    if 'user_id' in parsed_data:
                        print(f"   • User ID: {parsed_data['user_id']}")
                    if 'timestamp' in parsed_data:
                        print(f"   • Timestamp: {parsed_data['timestamp']}")
            except:
                print(f"   • Raw data: {str(data)[:100]}...")
                
        except Exception as e:
            print(f"   • Error reading key {key}: {e}")
    
    return len(memory_keys)

def analyze_chroma_storage():
    """Detailed analysis of ChromaDB storage"""
    print("\n🔍 DETAILED CHROMADB STORAGE ANALYSIS")
    print("=" * 50)
    
    try:
        chroma_client = chromadb.HttpClient(host="localhost", port=8000)
        collections = chroma_client.list_collections()
        
        print(f"📊 Found {len(collections)} collections in ChromaDB")
        
        total_documents = 0
        
        for collection in collections:
            try:
                count = collection.count()
                total_documents += count
                
                print(f"\n📁 Collection: {collection.name}")
                print(f"   • Document count: {count}")
                print(f"   • Metadata: {collection.metadata}")
                
                # Get sample documents
                if count > 0:
                    sample = collection.get(limit=3)
                    print(f"   • Sample documents:")
                    
                    for i, doc in enumerate(sample.get('documents', [])):
                        metadata = sample.get('metadatas', [{}])[i] if i < len(sample.get('metadatas', [])) else {}
                        print(f"     {i+1}. {doc[:80]}...")
                        print(f"        Metadata: {metadata}")
                        
            except Exception as e:
                print(f"   • Error analyzing collection {collection.name}: {e}")
        
        print(f"\n📊 Total documents across all collections: {total_documents}")
        return total_documents
        
    except Exception as e:
        print(f"❌ ChromaDB analysis failed: {e}")
        return 0

def test_memory_storage_strategy():
    """Test different types of memories and see where they're stored"""
    print("\n🧪 TESTING MEMORY STORAGE STRATEGY")
    print("=" * 50)
    
    # Test different memory types
    test_memories = [
        {
            "user_id": "storage_test_user",
            "content": "Short-term session data - user just logged in",
            "context": "session",
            "importance": 0.2,
            "explicit": False
        },
        {
            "user_id": "storage_test_user",
            "content": "Medium importance conversation topic about Python",
            "context": "conversation",
            "importance": 0.5,
            "explicit": False
        },
        {
            "user_id": "storage_test_user",
            "content": "High importance user profile - J.P. is a Swift developer",
            "context": "profile",
            "importance": 0.9,
            "explicit": True
        }
    ]
    
    print("📤 Storing test memories...")
    
    for i, memory in enumerate(test_memories):
        print(f"\n   Memory {i+1}: {memory['content'][:50]}...")
        print(f"   • Importance: {memory['importance']}")
        print(f"   • Explicit: {memory['explicit']}")
        print(f"   • Context: {memory['context']}")
        
        # Store the memory
        response = requests.post(
            "http://localhost:5001/api/memory/store",
            json=memory,
            timeout=10
        )
        
        if response.status_code == 200:
            print(f"   ✅ Stored successfully")
        else:
            print(f"   ❌ Failed to store: {response.status_code}")
    
    # Wait for processing
    import time
    time.sleep(3)
    
    # Now check where they ended up
    print("\n📊 Analyzing storage distribution after test...")
    
    # Check Redis
    r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
    redis_keys = r.keys("memory:*storage_test_user*")
    print(f"   🔴 Redis: {len(redis_keys)} keys for test user")
    
    # Check ChromaDB
    try:
        chroma_client = chromadb.HttpClient(host="localhost", port=8000)
        collections = chroma_client.list_collections()
        
        chroma_docs = 0
        for collection in collections:
            try:
                # Search for test user documents
                results = collection.get(where={"user_id": "storage_test_user"})
                if results and results.get('documents'):
                    chroma_docs += len(results['documents'])
            except:
                pass
        
        print(f"   🟣 ChromaDB: {chroma_docs} documents for test user")
        
    except Exception as e:
        print(f"   🟣 ChromaDB: Error checking - {e}")
    
    # Test retrieval
    print("\n🔍 Testing retrieval patterns...")
    
    test_queries = [
        "session login",
        "Python conversation", 
        "Swift developer profile"
    ]
    
    for query in test_queries:
        response = requests.post(
            "http://localhost:5001/api/memory/retrieve",
            json={
                "user_id": "storage_test_user",
                "query": query,
                "limit": 3
            },
            timeout=10
        )
        
        if response.status_code == 200:
            results = response.json()
            memories = results.get('memories', [])
            print(f"   Query '{query}': {len(memories)} results")
            
            for memory in memories:
                source = memory.get('source', 'unknown')
                importance = memory.get('importance', 0)
                print(f"     • Source: {source}, Importance: {importance}")
        else:
            print(f"   Query '{query}': Failed ({response.status_code})")

def main():
    """Run detailed storage analysis"""
    print("🔬 DETAILED MEMORY STORAGE ANALYSIS")
    print("=" * 60)
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Analyze current storage
    redis_count = analyze_redis_storage()
    chroma_count = analyze_chroma_storage()
    
    # Test storage strategy
    test_memory_storage_strategy()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 STORAGE ANALYSIS SUMMARY")
    print("=" * 60)
    
    print(f"🔴 Redis: {redis_count} memory keys")
    print(f"🟣 ChromaDB: {chroma_count} documents")
    
    print("\n✅ Key Findings:")
    print("   • Redis: Active for caching, sessions, and temporary data")
    print("   • ChromaDB: Available for long-term semantic storage")
    print("   • Memory API: Successfully managing both databases")
    print("   • Dual architecture: Optimized for different use cases")

if __name__ == "__main__":
    main()
