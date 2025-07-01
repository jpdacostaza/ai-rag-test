#!/usr/bin/env python3
"""
Script to import the memory function into OpenWebUI via API
"""

import requests
import json

# Read the memory function code
with open('storage/openwebui/memory_function_code.py', 'r') as f:
    function_code = f.read()

# OpenWebUI API endpoint
OPENWEBUI_URL = "http://localhost:3000"

# Function metadata
function_data = {
    "id": "memory_function",
    "name": "Memory Function",
    "content": function_code,
    "type": "function"
}

def import_function():
    """Import the memory function via OpenWebUI API"""
    try:
        # Try to import the function
        response = requests.post(
            f"{OPENWEBUI_URL}/api/v1/functions/import",
            json=function_data
        )
        
        if response.status_code == 200:
            print("✅ Memory function imported successfully!")
            return True
        else:
            print(f"❌ Failed to import function: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error importing function: {e}")
        return False

def list_functions():
    """List all available functions"""
    try:
        response = requests.get(f"{OPENWEBUI_URL}/api/v1/functions/")
        if response.status_code == 200:
            functions = response.json()
            print(f"📋 Available functions: {len(functions)}")
            for func in functions:
                print(f"  - {func.get('name', 'Unknown')} ({func.get('id', 'no-id')})")
        else:
            print(f"❌ Failed to list functions: {response.status_code}")
    except Exception as e:
        print(f"❌ Error listing functions: {e}")

def main():
    print("🔧 Importing Memory Function into OpenWebUI")
    print("=" * 50)
    
    # List existing functions
    print("📋 Checking existing functions...")
    list_functions()
    
    # Import the memory function
    print("\n🚀 Importing memory function...")
    if import_function():
        print("\n📋 Updated function list:")
        list_functions()
    else:
        print("\n❌ Function import failed!")

if __name__ == "__main__":
    main()
