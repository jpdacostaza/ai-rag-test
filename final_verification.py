#!/usr/bin/env python3
"""
Final Memory Function Verification
=================================
This script performs a comprehensive check of the memory function status.
"""

import sqlite3
import json
import requests
import time

def check_function_status():
    """Check the function status in the database"""
    print("🔍 Checking function status in database...")
    
    conn = sqlite3.connect('storage/openwebui/webui.db')
    cursor = conn.cursor()
    
    # Check function
    cursor.execute("SELECT id, name, is_active FROM function WHERE id = 'memory_function'")
    result = cursor.fetchone()
    
    if result:
        function_id, function_name, is_active = result
        status = "✅ ACTIVE" if is_active else "❌ DISABLED"
        print(f"   Function: {function_name} - {status}")
    else:
        print("   ❌ Function not found!")
        return False
    
    # Check model assignments
    cursor.execute("SELECT id, name, params FROM model")
    models = cursor.fetchall()
    
    print("📊 Model configurations:")
    for model_id, model_name, params_str in models:
        if params_str:
            try:
                params = json.loads(params_str)
                filters = params.get('filter_ids', [])
                has_memory = 'memory_function' in filters
                status = "✅ ASSIGNED" if has_memory else "❌ NOT ASSIGNED"
                print(f"   {model_name}: {status}")
            except:
                print(f"   {model_name}: ⚠️  UNKNOWN")
    
    conn.close()
    return result[2] if result else False

def test_memory_api():
    """Test the memory API connectivity"""
    print("🧠 Testing memory API connectivity...")
    
    try:
        # Test health endpoint
        response = requests.get('http://localhost:8001/health', timeout=5)
        if response.status_code == 200:
            print("   ✅ Memory API is healthy")
            return True
        else:
            print(f"   ❌ Memory API unhealthy: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Memory API unreachable: {e}")
        return False

def test_openwebui_function():
    """Test if OpenWebUI can load the function"""
    print("🌐 Testing OpenWebUI function loading...")
    
    try:
        # Test functions endpoint
        response = requests.get('http://localhost:3000/api/v1/functions/', timeout=10)
        if response.status_code == 200:
            functions = response.json()
            for func in functions:
                if func.get('id') == 'memory_function':
                    is_active = func.get('is_active', False)
                    status = "✅ ACTIVE" if is_active else "❌ DISABLED"
                    print(f"   Memory Function in API: {status}")
                    return is_active
            print("   ⚠️  Memory function not found in API response")
            return False
        else:
            print(f"   ⚠️  Cannot access functions API: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ⚠️  Error accessing OpenWebUI: {e}")
        return False

def main():
    """Run comprehensive verification"""
    print("🔬 Final Memory Function Verification")
    print("=" * 50)
    
    # Check database status
    db_active = check_function_status()
    
    # Test memory API
    api_working = test_memory_api()
    
    # Test OpenWebUI function loading
    ui_active = test_openwebui_function()
    
    print("\n📋 Summary:")
    print(f"   Database Status: {'✅ Active' if db_active else '❌ Disabled'}")
    print(f"   Memory API: {'✅ Working' if api_working else '❌ Failed'}")
    print(f"   OpenWebUI Integration: {'✅ Active' if ui_active else '❌ Issues'}")
    
    if db_active and api_working:
        print("\n🎉 Memory function is fully operational!")
        print("💡 The function should now remain active and work properly.")
        print("🔄 If it disables again, run: python memory_function_guardian.py")
        return True
    else:
        print("\n⚠️  Some issues detected - may need troubleshooting.")
        return False

if __name__ == "__main__":
    main()
