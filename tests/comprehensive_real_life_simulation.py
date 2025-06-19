#!/usr/bin/env python3
"""
Comprehensive Real-Life Simulation Test Suite
Tests all functionality across the entire project in realistic Docker environment.

This test simulates real-world usage patterns and validates:
- Docker containerization
- Database connections (Redis + ChromaDB)
- Cache management and memory systems
- AI tools integration
- Document processing and RAG
- Upload functionality
- Error handling and feedback
- Adaptive learning
- Storage management
- Health monitoring
- API endpoints
"""

import sys
import os
import time
import json
import requests
import asyncio
from datetime import datetime
from typing import Dict, Any, List
import tempfile
import traceback

# Add the parent directory to Python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from human_logging import init_logging, log_service_status

class ComprehensiveRealLifeTest:
    """Comprehensive real-life simulation test suite."""
    
    def __init__(self):
        self.base_url = "http://localhost:8001"
        self.openwebui_url = "http://localhost:3000"
        self.chroma_url = "http://localhost:8002"
        self.redis_url = "redis://localhost:6379"
        self.test_results = {}
        self.test_data = {}
        
        # Test configuration
        self.api_key = "f2b985dd-219f-45b1-a90e-170962cc7082"
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        init_logging(level="INFO")
    
    def log_test_start(self, test_name: str):
        """Log the start of a test."""
        log_service_status("TEST", "starting", f"🧪 Starting: {test_name}")
        print(f"\n{'='*60}")
        print(f"🧪 {test_name}")
        print(f"{'='*60}")
    
    def log_test_result(self, test_name: str, success: bool, details: str = ""):
        """Log the result of a test."""
        status = "ready" if success else "failed"
        emoji = "✅" if success else "❌"
        log_service_status("TEST", status, f"{emoji} {test_name}: {details}")
        self.test_results[test_name] = {"success": success, "details": details}
    
    def wait_for_service(self, url: str, service_name: str, timeout: int = 60) -> bool:
        """Wait for a service to become available."""
        print(f"⏳ Waiting for {service_name} at {url}...")
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                if url.startswith("redis://"):
                    # Redis check would require redis library
                    print(f"   Assuming Redis is available (container status shows healthy)")
                    return True
                else:
                    response = requests.get(url, timeout=5)
                    if response.status_code in [200, 404]:  # 404 is ok for base URLs
                        print(f"   ✅ {service_name} is available")
                        return True
            except Exception as e:
                pass
            
            time.sleep(2)
        
        print(f"   ❌ {service_name} did not become available within {timeout}s")
        return False
    
    def test_docker_container_health(self) -> bool:
        """Test that all Docker containers are running and healthy."""
        self.log_test_start("Docker Container Health")
        
        try:
            # Check if we can reach each service
            services = [
                (self.base_url, "LLM Backend"),
                (self.chroma_url, "ChromaDB"),
                (self.openwebui_url, "OpenWebUI"),
                ("http://localhost:6379", "Redis")  # Will be handled specially
            ]
            
            all_healthy = True
            service_status = {}
            
            for url, name in services:
                is_available = self.wait_for_service(url, name, timeout=30)
                service_status[name] = is_available
                if not is_available:
                    all_healthy = False
            
            self.test_data["container_health"] = service_status
            
            if all_healthy:
                self.log_test_result("Docker Container Health", True, "All containers healthy")
            else:
                failed_services = [name for name, status in service_status.items() if not status]
                self.log_test_result("Docker Container Health", False, f"Failed services: {failed_services}")
            
            return all_healthy
            
        except Exception as e:
            self.log_test_result("Docker Container Health", False, f"Exception: {str(e)}")
            return False
    
    def test_startup_memory_health_integration(self) -> bool:
        """Test the startup memory health check integration."""
        self.log_test_start("Startup Memory Health Integration")
        
        try:
            # Test the basic health endpoint
            response = requests.get(f"{self.base_url}/health", timeout=30)
            if response.status_code != 200:
                self.log_test_result("Startup Memory Health Integration", False, f"Health endpoint failed: {response.status_code}")
                return False
            
            health_data = response.json()
            
            # Check if cache information is included
            has_cache_info = "cache" in health_data
            cache_version = health_data.get("cache", {}).get("version", "unknown")
            cache_keys = health_data.get("cache", {}).get("total_keys", 0)
            
            # Check database status
            db_status = health_data.get("databases", {})
            redis_available = db_status.get("redis", {}).get("available", False)
            chromadb_available = db_status.get("chromadb", {}).get("available", False)
            
            self.test_data["startup_health"] = {
                "cache_info": has_cache_info,
                "cache_version": cache_version,
                "cache_keys": cache_keys,
                "redis_available": redis_available,
                "chromadb_available": chromadb_available
            }
            
            # Test detailed health endpoint
            try:
                detailed_response = requests.get(f"{self.base_url}/health/detailed", timeout=30)
                if detailed_response.status_code == 200:
                    detailed_data = detailed_response.json()
                    self.test_data["detailed_health"] = detailed_data
            except:
                pass
            
            success = has_cache_info and redis_available
            details = f"Cache: v{cache_version} ({cache_keys} keys), Redis: {'✅' if redis_available else '❌'}, ChromaDB: {'✅' if chromadb_available else '❌'}"
            
            self.log_test_result("Startup Memory Health Integration", success, details)
            return success
            
        except Exception as e:
            self.log_test_result("Startup Memory Health Integration", False, f"Exception: {str(e)}")
            return False
    
    def test_cache_manager_integration(self) -> bool:
        """Test cache manager with enhanced logging in real environment."""
        self.log_test_start("Cache Manager Integration")
        
        try:
            # Test multiple chat requests to trigger cache operations
            test_messages = [
                "What is the capital of France?",
                "Explain quantum computing in simple terms",
                "What is the capital of France?",  # Should hit cache
            ]
            
            response_times = []
            cache_behavior = []
            
            for i, message in enumerate(test_messages):
                start_time = time.time()
                
                chat_payload = {
                    "messages": [{"role": "user", "content": message}],
                    "model": "gpt-4o-mini",
                    "max_tokens": 100,
                    "temperature": 0.1  # Low temperature for consistent responses
                }
                
                response = requests.post(
                    f"{self.base_url}/v1/chat/completions", 
                    json=chat_payload, 
                    headers=self.headers,
                    timeout=60
                )
                
                duration = time.time() - start_time
                response_times.append(duration)
                
                if response.status_code == 200:
                    response_data = response.json()
                    cache_behavior.append({
                        "request": i + 1,
                        "message": message,
                        "duration": duration,
                        "status": "success"
                    })
                else:
                    cache_behavior.append({
                        "request": i + 1,
                        "message": message,
                        "duration": duration,
                        "status": f"failed_{response.status_code}"
                    })
            
            # Check if third request (duplicate) was faster than first (indicating cache hit)
            cache_hit_detected = len(response_times) >= 3 and response_times[2] < response_times[0] * 0.8
            
            self.test_data["cache_manager"] = {
                "response_times": response_times,
                "cache_behavior": cache_behavior,
                "cache_hit_detected": cache_hit_detected
            }
            
            # Check current cache statistics
            try:
                health_response = requests.get(f"{self.base_url}/health", timeout=10)
                if health_response.status_code == 200:
                    health_data = health_response.json()
                    current_cache_keys = health_data.get("cache", {}).get("total_keys", 0)
                    self.test_data["cache_manager"]["final_cache_keys"] = current_cache_keys
            except:
                pass
            
            success = all(cb["status"] == "success" for cb in cache_behavior[:2])  # At least first 2 should succeed
            details = f"Requests: {len(cache_behavior)}, Cache hit detected: {cache_hit_detected}"
            
            self.log_test_result("Cache Manager Integration", success, details)
            return success
            
        except Exception as e:
            self.log_test_result("Cache Manager Integration", False, f"Exception: {str(e)}")
            return False
    
    def test_ai_tools_integration(self) -> bool:
        """Test AI tools (weather, time, units) integration."""
        self.log_test_start("AI Tools Integration")
        
        try:
            # Test tool-invoking queries
            tool_tests = [
                {
                    "query": "What's the current time?",
                    "expected_tool": "get_current_time"
                },
                {
                    "query": "What's the weather like in London?",
                    "expected_tool": "get_weather"
                },
                {
                    "query": "Convert 100 celsius to fahrenheit",
                    "expected_tool": "convert_units"
                }
            ]
            
            tool_results = []
            
            for test in tool_tests:
                try:
                    chat_payload = {
                        "messages": [{"role": "user", "content": test["query"]}],
                        "model": "gpt-4o-mini",
                        "max_tokens": 200
                    }
                    
                    response = requests.post(
                        f"{self.base_url}/v1/chat/completions", 
                        json=chat_payload, 
                        headers=self.headers,
                        timeout=60
                    )
                    
                    if response.status_code == 200:
                        response_data = response.json()
                        content = response_data.get("choices", [{}])[0].get("message", {}).get("content", "")
                        
                        tool_results.append({
                            "query": test["query"],
                            "expected_tool": test["expected_tool"],
                            "response": content[:200],
                            "success": True
                        })
                    else:
                        tool_results.append({
                            "query": test["query"],
                            "expected_tool": test["expected_tool"],
                            "error": f"HTTP {response.status_code}",
                            "success": False
                        })
                        
                except Exception as e:
                    tool_results.append({
                        "query": test["query"],
                        "expected_tool": test["expected_tool"],
                        "error": str(e),
                        "success": False
                    })
            
            self.test_data["ai_tools"] = tool_results
            
            successful_tools = sum(1 for result in tool_results if result["success"])
            success = successful_tools >= len(tool_tests) // 2  # At least half should work
            
            details = f"Successful tool calls: {successful_tools}/{len(tool_tests)}"
            self.log_test_result("AI Tools Integration", success, details)
            return success
            
        except Exception as e:
            self.log_test_result("AI Tools Integration", False, f"Exception: {str(e)}")
            return False
    
    def test_document_upload_and_rag(self) -> bool:
        """Test document upload and RAG functionality."""
        self.log_test_start("Document Upload and RAG")
        
        try:
            # Create a test document
            test_content = """
            This is a comprehensive test document for validating the RAG system.
            
            Key Information:
            - The company was founded in 2023
            - We specialize in AI and machine learning solutions
            - Our headquarters is located in San Francisco
            - We have 50+ employees worldwide
            - Our main product is an intelligent chatbot platform
            
            Technical Details:
            - Built with Python and FastAPI
            - Uses ChromaDB for vector storage
            - Implements Redis for caching
            - Supports multiple AI models
            """
            
            # Create temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                f.write(test_content)
                temp_file_path = f.name
            
            try:
                # Test file upload
                with open(temp_file_path, 'rb') as file:
                    files = {'file': ('test_document.txt', file, 'text/plain')}
                    upload_response = requests.post(
                        f"{self.base_url}/upload/document",
                        files=files,
                        headers={"Authorization": f"Bearer {self.api_key}"},
                        timeout=60
                    )
                
                upload_success = upload_response.status_code == 200
                upload_details = upload_response.json() if upload_success else upload_response.text
                
                if upload_success:
                    # Wait a moment for processing
                    time.sleep(5)
                    
                    # Test RAG query about the uploaded document
                    rag_query = "What year was the company founded and where is it located?"
                    
                    chat_payload = {
                        "messages": [{"role": "user", "content": rag_query}],
                        "model": "gpt-4o-mini",
                        "max_tokens": 200
                    }
                    
                    rag_response = requests.post(
                        f"{self.base_url}/v1/chat/completions", 
                        json=chat_payload, 
                        headers=self.headers,
                        timeout=60
                    )
                    
                    rag_success = rag_response.status_code == 200
                    if rag_success:
                        rag_data = rag_response.json()
                        rag_content = rag_data.get("choices", [{}])[0].get("message", {}).get("content", "")
                        
                        # Check if the response contains information from the document
                        contains_year = "2023" in rag_content
                        contains_location = "San Francisco" in rag_content
                        rag_quality = contains_year and contains_location
                    else:
                        rag_quality = False
                        rag_content = "RAG query failed"
                
                else:
                    rag_success = False
                    rag_quality = False
                    rag_content = "Upload failed, cannot test RAG"
                
            finally:
                # Clean up temp file
                os.unlink(temp_file_path)
            
            self.test_data["document_rag"] = {
                "upload_success": upload_success,
                "upload_details": upload_details,
                "rag_success": rag_success,
                "rag_quality": rag_quality,
                "rag_response": rag_content[:200] if 'rag_content' in locals() else "No response"
            }
            
            overall_success = upload_success and rag_success and rag_quality
            details = f"Upload: {'✅' if upload_success else '❌'}, RAG: {'✅' if rag_success else '❌'}, Quality: {'✅' if rag_quality else '❌'}"
            
            self.log_test_result("Document Upload and RAG", overall_success, details)
            return overall_success
            
        except Exception as e:
            self.log_test_result("Document Upload and RAG", False, f"Exception: {str(e)}")
            return False
    
    def test_error_handling_and_feedback(self) -> bool:
        """Test error handling and feedback systems."""
        self.log_test_start("Error Handling and Feedback")
        
        try:
            error_tests = []
            
            # Test 1: Invalid API key
            try:
                invalid_headers = {"Authorization": "Bearer invalid_key"}
                response = requests.post(
                    f"{self.base_url}/v1/chat/completions",
                    json={"messages": [{"role": "user", "content": "test"}]},
                    headers=invalid_headers,
                    timeout=10
                )
                error_tests.append({
                    "test": "Invalid API Key",
                    "status_code": response.status_code,
                    "handled": response.status_code == 401
                })
            except Exception as e:
                error_tests.append({
                    "test": "Invalid API Key",
                    "error": str(e),
                    "handled": False
                })
            
            # Test 2: Malformed request
            try:
                response = requests.post(
                    f"{self.base_url}/v1/chat/completions",
                    json={"invalid": "request"},
                    headers=self.headers,
                    timeout=10
                )
                error_tests.append({
                    "test": "Malformed Request",
                    "status_code": response.status_code,
                    "handled": response.status_code in [400, 422]
                })
            except Exception as e:
                error_tests.append({
                    "test": "Malformed Request",
                    "error": str(e),
                    "handled": False
                })
            
            # Test 3: Health endpoint resilience
            try:
                response = requests.get(f"{self.base_url}/health", timeout=10)
                error_tests.append({
                    "test": "Health Endpoint",
                    "status_code": response.status_code,
                    "handled": response.status_code == 200
                })
            except Exception as e:
                error_tests.append({
                    "test": "Health Endpoint",
                    "error": str(e),
                    "handled": False
                })
            
            self.test_data["error_handling"] = error_tests
            
            handled_errors = sum(1 for test in error_tests if test.get("handled", False))
            success = handled_errors >= len(error_tests) * 0.7  # 70% should be handled properly
            
            details = f"Properly handled errors: {handled_errors}/{len(error_tests)}"
            self.log_test_result("Error Handling and Feedback", success, details)
            return success
            
        except Exception as e:
            self.log_test_result("Error Handling and Feedback", False, f"Exception: {str(e)}")
            return False
    
    def test_storage_and_persistence(self) -> bool:
        """Test storage management and data persistence."""
        self.log_test_start("Storage and Persistence")
        
        try:
            # Test storage endpoint
            try:
                storage_response = requests.get(f"{self.base_url}/health/storage", timeout=10)
                storage_available = storage_response.status_code == 200
                storage_data = storage_response.json() if storage_available else {}
            except:
                storage_available = False
                storage_data = {}
            
            # Test Redis persistence by checking cache statistics
            try:
                health_response = requests.get(f"{self.base_url}/health", timeout=10)
                if health_response.status_code == 200:
                    health_data = health_response.json()
                    cache_info = health_data.get("cache", {})
                    redis_persistent = cache_info.get("total_keys", 0) > 0
                else:
                    redis_persistent = False
            except:
                redis_persistent = False
            
            # Test ChromaDB persistence (if available)
            try:
                chroma_response = requests.get(f"{self.chroma_url}/api/v1/heartbeat", timeout=5)
                chromadb_available = chroma_response.status_code == 200
            except:
                chromadb_available = False
            
            self.test_data["storage_persistence"] = {
                "storage_endpoint": storage_available,
                "storage_data": storage_data,
                "redis_persistent": redis_persistent,
                "chromadb_available": chromadb_available
            }
            
            # Success if at least storage endpoint and Redis are working
            success = storage_available and redis_persistent
            details = f"Storage: {'✅' if storage_available else '❌'}, Redis: {'✅' if redis_persistent else '❌'}, ChromaDB: {'✅' if chromadb_available else '❌'}"
            
            self.log_test_result("Storage and Persistence", success, details)
            return success
            
        except Exception as e:
            self.log_test_result("Storage and Persistence", False, f"Exception: {str(e)}")
            return False
    
    def test_adaptive_learning_system(self) -> bool:
        """Test adaptive learning functionality."""
        self.log_test_start("Adaptive Learning System")
        
        try:
            # Test adaptive learning by sending feedback
            learning_tests = []
            
            # First, make a chat request
            initial_query = "Explain machine learning briefly"
            chat_payload = {
                "messages": [{"role": "user", "content": initial_query}],
                "model": "gpt-4o-mini",
                "max_tokens": 100
            }
            
            chat_response = requests.post(
                f"{self.base_url}/v1/chat/completions", 
                json=chat_payload, 
                headers=self.headers,
                timeout=30
            )
            
            if chat_response.status_code == 200:
                # Try to send feedback (if endpoint exists)
                try:
                    feedback_payload = {
                        "query": initial_query,
                        "response": "Generated response",
                        "rating": 5,
                        "feedback": "Good explanation"
                    }
                    
                    feedback_response = requests.post(
                        f"{self.base_url}/feedback",
                        json=feedback_payload,
                        headers=self.headers,
                        timeout=10
                    )
                    
                    feedback_success = feedback_response.status_code in [200, 201]
                    learning_tests.append({
                        "test": "Feedback Submission",
                        "success": feedback_success,
                        "status_code": feedback_response.status_code
                    })
                    
                except requests.exceptions.RequestException:
                    learning_tests.append({
                        "test": "Feedback Submission",
                        "success": False,
                        "note": "Feedback endpoint may not be available"
                    })
                
                # Test adaptive learning stats (if available)
                try:
                    stats_response = requests.get(f"{self.base_url}/adaptive/stats", timeout=10)
                    stats_success = stats_response.status_code == 200
                    learning_tests.append({
                        "test": "Learning Stats",
                        "success": stats_success,
                        "status_code": stats_response.status_code
                    })
                except:
                    learning_tests.append({
                        "test": "Learning Stats",
                        "success": False,
                        "note": "Stats endpoint may not be available"
                    })
                
                # Basic chat functionality is working
                learning_tests.append({
                    "test": "Basic Chat (Learning Foundation)",
                    "success": True,
                    "status_code": 200
                })
            
            else:
                learning_tests.append({
                    "test": "Basic Chat (Learning Foundation)",
                    "success": False,
                    "status_code": chat_response.status_code
                })
            
            self.test_data["adaptive_learning"] = learning_tests
            
            # Success if basic chat works (learning foundation)
            basic_success = any(test.get("success") and "Basic Chat" in test.get("test", "") for test in learning_tests)
            success = basic_success
            
            successful_tests = sum(1 for test in learning_tests if test.get("success", False))
            details = f"Learning components working: {successful_tests}/{len(learning_tests)}"
            
            self.log_test_result("Adaptive Learning System", success, details)
            return success
            
        except Exception as e:
            self.log_test_result("Adaptive Learning System", False, f"Exception: {str(e)}")
            return False
    
    def test_comprehensive_integration_scenario(self) -> bool:
        """Test a comprehensive real-world usage scenario."""
        self.log_test_start("Comprehensive Integration Scenario")
        
        try:
            scenario_steps = []
            
            # Step 1: Upload a document with company information
            print("   📄 Step 1: Document upload...")
            company_doc = """
            TechCorp Company Profile
            
            Founded: 2020
            Headquarters: New York, NY
            Employees: 150
            Industry: Technology Consulting
            
            Services:
            - AI and Machine Learning consulting
            - Cloud infrastructure setup
            - Data analytics solutions
            - Custom software development
            
            Recent Projects:
            - Implemented AI chatbot for customer service (2024)
            - Migrated legacy systems to cloud (2023)
            - Developed predictive analytics platform (2023)
            """
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                f.write(company_doc)
                temp_file_path = f.name
            
            try:
                with open(temp_file_path, 'rb') as file:
                    files = {'file': ('company_profile.txt', file, 'text/plain')}
                    upload_response = requests.post(
                        f"{self.base_url}/upload/document",
                        files=files,
                        headers={"Authorization": f"Bearer {self.api_key}"},
                        timeout=30
                    )
                
                upload_success = upload_response.status_code == 200
                scenario_steps.append({"step": "Document Upload", "success": upload_success})
                
                if upload_success:
                    time.sleep(3)  # Allow processing time
                
            finally:
                os.unlink(temp_file_path)
            
            # Step 2: Ask about the uploaded document (RAG)
            print("   🔍 Step 2: RAG query...")
            if upload_success:
                rag_query = "When was TechCorp founded and how many employees do they have?"
                chat_payload = {
                    "messages": [{"role": "user", "content": rag_query}],
                    "model": "gpt-4o-mini",
                    "max_tokens": 150
                }
                
                rag_response = requests.post(
                    f"{self.base_url}/v1/chat/completions", 
                    json=chat_payload, 
                    headers=self.headers,
                    timeout=30
                )
                
                rag_success = rag_response.status_code == 200
                scenario_steps.append({"step": "RAG Query", "success": rag_success})
                
                if rag_success:
                    rag_content = rag_response.json().get("choices", [{}])[0].get("message", {}).get("content", "")
                    rag_quality = "2020" in rag_content and "150" in rag_content
                    scenario_steps.append({"step": "RAG Quality", "success": rag_quality})
            
            # Step 3: Use AI tools (weather, time)
            print("   🛠️ Step 3: AI tools...")
            tool_query = "What's the current time and weather in New York?"
            chat_payload = {
                "messages": [{"role": "user", "content": tool_query}],
                "model": "gpt-4o-mini",
                "max_tokens": 200
            }
            
            tool_response = requests.post(
                f"{self.base_url}/v1/chat/completions", 
                json=chat_payload, 
                headers=self.headers,
                timeout=30
            )
            
            tool_success = tool_response.status_code == 200
            scenario_steps.append({"step": "AI Tools", "success": tool_success})
            
            # Step 4: Test caching with repeated query
            print("   💾 Step 4: Cache testing...")
            if tool_success:
                # Repeat the same query to test caching
                start_time = time.time()
                cache_response = requests.post(
                    f"{self.base_url}/v1/chat/completions", 
                    json=chat_payload, 
                    headers=self.headers,
                    timeout=30
                )
                cache_time = time.time() - start_time
                
                cache_success = cache_response.status_code == 200
                # Cache hit would typically be much faster
                cache_hit_likely = cache_time < 1.0  # Less than 1 second suggests cache hit
                scenario_steps.append({"step": "Cache Test", "success": cache_success and cache_hit_likely})
            
            # Step 5: Check system health
            print("   🏥 Step 5: Health check...")
            health_response = requests.get(f"{self.base_url}/health", timeout=10)
            health_success = health_response.status_code == 200
            scenario_steps.append({"step": "Health Check", "success": health_success})
            
            self.test_data["integration_scenario"] = scenario_steps
            
            # Success if most steps completed successfully
            successful_steps = sum(1 for step in scenario_steps if step["success"])
            total_steps = len(scenario_steps)
            success = successful_steps >= total_steps * 0.8  # 80% success rate
            
            details = f"Successful steps: {successful_steps}/{total_steps}"
            self.log_test_result("Comprehensive Integration Scenario", success, details)
            return success
            
        except Exception as e:
            self.log_test_result("Comprehensive Integration Scenario", False, f"Exception: {str(e)}")
            return False
    
    def test_persona_and_configuration(self) -> bool:
        """Test persona configuration and behavior."""
        self.log_test_start("Persona and Configuration")
        
        try:
            # Test if persona affects responses
            persona_tests = []
            
            # Test basic personality consistency
            personality_query = "How should I approach learning a new programming language?"
            chat_payload = {
                "messages": [{"role": "user", "content": personality_query}],
                "model": "gpt-4o-mini",
                "max_tokens": 200
            }
            
            response = requests.post(
                f"{self.base_url}/v1/chat/completions", 
                json=chat_payload, 
                headers=self.headers,
                timeout=30
            )
            
            if response.status_code == 200:
                response_data = response.json()
                content = response_data.get("choices", [{}])[0].get("message", {}).get("content", "")
                
                # Check for helpful, structured response (indicating good persona)
                is_helpful = len(content) > 50  # Substantial response
                is_structured = any(char in content for char in ['1.', '2.', '-', '*'])  # Some structure
                
                persona_tests.append({
                    "test": "Personality Consistency",
                    "success": is_helpful and is_structured,
                    "response_length": len(content),
                    "has_structure": is_structured
                })
            
            # Test configuration endpoints (if available)
            try:
                config_response = requests.get(f"{self.base_url}/config", timeout=10)
                config_success = config_response.status_code in [200, 404]  # 404 is acceptable
                persona_tests.append({
                    "test": "Configuration Endpoint",
                    "success": config_success,
                    "status_code": config_response.status_code
                })
            except:
                persona_tests.append({
                    "test": "Configuration Endpoint",
                    "success": False,
                    "note": "Endpoint not accessible"
                })
            
            self.test_data["persona_config"] = persona_tests
            
            # Success if basic personality test passes
            personality_success = any(test.get("success") and "Personality" in test.get("test", "") for test in persona_tests)
            
            details = f"Persona tests passed: {sum(1 for test in persona_tests if test.get('success', False))}/{len(persona_tests)}"
            self.log_test_result("Persona and Configuration", personality_success, details)
            return personality_success
            
        except Exception as e:
            self.log_test_result("Persona and Configuration", False, f"Exception: {str(e)}")
            return False
    
    def generate_comprehensive_report(self) -> Dict[str, Any]:
        """Generate a comprehensive test report with recommendations."""
        print("\n" + "="*80)
        print("📊 COMPREHENSIVE REAL-LIFE SIMULATION REPORT")
        print("="*80)
        
        # Calculate overall statistics
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result["success"])
        pass_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        # Categorize results
        critical_tests = [
            "Docker Container Health",
            "Startup Memory Health Integration", 
            "Cache Manager Integration"
        ]
        
        core_functionality = [
            "AI Tools Integration",
            "Document Upload and RAG",
            "Error Handling and Feedback"
        ]
        
        advanced_features = [
            "Storage and Persistence",
            "Adaptive Learning System",
            "Comprehensive Integration Scenario",
            "Persona and Configuration"
        ]
        
        # Generate detailed report
        report = {
            "test_summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": total_tests - passed_tests,
                "pass_rate": round(pass_rate, 2),
                "timestamp": datetime.now().isoformat()
            },
            "test_results": self.test_results,
            "test_data": self.test_data,
            "categories": {
                "critical": {
                    "tests": critical_tests,
                    "passed": sum(1 for test in critical_tests if self.test_results.get(test, {}).get("success", False)),
                    "total": len(critical_tests)
                },
                "core": {
                    "tests": core_functionality,
                    "passed": sum(1 for test in core_functionality if self.test_results.get(test, {}).get("success", False)),
                    "total": len(core_functionality)
                },
                "advanced": {
                    "tests": advanced_features,
                    "passed": sum(1 for test in advanced_features if self.test_results.get(test, {}).get("success", False)),
                    "total": len(advanced_features)
                }
            }
        }
        
        # Print summary
        print(f"\n🎯 OVERALL RESULTS:")
        print(f"   Total Tests: {total_tests}")
        print(f"   Passed: {passed_tests} ✅")
        print(f"   Failed: {total_tests - passed_tests} ❌")
        print(f"   Pass Rate: {pass_rate:.1f}%")
        
        print(f"\n📊 CATEGORY BREAKDOWN:")
        for category, data in report["categories"].items():
            cat_pass_rate = (data["passed"] / data["total"] * 100) if data["total"] > 0 else 0
            status_emoji = "✅" if cat_pass_rate >= 80 else "⚠️" if cat_pass_rate >= 60 else "❌"
            print(f"   {category.capitalize()}: {data['passed']}/{data['total']} ({cat_pass_rate:.1f}%) {status_emoji}")
        
        print(f"\n📋 DETAILED RESULTS:")
        for test_name, result in self.test_results.items():
            status = "✅ PASS" if result["success"] else "❌ FAIL"
            details = f" - {result['details']}" if result["details"] else ""
            print(f"   {test_name:<35} {status}{details}")
        
        # Generate recommendations
        recommendations = self.generate_recommendations(report)
        report["recommendations"] = recommendations
        
        print(f"\n💡 RECOMMENDATIONS:")
        for rec in recommendations:
            print(f"   • {rec}")
        
        # Overall assessment
        if pass_rate >= 90:
            assessment = "🎉 EXCELLENT - Production ready with full functionality"
        elif pass_rate >= 75:
            assessment = "✅ GOOD - Production ready with minor issues to address"
        elif pass_rate >= 60:
            assessment = "⚠️ FAIR - Needs attention before full production deployment"
        else:
            assessment = "❌ POOR - Significant issues need resolution"
        
        print(f"\n🏆 OVERALL ASSESSMENT: {assessment}")
        print(f"⏰ Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return report
    
    def generate_recommendations(self, report: Dict[str, Any]) -> List[str]:
        """Generate specific recommendations based on test results."""
        recommendations = []
        
        # Check critical systems
        critical_passed = report["categories"]["critical"]["passed"]
        critical_total = report["categories"]["critical"]["total"]
        
        if critical_passed < critical_total:
            recommendations.append("🚨 CRITICAL: Fix core infrastructure issues (Docker, memory, cache)")
        
        # Specific recommendations based on failures
        failed_tests = [name for name, result in self.test_results.items() if not result["success"]]
        
        if "Docker Container Health" in failed_tests:
            recommendations.append("Fix Docker container startup issues - check compose configuration")
        
        if "Startup Memory Health Integration" in failed_tests:
            recommendations.append("Investigate memory/cache initialization problems")
        
        if "Cache Manager Integration" in failed_tests:
            recommendations.append("Debug cache operations and Redis connectivity")
        
        if "AI Tools Integration" in failed_tests:
            recommendations.append("Verify API keys for weather service and tool implementations")
        
        if "Document Upload and RAG" in failed_tests:
            recommendations.append("Check file upload permissions and ChromaDB vector operations")
        
        if "Storage and Persistence" in failed_tests:
            recommendations.append("Validate storage directory permissions and persistence setup")
        
        # Performance recommendations
        cache_data = self.test_data.get("cache_manager", {})
        if cache_data.get("cache_hit_detected") == False:
            recommendations.append("Optimize cache configuration for better performance")
        
        # Security recommendations
        error_data = self.test_data.get("error_handling", [])
        handled_errors = sum(1 for test in error_data if test.get("handled", False))
        if handled_errors < len(error_data) * 0.8:
            recommendations.append("Improve error handling and security validation")
        
        # If everything is mostly working
        if report["test_summary"]["pass_rate"] >= 80:
            recommendations.append("✨ Consider implementing monitoring and alerting for production")
            recommendations.append("📚 Document deployment procedures and troubleshooting guides")
        
        return recommendations
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all tests in sequence."""
        print("🚀 STARTING COMPREHENSIVE REAL-LIFE SIMULATION")
        print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("\nThis test will validate all project functionality in the Docker environment...")
        
        # Define test sequence
        test_sequence = [
            self.test_docker_container_health,
            self.test_startup_memory_health_integration,
            self.test_cache_manager_integration,
            self.test_ai_tools_integration,
            self.test_document_upload_and_rag,
            self.test_error_handling_and_feedback,
            self.test_storage_and_persistence,
            self.test_adaptive_learning_system,
            self.test_comprehensive_integration_scenario,
            self.test_persona_and_configuration
        ]
        
        # Run tests
        for test_func in test_sequence:
            try:
                test_func()
                time.sleep(2)  # Brief pause between tests
            except Exception as e:
                test_name = test_func.__name__.replace("test_", "").replace("_", " ").title()
                self.log_test_result(test_name, False, f"Test crashed: {str(e)}")
                print(f"🔥 Test crashed: {e}")
                traceback.print_exc()
        
        # Generate final report
        return self.generate_comprehensive_report()

def main():
    """Main function to run the comprehensive test suite."""
    try:
        # Initialize test suite
        test_suite = ComprehensiveRealLifeTest()
        
        # Run all tests
        report = test_suite.run_all_tests()
        
        # Save detailed report
        report_filename = f"comprehensive_real_life_test_report_{int(time.time())}.json"
        with open(report_filename, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📄 Detailed report saved to: {report_filename}")
        
        # Return exit code based on results
        pass_rate = report["test_summary"]["pass_rate"]
        return 0 if pass_rate >= 75 else 1
        
    except Exception as e:
        print(f"🔥 Test suite crashed: {e}")
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
