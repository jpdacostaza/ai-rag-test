#!/usr/bin/env python3
"""
Comprehensive Smart Anti-Hallucination System Test Suite
=======================================================

This comprehensive test suite combines all individual tests into one unified test
that validates the complete Smart Anti-Hallucination System functionality:

1. Smart Web Search Trigger Logic
2. Memory System Integration
3. Pipeline Health & Configuration
4. Anti-Fabrication Measures
5. Web Search Functionality
6. Uncertainty Detection
7. System Integration & Performance

Run this after starting Docker containers to verify complete system functionality.
"""

import asyncio
import json
import time
import sys
import os
import requests
import httpx
from datetime import datetime
from typing import Dict, List, Optional, Any

# Add project paths
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class ComprehensiveSystemTester:
    def __init__(self):
        # Service URLs
        self.openwebui_url = "http://localhost:8080"
        self.memory_api_url = "http://localhost:5001" 
        self.pipelines_url = "http://localhost:9099"
        self.backend_url = "http://localhost:3000"
        self.redis_url = "redis://localhost:6379"
        self.chroma_url = "http://localhost:8000"
        
        # Test configuration
        self.test_user_id = "comprehensive_test_user"
        self.start_time = time.time()
        self.results = {
            "total_tests": 0,
            "passed_tests": 0,
            "failed_tests": 0,
            "test_details": []
        }
    
    def log(self, message: str, level: str = "INFO"):
        """Enhanced logging with timestamps and levels"""
        timestamp = time.strftime("%H:%M:%S")
        elapsed = time.time() - self.start_time
        emoji = {
            "INFO": "📝", "SUCCESS": "✅", "WARNING": "⚠️", 
            "ERROR": "❌", "DEBUG": "🔍", "TEST": "🧪",
            "SECTION": "🎯", "RESULT": "📊"
        }.get(level, "📝")
        print(f"[{timestamp}] {emoji} [{level}] [{elapsed:.1f}s] {message}")
    
    def record_test(self, test_name: str, passed: bool, details: str = ""):
        """Record test results for final summary"""
        self.results["total_tests"] += 1
        if passed:
            self.results["passed_tests"] += 1
        else:
            self.results["failed_tests"] += 1
        
        self.results["test_details"].append({
            "name": test_name,
            "passed": passed,
            "details": details,
            "timestamp": time.time()
        })
    
    # =====================================
    # 1. SMART WEB SEARCH TRIGGER TESTS
    # =====================================
    
    def test_smart_trigger_logic(self) -> bool:
        """Test the smart web search trigger logic with comprehensive scenarios"""
        self.log("Testing Smart Web Search Trigger Logic", "SECTION")
        
        try:
            from utilities.smart_web_search_trigger import should_trigger_web_search_smart
            
            test_cases = [
                # Should NOT trigger (confident model responses)
                {
                    "query": "What does Swift company do?",
                    "response": "Swift is a financial technology company that provides secure messaging services for banks.",
                    "expected": False,
                    "description": "Known company with confident response"
                },
                {
                    "query": "Hello my name is J.P. I work at swift, can you remember that?",
                    "response": "Hello J.P.! Yes, I'll remember that you work at Swift.",
                    "expected": False,
                    "description": "Personal introduction - no search needed"
                },
                {
                    "query": "What is Python programming?",
                    "response": "Python is a high-level programming language known for its simplicity and readability.",
                    "expected": False,
                    "description": "General knowledge with confident response"
                },
                
                # Should trigger (model uncertainty)
                {
                    "query": "What is the latest financial report from XyzCorp999?",
                    "response": "I don't have specific information about XyzCorp999's latest financial report.",
                    "expected": True,
                    "description": "Unknown entity with uncertainty"
                },
                {
                    "query": "What happened in the news today?",
                    "response": "I'm not sure about today's specific news events.",
                    "expected": True,
                    "description": "Current events with uncertainty"
                },
                {
                    "query": "Tell me about the recent developments at TechCorp",
                    "response": "I don't have current information about TechCorp's recent developments.",
                    "expected": True,
                    "description": "Recent developments with knowledge gap"
                },
                
                # Should trigger (explicit requests)
                {
                    "query": "Search the web for Swift company latest news",
                    "response": "I'll search for the latest news about Swift company.",
                    "expected": True,
                    "description": "Explicit search request"
                },
                {
                    "query": "Look up current information about Tesla stock",
                    "response": "Let me look up current Tesla stock information.",
                    "expected": True,
                    "description": "Explicit lookup request"
                }
            ]
            
            passed_count = 0
            for i, test_case in enumerate(test_cases, 1):
                result = should_trigger_web_search_smart(test_case["query"], test_case["response"])
                
                # Handle both tuple (bool, reason) and bool return formats
                if isinstance(result, tuple):
                    trigger_result, reason = result
                else:
                    trigger_result = result
                    reason = "No reason provided"
                
                passed = trigger_result == test_case["expected"]
                
                if passed:
                    passed_count += 1
                    self.log(f"Test {i}/8 PASSED: {test_case['description']}", "SUCCESS")
                else:
                    self.log(f"Test {i}/8 FAILED: {test_case['description']} (got {trigger_result}, expected {test_case['expected']}) - {reason}", "ERROR")
                
                self.record_test(f"Smart Trigger Test {i}", passed, test_case["description"])
            
            overall_passed = passed_count == len(test_cases)
            self.log(f"Smart Trigger Logic: {passed_count}/{len(test_cases)} tests passed", "RESULT")
            return overall_passed
            
        except ImportError as e:
            self.log(f"Smart trigger utility not available: {e}", "ERROR")
            self.record_test("Smart Trigger Logic", False, f"Import error: {e}")
            return False
        except Exception as e:
            self.log(f"Smart trigger test failed: {e}", "ERROR")
            self.record_test("Smart Trigger Logic", False, f"Test error: {e}")
            return False
    
    # =====================================
    # 2. SERVICE HEALTH TESTS
    # =====================================
    
    async def test_service_health(self) -> bool:
        """Test health of all system services"""
        self.log("Testing Service Health", "SECTION")
        
        services = [
            ("Memory API", self.memory_api_url, "/health"),
            ("Pipelines", self.pipelines_url, "/"),
            ("Backend API", self.backend_url, "/health"),
            ("ChromaDB", self.chroma_url, "/api/v1/heartbeat")
        ]
        
        healthy_services = 0
        for name, url, endpoint in services:
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.get(f"{url}{endpoint}")
                    if response.status_code in [200, 201]:
                        self.log(f"{name} is healthy", "SUCCESS")
                        healthy_services += 1
                        self.record_test(f"{name} Health", True, f"Status: {response.status_code}")
                    else:
                        self.log(f"{name} responded with status {response.status_code}", "WARNING")
                        self.record_test(f"{name} Health", False, f"Status: {response.status_code}")
            except Exception as e:
                self.log(f"{name} is not accessible: {e}", "ERROR")
                self.record_test(f"{name} Health", False, f"Connection error: {e}")
        
        self.log(f"Service Health: {healthy_services}/{len(services)} services healthy", "RESULT")
        return healthy_services == len(services)
    
    # =====================================
    # 3. MEMORY SYSTEM TESTS
    # =====================================
    
    async def test_memory_system(self) -> bool:
        """Test memory storage, retrieval, and anti-fabrication"""
        self.log("Testing Memory System", "SECTION")
        
        try:
            # Test memory storage
            test_interaction = {
                "user_id": self.test_user_id,
                "conversation_id": "comprehensive_test",
                "user_message": "Hello, my name is Alex and I'm a software engineer at TechCorp",
                "assistant_response": "Nice to meet you, Alex! I'll remember that you're a software engineer at TechCorp.",
                "source": "comprehensive_test"
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Store memory
                response = await client.post(
                    f"{self.memory_api_url}/api/learning/process_interaction",
                    json=test_interaction
                )
                
                storage_success = response.status_code == 200
                self.record_test("Memory Storage", storage_success, 
                               f"Status: {response.status_code}" if storage_success else "Failed to store")
                
                if not storage_success:
                    self.log(f"Memory storage failed: {response.status_code}", "ERROR")
                    return False
                
                self.log("Memory storage successful", "SUCCESS")
                
                # Wait for processing
                await asyncio.sleep(2)
                
                # Test memory retrieval
                retrieval_request = {
                    "user_id": self.test_user_id,
                    "query": "What do you know about me?",
                    "limit": 5,
                    "threshold": 0.001
                }
                
                response = await client.post(
                    f"{self.memory_api_url}/api/memory/retrieve",
                    json=retrieval_request
                )
                
                if response.status_code == 200:
                    memories = response.json()
                    retrieval_success = len(memories) > 0
                    self.log(f"Memory retrieval: Found {len(memories)} memories", "SUCCESS" if retrieval_success else "WARNING")
                    self.record_test("Memory Retrieval", retrieval_success, f"Found {len(memories)} memories")
                    return storage_success and retrieval_success
                else:
                    self.log(f"Memory retrieval failed: {response.status_code}", "ERROR")
                    self.record_test("Memory Retrieval", False, f"Status: {response.status_code}")
                    return False
                    
        except Exception as e:
            self.log(f"Memory system test failed: {e}", "ERROR")
            self.record_test("Memory System", False, f"Exception: {e}")
            return False
    
    # =====================================
    # 4. ANTI-FABRICATION TESTS
    # =====================================
    
    def test_anti_fabrication(self) -> bool:
        """Test persona files for anti-fabrication measures"""
        self.log("Testing Anti-Fabrication Measures", "SECTION")
        
        persona_files = [
            "config/persona_unified_small.json",
            "config/persona_new_user.json",
            "config/persona_enhanced.json"
        ]
        
        safe_indicators = [
            "only when provided",
            "never fabricate", 
            "anti-hallucination",
            "don't make up",
            "transparent about",
            "honest about limitations"
        ]
        
        fabrication_indicators = [
            "ALWAYS acknowledge",
            "MUST remember",
            "prove you remember", 
            "I remember you"
        ]
        
        safe_files = 0
        for file_path in persona_files:
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read().lower()
                    
                    safety_count = sum(1 for indicator in safe_indicators if indicator.lower() in content)
                    fabrication_count = sum(1 for indicator in fabrication_indicators if indicator.lower() in content)
                    
                    is_safe = safety_count > 0 and fabrication_count == 0
                    if is_safe:
                        safe_files += 1
                        self.log(f"{os.path.basename(file_path)}: SAFE ({safety_count} safety measures)", "SUCCESS")
                    else:
                        self.log(f"{os.path.basename(file_path)}: RISK ({fabrication_count} risky patterns)", "WARNING")
                    
                    self.record_test(f"Anti-Fabrication {os.path.basename(file_path)}", is_safe,
                                   f"Safety: {safety_count}, Risk: {fabrication_count}")
                    
                except Exception as e:
                    self.log(f"Error reading {file_path}: {e}", "ERROR")
                    self.record_test(f"Anti-Fabrication {os.path.basename(file_path)}", False, f"Read error: {e}")
            else:
                self.log(f"{file_path}: File not found", "WARNING")
                self.record_test(f"Anti-Fabrication {os.path.basename(file_path)}", False, "File not found")
        
        self.log(f"Anti-Fabrication: {safe_files}/{len(persona_files)} persona files are safe", "RESULT")
        return safe_files > 0  # At least one safe persona file
    
    # =====================================
    # 5. WEB SEARCH FUNCTIONALITY TESTS
    # =====================================
    
    async def test_web_search_functionality(self) -> bool:
        """Test web search functionality through DuckDuckGo"""
        self.log("Testing Web Search Functionality", "SECTION")
        
        try:
            # Test direct web search
            test_query = "Swift financial technology company"
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Test DuckDuckGo API directly
                duckduckgo_url = f"https://api.duckduckgo.com/?q={test_query}&format=json&no_html=1&skip_disambig=1"
                response = await client.get(duckduckgo_url)
                
                if response.status_code == 200:
                    data = response.json()
                    has_results = bool(data.get('Abstract') or data.get('Results') or data.get('RelatedTopics'))
                    
                    self.log(f"DuckDuckGo API: {'Working' if has_results else 'Limited results'}", 
                           "SUCCESS" if has_results else "WARNING")
                    self.record_test("DuckDuckGo API", True, f"Status: {response.status_code}")
                    
                    return True
                else:
                    self.log(f"DuckDuckGo API failed: {response.status_code}", "ERROR")
                    self.record_test("DuckDuckGo API", False, f"Status: {response.status_code}")
                    return False
                    
        except Exception as e:
            self.log(f"Web search test failed: {e}", "ERROR") 
            self.record_test("Web Search Functionality", False, f"Exception: {e}")
            return False
    
    # =====================================
    # 6. END-TO-END PIPELINE TESTS
    # =====================================
    
    async def test_end_to_end_pipeline(self) -> bool:
        """Test complete pipeline with different query types"""
        self.log("Testing End-to-End Pipeline", "SECTION")
        
        test_cases = [
            {
                "name": "Known Company Query",
                "query": "What does Swift company do?",
                "should_search": False,
                "description": "Should provide clean response without web search"
            },
            {
                "name": "Uncertainty Query", 
                "query": "What is the latest financial report from XyzCorp999?",
                "should_search": True,
                "description": "Should trigger web search due to uncertainty"
            },
            {
                "name": "Explicit Search Request",
                "query": "Search the web for Swift company latest news",
                "should_search": True,
                "description": "Should trigger web search due to explicit request"
            }
        ]
        
        passed_tests = 0
        
        for test_case in test_cases:
            try:
                # Use the backend chat endpoint
                chat_payload = {
                    "model": "qwen2.5:3b",
                    "messages": [{"role": "user", "content": test_case["query"]}],
                    "stream": False
                }
                
                response = requests.post(
                    f"{self.backend_url}/v1/chat/completions",
                    json=chat_payload,
                    headers={"Content-Type": "application/json"},
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    assistant_message = result.get('choices', [{}])[0].get('message', {}).get('content', '')
                    
                    # Check for web search indicators
                    web_indicators = [
                        "search", "current information", "based on", "according to",
                        "real-time", "latest", "sources", "web search"
                    ]
                    
                    has_web_search = any(indicator in assistant_message.lower() for indicator in web_indicators)
                    
                    test_passed = has_web_search == test_case["should_search"]
                    
                    if test_passed:
                        passed_tests += 1
                        self.log(f"{test_case['name']}: PASSED", "SUCCESS")
                    else:
                        self.log(f"{test_case['name']}: FAILED (expected search: {test_case['should_search']}, got: {has_web_search})", "ERROR")
                    
                    self.record_test(f"E2E {test_case['name']}", test_passed, test_case["description"])
                    
                else:
                    self.log(f"{test_case['name']}: Request failed ({response.status_code})", "ERROR")
                    self.record_test(f"E2E {test_case['name']}", False, f"HTTP {response.status_code}")
                    
            except Exception as e:
                self.log(f"{test_case['name']}: Exception - {e}", "ERROR")
                self.record_test(f"E2E {test_case['name']}", False, f"Exception: {e}")
        
        self.log(f"End-to-End Pipeline: {passed_tests}/{len(test_cases)} tests passed", "RESULT")
        return passed_tests == len(test_cases)
    
    # =====================================
    # 7. SYSTEM PERFORMANCE TESTS
    # =====================================
    
    async def test_system_performance(self) -> bool:
        """Test system response times and resource usage"""
        self.log("Testing System Performance", "SECTION")
        
        try:
            # Test memory API response time
            start_time = time.time()
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.memory_api_url}/health")
                memory_response_time = time.time() - start_time
            
            memory_fast = memory_response_time < 2.0
            self.log(f"Memory API response time: {memory_response_time:.2f}s", 
                   "SUCCESS" if memory_fast else "WARNING")
            self.record_test("Memory API Performance", memory_fast, f"{memory_response_time:.2f}s response time")
            
            # Test pipeline response time
            start_time = time.time()
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.pipelines_url}/")
                pipeline_response_time = time.time() - start_time
            
            pipeline_fast = pipeline_response_time < 2.0
            self.log(f"Pipelines response time: {pipeline_response_time:.2f}s",
                   "SUCCESS" if pipeline_fast else "WARNING")
            self.record_test("Pipelines Performance", pipeline_fast, f"{pipeline_response_time:.2f}s response time")
            
            overall_performance = memory_fast and pipeline_fast
            return overall_performance
            
        except Exception as e:
            self.log(f"Performance test failed: {e}", "ERROR")
            self.record_test("System Performance", False, f"Exception: {e}")
            return False
    
    # =====================================
    # MAIN TEST RUNNER
    # =====================================
    
    async def run_comprehensive_tests(self) -> Dict[str, Any]:
        """Run all comprehensive tests and return results"""
        self.log("Starting Comprehensive Smart Anti-Hallucination System Test", "SECTION")
        self.log("=" * 80, "INFO")
        
        # Run all test suites
        test_results = []
        
        # 1. Smart Trigger Logic Tests
        trigger_result = self.test_smart_trigger_logic()
        test_results.append(("Smart Trigger Logic", trigger_result))
        
        # 2. Service Health Tests
        health_result = await self.test_service_health()
        test_results.append(("Service Health", health_result))
        
        # 3. Memory System Tests  
        memory_result = await self.test_memory_system()
        test_results.append(("Memory System", memory_result))
        
        # 4. Anti-Fabrication Tests
        anti_fab_result = self.test_anti_fabrication()
        test_results.append(("Anti-Fabrication", anti_fab_result))
        
        # 5. Web Search Tests
        web_search_result = await self.test_web_search_functionality()
        test_results.append(("Web Search", web_search_result))
        
        # 6. End-to-End Pipeline Tests
        e2e_result = await self.test_end_to_end_pipeline()
        test_results.append(("End-to-End Pipeline", e2e_result))
        
        # 7. Performance Tests
        performance_result = await self.test_system_performance()
        test_results.append(("System Performance", performance_result))
        
        # Calculate overall results
        passed_suites = sum(1 for _, result in test_results if result)
        total_suites = len(test_results)
        
        self.log("=" * 80, "INFO")
        self.log("COMPREHENSIVE TEST RESULTS", "SECTION")
        self.log("=" * 80, "INFO")
        
        for suite_name, result in test_results:
            status = "✅ PASSED" if result else "❌ FAILED"
            self.log(f"{suite_name}: {status}", "RESULT")
        
        self.log("-" * 80, "INFO")
        self.log(f"Overall Test Suites: {passed_suites}/{total_suites} PASSED", "RESULT")
        self.log(f"Individual Tests: {self.results['passed_tests']}/{self.results['total_tests']} PASSED", "RESULT")
        self.log(f"Total Test Time: {time.time() - self.start_time:.1f} seconds", "RESULT")
        
        # Final verdict
        overall_success = passed_suites == total_suites
        if overall_success:
            self.log("🎉 ALL TESTS PASSED - Smart Anti-Hallucination System is WORKING PERFECTLY!", "SUCCESS")
        else:
            self.log("🚨 SOME TESTS FAILED - System needs attention", "ERROR")
        
        return {
            "overall_success": overall_success,
            "passed_suites": passed_suites,
            "total_suites": total_suites,
            "test_results": test_results,
            "detailed_results": self.results,
            "execution_time": time.time() - self.start_time
        }

# =====================================
# MAIN EXECUTION
# =====================================

async def main():
    """Main test execution function"""
    print("🚀 COMPREHENSIVE SMART ANTI-HALLUCINATION SYSTEM TEST SUITE")
    print("=" * 80)
    print("Testing all components of the Smart Anti-Hallucination System:")
    print("• Smart Web Search Trigger Logic")
    print("• Service Health & Connectivity") 
    print("• Memory System Integration")
    print("• Anti-Fabrication Measures")
    print("• Web Search Functionality")
    print("• End-to-End Pipeline Flow")
    print("• System Performance")
    print("=" * 80)
    
    tester = ComprehensiveSystemTester()
    results = await tester.run_comprehensive_tests()
    
    # Save detailed results to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"comprehensive_test_results_{timestamp}.json"
    
    try:
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"\n📄 Detailed results saved to: {results_file}")
    except Exception as e:
        print(f"\n⚠️ Could not save results file: {e}")
    
    # Exit with appropriate code
    exit_code = 0 if results["overall_success"] else 1
    return exit_code

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n🛑 Test interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n\n💥 Test suite crashed: {e}")
        sys.exit(1)
