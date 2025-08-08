#!/usr/bin/env python3
"""
Test Persona File Updates
========================

Test to verify that persona files have been updated with DuckDuckGo references
and that all test files are properly organized in the tests folder.
"""

import json
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_persona_files_updated():
    """Test that persona files have been updated with DuckDuckGo references."""
    print(" Testing persona file updates...")
    
    # Test persona_unified_small.json
    try:
        with open("../config/persona_unified_small.json", "r", encoding="utf-8") as f:
            small_persona = json.load(f)
        
        system_prompt = small_persona.get("system_prompt", "")
        capabilities = small_persona.get("capabilities", {})
        
        # Check for DuckDuckGo references
        assert "DuckDuckGo" in system_prompt, "persona_unified_small.json should mention DuckDuckGo"
        assert "SearXNG" not in system_prompt, "persona_unified_small.json should not mention SearXNG"
        
        # Check capabilities
        web_search = capabilities.get("web_search", {})
        assert web_search.get("primary_engine") == "duckduckgo", "Primary engine should be duckduckgo"
        
        print("[OK] persona_unified_small.json updated correctly")
        
    except Exception as e:
        print(f"[FAIL] Error testing persona_unified_small.json: {e}")
        return False
    
    # Test persona_new_user.json
    try:
        with open("../config/persona_new_user.json", "r", encoding="utf-8") as f:
            new_user_persona = json.load(f)
        
        system_prompt = new_user_persona.get("system_prompt", "")
        capabilities = new_user_persona.get("capabilities", {})
        
        # Check for DuckDuckGo references
        assert "DuckDuckGo" in system_prompt, "persona_new_user.json should mention DuckDuckGo"
        
        # Check capabilities
        web_search = capabilities.get("web_search", {})
        assert web_search.get("primary_engine") == "duckduckgo", "Primary engine should be duckduckgo"
        
        # Check instances
        primary_instances = web_search.get("search_quality", {}).get("primary_instances", [])
        assert "html.duckduckgo.com" in primary_instances, "Should include html.duckduckgo.com"
        
        print("[OK] persona_new_user.json updated correctly")
        
    except Exception as e:
        print(f"[FAIL] Error testing persona_new_user.json: {e}")
        return False
    
    return True

def test_tests_folder_organization():
    """Test that all test files are properly organized in tests folder."""
    print(" Testing tests folder organization...")
    
    expected_test_files = [
        "tests/tests/debug_memory_distances.py",
        "tests/tests/debug_trigger.py", 
        "tests/tests/test_anti_fabrication.py",
        "tests/tests/test_chat_web_search.py",
        "tests/tests/test_smart_memory.py",
        "tests/tests/test_uncertainty_triggers.py",
        "tests/tests/test_web_search.py",
        "tests/tests/validate_memory_system.py",
        "tests/tests/validate_pipeline.py",
        "tests/tests/validate_rag_system.py",
        "verify_fixes.py"
    ]
    
    tests_dir = "."  # Current directory is tests
    actual_files = os.listdir(tests_dir)
    
    missing_files = []
    for expected_file in expected_test_files:
        if expected_file not in actual_files:
            missing_files.append(expected_file)
    
    if missing_files:
        print(f"[FAIL] Missing test files: {missing_files}")
        return False
    
    print(f"[OK] All {len(expected_test_files)} test files found in tests folder")
    return True

def test_no_test_files_in_root():
    """Test that no test/debug files remain in root directory."""
    print(" Testing that no test files remain in root...")
    
    root_dir = ".."
    root_files = os.listdir(root_dir)
    
    test_patterns = ["test_", "debug_", "validate_", "verify_"]
    remaining_test_files = []
    
    for file in root_files:
        if file.endswith(".py") and any(file.startswith(pattern) for pattern in test_patterns):
            remaining_test_files.append(file)
    
    if remaining_test_files:
        print(f"[FAIL] Test files still in root directory: {remaining_test_files}")
        return False
    
    print("[OK] No test files remain in root directory")
    return True

def main():
    """Run all tests."""
    print(" Running persona update and test organization tests...\n")
    
    tests = [
        test_persona_files_updated,
        test_tests_folder_organization,
        test_no_test_files_in_root
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            print()  # Empty line between tests
        except Exception as e:
            print(f"[FAIL] Test {test.__name__} failed with exception: {e}\n")
    
    print(f"[CHART] Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print(" All tests passed! Persona files updated and tests organized correctly.")
        return True
    else:
        print("[WARN] Some tests failed. Please check the output above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
