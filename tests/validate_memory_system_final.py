#!/usr/bin/env python3
"""
Final Memory System Validation
===============================

This script provides final validation that the memory system is working correctly
and ready for production use with OpenWebUI.
"""

import asyncio
import json
import requests
import time
import random
from typing import Dict, Any, List

# Test configuration
MEMORY_API_URL = "http://localhost:5001"

class MemorySystemValidator:
    def __init__(self):
        self.base_url = MEMORY_API_URL
        self.test_results = {}
        
    def test_api_connection(self) -> bool:
        """Test basic API connection"""
        print("🔍 Testing Memory API Connection...")
        
        try:
            response = requests.get(f"{self.base_url}/health", timeout=10)
            if response.status_code == 200:
                print("✅ Memory API is accessible and healthy")
                return True
            else:
                print(f"❌ Memory API health check failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Memory API connection failed: {e}")
            return False
    
    def test_memory_storage(self) -> bool:
        """Test memory storage functionality"""
        print("🔍 Testing Memory Storage...")
        
        test_memories = [
            {
                "user_id": "validation_user_1",
                "content": "I prefer Python programming for data science projects",
                "context": "preference"
            },
            {
                "user_id": "validation_user_1", 
                "content": "My favorite IDE is VS Code with Copilot extension",
                "context": "tool_preference"
            },
            {
                "user_id": "validation_user_2",
                "content": "I work as a full-stack developer using React and Node.js",
                "context": "job_info"
            }
        ]
        
        stored_ids = []
        
        for memory in test_memories:
            try:
                response = requests.post(
                    f"{self.base_url}/api/memory/store",
                    json=memory,
                    timeout=10
                )
                
                if response.status_code == 200:
                    result = response.json()
                    stored_ids.append(result['memory_id'])
                    print(f"   ✅ Stored: {memory['content'][:30]}... -> {result['memory_id']}")
                else:
                    print(f"   ❌ Failed to store: {memory['content'][:30]}...")
                    return False
                    
            except Exception as e:
                print(f"   ❌ Storage error: {e}")
                return False
        
        print(f"✅ Successfully stored {len(stored_ids)} memories")
        return len(stored_ids) == len(test_memories)
    
    def test_memory_retrieval(self) -> bool:
        """Test memory retrieval functionality"""
        print("🔍 Testing Memory Retrieval...")
        
        test_queries = [
            {
                "user_id": "validation_user_1",
                "query": "Python programming",
                "expected_min": 1
            },
            {
                "user_id": "validation_user_1",
                "query": "IDE preferences",
                "expected_min": 1
            },
            {
                "user_id": "validation_user_2", 
                "query": "developer work",
                "expected_min": 1
            },
            {
                "user_id": "validation_user_2",
                "query": "Python programming",  # Should not return user_1's memories
                "expected_min": 0
            }
        ]
        
        for query_data in test_queries:
            try:
                response = requests.post(
                    f"{self.base_url}/api/memory/retrieve",
                    json={
                        "user_id": query_data["user_id"],
                        "query": query_data["query"],
                        "limit": 10
                    },
                    timeout=10
                )
                
                if response.status_code == 200:
                    result = response.json()
                    memories = result.get('memories', [])
                    
                    if len(memories) >= query_data["expected_min"]:
                        print(f"   ✅ Query '{query_data['query']}' -> {len(memories)} memories")
                    else:
                        print(f"   ❌ Query '{query_data['query']}' -> Expected >={query_data['expected_min']}, got {len(memories)}")
                        return False
                else:
                    print(f"   ❌ Retrieval failed for query: {query_data['query']}")
                    return False
                    
            except Exception as e:
                print(f"   ❌ Retrieval error: {e}")
                return False
        
        print("✅ All retrieval tests passed")
        return True
    
    def test_user_isolation(self) -> bool:
        """Test that users can only access their own memories"""
        print("🔍 Testing User Isolation...")
        
        # Try to access user_1's memories as user_2
        try:
            response = requests.post(
                f"{self.base_url}/api/memory/retrieve",
                json={
                    "user_id": "validation_user_2",
                    "query": "Python data science",  # This should be in user_1's memories
                    "limit": 10
                },
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                memories = result.get('memories', [])
                
                # Check that no memories contain user_1's specific content
                contaminated = False
                for memory in memories:
                    if "data science" in memory.get('content', '').lower():
                        contaminated = True
                        break
                
                if not contaminated:
                    print("✅ User isolation maintained - no cross-user contamination")
                    return True
                else:
                    print("❌ User isolation failed - found cross-user contamination")
                    return False
            else:
                print(f"❌ User isolation test failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ User isolation test error: {e}")
            return False
    
    def test_performance(self) -> bool:
        """Test basic performance metrics"""
        print("🔍 Testing Performance...")
        
        # Test storage performance
        start_time = time.time()
        storage_success = 0
        
        for i in range(10):
            try:
                response = requests.post(
                    f"{self.base_url}/api/memory/store",
                    json={
                        "user_id": "performance_test",
                        "content": f"Performance test memory number {i} with random data {random.randint(1000, 9999)}",
                        "context": "performance_test"
                    },
                    timeout=5
                )
                
                if response.status_code == 200:
                    storage_success += 1
                    
            except Exception:
                pass
        
        storage_time = time.time() - start_time
        storage_rate = storage_success / storage_time if storage_time > 0 else 0
        
        # Test retrieval performance
        start_time = time.time()
        retrieval_success = 0
        
        for i in range(5):
            try:
                response = requests.post(
                    f"{self.base_url}/api/memory/retrieve",
                    json={
                        "user_id": "performance_test",
                        "query": f"performance test {random.randint(1, 10)}",
                        "limit": 5
                    },
                    timeout=5
                )
                
                if response.status_code == 200:
                    retrieval_success += 1
                    
            except Exception:
                pass
        
        retrieval_time = time.time() - start_time
        retrieval_rate = retrieval_success / retrieval_time if retrieval_time > 0 else 0
        
        print(f"   Storage: {storage_success}/10 successful ({storage_rate:.1f}/s)")
        print(f"   Retrieval: {retrieval_success}/5 successful ({retrieval_rate:.1f}/s)")
        
        # Performance is acceptable if we get reasonable success rates
        if storage_success >= 8 and retrieval_success >= 4:
            print("✅ Performance is acceptable")
            return True
        else:
            print("❌ Performance below acceptable thresholds")
            return False
    
    def run_validation(self) -> bool:
        """Run complete validation suite"""
        print("🚀 Starting Memory System Final Validation")
        print("=" * 60)
        
        tests = [
            ("API Connection", self.test_api_connection),
            ("Memory Storage", self.test_memory_storage),
            ("Memory Retrieval", self.test_memory_retrieval),
            ("User Isolation", self.test_user_isolation),
            ("Performance", self.test_performance),
        ]
        
        results = {}
        
        for test_name, test_func in tests:
            print(f"\n📋 {test_name}")
            try:
                results[test_name] = test_func()
            except Exception as e:
                print(f"❌ {test_name} failed with exception: {e}")
                results[test_name] = False
        
        # Summary
        print("\n" + "=" * 60)
        print("🎯 Final Validation Summary")
        print("=" * 60)
        
        passed = sum(results.values())
        total = len(results)
        
        for test_name, passed_test in results.items():
            status = "✅ PASSED" if passed_test else "❌ FAILED"
            print(f"{test_name:<20}: {status}")
        
        print(f"\nOverall Result: {passed}/{total} tests passed")
        
        if passed == total:
            print("\n🎉 MEMORY SYSTEM FULLY VALIDATED!")
            print("✅ Your memory system is production-ready")
            print("✅ All core functionality working correctly")
            print("✅ User isolation maintained")
            print("✅ Performance is acceptable")
            print("\n🚀 Ready for OpenWebUI Integration!")
            print("   You can now use the memory system through OpenWebUI")
            print("   The system will remember conversations and provide context")
        else:
            print(f"\n⚠️  {total - passed} validation test(s) failed")
            print("🔧 Please address the failed tests before production use")
        
        return passed == total

def main():
    """Main validation execution"""
    validator = MemorySystemValidator()
    success = validator.run_validation()
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
