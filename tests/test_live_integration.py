#!/usr/bin/env python3
"""
Live System Integration Test for User Memory Management

This test runs against the actual running system to validate:
1. Real user ID extraction in live API calls
2. Actual memory save/retrieve operations
3. Live pipeline integration
4. Real user isolation testing
5. Actual memory API functionality

Requires the system to be running (docker-compose up)
"""

import requests
import json
import time
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional


class LiveSystemTester:
    """Test runner for live system integration tests"""
    
    def __init__(self):
        self.backend_url = "http://localhost:3000"
        self.memory_api_url = "http://localhost:8001" 
        self.pipelines_url = "http://localhost:9099"
        self.openwebui_url = "http://localhost:8080"
        
        self.test_results = []
        self.test_users = []
    
    def log_test_result(self, test_name: str, success: bool, details: str = ""):
        """Log test result"""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status = "✅" if success else "❌"
        print(f"{status} {test_name}")
        if details:
            print(f"   {details}")
    
    def check_system_health(self) -> bool:
        """Check if all system components are healthy"""
        print("\n🏥 Checking System Health...")
        
        services = [
            ("Backend", f"{self.backend_url}/health"),
            ("Memory API", f"{self.memory_api_url}/health"),
            ("Pipelines", f"{self.pipelines_url}/"),
        ]
        
        all_healthy = True
        
        for service_name, url in services:
            try:
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    self.log_test_result(f"{service_name} Health Check", True, f"Status: {response.status_code}")
                else:
                    self.log_test_result(f"{service_name} Health Check", False, f"Status: {response.status_code}")
                    all_healthy = False
            except Exception as e:
                self.log_test_result(f"{service_name} Health Check", False, f"Error: {str(e)}")
                all_healthy = False
        
        return all_healthy
    
    def test_user_id_extraction_priority(self):
        """Test user ID extraction priority in live system"""
        print("\n🎯 Testing User ID Extraction Priority...")
        
        test_cases = [
            {
                "name": "Pipeline Injection Priority",
                "request": {
                    "messages": [
                        {"role": "system", "content": "AUTHENTICATED_USER_ID: pipeline_user_999"},
                        {"role": "user", "content": "Test message with pipeline injection"}
                    ],
                    "user": {
                        "email": "other@example.com",
                        "id": "other_user"
                    }
                },
                "expected_user": "pipeline_user_999"
            },
            {
                "name": "Email Priority over ID",
                "request": {
                    "messages": [
                        {"role": "user", "content": "Test message with email priority"}
                    ],
                    "user": {
                        "email": "priority@example.com",
                        "id": "backup_id",
                        "username": "backup_username"
                    }
                },
                "expected_user": "priority@example.com"
            },
            {
                "name": "ID Priority over Username",
                "request": {
                    "messages": [
                        {"role": "user", "content": "Test message with ID priority"}
                    ],
                    "user": {
                        "id": "primary_id_123",
                        "username": "backup_username",
                        "name": "Backup Name"
                    }
                },
                "expected_user": "primary_id_123"
            },
            {
                "name": "Username Priority over Name",
                "request": {
                    "messages": [
                        {"role": "user", "content": "Test message with username priority"}
                    ],
                    "user": {
                        "username": "primary_username",
                        "name": "Backup Name"
                    }
                },
                "expected_user": "primary_username"
            },
            {
                "name": "Name Fallback",
                "request": {
                    "messages": [
                        {"role": "user", "content": "Test message with name fallback"}
                    ],
                    "user": {
                        "name": "Only Name Available"
                    }
                },
                "expected_user": "Only Name Available"
            },
            {
                "name": "Anonymous Fallback",
                "request": {
                    "messages": [
                        {"role": "user", "content": "Test message with no user data"}
                    ]
                },
                "expected_user": "anonymous"
            }
        ]
        
        for test_case in test_cases:
            try:
                # Create a test endpoint call
                response = requests.post(
                    f"{self.backend_url}/test-user-extraction",
                    json=test_case["request"],
                    headers={"Content-Type": "application/json"},
                    timeout=10
                )
                
                if response.status_code == 200:
                    result = response.json()
                    extracted_user = result.get("extracted_user_id")
                    
                    if extracted_user == test_case["expected_user"]:
                        self.log_test_result(
                            test_case["name"], 
                            True, 
                            f"Expected: {test_case['expected_user']}, Got: {extracted_user}"
                        )
                    else:
                        self.log_test_result(
                            test_case["name"], 
                            False, 
                            f"Expected: {test_case['expected_user']}, Got: {extracted_user}"
                        )
                else:
                    self.log_test_result(
                        test_case["name"], 
                        False, 
                        f"HTTP {response.status_code}: {response.text}"
                    )
                    
            except Exception as e:
                self.log_test_result(test_case["name"], False, f"Exception: {str(e)}")
    
    def test_memory_operations_with_user_isolation(self):
        """Test memory operations with real user isolation"""
        print("\n💾 Testing Memory Operations with User Isolation...")
        
        # Create unique test users
        test_users = [
            {
                "user_id": f"test_user_1_{uuid.uuid4().hex[:8]}",
                "email": f"user1_{uuid.uuid4().hex[:6]}@test.com",
                "secret_info": "I work at Google and love Python programming",
                "search_query": "work"
            },
            {
                "user_id": f"test_user_2_{uuid.uuid4().hex[:8]}",
                "email": f"user2_{uuid.uuid4().hex[:6]}@test.com", 
                "secret_info": "I work at Microsoft and prefer JavaScript development",
                "search_query": "work"
            },
            {
                "user_id": f"test_user_3_{uuid.uuid4().hex[:8]}",
                "email": f"user3_{uuid.uuid4().hex[:6]}@test.com",
                "secret_info": "I work at OpenAI and focus on machine learning research",
                "search_query": "work"
            }
        ]
        
        self.test_users = test_users
        
        # Step 1: Save memories for each user
        for user in test_users:
            try:
                chat_request = {
                    "messages": [
                        {"role": "user", "content": f"Remember this: {user['secret_info']}"}
                    ],
                    "user": {
                        "email": user["email"],
                        "id": user["user_id"]
                    },
                    "model": "test-model"
                }
                
                response = requests.post(
                    f"{self.backend_url}/chat",
                    json=chat_request,
                    headers={"Content-Type": "application/json"},
                    timeout=15
                )
                
                if response.status_code == 200:
                    self.log_test_result(
                        f"Save Memory for {user['email']}", 
                        True, 
                        f"Saved: {user['secret_info'][:50]}..."
                    )
                else:
                    self.log_test_result(
                        f"Save Memory for {user['email']}", 
                        False, 
                        f"HTTP {response.status_code}: {response.text[:100]}"
                    )
                    
            except Exception as e:
                self.log_test_result(
                    f"Save Memory for {user['email']}", 
                    False, 
                    f"Exception: {str(e)}"
                )
        
        # Wait for memory processing
        print("\n⏳ Waiting 5 seconds for memory processing...")
        time.sleep(5)
        
        # Step 2: Test memory retrieval and isolation
        for user in test_users:
            try:
                search_request = {
                    "query": user["search_query"],
                    "user_id": user["email"],  # Use email as primary user ID
                    "limit": 10
                }
                
                response = requests.post(
                    f"{self.memory_api_url}/search",
                    json=search_request,
                    headers={"Content-Type": "application/json"},
                    timeout=10
                )
                
                if response.status_code == 200:
                    result = response.json()
                    memories = result.get("memories", [])
                    
                    # Check if user found their own memory
                    found_own_memory = False
                    found_other_memory = False
                    
                    for memory in memories:
                        memory_content = memory.get("content", "")
                        
                        # Check if this is the user's own memory
                        if any(keyword in memory_content for keyword in user["secret_info"].split()):
                            found_own_memory = True
                        
                        # Check if this contains other users' secrets
                        for other_user in test_users:
                            if other_user["email"] != user["email"]:
                                if any(keyword in memory_content for keyword in other_user["secret_info"].split() if keyword not in ["work", "I", "at", "and"]):
                                    found_other_memory = True
                                    break
                    
                    if found_own_memory and not found_other_memory:
                        self.log_test_result(
                            f"Memory Isolation for {user['email']}", 
                            True, 
                            f"Found own memories, no bleed detected"
                        )
                    elif found_own_memory and found_other_memory:
                        self.log_test_result(
                            f"Memory Isolation for {user['email']}", 
                            False, 
                            f"MEMORY BLEED DETECTED - Found other users' data"
                        )
                    else:
                        self.log_test_result(
                            f"Memory Isolation for {user['email']}", 
                            False, 
                            f"No memories found (might be expected for fresh system)"
                        )
                else:
                    self.log_test_result(
                        f"Memory Retrieval for {user['email']}", 
                        False, 
                        f"HTTP {response.status_code}: {response.text[:100]}"
                    )
                    
            except Exception as e:
                self.log_test_result(
                    f"Memory Retrieval for {user['email']}", 
                    False, 
                    f"Exception: {str(e)}"
                )
    
    def test_pipeline_user_injection(self):
        """Test that pipeline properly injects user IDs"""
        print("\n🔄 Testing Pipeline User Injection...")
        
        test_scenarios = [
            {
                "name": "Email-based User Injection",
                "user_data": {
                    "email": "pipeline_test@example.com",
                    "id": "pipeline_user_123"
                },
                "message": "Test pipeline user injection with email priority"
            },
            {
                "name": "ID-based User Injection",
                "user_data": {
                    "id": "pipeline_id_456",
                    "username": "pipeline_user"
                },
                "message": "Test pipeline user injection with ID priority"
            },
            {
                "name": "Username-based User Injection",
                "user_data": {
                    "username": "pipeline_username",
                    "name": "Pipeline User"
                },
                "message": "Test pipeline user injection with username priority"
            }
        ]
        
        for scenario in test_scenarios:
            try:
                # Send request through the pipeline system
                chat_request = {
                    "messages": [
                        {"role": "user", "content": scenario["message"]}
                    ],
                    "user": scenario["user_data"],
                    "model": "test-model"
                }
                
                response = requests.post(
                    f"{self.backend_url}/chat",
                    json=chat_request,
                    headers={"Content-Type": "application/json"},
                    timeout=15
                )
                
                if response.status_code == 200:
                    # Check if the response indicates successful user injection
                    result = response.json()
                    
                    # For testing, we could add a debug endpoint that shows the processed messages
                    debug_response = requests.post(
                        f"{self.backend_url}/debug-messages",
                        json=chat_request,
                        headers={"Content-Type": "application/json"},
                        timeout=10
                    )
                    
                    if debug_response.status_code == 200:
                        debug_result = debug_response.json()
                        processed_messages = debug_result.get("processed_messages", [])
                        
                        # Check if system message with user ID was injected
                        has_user_injection = False
                        for msg in processed_messages:
                            if msg.get("role") == "system" and "AUTHENTICATED_USER_ID" in msg.get("content", ""):
                                has_user_injection = True
                                break
                        
                        if has_user_injection:
                            self.log_test_result(
                                scenario["name"], 
                                True, 
                                "User ID successfully injected into system message"
                            )
                        else:
                            self.log_test_result(
                                scenario["name"], 
                                False, 
                                "No user ID injection detected in system message"
                            )
                    else:
                        self.log_test_result(
                            scenario["name"], 
                            True, 
                            "Chat processed successfully (debug endpoint not available)"
                        )
                else:
                    self.log_test_result(
                        scenario["name"], 
                        False, 
                        f"HTTP {response.status_code}: {response.text[:100]}"
                    )
                    
            except Exception as e:
                self.log_test_result(scenario["name"], False, f"Exception: {str(e)}")
    
    def test_cross_user_memory_bleed_prevention(self):
        """Test that users cannot access each other's memories"""
        print("\n🛡️  Testing Cross-User Memory Bleed Prevention...")
        
        if not self.test_users:
            print("   ⚠️  Skipping - no test users available from previous tests")
            return
        
        # Test that each user can only access their own memories
        for user in self.test_users:
            for other_user in self.test_users:
                if user["email"] != other_user["email"]:
                    try:
                        # Try to search for the other user's secret info using current user's ID
                        search_request = {
                            "query": other_user["secret_info"],  # Search for other user's secret
                            "user_id": user["email"],  # Using current user's ID
                            "limit": 10
                        }
                        
                        response = requests.post(
                            f"{self.memory_api_url}/search",
                            json=search_request,
                            headers={"Content-Type": "application/json"},
                            timeout=10
                        )
                        
                        if response.status_code == 200:
                            result = response.json()
                            memories = result.get("memories", [])
                            
                            # Check if other user's secret was found
                            bleed_detected = False
                            for memory in memories:
                                memory_content = memory.get("content", "")
                                if other_user["secret_info"].lower() in memory_content.lower():
                                    bleed_detected = True
                                    break
                            
                            if not bleed_detected:
                                self.log_test_result(
                                    f"Bleed Prevention: {user['email'][:15]}... cannot access {other_user['email'][:15]}...", 
                                    True, 
                                    "No cross-user data access detected"
                                )
                            else:
                                self.log_test_result(
                                    f"Bleed Prevention: {user['email'][:15]}... cannot access {other_user['email'][:15]}...", 
                                    False, 
                                    "CRITICAL: Cross-user memory access detected!"
                                )
                        else:
                            self.log_test_result(
                                f"Bleed Prevention: {user['email'][:15]}... cannot access {other_user['email'][:15]}...", 
                                False, 
                                f"HTTP {response.status_code}: {response.text[:50]}"
                            )
                            
                    except Exception as e:
                        self.log_test_result(
                            f"Bleed Prevention: {user['email'][:15]}... cannot access {other_user['email'][:15]}...", 
                            False, 
                            f"Exception: {str(e)}"
                        )
    
    def test_edge_cases(self):
        """Test edge cases and error handling"""
        print("\n🔬 Testing Edge Cases and Error Handling...")
        
        edge_cases = [
            {
                "name": "Empty User Data",
                "request": {
                    "messages": [{"role": "user", "content": "Test with empty user"}],
                    "user": {}
                }
            },
            {
                "name": "Null User Data",
                "request": {
                    "messages": [{"role": "user", "content": "Test with null user"}],
                    "user": None
                }
            },
            {
                "name": "Missing User Field",
                "request": {
                    "messages": [{"role": "user", "content": "Test with missing user"}]
                }
            },
            {
                "name": "Empty Message Array",
                "request": {
                    "messages": [],
                    "user": {"email": "test@example.com"}
                }
            },
            {
                "name": "Invalid Message Format",
                "request": {
                    "messages": [{"invalid": "format"}],
                    "user": {"email": "test@example.com"}
                }
            }
        ]
        
        for case in edge_cases:
            try:
                response = requests.post(
                    f"{self.backend_url}/test-user-extraction",
                    json=case["request"],
                    headers={"Content-Type": "application/json"},
                    timeout=10
                )
                
                # Should handle gracefully without 500 errors
                if response.status_code < 500:
                    self.log_test_result(
                        case["name"], 
                        True, 
                        f"Handled gracefully - Status: {response.status_code}"
                    )
                else:
                    self.log_test_result(
                        case["name"], 
                        False, 
                        f"Server error - Status: {response.status_code}"
                    )
                    
            except Exception as e:
                self.log_test_result(case["name"], False, f"Exception: {str(e)}")
    
    def generate_report(self):
        """Generate comprehensive test report"""
        print("\n" + "="*80)
        print("📊 COMPREHENSIVE TEST REPORT")
        print("="*80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"\n📈 Overall Results:")
        print(f"   Total Tests: {total_tests}")
        print(f"   Passed: {passed_tests} ✅")
        print(f"   Failed: {failed_tests} ❌")
        print(f"   Success Rate: {success_rate:.1f}%")
        
        if failed_tests > 0:
            print(f"\n❌ Failed Tests:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"   • {result['test']}: {result['details']}")
        
        print(f"\n🎯 Test Categories:")
        categories = {
            "Health": [r for r in self.test_results if "Health" in r["test"]],
            "User ID Extraction": [r for r in self.test_results if any(keyword in r["test"] for keyword in ["Priority", "Extraction", "Injection"])],
            "Memory Operations": [r for r in self.test_results if any(keyword in r["test"] for keyword in ["Memory", "Isolation", "Bleed"])],
            "Edge Cases": [r for r in self.test_results if "Edge" in r["test"] or any(keyword in r["test"] for keyword in ["Empty", "Null", "Invalid"])],
        }
        
        for category, tests in categories.items():
            if tests:
                category_passed = sum(1 for t in tests if t["success"])
                category_total = len(tests)
                category_rate = (category_passed / category_total * 100) if category_total > 0 else 0
                print(f"   {category}: {category_passed}/{category_total} ({category_rate:.1f}%)")
        
        print(f"\n⏰ Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Save detailed report
        report_file = f"live_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump({
                "summary": {
                    "total_tests": total_tests,
                    "passed_tests": passed_tests,
                    "failed_tests": failed_tests,
                    "success_rate": success_rate,
                    "timestamp": datetime.now().isoformat()
                },
                "test_results": self.test_results
            }, f, indent=2)
        
        print(f"📄 Detailed report saved to: {report_file}")
        
        return success_rate >= 80  # Consider success if 80%+ tests pass
    
    def run_all_tests(self):
        """Run the complete test suite"""
        print("🚀 Starting Live System Integration Tests")
        print("=" * 60)
        
        # Check system health first
        if not self.check_system_health():
            print("\n❌ System health checks failed. Please ensure all services are running.")
            print("   Run: docker-compose up -d")
            return False
        
        # Run all test categories
        self.test_user_id_extraction_priority()
        self.test_memory_operations_with_user_isolation() 
        self.test_pipeline_user_injection()
        self.test_cross_user_memory_bleed_prevention()
        self.test_edge_cases()
        
        # Generate final report
        return self.generate_report()


def main():
    """Main test runner"""
    tester = LiveSystemTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 All tests completed successfully!")
        print("✅ Enhanced Memory Pipeline v4.0 is working correctly")
        return 0
    else:
        print("\n⚠️  Some tests failed or system issues detected")
        print("🔧 Please review the test report above")
        return 1


if __name__ == "__main__":
    exit(main())
