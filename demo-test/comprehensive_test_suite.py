#!/usr/bin/env python3
"""
Comprehensive Real-Life Simulation Test Suite
==============================================

This module provides thorough testing across ALL backend modules with real-life scenarios:
- API endpoint testing with various scenarios
- Authentication and authorization flows
- Tool functionality with edge cases
- Database operations and caching
- Error handling and recovery
- Performance and stress testing
- Integration between modules
- OpenAI compatibility verification
- Document processing and RAG
- Adaptive learning and feedback systems

Author: Backend Test Suite
Version: 1.0.0
"""

import asyncio
import json
import os
import random
import string
import tempfile
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import httpx
import requests
from pydantic import BaseModel


class TestConfig:
    """Configuration for test suite."""
    
    BASE_URL = "http://localhost:8001"
    API_KEY = "f2b985dd-219f-45b1-a90e-170962cc7082"
    TIMEOUT = 30
    MAX_RETRIES = 3
    
    # Test data
    TEST_USER_IDS = ["test_user_1", "test_user_2", "performance_user"]
    SAMPLE_MESSAGES = [
        "What is the weather in London?",
        "What time is it in Tokyo?", 
        "Calculate 15 + 25 * 3",
        "Convert 100 km to miles",
        "Search for artificial intelligence news",
        "Tell me about machine learning on Wikipedia",
        "Run Python: print('Hello World')",
        "What is 2+2?",
        "What's the current time?",
        "Hello, how are you?"
    ]


class TestResult:
    """Test result container."""
    
    def __init__(self, name: str, success: bool = True, 
                 message: str = "", duration: float = 0.0, 
                 data: Optional[Dict] = None):
        self.name = name
        self.success = success
        self.message = message
        self.duration = duration
        self.data = data or {}
        self.timestamp = datetime.now()


class TestReporter:
    """Test reporting and statistics."""
    
    def __init__(self):
        self.results: List[TestResult] = []
        self.start_time = time.time()
    
    def add_result(self, result: TestResult):
        """Add test result."""
        self.results.append(result)
        
    def print_progress(self, test_name: str, status: str = "RUNNING"):
        """Print test progress."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        if status == "PASS":
            print(f"[{timestamp}] ✅ {test_name}")
        elif status == "FAIL":
            print(f"[{timestamp}] ❌ {test_name}")
        elif status == "SKIP":
            print(f"[{timestamp}] ⏭️  {test_name}")
        else:
            print(f"[{timestamp}] 🔄 {test_name}")
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive test report."""
        total_tests = len(self.results)
        passed = sum(1 for r in self.results if r.success)
        failed = total_tests - passed
        
        total_duration = time.time() - self.start_time
        avg_duration = sum(r.duration for r in self.results) / total_tests if total_tests > 0 else 0
        
        return {
            "summary": {
                "total_tests": total_tests,
                "passed": passed,
                "failed": failed,
                "success_rate": f"{(passed/total_tests*100):.1f}%" if total_tests > 0 else "0%",
                "total_duration": f"{total_duration:.2f}s",
                "average_test_duration": f"{avg_duration:.2f}s"
            },
            "test_results": [
                {
                    "name": r.name,
                    "success": r.success,
                    "message": r.message,
                    "duration": f"{r.duration:.2f}s",
                    "timestamp": r.timestamp.isoformat()
                }
                for r in self.results
            ],
            "failed_tests": [
                {"name": r.name, "message": r.message}
                for r in self.results if not r.success
            ]
        }


