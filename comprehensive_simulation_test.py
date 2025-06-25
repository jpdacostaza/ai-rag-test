"""
Comprehensive Real-Life Simulation Test Suite
Tests all functionality, modules, functions, imports, and endpoints
Simulates real-world usage scenarios
"""

import asyncio
import json
import time
import uuid
import random
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
import statistics
import traceback

# Add backend to path for import testing
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

class ComprehensiveSimulationTest:
    def __init__(self, base_url: str = "http://localhost:9099"):
        self.base_url = base_url
        self.test_results = []
        self.performance_metrics = {}
        self.error_log = []
        self.test_users = []
        self.test_documents = []
        self.test_conversations = {}
        self.start_time = None
        self.end_time = None
        
    def run_all_tests(self):
        """Run comprehensive test suite"""
        print("🚀 Starting Comprehensive Real-Life Simulation Test Suite")
        print("=" * 80)
        
        self.start_time = datetime.now()
        
        try:
            # Phase 1: Module Import Tests
            self.test_module_imports()
            
            # Phase 2: Service Health Checks
            self.test_service_health()
            
            # Phase 3: User Simulation
            self.simulate_user_lifecycle()
            
            # Phase 4: Concurrent Operations
            self.test_concurrent_operations()
            
            # Phase 5: Edge Cases and Error Handling
            self.test_edge_cases()
            
            # Phase 6: Performance and Load Testing
            self.test_performance_under_load()
            
            # Phase 7: Integration Tests
            self.test_full_integration_scenarios()
            
            # Phase 8: Cleanup and Recovery Tests
            self.test_cleanup_and_recovery()
            
        except Exception as e:
            self.error_log.append({
                "phase": "main",
                "error": str(e),
                "traceback": traceback.format_exc()
            })
        
        self.end_time = datetime.now()
        
        # Generate comprehensive report
        self.generate_comprehensive_report()
    
    def test_module_imports(self):
        """Test all module imports"""
        print("\n📦 Phase 1: Testing Module Imports")
        print("-" * 60)
        
        modules_to_test = [
            ("main", "Main application"),
            ("config", "Configuration"),
            ("database", "Database interface"),
            ("database_manager", "Database manager"),
            ("human_logging", "Logging system"),
            ("error_handler", "Error handling"),
            ("routes.health", "Health routes"),
            ("routes.chat", "Chat routes"),
            ("routes.models", "Models routes"),
            ("routes.upload", "Upload routes"),
            ("routes.pipeline", "Pipeline routes"),
            ("routes.debug", "Debug routes"),
        ]
        
        import_results = []
        
        for module_name, description in modules_to_test:
            start_time = time.time()
            try:
                module = __import__(module_name, fromlist=[''])
                duration = (time.time() - start_time) * 1000
                
                # Check for required attributes
                attributes = dir(module)
                
                import_results.append({
                    "module": module_name,
                    "description": description,
                    "status": "success",
                    "duration_ms": round(duration, 2),
                    "attributes": len(attributes)
                })
                print(f"✅ {module_name} - Imported successfully ({duration:.2f}ms)")
                
            except Exception as e:
                import_results.append({
                    "module": module_name,
                    "description": description,
                    "status": "failed",
                    "error": str(e)
                })
                print(f"❌ {module_name} - Import failed: {str(e)}")
        
        self.test_results.append({
            "phase": "module_imports",
            "results": import_results,
            "success_rate": sum(1 for r in import_results if r["status"] == "success") / len(import_results)
        })
    
    def test_service_health(self):
        """Test all service health endpoints"""
        print("\n🏥 Phase 2: Service Health Checks")
        print("-" * 60)
        
        health_endpoints = [
            ("/health", "Main health check"),
            ("/", "Root endpoint"),
            ("/upload/health", "Upload service health"),
            ("/v1/models", "Models availability"),
        ]
        
        health_results = []
        
        for endpoint, description in health_endpoints:
            try:
                response = requests.get(f"{self.base_url}{endpoint}", timeout=5)
                response_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else {}
                
                health_results.append({
                    "endpoint": endpoint,
                    "description": description,
                    "status_code": response.status_code,
                    "healthy": response.status_code == 200,
                    "response_time_ms": round(response.elapsed.total_seconds() * 1000, 2),
                    "data": response_data
                })
                
                if response.status_code == 200:
                    print(f"✅ {endpoint} - Healthy ({response.elapsed.total_seconds() * 1000:.2f}ms)")
                else:
                    print(f"⚠️ {endpoint} - Status {response.status_code}")
                    
            except Exception as e:
                health_results.append({
                    "endpoint": endpoint,
                    "description": description,
                    "healthy": False,
                    "error": str(e)
                })
                print(f"❌ {endpoint} - Error: {str(e)}")
        
        self.test_results.append({
            "phase": "service_health",
            "results": health_results,
            "all_healthy": all(r.get("healthy", False) for r in health_results)
        })
    
    def simulate_user_lifecycle(self):
        """Simulate complete user lifecycle"""
        print("\n👥 Phase 3: User Lifecycle Simulation")
        print("-" * 60)
        
        # Create test users
        num_users = 5
        for i in range(num_users):
            user_id = f"test_user_{uuid.uuid4().hex[:8]}"
            self.test_users.append({
                "user_id": user_id,
                "created_at": datetime.now().isoformat(),
                "documents": [],
                "conversations": []
            })
        
        print(f"Created {num_users} test users")
        
        # Simulate user activities
        for user in self.test_users:
            print(f"\n🧪 Testing user: {user['user_id']}")
            
            # 1. Upload documents
            self._test_user_document_upload(user)
            
            # 2. Search documents
            self._test_user_document_search(user)
            
            # 3. Have conversations
            self._test_user_conversations(user)
            
            # 4. Check user memory
            self._test_user_memory_retrieval(user)
    
    def _test_user_document_upload(self, user: Dict):
        """Test document upload for user"""
        documents = [
            {
                "content": "Artificial Intelligence (AI) is transforming the world. Machine learning algorithms are becoming more sophisticated.",
                "metadata": {"category": "technology", "subject": "AI"}
            },
            {
                "content": "Climate change is one of the most pressing issues of our time. Renewable energy sources are crucial for sustainability.",
                "metadata": {"category": "environment", "subject": "climate"}
            },
            {
                "content": "The human brain contains approximately 86 billion neurons. Neuroscience continues to unlock its mysteries.",
                "metadata": {"category": "science", "subject": "neuroscience"}
            }
        ]
        
        for doc in documents:
            try:
                response = requests.post(
                    f"{self.base_url}/upload/document",
                    json={
                        "user_id": user["user_id"],
                        "content": doc["content"],
                        "metadata": doc["metadata"]
                    },
                    timeout=10
                )
                
                if response.status_code == 200:
                    user["documents"].append({
                        "uploaded_at": datetime.now().isoformat(),
                        "status": "success",
                        "content_preview": doc["content"][:50] + "...",
                        "response": response.json()
                    })
                    print(f"  ✅ Uploaded document: {doc['metadata']['subject']}")
                else:
                    print(f"  ❌ Failed to upload document: {response.status_code}")
                    
            except Exception as e:
                print(f"  ❌ Upload error: {str(e)}")
    
    def _test_user_document_search(self, user: Dict):
        """Test document search for user"""
        search_queries = ["AI", "climate", "brain", "technology", "future"]
        
        for query in search_queries:
            try:
                response = requests.post(
                    f"{self.base_url}/upload/search",
                    json={
                        "user_id": user["user_id"],
                        "query": query,
                        "limit": 3
                    },
                    timeout=5
                )
                
                if response.status_code == 200:
                    results = response.json()
                    print(f"  ✅ Search '{query}': {results.get('count', 0)} results")
                else:
                    print(f"  ❌ Search failed for '{query}': {response.status_code}")
                    
            except Exception as e:
                print(f"  ❌ Search error: {str(e)}")
    
    def _test_user_conversations(self, user: Dict):
        """Test chat conversations for user"""
        conversations = [
            "Tell me about artificial intelligence",
            "What are the impacts of climate change?",
            "How does the human brain work?",
            "Summarize what you know about my interests",
            "What documents have I shared with you?"
        ]
        
        for message in conversations:
            try:
                response = requests.post(
                    f"{self.base_url}/chat",
                    json={
                        "user_id": user["user_id"],
                        "message": message
                    },
                    timeout=30
                )
                
                if response.status_code == 200:
                    chat_response = response.json()
                    user["conversations"].append({
                        "timestamp": datetime.now().isoformat(),
                        "message": message,
                        "response": chat_response.get("response", "")[:100] + "...",
                        "duration_ms": response.elapsed.total_seconds() * 1000
                    })
                    print(f"  ✅ Chat: '{message[:30]}...' ({response.elapsed.total_seconds() * 1000:.0f}ms)")
                else:
                    print(f"  ❌ Chat failed: {response.status_code}")
                    
            except Exception as e:
                print(f"  ❌ Chat error: {str(e)}")
    
    def _test_user_memory_retrieval(self, user: Dict):
        """Test memory retrieval for user"""
        # This would test if the system remembers user context
        # For now, we'll verify through search
        try:
            response = requests.post(
                f"{self.base_url}/upload/search",
                json={
                    "user_id": user["user_id"],
                    "query": "artificial intelligence machine learning",
                    "limit": 10
                },
                timeout=5
            )
            
            if response.status_code == 200:
                results = response.json()
                print(f"  ✅ Memory check: {results.get('count', 0)} documents in user memory")
            else:
                print(f"  ❌ Memory check failed: {response.status_code}")
                
        except Exception as e:
            print(f"  ❌ Memory check error: {str(e)}")
    
    def test_concurrent_operations(self):
        """Test concurrent operations"""
        print("\n🔄 Phase 4: Concurrent Operations Test")
        print("-" * 60)
        
        concurrent_tasks = []
        num_concurrent = 10
        
        # Create tasks
        for i in range(num_concurrent):
            task_type = random.choice(["chat", "upload", "search", "health"])
            user_id = f"concurrent_user_{i}"
            
            if task_type == "chat":
                task = {
                    "type": "chat",
                    "endpoint": "/chat",
                    "method": "POST",
                    "data": {
                        "user_id": user_id,
                        "message": f"Concurrent test message {i}"
                    }
                }
            elif task_type == "upload":
                task = {
                    "type": "upload",
                    "endpoint": "/upload/document",
                    "method": "POST",
                    "data": {
                        "user_id": user_id,
                        "content": f"Concurrent test document {i}",
                        "metadata": {"test": True}
                    }
                }
            elif task_type == "search":
                task = {
                    "type": "search",
                    "endpoint": "/upload/search",
                    "method": "POST",
                    "data": {
                        "user_id": user_id,
                        "query": "test",
                        "limit": 5
                    }
                }
            else:  # health
                task = {
                    "type": "health",
                    "endpoint": "/health",
                    "method": "GET",
                    "data": None
                }
            
            concurrent_tasks.append(task)
        
        # Execute concurrent requests
        print(f"Executing {num_concurrent} concurrent requests...")
        start_time = time.time()
        results = []
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_task = {
                executor.submit(self._execute_request, task): task 
                for task in concurrent_tasks
            }
            
            for future in as_completed(future_to_task):
                task = future_to_task[future]
                try:
                    result = future.result()
                    results.append(result)
                    if result["success"]:
                        print(f"✅ {task['type']} request completed")
                    else:
                        print(f"❌ {task['type']} request failed")
                except Exception as e:
                    print(f"❌ {task['type']} request error: {str(e)}")
                    results.append({
                        "task": task,
                        "success": False,
                        "error": str(e)
                    })
        
        duration = time.time() - start_time
        successful = sum(1 for r in results if r.get("success", False))
        
        print(f"\nConcurrent test completed in {duration:.2f}s")
        print(f"Success rate: {successful}/{num_concurrent} ({(successful/num_concurrent)*100:.1f}%)")
        
        self.test_results.append({
            "phase": "concurrent_operations",
            "total_requests": num_concurrent,
            "successful": successful,
            "duration_seconds": duration,
            "requests_per_second": num_concurrent / duration
        })
    
    def _execute_request(self, task: Dict) -> Dict:
        """Execute a single request"""
        try:
            url = f"{self.base_url}{task['endpoint']}"
            start_time = time.time()
            
            if task["method"] == "GET":
                response = requests.get(url, timeout=30)
            else:
                response = requests.post(url, json=task["data"], timeout=30)
            
            duration = time.time() - start_time
            
            return {
                "task": task,
                "success": response.status_code < 400,
                "status_code": response.status_code,
                "duration_seconds": duration
            }
            
        except Exception as e:
            return {
                "task": task,
                "success": False,
                "error": str(e)
            }
    
    def test_edge_cases(self):
        """Test edge cases and error handling"""
        print("\n🔍 Phase 5: Edge Cases and Error Handling")
        print("-" * 60)
        
        edge_cases = [
            {
                "name": "Empty content upload",
                "endpoint": "/upload/document",
                "method": "POST",
                "data": {"user_id": "edge_user", "content": "", "metadata": {}},
                "expected_status": 422
            },
            {
                "name": "Missing user_id in chat",
                "endpoint": "/chat",
                "method": "POST",
                "data": {"message": "Hello"},
                "expected_status": 422
            },
            {
                "name": "Invalid search limit",
                "endpoint": "/upload/search",
                "method": "POST",
                "data": {"user_id": "edge_user", "query": "test", "limit": 100},
                "expected_status": 422
            },
            {
                "name": "Non-existent endpoint",
                "endpoint": "/api/v1/nonexistent",
                "method": "GET",
                "data": None,
                "expected_status": 404
            },
            {
                "name": "Extremely long content",
                "endpoint": "/upload/document",
                "method": "POST",
                "data": {
                    "user_id": "edge_user",
                    "content": "x" * 50000,  # 50KB of text (reduced from 100KB)
                    "metadata": {}
                },
                "expected_status": 200  # Should handle large content
            },
            {
                "name": "Special characters in user_id",
                "endpoint": "/chat",
                "method": "POST",
                "data": {
                    "user_id": "user!@#$%^&*()",
                    "message": "Test special characters"
                },
                "expected_status": 200  # Should handle special chars
            },
            {
                "name": "Unicode content",
                "endpoint": "/upload/document",
                "method": "POST",
                "data": {
                    "user_id": "unicode_user",
                    "content": "Hello 世界 🌍 مرحبا мир",
                    "metadata": {"unicode": True}
                },
                "expected_status": 200
            }
        ]
        
        edge_results = []
        
        for edge_case in edge_cases:
            try:
                url = f"{self.base_url}{edge_case['endpoint']}"
                
                if edge_case["method"] == "GET":
                    response = requests.get(url, timeout=30)
                else:
                    response = requests.post(url, json=edge_case["data"], timeout=30)
                
                success = response.status_code == edge_case["expected_status"]
                
                edge_results.append({
                    "name": edge_case["name"],
                    "success": success,
                    "actual_status": response.status_code,
                    "expected_status": edge_case["expected_status"]
                })
                
                if success:
                    print(f"✅ {edge_case['name']}: Got expected {response.status_code}")
                else:
                    print(f"❌ {edge_case['name']}: Got {response.status_code}, expected {edge_case['expected_status']}")
                    
            except Exception as e:
                edge_results.append({
                    "name": edge_case["name"],
                    "success": False,
                    "error": str(e)
                })
                print(f"❌ {edge_case['name']}: Error - {str(e)}")
        
        self.test_results.append({
            "phase": "edge_cases",
            "results": edge_results,
            "success_rate": sum(1 for r in edge_results if r.get("success", False)) / len(edge_results)
        })
    
    def test_performance_under_load(self):
        """Test performance under load"""
        print("\n📊 Phase 6: Performance and Load Testing")
        print("-" * 60)
        
        # Test different endpoints with increasing load
        load_tests = [
            {
                "endpoint": "/health",
                "method": "GET",
                "data": None,
                "iterations": 50,
                "name": "Health check load"
            },
            {
                "endpoint": "/upload/search",
                "method": "POST",
                "data": {"user_id": "load_test", "query": "test", "limit": 5},
                "iterations": 25,
                "name": "Search load"
            },
            {
                "endpoint": "/chat",
                "method": "POST",
                "data": {"user_id": "load_test", "message": "What is AI?"},
                "iterations": 10,
                "name": "Chat load"
            }
        ]
        
        load_results = []
        
        for test in load_tests:
            print(f"\nTesting: {test['name']} ({test['iterations']} iterations)")
            
            response_times = []
            errors = 0
            
            for i in range(test['iterations']):
                try:
                    start_time = time.time()
                    url = f"{self.base_url}{test['endpoint']}"
                    
                    if test["method"] == "GET":
                        response = requests.get(url, timeout=30)
                    else:
                        response = requests.post(url, json=test["data"], timeout=30)
                    
                    response_time = (time.time() - start_time) * 1000
                    response_times.append(response_time)
                    
                    if response.status_code >= 400:
                        errors += 1
                    
                    # Progress indicator
                    if (i + 1) % 10 == 0:
                        print(f"  Progress: {i + 1}/{test['iterations']}")
                        
                except Exception as e:
                    errors += 1
                    self.error_log.append({
                        "phase": "load_test",
                        "test": test["name"],
                        "error": str(e)
                    })
            
            if response_times:
                load_results.append({
                    "test": test["name"],
                    "iterations": test["iterations"],
                    "errors": errors,
                    "min_ms": round(min(response_times), 2),
                    "max_ms": round(max(response_times), 2),
                    "avg_ms": round(statistics.mean(response_times), 2),
                    "median_ms": round(statistics.median(response_times), 2),
                    "p95_ms": round(sorted(response_times)[int(len(response_times) * 0.95)], 2) if len(response_times) > 1 else response_times[0],
                    "success_rate": ((test["iterations"] - errors) / test["iterations"]) * 100
                })
                
                print(f"  ✅ Completed: Avg {statistics.mean(response_times):.2f}ms, Success rate: {((test['iterations'] - errors) / test['iterations']) * 100:.1f}%")
            else:
                print(f"  ❌ Failed: All requests errored")
        
        self.test_results.append({
            "phase": "performance_load",
            "results": load_results
        })
    
    def test_full_integration_scenarios(self):
        """Test full integration scenarios"""
        print("\n🔗 Phase 7: Full Integration Scenarios")
        print("-" * 60)
        
        scenarios = [
            {
                "name": "Research Assistant Workflow",
                "steps": [
                    ("Upload research paper", self._scenario_upload_research),
                    ("Ask questions about paper", self._scenario_ask_about_research),
                    ("Search for specific topics", self._scenario_search_topics),
                    ("Get summary", self._scenario_get_summary)
                ]
            },
            {
                "name": "Customer Support Bot",
                "steps": [
                    ("Upload FAQ documents", self._scenario_upload_faq),
                    ("Handle customer queries", self._scenario_customer_queries),
                    ("Search knowledge base", self._scenario_search_kb)
                ]
            }
        ]
        
        scenario_results = []
        
        for scenario in scenarios:
            print(f"\n🎬 Running scenario: {scenario['name']}")
            scenario_user = f"scenario_{uuid.uuid4().hex[:8]}"
            
            step_results = []
            for step_name, step_func in scenario["steps"]:
                try:
                    result = step_func(scenario_user)
                    step_results.append({
                        "step": step_name,
                        "success": result.get("success", False),
                        "details": result
                    })
                    
                    if result.get("success"):
                        print(f"  ✅ {step_name}")
                    else:
                        print(f"  ❌ {step_name}: {result.get('error', 'Failed')}")
                        
                except Exception as e:
                    step_results.append({
                        "step": step_name,
                        "success": False,
                        "error": str(e)
                    })
                    print(f"  ❌ {step_name}: {str(e)}")
            
            scenario_results.append({
                "scenario": scenario["name"],
                "user_id": scenario_user,
                "steps": step_results,
                "success_rate": sum(1 for s in step_results if s.get("success", False)) / len(step_results)
            })
        
        self.test_results.append({
            "phase": "integration_scenarios",
            "results": scenario_results
        })
    
    def _scenario_upload_research(self, user_id: str) -> Dict:
        """Upload research paper scenario"""
        try:
            research_content = """
            Title: Advances in Natural Language Processing
            
            Abstract: This paper reviews recent advances in NLP, including transformer architectures,
            large language models, and their applications in various domains.
            
            Introduction: Natural Language Processing has seen remarkable progress in recent years,
            driven by deep learning techniques and increased computational resources.
            
            Key Findings:
            1. Transformer models have revolutionized sequence processing
            2. Pre-training on large corpora enables better transfer learning
            3. Few-shot learning capabilities emerge in large models
            
            Conclusion: The future of NLP looks promising with continued research in
            efficient architectures and better understanding of language models.
            """
            
            response = requests.post(
                f"{self.base_url}/upload/document",
                json={
                    "user_id": user_id,
                    "content": research_content,
                    "metadata": {
                        "type": "research_paper",
                        "topic": "NLP",
                        "year": 2024
                    }
                },
                timeout=10
            )
            
            return {
                "success": response.status_code == 200,
                "status_code": response.status_code,
                "response": response.json() if response.status_code == 200 else None
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _scenario_ask_about_research(self, user_id: str) -> Dict:
        """Ask questions about uploaded research"""
        try:
            questions = [
                "What are the key findings in the NLP paper?",
                "What does the paper say about transformer models?",
                "Summarize the conclusion of the research"
            ]
            
            results = []
            for question in questions:
                response = requests.post(
                    f"{self.base_url}/chat",
                    json={
                        "user_id": user_id,
                        "message": question
                    },
                    timeout=30
                )
                
                results.append({
                    "question": question,
                    "success": response.status_code == 200,
                    "response": response.json().get("response", "") if response.status_code == 200 else None
                })
            
            return {
                "success": all(r["success"] for r in results),
                "questions_asked": len(questions),
                "successful_responses": sum(1 for r in results if r["success"])
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _scenario_search_topics(self, user_id: str) -> Dict:
        """Search for specific topics"""
        try:
            topics = ["transformer", "NLP", "language models", "deep learning"]
            
            search_results = []
            for topic in topics:
                response = requests.post(
                    f"{self.base_url}/upload/search",
                    json={
                        "user_id": user_id,
                        "query": topic,
                        "limit": 3
                    },
                    timeout=5
                )
                
                if response.status_code == 200:
                    results = response.json()
                    search_results.append({
                        "topic": topic,
                        "found": results.get("count", 0) > 0,
                        "count": results.get("count", 0)
                    })
            
            return {
                "success": len(search_results) == len(topics),
                "topics_searched": len(topics),
                "topics_found": sum(1 for r in search_results if r.get("found", False))
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _scenario_get_summary(self, user_id: str) -> Dict:
        """Get summary of user's documents"""
        try:
            response = requests.post(
                f"{self.base_url}/chat",
                json={
                    "user_id": user_id,
                    "message": "Summarize all the documents I've uploaded"
                },
                timeout=30
            )
            
            return {
                "success": response.status_code == 200,
                "summary_generated": response.status_code == 200,
                "response_length": len(response.json().get("response", "")) if response.status_code == 200 else 0
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _scenario_upload_faq(self, user_id: str) -> Dict:
        """Upload FAQ documents"""
        try:
            faqs = [
                {
                    "content": "Q: What are your business hours? A: We are open Monday-Friday 9AM-5PM EST.",
                    "metadata": {"category": "hours", "type": "faq"}
                },
                {
                    "content": "Q: How do I reset my password? A: Click on 'Forgot Password' on the login page and follow the instructions.",
                    "metadata": {"category": "account", "type": "faq"}
                },
                {
                    "content": "Q: What payment methods do you accept? A: We accept all major credit cards, PayPal, and bank transfers.",
                    "metadata": {"category": "payment", "type": "faq"}
                }
            ]
            
            upload_results = []
            for faq in faqs:
                response = requests.post(
                    f"{self.base_url}/upload/document",
                    json={
                        "user_id": user_id,
                        "content": faq["content"],
                        "metadata": faq["metadata"]
                    },
                    timeout=10
                )
                
                upload_results.append(response.status_code == 200)
            
            return {
                "success": all(upload_results),
                "uploaded": sum(upload_results),
                "total": len(faqs)
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _scenario_customer_queries(self, user_id: str) -> Dict:
        """Handle customer queries"""
        try:
            queries = [
                "What time do you close?",
                "I forgot my password",
                "Do you take credit cards?"
            ]
            
            query_results = []
            for query in queries:
                response = requests.post(
                    f"{self.base_url}/chat",
                    json={
                        "user_id": user_id,
                        "message": query
                    },
                    timeout=30
                )
                
                query_results.append({
                    "query": query,
                    "success": response.status_code == 200,
                    "response": response.json().get("response", "") if response.status_code == 200 else None
                })
            
            return {
                "success": all(r["success"] for r in query_results),
                "queries_handled": sum(1 for r in query_results if r["success"]),
                "total_queries": len(queries)
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _scenario_search_kb(self, user_id: str) -> Dict:
        """Search knowledge base"""
        try:
            response = requests.post(
                f"{self.base_url}/upload/search",
                json={
                    "user_id": user_id,
                    "query": "password hours payment",
                    "limit": 10
                },
                timeout=5
            )
            
            if response.status_code == 200:
                results = response.json()
                return {
                    "success": True,
                    "documents_found": results.get("count", 0),
                    "categories_covered": len(set(
                        r.get("metadata", {}).get("category", "unknown") 
                        for r in results.get("results", [])
                    ))
                }
            
            return {"success": False, "status_code": response.status_code}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def test_cleanup_and_recovery(self):
        """Test cleanup and recovery capabilities"""
        print("\n🧹 Phase 8: Cleanup and Recovery Tests")
        print("-" * 60)
        
        recovery_tests = []
        
        # Test 1: Service recovery after errors
        print("Testing service recovery after errors...")
        
        # Intentionally cause errors
        error_requests = []
        for i in range(5):
            try:
                response = requests.post(
                    f"{self.base_url}/chat",
                    json={"invalid": "data"},
                    timeout=5
                )
                error_requests.append(response.status_code)
            except:
                pass
        
        # Now test if service still works
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            recovery_tests.append({
                "test": "Service recovery after errors",
                "success": response.status_code == 200,
                "error_requests": len(error_requests),
                "recovered": response.status_code == 200
            })
            
            if response.status_code == 200:
                print("✅ Service recovered successfully after error requests")
            else:
                print("❌ Service did not recover properly")
                
        except Exception as e:
            recovery_tests.append({
                "test": "Service recovery after errors",
                "success": False,
                "error": str(e)
            })
            print(f"❌ Service recovery test failed: {str(e)}")
        
        # Test 2: Upload service health
        try:
            response = requests.get(f"{self.base_url}/upload/health", timeout=5)
            recovery_tests.append({
                "test": "Upload service health",
                "success": response.status_code == 200,
                "data": response.json() if response.status_code == 200 else None
            })
            
            if response.status_code == 200:
                print("✅ Upload service is healthy")
            else:
                print(f"❌ Upload service check failed: {response.status_code}")
                
        except Exception as e:
            recovery_tests.append({
                "test": "Upload service health",
                "success": False,
                "error": str(e)
            })
            print(f"❌ Upload service error: {str(e)}")
        
        self.test_results.append({
            "phase": "cleanup_recovery",
            "results": recovery_tests,
            "all_passed": all(r.get("success", False) for r in recovery_tests)
        })
    
    def generate_comprehensive_report(self):
        """Generate comprehensive test report"""
        if self.start_time and self.end_time:
            duration = (self.end_time - self.start_time).total_seconds()
            start_time_str = self.start_time.isoformat()
            end_time_str = self.end_time.isoformat()
        else:
            duration = 0
            start_time_str = "Unknown"
            end_time_str = "Unknown"
        
        report = {
            "test_suite": "Comprehensive Real-Life Simulation",
            "start_time": start_time_str,
            "end_time": end_time_str,
            "duration_seconds": duration,
            "phases_completed": len(self.test_results),
            "test_results": self.test_results,
            "error_log": self.error_log,
            "test_users_created": len(self.test_users),
            "performance_metrics": self._calculate_performance_metrics()
        }
        
        # Save JSON report
        with open("comprehensive_simulation_report.json", "w") as f:
            json.dump(report, f, indent=2)
        
        # Generate markdown report
        self._generate_markdown_report(report)
        
        # Print summary
        self._print_summary(report)
    
    def _calculate_performance_metrics(self) -> Dict:
        """Calculate overall performance metrics"""
        metrics = {
            "total_tests": 0,
            "successful_tests": 0,
            "failed_tests": 0,
            "phases": {}
        }
        
        for phase_result in self.test_results:
            phase_name = phase_result.get("phase", "unknown")
            
            if "results" in phase_result:
                results = phase_result["results"]
                if isinstance(results, list):
                    total = len(results)
                    successful = sum(1 for r in results if r.get("success", False) or r.get("healthy", False) or r.get("status") == "success")
                    metrics["total_tests"] += total
                    metrics["successful_tests"] += successful
                    metrics["failed_tests"] += (total - successful)
                    
                    metrics["phases"][phase_name] = {
                        "total": total,
                        "successful": successful,
                        "success_rate": (successful / total * 100) if total > 0 else 0
                    }
        
        metrics["overall_success_rate"] = (metrics["successful_tests"] / metrics["total_tests"] * 100) if metrics["total_tests"] > 0 else 0
        
        return metrics
    
    def _generate_markdown_report(self, report: Dict):
        """Generate markdown report"""
        md_content = f"""# Comprehensive Real-Life Simulation Test Report
Generated: {datetime.now().isoformat()}

## Executive Summary
- **Duration:** {report['duration_seconds']:.2f} seconds
- **Phases Completed:** {report['phases_completed']}
- **Test Users Created:** {report['test_users_created']}
- **Overall Success Rate:** {report['performance_metrics']['overall_success_rate']:.1f}%

## Phase Results

"""
        
        for phase_result in report["test_results"]:
            phase_name = phase_result.get("phase", "Unknown")
            md_content += f"### {phase_name.replace('_', ' ').title()}\n\n"
            
            if phase_name == "module_imports":
                success = sum(1 for r in phase_result["results"] if r["status"] == "success")
                total = len(phase_result["results"])
                md_content += f"- **Success Rate:** {success}/{total} ({phase_result['success_rate'] * 100:.1f}%)\n"
                md_content += "- **Modules Tested:**\n"
                for module in phase_result["results"]:
                    status = "✅" if module["status"] == "success" else "❌"
                    md_content += f"  - {status} {module['module']} - {module['description']}\n"
                    
            elif phase_name == "service_health":
                healthy = sum(1 for r in phase_result["results"] if r.get("healthy", False))
                total = len(phase_result["results"])
                md_content += f"- **Healthy Services:** {healthy}/{total}\n"
                for service in phase_result["results"]:
                    status = "✅" if service.get("healthy", False) else "❌"
                    md_content += f"  - {status} {service['endpoint']} ({service.get('response_time_ms', 'N/A')}ms)\n"
                    
            elif phase_name == "concurrent_operations":
                md_content += f"- **Total Requests:** {phase_result['total_requests']}\n"
                md_content += f"- **Successful:** {phase_result['successful']}\n"
                md_content += f"- **Duration:** {phase_result['duration_seconds']:.2f}s\n"
                md_content += f"- **Requests/Second:** {phase_result['requests_per_second']:.2f}\n"
                
            elif phase_name == "performance_load":
                md_content += "- **Load Test Results:**\n"
                for test in phase_result["results"]:
                    md_content += f"  - **{test['test']}**\n"
                    md_content += f"    - Iterations: {test['iterations']}\n"
                    md_content += f"    - Avg Response: {test['avg_ms']}ms\n"
                    md_content += f"    - P95 Response: {test['p95_ms']}ms\n"
                    md_content += f"    - Success Rate: {test['success_rate']:.1f}%\n"
            
            md_content += "\n"
        
        # Add error log if any
        if report["error_log"]:
            md_content += "## Errors Encountered\n\n"
            for error in report["error_log"][:10]:
                md_content += f"- **Phase:** {error['phase']}\n"
                md_content += f"  - **Error:** {error['error']}\n\n"
            
            if len(report["error_log"]) > 10:
                md_content += f"... and {len(report['error_log']) - 10} more errors\n"
        
        with open("COMPREHENSIVE_SIMULATION_REPORT.md", "w", encoding='utf-8') as f:
            f.write(md_content)
    
    def _print_summary(self, report: Dict):
        """Print test summary"""
        print("\n" + "=" * 80)
        print("📊 TEST SUMMARY")
        print("=" * 80)
        
        metrics = report["performance_metrics"]
        
        print(f"\n🎯 Overall Results:")
        print(f"   - Total Tests: {metrics['total_tests']}")
        print(f"   - Successful: {metrics['successful_tests']}")
        print(f"   - Failed: {metrics['failed_tests']}")
        print(f"   - Success Rate: {metrics['overall_success_rate']:.1f}%")
        
        print(f"\n⏱️  Performance:")
        print(f"   - Total Duration: {report['duration_seconds']:.2f} seconds")
        print(f"   - Test Users Created: {report['test_users_created']}")
        
        print(f"\n📋 Phase Summary:")
        for phase, data in metrics["phases"].items():
            print(f"   - {phase.replace('_', ' ').title()}: {data['successful']}/{data['total']} ({data['success_rate']:.1f}%)")
        
        if report["error_log"]:
            print(f"\n⚠️  Errors: {len(report['error_log'])} errors logged")
        
        print(f"\n📄 Reports Generated:")
        print(f"   - comprehensive_simulation_report.json")
        print(f"   - COMPREHENSIVE_SIMULATION_REPORT.md")
        
        print("\n✅ Comprehensive simulation testing completed!")


if __name__ == "__main__":
    # Run the comprehensive test suite
    tester = ComprehensiveSimulationTest()
    tester.run_all_tests()
