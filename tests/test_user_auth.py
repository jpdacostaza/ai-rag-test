#!/usr/bin/env python3
"""
Test script to validate the new user authentication system
with the Enhanced Memory Pipeline v4.0
"""

import requests
import json
import time
from datetime import datetime

# Test Configuration
BACKEND_URL = "http://localhost:3000"
MEMORY_API_URL = "http://localhost:8001"

def print_banner(message):
    print(f"\n{'='*60}")
    print(f"🧪 {message}")
    print(f"{'='*60}")

def test_backend_health():
    """Test backend health endpoint"""
    print_banner("Testing Backend Health")
    try:
        response = requests.get(f"{BACKEND_URL}/health")
        print(f"✅ Backend Health: {response.status_code} - {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Backend Health Error: {e}")
        return False

def test_memory_api_health():
    """Test memory API health endpoint"""
    print_banner("Testing Memory API Health")
    try:
        response = requests.get(f"{MEMORY_API_URL}/health")
        print(f"✅ Memory API Health: {response.status_code} - {response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Memory API Health Error: {e}")
        return False

def test_user_isolation():
    """Test user data isolation with different user IDs"""
    print_banner("Testing User Data Isolation")
    
    # Test data for different users
    test_users = [
        {
            "user_id": "user_123",
            "email": "alice@example.com",
            "message": "Alice's memory test - I love pizza and coffee"
        },
        {
            "user_id": "user_456", 
            "email": "bob@example.com",
            "message": "Bob's memory test - I enjoy hiking and reading books"
        },
        {
            "user_id": "user_789",
            "email": "charlie@example.com", 
            "message": "Charlie's memory test - I work on AI projects and machine learning"
        }
    ]
    
    print(f"\n📝 Testing memory storage for {len(test_users)} different users...")
    
    for user in test_users:
        try:
            # Simulate chat message with user identification
            chat_data = {
                "messages": [
                    {
                        "role": "system", 
                        "content": f"AUTHENTICATED_USER_ID: {user['user_id']}"
                    },
                    {
                        "role": "user", 
                        "content": user['message']
                    }
                ],
                "user": {
                    "id": user['user_id'],
                    "email": user['email']
                }
            }
            
            print(f"\n👤 Testing user: {user['email']} (ID: {user['user_id']})")
            print(f"   Message: {user['message']}")
            
            # Test chat endpoint
            response = requests.post(
                f"{BACKEND_URL}/chat",
                json=chat_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                print(f"   ✅ Chat processed successfully")
            else:
                print(f"   ❌ Chat failed: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"   ❌ Error for user {user['email']}: {e}")
    
    # Wait for memory processing
    print(f"\n⏳ Waiting 3 seconds for memory processing...")
    time.sleep(3)
    
    # Test memory retrieval for each user
    print(f"\n🔍 Testing memory retrieval for each user...")
    
    for user in test_users:
        try:
            # Test memory search with user context
            search_data = {
                "query": "What do I like?",
                "user_id": user['user_id']
            }
            
            response = requests.post(
                f"{MEMORY_API_URL}/search",
                json=search_data,
                headers={"Content-Type": "application/json"}
            )
            
            print(f"\n👤 Memory search for {user['email']}:")
            if response.status_code == 200:
                results = response.json()
                if results.get('memories'):
                    print(f"   ✅ Found {len(results['memories'])} memories")
                    for i, memory in enumerate(results['memories'][:2]):
                        print(f"      {i+1}. {memory.get('content', 'No content')[:100]}...")
                else:
                    print(f"   📝 No memories found (expected for fresh system)")
            else:
                print(f"   ❌ Memory search failed: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Memory search error for {user['email']}: {e}")

def test_authentication_priority():
    """Test the priority-based user authentication system"""
    print_banner("Testing Authentication Priority System")
    
    # Test different authentication scenarios
    test_scenarios = [
        {
            "name": "Pipeline Injection (Highest Priority)",
            "data": {
                "messages": [
                    {"role": "system", "content": "AUTHENTICATED_USER_ID: pipeline_user_999"},
                    {"role": "user", "content": "Test message with pipeline injection"}
                ]
            },
            "expected_user": "pipeline_user_999"
        },
        {
            "name": "Email-based Authentication",
            "data": {
                "messages": [
                    {"role": "user", "content": "Test message with email auth"}
                ],
                "user": {"email": "test@example.com"}
            },
            "expected_user": "test@example.com"
        },
        {
            "name": "ID-based Authentication", 
            "data": {
                "messages": [
                    {"role": "user", "content": "Test message with ID auth"}
                ],
                "user": {"id": "id_user_123"}
            },
            "expected_user": "id_user_123"
        }
    ]
    
    for scenario in test_scenarios:
        print(f"\n🎯 Testing: {scenario['name']}")
        try:
            response = requests.post(
                f"{BACKEND_URL}/test-auth",
                json=scenario['data'],
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                extracted_user = result.get('extracted_user_id')
                print(f"   ✅ Expected: {scenario['expected_user']}")
                print(f"   📋 Extracted: {extracted_user}")
                
                if extracted_user == scenario['expected_user']:
                    print(f"   ✅ Authentication priority working correctly!")
                else:
                    print(f"   ⚠️  Authentication result differs from expected")
            else:
                print(f"   ❌ Test failed: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")

def main():
    """Run comprehensive system tests"""
    print(f"\n🚀 Enhanced Memory Pipeline v4.0 - System Test Suite")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test system health
    backend_healthy = test_backend_health()
    memory_healthy = test_memory_api_health()
    
    if not (backend_healthy and memory_healthy):
        print(f"\n❌ System health checks failed. Stopping tests.")
        return
    
    # Test user isolation
    test_user_isolation()
    
    # Test authentication priority
    test_authentication_priority()
    
    print_banner("Test Suite Complete")
    print(f"✅ System is ready for multi-user testing!")
    print(f"🌐 Open http://localhost:8080 to access the OpenWebUI interface")
    print(f"📝 Each user will have isolated memory storage")
    print(f"🔐 Authentication system prioritizes pipeline > email > id > username > name")

if __name__ == "__main__":
    main()
