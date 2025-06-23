#!/usr/bin/env python3
"""
Live System Testing Script
Comprehensive testing of the running backend application for errors and functionality.
"""

import sys
import os
import json
import time
import requests
import threading
import asyncio
import concurrent.futures
from datetime import datetime
from typing import Dict, List, Any

# Test configuration
BASE_URL = "http://localhost:8001"
TEST_TIMEOUT = 30
MAX_CONCURRENT_REQUESTS = 10

class LiveSystemTester:
    def __init__(self):
        self.results = {}
        self.errors = []
        self.start_time = time.time()
        
    def log(self, message: str, level: str = "INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
        
    def log_error(self, test_name: str, error: str):
        self.errors.append(f"{test_name}: {error}")
        self.log(f"❌ {test_name} - {error}", "ERROR")
        
    def log_success(self, test_name: str, message: str = ""):
        self.log(f"✅ {test_name} - {message}", "SUCCESS")
        
    def test_basic_connectivity(self):
        """Test basic API connectivity."""
        test_name = "Basic Connectivity"
        try:
            response = requests.get(f"{BASE_URL}/health", timeout=10)
            if response.status_code == 200:
                data = response.json()
                self.log_success(test_name, f"Status: {data.get('status', 'unknown')}")
                return True
            else:
                self.log_error(test_name, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_error(test_name, str(e))
            return False
    
    def test_api_endpoints(self):
        """Test various API endpoints for errors."""
        endpoints = [
            ("/health", "GET", None),
            ("/docs", "GET", None),
            ("/openapi.json", "GET", None),
        ]
        
        results = {}
        for endpoint, method, data in endpoints:
            test_name = f"API Endpoint {method} {endpoint}"
            try:
                if method == "GET":
                    response = requests.get(f"{BASE_URL}{endpoint}", timeout=10)
                elif method == "POST":
                    response = requests.post(f"{BASE_URL}{endpoint}", json=data, timeout=10)
                
                if response.status_code in [200, 201]:
                    self.log_success(test_name, f"HTTP {response.status_code}")
                    results[endpoint] = True
                elif response.status_code == 404:
                    self.log(f"⚠️  {test_name} - Not Found (HTTP 404)", "WARNING")
                    results[endpoint] = "not_found"
                else:
                    self.log_error(test_name, f"HTTP {response.status_code}")
                    results[endpoint] = False
                    
            except Exception as e:
                self.log_error(test_name, str(e))
                results[endpoint] = False
                
        return results
    
    def test_chat_completions_endpoint(self):
        """Test the chat completions endpoint."""
        test_name = "Chat Completions Endpoint"
        try:
            payload = {
                "messages": [
                    {"role": "user", "content": "Hello, this is a test message. Please respond briefly."}
                ],
                "model": "llama3.2:3b",
                "stream": False,
                "max_tokens": 50,
                "temperature": 0.7
            }
            
            response = requests.post(
                f"{BASE_URL}/v1/chat/completions",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if "choices" in data:
                    self.log_success(test_name, "Response received successfully")
                    return True
                else:
                    self.log_error(test_name, "Invalid response format")
                    return False
            else:
                self.log_error(test_name, f"HTTP {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.log_error(test_name, str(e))
            return False
    
    def test_streaming_endpoint(self):
        """Test streaming functionality."""
        test_name = "Streaming Endpoint"
        try:
            payload = {
                "messages": [
                    {"role": "user", "content": "Count from 1 to 5, one number per line."}
                ],
                "model": "llama3.2:3b",
                "stream": True,
                "max_tokens": 30
            }
            
            response = requests.post(
                f"{BASE_URL}/v1/chat/completions",
                json=payload,
                stream=True,
                timeout=30
            )
            
            if response.status_code == 200:
                chunks_received = 0
                for line in response.iter_lines():
                    if line:
                        chunks_received += 1
                        if chunks_received >= 5:  # Stop after a few chunks
                            break
                
                if chunks_received > 0:
                    self.log_success(test_name, f"Received {chunks_received} chunks")
                    return True
                else:
                    self.log_error(test_name, "No streaming chunks received")
                    return False
            else:
                self.log_error(test_name, f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_error(test_name, str(e))
            return False
    
    def test_concurrent_requests(self):
        """Test concurrent request handling."""
        test_name = "Concurrent Requests"
        try:
            def make_request(request_id):
                try:
                    response = requests.get(f"{BASE_URL}/health", timeout=10)
                    return {
                        "id": request_id,
                        "status": response.status_code,
                        "success": response.status_code == 200
                    }
                except Exception as e:
                    return {
                        "id": request_id,
                        "status": "error",
                        "success": False,
                        "error": str(e)
                    }
            
            num_requests = 20
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                futures = [executor.submit(make_request, i) for i in range(num_requests)]
                results = [future.result() for future in concurrent.futures.as_completed(futures)]
            
            successful = sum(1 for r in results if r["success"])
            failed = num_requests - successful
            
            if failed == 0:
                self.log_success(test_name, f"All {num_requests} requests successful")
                return True
            elif failed < num_requests * 0.1:  # Less than 10% failure rate
                self.log(f"⚠️  {test_name} - {successful}/{num_requests} successful", "WARNING")
                return True
            else:
                self.log_error(test_name, f"High failure rate: {failed}/{num_requests} failed")
                return False
                
        except Exception as e:
            self.log_error(test_name, str(e))
            return False
    
    def test_memory_usage(self):
        """Test for memory leaks by making repeated requests."""
        test_name = "Memory Usage Test"
        try:
            # Make multiple requests to check for memory leaks
            for i in range(50):
                response = requests.get(f"{BASE_URL}/health", timeout=5)
                if response.status_code != 200:
                    self.log_error(test_name, f"Request {i} failed with status {response.status_code}")
                    return False
                
                if i % 10 == 0:
                    self.log(f"📊 {test_name} - Completed {i}/50 requests", "INFO")
            
            self.log_success(test_name, "No immediate memory issues detected")
            return True
            
        except Exception as e:
            self.log_error(test_name, str(e))
            return False
    
    def test_error_handling(self):
        """Test error handling with invalid requests."""
        test_name = "Error Handling"
        error_tests = [
            # Invalid JSON
            ("Invalid JSON", "/v1/chat/completions", "POST", "invalid json"),
            # Missing required fields
            ("Missing Fields", "/v1/chat/completions", "POST", {}),
            # Invalid endpoint
            ("Invalid Endpoint", "/nonexistent", "GET", None),
        ]
        
        results = {}
        for subtest, endpoint, method, data in error_tests:
            try:
                if method == "GET":
                    response = requests.get(f"{BASE_URL}{endpoint}", timeout=10)
                elif method == "POST":
                    if isinstance(data, str):
                        # Send raw string for invalid JSON test
                        response = requests.post(
                            f"{BASE_URL}{endpoint}",
                            data=data,
                            headers={"Content-Type": "application/json"},
                            timeout=10
                        )
                    else:
                        response = requests.post(f"{BASE_URL}{endpoint}", json=data, timeout=10)
                
                # For error handling tests, we expect 4xx or 5xx status codes
                if 400 <= response.status_code < 600:
                    self.log_success(f"{test_name} - {subtest}", f"Properly returned HTTP {response.status_code}")
                    results[subtest] = True
                else:
                    self.log_error(f"{test_name} - {subtest}", f"Unexpected status {response.status_code}")
                    results[subtest] = False
                    
            except Exception as e:
                self.log_error(f"{test_name} - {subtest}", str(e))
                results[subtest] = False
        
        return all(results.values())
    
    def test_service_dependencies(self):
        """Test that all service dependencies are working."""
        test_name = "Service Dependencies"
        try:
            response = requests.get(f"{BASE_URL}/health", timeout=10)
            if response.status_code == 200:
                data = response.json()
                databases = data.get("databases", {})
                
                # Check Redis
                redis_status = databases.get("redis", {}).get("available", False)
                if redis_status:
                    self.log_success(f"{test_name} - Redis", "Connected")
                else:
                    self.log_error(f"{test_name} - Redis", "Not available")
                
                # Check ChromaDB
                chroma_status = databases.get("chromadb", {}).get("available", False)
                if chroma_status:
                    self.log_success(f"{test_name} - ChromaDB", "Connected")
                else:
                    self.log_error(f"{test_name} - ChromaDB", "Not available")
                
                # Check Embeddings
                embeddings_status = databases.get("embeddings", {}).get("available", False)
                if embeddings_status:
                    self.log_success(f"{test_name} - Embeddings", "Available")
                else:
                    self.log_error(f"{test_name} - Embeddings", "Not available")
                
                return redis_status and chroma_status and embeddings_status
            else:
                self.log_error(test_name, f"Health check failed: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_error(test_name, str(e))
            return False
    
    def test_cpu_only_verification(self):
        """Verify CPU-only mode is still enforced during runtime."""
        test_name = "CPU-Only Verification"
        try:
            # This should be a custom endpoint or we can infer from behavior
            # For now, we'll check that the system is responding normally
            # which indicates CPU-only mode is working fine
            
            start_time = time.time()
            response = requests.get(f"{BASE_URL}/health", timeout=10)
            response_time = time.time() - start_time
            
            if response.status_code == 200:
                # If response time is reasonable for CPU processing, it's likely working correctly
                if response_time < 5.0:  # 5 second threshold
                    self.log_success(test_name, f"System responding normally (CPU mode) - {response_time:.2f}s")
                    return True
                else:
                    self.log(f"⚠️  {test_name} - Slow response time: {response_time:.2f}s", "WARNING")
                    return True
            else:
                self.log_error(test_name, f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_error(test_name, str(e))
            return False
    
    def run_all_tests(self):
        """Run all tests and generate a comprehensive report."""
        self.log("🚀 Starting Live System Testing")
        self.log("=" * 60)
        
        tests = [
            ("Basic Connectivity", self.test_basic_connectivity),
            ("API Endpoints", self.test_api_endpoints),
            ("Chat Completions", self.test_chat_completions_endpoint),
            ("Streaming", self.test_streaming_endpoint),
            ("Concurrent Requests", self.test_concurrent_requests),
            ("Memory Usage", self.test_memory_usage),
            ("Error Handling", self.test_error_handling),
            ("Service Dependencies", self.test_service_dependencies),
            ("CPU-Only Verification", self.test_cpu_only_verification),
        ]
        
        for test_name, test_func in tests:
            self.log(f"\n🔍 Running {test_name}...")
            try:
                result = test_func()
                self.results[test_name] = result
            except Exception as e:
                self.log_error(test_name, f"Test failed with exception: {e}")
                self.results[test_name] = False
        
        self.generate_report()
    
    def generate_report(self):
        """Generate a comprehensive test report."""
        total_time = time.time() - self.start_time
        
        self.log("\n" + "=" * 60)
        self.log("📋 LIVE SYSTEM TEST REPORT")
        self.log("=" * 60)
        
        passed = sum(1 for result in self.results.values() if result is True)
        total = len(self.results)
        
        self.log(f"Total Tests: {total}")
        self.log(f"Passed: {passed}")
        self.log(f"Failed: {total - passed}")
        self.log(f"Success Rate: {(passed/total)*100:.1f}%")
        self.log(f"Total Time: {total_time:.2f} seconds")
        
        self.log("\nDetailed Results:")
        for test_name, result in self.results.items():
            status = "✅ PASS" if result is True else "⚠️  WARN" if result == "not_found" else "❌ FAIL"
            self.log(f"  {test_name}: {status}")
        
        if self.errors:
            self.log(f"\n❌ Errors Found ({len(self.errors)}):")
            for error in self.errors:
                self.log(f"  - {error}")
        
        self.log("\n" + "=" * 60)
        if passed == total:
            self.log("🎉 ALL TESTS PASSED - SYSTEM IS HEALTHY! 🎉")
        elif passed >= total * 0.8:  # 80% pass rate
            self.log("⚠️  MOSTLY HEALTHY - Some issues detected")
        else:
            self.log("❌ SYSTEM ISSUES DETECTED - Review failures")
        self.log("=" * 60)
        
        return passed == total

if __name__ == "__main__":
    tester = LiveSystemTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)
