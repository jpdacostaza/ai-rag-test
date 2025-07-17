#!/usr/bin/env python3
"""
Enhanced Dual-Database Memory Service
====================================

This implementation properly utilizes both Redis and ChromaDB:
- Redis: Short-term memory, sessions, cache, frequent access
- ChromaDB: Long-term memory, semantic search, persistent storage

Memory storage strategy:
- Low importance (0.0-0.4): Redis only (short-term)
- Medium importance (0.5-0.7): Both Redis and ChromaDB
- High importance (0.8-1.0): ChromaDB with Redis cache
"""

import asyncio
import json
import logging
import time
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import redis
import chromadb
import httpx

class DualDatabaseMemoryService:
    """Memory service with proper dual-database architecture"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.redis_client = None
        self.chroma_client = None
        self.memory_collection = None
        self.initialized = False
        
        # Storage strategy thresholds
        self.SHORT_TERM_THRESHOLD = 0.4  # Below this: Redis only
        self.LONG_TERM_THRESHOLD = 0.8   # Above this: ChromaDB priority
        
    async def initialize(self) -> bool:
        """Initialize both Redis and ChromaDB connections"""
        self.logger.info("🚀 Initializing dual-database memory service...")
        
        try:
            # Initialize Redis connection
            self.redis_client = redis.Redis(
                host='localhost', 
                port=6379, 
                decode_responses=True,
                socket_timeout=5
            )
            
            # Test Redis connection
            self.redis_client.ping()
            self.logger.info("✅ Redis connected successfully")
            
            # Initialize ChromaDB connection
            self.chroma_client = chromadb.HttpClient(host="localhost", port=8000)
            
            # Test ChromaDB connection
            heartbeat = self.chroma_client.heartbeat()
            self.logger.info(f"✅ ChromaDB connected successfully: {heartbeat}")
            
            # Get or create memory collection
            try:
                self.memory_collection = self.chroma_client.get_collection("user_memories")
                self.logger.info("✅ Using existing memory collection")
            except:
                self.memory_collection = self.chroma_client.create_collection(
                    name="user_memories",
                    metadata={"description": "User long-term memories with semantic search"}
                )
                self.logger.info("✅ Created new memory collection")
            
            self.initialized = True
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize dual-database service: {e}")
            return False
    
    async def store_memory(self, user_id: str, content: str, context: str = None, 
                          importance: float = 0.5, explicit: bool = False, 
                          source: str = "memory_service") -> Dict[str, Any]:
        """Store memory using dual-database strategy"""
        
        if not self.initialized:
            await self.initialize()
        
        storage_info = {
            "redis": False,
            "chroma": False,
            "strategy": "none",
            "importance": importance
        }
        
        try:
            memory_data = {
                "user_id": user_id,
                "content": content,
                "context": context,
                "importance": importance,
                "explicit": explicit,
                "source": source,
                "timestamp": datetime.now().isoformat()
            }
            
            # Determine storage strategy based on importance
            if importance <= self.SHORT_TERM_THRESHOLD:
                # Low importance: Redis only (short-term)
                storage_info["strategy"] = "redis_only"
                
                if self.redis_client:
                    key = f"memory:{user_id}:{int(time.time())}"
                    # Shorter TTL for low importance memories
                    ttl = 3600  # 1 hour
                    self.redis_client.setex(key, ttl, json.dumps(memory_data))
                    storage_info["redis"] = True
                    self.logger.info(f"✅ Short-term memory stored in Redis (TTL: {ttl}s)")
                
            elif importance >= self.LONG_TERM_THRESHOLD:
                # High importance: ChromaDB priority with Redis cache
                storage_info["strategy"] = "chroma_priority"
                
                # Store in ChromaDB for long-term semantic search
                if self.memory_collection:
                    doc_id = f"{user_id}_{int(time.time())}"
                    self.memory_collection.add(
                        documents=[content],
                        metadatas=[{
                            "user_id": user_id,
                            "context": context or "",
                            "importance": importance,
                            "explicit": explicit,
                            "source": source,
                            "timestamp": memory_data["timestamp"]
                        }],
                        ids=[doc_id]
                    )
                    storage_info["chroma"] = True
                    self.logger.info(f"✅ Long-term memory stored in ChromaDB")
                
                # Also cache in Redis for quick access
                if self.redis_client:
                    key = f"memory:{user_id}:{int(time.time())}"
                    # Longer TTL for high importance memories
                    ttl = 86400  # 24 hours
                    self.redis_client.setex(key, ttl, json.dumps(memory_data))
                    storage_info["redis"] = True
                    self.logger.info(f"✅ High-importance memory cached in Redis (TTL: {ttl}s)")
            
            else:
                # Medium importance: Both databases
                storage_info["strategy"] = "dual_storage"
                
                # Store in both Redis and ChromaDB
                if self.redis_client:
                    key = f"memory:{user_id}:{int(time.time())}"
                    ttl = 43200  # 12 hours
                    self.redis_client.setex(key, ttl, json.dumps(memory_data))
                    storage_info["redis"] = True
                    self.logger.info(f"✅ Medium-importance memory stored in Redis (TTL: {ttl}s)")
                
                if self.memory_collection:
                    doc_id = f"{user_id}_{int(time.time())}"
                    self.memory_collection.add(
                        documents=[content],
                        metadatas=[{
                            "user_id": user_id,
                            "context": context or "",
                            "importance": importance,
                            "explicit": explicit,
                            "source": source,
                            "timestamp": memory_data["timestamp"]
                        }],
                        ids=[doc_id]
                    )
                    storage_info["chroma"] = True
                    self.logger.info(f"✅ Medium-importance memory stored in ChromaDB")
            
            return storage_info
            
        except Exception as e:
            self.logger.error(f"❌ Memory storage failed: {str(e)}")
            return storage_info
    
    async def get_memories(self, user_id: str, query: str = None, 
                          limit: int = 10) -> List[Dict]:
        """Retrieve memories using dual-database strategy"""
        
        if not self.initialized:
            await self.initialize()
        
        memories = []
        
        try:
            # First, get recent memories from Redis (fast access)
            if self.redis_client:
                pattern = f"memory:{user_id}:*"
                keys = self.redis_client.keys(pattern)
                
                redis_memories = []
                for key in keys:
                    data = self.redis_client.get(key)
                    if data:
                        memory = json.loads(data)
                        memory["source_db"] = "redis"
                        redis_memories.append(memory)
                
                # Sort by timestamp (most recent first)
                redis_memories.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
                memories.extend(redis_memories[:limit//2])  # Take half from Redis
                
                self.logger.info(f"✅ Retrieved {len(redis_memories)} memories from Redis")
            
            # Then, get semantic matches from ChromaDB (if query provided)
            if query and self.memory_collection:
                try:
                    # Search for semantically similar memories
                    results = self.memory_collection.query(
                        query_texts=[query],
                        n_results=limit//2,  # Take half from ChromaDB
                        where={"user_id": user_id}
                    )
                    
                    if results and results.get("documents"):
                        for i, doc in enumerate(results["documents"][0]):
                            metadata = results["metadatas"][0][i] if i < len(results["metadatas"][0]) else {}
                            
                            memory = {
                                "user_id": user_id,
                                "content": doc,
                                "context": metadata.get("context"),
                                "importance": metadata.get("importance", 0.5),
                                "explicit": metadata.get("explicit", False),
                                "source": metadata.get("source", "chroma"),
                                "timestamp": metadata.get("timestamp"),
                                "source_db": "chroma"
                            }
                            memories.append(memory)
                    
                    self.logger.info(f"✅ Retrieved {len(results['documents'][0])} memories from ChromaDB")
                    
                except Exception as e:
                    self.logger.warning(f"⚠️ ChromaDB query failed: {e}")
            
            # Remove duplicates and sort by importance/timestamp
            unique_memories = []
            seen_content = set()
            
            for memory in memories:
                content = memory.get("content", "")
                if content not in seen_content:
                    seen_content.add(content)
                    unique_memories.append(memory)
            
            # Sort by importance and timestamp
            unique_memories.sort(
                key=lambda x: (x.get("importance", 0), x.get("timestamp", "")), 
                reverse=True
            )
            
            return unique_memories[:limit]
            
        except Exception as e:
            self.logger.error(f"❌ Memory retrieval failed: {str(e)}")
            return memories
    
    async def get_storage_stats(self, user_id: str) -> Dict[str, Any]:
        """Get storage statistics for debugging"""
        stats = {
            "redis": {"keys": 0, "total_size": 0},
            "chroma": {"documents": 0, "collections": 0},
            "user_id": user_id
        }
        
        try:
            # Redis stats
            if self.redis_client:
                pattern = f"memory:{user_id}:*"
                keys = self.redis_client.keys(pattern)
                stats["redis"]["keys"] = len(keys)
                
                total_size = 0
                for key in keys:
                    data = self.redis_client.get(key)
                    if data:
                        total_size += len(data)
                stats["redis"]["total_size"] = total_size
            
            # ChromaDB stats
            if self.memory_collection:
                try:
                    # Get user's documents
                    results = self.memory_collection.get(where={"user_id": user_id})
                    stats["chroma"]["documents"] = len(results.get("documents", []))
                    stats["chroma"]["collections"] = 1  # We're using one collection
                except Exception as e:
                    self.logger.warning(f"⚠️ ChromaDB stats failed: {e}")
            
            return stats
            
        except Exception as e:
            self.logger.error(f"❌ Storage stats failed: {str(e)}")
            return stats

# Global service instance
dual_db_service = DualDatabaseMemoryService()

async def test_dual_database_service():
    """Test the dual database service"""
    print("🧪 Testing Dual Database Memory Service")
    print("=" * 50)
    
    # Initialize service
    success = await dual_db_service.initialize()
    if not success:
        print("❌ Failed to initialize service")
        return
    
    test_user = "dual_db_test_user"
    
    # Test different importance levels
    test_memories = [
        {
            "content": "User clicked on button A",
            "importance": 0.2,
            "context": "ui_interaction"
        },
        {
            "content": "User prefers Python over JavaScript",
            "importance": 0.6,
            "context": "preference"
        },
        {
            "content": "User's name is John and he works at Google",
            "importance": 0.9,
            "context": "profile"
        }
    ]
    
    print("\n📤 Storing memories with different importance levels...")
    for i, memory in enumerate(test_memories):
        result = await dual_db_service.store_memory(
            user_id=test_user,
            content=memory["content"],
            context=memory["context"],
            importance=memory["importance"]
        )
        
        print(f"   Memory {i+1} (importance: {memory['importance']}):")
        print(f"     • Strategy: {result['strategy']}")
        print(f"     • Redis: {'✅' if result['redis'] else '❌'}")
        print(f"     • ChromaDB: {'✅' if result['chroma'] else '❌'}")
    
    # Test retrieval
    print("\n🔍 Testing memory retrieval...")
    memories = await dual_db_service.get_memories(
        user_id=test_user,
        query="Python programming",
        limit=10
    )
    
    print(f"   Retrieved {len(memories)} memories:")
    for i, memory in enumerate(memories):
        print(f"     {i+1}. {memory['content'][:50]}...")
        print(f"        • Source: {memory.get('source_db', 'unknown')}")
        print(f"        • Importance: {memory.get('importance', 0)}")
    
    # Get storage stats
    print("\n📊 Storage statistics:")
    stats = await dual_db_service.get_storage_stats(test_user)
    print(f"   Redis: {stats['redis']['keys']} keys, {stats['redis']['total_size']} bytes")
    print(f"   ChromaDB: {stats['chroma']['documents']} documents")

if __name__ == "__main__":
    asyncio.run(test_dual_database_service())
