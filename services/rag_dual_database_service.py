#!/usr/bin/env python3
"""
RAG Dual-Database Memory Service
===============================

Proper implementation of:
- Redis: Short-term memory, fast access, temporary storage
- ChromaDB: Long-term memory, semantic search, permanent storage
- Explicit memory handling for "remember this" commands
"""

import asyncio
import json
import logging
import time
import uuid
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import redis
import chromadb
from chromadb.utils import embedding_functions

class RAGDualDatabaseService:
    """RAG-optimized dual-database memory service"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.redis_client = None
        self.chroma_client = None
        self.memory_collection = None
        self.embedding_function = None
        self.initialized = False
        
        # RAG Storage Strategy
        self.SHORT_TERM_IMPORTANCE = 0.4  # Below: Redis only
        self.LONG_TERM_IMPORTANCE = 0.7   # Above: ChromaDB priority
        
        # TTL Settings
        self.SHORT_TERM_TTL = 3600        # 1 hour
        self.MEDIUM_TERM_TTL = 43200      # 12 hours  
        self.LONG_TERM_TTL = 86400        # 24 hours
        
    async def initialize(self) -> bool:
        """Initialize dual-database connections"""
        self.logger.info("🚀 Initializing RAG Dual-Database Memory Service...")
        
        try:
            # Initialize Redis (short-term storage)
            # Try Docker hostname first, then localhost
            redis_hosts = ['redis', 'localhost']
            redis_connected = False
            
            for host in redis_hosts:
                try:
                    self.redis_client = redis.Redis(
                        host=host,
                        port=6379,
                        decode_responses=True,
                        socket_timeout=5
                    )
                    self.redis_client.ping()
                    self.logger.info(f"✅ Redis connected (short-term memory) via {host}")
                    redis_connected = True
                    break
                except Exception as e:
                    self.logger.warning(f"⚠️ Redis connection failed via {host}: {e}")
                    continue
            
            if not redis_connected:
                self.logger.error("❌ Could not connect to Redis")
                return False
            
            # Initialize ChromaDB (long-term storage)
            # Try Docker hostname first, then localhost
            chroma_hosts = ['chroma', 'localhost']
            chroma_connected = False
            
            for host in chroma_hosts:
                try:
                    self.chroma_client = chromadb.HttpClient(host=host, port=8000)
                    heartbeat = self.chroma_client.heartbeat()
                    self.logger.info(f"✅ ChromaDB connected (long-term memory) via {host}: {heartbeat}")
                    chroma_connected = True
                    break
                except Exception as e:
                    self.logger.warning(f"⚠️ ChromaDB connection failed via {host}: {e}")
                    continue
            
            if not chroma_connected:
                self.logger.error("❌ Could not connect to ChromaDB")
                return False
            
            # Initialize embedding function
            self.embedding_function = embedding_functions.DefaultEmbeddingFunction()
            
            # Get or create memory collection
            try:
                self.memory_collection = self.chroma_client.get_collection(
                    name="rag_memories",
                    embedding_function=self.embedding_function
                )
                self.logger.info("✅ Using existing RAG memory collection")
            except:
                self.memory_collection = self.chroma_client.create_collection(
                    name="rag_memories",
                    embedding_function=self.embedding_function,
                    metadata={"description": "RAG long-term memory with semantic search"}
                )
                self.logger.info("✅ Created new RAG memory collection")
            
            self.initialized = True
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize RAG service: {e}")
            return False
    
    async def store_memory(self, user_id: str, content: str, context: str = None,
                          importance: float = 0.5, explicit: bool = False,
                          source: str = "rag_service") -> Dict[str, Any]:
        """Store memory using RAG dual-database strategy"""
        
        if not self.initialized:
            await self.initialize()
        
        # Generate unique memory ID
        memory_id = f"mem_{user_id}_{int(time.time())}_{uuid.uuid4().hex[:8]}"
        
        # Adjust importance for explicit memories
        if explicit:
            importance = max(importance, 0.8)  # Explicit memories are important
        
        memory_data = {
            "memory_id": memory_id,
            "user_id": user_id,
            "content": content,
            "context": context,
            "importance": importance,
            "explicit": explicit,
            "source": source,
            "timestamp": datetime.now().isoformat(),
            "created_at": time.time()
        }
        
        storage_result = {
            "memory_id": memory_id,
            "redis_stored": False,
            "chroma_stored": False,
            "storage_strategy": "none",
            "importance": importance,
            "explicit": explicit
        }
        
        try:
            # Determine storage strategy based on importance
            if importance <= self.SHORT_TERM_IMPORTANCE:
                # LOW IMPORTANCE: Redis only (short-term)
                storage_result["storage_strategy"] = "redis_only"
                
                if self.redis_client:
                    redis_key = f"memory:short:{user_id}:{memory_id}"
                    self.redis_client.setex(
                        redis_key, 
                        self.SHORT_TERM_TTL, 
                        json.dumps(memory_data)
                    )
                    storage_result["redis_stored"] = True
                    self.logger.info(f"✅ Short-term memory stored in Redis (TTL: {self.SHORT_TERM_TTL}s)")
                
            elif importance >= self.LONG_TERM_IMPORTANCE:
                # HIGH IMPORTANCE: ChromaDB priority + Redis cache
                storage_result["storage_strategy"] = "chroma_priority"
                
                # Store in ChromaDB for long-term semantic search
                if self.memory_collection:
                    self.memory_collection.add(
                        documents=[content],
                        metadatas=[{
                            "memory_id": memory_id,
                            "user_id": user_id,
                            "context": context or "",
                            "importance": importance,
                            "explicit": explicit,
                            "source": source,
                            "timestamp": memory_data["timestamp"],
                            "created_at": memory_data["created_at"]
                        }],
                        ids=[memory_id]
                    )
                    storage_result["chroma_stored"] = True
                    self.logger.info(f"✅ Long-term memory stored in ChromaDB")
                
                # Cache in Redis for fast access
                if self.redis_client:
                    redis_key = f"memory:long:{user_id}:{memory_id}"
                    self.redis_client.setex(
                        redis_key,
                        self.LONG_TERM_TTL,
                        json.dumps(memory_data)
                    )
                    storage_result["redis_stored"] = True
                    self.logger.info(f"✅ Long-term memory cached in Redis (TTL: {self.LONG_TERM_TTL}s)")
                
            else:
                # MEDIUM IMPORTANCE: Dual storage
                storage_result["storage_strategy"] = "dual_storage"
                
                # Store in both databases
                if self.redis_client:
                    redis_key = f"memory:medium:{user_id}:{memory_id}"
                    self.redis_client.setex(
                        redis_key,
                        self.MEDIUM_TERM_TTL,
                        json.dumps(memory_data)
                    )
                    storage_result["redis_stored"] = True
                    self.logger.info(f"✅ Medium-term memory stored in Redis (TTL: {self.MEDIUM_TERM_TTL}s)")
                
                if self.memory_collection:
                    self.memory_collection.add(
                        documents=[content],
                        metadatas=[{
                            "memory_id": memory_id,
                            "user_id": user_id,
                            "context": context or "",
                            "importance": importance,
                            "explicit": explicit,
                            "source": source,
                            "timestamp": memory_data["timestamp"],
                            "created_at": memory_data["created_at"]
                        }],
                        ids=[memory_id]
                    )
                    storage_result["chroma_stored"] = True
                    self.logger.info(f"✅ Medium-term memory stored in ChromaDB")
            
            return storage_result
            
        except Exception as e:
            self.logger.error(f"❌ Memory storage failed: {str(e)}")
            return storage_result
    
    async def get_memories(self, user_id: str, query: str = None, 
                          limit: int = 10) -> List[Dict[str, Any]]:
        """Retrieve memories using RAG dual-database strategy"""
        
        if not self.initialized:
            await self.initialize()
        
        all_memories = []
        
        try:
            # 1. Get recent memories from Redis (fast access)
            redis_memories = await self._get_redis_memories(user_id, limit//2)
            all_memories.extend(redis_memories)
            
            # 2. Get semantic matches from ChromaDB (if query provided)
            if query:
                chroma_memories = await self._get_chroma_memories(user_id, query, limit//2)
                all_memories.extend(chroma_memories)
            
            # 3. Remove duplicates and sort
            unique_memories = self._deduplicate_memories(all_memories)
            
            # 4. Sort by importance and recency
            sorted_memories = sorted(
                unique_memories,
                key=lambda x: (x.get("importance", 0), x.get("created_at", 0)),
                reverse=True
            )
            
            return sorted_memories[:limit]
            
        except Exception as e:
            self.logger.error(f"❌ Memory retrieval failed: {str(e)}")
            return []
    
    async def _get_redis_memories(self, user_id: str, limit: int) -> List[Dict[str, Any]]:
        """Get memories from Redis"""
        memories = []
        
        try:
            if self.redis_client:
                # Get all memory types from Redis
                patterns = [
                    f"memory:short:{user_id}:*",
                    f"memory:medium:{user_id}:*",
                    f"memory:long:{user_id}:*"
                ]
                
                all_keys = []
                for pattern in patterns:
                    keys = self.redis_client.keys(pattern)
                    all_keys.extend(keys)
                
                # Get memory data
                for key in all_keys:
                    data = self.redis_client.get(key)
                    if data:
                        memory = json.loads(data)
                        memory["source_db"] = "redis"
                        memories.append(memory)
                
                # Sort by creation time (most recent first)
                memories.sort(key=lambda x: x.get("created_at", 0), reverse=True)
                
                self.logger.info(f"✅ Retrieved {len(memories)} memories from Redis")
                
        except Exception as e:
            self.logger.error(f"❌ Redis memory retrieval failed: {str(e)}")
        
        return memories[:limit]
    
    async def _get_chroma_memories(self, user_id: str, query: str, limit: int) -> List[Dict[str, Any]]:
        """Get memories from ChromaDB using semantic search"""
        memories = []
        
        try:
            if self.memory_collection:
                # Perform semantic search
                results = self.memory_collection.query(
                    query_texts=[query],
                    n_results=limit,
                    where={"user_id": user_id}
                )
                
                if results and results.get("documents"):
                    for i, doc in enumerate(results["documents"][0]):
                        metadata = results["metadatas"][0][i] if i < len(results["metadatas"][0]) else {}
                        
                        memory = {
                            "memory_id": metadata.get("memory_id", ""),
                            "user_id": user_id,
                            "content": doc,
                            "context": metadata.get("context"),
                            "importance": metadata.get("importance", 0.5),
                            "explicit": metadata.get("explicit", False),
                            "source": metadata.get("source", "chroma"),
                            "timestamp": metadata.get("timestamp"),
                            "created_at": metadata.get("created_at", 0),
                            "source_db": "chroma"
                        }
                        memories.append(memory)
                
                self.logger.info(f"✅ Retrieved {len(memories)} memories from ChromaDB")
                
        except Exception as e:
            self.logger.error(f"❌ ChromaDB memory retrieval failed: {str(e)}")
        
        return memories
    
    def _deduplicate_memories(self, memories: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate memories based on memory_id"""
        seen_ids = set()
        unique_memories = []
        
        for memory in memories:
            memory_id = memory.get("memory_id", "")
            if memory_id and memory_id not in seen_ids:
                seen_ids.add(memory_id)
                unique_memories.append(memory)
        
        return unique_memories
    
    async def get_storage_stats(self, user_id: str) -> Dict[str, Any]:
        """Get detailed storage statistics"""
        stats = {
            "user_id": user_id,
            "redis": {
                "short_term": 0,
                "medium_term": 0,
                "long_term": 0,
                "total": 0
            },
            "chroma": {
                "documents": 0,
                "explicit_memories": 0
            },
            "total_memories": 0,
            "explicit_memories": 0,
            "storage_distribution": {}
        }
        
        try:
            # Redis statistics
            if self.redis_client:
                patterns = {
                    "short_term": f"memory:short:{user_id}:*",
                    "medium_term": f"memory:medium:{user_id}:*",
                    "long_term": f"memory:long:{user_id}:*"
                }
                
                for term_type, pattern in patterns.items():
                    keys = self.redis_client.keys(pattern)
                    stats["redis"][term_type] = len(keys)
                
                stats["redis"]["total"] = sum(stats["redis"].values()) - stats["redis"]["total"]
            
            # ChromaDB statistics
            if self.memory_collection:
                try:
                    results = self.memory_collection.get(where={"user_id": user_id})
                    stats["chroma"]["documents"] = len(results.get("documents", []))
                    
                    # Count explicit memories
                    explicit_count = 0
                    for metadata in results.get("metadatas", []):
                        if metadata.get("explicit", False):
                            explicit_count += 1
                    stats["chroma"]["explicit_memories"] = explicit_count
                    
                except Exception as e:
                    self.logger.warning(f"⚠️ ChromaDB stats failed: {e}")
            
            # Calculate totals
            stats["total_memories"] = stats["redis"]["total"] + stats["chroma"]["documents"]
            stats["explicit_memories"] = stats["chroma"]["explicit_memories"]
            
            # Storage distribution
            if stats["total_memories"] > 0:
                stats["storage_distribution"] = {
                    "redis_percentage": (stats["redis"]["total"] / stats["total_memories"]) * 100,
                    "chroma_percentage": (stats["chroma"]["documents"] / stats["total_memories"]) * 100
                }
            
            return stats
            
        except Exception as e:
            self.logger.error(f"❌ Storage stats failed: {str(e)}")
            return stats
    
    async def health_check(self) -> Dict[str, Any]:
        """Comprehensive health check"""
        health = {
            "service": "rag_dual_database",
            "initialized": self.initialized,
            "redis": {"connected": False, "ping": False},
            "chroma": {"connected": False, "heartbeat": None},
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            # Test Redis
            if self.redis_client:
                self.redis_client.ping()
                health["redis"] = {"connected": True, "ping": True}
            
            # Test ChromaDB
            if self.chroma_client:
                heartbeat = self.chroma_client.heartbeat()
                health["chroma"] = {"connected": True, "heartbeat": heartbeat}
            
        except Exception as e:
            self.logger.error(f"❌ Health check failed: {str(e)}")
        
        return health

# Global service instance
rag_service = RAGDualDatabaseService()

async def test_rag_service():
    """Test the RAG service"""
    print("🧪 Testing RAG Dual-Database Service")
    print("=" * 50)
    
    # Initialize
    success = await rag_service.initialize()
    if not success:
        print("❌ Failed to initialize service")
        return
    
    test_user = "rag_test_user"
    
    # Test different importance levels
    test_memories = [
        {"content": "User clicked save button", "importance": 0.2, "explicit": False},
        {"content": "User prefers Python programming", "importance": 0.6, "explicit": False},
        {"content": "User's name is Alice and works at OpenAI", "importance": 0.9, "explicit": True},
        {"content": "Remember: I'm allergic to shellfish", "importance": 0.8, "explicit": True}
    ]
    
    print("\n📤 Storing memories...")
    for i, memory in enumerate(test_memories):
        result = await rag_service.store_memory(
            user_id=test_user,
            content=memory["content"],
            importance=memory["importance"],
            explicit=memory["explicit"]
        )
        
        print(f"   Memory {i+1}: {memory['content'][:40]}...")
        print(f"     • Strategy: {result['storage_strategy']}")
        print(f"     • Redis: {'✅' if result['redis_stored'] else '❌'}")
        print(f"     • ChromaDB: {'✅' if result['chroma_stored'] else '❌'}")
        print(f"     • Explicit: {'✅' if result['explicit'] else '❌'}")
    
    # Test retrieval
    print("\n🔍 Testing retrieval...")
    memories = await rag_service.get_memories(test_user, "Python programming", 10)
    print(f"   Retrieved {len(memories)} memories:")
    for i, memory in enumerate(memories):
        print(f"     {i+1}. {memory['content'][:50]}...")
        print(f"        • Source: {memory.get('source_db', 'unknown')}")
        print(f"        • Importance: {memory.get('importance', 0)}")
        print(f"        • Explicit: {memory.get('explicit', False)}")
    
    # Test stats
    print("\n📊 Storage statistics:")
    stats = await rag_service.get_storage_stats(test_user)
    print(f"   Redis: {stats['redis']['total']} memories")
    print(f"   ChromaDB: {stats['chroma']['documents']} documents")
    print(f"   Explicit memories: {stats['explicit_memories']}")
    print(f"   Total memories: {stats['total_memories']}")

if __name__ == "__main__":
    asyncio.run(test_rag_service())
