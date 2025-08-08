#!/usr/bin/env python3
"""
Install Enhanced Memory Function Filter in OpenWebUI
Fixes the pipeline vs function confusion - this installs as an OpenWebUI Function, not Pipeline
"""

import requests
import json
import os

def install_memory_function_filter():
    """Install the Enhanced Memory Function Filter in OpenWebUI"""
    print("🔧 INSTALLING ENHANCED MEMORY FUNCTION FILTER")
    print("=" * 70)
    
    # Read the function filter file
    function_file = "enhanced_memory_function_filter.py"
    
    if not os.path.exists(function_file):
        print(f"❌ Function file not found: {function_file}")
        return False
    
    with open(function_file, 'r') as f:
        function_content = f.read()
    
    print(f"📄 Function file loaded: {len(function_content)} characters")
    
    # Install in OpenWebUI Functions (not Pipelines)
    print("\n📋 INSTALLATION METHODS:")
    print("=" * 50)
    
    print("🔧 METHOD 1: Manual Installation (RECOMMENDED)")
    print("   1. Go to OpenWebUI → Settings → Functions")
    print("   2. Click 'Import Function' or '+' button")
    print("   3. Paste the following content:")
    print("   4. Save and enable the function")
    print("\n📝 FUNCTION CONTENT TO COPY:")
    print("-" * 50)
    
    # Print the function content for manual copying
    print(function_content)
    
    print("-" * 50)
    
    print("\n🔧 METHOD 2: Direct File Installation")
    print("   1. Copy enhanced_memory_function_filter.py to OpenWebUI functions directory")
    print("   2. Restart OpenWebUI")
    print("   3. Enable in Settings → Functions")
    
    print("\n📋 CONFIGURATION AFTER INSTALLATION:")
    print("=" * 50)
    print("✅ Function should appear in Settings → Functions")
    print("✅ Enable the 'Enhanced Memory Function Filter'")
    print("✅ Configure valves:")
    print("   - MEMORY_ENABLED: True")
    print("   - MEMORY_API_URL: http://localhost:5001 (or memory-api:5001)")
    print("   - DEBUG_LOGGING: True (for testing)")
    
    print("\n🧪 TESTING AFTER INSTALLATION:")
    print("=" * 50)
    print("1. Start a new conversation")
    print("2. Say: 'Hello, my name is J.P. and I work at Swift'")
    print("3. Start another new conversation")
    print("4. Ask: 'What do you know about me?'")
    print("5. The AI should remember you're J.P. from Swift")
    
    return True

def verify_memory_api():
    """Verify the memory API is accessible"""
    print("\n🔍 VERIFYING MEMORY API ACCESS")
    print("=" * 50)
    
    try:
        # Test memory API health
        response = requests.get("http://localhost:5001/health", timeout=5)
        if response.status_code == 200:
            print("✅ Memory API: ACCESSIBLE")
            
            # Check stored memories
            memory_response = requests.get("http://localhost:5001/api/memory/global_user")
            if memory_response.status_code == 200:
                memories = memory_response.json().get("memories", [])
                print(f"✅ Stored memories: {len(memories)} found")
                
                # Show sample memories
                if memories:
                    print("📝 Sample memories:")
                    for i, memory in enumerate(memories[:2], 1):
                        content = memory.get("content", "")[:60]
                        print(f"   {i}. {content}...")
            else:
                print("⚠️ Memory retrieval: Issues detected")
                
        else:
            print(f"❌ Memory API: NOT ACCESSIBLE (status: {response.status_code})")
            
    except Exception as e:
        print(f"❌ Memory API: CONNECTION FAILED - {e}")
        print("💡 Make sure memory-api container is running:")
        print("   docker ps | grep memory-api")

def explain_function_vs_pipeline():
    """Explain the difference between Functions and Pipelines"""
    print("\n📚 FUNCTIONS vs PIPELINES EXPLANATION")
    print("=" * 70)
    
    print("🔧 OpenWebUI FUNCTIONS (What we need):")
    print("   - Built-in OpenWebUI feature")
    print("   - Installed in Settings → Functions")
    print("   - Automatically applied to all conversations")
    print("   - Zero configuration required")
    print("   - inlet() and outlet() methods work reliably")
    
    print("\n🔧 OpenWebUI PIPELINES (What we had before):")
    print("   - External server on port 9099")
    print("   - Requires manual model assignment")
    print("   - Known bugs with inlet() not being called")
    print("   - More complex setup and configuration")
    
    print("\n💡 WHY FUNCTIONS ARE BETTER FOR MEMORY:")
    print("   - Reliable inlet() execution for memory retrieval")
    print("   - Automatic application to all models")
    print("   - No model-specific configuration needed")
    print("   - Simpler debugging and troubleshooting")

def main():
    """Main installation function"""
    print("🚀 ENHANCED MEMORY FUNCTION FILTER INSTALLER")
    print("=" * 70)
    
    # Verify memory API first
    verify_memory_api()
    
    # Install the function filter
    success = install_memory_function_filter()
    
    if success:
        # Explain the approach
        explain_function_vs_pipeline()
        
        print("\n" + "=" * 70)
        print("🎯 INSTALLATION COMPLETE")
        print("=" * 70)
        print("✅ Function filter code ready for installation")
        print("📋 Next steps: Copy the function content to OpenWebUI Functions")
        print("🧪 Test: Memory should work in conversations after enabling")
        
        print("\n🔧 CRITICAL DIFFERENCE:")
        print("   OLD: Pipeline on port 9099 (inlet() bug)")
        print("   NEW: Function in OpenWebUI (inlet() works)")
        
        print("\n💡 The function approach fixes the session persistence issue!")
        
    else:
        print("❌ Installation preparation failed")

if __name__ == "__main__":
    main()
