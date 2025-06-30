#!/usr/bin/env python3
"""
Install Memory Function into OpenWebUI
=====================================

This script installs the memory function into OpenWebUI by uploading the function code
and configuring it properly.
"""

import json
import sys
import argparse
from pathlib import Path
import httpx

def print_colored(message, color='reset'):
    """Print colored output"""
    colors = {
        'red': '\033[31m',
        'green': '\033[32m',
        'yellow': '\033[33m',
        'blue': '\033[34m',
        'cyan': '\033[36m',
        'reset': '\033[0m'
    }
    print(f"{colors.get(color, colors['reset'])}{message}{colors['reset']}")

def test_openwebui_connection(url):
    """Test if OpenWebUI is accessible"""
    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.get(f"{url}/api/v1/auths")
            return response.status_code == 200
    except:
        return False

def main():
    parser = argparse.ArgumentParser(description="Install Memory Function into OpenWebUI")
    parser.add_argument("--url", default="http://localhost:3000", help="OpenWebUI URL")
    parser.add_argument("--api-key", help="API key for admin access")
    args = parser.parse_args()

    print_colored("🚀 OpenWebUI Memory Function Installer", 'cyan')
    print_colored("====================================", 'cyan')

    # Check OpenWebUI connection
    print_colored("\n🔍 Checking OpenWebUI connection...", 'blue')
    if not test_openwebui_connection(args.url):
        print_colored(f"❌ Cannot connect to OpenWebUI at {args.url}", 'red')
        print_colored("   Please ensure OpenWebUI is running and accessible", 'yellow')
        sys.exit(1)
    print_colored("✅ OpenWebUI is accessible", 'green')

    # Check if memory function file exists
    memory_function_path = Path("memory_function.py")
    if not memory_function_path.exists():
        print_colored(f"❌ Memory function file not found: {memory_function_path}", 'red')
        print_colored("   Please run this script from the backend directory", 'yellow')
        sys.exit(1)

    # Read the memory function code
    print_colored("\n📖 Reading memory function code...", 'blue')
    function_code = memory_function_path.read_text(encoding='utf-8')

    # Create function payload
    function_payload = {
        "id": "memory_function",
        "name": "Enhanced Memory Function",
        "type": "function", 
        "content": function_code,
        "is_active": True,
        "is_global": True
    }

    print_colored("✅ Function payload prepared", 'green')

    # Install function into OpenWebUI
    print_colored("\n🔧 Installing memory function...", 'blue')

    try:
        with httpx.Client(timeout=30.0) as client:
            headers = {"Content-Type": "application/json"}
            if args.api_key:
                headers["Authorization"] = f"Bearer {args.api_key}"

            # Check if function already exists
            functions_response = client.get(f"{args.url}/api/v1/functions/")
            existing_functions = functions_response.json()
            
            existing_function = None
            for func in existing_functions:
                if func.get('id') == 'memory_function':
                    existing_function = func
                    break

            if existing_function:
                print_colored("⚠️  Memory function already exists. Updating...", 'yellow')
                response = client.put(
                    f"{args.url}/api/v1/functions/memory_function",
                    json=function_payload,
                    headers=headers
                )
            else:
                print_colored("📦 Installing new memory function...", 'blue')
                response = client.post(
                    f"{args.url}/api/v1/functions/",
                    json=function_payload,
                    headers=headers
                )

            if response.status_code in [200, 201]:
                result = response.json()
                print_colored("✅ Memory function installed successfully!", 'green')
                print_colored(f"   Function ID: {result.get('id', 'N/A')}", 'reset')
                print_colored(f"   Function Name: {result.get('name', 'N/A')}", 'reset')
                print_colored("   Status: Active", 'reset')
            else:
                print_colored(f"❌ Failed to install: HTTP {response.status_code}", 'red')
                print_colored(f"   Response: {response.text}", 'yellow')
                sys.exit(1)

    except Exception as e:
        print_colored("❌ Failed to install memory function", 'red')
        print_colored(f"   Error: {str(e)}", 'yellow')
        
        if "401" in str(e) or "403" in str(e):
            print_colored("   💡 Try providing an API key with --api-key parameter", 'cyan')
            print_colored("   💡 Or ensure you're logged in as admin in OpenWebUI", 'cyan')
        sys.exit(1)

    # Verify installation
    print_colored("\n🔍 Verifying installation...", 'blue')
    try:
        with httpx.Client(timeout=10.0) as client:
            functions_response = client.get(f"{args.url}/api/v1/functions/")
            functions = functions_response.json()
            
            installed_function = None
            for func in functions:
                if func.get('id') == 'memory_function':
                    installed_function = func
                    break

            if installed_function:
                print_colored("✅ Verification successful!", 'green')
                print_colored("   Memory function is now available in OpenWebUI", 'reset')
                print_colored("   You can find it in: Admin → Functions → memory_function", 'cyan')
            else:
                print_colored("⚠️  Function installed but not found in verification", 'yellow')
                
    except Exception as e:
        print_colored(f"⚠️  Could not verify installation: {str(e)}", 'yellow')

    print_colored("\n🎉 Installation Complete!", 'green')
    print_colored("========================================", 'cyan')
    print_colored("Next steps:", 'blue')
    print_colored("1. Go to OpenWebUI Admin → Functions", 'reset')
    print_colored("2. Find 'Enhanced Memory Function'", 'reset')
    print_colored("3. Configure the function settings if needed", 'reset')
    print_colored("4. Test the function in a conversation", 'reset')
    print_colored("\n💡 The function will automatically connect to your memory API", 'cyan')
    print_colored("   at http://memory_api:8000 (or configured endpoint)", 'reset')

if __name__ == "__main__":
    main()
