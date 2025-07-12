#!/usr/bin/env python3
"""
Test script to verify user ID extraction from Enhanced Memory Pipeline
"""
import requests
import json
import sys

# Test data simulating an OpenWebUI request
test_data = {
    "model": "llama3.2:3b",
    "messages": [
        {
            "role": "user",
            "content": "Hello, my name is John Doe and I work as a software engineer"
        }
    ],
    "stream": False
}

# Test with different user scenarios
test_users = [
    {
        "name": "UUID User",
        "user": {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "email": "john.doe@example.com",
            "username": "johndoe",
            "name": "John Doe"
        }
    },
    {
        "name": "Email User", 
        "user": {
            "email": "jane.smith@company.net",
            "username": "janesmith",
            "name": "Jane Smith"
        }
    },
    {
        "name": "Username User",
        "user": {
            "username": "testuser123",
            "name": "Test User"
        }
    }
]

def test_user_extraction(user_data):
    """Test user ID extraction with different user data"""
    print(f"\n=== Testing: {user_data['name']} ===")
    
    # Add user to test data
    test_payload = test_data.copy()
    test_payload["user"] = user_data["user"]
    
    print(f"User object: {json.dumps(user_data['user'], indent=2)}")
    
    try:
        # Send request to backend
        response = requests.post(
            "http://localhost:3000/v1/chat/completions",
            json=test_payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Request successful")
            print(f"Response: {result.get('choices', [{}])[0].get('message', {}).get('content', 'No content')[:100]}...")
        else:
            print(f"❌ Request failed: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Connection error: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("🧪 Testing Enhanced Memory Pipeline User ID Extraction")
    print("=" * 60)
    
    # Test each user scenario
    for user_data in test_users:
        test_user_extraction(user_data)
    
    print("\n" + "=" * 60)
    print("✅ User ID extraction testing complete")
