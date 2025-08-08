#!/usr/bin/env python3
"""
Manual Function Import Test
===========================

This script attempts to manually import the memory function into OpenWebUI
since filesystem auto-loading doesn't seem to be working.
"""

import json
import httpx
import asyncio
import sys
from pathlib import Path

OPENWEBUI_URL = "http://localhost:8080"

def read_function_code():
    """Read the function code from the container."""
    import subprocess
    
    try:
        result = subprocess.run([
            "docker", "exec", "backend-openwebui", 
            "cat", "/app/backend/data/functions/enhanced_memory_function_filter.py"
        ], capture_output=True, text=True, check=True)
        
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"❌ Error reading function code: {e}")
        return None

def create_function_data(function_code):
    """Create the function data payload for import."""
    
    # Extract metadata from the function code
    lines = function_code.split('\n')
    
    # Parse the docstring metadata
    metadata = {
        "title": "Enhanced Memory Function Filter",
        "author": "AI Assistant", 
        "version": "3.0",
        "description": "Zero-configuration memory function filter that automatically enhances conversations with relevant user memories",
        "requirements": "requests"
    }
    
    for line in lines[:20]:  # Check first 20 lines for metadata
        if "title:" in line:
            metadata["title"] = line.split("title:")[1].strip()
        elif "author:" in line:
            metadata["author"] = line.split("author:")[1].strip()
        elif "version:" in line:
            metadata["version"] = line.split("version:")[1].strip()
        elif "description:" in line:
            metadata["description"] = line.split("description:")[1].strip()
    
    function_data = {
        "id": "enhanced_memory_function_filter",
        "name": metadata["title"],
        "type": "filter",
        "content": function_code,
        "meta": {
            "description": metadata["description"],
            "author": metadata["author"],
            "version": metadata["version"],
            "requirements": metadata.get("requirements", "")
        }
    }
    
    return function_data

async def test_function_import():
    """Test manual function import via API."""
    print("🔄 Testing Manual Function Import...")
    
    # Read function code
    function_code = read_function_code()
    if not function_code:
        return False
    
    print(f"📄 Function code loaded ({len(function_code)} characters)")
    
    # Create function data
    function_data = create_function_data(function_code)
    
    # Try multiple import methods
    async with httpx.AsyncClient(timeout=30.0) as client:
        
        # Method 1: POST to /api/v1/functions/
        print("\n🧪 Method 1: POST /api/v1/functions/")
        try:
            response = await client.post(
                f"{OPENWEBUI_URL}/api/v1/functions/",
                json=function_data,
                headers={"Content-Type": "application/json"}
            )
            print(f"   Status: {response.status_code}")
            if response.status_code in [200, 201]:
                print("   ✅ Success!")
                return True
            else:
                print(f"   Response: {response.text[:200]}")
        except Exception as e:
            print(f"   Error: {e}")
        
        # Method 2: POST to /api/v1/functions/import
        print("\n🧪 Method 2: POST /api/v1/functions/import")
        try:
            response = await client.post(
                f"{OPENWEBUI_URL}/api/v1/functions/import",
                json=function_data
            )
            print(f"   Status: {response.status_code}")
            if response.status_code in [200, 201]:
                print("   ✅ Success!")
                return True
            else:
                print(f"   Response: {response.text[:200]}")
        except Exception as e:
            print(f"   Error: {e}")
        
        # Method 3: Direct file import simulation
        print("\n🧪 Method 3: File-based import simulation")
        try:
            # Try to trigger a rescan or reload
            response = await client.post(
                f"{OPENWEBUI_URL}/api/v1/functions/scan",
                json={}
            )
            print(f"   Status: {response.status_code}")
            if response.status_code in [200, 201]:
                print("   ✅ Function scan triggered!")
                return True
            else:
                print(f"   Response: {response.text[:200]}")
        except Exception as e:
            print(f"   Error: {e}")
            
    return False

async def check_function_after_import():
    """Check if function is now visible in OpenWebUI."""
    print("\n🔍 Checking Function List After Import...")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(f"{OPENWEBUI_URL}/api/v1/functions/")
            print(f"Functions API Status: {response.status_code}")
            
            if response.status_code == 200:
                functions = response.json()
                print(f"Total functions: {len(functions)}")
                
                for func in functions:
                    print(f"  - {func.get('name', 'Unknown')} (ID: {func.get('id', 'Unknown')})")
                    
                return len(functions) > 0
            else:
                print(f"API Error: {response.text}")
                return False
                
        except Exception as e:
            print(f"Error: {e}")
            return False

def check_openwebui_function_configuration():
    """Check OpenWebUI's function configuration."""
    print("\n🔧 Checking OpenWebUI Function Configuration...")
    
    import subprocess
    
    try:
        # Check if OpenWebUI has function loading enabled
        result = subprocess.run([
            "docker", "exec", "backend-openwebui", 
            "find", "/app", "-name", "*.py", "-exec", "grep", "-l", "functions", "{}", ";"
        ], capture_output=True, text=True, check=True)
        
        print("Function-related files in OpenWebUI:")
        for line in result.stdout.split('\n')[:10]:  # First 10 results
            if line.strip():
                print(f"  {line}")
                
    except subprocess.CalledProcessError:
        print("Could not search for function-related files")
    
    # Check function directory permissions and contents
    try:
        result = subprocess.run([
            "docker", "exec", "backend-openwebui", 
            "ls", "-la", "/app/backend/data/"
        ], capture_output=True, text=True, check=True)
        
        print("\nBackend data directory:")
        print(result.stdout)
        
    except subprocess.CalledProcessError:
        print("Could not check backend data directory")

async def main():
    """Run manual function import test."""
    print("🔄 Manual Function Import Test")
    print("=" * 40)
    
    # Check configuration first
    check_openwebui_function_configuration()
    
    # Try manual import
    if await test_function_import():
        print("\n✅ Function import succeeded!")
    else:
        print("\n❌ Function import failed")
    
    # Check results
    if await check_function_after_import():
        print("\n🎉 Function is now visible in OpenWebUI!")
        return 0
    else:
        print("\n⚠️  Function still not visible - may need different approach")
        return 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
