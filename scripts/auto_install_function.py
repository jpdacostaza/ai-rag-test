#!/usr/bin/env python3
"""
Automatic Memory Function Installer for OpenWebUI
================================================

This script automatically installs the memory function into OpenWebUI
via the admin API.
"""

import time
import json
import httpx
from pathlib import Path

OPENWEBUI_URL = "http://localhost:8080"
MEMORY_FUNCTION_PATH = "memory_function.py"
MAX_RETRIES = 30
RETRY_DELAY = 10


def wait_for_openwebui():
    """Wait for OpenWebUI to be ready."""
    print("🔍 Waiting for OpenWebUI to be ready...")
    
    for attempt in range(MAX_RETRIES):
        try:
            with httpx.Client(timeout=5.0) as client:
                response = client.get(f"{OPENWEBUI_URL}/health")
                if response.status_code == 200:
                    print("✅ OpenWebUI is ready!")
                    return True
        except Exception as e:
            print(f"⏳ Attempt {attempt + 1}/{MAX_RETRIES} - OpenWebUI not ready yet: {e}")
            time.sleep(RETRY_DELAY)
    
    print("❌ OpenWebUI failed to become ready within timeout")
    return False


def load_memory_function():
    """Load the memory function code."""
    try:
        memory_function_path = Path(MEMORY_FUNCTION_PATH)
        if memory_function_path.exists():
            with open(memory_function_path, 'r', encoding='utf-8') as f:
                return f.read()
        else:
            # Fallback to the filter function
            filter_path = Path("memory/functions/memory_filter.py")
            if filter_path.exists():
                with open(filter_path, 'r', encoding='utf-8') as f:
                    return f.read()
            else:
                print("❌ No memory function file found")
                return None
    except Exception as e:
        print(f"❌ Error loading memory function: {e}")
        return None


def install_function():
    """Install the memory function via OpenWebUI API."""
    function_code = load_memory_function()
    if not function_code:
        return False
    
    function_data = {
        "id": "enhanced_memory_function",
        "name": "Enhanced Memory Function",
        "type": "filter",
        "content": function_code,
        "meta": {
            "description": "Stores and retrieves conversation context using the backend memory API",
            "author": "AI Backend System",
            "version": "2.0.0"
        }
    }
    
    try:
        print("🚀 Installing memory function...")
        
        with httpx.Client(timeout=30.0) as client:
            # Try the functions API endpoint
            response = client.post(
                f"{OPENWEBUI_URL}/api/v1/functions/",
                json=function_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code in [200, 201]:
                print("✅ Memory function installed successfully!")
                return True
            else:
                print(f"❌ Failed to install function: {response.status_code}")
                print(f"Response: {response.text}")
                
                # Try alternative endpoint
                response = client.post(
                    f"{OPENWEBUI_URL}/api/v1/functions/import",
                    json=function_data
                )
                
                if response.status_code in [200, 201]:
                    print("✅ Memory function installed via import endpoint!")
                    return True
                else:
                    print(f"❌ Alternative endpoint also failed: {response.status_code}")
                    return False
                
    except Exception as e:
        print(f"❌ Error installing function: {e}")
        return False


def main():
    """Main installation process."""
    print("🎯 Enhanced Memory Function Auto-Installer")
    print("=" * 50)
    
    # Wait for OpenWebUI
    if not wait_for_openwebui():
        exit(1)
    
    # Install function
    if install_function():
        print("\n🎉 Installation completed successfully!")
        print("💡 The Enhanced Memory Function is now available in OpenWebUI")
        print("📋 Go to Admin → Functions to configure it")
    else:
        print("\n❌ Installation failed")
        print("💡 You may need to install the function manually")
        exit(1)


if __name__ == "__main__":
    main()
