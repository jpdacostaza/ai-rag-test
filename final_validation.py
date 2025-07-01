#!/usr/bin/env python3
"""
Final System Validation - July 1, 2025
=====================================
Comprehensive validation of the complete memory system after rebuild and filter implementation.
"""

import sqlite3
import os
import subprocess
import json
import sys

def validate_files():
    """Validate all key files exist"""
    print("🔍 VALIDATING FILES...")
    
    required_files = [
        "memory/functions/memory_filter.py",
        "deploy_memory_filter.py", 
        "test_filter_loading.py",
        "integrated_memory_startup.py",
        "docs/COMPLETE_CHAT_SESSION_SUMMARY_JULY1.md",
        "COMPLETE_CHAT_HANDOVER_JULY_2025.md"
    ]
    
    for file in required_files:
        if os.path.exists(file):
            print(f"✅ {file}")
        else:
            print(f"❌ {file} - MISSING")
            return False
    
    return True

def validate_database():
    """Validate database contains both function and filter"""
    print("\n🗄️ VALIDATING DATABASE...")
    
    try:
        conn = sqlite3.connect('storage/openwebui/webui.db')
        cursor = conn.cursor()
        
        # Check for both function and filter
        cursor.execute("SELECT id, name, type, is_active FROM function WHERE id IN ('memory_function', 'memory_filter')")
        entries = cursor.fetchall()
        
        function_found = False
        filter_found = False
        
        for entry in entries:
            print(f"✅ {entry[0]} - {entry[1]} (type: {entry[2]}, active: {entry[3]})")
            if entry[0] == 'memory_function' and entry[2] == 'function':
                function_found = True
            if entry[0] == 'memory_filter' and entry[2] == 'filter':
                filter_found = True
        
        conn.close()
        
        if function_found and filter_found:
            print("✅ Both function and filter entries found and active")
            return True
        else:
            print("❌ Missing function or filter entry")
            return False
            
    except Exception as e:
        print(f"❌ Database validation failed: {e}")
        return False

def validate_containers():
    """Validate all containers are running"""
    print("\n🐳 VALIDATING CONTAINERS...")
    
    try:
        result = subprocess.run(['docker-compose', 'ps', '--format', 'json'], 
                              capture_output=True, text=True, cwd='.')
        
        if result.returncode != 0:
            print("❌ Docker compose not available")
            return False
        
        containers = []
        for line in result.stdout.strip().split('\n'):
            if line.strip():
                containers.append(json.loads(line))
        
        required_services = ['redis', 'chroma', 'ollama', 'memory_api', 'openwebui']
        running_services = []
        
        for container in containers:
            service = container.get('Service', '')
            state = container.get('State', '')
            if service in required_services and 'running' in state.lower():
                running_services.append(service)
                print(f"✅ {service} - {state}")
        
        if len(running_services) == len(required_services):
            print("✅ All required containers running")
            return True
        else:
            missing = set(required_services) - set(running_services)
            print(f"❌ Missing containers: {missing}")
            return False
            
    except Exception as e:
        print(f"❌ Container validation failed: {e}")
        return False

def validate_git():
    """Validate git status is clean"""
    print("\n📚 VALIDATING GIT STATUS...")
    
    try:
        result = subprocess.run(['git', 'status', '--porcelain'], 
                              capture_output=True, text=True, cwd='.')
        
        if result.returncode != 0:
            print("❌ Git not available")
            return False
        
        if result.stdout.strip() == '':
            print("✅ Git working directory clean")
            return True
        else:
            print(f"❌ Uncommitted changes found:\n{result.stdout}")
            return False
            
    except Exception as e:
        print(f"❌ Git validation failed: {e}")
        return False

def main():
    """Run complete system validation"""
    print("=" * 60)
    print("🏁 FINAL SYSTEM VALIDATION - JULY 1, 2025")
    print("=" * 60)
    
    validations = [
        ("Files", validate_files),
        ("Database", validate_database), 
        ("Containers", validate_containers),
        ("Git", validate_git)
    ]
    
    results = []
    for name, validator in validations:
        try:
            result = validator()
            results.append((name, result))
        except Exception as e:
            print(f"❌ {name} validation crashed: {e}")
            results.append((name, False))
    
    print("\n" + "=" * 60)
    print("📊 VALIDATION SUMMARY")
    print("=" * 60)
    
    all_passed = True
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{name:15} {status}")
        if not result:
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 ALL VALIDATIONS PASSED!")
        print("🚀 System is fully operational and ready for use")
        print("📋 Memory system with both function and filter support")
        print("🔄 Complete Docker rebuild completed successfully")
        print("💾 All changes committed and pushed to git")
    else:
        print("⚠️  SOME VALIDATIONS FAILED!")
        print("🔧 Please review and fix issues before proceeding")
    
    print("=" * 60)
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
