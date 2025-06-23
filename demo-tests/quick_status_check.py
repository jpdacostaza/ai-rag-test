#!/usr/bin/env python3
"""
Quick status check for the memory recall system
"""

import requests
import json
import time

BASE_URL = "http://localhost:8001"

def test_basic_chat():
    """Test basic chat functionality"""
    print("🔍 Testing basic chat functionality...")
    
    # Test 1: Simple chat
    response = requests.post(f"{BASE_URL}/chat", json={
        "user_id": "status_test_user",
        "message": "Hello, can you help me?"
    })
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ First message response: '{result['response'][:100]}...'")
        
        # Test 2: Follow-up message
        time.sleep(2)
        response2 = requests.post(f"{BASE_URL}/chat", json={
            "user_id": "status_test_user", 
            "message": "What is my previous message about?"
        })
        
        if response2.status_code == 200:
            result2 = response2.json()
            print(f"✅ Second message response: '{result2['response'][:100]}...'")
            
            if len(result2['response'].strip()) > 0:
                print("✅ Follow-up messages working!")
                return True
            else:
                print("❌ Follow-up message returned empty response")
                return False
        else:
            print(f"❌ Second request failed: {response2.status_code}")
            return False
    else:
        print(f"❌ First request failed: {response.status_code}")
        return False

def test_tool_functionality():
    """Test tool functionality"""
    print("\n🔧 Testing tool functionality...")
    
    response = requests.post(f"{BASE_URL}/chat", json={
        "user_id": "tool_test_user",
        "message": "What time is it in Amsterdam?"
    })
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Tool response: '{result['response'][:100]}...'")
        return True
    else:
        print(f"❌ Tool test failed: {response.status_code}")
        return False

def main():
    print("🚀 QUICK STATUS CHECK")
    print("=" * 50)
    
    # Test health
    try:
        health = requests.get(f"{BASE_URL}/health/simple")
        if health.status_code == 200:
            data = health.json()
            print(f"✅ Backend healthy (uptime: {data['uptime_seconds']:.1f}s)")
        else:
            print(f"❌ Backend health check failed: {health.status_code}")
            return
    except Exception as e:
        print(f"❌ Cannot connect to backend: {e}")
        return
    
    # Run tests
    chat_working = test_basic_chat()
    tool_working = test_tool_functionality()
    
    print("\n" + "=" * 50)
    print("📊 SUMMARY:")
    print(f"- Basic chat: {'✅ WORKING' if chat_working else '❌ ISSUES'}")
    print(f"- Tool functionality: {'✅ WORKING' if tool_working else '❌ ISSUES'}")
    
    if chat_working and tool_working:
        print("🎉 All systems operational!")
    else:
        print("⚠️  Some issues detected - see details above")

if __name__ == "__main__":
    main()
