#!/usr/bin/env python3
"""
Test script to verify OpenWebUI can connect to our pipelines server
"""

import requests
import json

def test_direct_pipelines():
    """Test direct connection to pipelines server"""
    print("🔧 Testing Direct Pipelines Connection...")
    
    try:
        # Test pipelines server health
        response = requests.get("http://localhost:9098/", 
                              headers={"Authorization": "Bearer 0p3n-w3bu!"})
        print(f"✅ Pipelines Health: {response.status_code}")
        
        # Test pipelines list
        response = requests.get("http://localhost:9098/pipelines", 
                              headers={"Authorization": "Bearer 0p3n-w3bu!"})
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Pipelines Found: {len(data.get('data', []))}")
            for pipeline in data.get('data', []):
                print(f"   - {pipeline.get('name')} ({pipeline.get('type')})")
        else:
            print(f"❌ Pipelines List Error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Connection Error: {e}")

def test_openwebui_config():
    """Test OpenWebUI configuration"""
    print("\n🔧 Testing OpenWebUI Configuration...")
    
    try:
        # Test OpenWebUI health
        response = requests.get("http://localhost:3000/health")
        print(f"✅ OpenWebUI Health: {response.status_code}")
        
        # Test if we can see the pipelines endpoint
        # Note: This will require authentication in a real scenario
        
    except Exception as e:
        print(f"❌ OpenWebUI Error: {e}")

def print_manual_config_steps():
    """Print manual configuration steps"""
    print("\n📋 Manual Configuration Steps:")
    print("1. Go to http://localhost:3000")
    print("2. Log in as admin")
    print("3. Go to Settings → Admin Panel")
    print("4. Look for 'Pipelines' or 'External APIs' section")
    print("5. Add Pipeline Server:")
    print("   - URL: http://localhost:9098")
    print("   - API Key: 0p3n-w3bu!")
    print("6. Save and refresh")
    print("\n🔍 If you don't see a pipelines configuration section:")
    print("   - The OpenWebUI version might not support pipelines UI configuration")
    print("   - Environment variables should handle the configuration automatically")

if __name__ == "__main__":
    print("🧪 OpenWebUI Pipelines Connection Test")
    print("=" * 50)
    
    test_direct_pipelines()
    test_openwebui_config()
    print_manual_config_steps()
    
    print("\n🎯 Next Steps:")
    print("1. Refresh your browser at http://localhost:3000")
    print("2. Check if 'Pipelines' appears in the sidebar or settings")  
    print("3. Look for the 'Advanced Memory Pipeline' to enable")
