#!/usr/bin/env python3
"""
Extensive Memory System Test
============================

Comprehensive testing of the memory system including:
- Core connectivity tests
- Memory storage and retrieval
- Memory persistence across operations
- Memory search functionality
- API endpoint testing
- Performance benchmarks
"""

import redis
import requests
import json
import sys
import time
import uuid
from datetime import datetime
from typing import List, Dict, Any

class ExtensiveMemoryTester:
    def __init__(self):
        self.redis_host = "localhost"
        self.redis_port = 6379
        self.chroma_host = "localhost"
        self.chroma_port = 8000
        self.memory_api_host = "localhost"
        self.memory_api_port = 8001
        self.openwebui_host = "localhost"
        self.openwebui_port = 3000
        
        self.test_results = {}
        self.test_data = []
        self.test_user_id = f"test_user_{uuid.uuid4().hex[:8]}"
        
    def log(self, message, level="INFO"):
        """Log messages with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
        
    def test_basic_connectivity(self):
        """Test basic connectivity to all services"""
        self.log("=== BASIC CONNECTIVITY TESTS ===")
        
        # Redis test
        try:
            r = redis.Redis(host=self.redis_host, port=self.redis_port, decode_responses=True)
            r.ping()
            self.log("✅ Redis connection successful")
            self.test_results["redis_connectivity"] = True
        except Exception as e:
            self.log(f"❌ Redis connection failed: {e}", "ERROR")
            self.test_results["redis_connectivity"] = False
            
        # ChromaDB test
        try:
            response = requests.get(f"http://{self.chroma_host}:{self.chroma_port}/api/v2/version", timeout=10)
            if response.status_code == 200:
                version = response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text.strip('"')
                self.log(f"✅ ChromaDB v2 API accessible (version: {version})")
                self.test_results["chroma_connectivity"] = True
            else:
                self.log(f"❌ ChromaDB returned status {response.status_code}", "ERROR")
                self.test_results["chroma_connectivity"] = False
        except Exception as e:
            self.log(f"❌ ChromaDB connection failed: {e}", "ERROR")
            self.test_results["chroma_connectivity"] = False
            
        # Memory API test
        try:
            response = requests.get(f"http://{self.memory_api_host}:{self.memory_api_port}/health", timeout=10)
            if response.status_code == 200:
                health_data = response.json()
                self.log(f"✅ Memory API health: {health_data}")
                self.test_results["memory_api_connectivity"] = True
            else:
                self.log(f"❌ Memory API returned status {response.status_code}", "ERROR")
                self.test_results["memory_api_connectivity"] = False
        except Exception as e:
            self.log(f"❌ Memory API connection failed: {e}", "ERROR")
            self.test_results["memory_api_connectivity"] = False
            
        # OpenWebUI test
        try:
            response = requests.get(f"http://{self.openwebui_host}:{self.openwebui_port}", timeout=10)
            if response.status_code == 200:
                self.log("✅ OpenWebUI accessible")
                self.test_results["openwebui_connectivity"] = True
            else:
                self.log(f"❌ OpenWebUI returned status {response.status_code}", "ERROR")
                self.test_results["openwebui_connectivity"] = False
        except Exception as e:
            self.log(f"❌ OpenWebUI connection failed: {e}", "ERROR")
            self.test_results["openwebui_connectivity"] = False
            
    def test_memory_storage(self):
        """Test memory storage functionality"""
        self.log("\n=== MEMORY STORAGE TESTS ===")
        
        test_interactions = [
            {
                "user_id": self.test_user_id,
                "conversation_id": f"test_conv_{self.test_user_id}",
                "user_message": "I prefer coffee over tea in the morning",
                "assistant_response": "I'll remember that you prefer coffee in the morning",
                "context": {"category": "preferences", "time": "morning"}
            },
            {
                "user_id": self.test_user_id,
                "conversation_id": f"test_conv_{self.test_user_id}",
                "user_message": "My favorite programming language is Python",
                "assistant_response": "Got it, Python is your favorite programming language",
                "context": {"category": "preferences", "topic": "programming"}
            },
            {
                "user_id": self.test_user_id,
                "conversation_id": f"test_conv_{self.test_user_id}",
                "user_message": "I live in San Francisco and work in tech",
                "assistant_response": "I'll remember you're in San Francisco working in tech",
                "context": {"category": "personal", "location": "SF"}
            },
            {
                "user_id": self.test_user_id,
                "conversation_id": f"test_conv_{self.test_user_id}",
                "user_message": "I have a meeting every Tuesday at 3 PM",
                "assistant_response": "I'll remember your recurring Tuesday meeting at 3 PM",
                "context": {"category": "schedule", "recurring": True}
            },
            {
                "user_id": self.test_user_id,
                "conversation_id": f"test_conv_{self.test_user_id}",
                "user_message": "My project deadline is next Friday",
                "assistant_response": "I'll remember your project deadline is next Friday",
                "context": {"category": "work", "urgent": True}
            }
        ]
        
        stored_count = 0
        for i, interaction in enumerate(test_interactions):
            try:
                response = requests.post(
                    f"http://{self.memory_api_host}:{self.memory_api_port}/api/learning/process_interaction",
                    json=interaction,
                    timeout=10
                )
                
                if response.status_code == 200:
                    result = response.json()
                    self.log(f"✅ Interaction {i+1} processed: {result.get('status', 'success')}")
                    self.test_data.append({"content": interaction["user_message"], "response": interaction["assistant_response"]})
                    stored_count += 1
                else:
                    self.log(f"❌ Failed to store interaction {i+1}: {response.status_code}", "ERROR")
                    
            except Exception as e:
                self.log(f"❌ Error storing interaction {i+1}: {e}", "ERROR")
                
        self.test_results["memory_storage"] = stored_count == len(test_interactions)
        self.log(f"Memory storage result: {stored_count}/{len(test_interactions)} interactions stored")
        
    def test_memory_retrieval(self):
        """Test memory retrieval functionality"""
        self.log("\n=== MEMORY RETRIEVAL TESTS ===")
        
        test_queries = [
            "coffee preferences",
            "programming language",
            "where does user live",
            "meeting schedule",
            "project deadline"
        ]
        
        successful_retrievals = 0
        for query in test_queries:
            try:
                response = requests.post(
                    f"http://{self.memory_api_host}:{self.memory_api_port}/api/memory/retrieve",
                    json={"user_id": self.test_user_id, "query": query, "limit": 5},
                    timeout=10
                )
                
                if response.status_code == 200:
                    result = response.json()
                    memories = result.get('memories', [])
                    if memories and len(memories) > 0:
                        self.log(f"✅ Query '{query}': Found {len(memories)} memories")
                        for memory in memories[:2]:  # Show first 2 results
                            content = memory.get('content', memory.get('text', 'No content'))
                            self.log(f"   - {content[:60]}...")
                        successful_retrievals += 1
                    else:
                        self.log(f"⚠️ Query '{query}': No memories found", "WARNING")
                else:
                    self.log(f"❌ Query '{query}' failed: {response.status_code}", "ERROR")
                    
            except Exception as e:
                self.log(f"❌ Error querying '{query}': {e}", "ERROR")
                
        self.test_results["memory_retrieval"] = successful_retrievals >= len(test_queries) * 0.8  # 80% success rate
        self.log(f"Memory retrieval result: {successful_retrievals}/{len(test_queries)} queries successful")
        
    def test_memory_search_accuracy(self):
        """Test memory search accuracy and relevance"""
        self.log("\n=== MEMORY SEARCH ACCURACY TESTS ===")
        
        # Test specific searches
        specific_tests = [
            {
                "query": "Python programming",
                "expected_content": "programming language is Python",
                "test_name": "Programming Language Search"
            },
            {
                "query": "Tuesday meeting",
                "expected_content": "Tuesday at 3 PM",
                "test_name": "Schedule Search"
            },
            {
                "query": "San Francisco location",
                "expected_content": "lives in San Francisco",
                "test_name": "Location Search"
            }
        ]
        
        accurate_searches = 0
        for test in specific_tests:
            try:
                response = requests.post(
                    f"http://{self.memory_api_host}:{self.memory_api_port}/api/memory/retrieve",
                    json={"user_id": self.test_user_id, "query": test["query"], "limit": 3},
                    timeout=10
                )
                
                if response.status_code == 200:
                    result = response.json()
                    memories = result.get('memories', [])
                    if memories:
                        # Check if expected content is in top results
                        found_match = any(test["expected_content"].lower() in memory.get("content", memory.get("text", "")).lower() 
                                        for memory in memories)
                        if found_match:
                            self.log(f"✅ {test['test_name']}: Accurate result found")
                            accurate_searches += 1
                        else:
                            self.log(f"⚠️ {test['test_name']}: Expected content not in top results", "WARNING")
                    else:
                        self.log(f"❌ {test['test_name']}: No results returned", "ERROR")
                else:
                    self.log(f"❌ {test['test_name']}: API error {response.status_code}", "ERROR")
                    
            except Exception as e:
                self.log(f"❌ {test['test_name']}: Error {e}", "ERROR")
                
        self.test_results["search_accuracy"] = accurate_searches >= len(specific_tests) * 0.7  # 70% accuracy
        self.log(f"Search accuracy result: {accurate_searches}/{len(specific_tests)} tests accurate")
        
    def test_memory_persistence(self):
        """Test memory persistence by checking if stored memories still exist"""
        self.log("\n=== MEMORY PERSISTENCE TESTS ===")
        
        if not self.test_data:
            self.log("❌ No test data available for persistence test", "ERROR")
            self.test_results["memory_persistence"] = False
            return
            
        persistent_memories = 0
        for test_memory in self.test_data:
            try:
                # Search for the specific memory content
                response = requests.post(
                    f"http://{self.memory_api_host}:{self.memory_api_port}/api/memory/retrieve",
                    json={"user_id": self.test_user_id, "query": test_memory["content"][:30], "limit": 10},
                    timeout=10
                )
                
                if response.status_code == 200:
                    result = response.json()
                    memories = result.get('memories', [])
                    found = any(test_memory["content"].lower() in memory.get("content", memory.get("text", "")).lower() 
                             for memory in memories)
                    if found:
                        persistent_memories += 1
                        self.log(f"✅ Memory persisted: {test_memory['content'][:40]}...")
                    else:
                        self.log(f"⚠️ Memory not found: {test_memory['content'][:40]}...", "WARNING")
                else:
                    self.log(f"❌ Persistence check failed: {response.status_code}", "ERROR")
                    
            except Exception as e:
                self.log(f"❌ Persistence check error: {e}", "ERROR")
                
        self.test_results["memory_persistence"] = persistent_memories >= len(self.test_data) * 0.9  # 90% persistence
        self.log(f"Memory persistence result: {persistent_memories}/{len(self.test_data)} memories persistent")
        
    def test_api_endpoints(self):
        """Test various API endpoints"""
        self.log("\n=== API ENDPOINTS TESTS ===")
        
        endpoints = [
            ("GET", "/health", "Health Check", 200),
            ("GET", "/debug/stats", "Debug Stats", 200),
            ("GET", "/", "Root Endpoint", 200),
        ]
        
        working_endpoints = 0
        for method, endpoint, name, expected_status in endpoints:
            try:
                url = f"http://{self.memory_api_host}:{self.memory_api_port}{endpoint}"
                if method == "GET":
                    response = requests.get(url, timeout=10)
                else:
                    continue  # Skip non-GET for now
                    
                if response.status_code == expected_status:
                    self.log(f"✅ {name}: {response.status_code}")
                    working_endpoints += 1
                else:
                    self.log(f"⚠️ {name}: {response.status_code} (expected {expected_status})", "WARNING")
                    
            except Exception as e:
                self.log(f"❌ {name}: Error {e}", "ERROR")
                
        self.test_results["api_endpoints"] = working_endpoints >= len(endpoints) * 0.7
        self.log(f"API endpoints result: {working_endpoints}/{len(endpoints)} endpoints working")
        
    def test_performance_benchmark(self):
        """Run basic performance benchmarks"""
        self.log("\n=== PERFORMANCE BENCHMARK TESTS ===")
        
        # Test storage performance
        start_time = time.time()
        quick_interactions = [
            {
                "user_id": self.test_user_id,
                "conversation_id": f"perf_test_{self.test_user_id}",
                "user_message": f"Performance test memory {i}",
                "assistant_response": f"Stored test memory {i}",
                "context": {"test": True}
            }
            for i in range(5)
        ]
        
        stored = 0
        for interaction in quick_interactions:
            try:
                response = requests.post(
                    f"http://{self.memory_api_host}:{self.memory_api_port}/api/learning/process_interaction",
                    json=interaction,
                    timeout=5
                )
                if response.status_code == 200:
                    stored += 1
            except:
                pass
                
        storage_time = time.time() - start_time
        self.log(f"✅ Storage performance: {stored} memories in {storage_time:.2f}s ({stored/storage_time:.1f}/s)")
        
        # Test retrieval performance
        start_time = time.time()
        searches = 0
        for i in range(3):
            try:
                response = requests.post(
                    f"http://{self.memory_api_host}:{self.memory_api_port}/api/memory/retrieve",
                    json={"user_id": self.test_user_id, "query": "performance test", "limit": 5},
                    timeout=5
                )
                if response.status_code == 200:
                    searches += 1
            except:
                pass
                
        retrieval_time = time.time() - start_time
        self.log(f"✅ Retrieval performance: {searches} searches in {retrieval_time:.2f}s ({searches/retrieval_time:.1f}/s)")
        
        self.test_results["performance"] = storage_time < 10 and retrieval_time < 5  # Reasonable performance
        
    def cleanup_test_data(self):
        """Clean up test data"""
        self.log("\n=== CLEANUP TEST DATA ===")
        
        try:
            # Try to delete test memories (if delete endpoint exists)
            deleted = 0
            for test_memory in self.test_data:
                try:
                    response = requests.delete(
                        f"http://{self.memory_api_host}:{self.memory_api_port}/memories/{test_memory['id']}",
                        timeout=5
                    )
                    if response.status_code in [200, 204, 404]:
                        deleted += 1
                except:
                    pass
                    
            if deleted > 0:
                self.log(f"✅ Cleaned up {deleted} test memories")
            else:
                self.log("ℹ️ Test cleanup not available (memories will remain)", "INFO")
                
        except Exception as e:
            self.log(f"ℹ️ Cleanup note: {e}", "INFO")
            
    def run_extensive_tests(self):
        """Run all extensive tests"""
        self.log("🧪 STARTING EXTENSIVE MEMORY SYSTEM TESTS")
        self.log("=" * 70)
        
        # Run all test suites
        test_suites = [
            ("Basic Connectivity", self.test_basic_connectivity),
            ("Memory Storage", self.test_memory_storage),
            ("Memory Retrieval", self.test_memory_retrieval),
            ("Search Accuracy", self.test_memory_search_accuracy),
            ("Memory Persistence", self.test_memory_persistence),
            ("API Endpoints", self.test_api_endpoints),
            ("Performance Benchmark", self.test_performance_benchmark),
        ]
        
        passed_suites = 0
        total_suites = len(test_suites)
        
        for suite_name, test_func in test_suites:
            self.log(f"\n🔬 Running {suite_name} Tests...")
            try:
                test_func()
                passed_suites += 1
            except Exception as e:
                self.log(f"❌ {suite_name} suite failed: {e}", "ERROR")
                
        # Cleanup
        self.cleanup_test_data()
        
        # Final results
        self.log("\n" + "=" * 70)
        self.log("📊 EXTENSIVE TEST RESULTS SUMMARY")
        self.log("=" * 70)
        
        for test_name, result in self.test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            self.log(f"{test_name.replace('_', ' ').title()}: {status}")
            
        passed_tests = sum(1 for result in self.test_results.values() if result)
        total_tests = len(self.test_results)
        
        self.log(f"\nTest Suites: {passed_suites}/{total_suites} completed")
        self.log(f"Individual Tests: {passed_tests}/{total_tests} passed")
        self.log(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if passed_tests >= total_tests * 0.8:  # 80% pass rate
            self.log("\n🎉 EXTENSIVE MEMORY SYSTEM TEST: SUCCESS")
            self.log("Memory system is performing well and ready for production use!")
            return True
        else:
            self.log("\n⚠️ EXTENSIVE MEMORY SYSTEM TEST: ISSUES DETECTED")
            self.log("Some tests failed. Review the logs above for details.")
            return False

def main():
    """Main function to run extensive memory tests"""
    tester = ExtensiveMemoryTester()
    success = tester.run_extensive_tests()
    
    return 0 if success else 1

if __name__ == "__main__":
    result = main()
    sys.exit(result)
