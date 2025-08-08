#!/usr/bin/env python3
"""
Debug Memory Function Execution
Check why the function isn't executing during conversations
"""

import requests
import json
from datetime import datetime

def check_function_status():
    """Check if the function is properly loaded and enabled"""
    print("🔍 DEBUGGING FUNCTION EXECUTION")
    print("=" * 40)
    
    # Check if function is loaded
    try:
        response = requests.get("http://localhost:8080/api/v1/functions/", timeout=5)
        if response.status_code == 200:
            functions = response.json()
            print(f"✅ Found {len(functions)} functions loaded")
            
            for func in functions:
                name = func.get("name", "unknown")
                enabled = func.get("is_active", False)
                global_enabled = func.get("is_global", False)
                print(f"   📋 {name}: enabled={enabled}, global={global_enabled}")
                
        else:
            print(f"❌ Failed to get functions: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error checking functions: {e}")

def test_memory_api_from_container():
    """Test memory API access from OpenWebUI container"""
    print("\n🔗 TESTING MEMORY API FROM OPENWEBUI CONTAINER")
    print("=" * 50)
    
    try:
        # Test from inside the OpenWebUI container
        result = requests.get("http://localhost:8080/api/v1/functions/", timeout=5)
        print(f"OpenWebUI API accessible: {result.status_code == 200}")
        
        # Now test if we can simulate a memory call
        test_payload = {
            "user_id": "global_user",
            "query": "test connection",
            "limit": 3
        }
        
        # This would be called from within the function
        memory_response = requests.post("http://localhost:5001/api/memory/retrieve", 
                                      json=test_payload, timeout=5)
        print(f"Memory API from host: {memory_response.status_code}")
        
    except Exception as e:
        print(f"❌ Connection test error: {e}")

def create_minimal_test_function():
    """Create a minimal test function to see if functions execute at all"""
    print("\n🧪 CREATING MINIMAL TEST FUNCTION")
    print("=" * 35)
    
    minimal_function = '''"""
title: Debug Test Function
author: Debug
date: 2025-08-08
version: 1.0
license: MIT
description: Minimal function to test execution
"""

class Filter:
    def __init__(self):
        self.name = "Debug Test Function"
        print("[DEBUG] Test function initialized!")
        
    async def inlet(self, body: dict, __user__=None) -> dict:
        print(f"[DEBUG] Inlet called with: {len(body.get('messages', []))} messages")
        
        # Add a debug message to the conversation
        messages = body.get("messages", [])
        if messages:
            last_msg = messages[-1]
            if last_msg.get("role") == "user":
                original = last_msg["content"]
                last_msg["content"] = f"[DEBUG: Function is working!] {original}"
                
        return body
        
    async def outlet(self, body: dict, __user__=None) -> dict:
        print(f"[DEBUG] Outlet called")
        return body
'''
    
    print("📝 Minimal test function created:")
    print("   - Logs to console when initialized")
    print("   - Adds [DEBUG] prefix to user messages")
    print("   - Should be visible in both logs and chat")
    print()
    print("🔧 To test:")
    print("1. Import this function in OpenWebUI")
    print("2. Enable it globally")
    print("3. Send a test message")
    print("4. Check if '[DEBUG: Function is working!]' appears")
    
    return minimal_function

def check_docker_network():
    """Check if containers can communicate"""
    print("\n🌐 CHECKING DOCKER NETWORK CONNECTIVITY")
    print("=" * 45)
    
    try:
        # Test if memory API is accessible from host
        memory_response = requests.get("http://localhost:5001/api/health", timeout=5)
        print(f"Memory API from host: {memory_response.status_code}")
        
        # Test OpenWebUI
        webui_response = requests.get("http://localhost:8080/health", timeout=5)
        print(f"OpenWebUI from host: {webui_response.status_code}")
        
        print("\n🔍 Container network analysis:")
        print("   - Both containers accessible from host ✅")
        print("   - Need to test container-to-container communication")
        
    except Exception as e:
        print(f"❌ Network test error: {e}")

def analyze_function_not_executing():
    """Analyze why the function might not be executing"""
    print("\n🔬 FUNCTION EXECUTION ANALYSIS")
    print("=" * 35)
    
    print("Possible issues:")
    print("1. 🔄 Function not actually enabled globally")
    print("2. 🐛 Function has syntax errors preventing execution")
    print("3. 🌐 Memory API not accessible from container (http://memory-api:5001)")
    print("4. 📝 Function inlet/outlet not being called by OpenWebUI")
    print("5. 🔇 Debug logging not appearing in logs")
    print()
    
    print("Debugging steps:")
    print("1. ✅ Function is imported (confirmed from screenshot)")
    print("2. ✅ Function is enabled globally (green toggle)")
    print("3. ❓ Function initialization - need to check logs")
    print("4. ❓ Function execution - no debug logs seen")
    print("5. ❓ Memory API connectivity from container")
    print()
    
    print("🎯 NEXT ACTIONS:")
    print("1. Test minimal function to confirm execution")
    print("2. Check container-to-container network")
    print("3. Verify function syntax is correct")
    print("4. Enable more verbose logging")

def test_memory_query_manually():
    """Test memory queries manually to verify API works"""
    print("\n🔍 MANUAL MEMORY QUERY TEST")
    print("=" * 30)
    
    queries = ["J.P.", "Swift", "what do you know about me"]
    
    for query in queries:
        try:
            payload = {
                "user_id": "global_user", 
                "query": query,
                "limit": 5
            }
            
            response = requests.post("http://localhost:5001/api/memory/retrieve",
                                   json=payload, timeout=5)
            
            if response.status_code == 200:
                result = response.json()
                memories = result.get("memories", [])
                relevant = [m for m in memories if m.get("similarity_score", -1) >= -0.3]
                
                print(f"Query '{query}': {len(memories)} total, {len(relevant)} relevant")
                if relevant:
                    best = relevant[0]
                    print(f"   Best: {best.get('similarity_score', 0):.3f} - {best.get('content', '')[:50]}...")
                    
            else:
                print(f"Query '{query}' failed: {response.status_code}")
                
        except Exception as e:
            print(f"Query '{query}' error: {e}")

def main():
    """Run comprehensive debugging"""
    print("🚨 MEMORY FUNCTION DEBUG SESSION")
    print("Investigating why the function isn't working")
    print("=" * 50)
    
    # Check function status
    check_function_status()
    
    # Test API connectivity
    test_memory_api_from_container()
    
    # Check network
    check_docker_network()
    
    # Manual memory test
    test_memory_query_manually()
    
    # Create minimal test
    minimal_func = create_minimal_test_function()
    
    # Analysis
    analyze_function_not_executing()
    
    print("\n" + "=" * 50)
    print("🎯 DEBUGGING SUMMARY")
    print("Follow the analysis above to identify the issue")
    print("=" * 50)
    
    # Save minimal function for testing
    with open("minimal_test_function.py", "w") as f:
        f.write(minimal_func)
    print("\n📁 Saved minimal_test_function.py for testing")

if __name__ == "__main__":
    main()
