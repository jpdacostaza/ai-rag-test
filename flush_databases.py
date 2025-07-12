#!/usr/bin/env python3
"""
Database Flush Script
====================

Flush both Redis and ChromaDB databases to clear all memory data.
"""

import redis
import chromadb
from chromadb.config import Settings
import time

# Database configuration
REDIS_HOST = "localhost"
REDIS_PORT = 6379
CHROMA_HOST = "localhost"
CHROMA_PORT = 8000

def flush_redis():
    """Flush all data from Redis database."""
    try:
        print("🔄 Connecting to Redis...")
        redis_client = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5
        )
        
        # Test connection
        redis_client.ping()
        print("✅ Redis connection successful")
        
        # Get memory count before flush
        memory_keys = redis_client.keys("memory:*")
        explicit_keys = redis_client.keys("memory:explicit:*")
        total_keys = len(memory_keys) + len(explicit_keys)
        
        print(f"📊 Found {len(memory_keys)} regular memory keys")
        print(f"📊 Found {len(explicit_keys)} explicit memory keys")
        print(f"📊 Total memory keys to delete: {total_keys}")
        
        if total_keys > 0:
            # Delete memory keys
            all_memory_keys = memory_keys + explicit_keys
            redis_client.delete(*all_memory_keys)
            print(f"🗑️ Deleted {total_keys} memory keys from Redis")
        else:
            print("✅ Redis already clean - no memory keys found")
            
        # Verify cleanup
        remaining_keys = redis_client.keys("memory:*")
        if len(remaining_keys) == 0:
            print("✅ Redis memory cleanup successful")
            return True
        else:
            print(f"⚠️ {len(remaining_keys)} keys still remain in Redis")
            return False
            
    except Exception as e:
        print(f"❌ Redis flush error: {e}")
        return False

def flush_chromadb():
    """Flush all data from ChromaDB collection."""
    try:
        print("🔄 Connecting to ChromaDB...")
        chroma_client = chromadb.HttpClient(
            host=CHROMA_HOST,
            port=CHROMA_PORT,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Get or create collection
        try:
            memory_collection = chroma_client.get_collection("user_memories")
            print("✅ ChromaDB connection successful")
            
            # Get count before flush
            initial_count = memory_collection.count()
            print(f"📊 Found {initial_count} documents in ChromaDB")
            
            if initial_count > 0:
                # Delete the entire collection and recreate it
                chroma_client.delete_collection("user_memories")
                print("🗑️ Deleted user_memories collection")
                
                # Recreate the collection
                memory_collection = chroma_client.create_collection(
                    name="user_memories",
                    metadata={"description": "Long-term user memory storage"}
                )
                print("🆕 Recreated clean user_memories collection")
                
                # Verify cleanup
                final_count = memory_collection.count()
                if final_count == 0:
                    print("✅ ChromaDB cleanup successful")
                    return True
                else:
                    print(f"⚠️ {final_count} documents still remain in ChromaDB")
                    return False
            else:
                print("✅ ChromaDB already clean - no documents found")
                return True
                
        except Exception as e:
            if "does not exist" in str(e).lower():
                print("✅ ChromaDB already clean - collection doesn't exist")
                # Create fresh collection
                memory_collection = chroma_client.create_collection(
                    name="user_memories",
                    metadata={"description": "Long-term user memory storage"}
                )
                print("🆕 Created fresh user_memories collection")
                return True
            else:
                raise e
                
    except Exception as e:
        print(f"❌ ChromaDB flush error: {e}")
        return False

def main():
    """Main function to flush both databases."""
    print("🚀 Starting Database Flush Process...\n")
    
    start_time = time.time()
    
    # Flush Redis
    print("=" * 50)
    print("Redis Database Flush")
    print("=" * 50)
    redis_success = flush_redis()
    
    print("\n" + "=" * 50)
    print("ChromaDB Database Flush")
    print("=" * 50)
    chromadb_success = flush_chromadb()
    
    # Summary
    print("\n" + "=" * 50)
    print("Flush Summary")
    print("=" * 50)
    
    elapsed_time = time.time() - start_time
    
    print(f"⏱️ Total time: {elapsed_time:.2f} seconds")
    print(f"Redis: {'✅ SUCCESS' if redis_success else '❌ FAILED'}")
    print(f"ChromaDB: {'✅ SUCCESS' if chromadb_success else '❌ FAILED'}")
    
    if redis_success and chromadb_success:
        print("\n🎉 All databases flushed successfully!")
        print("🧹 Memory system is now clean and ready for fresh data")
    else:
        print("\n⚠️ Some databases failed to flush completely")
        print("🔧 Check the errors above and try manual cleanup if needed")
    
    return redis_success and chromadb_success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
