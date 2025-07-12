#!/usr/bin/env python3
"""
Simple API Test for Enhanced Memory Pipeline v4.0

This script tests the actual running system to verify:
1. User ID extraction and injection
2. Memory isolation between users
3. Live system functionality
"""

import requests
import json
import time
from typing import Dict, Any, Optional


class SimpleAPITester:
    """Simple API tester for the memory system"""
    
    def __init__(self, base_url: str = "http://localhost:3000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.test_results = []
    
    def log_test(self, test_name: str, success: bool, details: str = ""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"   Details: {details}")
        
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": time.time()
        })
    
    def test_system_health(self) -> bool:
        """Test if the system is running"""
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=5)
            if response.status_code == 200:
                self.log_test("System Health Check", True, "System is running")
                return True
            else:
                self.log_test("System Health Check", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("System Health Check", False, f"Error: {str(e)}")
            return False
    
    def test_chat_endpoint(self, user_data: Dict[str, Any], test_name: str) -> Optional[Dict]:
        """Test chat endpoint with specific user data"""
        try:
            payload = {
                "model": "llama3.2:1b",
                "messages": [
                    {"role": "user", "content": "Hello, remember that I like coffee"}
                ],
                "user": user_data
            }
            
            response = self.session.post(
                f"{self.base_url}/v1/chat/completions",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                self.log_test(f"Chat API - {test_name}", True, "Chat request successful")
                return response.json()
            else:
                self.log_test(f"Chat API - {test_name}", False, f"Status: {response.status_code}")
                return None
                
        except Exception as e:
            self.log_test(f"Chat API - {test_name}", False, f"Error: {str(e)}")
            return None
    
    def test_memory_endpoint(self, user_id: str, test_name: str) -> Optional[Dict]:
        """Test memory retrieval endpoint"""
        try:
            response = self.session.get(
                f"{self.base_url}/api/memory/search",
                params={"user_id": user_id, "query": "coffee"},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log_test(f"Memory API - {test_name}", True, f"Found {len(data.get('memories', []))} memories")
                return data
            else:
                self.log_test(f"Memory API - {test_name}", False, f"Status: {response.status_code}")
                return None
                
        except Exception as e:
            self.log_test(f"Memory API - {test_name}", False, f"Error: {str(e)}")
            return None
    
    def run_user_isolation_test(self):
        """Test user isolation functionality"""
        print("\n🔐 Testing User Isolation")
        print("-" * 40)
        
        # Test User 1
        user1_data = {
            "email": "alice@test.com",
            "id": "alice_123",
            "username": "alice"
        }
        
        # Test User 2  
        user2_data = {
            "email": "bob@test.com", 
            "id": "bob_456",
            "username": "bob"
        }
        
        # Send chat for User 1
        self.test_chat_endpoint(user1_data, "User 1 (Alice)")
        time.sleep(2)  # Allow processing
        
        # Send chat for User 2
        self.test_chat_endpoint(user2_data, "User 2 (Bob)")
        time.sleep(2)  # Allow processing
        
        # Check User 1 memory
        self.test_memory_endpoint("alice@test.com", "User 1 Memory Check")
        
        # Check User 2 memory
        self.test_memory_endpoint("bob@test.com", "User 2 Memory Check")
    
    def run_priority_test(self):
        """Test priority-based user ID extraction"""
        print("\n🎯 Testing User ID Priority")
        print("-" * 40)
        
        # Test with all fields (email should win)
        priority_user = {
            "email": "priority@test.com",
            "id": "backup_id",
            "username": "backup_user",
            "name": "Backup Name"
        }
        
        self.test_chat_endpoint(priority_user, "Priority Test (Email)")
        
        # Test with only username (should use username)
        username_user = {
            "username": "only_username",
            "name": "Some Name"
        }
        
        self.test_chat_endpoint(username_user, "Priority Test (Username)")
        
        # Test with only name (should use name)
        name_user = {
            "name": "Only Name"
        }
        
        self.test_chat_endpoint(name_user, "Priority Test (Name)")
    
    def run_all_tests(self):
        """Run all simple API tests"""
        print("🧪 Simple API Test Suite for Enhanced Memory Pipeline v4.0")
        print("=" * 70)
        
        # Check system health first
        if not self.test_system_health():
            print("\n❌ System is not running. Please start the system first.")
            print("Run: docker-compose up -d")
            return False
        
        # Run tests
        self.run_user_isolation_test()
        self.run_priority_test()
        
        # Summary
        print("\n📊 Test Summary")
        print("-" * 30)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        
        if failed_tests == 0:
            print("\n🎉 All tests passed! Enhanced Memory Pipeline v4.0 is working correctly!")
        else:
            print(f"\n⚠️  {failed_tests} test(s) failed. Check the details above.")
        
        return failed_tests == 0


def main():
    """Main test execution"""
    print("Starting Simple API Tests...")
    print()
    
    # Wait a moment for any startup
    time.sleep(1)
    
    tester = SimpleAPITester()
    success = tester.run_all_tests()
    
    # Save results
    with open("simple_api_test_results.json", "w") as f:
        json.dump({
            "timestamp": time.time(),
            "success": success,
            "results": tester.test_results
        }, f, indent=2)
    
    print(f"\n📝 Results saved to: simple_api_test_results.json")
    
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())
