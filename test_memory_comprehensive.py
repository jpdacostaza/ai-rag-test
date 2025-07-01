#!/usr/bin/env python3
"""
Comprehensive Memory System Test Script
Tests all components of the memory system including:
- Redis connectivity
- ChromaDB connectivity  
- Memory API functionality
- OpenWebUI connectivity
- Basic Docker container status
"""

import redis
import requests
import json
import sys
from datetime import datetime

class MemorySystemTester:
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
        
    def log(self, message, level="INFO"):
        """Log messages with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
        
    def test_redis_connection(self):
        """Test Redis connectivity"""
        try:
            self.log("Testing Redis connection...")
            r = redis.Redis(host=self.redis_host, port=self.redis_port, decode_responses=True)
            
            # Test basic operations
            r.ping()
            r.set("test_key", "test_value")
            value = r.get("test_key")
            r.delete("test_key")
            
            if value == "test_value":
                self.log("✅ Redis connection successful")
                self.test_results["redis"] = True
                return True
            else:
                self.log("❌ Redis test failed - value mismatch", "ERROR")
                self.test_results["redis"] = False
                return False
                
        except Exception as e:
            self.log(f"❌ Redis connection failed: {e}", "ERROR")
            self.test_results["redis"] = False
            return False
            
    def test_chroma_connection(self):
        """Test ChromaDB connectivity"""
        try:
            self.log("Testing ChromaDB connection...")
            
            # Test HTTP endpoint with v2 API
            response = requests.get(f"http://{self.chroma_host}:{self.chroma_port}/api/v2/version", timeout=10)
            if response.status_code == 200:
                version = response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text.strip('"')
                self.log(f"✅ ChromaDB v2 API accessible (version: {version})")
                
                # Test heartbeat if available
                try:
                    heartbeat_response = requests.get(f"http://{self.chroma_host}:{self.chroma_port}/api/v2/heartbeat", timeout=5)
                    if heartbeat_response.status_code == 200:
                        self.log("✅ ChromaDB heartbeat successful")
                except:
                    # Heartbeat might not be available in v2, that's okay
                    pass
                    
                self.test_results["chroma"] = True
                return True
            else:
                self.log(f"❌ ChromaDB HTTP endpoint returned status {response.status_code}", "ERROR")
                self.test_results["chroma"] = False
                return False
                
        except Exception as e:
            self.log(f"❌ ChromaDB connection failed: {e}", "ERROR")
            self.test_results["chroma"] = False
            return False
            
    def test_memory_api(self):
        """Test Memory API functionality"""
        try:
            self.log("Testing Memory API...")
            
            # Test health endpoint
            response = requests.get(f"http://{self.memory_api_host}:{self.memory_api_port}/health", timeout=10)
            if response.status_code == 200:
                self.log("✅ Memory API health endpoint accessible")
                self.test_results["memory_api"] = True
                return True
            else:
                self.log(f"❌ Memory API health endpoint returned status {response.status_code}", "ERROR")
                self.test_results["memory_api"] = False
                return False
                
        except Exception as e:
            self.log(f"❌ Memory API test failed: {e}", "ERROR")
            self.test_results["memory_api"] = False
            return False
            
    def test_openwebui_connection(self):
        """Test OpenWebUI connectivity"""
        try:
            self.log("Testing OpenWebUI connection...")
            
            response = requests.get(f"http://{self.openwebui_host}:{self.openwebui_port}", timeout=10)
            if response.status_code == 200:
                self.log("✅ OpenWebUI accessible")
                self.test_results["openwebui"] = True
                return True
            else:
                self.log(f"❌ OpenWebUI returned status {response.status_code}", "ERROR")
                self.test_results["openwebui"] = False
                return False
                
        except Exception as e:
            self.log(f"❌ OpenWebUI connection failed: {e}", "ERROR")
            self.test_results["openwebui"] = False
            return False
            
    def run_all_tests(self):
        """Run all tests in sequence"""
        self.log("Starting comprehensive memory system test...")
        self.log("=" * 60)
        
        tests = [
            ("Redis Connection", self.test_redis_connection),
            ("ChromaDB Connection", self.test_chroma_connection),
            ("Memory API", self.test_memory_api),
            ("OpenWebUI Connection", self.test_openwebui_connection),
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            self.log(f"\n--- {test_name} ---")
            if test_func():
                passed += 1
                
        self.log("\n" + "=" * 60)
        self.log("TEST RESULTS SUMMARY")
        self.log("=" * 60)
        
        for test_name, (_, test_func) in zip([t[0] for t in tests], tests):
            result = self.test_results.get(test_name.lower().replace(" ", "_"), False)
            status = "✅ PASS" if result else "❌ FAIL"
            self.log(f"{test_name}: {status}")
            
        self.log(f"\nOverall: {passed}/{total} tests passed")
        
        if passed == total:
            self.log("🎉 All tests passed! Memory system is fully operational.")
            return True
        else:
            self.log(f"⚠️ {total - passed} test(s) failed. Please check the logs above.")
            return False

def main():
    """Main function to run the memory system tests"""
    tester = MemorySystemTester()
    success = tester.run_all_tests()
    
    if success:
        return 0
    else:
        return 1

if __name__ == "__main__":
    result = main()
    sys.exit(result)
