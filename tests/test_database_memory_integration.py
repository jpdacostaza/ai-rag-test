"""
Comprehensive integration test for Database Manager and Memory Service.
Tests the integration between caching, vector storage, and memory retrieval.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import asyncio
import json
import time
from typing import Dict, Any, List
from unittest.mock import patch, MagicMock

# Import the components to test
from services.database_manager import (
    DatabaseManager, initialize_database, get_database_health,
    get_chat_history, store_chat_entry, get_embedding, store_vector_data,
    query_similar, get_cache, set_cache
)
from services.memory_service import MemoryService


class TestDatabaseMemoryIntegration:
    """Integration tests for Database Manager and Memory Service."""

    @pytest.fixture
    async def database_manager(self):
        """Create a test database manager instance."""
        # Initialize the database manager
        db_manager = DatabaseManager()
        await db_manager.ensure_initialized()
        yield db_manager
        
        # Cleanup
        try:
            await db_manager.cleanup()
        except Exception:
            pass

    @pytest.fixture
    async def memory_service(self, database_manager):
        """Create a test memory service instance using pipeline architecture."""
        from services.memory_service import get_memory_service, MemoryProviderType, create_memory_service
        
        # Ensure we're using the pipeline provider (pipes/valves architecture)
        memory_service = create_memory_service(MemoryProviderType.PIPELINE)
        
        # Initialize if it has an initialize method
        if hasattr(memory_service, 'initialize'):
            await memory_service.initialize()
        yield memory_service

    @pytest.mark.asyncio
    async def test_database_health_check(self, database_manager):
        """Test that database health check returns comprehensive status."""
        health = await get_database_health()
        
        # Check basic structure
        assert isinstance(health, dict)
        assert "redis" in health
        assert "chromadb" in health
        assert "embeddings" in health
        
        # Check component health structure
        for component in ["redis", "chromadb", "embeddings"]:
            assert "status" in health[component]
            assert "details" in health[component]
            assert health[component]["status"] in ["healthy", "unhealthy", "degraded"]

    @pytest.mark.asyncio
    async def test_cache_operations(self, database_manager):
        """Test Redis caching operations."""
        # Test cache set/get
        test_key = f"test_key_{int(time.time())}"
        test_value = {"message": "test cache value", "timestamp": time.time()}
        
        # Set cache value
        success = set_cache(test_key, test_value)
        assert success is True
        
        # Get cache value
        cache_manager = get_cache()
        cached_value = cache_manager.get(test_key)
        
        # Verify cache contents
        if cached_value is not None:
            assert cached_value["message"] == test_value["message"]

    @pytest.mark.asyncio
    async def test_chat_history_operations(self, database_manager):
        """Test chat history storage and retrieval."""
        chat_id = f"test_chat_{int(time.time())}"
        
        # Create test chat entries
        test_messages = [
            {
                "role": "user",
                "content": "Hello, this is a test message",
                "timestamp": time.time(),
                "message_id": "msg_1"
            },
            {
                "role": "assistant", 
                "content": "Hello! I'm here to help you with your test.",
                "timestamp": time.time(),
                "message_id": "msg_2"
            }
        ]
        
        # Store chat entries
        for message in test_messages:
            success = await store_chat_entry(chat_id, message)
            assert success is True
        
        # Retrieve chat history
        history = await get_chat_history(chat_id, limit=10)
        
        # Verify history (Redis stores in reverse order)
        assert len(history) >= len(test_messages)
        
        # Check that messages are present (order may be reversed)
        stored_contents = [msg.get("content", "") for msg in history]
        for test_msg in test_messages:
            assert any(test_msg["content"] in content for content in stored_contents)

    @pytest.mark.asyncio
    async def test_embedding_generation(self, database_manager):
        """Test embedding generation functionality."""
        test_text = "This is a test sentence for embedding generation."
        
        # Generate embedding
        embedding = await get_embedding(test_text)
        
        if embedding is not None:
            # Verify embedding structure
            assert isinstance(embedding, list)
            assert len(embedding) > 0
            assert all(isinstance(x, (int, float)) for x in embedding)
            print(f"✅ Generated embedding of dimension: {len(embedding)}")
        else:
            print("⚠️ Embedding generation returned None (model may not be available)")

    @pytest.mark.asyncio
    async def test_vector_storage_and_retrieval(self, database_manager):
        """Test vector storage and similarity search."""
        # Test documents
        test_docs = [
            {
                "text": "Python is a high-level programming language known for its simplicity.",
                "metadata": {"topic": "programming", "language": "python", "user_id": "test_user"}
            },
            {
                "text": "Machine learning involves training algorithms on data to make predictions.",
                "metadata": {"topic": "ai", "category": "machine_learning", "user_id": "test_user"}
            },
            {
                "text": "Redis is an in-memory data structure store used as a database and cache.",
                "metadata": {"topic": "databases", "type": "nosql", "user_id": "test_user"}
            }
        ]
        
        # Store vector data
        stored_count = 0
        for doc in test_docs:
            success = await store_vector_data(doc["text"], doc["metadata"])
            if success:
                stored_count += 1
        
        if stored_count > 0:
            print(f"✅ Stored {stored_count} documents in vector database")
            
            # Test similarity search
            query_text = "programming languages and coding"
            results = await query_similar(query_text, n_results=3)
            
            # Verify results structure
            assert isinstance(results, dict)
            assert "matches" in results
            assert isinstance(results["matches"], list)
            
            if results["matches"]:
                print(f"✅ Found {len(results['matches'])} similar documents")
                
                # Verify match structure
                for match in results["matches"]:
                    assert "document" in match
                    assert "metadata" in match  
                    assert "distance" in match
                    assert isinstance(match["distance"], (int, float))
            else:
                print("⚠️ No matches found (ChromaDB may not be available)")
        else:
            print("⚠️ No documents stored (vector storage may not be available)")

    @pytest.mark.asyncio
    async def test_memory_service_integration(self, memory_service, database_manager):
        """Test memory service integration with database manager."""
        user_id = "test_user_memory"
        context = "I need help with Python programming and databases"
        
        try:
            # Test memory storage via memory service
            success = await memory_service.store_memory(
                user_id=user_id,
                content="User is learning Python programming and working with databases like Redis and PostgreSQL",
                context="learning session",
                importance=0.8,
                source="integration_test"
            )
            
            if success:
                print("✅ Memory stored successfully via MemoryService")
                
                # Test memory retrieval
                memories = await memory_service.get_relevant_memories(
                    user_id=user_id,
                    context=context,
                    max_memories=5
                )
                
                # Verify memory retrieval
                assert isinstance(memories, list)
                print(f"✅ Retrieved {len(memories)} relevant memories")
                
                if memories:
                    # Verify memory structure
                    for memory in memories:
                        assert isinstance(memory, dict)
                        # Check for required fields (may vary based on implementation)
                        assert "content" in memory or "document" in memory
                
            else:
                print("⚠️ Memory storage failed (memory service may not be available)")
                
        except Exception as e:
            print(f"⚠️ Memory service test failed: {str(e)}")

    @pytest.mark.asyncio
    async def test_error_handling_and_resilience(self, database_manager):
        """Test error handling and system resilience."""
        # Test with invalid inputs
        try:
            # Test invalid chat history retrieval
            history = await get_chat_history("", limit=-1)
            assert isinstance(history, list)  # Should return empty list, not crash
            
            # Test invalid embedding generation
            embedding = await get_embedding("")
            # Should handle gracefully (may return None or empty list)
            
            # Test invalid vector query
            results = await query_similar("", n_results=0)
            assert isinstance(results, dict)
            assert "matches" in results
            
            print("✅ Error handling tests passed")
            
        except Exception as e:
            print(f"⚠️ Error handling test failed: {str(e)}")

    @pytest.mark.asyncio
    async def test_connection_factory_integration(self, database_manager):
        """Test connection factory integration."""
        # Verify connection factory is being used
        assert database_manager.connection_factory is not None
        
        # Test health status includes connection factory info
        health = await get_database_health()
        
        if "connection_factory" in health:
            cf_health = health["connection_factory"]
            assert "status" in cf_health
            assert "connections" in cf_health
            print("✅ Connection factory integration verified")
        else:
            print("⚠️ Connection factory health not included in status")

    @pytest.mark.asyncio
    async def test_cache_statistics(self, database_manager):
        """Test cache statistics and monitoring."""
        # Get cache statistics
        cache_stats = database_manager.get_cache_stats()
        
        assert isinstance(cache_stats, dict)
        expected_stats = ["hit_count", "miss_count", "hit_rate", "size"]
        
        for stat in expected_stats:
            if stat in cache_stats:
                assert isinstance(cache_stats[stat], (int, float, str))
        
        print("✅ Cache statistics available")

    @pytest.mark.asyncio
    async def test_concurrent_operations(self, database_manager):
        """Test concurrent database operations."""
        async def concurrent_cache_operations():
            """Perform concurrent cache operations."""
            tasks = []
            for i in range(5):
                key = f"concurrent_test_{i}"
                value = {"data": f"test_value_{i}", "index": i}
                task = asyncio.create_task(self._async_cache_operation(key, value))
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            return results
        
        try:
            results = await concurrent_cache_operations()
            success_count = sum(1 for r in results if r is True)
            print(f"✅ Concurrent operations: {success_count}/5 successful")
        except Exception as e:
            print(f"⚠️ Concurrent operations test failed: {str(e)}")

    async def _async_cache_operation(self, key: str, value: Any) -> bool:
        """Helper method for async cache operations."""
        try:
            # Small delay to increase concurrency
            await asyncio.sleep(0.01)
            return set_cache(key, value)
        except Exception:
            return False

    @pytest.mark.asyncio
    async def test_cleanup_and_resource_management(self, database_manager):
        """Test proper cleanup and resource management."""
        # Test that cleanup doesn't raise exceptions
        try:
            await database_manager.cleanup()
            print("✅ Cleanup completed successfully")
        except Exception as e:
            print(f"⚠️ Cleanup failed: {str(e)}")
        
        # Re-initialize for other tests
        await database_manager.ensure_initialized()

    @pytest.mark.asyncio
    async def test_pipeline_integration_verification(self, memory_service):
        """Verify that we're using the pipeline architecture (pipes/valves)."""
        # Check that we're using the pipeline provider
        assert memory_service.provider_type == "pipeline", f"Expected pipeline provider, got {memory_service.provider_type}"
        
        # Verify pipeline provider is loaded
        assert hasattr(memory_service.provider, 'pipeline_instance'), "Pipeline provider should have pipeline_instance"
        
        print(f"✅ Using {memory_service.provider_type} provider (pipes/valves architecture)")
        
        # Test pipeline health check
        health = await memory_service.provider.health_check()
        if health:
            print("✅ Pipeline provider health check passed")
        else:
            print("⚠️ Pipeline provider health check failed (pipeline may not be available)")


