#!/usr/bin/env python3
"""
Memory Function Integration Test
==============================            if response.status_code in [200, 201]:  # Accept both 200 and 201 for successful storage
                result = response.json()
                memory_id = result.get("memory_id", "unknown")
                self.log(f"✅ Memory Stored Successfully: ID {memory_id}")
                self.test_results["memory_storage"] = {"status": "PASS", "memory_id": memory_id}
                return Truehis test verifies that the Enhanced Memory Function is working correctly
with the fixed endpoint and proper memory retrieval.

Test Coverage:
- Memory API connectivity
- Function endpoint correction (/api/memory/retrieve)
- Memory storage and retrieval
- Function integration with OpenWebUI
- User context enhancement

Location: tests/ (as per project organization standards)
"""

import sys
import os
import json
import time
import requests
from typing import Dict, List, Any

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class MemoryFunctionTester:
    def __init__(self):
        self.memory_api_url = "http://localhost:5001"
        self.openwebui_url = "http://localhost:8080"
        self.test_user_id = "test_user_jp"
        self.test_results = {}
        
    def log(self, message: str, level: str = "INFO"):
        """Log test messages with timestamp."""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] [MemoryTest] {message}")
    
    def test_memory_api_health(self) -> bool:
        """Test 1: Verify memory API is healthy and accessible."""
        self.log("🔍 Testing Memory API Health...")
        
        try:
            response = requests.get(f"{self.memory_api_url}/health", timeout=10)
            
            if response.status_code == 200:
                health_data = response.json()
                memory_count = health_data.get("memory_count", 0)
                redis_connected = health_data.get("redis_connected", False)
                chromadb_connected = health_data.get("chromadb_connected", False)
                
                self.log(f"✅ Memory API Health: {health_data.get('status', 'unknown')}")
                self.log(f"   - Redis Connected: {redis_connected}")
                self.log(f"   - ChromaDB Connected: {chromadb_connected}")
                self.log(f"   - Total Memories: {memory_count}")
                
                self.test_results["memory_api_health"] = {
                    "status": "PASS",
                    "memory_count": memory_count,
                    "redis": redis_connected,
                    "chromadb": chromadb_connected
                }
                return True
            else:
                self.log(f"❌ Memory API Health Check Failed: {response.status_code}", "ERROR")
                self.test_results["memory_api_health"] = {"status": "FAIL", "error": f"HTTP {response.status_code}"}
                return False
                
        except Exception as e:
            self.log(f"❌ Memory API Health Check Exception: {e}", "ERROR")
            self.test_results["memory_api_health"] = {"status": "FAIL", "error": str(e)}
            return False
    
    def test_memory_storage(self) -> bool:
        """Test 2: Store a test memory and verify it was saved."""
        self.log("💾 Testing Memory Storage...")
        
        try:
            test_memory = {
                "content": f"Test memory for {self.test_user_id}: User is testing the memory system at {time.strftime('%Y-%m-%d %H:%M:%S')}",
                "user_id": self.test_user_id,
                "context": "Integration Test",
                "timestamp": "auto"
            }
            
            response = requests.post(
                f"{self.memory_api_url}/api/memory/store",
                json=test_memory,
                timeout=10
            )
            
            if response.status_code in [200, 201]:  # Accept both status codes
                result = response.json()
                memory_id = result.get("memory_id", result.get("id", "unknown"))  # Handle different response formats
                self.log(f"✅ Memory Stored Successfully: ID {memory_id}")
                self.test_results["memory_storage"] = {"status": "PASS", "memory_id": memory_id}
                return True
            else:
                self.log(f"❌ Memory Storage Failed: {response.status_code} - {response.text}", "ERROR")
                self.test_results["memory_storage"] = {"status": "FAIL", "error": f"HTTP {response.status_code}"}
                return False
                
        except Exception as e:
            self.log(f"❌ Memory Storage Exception: {e}", "ERROR")
            self.test_results["memory_storage"] = {"status": "FAIL", "error": str(e)}
            return False
    
    def test_memory_retrieval_fixed_endpoint(self) -> bool:
        """Test 3: Test memory retrieval using the FIXED endpoint (/api/memory/retrieve)."""
        self.log("🔍 Testing Memory Retrieval (Fixed Endpoint)...")
        
        try:
            # Test the fixed endpoint that the Function now uses
            retrieval_request = {
                "query": "testing memory system",
                "user_id": self.test_user_id,
                "max_results": 3
            }
            
            response = requests.post(
                f"{self.memory_api_url}/api/memory/retrieve",  # FIXED ENDPOINT
                json=retrieval_request,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                memories = result.get("memories", [])
                
                self.log(f"✅ Memory Retrieval Successful: Found {len(memories)} memories")
                
                for i, memory in enumerate(memories[:3], 1):
                    content = memory.get("content", "")[:50] + "..." if len(memory.get("content", "")) > 50 else memory.get("content", "")
                    similarity = memory.get("similarity_score", 0)
                    self.log(f"   {i}. {content} (similarity: {similarity:.3f})")
                
                self.test_results["memory_retrieval_fixed"] = {
                    "status": "PASS", 
                    "memories_found": len(memories),
                    "endpoint": "/api/memory/retrieve"
                }
                return True
            else:
                self.log(f"❌ Memory Retrieval Failed: {response.status_code} - {response.text}", "ERROR")
                self.test_results["memory_retrieval_fixed"] = {"status": "FAIL", "error": f"HTTP {response.status_code}"}
                return False
                
        except Exception as e:
            self.log(f"❌ Memory Retrieval Exception: {e}", "ERROR")
            self.test_results["memory_retrieval_fixed"] = {"status": "FAIL", "error": str(e)}
            return False
    
    def test_jp_swift_memories(self) -> bool:
        """Test 4: Verify J.P./Swift memories are accessible."""
        self.log("👤 Testing J.P./Swift Memory Retrieval...")
        
        try:
            retrieval_request = {
                "query": "J.P. Swift work",
                "user_id": "global_user",
                "max_results": 5
            }
            
            response = requests.post(
                f"{self.memory_api_url}/api/memory/retrieve",
                json=retrieval_request,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                memories = result.get("memories", [])
                
                jp_swift_memories = [m for m in memories if any(keyword in m.get("content", "").lower() 
                                                               for keyword in ["j.p.", "jp", "swift"])]
                
                self.log(f"✅ J.P./Swift Memories Found: {len(jp_swift_memories)} relevant memories")
                
                for i, memory in enumerate(jp_swift_memories[:3], 1):
                    content = memory.get("content", "")
                    self.log(f"   {i}. {content}")
                
                self.test_results["jp_swift_memories"] = {
                    "status": "PASS", 
                    "total_memories": len(memories),
                    "jp_swift_memories": len(jp_swift_memories)
                }
                return len(jp_swift_memories) > 0
            else:
                self.log(f"❌ J.P./Swift Memory Retrieval Failed: {response.status_code}", "ERROR")
                self.test_results["jp_swift_memories"] = {"status": "FAIL", "error": f"HTTP {response.status_code}"}
                return False
                
        except Exception as e:
            self.log(f"❌ J.P./Swift Memory Retrieval Exception: {e}", "ERROR")
            self.test_results["jp_swift_memories"] = {"status": "FAIL", "error": str(e)}
            return False
    
    def test_function_file_exists(self) -> bool:
        """Test 5: Verify the enhanced memory function file exists in the correct location."""
        self.log("📁 Testing Function File Location...")
        
        function_paths = [
            "memory/functions/enhanced_memory_filter_fixed.py",
            "/app/data/functions/enhanced_memory_filter_fixed.py"
        ]
        
        for path in function_paths:
            try:
                if os.path.exists(path):
                    file_size = os.path.getsize(path)
                    self.log(f"✅ Function File Found: {path} ({file_size} bytes)")
                    
                    # Check if it contains the fixed endpoint
                    with open(path, 'r') as f:
                        content = f.read()
                        if "/api/memory/retrieve" in content:
                            self.log("✅ Function contains FIXED endpoint (/api/memory/retrieve)")
                            endpoint_fixed = True
                        else:
                            self.log("⚠️ Function may still use old endpoint", "WARN")
                            endpoint_fixed = False
                    
                    self.test_results["function_file"] = {
                        "status": "PASS",
                        "path": path,
                        "size": file_size,
                        "endpoint_fixed": endpoint_fixed
                    }
                    return True
            except Exception as e:
                self.log(f"Error checking {path}: {e}", "DEBUG")
                continue
        
        self.log("❌ Function file not found in any expected location", "ERROR")
        self.test_results["function_file"] = {"status": "FAIL", "error": "File not found"}
        return False
    
    def test_openwebui_connectivity(self) -> bool:
        """Test 6: Verify OpenWebUI is accessible."""
        self.log("🌐 Testing OpenWebUI Connectivity...")
        
        try:
            response = requests.get(f"{self.openwebui_url}/health", timeout=10)
            
            if response.status_code == 200:
                self.log("✅ OpenWebUI is accessible")
                self.test_results["openwebui_connectivity"] = {"status": "PASS"}
                return True
            else:
                # Try the main page if /health doesn't exist
                response = requests.get(self.openwebui_url, timeout=10)
                if response.status_code == 200:
                    self.log("✅ OpenWebUI main page accessible")
                    self.test_results["openwebui_connectivity"] = {"status": "PASS"}
                    return True
                else:
                    self.log(f"❌ OpenWebUI not accessible: {response.status_code}", "ERROR")
                    self.test_results["openwebui_connectivity"] = {"status": "FAIL", "error": f"HTTP {response.status_code}"}
                    return False
                    
        except Exception as e:
            self.log(f"❌ OpenWebUI Connectivity Exception: {e}", "ERROR")
            self.test_results["openwebui_connectivity"] = {"status": "FAIL", "error": str(e)}
            return False
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all integration tests and return results."""
        self.log("🚀 Starting Memory Function Integration Tests...")
        self.log("=" * 60)
        
        tests = [
            ("Memory API Health", self.test_memory_api_health),
            ("Memory Storage", self.test_memory_storage),
            ("Memory Retrieval (Fixed Endpoint)", self.test_memory_retrieval_fixed_endpoint),
            ("J.P./Swift Memories", self.test_jp_swift_memories),
            ("Function File Location", self.test_function_file_exists),
            ("OpenWebUI Connectivity", self.test_openwebui_connectivity)
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test_name, test_func in tests:
            self.log(f"\n📋 Running Test: {test_name}")
            try:
                if test_func():
                    passed_tests += 1
                    self.log(f"✅ {test_name}: PASSED")
                else:
                    self.log(f"❌ {test_name}: FAILED")
            except Exception as e:
                self.log(f"❌ {test_name}: EXCEPTION - {e}", "ERROR")
        
        # Summary
        self.log("\n" + "=" * 60)
        self.log(f"🎯 Test Summary: {passed_tests}/{total_tests} tests passed")
        
        if passed_tests == total_tests:
            self.log("🎉 ALL TESTS PASSED - Memory Function Integration Complete!")
            overall_status = "PASS"
        else:
            self.log(f"⚠️ {total_tests - passed_tests} tests failed - Check logs above", "WARN")
            overall_status = "PARTIAL"
        
        # Save detailed results
        final_results = {
            "overall_status": overall_status,
            "passed_tests": passed_tests,
            "total_tests": total_tests,
            "test_results": self.test_results,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        return final_results

def main():
    """Main test execution function."""
    print("Enhanced Memory Function Integration Test")
    print("Location: tests/ directory (organized file structure)")
    print("Purpose: Verify memory system functionality after endpoint fix")
    print("=" * 60)
    
    tester = MemoryFunctionTester()
    results = tester.run_all_tests()
    
    # Save results to file in tests directory
    results_file = os.path.join(os.path.dirname(__file__), "memory_function_test_results.json")
    try:
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\n💾 Test results saved to: {results_file}")
    except Exception as e:
        print(f"⚠️ Could not save results: {e}")
    
    return results

if __name__ == "__main__":
    main()
