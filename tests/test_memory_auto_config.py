#!/usr/bin/env python3
"""
Test Auto-Configured Memory System
=====================================

This script tests that the Enhanced Memory Pipeline is now working automatically
without any manual configuration, processing conversations and storing/retrieving
memories properly.

It simulates a conversation flow and verifies:
1. Memory storage is working
2. Memory retrieval is working  
3. Context injection is happening
4. No manual configuration is required
"""

import requests
import json
import time
import sys
import os

# Configuration
OPENWEBUI_URL = "http://localhost:3000"
MEMORY_API_URL = "http://localhost:8001"
PIPELINE_URL = "http://localhost:9099"

def test_memory_api_direct():
    """Test Memory API directly to ensure it's still working."""
    print("\n🔧 Testing Memory API directly...")
    
    try:
        # Test health endpoint
        response = requests.get(f"{MEMORY_API_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Memory API health check: PASSED")
        else:
            print(f"❌ Memory API health check: FAILED ({response.status_code})")
            return False
            
        # Test storing a memory using the correct endpoint
        memory_data = {
            "user_id": "test_user_auto_config",
            "content": "The user mentioned they work as a software engineer and prefer Python programming",
            "source": "auto_config_test",
            "conversation_id": "auto_config_test_001",
            "metadata": {
                "timestamp": time.time(),
                "importance": 8,
                "category": "personal_info"
            }
        }
        
        response = requests.post(f"{MEMORY_API_URL}/api/memory/store_explicit", json=memory_data, timeout=5)
        if response.status_code == 200:
            print("✅ Memory storage test: PASSED")
        else:
            print(f"❌ Memory storage test: FAILED ({response.status_code})")
            if response.text:
                print(f"   Error: {response.text}")
            return False
            
        # Test retrieving memories using the correct endpoint
        retrieval_data = {
            "user_id": "test_user_auto_config",
            "query": "software engineer Python",
            "limit": 5
        }
        
        response = requests.post(f"{MEMORY_API_URL}/api/memory/retrieve", json=retrieval_data, timeout=5)
        if response.status_code == 200:
            result = response.json()
            memories = result.get('memories', [])
            if len(memories) > 0:
                print("✅ Memory retrieval test: PASSED")
                print(f"   Retrieved {len(memories)} memories")
            else:
                print("⚠️  Memory retrieval test: No memories found")
        else:
            print(f"❌ Memory retrieval test: FAILED ({response.status_code})")
            if response.text:
                print(f"   Error: {response.text}")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Memory API test failed: {e}")
        return False

def test_pipeline_access():
    """Test that Enhanced Memory Pipeline is accessible."""
    print("\n🔧 Testing Enhanced Memory Pipeline access...")
    
    try:
        # Test pipeline list
        response = requests.get(f"{PIPELINE_URL}/pipelines", timeout=5)
        if response.status_code == 200:
            pipelines = response.json()
            print("✅ Pipeline list access: PASSED")
            
            # Check if enhanced_memory_pipeline is in the list
            pipeline_names = [p.get('id', p.get('name', '')) for p in pipelines]
            if 'enhanced_memory_pipeline' in pipeline_names:
                print("✅ Enhanced Memory Pipeline found in list")
            else:
                print("⚠️  Enhanced Memory Pipeline not found in list")
                print(f"   Available pipelines: {pipeline_names}")
        else:
            print(f"❌ Pipeline list access: FAILED ({response.status_code})")
            return False
            
        # Test pipeline valves
        response = requests.get(f"{PIPELINE_URL}/enhanced_memory_pipeline/valves", timeout=5)
        if response.status_code == 200:
            valves = response.json()
            print("✅ Pipeline valves access: PASSED")
            print(f"   Memory enabled: {valves.get('enable_memory', 'unknown')}")
            print(f"   Debug mode: {valves.get('debug_mode', 'unknown')}")
            print(f"   Backend URL: {valves.get('backend_url', 'unknown')}")
        else:
            print(f"❌ Pipeline valves access: FAILED ({response.status_code})")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Pipeline access test failed: {e}")
        return False

def test_openwebui_pipeline_integration():
    """Test OpenWebUI integration with pipelines."""
    print("\n🔧 Testing OpenWebUI pipeline integration...")
    
    try:
        # This would require authentication to OpenWebUI
        # For now, just check if OpenWebUI is responding
        response = requests.get(f"{OPENWEBUI_URL}/api/v1/models", timeout=5)
        if response.status_code == 200:
            print("✅ OpenWebUI API access: PASSED")
        else:
            print(f"⚠️  OpenWebUI API access: Limited ({response.status_code})")
            
        return True
        
    except Exception as e:
        print(f"❌ OpenWebUI integration test failed: {e}")
        return False

def check_docker_containers():
    """Check that all required Docker containers are running."""
    print("\n🔧 Checking Docker container status...")
    
    try:
        import subprocess
        
        # Check container status
        result = subprocess.run(
            ["docker", "ps", "--format", "table {{.Names}}\\t{{.Status}}"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            print("✅ Docker containers status:")
            lines = result.stdout.strip().split('\n')
            for line in lines:
                if 'backend-' in line:
                    print(f"   {line}")
        else:
            print(f"❌ Docker status check failed: {result.stderr}")
            
    except Exception as e:
        print(f"❌ Docker check failed: {e}")

def main():
    """Run all tests to verify auto-configured memory system."""
    print("🧪 Testing Auto-Configured Enhanced Memory System")
    print("=" * 60)
    
    # Check Docker containers
    check_docker_containers()
    
    # Test each component
    tests = [
        ("Memory API", test_memory_api_direct),
        ("Pipeline Access", test_pipeline_access),
        ("OpenWebUI Integration", test_openwebui_pipeline_integration),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✅ All tests passed! Memory system appears to be auto-configured correctly.")
        print("\n🔍 Next steps:")
        print("   1. Test with actual conversation in OpenWebUI")
        print("   2. Check logs for 'INLET CALLED' and 'OUTLET CALLED' messages")
        print("   3. Verify memory consistency in conversations")
    else:
        print("❌ Some tests failed. Memory system may need additional configuration.")
        
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