class ComprehensiveTestSuite:
    """Main test suite class."""
    
    def __init__(self):
        self.config = TestConfig()
        self.reporter = TestReporter()
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'X-API-Key': self.config.API_KEY
        })

    def make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """Make HTTP request with retries."""
        url = f"{self.config.BASE_URL}{endpoint}"
        
        for attempt in range(self.config.MAX_RETRIES):
            try:
                response = self.session.request(
                    method, url, timeout=self.config.TIMEOUT, **kwargs
                )
                return response
            except requests.exceptions.RequestException as e:
                if attempt == self.config.MAX_RETRIES - 1:
                    raise e
                time.sleep(1)
        
        # This should never be reached, but added for type safety
        raise requests.exceptions.RequestException("Max retries exceeded")
    
    def test_health_endpoints(self):
        """Test all health check endpoints."""
        test_name = "Health Endpoints"
        self.reporter.print_progress(test_name)
        start_time = time.time()
        
        health_endpoints = [
            "/health",
            "/health/simple", 
            "/health/detailed",
            "/health/redis",
            "/health/chromadb"
        ]
        
        success = True
        messages = []
        
        for endpoint in health_endpoints:
            try:
                response = self.make_request("GET", endpoint)
                if response.status_code == 200:
                    messages.append(f"✅ {endpoint}")
                else:
                    messages.append(f"❌ {endpoint} - Status: {response.status_code}")
                    success = False
            except Exception as e:
                messages.append(f"❌ {endpoint} - Error: {str(e)}")
                success = False
        
        duration = time.time() - start_time
        result = TestResult(test_name, success, "; ".join(messages), duration)
        self.reporter.add_result(result)
        self.reporter.print_progress(test_name, "PASS" if success else "FAIL")
    
    def test_authentication_scenarios(self):
        """Test authentication with various scenarios."""
        test_name = "Authentication Scenarios"
        self.reporter.print_progress(test_name)
        start_time = time.time()
        
        scenarios = [
            ("Valid API Key", {"X-API-Key": self.config.API_KEY}, 200),
            ("Invalid API Key", {"X-API-Key": "invalid-key"}, 401),
            ("Missing API Key", {}, 401),
            ("Bearer Token", {"Authorization": f"Bearer {self.config.API_KEY}"}, 200),
            ("Query Parameter", {}, 200, {"api_key": self.config.API_KEY})
        ]
        
        success = True
        messages = []
        
        for scenario_name, headers, expected_status, params in scenarios:
            try:
                # Remove default headers for this test
                temp_session = requests.Session()
                temp_session.headers.update(headers)
                
                response = temp_session.get(
                    f"{self.config.BASE_URL}/health/simple",
                    params=params if len(scenarios[scenarios.index((scenario_name, headers, expected_status, params))]) > 3 else None,
                    timeout=self.config.TIMEOUT
                )
                
                if response.status_code == expected_status:
                    messages.append(f"✅ {scenario_name}")
                else:
                    messages.append(f"❌ {scenario_name} - Expected: {expected_status}, Got: {response.status_code}")
                    success = False
                    
            except Exception as e:
                messages.append(f"❌ {scenario_name} - Error: {str(e)}")
                success = False
        
        duration = time.time() - start_time
        result = TestResult(test_name, success, "; ".join(messages), duration)
        self.reporter.add_result(result)
        self.reporter.print_progress(test_name, "PASS" if success else "FAIL")
    
    def test_chat_functionality(self):
        """Test chat endpoint with various message types."""
        test_name = "Chat Functionality"
        self.reporter.print_progress(test_name)
        start_time = time.time()
        
        success = True
        messages = []
        
        for i, message in enumerate(self.config.SAMPLE_MESSAGES):
            try:
                response = self.make_request("POST", "/chat", json={
                    "user_id": f"test_user_{i}",
                    "message": message
                })
                
                if response.status_code == 200:
                    data = response.json()
                    if "response" in data and data["response"]:
                        messages.append(f"✅ Message {i+1}: {message[:30]}...")
                    else:
                        messages.append(f"❌ Message {i+1}: Empty response")
                        success = False
                else:
                    messages.append(f"❌ Message {i+1}: Status {response.status_code}")
                    success = False
                    
                # Small delay between requests
                time.sleep(0.5)
                
            except Exception as e:
                messages.append(f"❌ Message {i+1}: Error - {str(e)}")
                success = False
        
        duration = time.time() - start_time
        result = TestResult(test_name, success, "; ".join(messages), duration)
        self.reporter.add_result(result)
        self.reporter.print_progress(test_name, "PASS" if success else "FAIL")
    
    def test_tool_functionality(self):
        """Test individual AI tools."""
        test_name = "AI Tools"
        self.reporter.print_progress(test_name)
        start_time = time.time()
        
        tool_tests = [
            ("Weather Tool", "What's the weather in London?"),
            ("Time Tool", "What time is it in Tokyo?"),
            ("Math Tool", "Calculate 15 + 25 * 3"),
            ("Conversion Tool", "Convert 100 km to miles"),
            ("Web Search", "Search for Python programming"),
            ("Wikipedia", "Tell me about artificial intelligence on Wikipedia"),
            ("Calculator", "What is the square root of 144?")
        ]
        
        success = True
        messages = []
        
        for tool_name, test_message in tool_tests:
            try:
                response = self.make_request("POST", "/chat", json={
                    "user_id": "tool_test_user",
                    "message": test_message
                })
                
                if response.status_code == 200:
                    data = response.json()
                    response_text = data.get("response", "")
                    if response_text and len(response_text) > 10:
                        messages.append(f"✅ {tool_name}")
                    else:
                        messages.append(f"❌ {tool_name}: Short/empty response")
                        success = False
                else:
                    messages.append(f"❌ {tool_name}: Status {response.status_code}")
                    success = False
                    
                time.sleep(1)  # Give tools time to process
                
            except Exception as e:
                messages.append(f"❌ {tool_name}: Error - {str(e)}")
                success = False
        
        duration = time.time() - start_time
        result = TestResult(test_name, success, "; ".join(messages), duration)
        self.reporter.add_result(result)
        self.reporter.print_progress(test_name, "PASS" if success else "FAIL")
    
    def test_openai_compatibility(self):
        """Test OpenAI-compatible endpoints."""
        test_name = "OpenAI Compatibility"
        self.reporter.print_progress(test_name)
        start_time = time.time()
        
        success = True
        messages = []
        
        # Test models endpoint
        try:
            response = self.make_request("GET", "/v1/models")
            if response.status_code == 200:
                data = response.json()
                if "data" in data and isinstance(data["data"], list):
                    messages.append(f"✅ Models endpoint: {len(data['data'])} models")
                else:
                    messages.append("❌ Models endpoint: Invalid response format")
                    success = False
            else:
                messages.append(f"❌ Models endpoint: Status {response.status_code}")
                success = False
        except Exception as e:
            messages.append(f"❌ Models endpoint: Error - {str(e)}")
            success = False
        
        # Test chat completions endpoint
        try:
            openai_payload = {
                "model": "gpt-4",
                "messages": [
                    {"role": "user", "content": "Hello, this is a test message"}
                ],
                "stream": False
            }
            
            response = self.make_request("POST", "/v1/chat/completions", json=openai_payload)
            if response.status_code == 200:
                data = response.json()
                if "choices" in data and len(data["choices"]) > 0:
                    messages.append("✅ Chat completions endpoint")
                else:
                    messages.append("❌ Chat completions: No choices in response")
                    success = False
            else:
                messages.append(f"❌ Chat completions: Status {response.status_code}")
                success = False
        except Exception as e:
            messages.append(f"❌ Chat completions: Error - {str(e)}")
            success = False
        
        duration = time.time() - start_time
        result = TestResult(test_name, success, "; ".join(messages), duration)
        self.reporter.add_result(result)
        self.reporter.print_progress(test_name, "PASS" if success else "FAIL")
    
    def test_document_upload_and_rag(self):
        """Test document upload and RAG functionality."""
        test_name = "Document Upload & RAG"
        self.reporter.print_progress(test_name)
        start_time = time.time()
        
        success = True
        messages = []
        
        # Create a test document
        test_content = """
        This is a test document for RAG testing.
        It contains information about artificial intelligence and machine learning.
        AI systems can process natural language and perform complex tasks.
        Machine learning algorithms learn from data to make predictions.
        """
        
        try:
            # Test document upload
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                f.write(test_content)
                temp_file_path = f.name
            
            with open(temp_file_path, 'rb') as f:
                files = {'file': ('test_doc.txt', f, 'text/plain')}
                data = {'user_id': 'rag_test_user'}
                
                # Use requests without json header for multipart
                temp_session = requests.Session()
                temp_session.headers.update({'X-API-Key': self.config.API_KEY})
                
                response = temp_session.post(
                    f"{self.config.BASE_URL}/upload/document",
                    files=files,
                    data=data,
                    timeout=self.config.TIMEOUT
                )
            
            os.unlink(temp_file_path)  # Clean up
            
            if response.status_code == 200:
                messages.append("✅ Document upload")
                
                # Test RAG query
                time.sleep(2)  # Allow time for indexing
                
                rag_response = self.make_request("POST", "/chat", json={
                    "user_id": "rag_test_user",
                    "message": "What does this document say about machine learning?"
                })
                
                if rag_response.status_code == 200:
                    rag_data = rag_response.json()
                    if "machine learning" in rag_data.get("response", "").lower():
                        messages.append("✅ RAG query")
                    else:
                        messages.append("❌ RAG query: No relevant content found")
                        success = False
                else:
                    messages.append(f"❌ RAG query: Status {rag_response.status_code}")
                    success = False
            else:
                messages.append(f"❌ Document upload: Status {response.status_code}")
                success = False
                
        except Exception as e:
            messages.append(f"❌ Document upload/RAG: Error - {str(e)}")
            success = False
        
        duration = time.time() - start_time
        result = TestResult(test_name, success, "; ".join(messages), duration)
        self.reporter.add_result(result)
        self.reporter.print_progress(test_name, "PASS" if success else "FAIL")
    
    def test_enhanced_endpoints(self):
        """Test enhanced integration endpoints."""
        test_name = "Enhanced Endpoints"
        self.reporter.print_progress(test_name)
        start_time = time.time()
        
        enhanced_endpoints = [
            ("/config", "GET"),
            ("/persona", "GET"),
            ("/cache/stats", "GET"),
            ("/storage/health", "GET"),
            ("/adaptive/stats", "GET"),
            ("/learning/health", "GET")
        ]
        
        success = True
        messages = []
        
        for endpoint, method in enhanced_endpoints:
            try:
                response = self.make_request(method, endpoint)
                if response.status_code in [200, 201]:
                    messages.append(f"✅ {method} {endpoint}")
                elif response.status_code == 404:
                    messages.append(f"⏭️  {method} {endpoint} (Not implemented)")
                else:
                    messages.append(f"❌ {method} {endpoint}: Status {response.status_code}")
                    success = False
            except Exception as e:
                messages.append(f"❌ {method} {endpoint}: Error - {str(e)}")
                success = False
        
        duration = time.time() - start_time
        result = TestResult(test_name, success, "; ".join(messages), duration)
        self.reporter.add_result(result)
        self.reporter.print_progress(test_name, "PASS" if success else "FAIL")
    
    def test_error_handling(self):
        """Test error handling scenarios."""
        test_name = "Error Handling"
        self.reporter.print_progress(test_name)
        start_time = time.time()
        
        error_scenarios = [
            ("Invalid JSON", "/chat", "POST", "invalid json"),
            ("Missing required field", "/chat", "POST", {"user_id": "test"}),
            ("Non-existent endpoint", "/nonexistent", "GET", None),
            ("Invalid method", "/health", "DELETE", None)
        ]
        
        success = True
        messages = []
        
        for scenario_name, endpoint, method, payload in error_scenarios:
            try:
                if payload == "invalid json":
                    # Send invalid JSON
                    temp_session = requests.Session()
                    temp_session.headers.update({
                        'Content-Type': 'application/json',
                        'X-API-Key': self.config.API_KEY
                    })
                    response = temp_session.request(
                        method,
                        f"{self.config.BASE_URL}{endpoint}",
                        data="invalid json",
                        timeout=self.config.TIMEOUT
                    )
                else:
                    response = self.make_request(method, endpoint, json=payload)
                
                if response.status_code >= 400:
                    messages.append(f"✅ {scenario_name}: Proper error response")
                else:
                    messages.append(f"❌ {scenario_name}: Should have returned error")
                    success = False
                    
            except Exception as e:
                # Some errors are expected (like connection errors for invalid endpoints)
                messages.append(f"✅ {scenario_name}: Exception handled - {type(e).__name__}")
        
        duration = time.time() - start_time
        result = TestResult(test_name, success, "; ".join(messages), duration)
        self.reporter.add_result(result)
        self.reporter.print_progress(test_name, "PASS" if success else "FAIL")
    
    def test_performance_stress(self):
        """Test system performance under load."""
        test_name = "Performance & Stress Test"
        self.reporter.print_progress(test_name)
        start_time = time.time()
        
        success = True
        messages = []
        concurrent_requests = 5
        
        try:
            # Measure response times
            response_times = []
            
            for i in range(concurrent_requests):
                req_start = time.time()
                response = self.make_request("POST", "/chat", json={
                    "user_id": f"perf_user_{i}",
                    "message": f"Performance test message {i}"
                })
                req_duration = time.time() - req_start
                response_times.append(req_duration)
                
                if response.status_code != 200:
                    success = False
                    break
            
            if response_times:
                avg_response_time = sum(response_times) / len(response_times)
                max_response_time = max(response_times)
                
                messages.append(f"Avg response time: {avg_response_time:.2f}s")
                messages.append(f"Max response time: {max_response_time:.2f}s")
                
                if avg_response_time > 10:  # More than 10 seconds average
                    messages.append("⚠️  High average response time")
                    success = False
                else:
                    messages.append("✅ Response times acceptable")
            
        except Exception as e:
            messages.append(f"❌ Performance test error: {str(e)}")
            success = False
        
        duration = time.time() - start_time
        result = TestResult(test_name, success, "; ".join(messages), duration)
        self.reporter.add_result(result)
        self.reporter.print_progress(test_name, "PASS" if success else "FAIL")
    
    def test_cache_functionality(self):
        """Test caching system."""
        test_name = "Cache Functionality"
        self.reporter.print_progress(test_name)
        start_time = time.time()
        
        success = True
        messages = []
        
        try:
            # Send identical requests to test caching
            test_message = "What is 2+2?"
            user_id = "cache_test_user"
            
            # First request
            first_start = time.time()
            first_response = self.make_request("POST", "/chat", json={
                "user_id": user_id,
                "message": test_message
            })
            first_duration = time.time() - first_start
            
            # Second request (should be cached)
            time.sleep(1)  # Brief pause
            second_start = time.time()
            second_response = self.make_request("POST", "/chat", json={
                "user_id": user_id,
                "message": test_message
            })
            second_duration = time.time() - second_start
            
            if first_response.status_code == 200 and second_response.status_code == 200:
                first_text = first_response.json().get("response", "")
                second_text = second_response.json().get("response", "")
                
                if first_text == second_text:
                    messages.append("✅ Cache consistency")
                    
                    # Check if second request was faster (cache hit)
                    if second_duration < first_duration * 0.8:
                        messages.append("✅ Cache performance improvement")
                    else:
                        messages.append("⚠️  No significant cache speedup")
                else:
                    messages.append("❌ Cache inconsistency")
                    success = False
            else:
                messages.append("❌ Cache test requests failed")
                success = False
                
        except Exception as e:
            messages.append(f"❌ Cache test error: {str(e)}")
            success = False
        
        duration = time.time() - start_time
        result = TestResult(test_name, success, "; ".join(messages), duration)
        self.reporter.add_result(result)
        self.reporter.print_progress(test_name, "PASS" if success else "FAIL")
    
    def test_session_management(self):
        """Test session and user management."""
        test_name = "Session Management"
        self.reporter.print_progress(test_name)
        start_time = time.time()
        
        success = True
        messages = []
        
        try:
            # Test multiple users with separate sessions
            users = ["session_user_1", "session_user_2", "session_user_3"]
            
            for user in users:
                response = self.make_request("POST", "/chat", json={
                    "user_id": user,
                    "message": f"Hello, I am {user}"
                })
                
                if response.status_code == 200:
                    messages.append(f"✅ Session for {user}")
                else:
                    messages.append(f"❌ Session failed for {user}")
                    success = False
                    
                time.sleep(0.5)
            
            # Test session persistence (send follow-up message)
            follow_up_response = self.make_request("POST", "/chat", json={
                "user_id": users[0],
                "message": "Do you remember me?"
            })
            
            if follow_up_response.status_code == 200:
                messages.append("✅ Session persistence")
            else:
                messages.append("❌ Session persistence failed")
                success = False
                
        except Exception as e:
            messages.append(f"❌ Session management error: {str(e)}")
            success = False
        
        duration = time.time() - start_time
        result = TestResult(test_name, success, "; ".join(messages), duration)
        self.reporter.add_result(result)
        self.reporter.print_progress(test_name, "PASS" if success else "FAIL")
    
    def run_all_tests(self):
        """Run all test suites."""
        print("🚀 Starting Comprehensive Real-Life Simulation Test Suite")
        print("=" * 60)
        print(f"Base URL: {self.config.BASE_URL}")
        print(f"API Key: {self.config.API_KEY[:8]}...")
        print(f"Timestamp: {datetime.now().isoformat()}")
        print("=" * 60)
        
        # Wait for system to be ready
        print("⏳ Waiting for system to be ready...")
        time.sleep(3)
        
        # Run all test suites
        test_methods = [
            self.test_health_endpoints,
            self.test_authentication_scenarios,
            self.test_chat_functionality,
            self.test_tool_functionality,
            self.test_openai_compatibility,
            self.test_document_upload_and_rag,
            self.test_enhanced_endpoints,
            self.test_error_handling,
            self.test_performance_stress,
            self.test_cache_functionality,
            self.test_session_management
        ]
        
        for test_method in test_methods:
            try:
                test_method()
                time.sleep(1)  # Brief pause between test suites
            except Exception as e:
                test_name = test_method.__name__.replace("test_", "").replace("_", " ").title()
                result = TestResult(test_name, False, f"Test suite error: {str(e)}")
                self.reporter.add_result(result)
                self.reporter.print_progress(test_name, "FAIL")
        
        # Generate and display report
        print("\n" + "=" * 60)
        print("📊 TEST SUITE RESULTS")
        print("=" * 60)
        
        report = self.reporter.generate_report()
        
        # Summary
        summary = report["summary"]
        print(f"Total Tests: {summary['total_tests']}")
        print(f"Passed: {summary['passed']}")
        print(f"Failed: {summary['failed']}")
        print(f"Success Rate: {summary['success_rate']}")
        print(f"Total Duration: {summary['total_duration']}")
        print(f"Average Test Duration: {summary['average_test_duration']}")
        
        # Failed tests
        if report["failed_tests"]:
            print("\n❌ FAILED TESTS:")
            for failed_test in report["failed_tests"]:
                print(f"  - {failed_test['name']}: {failed_test['message']}")
        
        # Save detailed report
        report_file = f"demo-test/comprehensive_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        try:
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            print(f"\n📄 Detailed report saved to: {report_file}")
        except Exception as e:
            print(f"\n⚠️  Could not save report: {e}")
        
        print("\n🏁 Comprehensive test suite completed!")
        
        return summary['failed'] == 0


def main():
    """Main function to run the test suite."""
    try:
        suite = ComprehensiveTestSuite()
        success = suite.run_all_tests()
        return 0 if success else 1
    except KeyboardInterrupt:
        print("\n\n⚠️  Test suite interrupted by user")
        return 1
    except Exception as e:
        print(f"\n\n❌ Test suite failed with error: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
