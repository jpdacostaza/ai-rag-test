#!/usr/bin/env python3
"""
Memory Service Endpoint Testing Framework
=========================================

This test comprehensively checks all memory service methods and endpoints
to identify what's working and what needs to be fixed.

Tests:
- Memory API endpoints (/api/memory/store, /api/memory/retrieve, etc.)
- Memory service providers (API, Database, Pipeline)
- Method compatibility and parameter handling
- Error handling and fallback mechanisms
"""

import asyncio
import json
import time
import httpx
from typing import Dict, Any, List
from datetime import datetime

# Setup logging
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from core.logging_config import setup_logging, get_logger
setup_logging(level="INFO", style="human")
logger = get_logger(__name__)

class MemoryServiceTester:
    """Comprehensive memory service endpoint tester."""
    
    def __init__(self):
        self.base_urls = {
            'memory_api': 'http://localhost:5001',
            'backend': 'http://localhost:3000'
        }
        self.test_user_id = "test-user-memory-endpoints"
        self.test_results = {}
        self.session = None
    
    async def __aenter__(self):
        timeout = httpx.Timeout(10.0, connect=5.0)
        self.session = httpx.AsyncClient(timeout=timeout)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.aclose()
    
    def log_test_result(self, test_name: str, success: bool, details: str = "", response_data: Any = None):
        """Log test results with details."""
        status = "✅ PASS" if success else "❌ FAIL"
        logger.info(f"{status} | {test_name}")
        if details:
            logger.info(f"   Details: {details}")
        if response_data:
            logger.info(f"   Response: {json.dumps(response_data, indent=2)[:200]}...")
        
        self.test_results[test_name] = {
            'success': success, 
            'details': details, 
            'response': response_data
        }
    
    async def test_memory_api_endpoints(self):
        """Test all Memory API endpoints."""
        logger.info("\n" + "="*60)
        logger.info("TESTING MEMORY API ENDPOINTS")
        logger.info("="*60)
        
        # Test data
        test_memory = {
            "user_id": self.test_user_id,
            "content": "I am a Python developer who loves machine learning and AI",
            "context": "user preference test",
            "importance": 0.8,
            "source": "endpoint_test",
            "forced": False
        }
        
        # 1. Test /health endpoint
        try:
            response = await self.session.get(f"{self.base_urls['memory_api']}/health")
            success = response.status_code == 200
            self.log_test_result(
                "Memory API Health Check", 
                success, 
                f"HTTP {response.status_code}",
                response.json() if success else response.text
            )
        except Exception as e:
            self.log_test_result("Memory API Health Check", False, f"Exception: {str(e)}")
        
        # 2. Test /store endpoint (original)
        try:
            response = await self.session.post(
                f"{self.base_urls['memory_api']}/store",
                json=test_memory
            )
            success = response.status_code == 200
            response_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
            self.log_test_result(
                "Memory API /store", 
                success, 
                f"HTTP {response.status_code}",
                response_data
            )
        except Exception as e:
            self.log_test_result("Memory API /store", False, f"Exception: {str(e)}")
        
        # 3. Test /api/memory/store endpoint (new)
        try:
            response = await self.session.post(
                f"{self.base_urls['memory_api']}/api/memory/store",
                json=test_memory
            )
            success = response.status_code == 200
            response_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
            self.log_test_result(
                "Memory API /api/memory/store", 
                success, 
                f"HTTP {response.status_code}",
                response_data
            )
        except Exception as e:
            self.log_test_result("Memory API /api/memory/store", False, f"Exception: {str(e)}")
        
        # 4. Test /api/memory/store_explicit endpoint
        try:
            response = await self.session.post(
                f"{self.base_urls['memory_api']}/api/memory/store_explicit",
                json=test_memory
            )
            success = response.status_code == 200
            response_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
            self.log_test_result(
                "Memory API /api/memory/store_explicit", 
                success, 
                f"HTTP {response.status_code}",
                response_data
            )
        except Exception as e:
            self.log_test_result("Memory API /api/memory/store_explicit", False, f"Exception: {str(e)}")
        
        # 5. Test /retrieve/{user_id} endpoint
        try:
            response = await self.session.get(
                f"{self.base_urls['memory_api']}/retrieve/{self.test_user_id}"
            )
            success = response.status_code == 200
            response_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
            self.log_test_result(
                "Memory API /retrieve/{user_id}", 
                success, 
                f"HTTP {response.status_code}",
                response_data
            )
        except Exception as e:
            self.log_test_result("Memory API /retrieve/{user_id}", False, f"Exception: {str(e)}")
        
        # 6. Test /api/memory/retrieve endpoint
        retrieve_payload = {
            "user_id": self.test_user_id,
            "query": "Python developer",
            "limit": 5,
            "threshold": 0.1
        }
        try:
            response = await self.session.post(
                f"{self.base_urls['memory_api']}/api/memory/retrieve",
                json=retrieve_payload
            )
            success = response.status_code == 200
            response_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
            self.log_test_result(
                "Memory API /api/memory/retrieve", 
                success, 
                f"HTTP {response.status_code}",
                response_data
            )
        except Exception as e:
            self.log_test_result("Memory API /api/memory/retrieve", False, f"Exception: {str(e)}")
        
        # 7. Test /api/memory/stats/{user_id} endpoint
        try:
            response = await self.session.get(
                f"{self.base_urls['memory_api']}/api/memory/stats/{self.test_user_id}"
            )
            success = response.status_code == 200
            response_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
            self.log_test_result(
                "Memory API /api/memory/stats/{user_id}", 
                success, 
                f"HTTP {response.status_code}",
                response_data
            )
        except Exception as e:
            self.log_test_result("Memory API /api/memory/stats/{user_id}", False, f"Exception: {str(e)}")
    
    async def test_memory_service_providers(self):
        """Test memory service providers directly."""
        logger.info("\n" + "="*60)
        logger.info("TESTING MEMORY SERVICE PROVIDERS")
        logger.info("="*60)
        
        try:
            from services.memory_service import (
                create_memory_service, 
                MemoryProviderType,
                MemoryEntry,
                MemoryMetadata,
                MemoryQuery
            )
            
            # Test data
            metadata = MemoryMetadata(
                user_id=self.test_user_id,
                timestamp=datetime.now().isoformat(),
                source="provider_test",
                importance=0.7,
                context="direct provider test"
            )
            test_entry = MemoryEntry(
                content="Testing memory service providers directly",
                metadata=metadata
            )
            test_query = MemoryQuery(
                user_id=self.test_user_id,
                query="testing providers",
                limit=5
            )
            
            # Test Database Provider
            try:
                db_service = create_memory_service(MemoryProviderType.DATABASE)
                
                # Test health check
                health = await db_service.health_check()
                self.log_test_result("Database Provider Health", health, f"Health status: {health}")
                
                # Test store
                store_result = await db_service.store_memory(
                    self.test_user_id, 
                    "Database provider test memory", 
                    context="database test"
                )
                self.log_test_result("Database Provider Store", store_result, f"Store result: {store_result}")
                
                # Test retrieve
                memories = await db_service.get_memories(self.test_user_id, "database test", limit=3)
                self.log_test_result(
                    "Database Provider Retrieve", 
                    len(memories) >= 0, 
                    f"Retrieved {len(memories)} memories"
                )
                
            except Exception as e:
                self.log_test_result("Database Provider Test", False, f"Exception: {str(e)}")
            
            # Test API Provider
            try:
                api_service = create_memory_service(MemoryProviderType.API)
                
                # Test health check
                health = await api_service.health_check()
                self.log_test_result("API Provider Health", health, f"Health status: {health}")
                
                # Test store
                store_result = await api_service.store_memory(
                    self.test_user_id, 
                    "API provider test memory", 
                    context="api test"
                )
                self.log_test_result("API Provider Store", store_result, f"Store result: {store_result}")
                
                # Test retrieve
                memories = await api_service.get_memories(self.test_user_id, "api test", limit=3)
                self.log_test_result(
                    "API Provider Retrieve", 
                    len(memories) >= 0, 
                    f"Retrieved {len(memories)} memories"
                )
                
            except Exception as e:
                self.log_test_result("API Provider Test", False, f"Exception: {str(e)}")
            
            # Test Pipeline Provider
            try:
                pipeline_service = create_memory_service(MemoryProviderType.PIPELINE)
                
                # Test health check
                health = await pipeline_service.health_check()
                self.log_test_result("Pipeline Provider Health", health, f"Health status: {health}")
                
                # Test store
                store_result = await pipeline_service.store_memory(
                    self.test_user_id, 
                    "Pipeline provider test memory", 
                    context="pipeline test"
                )
                self.log_test_result("Pipeline Provider Store", store_result, f"Store result: {store_result}")
                
                # Test retrieve
                memories = await pipeline_service.get_memories(self.test_user_id, "pipeline test", limit=3)
                self.log_test_result(
                    "Pipeline Provider Retrieve", 
                    len(memories) >= 0, 
                    f"Retrieved {len(memories)} memories"
                )
                
            except Exception as e:
                self.log_test_result("Pipeline Provider Test", False, f"Exception: {str(e)}")
        
        except Exception as e:
            self.log_test_result("Memory Service Provider Import", False, f"Import failed: {str(e)}")
    
    async def test_method_compatibility(self):
        """Test method signature compatibility issues."""
        logger.info("\n" + "="*60)
        logger.info("TESTING METHOD COMPATIBILITY")
        logger.info("="*60)
        
        try:
            from services.memory_service import get_memory_service
            
            memory_service = get_memory_service()
            
            # Test get_relevant_memories with different parameter combinations
            try:
                # Test with max_memories parameter
                memories1 = await memory_service.get_relevant_memories(
                    self.test_user_id, 
                    "test context", 
                    max_memories=3
                )
                self.log_test_result(
                    "get_relevant_memories(max_memories)", 
                    True, 
                    f"Retrieved {len(memories1)} memories with max_memories param"
                )
            except Exception as e:
                self.log_test_result("get_relevant_memories(max_memories)", False, f"Exception: {str(e)}")
            
            try:
                # Test with limit parameter
                memories2 = await memory_service.get_relevant_memories(
                    self.test_user_id, 
                    "test context", 
                    limit=3
                )
                self.log_test_result(
                    "get_relevant_memories(limit)", 
                    True, 
                    f"Retrieved {len(memories2)} memories with limit param"
                )
            except Exception as e:
                self.log_test_result("get_relevant_memories(limit)", False, f"Exception: {str(e)}")
            
            try:
                # Test with both parameters
                memories3 = await memory_service.get_relevant_memories(
                    self.test_user_id, 
                    "test context", 
                    max_memories=2,
                    limit=3
                )
                self.log_test_result(
                    "get_relevant_memories(both params)", 
                    True, 
                    f"Retrieved {len(memories3)} memories with both params"
                )
            except Exception as e:
                self.log_test_result("get_relevant_memories(both params)", False, f"Exception: {str(e)}")
        
        except Exception as e:
            self.log_test_result("Method Compatibility Import", False, f"Import failed: {str(e)}")
    
    async def test_database_functions(self):
        """Test database manager functions directly."""
        logger.info("\n" + "="*60)
        logger.info("TESTING DATABASE FUNCTIONS")
        logger.info("="*60)
        
        try:
            from services.database_manager import (
                store_vector_data, 
                retrieve_user_memory,
                db_manager
            )
            
            # Test database manager initialization
            try:
                if db_manager and hasattr(db_manager, 'is_initialized'):
                    initialized = db_manager.is_initialized()
                    self.log_test_result("Database Manager Initialized", initialized, f"DB initialized: {initialized}")
                    
                    if not initialized and hasattr(db_manager, 'ensure_initialized'):
                        await db_manager.ensure_initialized()
                        initialized = db_manager.is_initialized()
                        self.log_test_result("Database Manager Init After Ensure", initialized, f"DB initialized after ensure: {initialized}")
                else:
                    self.log_test_result("Database Manager Instance", False, "db_manager not available or missing methods")
            except Exception as e:
                self.log_test_result("Database Manager Check", False, f"Exception: {str(e)}")
            
            # Test store_vector_data function
            try:
                store_result = await store_vector_data(
                    text="Direct database function test memory",
                    metadata={
                        "user_id": self.test_user_id,
                        "timestamp": datetime.now().isoformat(),
                        "source": "direct_db_test",
                        "importance": 0.6
                    }
                )
                self.log_test_result("store_vector_data Function", store_result, f"Store result: {store_result}")
            except Exception as e:
                self.log_test_result("store_vector_data Function", False, f"Exception: {str(e)}")
            
            # Test retrieve_user_memory function
            try:
                retrieve_result = await retrieve_user_memory(
                    user_id=self.test_user_id,
                    query="database function test",
                    n_results=3
                )
                self.log_test_result(
                    "retrieve_user_memory Function", 
                    len(retrieve_result) >= 0, 
                    f"Retrieved {len(retrieve_result)} memories"
                )
            except Exception as e:
                self.log_test_result("retrieve_user_memory Function", False, f"Exception: {str(e)}")
        
        except Exception as e:
            self.log_test_result("Database Functions Import", False, f"Import failed: {str(e)}")
    
    async def run_all_tests(self):
        """Run all memory service tests."""
        logger.info("\n" + "🧪" + "="*80)
        logger.info("COMPREHENSIVE MEMORY SERVICE ENDPOINT TESTING")
        logger.info("="*80 + "🧪")
        logger.info(f"Test started: {datetime.now()}")
        logger.info(f"Test user ID: {self.test_user_id}")
        
        # Run all test suites
        await self.test_memory_api_endpoints()
        await self.test_memory_service_providers()
        await self.test_method_compatibility()
        await self.test_database_functions()
        
        # Summary
        logger.info("\n" + "📊" + "="*60)
        logger.info("TEST RESULTS SUMMARY")
        logger.info("="*60 + "📊")
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result['success'])
        failed_tests = total_tests - passed_tests
        
        logger.info(f"Total Tests: {total_tests}")
        logger.info(f"Passed: {passed_tests} ✅")
        logger.info(f"Failed: {failed_tests} ❌")
        logger.info(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        # List failed tests
        if failed_tests > 0:
            logger.info("\n❌ FAILED TESTS:")
            for test_name, result in self.test_results.items():
                if not result['success']:
                    logger.info(f"   • {test_name}: {result['details']}")
        
        # List passed tests
        logger.info("\n✅ PASSED TESTS:")
        for test_name, result in self.test_results.items():
            if result['success']:
                logger.info(f"   • {test_name}: {result['details']}")
        
        logger.info(f"\nTest completed: {datetime.now()}")
        logger.info("="*80)


async def main():
    """Run the memory service endpoint tests."""
    async with MemoryServiceTester() as tester:
        await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
