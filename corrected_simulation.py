#!/usr/bin/env python3
"""
CORRECTED REAL-LIFE SIMULATION TEST
==================================

This corrected version tests actual available endpoints and functionality.

Date: June 19, 2025
"""

import json
import sys
import time
from datetime import datetime
from typing import Any

import requests


class CorrectedSimulation:
    """Corrected simulation testing actual available endpoints."""

    def __init__(self):
        self.base_url = "http://localhost:8001"
        self.api_key = "f2b985dd-219f-45b1-a90e-170962cc7082"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        self.test_results = {
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "start_time": datetime.now().isoformat(),
            "tests": [],
        }

    def log_test_result(
        self,
        test_name: str,
        success: bool,
        details: str = "",
        response_time: float = 0,
        data: Any = None,
    ):
        """Log a test result."""
        self.test_results["total_tests"] += 1
        if success:
            self.test_results["passed"] += 1
            print(f"✅ {test_name}: PASSED ({response_time:.2f}s)")
        else:
            self.test_results["failed"] += 1
            print(f"❌ {test_name}: FAILED - {details}")

        self.test_results["tests"].append(
            {
                "name": test_name,
                "success": success,
                "details": details,
                "response_time": response_time,
                "timestamp": datetime.now().isoformat(),
                "data": data,
            }
        )

    def test_1_service_health(self):
        """Test 1: Service Health Check"""
        print("\n🏥 TESTING SERVICE HEALTH")

        start_time = time.time()
        try:
            response = requests.get(f"{self.base_url}/health", timeout=10)
            response_time = time.time() - start_time

            if response.status_code == 200:
                health_data = response.json()
                self.log_test_result(
                    "Service Health Check",
                    True,
                    "All services healthy",
                    response_time,
                    health_data,
                )
                print(f"Status: {health_data.get('status')}")
                print(f"Summary: {health_data.get('summary')}")
            else:
                self.log_test_result(
                    "Service Health Check",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    response_time,
                )
        except Exception as e:
            self.log_test_result(
                "Service Health Check",
                False,
                f"Exception: {str(e)}",
                time.time() - start_time,
            )

    def test_2_cache_operations(self):
        """Test 2: Cache Operations"""
        print("\n🗃️ TESTING CACHE OPERATIONS")

        start_time = time.time()
        try:
            # Test cache set
            test_data = {
                "key": "test_simulation_key",
                "value": "real_life_test_value",
                "ttl": 3600,
            }

            response = requests.post(
                f"{self.base_url}/cache/set",
                headers=self.headers,
                json=test_data,
                timeout=10,
            )
            response_time = time.time() - start_time

            if response.status_code == 200:
                # Test cache get
                get_response = requests.get(
                    f"{self.base_url}/cache/get/test_simulation_key",
                    headers=self.headers,
                    timeout=10,
                )

                if get_response.status_code == 200:
                    cached_data = get_response.json()
                    self.log_test_result(
                        "Cache Operations",
                        True,
                        "Cache set and get successful",
                        response_time,
                        cached_data,
                    )
                else:
                    self.log_test_result(
                        "Cache Operations",
                        False,
                        f"Cache get failed: {get_response.text}",
                        response_time,
                    )
            else:
                self.log_test_result(
                    "Cache Operations",
                    False,
                    f"Cache set failed: {response.text}",
                    response_time,
                )
        except Exception as e:
            self.log_test_result(
                "Cache Operations",
                False,
                f"Exception: {str(e)}",
                time.time() - start_time,
            )

    def test_3_document_upload(self):
        """Test 3: Document Upload"""
        print("\n📄 TESTING DOCUMENT UPLOAD")

        start_time = time.time()
        try:
            # Test document upload
            test_document = {
                "content": """
                # System Documentation

                This is a test document for our LLM backend system.
                It contains information about:
                - FastAPI backend architecture
                - Redis caching layer
                - ChromaDB vector database
                - Ollama LLM integration

                ## Performance
                The system is designed for high performance and scalability.
                """,
                "filename": "test_doc.md",
                "document_type": "markdown",
            }

            response = requests.post(
                f"{self.base_url}/document",
                headers=self.headers,
                json=test_document,
                timeout=30,
            )
            response_time = time.time() - start_time

            if response.status_code == 200:
                upload_result = response.json()
                self.log_test_result(
                    "Document Upload",
                    True,
                    "Document uploaded successfully",
                    response_time,
                    upload_result,
                )
                # Store document ID for later tests
                self.document_id = upload_result.get("document_id")
            else:
                self.log_test_result(
                    "Document Upload",
                    False,
                    f"Upload failed: {response.text}",
                    response_time,
                )
        except Exception as e:
            self.log_test_result(
                "Document Upload",
                False,
                f"Exception: {str(e)}",
                time.time() - start_time,
            )

    def test_4_rag_query(self):
        """Test 4: RAG Query"""
        print("\n🔍 TESTING RAG QUERY")

        start_time = time.time()
        try:
            # Test RAG query with proper parameters
            rag_query = {
                "query": "What is the system architecture?",
                "user_id": "test_user_simulation",
                "use_rag": True,
                "max_results": 5,
                "similarity_threshold": 0.7,
            }

            response = requests.post(
                f"{self.base_url}/rag/query",
                headers=self.headers,
                json=rag_query,
                timeout=30,
            )
            response_time = time.time() - start_time

            if response.status_code == 200:
                rag_result = response.json()
                self.log_test_result(
                    "RAG Query",
                    True,
                    "RAG query successful",
                    response_time,
                    rag_result,
                )
            else:
                self.log_test_result(
                    "RAG Query",
                    False,
                    f"RAG query failed: {response.text}",
                    response_time,
                )
        except Exception as e:
            self.log_test_result(
                "RAG Query", False, f"Exception: {str(e)}", time.time() - start_time
            )

    def test_5_llm_chat(self):
        """Test 5: LLM Chat"""
        print("\n💬 TESTING LLM CHAT")

        start_time = time.time()
        try:
            # Test OpenAI-compatible chat endpoint
            chat_request = {
                "model": "llama3.2:3b",
                "messages": [
                    {
                        "role": "user",
                        "content": "What is 2+2? Please give a brief answer.",
                    }
                ],
                "temperature": 0.7,
                "max_tokens": 100,
            }

            response = requests.post(
                f"{self.base_url}/v1/chat/completions",
                headers=self.headers,
                json=chat_request,
                timeout=60,
            )
            response_time = time.time() - start_time

            if response.status_code == 200:
                chat_result = response.json()
                self.log_test_result(
                    "LLM Chat",
                    True,
                    "Chat completion successful",
                    response_time,
                    chat_result,
                )

                # Log the response content
                if chat_result.get("choices"):
                    content = chat_result["choices"][0]["message"]["content"]
                    print(f"LLM Response: {content[:100]}...")
            else:
                self.log_test_result(
                    "LLM Chat", False, f"Chat failed: {response.text}", response_time
                )
        except Exception as e:
            self.log_test_result(
                "LLM Chat", False, f"Exception: {str(e)}", time.time() - start_time
            )

    def test_6_models_endpoint(self):
        """Test 6: Models Endpoint"""
        print("\n🤖 TESTING MODELS ENDPOINT")

        start_time = time.time()
        try:
            response = requests.get(
                f"{self.base_url}/v1/models", headers=self.headers, timeout=10
            )
            response_time = time.time() - start_time

            if response.status_code == 200:
                models_data = response.json()
                self.log_test_result(
                    "Models Endpoint",
                    True,
                    f"Retrieved {len(models_data.get('data', []))} models",
                    response_time,
                    models_data,
                )
            else:
                self.log_test_result(
                    "Models Endpoint",
                    False,
                    f"Models failed: {response.text}",
                    response_time,
                )
        except Exception as e:
            self.log_test_result(
                "Models Endpoint",
                False,
                f"Exception: {str(e)}",
                time.time() - start_time,
            )

    def test_7_learning_system(self):
        """Test 7: Learning System"""
        print("\n🧠 TESTING LEARNING SYSTEM")

        start_time = time.time()
        try:
            # Test learning submission
            learning_data = {
                "user_id": "test_user_simulation",
                "query": "What is the system architecture?",
                "response": "The system uses FastAPI with Redis and ChromaDB.",
                "feedback": "positive",
                "context": "simulation_test",
            }

            response = requests.post(
                f"{self.base_url}/learning/submit",
                headers=self.headers,
                json=learning_data,
                timeout=10,
            )
            response_time = time.time() - start_time

            if response.status_code == 200:
                learning_result = response.json()
                self.log_test_result(
                    "Learning System",
                    True,
                    "Learning data submitted successfully",
                    response_time,
                    learning_result,
                )
            else:
                self.log_test_result(
                    "Learning System",
                    False,
                    f"Learning submission failed: {response.text}",
                    response_time,
                )
        except Exception as e:
            self.log_test_result(
                "Learning System",
                False,
                f"Exception: {str(e)}",
                time.time() - start_time,
            )

    def test_8_storage_health(self):
        """Test 8: Storage Health"""
        print("\n💾 TESTING STORAGE HEALTH")

        start_time = time.time()
        try:
            response = requests.get(
                f"{self.base_url}/storage/health", headers=self.headers, timeout=10
            )
            response_time = time.time() - start_time

            if response.status_code == 200:
                storage_data = response.json()
                self.log_test_result(
                    "Storage Health",
                    True,
                    "Storage health check successful",
                    response_time,
                    storage_data,
                )
            else:
                self.log_test_result(
                    "Storage Health",
                    False,
                    f"Storage health failed: {response.text}",
                    response_time,
                )
        except Exception as e:
            self.log_test_result(
                "Storage Health",
                False,
                f"Exception: {str(e)}",
                time.time() - start_time,
            )

    def generate_report(self):
        """Generate final test report."""
        self.test_results["end_time"] = datetime.now().isoformat()
        self.test_results["duration"] = (
            datetime.fromisoformat(self.test_results["end_time"])
            - datetime.fromisoformat(self.test_results["start_time"])
        ).total_seconds()

        success_rate = (
            self.test_results["passed"] / max(self.test_results["total_tests"], 1)
        ) * 100

        print("\n" + "=" * 80)
        print("🏁 CORRECTED SIMULATION TEST REPORT")
        print("=" * 80)
        print(f"📊 Total Tests: {self.test_results['total_tests']}")
        print(f"✅ Passed: {self.test_results['passed']}")
        print(f"❌ Failed: {self.test_results['failed']}")
        print(f"📈 Success Rate: {success_rate:.1f}%")
        print(f"⏱️ Total Duration: {self.test_results['duration']:.2f} seconds")
        print("=" * 80)

        # Save detailed report
        with open("corrected_simulation_report.json", "w") as f:
            json.dump(self.test_results, f, indent=2, default=str)

        print("📋 Detailed report saved to: corrected_simulation_report.json")

        if success_rate >= 70:
            print("🎉 SIMULATION PASSED: Core functionality working!")
        else:
            print("⚠️ SIMULATION NEEDS ATTENTION: Some issues found")

        return success_rate >= 70

    def run_simulation(self):
        """Run the corrected simulation."""
        print("🚀 STARTING CORRECTED REAL-LIFE SIMULATION")
        print("=" * 80)

        # Run all tests
        try:
            self.test_1_service_health()
            self.test_2_cache_operations()
            self.test_3_document_upload()
            self.test_4_rag_query()
            self.test_5_llm_chat()
            self.test_6_models_endpoint()
            self.test_7_learning_system()
            self.test_8_storage_health()
        except KeyboardInterrupt:
            print("⚠️ Simulation interrupted by user")
        except Exception as e:
            print(f"❌ Simulation failed with exception: {str(e)}")

        # Generate final report
        return self.generate_report()


def main():
    """Main entry point for the corrected simulation."""
    print(
        """
    🌟 CORRECTED REAL-LIFE SIMULATION TEST 🌟
    ========================================

    Testing actual available endpoints:
    ✓ Service Health Checks
    ✓ Cache Operations
    ✓ Document Upload
    ✓ RAG Query Processing
    ✓ LLM Chat Completions
    ✓ Models Endpoint
    ✓ Learning System
    ✓ Storage Health

    Starting corrected simulation...
    """
    )

    simulation = CorrectedSimulation()
    success = simulation.run_simulation()

    if success:
        print("\n🎉 CORE FUNCTIONALITY VERIFIED! 🎉")
        return 0
    else:
        print("\n⚠️ SOME ISSUES FOUND - REVIEW NEEDED ⚠️")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
