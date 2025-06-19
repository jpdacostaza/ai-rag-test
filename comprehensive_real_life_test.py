#!/usr/bin/env python3
"""
Comprehensive Real-Life Simulation Test Suite (Streamlined)
============================================================

A comprehensive test suite for the AI Backend project that tests all functionality
in a realistic Docker environment with proper error handling and reporting.
"""

import json
import os
import random
import tempfile
import time
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Any, Dict, Optional, Tuple

import requests


class ComprehensiveTestSuite:
    """Comprehensive real-life simulation test suite."""

    def __init__(self):
        print("🚀 Initializing Comprehensive Test Suite...")

        # Service URLs
        self.base_url = "http://localhost:8001"
        self.chroma_url = "http://localhost:8002"

        # Test configuration
        self.api_key = "f2b985dd-219f-45b1-a90e-170962cc7082"
        self.headers = {"Content-Type": "application/json", "X-API-Key": self.api_key}

        # Test data storage
        self.test_results = {}
        self.performance_metrics = {}
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        self.start_time = None

        print(f"📊 Target URL: {self.base_url}")
        print(f"🔑 API Key: {self.api_key[:10]}...")
        print("✅ Initialization complete")

    def log_test_start(self, test_name: str, description: str = ""):
        """Log the start of a test."""
        self.total_tests += 1
        print(f"\n{'='*60}")
        print(f"🧪 TEST #{self.total_tests}: {test_name}")
        if description:
            print(f"📝 {description}")
        print(f"{'='*60}")
        return time.time()

    def log_test_result(
        self, test_name: str, success: bool, details: str = "", duration: float = 0
    ):
        """Log the result of a test."""
        emoji = "✅" if success else "❌"
        status = "PASSED" if success else "FAILED"

        if success:
            self.passed_tests += 1
        else:
            self.failed_tests += 1

        print(f"{emoji} {status}: {test_name}")
        if details:
            print(f"   📋 {details}")
        if duration > 0:
            print(f"   ⏱️  Duration: {duration:.2f}s")

        self.test_results[test_name] = {
            "success": success,
            "details": details,
            "duration": duration,
            "timestamp": datetime.now().isoformat(),
        }

    def make_request(
        self,
        method: str,
        endpoint: str,
        headers: Optional[Dict] = None,
        data: Any = None,
        files: Optional[Dict] = None,
        timeout: int = 30,
    ) -> Tuple[Optional[requests.Response], Optional[str]]:
        """Make HTTP request with error handling."""
        try:
            url = f"{self.base_url}{endpoint}"
            req_headers = headers or self.headers

            print(f"   🌐 {method} {url}")

            if method.upper() == "GET":
                response = requests.get(url, headers=req_headers, timeout=timeout)
            elif method.upper() == "POST":
                if files:
                    file_headers = {
                        k: v for k, v in req_headers.items() if k != "Content-Type"
                    }
                    response = requests.post(
                        url,
                        headers=file_headers,
                        data=data,
                        files=files,
                        timeout=timeout,
                    )
                else:
                    response = requests.post(
                        url, headers=req_headers, json=data, timeout=timeout
                    )
            elif method.upper() == "PUT":
                response = requests.put(
                    url, headers=req_headers, json=data, timeout=timeout
                )
            elif method.upper() == "DELETE":
                response = requests.delete(url, headers=req_headers, timeout=timeout)
            else:
                return None, f"Unsupported method: {method}"

            print(f"   📊 Response: {response.status_code}")
            return response, None
        except Exception as e:
            print(f"   ❌ Request error: {e}")
            return None, str(e)

    def test_service_availability(self) -> bool:
        """Test that all services are available."""
        start_time = self.log_test_start(
            "Service Availability",
            "Checking if all Docker services are running and accessible",
        )

        services = [
            (f"{self.base_url}/health/simple", "Backend API"),
            (f"{self.chroma_url}", "ChromaDB"),
        ]

        all_ready = True
        for url, name in services:
            print(f"⏳ Checking {name}...")
            try:
                response = requests.get(url, timeout=10)
                if response.status_code in [200, 404]:  # 404 is ok for base URLs
                    print(f"   ✅ {name} is available (status: {response.status_code})")
                else:
                    print(f"   ❌ {name} returned status: {response.status_code}")
                    all_ready = False
            except Exception as e:
                print(f"   ❌ {name} is not accessible: {e}")
                all_ready = False

        duration = time.time() - start_time
        self.log_test_result(
            "Service Availability",
            all_ready,
            f"Services {'all ready' if all_ready else 'some unavailable'}",
            duration,
        )
        return all_ready

    def test_health_endpoints(self) -> bool:
        """Test all health monitoring endpoints."""
        start_time = self.log_test_start(
            "Health Monitoring", "Testing health check endpoints"
        )

        endpoints = [
            "/health",
            "/health/simple",
            "/health/detailed",
            "/health/redis",
            "/health/chromadb",
            "/health/storage",
        ]

        results = {}
        for endpoint in endpoints:
            response, error = self.make_request("GET", endpoint)
            if response and response.status_code == 200:
                results[endpoint] = True
                try:
                    data = response.json()
                    status = data.get("status", "unknown")
                    print(f"   ✅ {endpoint} - Status: {status}")
                except:
                    print(f"   ✅ {endpoint} - OK")
            else:
                results[endpoint] = False
                error_msg = (
                    error
                    or f"HTTP {response.status_code if response else 'No response'}"
                )
                print(f"   ❌ {endpoint} - Error: {error_msg}")

        success = all(results.values())
        passed_count = sum(results.values())
        total_count = len(results)

        duration = time.time() - start_time
        self.log_test_result(
            "Health Monitoring",
            success,
            f"Passed: {passed_count}/{total_count}",
            duration,
        )
        return success

    def test_authentication(self) -> bool:
        """Test authentication middleware."""
        start_time = self.log_test_start(
            "Authentication", "Testing API key authentication and access control"
        )

        tests = {}

        # Test 1: Valid API key
        print("   🔑 Testing with valid API key...")
        response, error = self.make_request("GET", "/models")
        tests["Valid API Key"] = response is not None and response.status_code == 200

        # Test 2: Invalid API key
        print("   🚫 Testing with invalid API key...")
        invalid_headers = {
            "X-API-Key": "invalid-key-12345",
            "Content-Type": "application/json",
        }
        response, error = self.make_request("GET", "/models", headers=invalid_headers)
        tests["Invalid API Key Rejection"] = (
            response is not None and response.status_code in [401, 403]
        )

        # Test 3: No API key
        print("   🔓 Testing without API key...")
        no_auth_headers = {"Content-Type": "application/json"}
        response, error = self.make_request("GET", "/models", headers=no_auth_headers)
        tests["No API Key Rejection"] = (
            response is not None and response.status_code in [401, 403]
        )

        # Test 4: Public endpoint access
        print("   🌐 Testing public endpoint access...")
        response, error = self.make_request(
            "GET", "/health/simple", headers=no_auth_headers
        )
        tests["Public Endpoint Access"] = (
            response is not None and response.status_code == 200
        )

        success = all(tests.values())
        details = (
            f"Valid auth: {'✅' if tests.get('Valid API Key') else '❌'}, "
            + f"Rejects invalid: {'✅' if tests.get('Invalid API Key Rejection') else '❌'}"
        )

        duration = time.time() - start_time
        self.log_test_result("Authentication", success, details, duration)
        return success

    def test_model_management(self) -> bool:
        """Test model listing and management."""
        start_time = self.log_test_start(
            "Model Management", "Testing model endpoints and availability"
        )

        tests = {}

        # Test model listing
        print("   📋 Testing model listing...")
        response, error = self.make_request("GET", "/models")
        if response and response.status_code == 200:
            try:
                data = response.json()
                model_count = len(data.get("data", []))
                tests["List Models"] = model_count > 0
                print(f"   📊 Found {model_count} models")

                # Store first model for later tests
                if model_count > 0:
                    self.first_model = data["data"][0].get("id", "")
                    print(f"   🎯 Primary model: {self.first_model}")
            except Exception as e:
                tests["List Models"] = False
                print(f"   ❌ Error parsing models: {e}")
        else:
            tests["List Models"] = False

        # Test OpenAI compatible endpoint
        print("   🔗 Testing OpenAI compatibility...")
        response, error = self.make_request("GET", "/v1/models")
        tests["OpenAI Compatible"] = (
            response is not None and response.status_code == 200
        )

        # Test model refresh
        print("   🔄 Testing model refresh...")
        response, error = self.make_request("POST", "/models/refresh")
        tests["Model Refresh"] = response is not None and response.status_code == 200

        success = all(tests.values())
        model_count = len(getattr(self, "first_model", "") or "")
        details = (
            f"Models available: {'✅' if tests.get('List Models') else '❌'}, "
            + f"OpenAI compat: {'✅' if tests.get('OpenAI Compatible') else '❌'}"
        )

        duration = time.time() - start_time
        self.log_test_result("Model Management", success, details, duration)
        return success

    def test_chat_functionality(self) -> bool:
        """Test chat endpoints."""
        start_time = self.log_test_start(
            "Chat Functionality", "Testing conversation and chat endpoints"
        )

        tests = {}

        # Test basic chat
        print("   💬 Testing basic chat...")
        chat_data = {
            "user_id": "test_user_comprehensive",
            "message": "Hello! What is 2 + 2? Please give a short answer.",
        }
        response, error = self.make_request("POST", "/chat", data=chat_data, timeout=45)
        if response and response.status_code == 200:
            try:
                data = response.json()
                response_text = data.get("response", "")
                tests["Basic Chat"] = len(response_text) > 0
                print(f"   📝 Response length: {len(response_text)} characters")
                if len(response_text) > 0:
                    preview = response_text[:100].replace("\n", " ")
                    print(f"   👁️  Preview: {preview}...")
                else:
                    print("   ⚠️  Empty response received")
            except Exception as e:
                tests["Basic Chat"] = False
                print(f"   ❌ Error parsing chat response: {e}")
        else:
            tests["Basic Chat"] = False
            print(f"   ❌ Chat request failed: {error}")

        # Test OpenAI compatible chat
        print("   🤖 Testing OpenAI compatible chat...")
        openai_data = {
            "model": getattr(self, "first_model", "llama3.2:3b"),
            "messages": [
                {
                    "role": "user",
                    "content": "What is the capital of France? Answer in one word.",
                }
            ],
            "temperature": 0.7,
            "max_tokens": 50,
        }
        response, error = self.make_request(
            "POST", "/v1/chat/completions", data=openai_data, timeout=45
        )
        tests["OpenAI Chat"] = response is not None and response.status_code == 200

        success = all(tests.values())
        details = (
            f"Basic chat: {'✅' if tests.get('Basic Chat') else '❌'}, "
            + f"OpenAI chat: {'✅' if tests.get('OpenAI Chat') else '❌'}"
        )

        duration = time.time() - start_time
        self.log_test_result("Chat Functionality", success, details, duration)
        return success

    def test_document_processing(self) -> bool:
        """Test document upload and processing."""
        start_time = self.log_test_start(
            "Document Processing", "Testing file upload and RAG functionality"
        )

        tests = {}

        # Test supported formats
        print("   📄 Testing supported formats...")
        response, error = self.make_request("GET", "/upload/formats")
        tests["Supported Formats"] = (
            response is not None and response.status_code == 200
        )

        # Test document upload
        print("   📤 Testing document upload...")
        test_content = "This is a test document about artificial intelligence and machine learning technologies."

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write(test_content)
            temp_path = f.name

        try:
            with open(temp_path, "rb") as file:
                files = {"file": ("test_doc.txt", file, "text/plain")}
                data = {"user_id": "test_user", "description": "Test document upload"}

                response, error = self.make_request(
                    "POST", "/upload/document", files=files, data=data, timeout=30
                )
                tests["Document Upload"] = (
                    response is not None and response.status_code == 200
                )
        finally:
            os.unlink(temp_path)  # Test document search
        print("   🔍 Testing document search...")
        search_data = {
            "query": "artificial intelligence",
            "user_id": "test_user",
            "limit": 3,
        }
        # Send as form data by using files={} to trigger form data mode
        response, error = self.make_request(
            "POST",
            "/upload/search",
            headers={"X-API-Key": self.api_key},
            data=search_data,
            files={},
        )
        tests["Document Search"] = response is not None and response.status_code == 200

        success = all(tests.values())
        details = (
            f"Upload: {'✅' if tests.get('Document Upload') else '❌'}, "
            + f"Search: {'✅' if tests.get('Document Search') else '❌'}"
        )

        duration = time.time() - start_time
        self.log_test_result("Document Processing", success, details, duration)
        return success

    def test_cache_and_storage(self) -> bool:
        """Test cache and storage systems."""
        start_time = self.log_test_start(
            "Cache & Storage", "Testing cache management and storage operations"
        )

        tests = {}

        # Test cache stats
        print("   📊 Testing cache statistics...")
        response, error = self.make_request("GET", "/cache/stats")
        tests["Cache Stats"] = response is not None and response.status_code == 200

        # Test cache operations
        print("   💾 Testing cache set/get operations...")
        timestamp = int(time.time())
        cache_data = {
            "key": f"test_key_{timestamp}",
            "value": f"test_value_{timestamp}",
            "ttl": 300,
        }

        # Set cache
        response, error = self.make_request("POST", "/cache/set", data=cache_data)
        tests["Cache Set"] = response is not None and response.status_code == 200

        # Get cache
        if tests["Cache Set"]:
            response, error = self.make_request(
                "GET", f"/cache/get/{cache_data['key']}"
            )
            if response and response.status_code == 200:
                try:
                    retrieved = response.json()
                    tests["Cache Get"] = retrieved.get("value") == cache_data["value"]
                    print("   ✅ Cache retrieval successful")
                except:
                    tests["Cache Get"] = False
            else:
                tests["Cache Get"] = False

        # Test storage health
        print("   🏥 Testing storage health...")
        response, error = self.make_request("GET", "/storage/health")
        tests["Storage Health"] = response is not None and response.status_code == 200

        success = all(tests.values())
        details = (
            f"Cache ops: {'✅' if tests.get('Cache Set') and tests.get('Cache Get') else '❌'}, "
            + f"Storage: {'✅' if tests.get('Storage Health') else '❌'}"
        )

        duration = time.time() - start_time
        self.log_test_result("Cache & Storage", success, details, duration)
        return success

    def test_error_handling(self) -> bool:
        """Test error handling and edge cases."""
        start_time = self.log_test_start(
            "Error Handling", "Testing system response to invalid requests"
        )

        tests = {}

        # Test invalid endpoint
        print("   🚫 Testing invalid endpoint...")
        response, error = self.make_request("GET", "/nonexistent/endpoint")
        tests["404 Handling"] = response is not None and response.status_code == 404

        # Test malformed request
        print("   ⚠️  Testing malformed request...")
        response, error = self.make_request("POST", "/chat", data={})
        tests["Malformed Request"] = response is not None and response.status_code in [
            400,
            422,
        ]

        # Test unauthorized access
        print("   🔒 Testing unauthorized access...")
        invalid_headers = {
            "X-API-Key": "definitely-invalid",
            "Content-Type": "application/json",
        }
        response, error = self.make_request("GET", "/models", headers=invalid_headers)
        tests["Auth Rejection"] = response is not None and response.status_code in [
            401,
            403,
        ]

        success = all(tests.values())
        details = (
            f"404: {'✅' if tests.get('404 Handling') else '❌'}, "
            + f"Auth: {'✅' if tests.get('Auth Rejection') else '❌'}"
        )

        duration = time.time() - start_time
        self.log_test_result("Error Handling", success, details, duration)
        return success

    def test_concurrent_load(self) -> bool:
        """Test system under concurrent load."""
        start_time = self.log_test_start(
            "Concurrent Load", "Testing system performance under concurrent requests"
        )

        def make_concurrent_request(request_id: int) -> Dict:
            chat_data = {
                "user_id": f"load_test_{request_id}",
                "message": f"Quick test #{request_id}: What is {random.randint(1, 10)} + {random.randint(1, 10)}?",
            }

            req_start = time.time()
            response, error = self.make_request(
                "POST", "/chat", data=chat_data, timeout=20
            )
            req_duration = time.time() - req_start

            return {
                "id": request_id,
                "success": response is not None and response.status_code == 200,
                "duration": req_duration,
                "error": error,
            }

        # Test with 5 concurrent requests
        concurrent_count = 5
        print(f"   🚀 Running {concurrent_count} concurrent requests...")

        results = []
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [
                executor.submit(make_concurrent_request, i)
                for i in range(concurrent_count)
            ]

            for future in as_completed(futures):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    results.append({"success": False, "error": str(e)})

        # Analyze results
        successful = sum(1 for r in results if r.get("success", False))
        total = len(results)
        success_rate = successful / total if total > 0 else 0
        avg_time = (
            sum(r.get("duration", 0) for r in results if r.get("success", False))
            / successful
            if successful > 0
            else 0
        )

        success = success_rate >= 0.6  # 60% success rate threshold for concurrent tests
        details = f"Success rate: {success_rate:.1%} ({successful}/{total}), Avg time: {avg_time:.2f}s"

        print(f"   📊 Concurrent test results: {details}")

        # Store performance metrics
        self.performance_metrics["concurrent_load"] = {
            "total_requests": total,
            "successful_requests": successful,
            "success_rate": success_rate,
            "average_response_time": avg_time,
        }

        duration = time.time() - start_time
        self.log_test_result("Concurrent Load", success, details, duration)
        return success

    def generate_final_report(self) -> Dict:
        """Generate and display final test report."""
        print(f"\n{'='*80}")
        print("📊 COMPREHENSIVE TEST SUITE - FINAL REPORT")
        print(f"{'='*80}")

        total_duration = time.time() - self.start_time if self.start_time else 0
        success_rate = (
            (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        )

        # Summary
        print("📈 SUMMARY:")
        print(f"   Total Tests: {self.total_tests}")
        print(f"   Passed: {self.passed_tests} ✅")
        print(f"   Failed: {self.failed_tests} ❌")
        print(f"   Success Rate: {success_rate:.1f}%")
        print(f"   Total Duration: {total_duration:.2f} seconds")

        # Detailed results
        print("\n🎯 DETAILED RESULTS:")
        for test_name, result in self.test_results.items():
            status = "✅ PASSED" if result["success"] else "❌ FAILED"
            duration = result.get("duration", 0)
            print(f"   {status} {test_name} ({duration:.2f}s)")
            if result.get("details"):
                print(f"      📋 {result['details']}")

        # Performance metrics
        if self.performance_metrics:
            print("\n⚡ PERFORMANCE METRICS:")
            for metric_name, metrics in self.performance_metrics.items():
                print(f"   {metric_name.replace('_', ' ').title()}:")
                for key, value in metrics.items():
                    if isinstance(value, float):
                        print(f"      {key}: {value:.3f}")
                    else:
                        print(f"      {key}: {value}")

        # Create report data
        report = {
            "summary": {
                "total_tests": self.total_tests,
                "passed_tests": self.passed_tests,
                "failed_tests": self.failed_tests,
                "success_rate": success_rate,
                "total_duration": total_duration,
                "timestamp": datetime.now().isoformat(),
            },
            "test_results": self.test_results,
            "performance_metrics": self.performance_metrics,
        }

        # Save report
        try:
            os.makedirs("reports", exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"reports/comprehensive_test_report_{timestamp}.json"

            with open(filename, "w") as f:
                json.dump(report, f, indent=2, default=str)

            print(f"\n💾 Report saved to: {filename}")
        except Exception as e:
            print(f"\n⚠️ Could not save report: {e}")

        # Final verdict
        if success_rate == 100:
            print(
                "\n🎉 ALL TESTS PASSED! The system is fully functional and ready for production."
            )
        elif success_rate >= 80:
            print(
                f"\n✅ MOSTLY SUCCESSFUL! {success_rate:.1f}% tests passed. Minor issues may need attention."
            )
        elif success_rate >= 60:
            print(
                f"\n⚠️ PARTIAL SUCCESS! {success_rate:.1f}% tests passed. Some components need fixing."
            )
        else:
            print(
                f"\n❌ SIGNIFICANT ISSUES! Only {success_rate:.1f}% tests passed. Major fixes required."
            )

        print(f"\n{'='*80}")
        return report

    def run_all_tests(self) -> bool:
        """Run the complete test suite."""
        self.start_time = time.time()

        print("🚀 STARTING COMPREHENSIVE TEST SUITE")
        print(f"📅 Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🎯 Target: {self.base_url}")

        # Define test sequence
        test_sequence = [
            ("Service Availability", self.test_service_availability),
            ("Health Monitoring", self.test_health_endpoints),
            ("Authentication", self.test_authentication),
            ("Model Management", self.test_model_management),
            ("Chat Functionality", self.test_chat_functionality),
            ("Document Processing", self.test_document_processing),
            ("Cache & Storage", self.test_cache_and_storage),
            ("Error Handling", self.test_error_handling),
            ("Concurrent Load", self.test_concurrent_load),
        ]

        # Execute all tests
        print(f"\n🧪 Executing {len(test_sequence)} test suites...")

        for test_name, test_func in test_sequence:
            try:
                print(f"\n🔄 Starting {test_name}...")
                test_func()
            except Exception as e:
                self.log_test_result(test_name, False, f"Exception: {str(e)}")
                print(f"❌ EXCEPTION in {test_name}: {e}")
                traceback.print_exc()

        # Generate final report
        report = self.generate_final_report()

        # Return overall success
        return self.passed_tests == self.total_tests


def main():
    """Main entry point."""
    print("🧪 Comprehensive Real-Life Simulation Test Suite")
    print("=" * 80)

    try:
        suite = ComprehensiveTestSuite()
        success = suite.run_all_tests()

        exit_code = 0 if success else 1
        print(f"\n👋 Test suite completed with exit code: {exit_code}")
        return exit_code

    except KeyboardInterrupt:
        print("\n\n🛑 Test suite interrupted by user")
        return 130
    except Exception as e:
        print(f"\n\n💥 Test suite crashed: {e}")
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
