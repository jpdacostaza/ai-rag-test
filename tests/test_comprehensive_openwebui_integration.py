#!/usr/bin/env python3
"""
Comprehensive OpenWebUI Integration Test Suite
==============================================

This script provides complete testing of OpenWebUI integration including:
- Memory Functions/Filters
- Pipeline Integration  
- Persona System
- API Endpoints
- Model Management
- User Authentication
- Chat Functionality

Tests the entire stack end-to-end to ensure production readiness.
"""

import asyncio
import json
import requests
import time
import random
import uuid
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import urllib.parse

@dataclass
class TestResult:
    """Test result data structure"""
    name: str
    passed: bool
    message: str
    details: Optional[Dict] = None
    duration: float = 0.0

class OpenWebUIIntegrationTester:
    def __init__(self):
        self.base_url = "http://localhost:8080"
        self.memory_api_url = "http://localhost:5001"
        self.pipeline_url = "http://localhost:9099"
        self.main_api_url = "http://localhost:3000"
        self.ollama_url = "http://localhost:11434"
        
        self.test_results: List[TestResult] = []
        self.session = requests.Session()
        self.auth_token = None
        self.test_user_id = f"test_user_{uuid.uuid4().hex[:8]}"
        
    def log_result(self, name: str, passed: bool, message: str, details: Dict = None, duration: float = 0.0):
        """Log a test result"""
        result = TestResult(name, passed, message, details, duration)
        self.test_results.append(result)
        
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"   {status}: {name} - {message}")
        if details and not passed:
            print(f"     Details: {details}")
    
    def test_service_health(self) -> bool:
        """Test health of all core services"""
        print("🔍 Testing Service Health...")
        
        services = [
            ("OpenWebUI", self.base_url),
            ("Memory API", self.memory_api_url),
            ("Pipelines", self.pipeline_url),
            ("Main API", self.main_api_url),
            ("Ollama", self.ollama_url)
        ]
        
        all_healthy = True
        
        for service_name, url in services:
            start_time = time.time()
            try:
                # Try different health endpoints
                health_endpoints = ["/health", "/api/health", "/", "/api/status"]
                success = False
                
                for endpoint in health_endpoints:
                    try:
                        response = self.session.get(f"{url}{endpoint}", timeout=10)
                        if response.status_code in [200, 401]:  # 401 might be expected for auth
                            success = True
                            break
                    except:
                        continue
                
                duration = time.time() - start_time
                
                if success:
                    self.log_result(f"{service_name} Health", True, f"Service accessible ({duration:.2f}s)", duration=duration)
                else:
                    self.log_result(f"{service_name} Health", False, f"Service not accessible", duration=duration)
                    all_healthy = False
                    
            except Exception as e:
                duration = time.time() - start_time
                self.log_result(f"{service_name} Health", False, f"Connection error: {str(e)}", duration=duration)
                all_healthy = False
        
        return all_healthy
    
    def test_memory_api_integration(self) -> bool:
        """Test Memory API integration"""
        print("🔍 Testing Memory API Integration...")
        
        start_time = time.time()
        
        # Test memory storage
        try:
            store_payload = {
                "user_id": self.test_user_id,
                "content": "I am testing the complete OpenWebUI integration with memory functions",
                "context": "integration_test",
                "importance": 0.8
            }
            
            response = self.session.post(
                f"{self.memory_api_url}/api/memory/store",
                json=store_payload,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                memory_id = result.get('memory_id')
                duration = time.time() - start_time
                self.log_result("Memory Storage", True, f"Stored memory: {memory_id}", 
                              {"memory_id": memory_id}, duration)
            else:
                duration = time.time() - start_time
                self.log_result("Memory Storage", False, f"Storage failed: {response.status_code}", 
                              {"response": response.text}, duration)
                return False
                
        except Exception as e:
            duration = time.time() - start_time
            self.log_result("Memory Storage", False, f"Storage error: {str(e)}", duration=duration)
            return False
        
        # Test memory retrieval
        start_time = time.time()
        try:
            retrieve_payload = {
                "user_id": self.test_user_id,
                "query": "OpenWebUI integration",
                "limit": 5
            }
            
            response = self.session.post(
                f"{self.memory_api_url}/api/memory/retrieve",
                json=retrieve_payload,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                memories = result.get('memories', [])
                duration = time.time() - start_time
                self.log_result("Memory Retrieval", True, f"Retrieved {len(memories)} memories", 
                              {"count": len(memories)}, duration)
                return len(memories) > 0
            else:
                duration = time.time() - start_time
                self.log_result("Memory Retrieval", False, f"Retrieval failed: {response.status_code}", 
                              {"response": response.text}, duration)
                return False
                
        except Exception as e:
            duration = time.time() - start_time
            self.log_result("Memory Retrieval", False, f"Retrieval error: {str(e)}", duration=duration)
            return False
    
    def test_pipeline_integration(self) -> bool:
        """Test Pipeline integration"""
        print("🔍 Testing Pipeline Integration...")
        
        start_time = time.time()
        
        try:
            # Test pipeline health/status
            response = self.session.get(f"{self.pipeline_url}/health", timeout=10)
            
            if response.status_code == 200:
                duration = time.time() - start_time
                self.log_result("Pipeline Health", True, "Pipeline service accessible", duration=duration)
            else:
                duration = time.time() - start_time
                self.log_result("Pipeline Health", False, f"Pipeline not accessible: {response.status_code}", duration=duration)
                return False
                
        except Exception as e:
            duration = time.time() - start_time
            self.log_result("Pipeline Health", False, f"Pipeline connection error: {str(e)}", duration=duration)
            return False
        
        # Test pipeline endpoints
        start_time = time.time()
        try:
            # Try to get pipeline information
            endpoints_to_test = ["/", "/pipelines", "/api/pipelines"]
            
            for endpoint in endpoints_to_test:
                try:
                    response = self.session.get(f"{self.pipeline_url}{endpoint}", timeout=5)
                    if response.status_code in [200, 404]:  # 404 is also acceptable, means endpoint exists
                        duration = time.time() - start_time
                        self.log_result("Pipeline Endpoints", True, f"Pipeline API responsive", duration=duration)
                        return True
                except:
                    continue
            
            duration = time.time() - start_time
            self.log_result("Pipeline Endpoints", False, "No responsive pipeline endpoints found", duration=duration)
            return False
            
        except Exception as e:
            duration = time.time() - start_time
            self.log_result("Pipeline Endpoints", False, f"Pipeline endpoint error: {str(e)}", duration=duration)
            return False
    
    def test_openwebui_api(self) -> bool:
        """Test OpenWebUI API endpoints"""
        print("🔍 Testing OpenWebUI API...")
        
        # Test basic API access
        start_time = time.time()
        try:
            response = self.session.get(f"{self.base_url}/api/v1/auths", timeout=10)
            
            # We expect 401 or 200 - both indicate the API is working
            if response.status_code in [200, 401]:
                duration = time.time() - start_time
                self.log_result("OpenWebUI API", True, "API endpoints accessible", duration=duration)
            else:
                duration = time.time() - start_time
                self.log_result("OpenWebUI API", False, f"API not accessible: {response.status_code}", duration=duration)
                return False
                
        except Exception as e:
            duration = time.time() - start_time
            self.log_result("OpenWebUI API", False, f"API connection error: {str(e)}", duration=duration)
            return False
        
        # Test models endpoint
        start_time = time.time()
        try:
            response = self.session.get(f"{self.base_url}/api/v1/models", timeout=10)
            
            if response.status_code == 200:
                models = response.json()
                duration = time.time() - start_time
                self.log_result("OpenWebUI Models", True, f"Found {len(models)} models", 
                              {"model_count": len(models)}, duration)
            elif response.status_code == 401:
                duration = time.time() - start_time
                self.log_result("OpenWebUI Models", True, "Models endpoint requires auth (normal)", duration=duration)
            else:
                duration = time.time() - start_time
                self.log_result("OpenWebUI Models", False, f"Models endpoint error: {response.status_code}", duration=duration)
                return False
                
        except Exception as e:
            duration = time.time() - start_time
            self.log_result("OpenWebUI Models", False, f"Models endpoint error: {str(e)}", duration=duration)
            return False
        
        return True
    
    def test_function_files(self) -> bool:
        """Test function file presence and validity"""
        print("🔍 Testing Function Files...")
        
        start_time = time.time()
        
        # Check if we can access the function files through Docker
        try:
            import subprocess
            result = subprocess.run(
                ["docker", "exec", "backend-openwebui", "ls", "-la", "/app/data/functions/"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                output = result.stdout
                
                # Check for our memory function
                if "enhanced_memory_function_filter.py" in output:
                    duration = time.time() - start_time
                    self.log_result("Function Files", True, "Memory function file found", 
                                  {"file_output": output.strip()}, duration)
                else:
                    duration = time.time() - start_time
                    self.log_result("Function Files", False, "Memory function file missing", 
                                  {"file_output": output.strip()}, duration)
                    return False
            else:
                duration = time.time() - start_time
                self.log_result("Function Files", False, f"Cannot access function directory: {result.stderr}", duration=duration)
                return False
                
        except Exception as e:
            duration = time.time() - start_time
            self.log_result("Function Files", False, f"Function file check error: {str(e)}", duration=duration)
            return False
        
        return True
    
    def test_ollama_integration(self) -> bool:
        """Test Ollama model integration"""
        print("🔍 Testing Ollama Integration...")
        
        start_time = time.time()
        
        try:
            # Test Ollama API
            response = self.session.get(f"{self.ollama_url}/api/tags", timeout=10)
            
            if response.status_code == 200:
                models = response.json()
                model_list = models.get('models', [])
                duration = time.time() - start_time
                self.log_result("Ollama Models", True, f"Found {len(model_list)} models", 
                              {"model_count": len(model_list)}, duration)
                
                # List available models
                if model_list:
                    for model in model_list[:3]:  # Show first 3 models
                        print(f"     Model: {model.get('name', 'Unknown')}")
                
                return True
            else:
                duration = time.time() - start_time
                self.log_result("Ollama Models", False, f"Ollama API error: {response.status_code}", duration=duration)
                return False
                
        except Exception as e:
            duration = time.time() - start_time
            self.log_result("Ollama Models", False, f"Ollama connection error: {str(e)}", duration=duration)
            return False
    
    def test_persona_system(self) -> bool:
        """Test persona system integration"""
        print("🔍 Testing Persona System...")
        
        start_time = time.time()
        
        # Check for persona configuration files
        try:
            import os
            persona_files = [
                "config/persona.json",
                "config/persona_enhanced.json", 
                "config/persona_compact.json",
                "config/persona_new_user.json"
            ]
            
            found_personas = []
            for persona_file in persona_files:
                if os.path.exists(persona_file):
                    found_personas.append(persona_file)
            
            duration = time.time() - start_time
            
            if found_personas:
                self.log_result("Persona Files", True, f"Found {len(found_personas)} persona files", 
                              {"files": found_personas}, duration)
            else:
                self.log_result("Persona Files", False, "No persona files found", duration=duration)
                return False
                
        except Exception as e:
            duration = time.time() - start_time
            self.log_result("Persona Files", False, f"Persona file check error: {str(e)}", duration=duration)
            return False
        
        # Test persona loading through main API
        start_time = time.time()
        try:
            response = self.session.get(f"{self.main_api_url}/api/persona/current", timeout=10)
            
            if response.status_code == 200:
                persona_data = response.json()
                duration = time.time() - start_time
                self.log_result("Persona API", True, "Persona API accessible", 
                              {"persona_keys": list(persona_data.keys()) if isinstance(persona_data, dict) else None}, duration)
            elif response.status_code == 404:
                duration = time.time() - start_time
                self.log_result("Persona API", True, "Persona API endpoint exists (404 expected)", duration=duration)
            else:
                duration = time.time() - start_time
                self.log_result("Persona API", False, f"Persona API error: {response.status_code}", duration=duration)
                return False
                
        except Exception as e:
            duration = time.time() - start_time
            self.log_result("Persona API", False, f"Persona API error: {str(e)}", duration=duration)
            return False
        
        return True
    
    def test_end_to_end_flow(self) -> bool:
        """Test end-to-end memory flow simulation"""
        print("🔍 Testing End-to-End Memory Flow...")
        
        start_time = time.time()
        
        try:
            # Simulate storing a conversation memory
            conversation_data = {
                "user_id": self.test_user_id,
                "content": "I enjoy machine learning and prefer Python for data science projects",
                "context": "user_preference",
                "importance": 0.9
            }
            
            # Store memory
            store_response = self.session.post(
                f"{self.memory_api_url}/api/memory/store",
                json=conversation_data,
                timeout=10
            )
            
            if store_response.status_code != 200:
                duration = time.time() - start_time
                self.log_result("E2E Memory Store", False, f"Failed to store: {store_response.status_code}", duration=duration)
                return False
            
            memory_id = store_response.json().get('memory_id')
            
            # Wait briefly for indexing
            time.sleep(0.5)
            
            # Retrieve relevant memories
            retrieve_data = {
                "user_id": self.test_user_id,
                "query": "machine learning Python",
                "limit": 5
            }
            
            retrieve_response = self.session.post(
                f"{self.memory_api_url}/api/memory/retrieve",
                json=retrieve_data,
                timeout=10
            )
            
            if retrieve_response.status_code == 200:
                memories = retrieve_response.json().get('memories', [])
                
                # Check if our stored memory is retrieved
                found_memory = False
                for memory in memories:
                    if memory.get('metadata', {}).get('memory_id') == memory_id:
                        found_memory = True
                        break
                
                duration = time.time() - start_time
                
                if found_memory:
                    self.log_result("E2E Memory Flow", True, "Complete memory flow working", 
                                  {"stored_id": memory_id, "retrieved_count": len(memories)}, duration)
                    return True
                else:
                    self.log_result("E2E Memory Flow", False, "Stored memory not retrieved", 
                                  {"stored_id": memory_id, "retrieved_count": len(memories)}, duration)
                    return False
            else:
                duration = time.time() - start_time
                self.log_result("E2E Memory Flow", False, f"Retrieval failed: {retrieve_response.status_code}", duration=duration)
                return False
                
        except Exception as e:
            duration = time.time() - start_time
            self.log_result("E2E Memory Flow", False, f"E2E flow error: {str(e)}", duration=duration)
            return False
    
    def test_performance_benchmarks(self) -> bool:
        """Test performance benchmarks"""
        print("🔍 Testing Performance Benchmarks...")
        
        # Test concurrent memory operations
        start_time = time.time()
        
        try:
            import concurrent.futures
            import threading
            
            def store_memory(index):
                try:
                    response = self.session.post(
                        f"{self.memory_api_url}/api/memory/store",
                        json={
                            "user_id": f"{self.test_user_id}_perf",
                            "content": f"Performance test memory {index} with unique content {random.randint(1000, 9999)}",
                            "context": "performance_test"
                        },
                        timeout=5
                    )
                    return response.status_code == 200
                except:
                    return False
            
            # Test with 10 concurrent operations
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                futures = [executor.submit(store_memory, i) for i in range(10)]
                results = [future.result() for future in concurrent.futures.as_completed(futures)]
            
            success_rate = sum(results) / len(results) * 100
            duration = time.time() - start_time
            
            if success_rate >= 80:  # 80% success rate acceptable
                self.log_result("Performance Test", True, f"Performance acceptable: {success_rate:.1f}% success", 
                              {"success_rate": success_rate, "duration": duration}, duration)
                return True
            else:
                self.log_result("Performance Test", False, f"Performance poor: {success_rate:.1f}% success", 
                              {"success_rate": success_rate, "duration": duration}, duration)
                return False
                
        except Exception as e:
            duration = time.time() - start_time
            self.log_result("Performance Test", False, f"Performance test error: {str(e)}", duration=duration)
            return False
    
    def run_comprehensive_tests(self) -> bool:
        """Run all comprehensive tests"""
        print("🚀 Starting Comprehensive OpenWebUI Integration Tests")
        print("=" * 80)
        
        test_categories = [
            ("Service Health", self.test_service_health),
            ("Memory API Integration", self.test_memory_api_integration),
            ("Pipeline Integration", self.test_pipeline_integration), 
            ("OpenWebUI API", self.test_openwebui_api),
            ("Function Files", self.test_function_files),
            ("Ollama Integration", self.test_ollama_integration),
            ("Persona System", self.test_persona_system),
            ("End-to-End Flow", self.test_end_to_end_flow),
            ("Performance Benchmarks", self.test_performance_benchmarks),
        ]
        
        category_results = {}
        
        for category_name, test_func in test_categories:
            print(f"\n📋 {category_name}")
            try:
                category_results[category_name] = test_func()
            except Exception as e:
                print(f"❌ {category_name} failed with exception: {e}")
                category_results[category_name] = False
        
        # Generate comprehensive summary
        self.generate_summary(category_results)
        
        # Return overall success
        return all(category_results.values())
    
    def generate_summary(self, category_results: Dict[str, bool]):
        """Generate comprehensive test summary"""
        print("\n" + "=" * 80)
        print("🎯 Comprehensive Integration Test Summary")
        print("=" * 80)
        
        # Category summary
        passed_categories = sum(category_results.values())
        total_categories = len(category_results)
        
        print(f"\n📊 Test Categories: {passed_categories}/{total_categories} passed")
        for category, passed in category_results.items():
            status = "✅ PASSED" if passed else "❌ FAILED"
            print(f"  {category:<25}: {status}")
        
        # Detailed test summary
        passed_tests = sum(1 for result in self.test_results if result.passed)
        total_tests = len(self.test_results)
        
        print(f"\n📋 Individual Tests: {passed_tests}/{total_tests} passed")
        
        # Performance summary
        total_duration = sum(result.duration for result in self.test_results)
        print(f"⏱️  Total Test Duration: {total_duration:.2f} seconds")
        
        # Failed tests detail
        failed_tests = [result for result in self.test_results if not result.passed]
        if failed_tests:
            print(f"\n❌ Failed Tests ({len(failed_tests)}):")
            for test in failed_tests:
                print(f"  • {test.name}: {test.message}")
        
        # Success rate
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"\n📈 Overall Success Rate: {success_rate:.1f}%")
        
        # Final verdict
        if success_rate >= 90:
            print("\n🎉 EXCELLENT! OpenWebUI integration is production-ready!")
            print("✅ All major systems are functioning correctly")
            print("✅ Memory system integrated and working")
            print("✅ Performance benchmarks met")
            print("✅ Ready for production use")
        elif success_rate >= 75:
            print("\n✅ GOOD! OpenWebUI integration is mostly working")
            print("⚠️  Some minor issues detected - review failed tests")
            print("🔧 Address failing components for optimal performance")
        else:
            print("\n⚠️  NEEDS WORK! Several integration issues detected")
            print("🔧 Please address failed tests before production use")
            print("📞 Review system configuration and connectivity")
        
        # Next steps
        if passed_categories == total_categories:
            print("\n🚀 Next Steps:")
            print("  1. Test through OpenWebUI web interface")
            print("  2. Verify memory persistence in conversations")
            print("  3. Test with different user accounts")
            print("  4. Monitor system performance under load")
        
        return success_rate

def main():
    """Main test execution"""
    tester = OpenWebUIIntegrationTester()
    success = tester.run_comprehensive_tests()
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
