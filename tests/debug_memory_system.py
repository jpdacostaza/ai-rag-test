#!/usr/bin/env python3
"""
Direct ChromaDB and Memory API Debugging
Tests the memory system at the database level
"""

import requests
import json
import time
import uuid
from datetime import datetime


def test_redis_connection():
    """Test Redis connection directly"""
    print("🔍 Testing Redis Connection...")
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, db=0)
        r.ping()
        print("   ✅ Redis connection successful")
        
        # Check for memory keys
        keys = r.keys("memory:*")
        print(f"   📊 Found {len(keys)} memory keys in Redis")
        
        if keys:
            # Show a sample
            sample_key = keys[0].decode() if keys else None
            if sample_key:
                sample_data = r.hgetall(sample_key)
                print(f"   📝 Sample memory key: {sample_key}")
                print(f"   📄 Sample data: {list(sample_data.keys())}")
        
        return True
    except Exception as e:
        print(f"   ❌ Redis connection failed: {e}")
        return False


def test_chromadb_connection():
    """Test ChromaDB connection directly"""
    print("🔍 Testing ChromaDB Connection...")
    try:
        import chromadb
        client = chromadb.HttpClient(host='localhost', port=8000)
        
        # Test heartbeat
        heartbeat = client.heartbeat()
        print(f"   ✅ ChromaDB heartbeat: {heartbeat}")
        
        # List collections
        collections = client.list_collections()
        print(f"   📊 Found {len(collections)} collections")
        
        for collection in collections:
            print(f"   📁 Collection: {collection.name}")
            count = collection.count()
            print(f"      📈 Items: {count}")
            
            if count > 0:
                # Get a sample
                try:
                    result = collection.get(limit=1)
                    if result['documents']:
                        print(f"      📝 Sample document: {result['documents'][0][:100]}...")
                except Exception as e:
                    print(f"      ⚠️  Sample retrieval failed: {e}")
        
        return True
    except Exception as e:
        print(f"   ❌ ChromaDB connection failed: {e}")
        return False


def test_memory_api_flow():
    """Test the complete memory API flow step by step"""
    print("🔍 Testing Memory API Flow...")
    
    api_url = "http://localhost:5001"
    test_user = f"flow_test_{uuid.uuid4().hex[:8]}"
    
    # Step 1: Store memory
    print(f"   📝 Step 1: Storing memory for {test_user}")
    memory_data = {
        "user_id": test_user,
        "content": "Flow test memory for debugging ChromaDB integration in OpenWebUI memory system",
        "metadata": {"test": "flow", "debug": True},
        "importance": 0.8
    }
    
    store_response = requests.post(
        f"{api_url}/api/memory/store",
        json=memory_data,
        timeout=15
    )
    
    if store_response.status_code == 200:
        result = store_response.json()
        memory_id = result.get("memory_id")
        storage_location = result.get("storage_location")
        print(f"   ✅ Storage successful: {memory_id}")
        print(f"   📍 Storage location: {storage_location}")
        
        # Step 2: Wait and then test retrieval
        print("   ⏳ Step 2: Waiting for indexing...")
        time.sleep(3)
        
        # Step 3: Test retrieval with various approaches
        print("   🔍 Step 3: Testing retrieval...")
        
        # Try different query approaches
        test_queries = [
            {"query": "flow test memory", "threshold": None},
            {"query": "debugging ChromaDB", "threshold": None},
            {"query": "OpenWebUI memory", "threshold": None},
            {"query": "flow test memory", "threshold": 0.5},
            {"query": "flow test memory", "threshold": 1.0},
            {"query": "flow test memory", "threshold": 1.5}
        ]
        
        successful_retrievals = 0
        for i, test_query in enumerate(test_queries):
            retrieve_data = {
                "user_id": test_user,
                "query": test_query["query"],
                "limit": 5
            }
            
            if test_query["threshold"] is not None:
                retrieve_data["threshold"] = test_query["threshold"]
            
            response = requests.post(
                f"{api_url}/api/memory/retrieve",
                json=retrieve_data,
                timeout=15
            )
            
            if response.status_code == 200:
                result = response.json()
                memories = result.get("memories", [])
                threshold = test_query.get("threshold", "default")
                print(f"      🔍 Query {i+1} (threshold={threshold}): {len(memories)} memories")
                
                if memories:
                    successful_retrievals += 1
                    for memory in memories:
                        distance = memory.get("distance", "N/A")
                        similarity = memory.get("similarity_score", "N/A")
                        print(f"         📊 Distance: {distance}, Similarity: {similarity}")
                        print(f"         💭 Content: {memory.get('content', '')[:80]}...")
            else:
                print(f"      ❌ Query {i+1} failed: {response.status_code}")
        
        if successful_retrievals > 0:
            print(f"   🎉 SUCCESS: {successful_retrievals}/{len(test_queries)} queries returned results")
            return True
        else:
            print(f"   ⚠️  ISSUE: 0/{len(test_queries)} queries returned results")
            
            # Step 4: Check stats
            print("   📊 Step 4: Checking memory stats...")
            stats_response = requests.get(f"{api_url}/api/memory/stats/{test_user}")
            if stats_response.status_code == 200:
                stats = stats_response.json()
                total_memories = stats.get("total_memories", 0)
                storage_breakdown = stats.get("storage_breakdown", {})
                print(f"      📈 Total memories: {total_memories}")
                print(f"      📍 Storage breakdown: {storage_breakdown}")
                
                if total_memories == 0:
                    print("      ❌ CRITICAL: No memories found in stats - storage failed!")
                    return False
                else:
                    print("      ⚠️  Memories stored but not retrievable - query issue!")
                    return False
            else:
                print(f"      ❌ Stats check failed: {stats_response.status_code}")
                return False
    else:
        print(f"   ❌ Storage failed: {store_response.status_code}")
        return False


def main():
    """Run complete memory system diagnosis"""
    print("🚀 Starting Complete Memory System Diagnosis")
    print("=" * 60)
    
    # Test individual components
    redis_ok = test_redis_connection()
    print()
    chromadb_ok = test_chromadb_connection()
    print()
    
    # Test complete flow
    flow_ok = test_memory_api_flow()
    print()
    
    # Summary
    print("=" * 60)
    print("🎯 Memory System Diagnosis Summary")
    print("=" * 60)
    
    print(f"📊 Component Status:")
    print(f"   Redis Connection: {'✅ OK' if redis_ok else '❌ FAILED'}")
    print(f"   ChromaDB Connection: {'✅ OK' if chromadb_ok else '❌ FAILED'}")
    print(f"   Memory API Flow: {'✅ OK' if flow_ok else '❌ FAILED'}")
    
    if redis_ok and chromadb_ok and flow_ok:
        print("\n🎉 EXCELLENT! Memory system is fully functional!")
        print("✅ All components working correctly")
        return True
    elif redis_ok and chromadb_ok:
        print("\n⚠️  Infrastructure OK but API flow has issues")
        print("🔧 Check memory API query logic and thresholds")
        return False
    else:
        print("\n❌ CRITICAL: Infrastructure components failing")
        print("🔧 Check Redis and ChromaDB container connections")
        return False


if __name__ == "__main__":
    try:
        success = main()
        exit(0 if success else 1)
    except Exception as e:
        print(f"🔥 FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
