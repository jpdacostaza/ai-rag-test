#!/usr/bin/env python3
"""
Minimal System Configuration Verification
==========================================

This script verifies that the minimal environment-only system is working correctly.

CHANGES APPLIED:
- Removed all JSON file loading
- Simplified to environment variables only
- Eliminated complex persona loading
- Streamlined prompt system for performance

"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, Any

def test_environment_config():
    """Test that environment variables are properly configured."""
    print("\n1. [CHECK] ENVIRONMENT CONFIGURATION")
    
    # Check system prompt
    system_prompt = os.getenv('DEFAULT_SYSTEM_PROMPT', '')
    if system_prompt:
        print(f"   [PASS] System prompt loaded: {len(system_prompt)} chars")
        print(f"   [INFO] Prompt: {system_prompt[:100]}...")
    else:
        print("   [FAIL] DEFAULT_SYSTEM_PROMPT not found")
        return False
    
    # Check other key variables
    required_vars = [
        'OLLAMA_BASE_URL',
        'BACKEND_HOST',
        'BACKEND_PORT',
        'REDIS_URL'
    ]
    
    for var in required_vars:
        value = os.getenv(var)
        if value:
            print(f"   [PASS] {var}: {value}")
        else:
            print(f"   [WARN] {var} not set")
    
    return True

def test_minimal_processor():
    """Test that the minimal processor is working."""
    print("\n2. [CHECK] MINIMAL PROCESSOR")
    
    try:
        sys.path.append('/app/backend')
        from pipelines.memory_system.processor import MemorySystemProcessor
        
        processor = MemorySystemProcessor(debug=True)
        
        # Test prompt loading
        prompt = processor._get_prompt()
        if prompt:
            print(f"   [PASS] Processor prompt loaded: {len(prompt)} chars")
        else:
            print("   [FAIL] Processor failed to load prompt")
            return False
        
        # Test system message creation
        system_msg = processor.create_system_message("test_user", [], None)
        if system_msg:
            print(f"   [PASS] System message created: {len(system_msg)} chars")
        else:
            print("   [FAIL] Failed to create system message")
            return False
            
        return True
        
    except Exception as e:
        print(f"   [FAIL] Processor import error: {e}")
        return False

def test_config_cleanup():
    """Test that old complex files are removed."""
    print("\n3. [CHECK] CONFIGURATION CLEANUP")
    
    # Check that JSON prompt files are removed
    json_files = [
        '/app/backend/config/unified_prompt.json',
        '/app/backend/config/unified_prompt_minimal.json'
    ]
    
    all_removed = True
    for file_path in json_files:
        if Path(file_path).exists():
            print(f"   [WARN] Old file still exists: {file_path}")
            all_removed = False
        else:
            print(f"   [PASS] File properly removed: {file_path}")
    
    return all_removed

def test_performance_readiness():
    """Test that the system is optimized for performance."""
    print("\n4. [CHECK] PERFORMANCE OPTIMIZATION")
    
    # Check Ollama settings
    ollama_vars = {
        'OLLAMA_FLASH_ATTENTION': '1',
        'OLLAMA_KV_CACHE_TYPE': 'q4_0',
        'OLLAMA_NUM_THREAD': '8',
        'OLLAMA_NUM_PARALLEL': '2'
    }
    
    all_optimized = True
    for var, expected in ollama_vars.items():
        actual = os.getenv(var)
        if actual == expected:
            print(f"   [PASS] {var}: {actual}")
        else:
            print(f"   [WARN] {var}: {actual} (expected: {expected})")
            all_optimized = False
    
    return all_optimized

def main():
    """Main verification function."""
    print("🔍 MINIMAL SYSTEM VERIFICATION")
    print("=" * 50)
    
    tests = [
        ("Environment Config", test_environment_config),
        ("Minimal Processor", test_minimal_processor),
        ("Configuration Cleanup", test_config_cleanup),
        ("Performance Settings", test_performance_readiness)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"   [ERROR] {test_name} failed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 VERIFICATION SUMMARY")
    print("=" * 50)
    
    passed = 0
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"   {status:4s} | {test_name}")
        if result:
            passed += 1
    
    print(f"\n✅ Tests passed: {passed}/{len(results)}")
    
    if passed == len(results):
        print("🎉 All systems optimized and ready!")
        return True
    else:
        print("⚠️  Some issues found - check logs above")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
