#!/usr/bin/env python3
"""
Quick Setup Script for OpenWebUI API Key Management
Demonstrates the complete setup and usage workflow.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path to import API key manager
sys.path.append(str(Path(__file__).parent.parent))
from setup.api_key_manager import APIKeyManager


def demo_api_key_setup():
    """Demonstrate API key setup and usage."""
    print("🔑 OpenWebUI API Key Management Demo")
    print("=" * 45)
    
    # Initialize manager
    manager = APIKeyManager()
    
    print("1. Checking existing configuration...")
    
    # Check current status
    default_key = manager.get_default_key()
    users = manager.list_users()
    environments = manager.list_environments()
    
    if default_key and default_key.get('api_key'):
        print(f"   ✅ Default key configured: ...{default_key['api_key'][-8:]}")
    else:
        print("   ⚠️  No default key configured")
    
    if users:
        print(f"   ✅ {len(users)} user(s) configured: {', '.join(users.keys())}")
    else:
        print("   ⚠️  No user keys configured")
    
    if environments:
        print(f"   ✅ {len(environments)} environment(s) configured: {', '.join(environments.keys())}")
    else:
        print("   ⚠️  No environment keys configured")
    
    print("\n2. Environment variable support...")
    env_key = os.getenv("OPENWEBUI_API_KEY")
    env_url = os.getenv("OPENWEBUI_BASE_URL")
    
    if env_key:
        print(f"   ✅ OPENWEBUI_API_KEY set: ...{env_key[-8:]}")
        print(f"   ✅ OPENWEBUI_BASE_URL: {env_url or 'http://localhost:3000'}")
    else:
        print("   ⚠️  OPENWEBUI_API_KEY not set")
    
    print("\n3. Key retrieval demonstration...")
    
    # Test different retrieval methods
    test_scenarios = [
        ("Default fallback", None, None),
        ("User lookup", "example_user", None),
        ("Environment lookup", None, "development"),
    ]
    
    for scenario_name, user, environment in test_scenarios:
        print(f"   🧪 Testing {scenario_name}...")
        credentials = manager.get_key(user=user, environment=environment)
        
        if credentials:
            source = credentials.get('source', 'unknown')
            key_preview = credentials['api_key'][-8:] if len(credentials['api_key']) > 8 else 'short-key'
            print(f"      ✅ Found key from {source}: ...{key_preview}")
            print(f"      🌐 Base URL: {credentials['base_url']}")
        else:
            print(f"      ❌ No key found for this scenario")
    
    print("\n4. Setup options...")
    print("   To add keys interactively:")
    print("   📝 python api_key_manager.py")
    
    print("\n   To set environment variables:")
    print("   🔧 export OPENWEBUI_API_KEY='your-key-here'")
    print("   🔧 export OPENWEBUI_BASE_URL='http://localhost:3000'")
      print("\n   To use updated diagnostic tools:")
    print("   🔍 python demo-tests/debug-tools/openwebui_memory_diagnostic.py")
    print("   🧠 python demo-tests/debug-tools/test_memory_cross_chat.py")
    
    print("\n5. Shell script alternatives:")
    shell_scripts = [
        ("setup-api-keys.ps1", "PowerShell script for Windows"),
        ("setup-api-keys.sh", "Bash script for Linux/macOS"),
        ("SHELL_SCRIPTS_GUIDE.md", "Shell script documentation"),
    ]
    
    for filename, description in shell_scripts:
        file_path = Path(__file__).parent / filename
        status = "✅" if file_path.exists() else "❌"
        print(f"   {status} {filename} - {description}")
    
    if Path(__file__).parent.joinpath("setup-api-keys.ps1").exists():
        print(f"      💻 Windows: .\\setup-api-keys.ps1 -Status")
    if Path(__file__).parent.joinpath("setup-api-keys.sh").exists():
        print(f"      🐧 Linux/macOS: ./setup-api-keys.sh --status")

    print("\n6. Files created/updated:")
    files_info = [
        ("api_key_manager.py", "Main utility class"),
        ("openwebui_api_keys.example.json", "Example configuration"),
        ("API_KEY_MANAGEMENT.md", "Complete documentation"),
        ("SHELL_SCRIPTS_GUIDE.md", "Shell script documentation"),
        ("setup-api-keys.ps1", "PowerShell setup script"),
        ("setup-api-keys.sh", "Bash setup script"),
        (".gitignore", "Updated with key protection"),
        ("demo-tests/debug-tools/openwebui_memory_diagnostic.py", "Updated diagnostic tool"),
        ("demo-tests/debug-tools/test_memory_cross_chat.py", "Updated test tool"),
    ]
    
    for filename, description in files_info:
        file_path = Path(filename)
        if filename.startswith("demo-tests/"):
            file_path = Path(__file__).parent / filename
        else:
            file_path = Path(__file__).parent / filename
            
        status = "✅" if file_path.exists() else "❌"
        print(f"   {status} {filename} - {description}")
    
    print("\n🎯 Next Steps:")
    print("1. Set up your API keys using one of the methods above")
    print("2. Run the diagnostic tool to test memory functionality")
    print("3. Use --user=username or --env=environment for specific contexts")
    print("4. Check API_KEY_MANAGEMENT.md for detailed documentation")


if __name__ == "__main__":
    try:
        demo_api_key_setup()
    except KeyboardInterrupt:
        print("\n❌ Demo cancelled by user")
    except Exception as e:
        print(f"❌ Error running demo: {e}")
        import traceback
        traceback.print_exc()