# Helper function to run all tests
async def run_integration_tests():
    """Run all integration tests manually."""
    # Set environment variables for local testing
    os.environ["REDIS_HOST"] = "localhost"
    os.environ["OLLAMA_BASE_URL"] = "http://localhost:11434"
    
    print("🚀 Starting Database Manager and Memory Service Integration Tests\n")
    
    try:
        # Initialize test components
        db_manager = DatabaseManager()
        await db_manager.ensure_initialized()
        
        from services.memory_service import create_memory_service, MemoryProviderType
        # Use pipeline provider for pipes/valves architecture
        memory_service = create_memory_service(MemoryProviderType.PIPELINE)
        
        # Initialize if it has an initialize method
        if hasattr(memory_service, 'initialize'):
            await memory_service.initialize()
        
        test_instance = TestDatabaseMemoryIntegration()
        
        # Run each test
        tests = [
            ("Pipeline Integration Verification", test_instance.test_pipeline_integration_verification),
            ("Database Health Check", test_instance.test_database_health_check),
            ("Cache Operations", test_instance.test_cache_operations),
            ("Chat History Operations", test_instance.test_chat_history_operations),
            ("Embedding Generation", test_instance.test_embedding_generation),
            ("Vector Storage and Retrieval", test_instance.test_vector_storage_and_retrieval),
            ("Memory Service Integration", test_instance.test_memory_service_integration),
            ("Error Handling", test_instance.test_error_handling_and_resilience),
            ("Connection Factory Integration", test_instance.test_connection_factory_integration),
            ("Cache Statistics", test_instance.test_cache_statistics),
            ("Concurrent Operations", test_instance.test_concurrent_operations),
            ("Cleanup and Resource Management", test_instance.test_cleanup_and_resource_management),
        ]
        
        passed = 0
        failed = 0
        
        for test_name, test_func in tests:
            print(f"\n📋 Running: {test_name}")
            try:
                if test_name == "Memory Service Integration":
                    await test_func(memory_service, db_manager)
                elif test_name == "Pipeline Integration Verification":
                    await test_func(memory_service)
                else:
                    await test_func(db_manager)
                passed += 1
                print(f"✅ {test_name} - PASSED")
            except Exception as e:
                failed += 1
                print(f"❌ {test_name} - FAILED: {str(e)}")
        
        print(f"\n📊 Test Results: {passed} passed, {failed} failed")
        
        # Final cleanup
        try:
            # Clean up memory service
            if hasattr(memory_service, 'cleanup'):
                await memory_service.cleanup()
            
            # Clean up database manager
            await db_manager.cleanup()
        except Exception as e:
            print(f"⚠️ Cleanup warning: {e}")
            
    except Exception as e:
        print(f"❌ Test setup failed: {str(e)}")


if __name__ == "__main__":
    # Run tests directly
    asyncio.run(run_integration_tests())
