#!/usr/bin/env python3
"""
Test Pipeline Integration in OpenWebUI
"""
import requests
import json
import time

def test_openwebui_pipeline():
    """Test if OpenWebUI is using the memory pipeline"""
    print("🔬 Testing OpenWebUI Pipeline Integration")
    print("=" * 50)
    
    # Wait a moment for OpenWebUI to fully start
    print("⏳ Waiting for OpenWebUI to fully initialize...")
    time.sleep(5)
    
    # Test chat completion with memory context
    print("1. Testing chat completion with memory context...")
    
    # Create a chat payload that should trigger memory
    chat_payload = {
        "model": "llama3.2:3b",
        "messages": [
            {
                "role": "user", 
                "content": "Hello, what do you know about me?"
            }
        ],
        "stream": False,
        "temperature": 0.7
    }
    
    try:
        # Send request to OpenWebUI chat endpoint
        response = requests.post(
            "http://localhost:8080/api/chat/completions",
            json=chat_payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Chat completion successful")
            
            # Check if response contains memory context
            if 'choices' in result and len(result['choices']) > 0:
                content = result['choices'][0]['message']['content']
                print(f"   📝 Response: {content[:200]}...")
                
                # Check for memory indicators
                if 'J.P.' in content or 'Swift' in content:
                    print(f"   🎯 MEMORY WORKING: Pipeline integration successful!")
                    return True
                elif "don't have personal memories" in content:
                    print(f"   ❌ MEMORY NOT WORKING: Pipeline not integrated")
                    return False
                else:
                    print(f"   ⚠️ UNCLEAR: Response doesn't clearly indicate memory status")
                    return False
            else:
                print(f"   ❌ Invalid response format")
                return False
        else:
            print(f"   ❌ Chat completion failed: {response.status_code}")
            print(f"   Response: {response.text[:200]}...")
            return False
            
    except Exception as e:
        print(f"   ❌ Error testing chat: {e}")
        return False

def test_pipeline_direct():
    """Test if we can call the pipeline directly"""
    print("\n2. Testing direct pipeline access...")
    
    try:
        # Test pipeline endpoints
        response = requests.get("http://localhost:9099/", timeout=5)
        if response.status_code == 200:
            print(f"   ✅ Pipelines server accessible")
            
            # Try to get pipeline info
            try:
                pipeline_response = requests.get("http://localhost:9099/pipelines", timeout=5)
                if pipeline_response.status_code == 200:
                    print(f"   ✅ Pipeline endpoints accessible")
                    return True
                else:
                    print(f"   ⚠️ Pipeline endpoints not found")
                    return False
            except Exception as e:
                print(f"   ⚠️ Pipeline endpoint error: {e}")
                return False
        else:
            print(f"   ❌ Pipelines server not accessible")
            return False
            
    except Exception as e:
        print(f"   ❌ Error accessing pipelines: {e}")
        return False

def check_pipeline_file():
    """Check if pipeline file exists in OpenWebUI"""
    print("\n3. Checking pipeline file in OpenWebUI...")
    
    try:
        # Check if we can access the pipeline file
        import subprocess
        result = subprocess.run([
            "docker", "exec", "backend-openwebui", 
            "ls", "-la", "/app/backend/data/pipelines/"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"   ✅ Pipeline directory exists in OpenWebUI")
            if "enhanced_memory_pipeline.py" in result.stdout:
                print(f"   ✅ Memory pipeline file found")
                return True
            else:
                print(f"   ❌ Memory pipeline file not found")
                return False
        else:
            print(f"   ❌ Pipeline directory not accessible")
            return False
            
    except Exception as e:
        print(f"   ❌ Error checking pipeline file: {e}")
        return False

if __name__ == "__main__":
    print("🎯 TESTING PIPELINE INTEGRATION")
    print("=" * 50)
    
    # Run tests
    test1 = check_pipeline_file()
    test2 = test_pipeline_direct()
    test3 = test_openwebui_pipeline()
    
    print("\n🎯 RESULTS:")
    print(f"   Pipeline File Present: {'✅' if test1 else '❌'}")
    print(f"   Pipeline Server Running: {'✅' if test2 else '❌'}")
    print(f"   OpenWebUI Integration: {'✅' if test3 else '❌'}")
    
    if test1 and test2 and test3:
        print("\n🎉 ALL TESTS PASSED - PIPELINE INTEGRATION WORKING!")
    else:
        print("\n⚠️ SOME TESTS FAILED - PIPELINE INTEGRATION NEEDS ATTENTION")
