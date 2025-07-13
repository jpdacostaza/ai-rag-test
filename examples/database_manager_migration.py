"""
Database Manager Migration Example - Using ConnectionFactory

This file demonstrates how to migrate the existing database_manager.py
to use the new ConnectionFactory pattern, eliminating code duplication.

BEFORE: database_manager.py had ~180 lines of connection logic
AFTER: Uses ConnectionFactory with ~20 lines of clean integration code
"""

import asyncio
import os
from typing import Optional, Any
from utilities.connection_factory import (
    get_connection_factory, 
    get_redis, 
    get_chroma,
    RedisConfig,
    ChromaConfig
)
from config.config_unified import Config

# Import for old way comparison
try:
    import redis.asyncio as redis
    import chromadb
except ImportError:
    redis = None
    chromadb = None


class DatabaseManagerModern:
    """
    Modernized Database Manager using ConnectionFactory.
    
    This replaces the old database_manager.py connection logic:
    - Removes 180+ lines of duplicate connection code
    - Uses centralized error handling and retry logic
    - Provides consistent health monitoring
    - Simplifies maintenance and testing
    """
    
    def __init__(self):
        self.config = Config.get_instance()
        self.connection_factory = get_connection_factory()
        self._initialized = False

    async def initialize(self):
        """Initialize all database connections using the factory."""
        if self._initialized:
            return
            
        # Create connections using factory - no complex retry logic needed!
        redis_client = await self.connection_factory.create_redis_connection("main")
        chroma_client = await self.connection_factory.create_chroma_connection("main")
        
        if redis_client:
            print("✅ Redis connected via ConnectionFactory")
        else:
            print("⚠️ Redis connection failed - check factory logs")
            
        if chroma_client:
            print("✅ ChromaDB connected via ConnectionFactory")
        else:
            print("⚠️ ChromaDB connection failed - check factory logs")
        
        self._initialized = True

    async def get_redis_client(self):
        """Get Redis client with context management."""
        # Clean, simple access with automatic error handling
        return get_redis("main")
    
    async def get_chroma_client(self):
        """Get ChromaDB client with context management."""
        # Clean, simple access with automatic error handling
        return get_chroma("main")

    async def retrieve_user_memory(self, user_id: str, query: str, n_results: int = 5):
        """
        Example of using ConnectionFactory in a service method.
        
        BEFORE: 50+ lines of connection handling mixed with business logic
        AFTER: Clean separation - connection via factory, business logic focused
        """
        try:
            # Use context manager for automatic connection management
            async with self.get_chroma_client() as chroma_client:
                collection = chroma_client.get_or_create_collection("user_memory")
                
                # Business logic only - no connection handling clutter
                results = collection.query(
                    query_texts=[query],
                    n_results=n_results,
                    where={"user_id": user_id}
                )
                
                return self._format_memory_results(results)
                
        except Exception as e:
            # ConnectionFactory handles connection errors, we handle business errors
            print(f"Memory retrieval error: {e}")
            return []

    async def store_user_memory(self, user_id: str, content: str, metadata: dict):
        """
        Example of storing data with ConnectionFactory.
        
        Benefits:
        - No connection setup/teardown code
        - Automatic retry logic from factory
        - Consistent error handling
        - Health monitoring built-in
        """
        try:
            async with self.get_chroma_client() as chroma_client:
                collection = chroma_client.get_or_create_collection("user_memory")
                
                # Pure business logic
                collection.add(
                    documents=[content],
                    metadatas=[{**metadata, "user_id": user_id}],
                    ids=[f"{user_id}_{hash(content)}"]
                )
                
                return True
                
        except Exception as e:
            print(f"Memory storage error: {e}")
            return False

    async def cache_data(self, key: str, value: str, ttl: int = 3600):
        """Example Redis operation with ConnectionFactory."""
        try:
            async with self.get_redis_client() as redis_client:
                await redis_client.setex(key, ttl, value)
                return True
        except Exception as e:
            print(f"Cache storage error: {e}")
            return False

    def get_health_status(self):
        """Get health status from ConnectionFactory."""
        return self.connection_factory.get_health_status()

    def _format_memory_results(self, results):
        """Format ChromaDB results - pure business logic."""
        formatted = []
        if results and 'documents' in results:
            for i, doc in enumerate(results['documents'][0]):
                formatted.append({
                    'content': doc,
                    'metadata': results['metadatas'][0][i] if 'metadatas' in results else {},
                    'score': results['distances'][0][i] if 'distances' in results else 0.0
                })
        return formatted


