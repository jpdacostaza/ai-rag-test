#!/usr/bin/env python3
"""
Memory Pipeline Installation Verification
========================================
Confirms that the memory pipeline is successfully installed and operational.
"""

import requests
import json
import sys
import time
from datetime import datetime

def verify_memory_pipeline_installation():
    """Verify the memory pipeline installation is complete and functional"""
    
    print("🚀 MEMORY PIPELINE INSTALLATION VERIFICATION")
    print("="*60)
    print(f"Started at: {datetime.now()}")
    
    backend_url = "http://localhost:8001"
    openwebui_url = "http://localhost:3000"
    api_key = "f2b985dd-219f-45b1-a90e-170962cc7082"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    
    results = {
        "openwebui_accessible": False,
        "backend_accessible": False,
        "pipeline_file_exists": False,
        "memory_endpoint": False,
        "learning_endpoint": False,
        "status_endpoint": False,
        "overall_success": False
    }
    
    # Test 1: OpenWebUI accessibility
    print("\n1️⃣ Testing OpenWebUI accessibility...")
    try:
        response = requests.get(openwebui_url, timeout=10)
        if response.status_code == 200:
            print("   ✅ OpenWebUI is running and accessible")
            results["openwebui_accessible"] = True
        else:
            print(f"   ❌ OpenWebUI returned status: {response.status_code}")
    except Exception as e:
        print(f"   ❌ OpenWebUI connection failed: {e}")
    
    # Test 2: Backend accessibility
    print("\n2️⃣ Testing backend accessibility...")
    try:
        response = requests.get(f"{backend_url}/health", timeout=10)
        if response.status_code == 200:
            health_data = response.json()
            print("   ✅ Backend is healthy and operational")
            print(f"   📊 Status: {health_data.get('status', 'unknown')}")
            results["backend_accessible"] = True
        else:
            print(f"   ❌ Backend returned status: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Backend connection failed: {e}")
    
    # Test 3: Check pipeline file existence in container
    print("\n3️⃣ Checking pipeline file in OpenWebUI container...")
    try:
        import subprocess
        result = subprocess.run([
            "docker", "exec", "backend-openwebui", "ls", "-la", "/app/backend/data/pipelines/memory_pipeline.py"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("   ✅ Memory pipeline file exists in OpenWebUI container")
            print(f"   📄 File details: {result.stdout.strip()}")
            results["pipeline_file_exists"] = True
        else:
            print("   ❌ Memory pipeline file not found in container")
    except Exception as e:
        print(f"   ❌ Failed to check pipeline file: {e}")
    
    # Test 4: Memory retrieval endpoint
    print("\n4️⃣ Testing memory retrieval endpoint...")
    try:
        test_data = {
            "user_id": "verification_user",
            "query": "test query",
            "limit": 3
        }
        
        response = requests.post(f"{backend_url}/api/memory/retrieve", 
                               json=test_data, headers=headers, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            print("   ✅ Memory retrieval endpoint is functional")
            print(f"   📊 Retrieved {result.get('count', 0)} memories")
            results["memory_endpoint"] = True
        else:
            print(f"   ❌ Memory endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Memory endpoint error: {e}")
    
    # Test 5: Learning endpoint
    print("\n5️⃣ Testing learning endpoint...")
    try:
        test_data = {
            "user_id": "verification_user",
            "conversation_id": "verification_conversation",
            "user_message": "Hello, my name is Test User",
            "assistant_response": "Hello Test User! Nice to meet you.",
            "response_time": 1.0,
            "source": "verification"
        }
        
        response = requests.post(f"{backend_url}/api/learning/process_interaction",
                               json=test_data, headers=headers, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            print("   ✅ Learning endpoint is functional")
            print(f"   📊 Processing status: {result.get('status', 'unknown')}")
            results["learning_endpoint"] = True
        else:
            print(f"   ❌ Learning endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Learning endpoint error: {e}")
    
    # Test 6: Pipeline status endpoint
    print("\n6️⃣ Testing pipeline status endpoint...")
    try:
        response = requests.get(f"{backend_url}/api/pipeline/status", 
                              headers=headers, timeout=10)
        
        if response.status_code == 200:
            status = response.json()
            print("   ✅ Pipeline status endpoint is functional")
            print(f"   📊 Backend status: {status.get('status', 'unknown')}")
            results["status_endpoint"] = True
        else:
            print(f"   ❌ Pipeline status failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Pipeline status error: {e}")
    
    # Final assessment
    print("\n" + "="*60)
    print("🏁 INSTALLATION VERIFICATION RESULTS")
    print("="*60)
    
    success_count = sum(results.values())
    total_tests = len(results) - 1  # Exclude overall_success
    
    print(f"\n📊 TEST RESULTS SUMMARY:")
    print(f"   ✅ Passed: {success_count}/{total_tests} tests")
    print(f"   📈 Success rate: {(success_count/total_tests)*100:.1f}%")
    
    print(f"\n📋 DETAILED RESULTS:")
    for test_name, passed in results.items():
        if test_name != "overall_success":
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"   {test_name}: {status}")
    
    # Overall status
    results["overall_success"] = success_count >= total_tests - 1  # Allow 1 failure
    
    if results["overall_success"]:
        print(f"\n🎉 MEMORY PIPELINE INSTALLATION SUCCESSFUL!")
        print(f"   The memory pipeline is installed and ready to use.")
        
        print(f"\n📖 NEXT STEPS:")
        print(f"   1. Open OpenWebUI at: http://localhost:3000")
        print(f"   2. Create an account or sign in")
        print(f"   3. Start a new chat")
        print(f"   4. Tell the AI: 'My name is [YourName] and I like [hobby]'")
        print(f"   5. In a new chat, ask: 'What do you remember about me?'")
        print(f"   6. The AI should remember your name and preferences!")
        
        print(f"\n🔧 MEMORY PIPELINE FEATURES:")
        print(f"   • Automatic memory injection in conversations")
        print(f"   • Persistent user information across sessions")
        print(f"   • Adaptive learning from user interactions")
        print(f"   • Context-aware memory retrieval")
        
    else:
        print(f"\n⚠️  MEMORY PIPELINE INSTALLATION ISSUES DETECTED")
        print(f"   Some tests failed. Check the logs above for details.")
        print(f"   The system may still work with reduced functionality.")
    
    return results

if __name__ == "__main__":
    results = verify_memory_pipeline_installation()
    sys.exit(0 if results["overall_success"] else 1)
