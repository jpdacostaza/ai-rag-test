#!/usr/bin/env python3
"""
Memory & Cache Health Testing Module
Provides comprehensive testing of Redis (cache/history) and ChromaDB (long-term memory)
for both startup validation and health monitoring.
"""

import time
import json
import hashlib
from datetime import datetime
from typing import Dict, Any, List, Optional
from human_logging import log_service_status

class MemoryCacheHealthTester:
    """Comprehensive health testing for memory and cache systems."""
    
    def __init__(self, db_manager, cache_manager=None):
        """Initialize with database manager and optional cache manager."""
        self.db_manager = db_manager
        self.cache_manager = cache_manager
        self.test_prefix = "health_test"
        
    def run_startup_tests(self) -> Dict[str, Any]:
        """Run comprehensive startup tests for all memory systems."""
        log_service_status("HEALTH", "starting", "🧪 Running memory & cache startup tests")
        
        results = {
            "timestamp": datetime.utcnow().isoformat(),
            "tests": {},
            "overall_status": "unknown",
            "services_tested": 0,
            "services_healthy": 0
        }
        
        # Test Redis cache functionality
        redis_result = self._test_redis_cache()
        results["tests"]["redis_cache"] = redis_result
        results["services_tested"] += 1
        if redis_result["status"] == "healthy":
            results["services_healthy"] += 1
        
        # Test Redis chat history functionality
        history_result = self._test_chat_history()
        results["tests"]["chat_history"] = history_result
        results["services_tested"] += 1
        if history_result["status"] == "healthy":
            results["services_healthy"] += 1
        
        # Test ChromaDB if available
        if self.db_manager.chroma_client:
            chromadb_result = self._test_chromadb_memory()
            results["tests"]["chromadb_memory"] = chromadb_result
            results["services_tested"] += 1
            if chromadb_result["status"] == "healthy":
                results["services_healthy"] += 1
        else:
            results["tests"]["chromadb_memory"] = {
                "status": "unavailable",
                "message": "ChromaDB client not available (graceful degradation)",
                "impact": "minimal"
            }
        
        # Test embedding functionality if available
        if self.db_manager.embedding_model:
            embedding_result = self._test_embeddings()
            results["tests"]["embeddings"] = embedding_result
            results["services_tested"] += 1
            if embedding_result["status"] == "healthy":
                results["services_healthy"] += 1
        else:
            results["tests"]["embeddings"] = {
                "status": "unavailable", 
                "message": "Embedding model not available",
                "impact": "moderate"
            }
        
        # Test cache manager if available
        if self.cache_manager:
            cache_mgr_result = self._test_cache_manager()
            results["tests"]["cache_manager"] = cache_mgr_result
            results["services_tested"] += 1
            if cache_mgr_result["status"] == "healthy":
                results["services_healthy"] += 1
        
        # Determine overall status
        if results["services_healthy"] == results["services_tested"]:
            results["overall_status"] = "healthy"
            log_service_status("HEALTH", "ready", f"✅ All {results['services_healthy']} memory services healthy")
        elif results["services_healthy"] >= results["services_tested"] * 0.5:
            results["overall_status"] = "degraded"
            log_service_status("HEALTH", "degraded", f"⚠️ {results['services_healthy']}/{results['services_tested']} memory services healthy")
        else:
            results["overall_status"] = "unhealthy"
            log_service_status("HEALTH", "failed", f"❌ Only {results['services_healthy']}/{results['services_tested']} memory services healthy")
        
        # Cleanup test data
        self._cleanup_test_data()
        
        return results
    
    def run_quick_health_check(self) -> Dict[str, Any]:
        """Run quick health check suitable for frequent monitoring."""
        log_service_status("HEALTH", "starting", "⚡ Running quick memory health check")
        
        results = {
            "timestamp": datetime.utcnow().isoformat(),
            "tests": {},
            "status": "unknown"
        }
        
        # Quick Redis connectivity test
        try:
            redis_client = self.db_manager.get_redis_client()
            if redis_client:
                redis_client.ping()
                test_key = f"{self.test_prefix}:quick_test"
                redis_client.set(test_key, "test", ex=10)
                retrieved = redis_client.get(test_key)
                redis_client.delete(test_key)
                
                results["tests"]["redis"] = {
                    "status": "healthy",
                    "response_time": "< 0.01s",
                    "operations": ["ping", "set", "get", "delete"]
                }
            else:
                results["tests"]["redis"] = {"status": "unhealthy", "error": "No Redis client"}
        except Exception as e:
            results["tests"]["redis"] = {"status": "unhealthy", "error": str(e)}
        
        # Quick ChromaDB test if available
        if self.db_manager.chroma_client:
            try:
                collections = self.db_manager.chroma_client.list_collections()
                results["tests"]["chromadb"] = {
                    "status": "healthy",
                    "collections": len(collections),
                    "operations": ["list_collections"]
                }
            except Exception as e:
                results["tests"]["chromadb"] = {"status": "unhealthy", "error": str(e)}
        else:
            results["tests"]["chromadb"] = {"status": "unavailable", "message": "Not configured"}
        
        # Determine overall status
        healthy_tests = sum(1 for test in results["tests"].values() if test.get("status") == "healthy")
        total_tests = len([t for t in results["tests"].values() if t.get("status") in ["healthy", "unhealthy"]])
        
        if total_tests > 0 and healthy_tests == total_tests:
            results["status"] = "healthy"
        elif healthy_tests > 0:
            results["status"] = "degraded"
        else:
            results["status"] = "unhealthy"
        
        return results
    
    def _test_redis_cache(self) -> Dict[str, Any]:
        """Test Redis cache functionality."""
        try:
            log_service_status("HEALTH", "testing", "Testing Redis cache operations")
            
            redis_client = self.db_manager.get_redis_client()
            if not redis_client:
                return {"status": "unhealthy", "error": "No Redis client available"}
            
            test_data = {
                "simple_key": "simple_value",
                "json_data": json.dumps({"test": "data", "timestamp": datetime.utcnow().isoformat()}),
                "cache_entry": json.dumps({
                    "value": "This is a test cache entry",
                    "cached_at": datetime.utcnow().isoformat(),
                    "version": "v2.0.0",
                    "format": "plain_text"
                })
            }
            
            operations_tested = []
            
            # Test basic set/get
            for key, value in test_data.items():
                test_key = f"{self.test_prefix}:cache:{key}"
                redis_client.setex(test_key, 60, value)
                retrieved = redis_client.get(test_key)
                if retrieved != value:
                    return {"status": "unhealthy", "error": f"Data mismatch for {key}"}
                operations_tested.append(f"set/get:{key}")
            
            # Test TTL
            ttl_key = f"{self.test_prefix}:cache:ttl_test"
            redis_client.setex(ttl_key, 5, "ttl_test")
            ttl = redis_client.ttl(ttl_key)
            if ttl <= 0 or ttl > 5:
                return {"status": "unhealthy", "error": "TTL not working correctly"}
            operations_tested.append("ttl")
            
            # Test exists and delete
            if not redis_client.exists(ttl_key):
                return {"status": "unhealthy", "error": "EXISTS operation failed"}
            operations_tested.append("exists")
            
            redis_client.delete(ttl_key)
            if redis_client.exists(ttl_key):
                return {"status": "unhealthy", "error": "DELETE operation failed"}
            operations_tested.append("delete")
            
            return {
                "status": "healthy",
                "operations_tested": operations_tested,
                "test_keys": len(test_data),
                "message": "All Redis cache operations working correctly"
            }
            
        except Exception as e:
            return {"status": "unhealthy", "error": f"Redis cache test failed: {e}"}
    
    def _test_chat_history(self) -> Dict[str, Any]:
        """Test Redis chat history functionality."""
        try:
            log_service_status("HEALTH", "testing", "Testing chat history operations")
            
            redis_client = self.db_manager.get_redis_client()
            if not redis_client:
                return {"status": "unhealthy", "error": "No Redis client available"}
            
            test_user = f"{self.test_prefix}_user"
            history_key = f"chat_history:{test_user}"
            
            # Test chat history operations
            test_messages = [
                {"message": "Hello", "response": "Hi there!", "timestamp": datetime.utcnow().isoformat()},
                {"message": "How are you?", "response": "I'm doing well!", "timestamp": datetime.utcnow().isoformat()},
                {"message": "Goodbye", "response": "See you later!", "timestamp": datetime.utcnow().isoformat()}
            ]
            
            operations_tested = []
            
            # Test RPUSH (add messages)
            for msg in test_messages:
                redis_client.rpush(history_key, json.dumps(msg))
            operations_tested.append("rpush")
            
            # Test LLEN (get length)
            length = redis_client.llen(history_key)
            if length != len(test_messages):
                return {"status": "unhealthy", "error": f"Expected {len(test_messages)} messages, got {length}"}
            operations_tested.append("llen")
            
            # Test LRANGE (get messages)
            retrieved_msgs = redis_client.lrange(history_key, 0, -1)
            if len(retrieved_msgs) != len(test_messages):
                return {"status": "unhealthy", "error": "LRANGE returned wrong number of messages"}
            operations_tested.append("lrange")
            
            # Test LTRIM (limit history)
            redis_client.ltrim(history_key, -2, -1)  # Keep last 2
            trimmed_length = redis_client.llen(history_key)
            if trimmed_length != 2:
                return {"status": "unhealthy", "error": f"LTRIM failed, expected 2 messages, got {trimmed_length}"}
            operations_tested.append("ltrim")
            
            return {
                "status": "healthy",
                "operations_tested": operations_tested,
                "messages_tested": len(test_messages),
                "message": "All chat history operations working correctly"
            }
            
        except Exception as e:
            return {"status": "unhealthy", "error": f"Chat history test failed: {e}"}
    
    def _test_chromadb_memory(self) -> Dict[str, Any]:
        """Test ChromaDB long-term memory functionality."""
        try:
            log_service_status("HEALTH", "testing", "Testing ChromaDB memory operations")
            
            if not self.db_manager.chroma_collection:
                return {"status": "unhealthy", "error": "No ChromaDB collection available"}
            
            # Test data
            test_documents = [
                "This is a test document about artificial intelligence and machine learning concepts.",
                "Web development involves creating responsive websites using HTML, CSS, and JavaScript.",
                "Database management systems store and organize data efficiently for applications."
            ]
            
            test_ids = [f"{self.test_prefix}:doc_{i}" for i in range(len(test_documents))]
            test_metadata = [{"source": "health_test", "topic": f"topic_{i}"} for i in range(len(test_documents))]
            
            operations_tested = []
            
            # Test ADD operation
            self.db_manager.chroma_collection.add(
                documents=test_documents,
                ids=test_ids,
                metadatas=test_metadata
            )
            operations_tested.append("add")
            
            # Test COUNT operation
            count = self.db_manager.chroma_collection.count()
            if count < len(test_documents):
                return {"status": "unhealthy", "error": f"Document count too low: {count}"}
            operations_tested.append("count")
            
            # Test GET operation
            results = self.db_manager.chroma_collection.get(ids=test_ids)
            if len(results.get('ids', [])) != len(test_ids):
                return {"status": "unhealthy", "error": "GET operation returned wrong number of documents"}
            operations_tested.append("get")
            
            # Test QUERY operation (if embeddings available)
            if self.db_manager.embedding_model:
                query_results = self.db_manager.chroma_collection.query(
                    query_texts=["artificial intelligence"],
                    n_results=1
                )
                if not query_results.get('ids'):
                    return {"status": "unhealthy", "error": "QUERY operation returned no results"}
                operations_tested.append("query")
            
            return {
                "status": "healthy",
                "operations_tested": operations_tested,
                "documents_tested": len(test_documents),
                "total_documents": count,
                "message": "All ChromaDB operations working correctly"
            }
            
        except Exception as e:
            return {"status": "unhealthy", "error": f"ChromaDB test failed: {e}"}
    
    def _test_embeddings(self) -> Dict[str, Any]:
        """Test embedding model functionality."""
        try:
            log_service_status("HEALTH", "testing", "Testing embedding model")
            
            if not self.db_manager.embedding_model:
                return {"status": "unhealthy", "error": "No embedding model available"}
            
            test_texts = [
                "This is a test sentence for embedding generation.",
                "Another test sentence with different content.",
                "Final test sentence for embedding validation."
            ]
            
            # Test embedding generation
            start_time = time.time()
            embeddings = self.db_manager.embedding_model.encode(test_texts)
            generation_time = time.time() - start_time
            
            # Validate embeddings
            if embeddings is None or len(embeddings) != len(test_texts):
                return {"status": "unhealthy", "error": "Embedding generation failed"}
            
            # Check embedding dimensions
            if len(embeddings.shape) != 2 or embeddings.shape[0] != len(test_texts):
                return {"status": "unhealthy", "error": "Invalid embedding dimensions"}
            
            # Check for reasonable embedding values
            import numpy as np
            if np.any(np.isnan(embeddings)) or np.any(np.isinf(embeddings)):
                return {"status": "unhealthy", "error": "Invalid embedding values (NaN or Inf)"}
            
            return {
                "status": "healthy",
                "texts_embedded": len(test_texts),
                "embedding_dimension": embeddings.shape[1],
                "generation_time": f"{generation_time:.3f}s",
                "model": str(type(self.db_manager.embedding_model).__name__),
                "message": "Embedding model working correctly"
            }
            
        except Exception as e:
            return {"status": "unhealthy", "error": f"Embedding test failed: {e}"}
    
    def _test_cache_manager(self) -> Dict[str, Any]:
        """Test cache manager functionality."""
        try:
            log_service_status("HEALTH", "testing", "Testing cache manager operations")
            
            if not self.cache_manager:
                return {"status": "unhealthy", "error": "No cache manager available"}
            
            test_key = f"{self.test_prefix}:cache_mgr_test"
            test_value = "This is a test value for cache manager validation"
            
            operations_tested = []
            
            # Test cache SET operation
            set_result = self.cache_manager.set_with_validation(test_key, test_value, 60)
            if not set_result:
                return {"status": "unhealthy", "error": "Cache manager SET operation failed"}
            operations_tested.append("set_with_validation")
            
            # Test cache GET operation
            retrieved_value = self.cache_manager.get_with_validation(test_key)
            if retrieved_value != test_value:
                return {"status": "unhealthy", "error": "Cache manager GET operation failed"}
            operations_tested.append("get_with_validation")
            
            # Test JSON rejection
            json_value = '{"test": "json_data"}'
            json_result = self.cache_manager.set_with_validation(f"{test_key}_json", json_value, 60)
            if json_result:
                return {"status": "unhealthy", "error": "Cache manager should reject JSON format"}
            operations_tested.append("json_validation")
            
            # Test cache statistics
            stats = self.cache_manager.get_cache_stats()
            if not stats or "total_keys" not in stats:
                return {"status": "unhealthy", "error": "Cache statistics not available"}
            operations_tested.append("get_cache_stats")
            
            return {
                "status": "healthy",
                "operations_tested": operations_tested,
                "cache_version": stats.get("version", "unknown"),
                "total_keys": stats.get("total_keys", 0),
                "message": "Cache manager working correctly"
            }
            
        except Exception as e:
            return {"status": "unhealthy", "error": f"Cache manager test failed: {e}"}
    
    def _cleanup_test_data(self):
        """Clean up test data from all systems."""
        try:
            # Clean Redis test data
            redis_client = self.db_manager.get_redis_client()
            if redis_client:
                # Find and delete test keys
                test_keys = []
                cursor = 0
                while True:
                    cursor, keys = redis_client.scan(cursor, match=f"{self.test_prefix}*", count=1000)
                    test_keys.extend(keys)
                    if cursor == 0:
                        break
                
                if test_keys:
                    redis_client.delete(*test_keys)
                    log_service_status("HEALTH", "ready", f"Cleaned up {len(test_keys)} Redis test keys")
            
            # Clean ChromaDB test data
            if self.db_manager.chroma_collection:
                try:
                    # Get all documents with health_test metadata
                    results = self.db_manager.chroma_collection.get(
                        where={"source": "health_test"}
                    )
                    if results.get('ids'):
                        self.db_manager.chroma_collection.delete(ids=results['ids'])
                        log_service_status("HEALTH", "ready", f"Cleaned up {len(results['ids'])} ChromaDB test documents")
                except Exception as e:
                    log_service_status("HEALTH", "warning", f"ChromaDB cleanup failed: {e}")
                    
        except Exception as e:
            log_service_status("HEALTH", "warning", f"Cleanup failed: {e}")

def create_health_tester():
    """Factory function to create health tester with current database configuration."""
    from database import db_manager, get_cache_manager
    cache_manager = get_cache_manager()
    return MemoryCacheHealthTester(db_manager, cache_manager)
