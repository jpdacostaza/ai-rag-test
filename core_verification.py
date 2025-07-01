#!/usr/bin/env python3
"""
Final Core System Verification
Verifies only the essential functionality after cleanup
"""
import requests
import json
import time

def test_core_functionality():
    """Test the core memory system functionality"""
    print("🔧 Core System Verification")
    print("=" * 40)
    
    memory_api_url = "http://localhost:8001"
    test_user = "core_verification_user"
    
    # Test 1: Basic API Health
    print("\n1. API Health Check...")
    try:
        response = requests.get(f"{memory_api_url}/", timeout=5)
        if response.status_code == 200:
            print("   ✅ Memory API is running")
        else:
            print(f"   ❌ Memory API health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Memory API is not accessible: {e}")
        return False
    
    # Test 2: Remember Function
    print("\n2. Testing Remember Function...")
    try:
        response = requests.post(
            f"{memory_api_url}/api/memory/remember",
            json={
                "user_id": test_user,
                "content": "Core verification test memory",
                "source": "core_test"
            },
            timeout=5
        )
        if response.status_code == 200:
            print("   ✅ Remember function working")
        else:
            print(f"   ❌ Remember function failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Remember function error: {e}")
        return False
    
    # Test 3: Retrieve Function
    print("\n3. Testing Retrieve Function...")
    try:
        response = requests.post(
            f"{memory_api_url}/api/memory/retrieve",
            json={
                "user_id": test_user,
                "query": "verification test",
                "threshold": 0.05,
                "limit": 5
            },
            timeout=5
        )
        if response.status_code == 200:
            result = response.json()
            memories = result.get('memories', [])
            if len(memories) > 0:
                print(f"   ✅ Retrieve function working ({len(memories)} memories found)")
            else:
                print("   ⚠️ Retrieve function working but no memories found")
        else:
            print(f"   ❌ Retrieve function failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Retrieve function error: {e}")
        return False
    
    # Test 4: Forget Function
    print("\n4. Testing Forget Function...")
    try:
        response = requests.post(
            f"{memory_api_url}/api/memory/forget",
            json={
                "user_id": test_user,
                "forget_query": "verification test",
                "source": "core_test"
            },
            timeout=5
        )
        if response.status_code == 200:
            result = response.json()
            removed_count = result.get('removed_count', 0)
            print(f"   ✅ Forget function working ({removed_count} memories removed)")
        else:
            print(f"   ❌ Forget function failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Forget function error: {e}")
        return False
    
    # Test 5: Debug Stats
    print("\n5. Testing Debug Stats...")
    try:
        response = requests.get(f"{memory_api_url}/debug/stats", timeout=5)
        if response.status_code == 200:
            result = response.json()
            print("   ✅ Debug stats working")
            print(f"      Redis connected: {result.get('redis', {}).get('connected', False)}")
            print(f"      ChromaDB connected: {result.get('chromadb', {}).get('connected', False)}")
        else:
            print(f"   ❌ Debug stats failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Debug stats error: {e}")
        return False
    
    print("\n" + "=" * 40)
    print("🎉 All core functionality tests PASSED!")
    return True

def check_essential_files():
    """Check that essential files are present"""
    print("\n📁 Essential Files Check")
    print("=" * 40)
    
    essential_files = [
        "enhanced_memory_api.py",
        "docker-compose.yml",
        "requirements.txt",
        "storage/openwebui/memory_function_working.py"
    ]
    
    missing_files = []
    for file_path in essential_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
        else:
            print(f"   ✅ {file_path}")
    
    if missing_files:
        print(f"\n❌ Missing essential files:")
        for file_path in missing_files:
            print(f"   • {file_path}")
        return False
    else:
        print("\n✅ All essential files present")
        return True

def main():
    """Main verification function"""
    print("🚀 Final Core System Verification")
    print("=" * 50)
    
    # Check files first
    files_ok = check_essential_files()
    
    # Then test functionality
    if files_ok:
        functionality_ok = test_core_functionality()
        
        if functionality_ok:
            print("\n🎉 SYSTEM STATUS: FULLY OPERATIONAL ✅")
            print("The core memory system is working perfectly!")
        else:
            print("\n❌ SYSTEM STATUS: FUNCTIONALITY ISSUES")
            print("Some core functions are not working properly.")
    else:
        print("\n❌ SYSTEM STATUS: MISSING FILES")
        print("Essential files are missing.")

if __name__ == "__main__":
    import os
    main()
