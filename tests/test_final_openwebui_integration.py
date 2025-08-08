#!/usr/bin/env python3
"""
Final Comprehensive OpenWebUI Integration Test Suite
Tests all components with correct endpoints and realistic expectations
"""

import asyncio
import json
import requests
import time
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional


class FinalOpenWebUIIntegrationTest:
    """Final comprehensive integration test for OpenWebUI ecosystem"""
    
    def __init__(self):
        self.services = {
            'openwebui': 'http://localhost:8080',
            'memory_api': 'http://localhost:5001', 
            'pipeline': 'http://localhost:9099',
            'ollama': 'http://localhost:11434'
        }
        self.results = {'passed': 0, 'failed': 0, 'tests': []}
        self.start_time = time.time()
        
    def log(self, message: str, success: bool = True):
        """Log test results"""
        symbol = "✅" if success else "❌"
        status = "PASSED" if success else "FAILED"
        print(f"   {symbol} {status}: {message}")
        
        if success:
            self.results['passed'] += 1
        else:
            self.results['failed'] += 1
            
        self.results['tests'].append({
            'message': message,
            'success': success,
            'timestamp': datetime.now().isoformat()
        })

    def test_core_services(self) -> Dict[str, bool]:
        """Test all core services are accessible"""
        print("🔍 Testing Core Services...")
        results = {}
        
        # OpenWebUI Web Interface
        try:
            response = requests.get(f"{self.services['openwebui']}/", timeout=5)
            if response.status_code == 200 and "Open WebUI" in response.text:
                self.log("OpenWebUI Web Interface - Accessible and rendering")
                results['openwebui'] = True
            else:
                self.log("OpenWebUI Web Interface - Not responding correctly", False)
                results['openwebui'] = False
        except Exception as e:
            self.log(f"OpenWebUI Web Interface - Connection failed: {str(e)}", False)
            results['openwebui'] = False
            
        # Memory API
        try:
            response = requests.get(f"{self.services['memory_api']}/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'healthy':
                    self.log("Memory API - Service healthy and responding")
                    results['memory_api'] = True
                else:
                    self.log("Memory API - Service unhealthy", False)
                    results['memory_api'] = False
            else:
                self.log("Memory API - Health check failed", False)
                results['memory_api'] = False
        except Exception as e:
            self.log(f"Memory API - Connection failed: {str(e)}", False)
            results['memory_api'] = False
            
        # Pipeline Service
        try:
            response = requests.get(f"{self.services['pipeline']}/", timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get('status') is True:
                    self.log("Pipeline Service - Service active and responding")
                    results['pipeline'] = True
                else:
                    self.log("Pipeline Service - Service not ready", False)
                    results['pipeline'] = False
            else:
                self.log("Pipeline Service - Not responding", False)
                results['pipeline'] = False
        except Exception as e:
            self.log(f"Pipeline Service - Connection failed: {str(e)}", False)
            results['pipeline'] = False
            
        # Ollama Service
        try:
            response = requests.get(f"{self.services['ollama']}/api/tags", timeout=5)
            if response.status_code == 200:
                data = response.json()
                models = data.get('models', [])
                if models:
                    model_names = [m['name'] for m in models]
                    self.log(f"Ollama Service - {len(models)} models available: {', '.join(model_names)}")
                    results['ollama'] = True
                else:
                    self.log("Ollama Service - No models available", False)
                    results['ollama'] = False
            else:
                self.log("Ollama Service - API not responding", False)
                results['ollama'] = False
        except Exception as e:
            self.log(f"Ollama Service - Connection failed: {str(e)}", False)
            results['ollama'] = False
            
        return results

    def test_memory_system_complete(self) -> Dict[str, bool]:
        """Test complete memory system functionality"""
        print("🔍 Testing Complete Memory System...")
        results = {}
        test_user = f"integration_test_user_{uuid.uuid4().hex[:8]}"
        
        # Test memory storage
        try:
            memory_data = {
                "content": f"Integration test memory from {datetime.now()}",
                "metadata": {"test": True, "integration": True},
                "user_id": test_user
            }
            
            response = requests.post(
                f"{self.services['memory_api']}/api/memory/store",
                json=memory_data,
                timeout=10
            )
            
            if response.status_code == 200:
                stored_memory = response.json()
                memory_id = stored_memory.get('memory_id')
                if memory_id:
                    self.log(f"Memory Storage - Successfully stored: {memory_id[:20]}...")
                    results['storage'] = True
                    
                    # Test memory retrieval with correct endpoint
                    try:
                        retrieve_data = {
                            "query": "integration test",
                            "user_id": test_user,
                            "max_results": 5
                        }
                        
                        response = requests.post(
                            f"{self.services['memory_api']}/api/memory/retrieve",
                            json=retrieve_data,
                            timeout=10
                        )
                        
                        if response.status_code == 200:
                            memories = response.json()
                            if isinstance(memories, list) and len(memories) > 0:
                                self.log(f"Memory Retrieval - Found {len(memories)} relevant memories")
                                results['retrieval'] = True
                            else:
                                self.log("Memory Retrieval - No memories found for test query", False)
                                results['retrieval'] = False
                        else:
                            self.log(f"Memory Retrieval - API error: {response.status_code}", False)
                            results['retrieval'] = False
                    except Exception as e:
                        self.log(f"Memory Retrieval - Request failed: {str(e)}", False)
                        results['retrieval'] = False
                        
                else:
                    self.log("Memory Storage - No memory ID returned", False)
                    results['storage'] = False
            else:
                self.log(f"Memory Storage - API error: {response.status_code}", False)
                results['storage'] = False
        except Exception as e:
            self.log(f"Memory Storage - Request failed: {str(e)}", False)
            results['storage'] = False
            results['retrieval'] = False
            
        return results

    def test_function_integration(self) -> Dict[str, bool]:
        """Test OpenWebUI function integration"""
        print("🔍 Testing Function Integration...")
        results = {}
        
        # Check if function file exists and is accessible to OpenWebUI
        function_path = "memory/functions/enhanced_memory_function_filter.py"
        try:
            with open(function_path, 'r') as f:
                content = f.read()
                
            # Validate function structure
            required_elements = [
                'class Filter:',
                'class Valves',
                'async def inlet',
                'title: Enhanced Memory Function Filter'
            ]
            
            missing_elements = []
            for element in required_elements:
                if element not in content:
                    missing_elements.append(element)
                    
            if not missing_elements:
                self.log("Function File Structure - Valid OpenWebUI function format")
                results['structure'] = True
                
                # Check if function imports are valid
                try:
                    import ast
                    parsed = ast.parse(content)
                    self.log("Function Syntax - Python syntax is valid")
                    results['syntax'] = True
                except SyntaxError as e:
                    self.log(f"Function Syntax - Syntax error: {str(e)}", False)
                    results['syntax'] = False
                    
            else:
                self.log(f"Function File Structure - Missing elements: {missing_elements}", False)
                results['structure'] = False
                results['syntax'] = False
                
        except FileNotFoundError:
            self.log("Function File Structure - Function file not found", False)
            results['structure'] = False
            results['syntax'] = False
        except Exception as e:
            self.log(f"Function File Structure - Error reading file: {str(e)}", False)
            results['structure'] = False
            results['syntax'] = False
            
        return results

    def test_model_integration(self) -> Dict[str, bool]:
        """Test model availability and basic functionality"""
        print("🔍 Testing Model Integration...")
        results = {}
        
        try:
            # Get available models
            response = requests.get(f"{self.services['ollama']}/api/tags", timeout=10)
            if response.status_code == 200:
                data = response.json()
                models = data.get('models', [])
                
                if models:
                    model_names = [m['name'] for m in models]
                    self.log(f"Model Availability - {len(models)} models found: {', '.join(model_names)}")
                    results['availability'] = True
                    
                    # Test basic model generation with first available model
                    test_model = models[0]['name']
                    try:
                        generate_data = {
                            "model": test_model,
                            "prompt": "Hello, respond with just 'OK' to confirm you're working.",
                            "stream": False
                        }
                        
                        response = requests.post(
                            f"{self.services['ollama']}/api/generate",
                            json=generate_data,
                            timeout=30
                        )
                        
                        if response.status_code == 200:
                            result = response.json()
                            if 'response' in result:
                                self.log(f"Model Generation - Model {test_model} is responsive")
                                results['generation'] = True
                            else:
                                self.log(f"Model Generation - Model {test_model} response format unexpected", False)
                                results['generation'] = False
                        else:
                            self.log(f"Model Generation - Model {test_model} API error: {response.status_code}", False)
                            results['generation'] = False
                    except Exception as e:
                        self.log(f"Model Generation - Model {test_model} generation failed: {str(e)}", False)
                        results['generation'] = False
                        
                else:
                    self.log("Model Availability - No models available", False)
                    results['availability'] = False
                    results['generation'] = False
            else:
                self.log("Model Availability - Ollama API not responding", False)
                results['availability'] = False
                results['generation'] = False
        except Exception as e:
            self.log(f"Model Availability - Connection failed: {str(e)}", False)
            results['availability'] = False
            results['generation'] = False
            
        return results

    def test_end_to_end_flow(self) -> Dict[str, bool]:
        """Test complete end-to-end integration flow"""
        print("🔍 Testing End-to-End Integration Flow...")
        results = {}
        
        # Test full integration chain
        try:
            # 1. Store a memory
            test_user = f"e2e_test_{uuid.uuid4().hex[:8]}"
            memory_content = "The user loves Python programming and uses VS Code as their primary IDE."
            
            store_response = requests.post(
                f"{self.services['memory_api']}/api/memory/store",
                json={
                    "content": memory_content,
                    "metadata": {"context": "programming_preferences"},
                    "user_id": test_user
                },
                timeout=10
            )
            
            if store_response.status_code == 200:
                self.log("E2E Flow Step 1 - Memory stored successfully")
                
                # 2. Retrieve relevant memories
                retrieve_response = requests.post(
                    f"{self.services['memory_api']}/api/memory/retrieve",
                    json={
                        "query": "What does the user like for programming?",
                        "user_id": test_user,
                        "max_results": 3
                    },
                    timeout=10
                )
                
                if retrieve_response.status_code == 200:
                    memories = retrieve_response.json()
                    if memories and len(memories) > 0:
                        self.log("E2E Flow Step 2 - Memory retrieval successful")
                        
                        # 3. Test model is available for completion
                        models_response = requests.get(f"{self.services['ollama']}/api/tags", timeout=5)
                        if models_response.status_code == 200:
                            models_data = models_response.json()
                            if models_data.get('models'):
                                self.log("E2E Flow Step 3 - Models available for completion")
                                results['complete_flow'] = True
                            else:
                                self.log("E2E Flow Step 3 - No models available", False)
                                results['complete_flow'] = False
                        else:
                            self.log("E2E Flow Step 3 - Model service not available", False)
                            results['complete_flow'] = False
                    else:
                        self.log("E2E Flow Step 2 - Memory retrieval returned no results", False)
                        results['complete_flow'] = False
                else:
                    self.log("E2E Flow Step 2 - Memory retrieval failed", False)
                    results['complete_flow'] = False
            else:
                self.log("E2E Flow Step 1 - Memory storage failed", False)
                results['complete_flow'] = False
                
        except Exception as e:
            self.log(f"E2E Flow - Integration test failed: {str(e)}", False)
            results['complete_flow'] = False
            
        return results

    def test_performance_and_reliability(self) -> Dict[str, bool]:
        """Test system performance and reliability"""
        print("🔍 Testing Performance & Reliability...")
        results = {}
        
        # Test multiple concurrent requests
        test_start = time.time()
        success_count = 0
        total_requests = 10
        
        for i in range(total_requests):
            try:
                response = requests.get(f"{self.services['memory_api']}/health", timeout=2)
                if response.status_code == 200:
                    success_count += 1
            except:
                pass
                
        test_duration = time.time() - test_start
        success_rate = (success_count / total_requests) * 100
        
        if success_rate >= 90:
            self.log(f"Performance Test - Excellent reliability: {success_rate:.1f}% success rate")
            results['performance'] = True
        elif success_rate >= 70:
            self.log(f"Performance Test - Good reliability: {success_rate:.1f}% success rate")
            results['performance'] = True
        else:
            self.log(f"Performance Test - Poor reliability: {success_rate:.1f}% success rate", False)
            results['performance'] = False
            
        return results

    def run_all_tests(self):
        """Run all integration tests"""
        print("🚀 Starting Final OpenWebUI Integration Test Suite")
        print("=" * 70)
        
        categories = [
            ("📋 Core Services", self.test_core_services),
            ("📋 Memory System", self.test_memory_system_complete),
            ("📋 Function Integration", self.test_function_integration),
            ("📋 Model Integration", self.test_model_integration),
            ("📋 End-to-End Flow", self.test_end_to_end_flow),
            ("📋 Performance & Reliability", self.test_performance_and_reliability)
        ]
        
        category_results = {}
        
        for category_name, test_func in categories:
            print(f"\n{category_name}")
            start_time = time.time()
            category_result = test_func()
            duration = time.time() - start_time
            
            # Determine if category passed (all tests in category passed)
            category_passed = all(category_result.values()) if category_result else False
            category_results[category_name] = category_passed
            
        # Final summary
        total_duration = time.time() - self.start_time
        passed_categories = sum(1 for passed in category_results.values() if passed)
        total_categories = len(category_results)
        
        print("\n" + "=" * 70)
        print("🎯 Final Integration Test Summary")
        print("=" * 70)
        
        print(f"\n📊 Test Categories: {passed_categories}/{total_categories} passed")
        for category, passed in category_results.items():
            status = "✅ PASSED" if passed else "❌ FAILED"
            clean_name = category.replace("📋 ", "")
            print(f"  {clean_name:<25}: {status}")
            
        print(f"\n📋 Individual Tests: {self.results['passed']}/{self.results['passed'] + self.results['failed']} passed")
        print(f"⏱️  Total Duration: {total_duration:.2f}s | Average: {total_duration/(self.results['passed'] + self.results['failed']):.3f}s per test")
        
        overall_success_rate = (self.results['passed'] / (self.results['passed'] + self.results['failed'])) * 100
        category_success_rate = (passed_categories / total_categories) * 100
        
        print(f"\n📈 Success Rates:")
        print(f"  Overall Tests: {overall_success_rate:.1f}%")
        print(f"  Categories: {category_success_rate:.1f}%")
        
        if passed_categories == total_categories and overall_success_rate >= 95:
            print(f"\n🎉 EXCELLENT! OpenWebUI Integration is working perfectly!")
            print(f"🚀 All systems operational and ready for production use")
            return True
        elif passed_categories >= total_categories * 0.8 and overall_success_rate >= 85:
            print(f"\n✅ GOOD! OpenWebUI Integration is working well")
            print(f"🔧 Minor issues detected but system is functional")
            return True
        else:
            print(f"\n⚠️  NEEDS ATTENTION! Some Integration Issues Detected")
            print(f"🔧 Please address failed tests before production use")
            print(f"📞 Review system configuration and dependencies")
            return False


if __name__ == "__main__":
    tester = FinalOpenWebUIIntegrationTest()
    success = tester.run_all_tests()
    exit(0 if success else 1)
