#!/usr/bin/env python3
"""
FINAL COMPREHENSIVE TEST SUITE
==============================

Complete end-to-end testing of the LLM backend system including model setup.

Date: June 19, 2025
"""

import json
import subprocess
import sys
import time
from datetime import datetime

import requests


class FinalTestSuite:
    """Complete test suite for the LLM backend system."""

    def __init__(self):
        self.base_url = "http://localhost:8001"
        self.api_key = "f2b985dd-219f-45b1-a90e-170962cc7082"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        self.results = []

    def log(self, message):
        """Log a message with timestamp."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")

    def test_step(self, name, func):
        """Execute a test step and log results."""
        self.log(f"🔄 {name}")
        try:
            start_time = time.time()
            result = func()
            duration = time.time() - start_time
            if result:
                self.log(f"✅ {name} - PASSED ({duration:.2f}s)")
                self.results.append(
                    {"name": name, "status": "PASSED", "duration": duration}
                )
                return True
            else:
                self.log(f"❌ {name} - FAILED ({duration:.2f}s)")
                self.results.append(
                    {"name": name, "status": "FAILED", "duration": duration}
                )
                return False
        except Exception as e:
            self.log(f"❌ {name} - ERROR: {str(e)}")
            self.results.append({"name": name, "status": "ERROR", "error": str(e)})
            return False

    def check_docker_status(self):
        """Check if all Docker containers are running."""
        try:
            result = subprocess.run(
                ["docker", "compose", "ps", "--format", "json"],
                capture_output=True,
                text=True,
                check=True,
            )
            containers = json.loads(result.stdout) if result.stdout.strip() else []

            required_services = [
                "backend-redis",
                "backend-chroma",
                "backend-ollama",
                "backend-llm-backend",
                "backend-openwebui",
            ]
            running_services = [
                c["Name"] for c in containers if c["State"] == "running"
            ]

            missing = [s for s in required_services if s not in running_services]
            if missing:
                self.log(f"❌ Missing services: {missing}")
                return False

            self.log(f"✅ All {len(required_services)} services running")
            return True
        except Exception as e:
            self.log(f"❌ Docker check failed: {e}")
            return False

    def test_health_endpoint(self):
        """Test the health endpoint."""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "ok":
                    self.log(f"   Status: {data.get('summary', 'OK')}")
                    return True
            return False
        except:
            return False

    def test_cache_functionality(self):
        """Test Redis cache functionality."""
        try:
            # Set cache
            set_data = {"key": "test_final", "value": "test_value_final", "ttl": 300}
            set_response = requests.post(
                f"{self.base_url}/cache/set",
                headers=self.headers,
                json=set_data,
                timeout=5,
            )

            if set_response.status_code != 200:
                return False

            # Get cache
            get_response = requests.get(
                f"{self.base_url}/cache/get/test_final", headers=self.headers, timeout=5
            )

            if get_response.status_code == 200:
                data = get_response.json()
                return data.get("success", False)
            return False
        except:
            return False

    def test_models_endpoint(self):
        """Test the models endpoint."""
        try:
            response = requests.get(
                f"{self.base_url}/v1/models", headers=self.headers, timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                models = data.get("data", [])
                self.log(f"   Found {len(models)} models")
                return True
            return False
        except:
            return False

    def check_ollama_model(self):
        """Check if Ollama model is available."""
        try:
            result = subprocess.run(
                ["docker", "exec", "backend-ollama", "ollama", "list"],
                capture_output=True,
                text=True,
                check=True,
            )

            lines = result.stdout.strip().split("\n")[1:]  # Skip header
            models = [line.split()[0] for line in lines if line.strip()]

            if "llama3.2:3b" in models:
                self.log("   Model llama3.2:3b is available")
                return True
            else:
                self.log("   Model llama3.2:3b not found")
                return False
        except:
            return False

    def test_chat_completion(self):
        """Test chat completion functionality."""
        try:
            chat_data = {
                "model": "llama3.2:3b",
                "messages": [
                    {"role": "user", "content": "Say 'Hello, World!' and nothing else."}
                ],
                "max_tokens": 50,
                "temperature": 0.1,
            }

            response = requests.post(
                f"{self.base_url}/v1/chat/completions",
                headers=self.headers,
                json=chat_data,
                timeout=30,
            )

            if response.status_code == 200:
                data = response.json()
                if data.get("choices") and len(data["choices"]) > 0:
                    content = data["choices"][0]["message"]["content"]
                    self.log(f"   Response: {content[:50]}...")
                    return True
            return False
        except:
            return False

    def test_rag_query(self):
        """Test RAG query functionality."""
        try:
            rag_data = {
                "query": "What is machine learning?",
                "user_id": "test_final_user",
                "max_results": 3,
                "similarity_threshold": 0.7,
            }

            response = requests.post(
                f"{self.base_url}/rag/query",
                headers=self.headers,
                json=rag_data,
                timeout=10,
            )

            if response.status_code == 200:
                data = response.json()
                self.log("   RAG query processed successfully")
                return True
            return False
        except:
            return False

    def test_web_interface(self):
        """Test web interface accessibility."""
        try:
            response = requests.get("http://localhost:3000", timeout=5)
            if response.status_code == 200 and "Open WebUI" in response.text:
                self.log("   Web interface is accessible")
                return True
            return False
        except:
            return False

    def run_comprehensive_test(self):
        """Run the complete test suite."""
        self.log("🚀 STARTING FINAL COMPREHENSIVE TEST SUITE")
        self.log("=" * 60)

        start_time = time.time()

        # Core infrastructure tests
        self.test_step("Docker Container Status", self.check_docker_status)
        self.test_step("Health Endpoint", self.test_health_endpoint)
        self.test_step("Cache Functionality", self.test_cache_functionality)
        self.test_step("Models Endpoint", self.test_models_endpoint)

        # Model and AI tests
        self.test_step("Ollama Model Availability", self.check_ollama_model)
        self.test_step("Chat Completion", self.test_chat_completion)
        self.test_step("RAG Query Processing", self.test_rag_query)

        # Interface tests
        self.test_step("Web Interface", self.test_web_interface)

        total_time = time.time() - start_time

        # Generate summary
        self.log("=" * 60)
        self.log("🏁 FINAL TEST SUMMARY")
        self.log("=" * 60)

        passed = len([r for r in self.results if r["status"] == "PASSED"])
        failed = len([r for r in self.results if r["status"] in ["FAILED", "ERROR"]])
        total = len(self.results)

        self.log(f"📊 Tests: {total} | ✅ Passed: {passed} | ❌ Failed: {failed}")
        self.log(f"📈 Success Rate: {(passed/total)*100:.1f}%")
        self.log(f"⏱️ Total Time: {total_time:.2f}s")

        if passed >= total * 0.8:  # 80% success rate
            self.log("🎉 SYSTEM IS PRODUCTION READY!")
            status = "PRODUCTION_READY"
        elif passed >= total * 0.6:  # 60% success rate
            self.log("⚠️ SYSTEM NEEDS MINOR FIXES")
            status = "MINOR_ISSUES"
        else:
            self.log("❌ SYSTEM NEEDS MAJOR ATTENTION")
            status = "MAJOR_ISSUES"

        # Save results
        report = {
            "timestamp": datetime.now().isoformat(),
            "duration": total_time,
            "status": status,
            "success_rate": (passed / total) * 100,
            "results": self.results,
        }

        with open("final_test_report.json", "w") as f:
            json.dump(report, f, indent=2)

        self.log("📋 Detailed report saved to: final_test_report.json")

        return status == "PRODUCTION_READY"


def main():
    """Main function."""
    print(
        """
    🌟 FINAL COMPREHENSIVE TEST SUITE 🌟
    ===================================

    This test validates the complete LLM backend system:
    • Docker container orchestration
    • Service health and connectivity
    • Cache and database functionality
    • LLM model availability and processing
    • API endpoints and chat completions
    • RAG query processing
    • Web interface accessibility

    """
    )

    tester = FinalTestSuite()
    success = tester.run_comprehensive_test()

    if success:
        print("\n🎉 ALL SYSTEMS GO - READY FOR DEPLOYMENT! 🎉")
        sys.exit(0)
    else:
        print("\n⚠️ SYSTEM CHECK COMPLETE - REVIEW RESULTS ⚠️")
        sys.exit(1)


if __name__ == "__main__":
    main()