# Migration comparison
class OldDatabaseManagerComparison:
    """
    This shows what the OLD database_manager.py looked like.
    
    PROBLEMS WITH OLD APPROACH:
    - 180+ lines of connection logic
    - Duplicated error handling in every method
    - Inconsistent retry strategies
    - Mixed business logic with connection management
    - Hard to test individual components
    - Configuration scattered across methods
    """
    
    async def _initialize_redis_OLD_WAY(self):
        """OLD WAY: Duplicated in database_manager, watchdog, error_handler, etc."""
        try:
            redis_host = os.getenv("REDIS_HOST", "localhost") 
            redis_port = int(os.getenv("REDIS_PORT", "6379"))
            redis_db = int(os.getenv("REDIS_DB", "0"))

            # Duplicated connection setup (8+ times across codebase)
            self.redis_client = redis.Redis(
                host=redis_host, 
                port=redis_port, 
                db=redis_db, 
                decode_responses=True
            )
            
            # Duplicated test connection (5+ times across codebase)
            self.redis_client.ping()
            print("Redis initialized successfully")  # Inconsistent logging
            
        except redis.ConnectionError as e:
            print(f"Redis initialization failed: {str(e)}")  # Different error format
            raise  # Different error handling strategies

    async def _initialize_chroma_OLD_WAY(self):
        """OLD WAY: 100+ lines of duplicated ChromaDB setup."""
        chroma_host = os.getenv("CHROMA_HOST", "localhost")  # Duplicated config loading
        chroma_port = int(os.getenv("CHROMA_PORT", "8000"))
        max_retries = int(os.getenv("CHROMA_INIT_MAX_RETRIES", "3"))  # Different retry logic
        retry_delay = int(os.getenv("CHROMA_INIT_RETRY_DELAY", "5"))
        
        # Custom retry logic (different implementations everywhere)
        for attempt in range(max_retries):
            try:
                settings = chromadb.Settings(
                    chroma_server_host=chroma_host,
                    chroma_server_http_port=chroma_port,
                    anonymized_telemetry=False)
                self.chroma_client = chromadb.Client(settings)
                self.chroma_client.heartbeat()  # Different health check approach
                print("ChromaDB initialized successfully")  # Inconsistent logging format
                return
            except Exception as e:
                print(f"ChromaDB attempt {attempt + 1}/{max_retries} failed: {str(e)}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(retry_delay)  # Fixed delay (not exponential)
        
        print("ChromaDB initialization failed after multiple retries")  # Different error format
        self.chroma_client = None


# Usage demonstration
async def demonstrate_migration():
    """Show the difference between old and new approaches."""
    
    print("🔄 Demonstrating ConnectionFactory Migration")
    print("=" * 50)
    
    # NEW WAY: Clean and simple
    print("\n✅ NEW WAY - Using ConnectionFactory:")
    db_manager = DatabaseManagerModern()
    await db_manager.initialize()
    
    # Simple operations with automatic error handling
    memories = await db_manager.retrieve_user_memory("user123", "work information")
    cached = await db_manager.cache_data("session:123", "user_data")
    health = db_manager.get_health_status()
    
    print(f"   📋 Retrieved {len(memories)} memories")
    print(f"   💾 Cache operation: {'✅' if cached else '❌'}")
    print(f"   🏥 Health status: {len(health)} services monitored")
    
    print("\n📊 Migration Benefits:")
    print("   • 87% reduction in connection code (180+ lines → ~20 lines)")
    print("   • Unified error handling across all services")
    print("   • Automatic retry logic with exponential backoff")
    print("   • Built-in health monitoring and logging")
    print("   • Context managers for automatic cleanup")
    print("   • Configuration-driven setup")
    print("   • Easy testing and mocking")


if __name__ == "__main__":
    asyncio.run(demonstrate_migration())
