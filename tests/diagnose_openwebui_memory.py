#!/usr/bin/env python3
"""
Diagnose OpenWebUI Memory Pipeline Integration Issues
"""

import requests
import json
import time
import subprocess

def check_pipeline_status():
    """Check the status of all pipelines"""
    print("🔍 Checking Pipeline Status")
    print("=" * 40)
    
    pipeline_url = "http://localhost:9099"
    
    # Check enhanced memory pipeline valves
    try:
        response = requests.get(f"{pipeline_url}/enhanced_memory_pipeline/valves")
        if response.status_code == 200:
            valves = response.json()
            print("✅ Enhanced Memory Pipeline Valves:")
            for key, value in valves.items():
                print(f"   {key}: {value}")
        else:
            print(f"❌ Failed to get valves: {response.status_code}")
    except Exception as e:
        print(f"❌ Error checking valves: {e}")

def check_memory_api_health():
    """Check memory API health and memory count"""
    print("\n🏥 Checking Memory API Health")
    print("=" * 40)
    
    try:
        response = requests.get("http://localhost:5001/health")
        if response.status_code == 200:
            health = response.json()
            print("✅ Memory API Health:")
            for key, value in health.items():
                print(f"   {key}: {value}")
        else:
            print(f"❌ Memory API unhealthy: {response.status_code}")
    except Exception as e:
        print(f"❌ Error checking memory API: {e}")

def test_direct_pipeline_access():
    """Test direct access to the enhanced memory pipeline"""
    print("\n🧪 Testing Direct Pipeline Access")
    print("=" * 45)
    
    pipeline_url = "http://localhost:9099"
    
    # Simple test message
    test_message = {
        "user": {
            "id": "direct_test_user",
            "name": "Test User",
            "role": "user"
        },
        "messages": [
            {
                "role": "user",
                "content": "Hello, what do you know about me?"
            }
        ],
        "body": {
            "model": "qwen2.5:3b",
            "messages": [
                {
                    "role": "user",
                    "content": "Hello, what do you know about me?"
                }
            ],
            "stream": False
        }
    }
    
    try:
        response = requests.post(
            f"{pipeline_url}/enhanced_memory_pipeline/filter/inlet",
            json=test_message,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            enhanced_content = result["messages"][0]["content"]
            print(f"✅ Pipeline accessible: {len(enhanced_content)} chars response")
            
            if "Relevant Context from Memory" in enhanced_content:
                print("✅ Memory enhancement active")
            else:
                print("⚠️ No memory enhancement detected")
                
        else:
            print(f"❌ Pipeline request failed: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error testing pipeline: {e}")

def check_openwebui_pipeline_configuration():
    """Check how OpenWebUI is configured to use pipelines"""
    print("\n⚙️ Checking OpenWebUI Pipeline Configuration")
    print("=" * 55)
    
    # Check if OpenWebUI can see the enhanced memory pipeline
    try:
        # This endpoint might require authentication, but let's try
        response = requests.get("http://localhost:8080/api/v1/pipelines/list")
        if response.status_code == 200:
            pipelines = response.json()
            print(f"✅ OpenWebUI can see {len(pipelines)} pipelines")
            for pipeline in pipelines:
                print(f"   - {pipeline}")
        else:
            print(f"ℹ️ Cannot access pipeline list: {response.status_code}")
            print("   (This might be normal due to authentication)")
    except Exception as e:
        print(f"ℹ️ Cannot check OpenWebUI pipeline config: {e}")

def monitor_pipeline_logs():
    """Monitor pipeline logs for activity"""
    print("\n📊 Recent Pipeline Activity")
    print("=" * 35)
    
    try:
        # Get recent logs
        result = subprocess.run(
            ["docker", "logs", "backend-pipelines", "--tail", "10"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            logs = result.stdout.strip()
            if logs:
                print("📋 Recent pipeline logs:")
                for line in logs.split('\n')[-5:]:  # Last 5 lines
                    if line.strip():
                        print(f"   {line}")
            else:
                print("📋 No recent pipeline activity")
        else:
            print("❌ Failed to get pipeline logs")
            
    except Exception as e:
        print(f"❌ Error getting logs: {e}")

def suggest_fixes():
    """Suggest potential fixes for the memory pipeline issues"""
    print("\n🔧 POTENTIAL FIXES FOR OPENWEBUI MEMORY ISSUES")
    print("=" * 60)
    
    print("1. 📌 PIPELINE ENABLING IN OPENWEBUI:")
    print("   • Go to OpenWebUI Settings > Pipelines")
    print("   • Make sure 'Enhanced Memory Pipeline' is enabled")
    print("   • Check if it's assigned to the model you're using")
    
    print("\n2. 🔄 MODEL-SPECIFIC PIPELINE CONFIGURATION:")
    print("   • Some pipelines need to be enabled per model")
    print("   • Check model settings in OpenWebUI")
    
    print("\n3. 🧠 USER-SPECIFIC MEMORY:")
    print("   • The pipeline stores memories under 'global_user'")
    print("   • OpenWebUI might be using different user IDs")
    print("   • May need to modify pipeline to use actual user IDs")
    
    print("\n4. 🔍 SESSION PERSISTENCE:")
    print("   • Memory should persist between sessions")
    print("   • Check if OpenWebUI is starting new conversations properly")
    
    print("\n5. ⚡ IMMEDIATE TEST:")
    print("   • Try asking: 'What do you remember about me?'")
    print("   • If no response, pipeline may not be active for conversations")

def main():
    """Run comprehensive diagnosis"""
    print("🩺 OPENWEBUI MEMORY PIPELINE DIAGNOSIS")
    print("=" * 60)
    
    check_pipeline_status()
    check_memory_api_health()
    test_direct_pipeline_access()
    check_openwebui_pipeline_configuration()
    monitor_pipeline_logs()
    suggest_fixes()
    
    print("\n" + "=" * 60)
    print("✅ DIAGNOSIS COMPLETE")
    print("   Review the findings above and apply suggested fixes")

if __name__ == "__main__":
    main()
