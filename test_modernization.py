#!/usr/bin/env python3
"""
Final Modernization Validation Test
==================================

Tests that modernization fixes have resolved the web search triggering issues.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_enhanced_web_search_import():
    """Test that enhanced web search can be imported correctly."""
    try:
        from utilities.enhanced_web_search import should_trigger_web_search, search_web
        print("✅ Enhanced web search import: SUCCESS")
        return True
    except ImportError as e:
        print(f"❌ Enhanced web search import: FAILED - {e}")
        return False

def test_legacy_trigger_scenarios():
    """Test various scenarios that should NOT trigger web search."""
    try:
        from utilities.enhanced_web_search import should_trigger_web_search
        
        test_cases = [
            ("Hello my name is J.P. I work at swift, can you remember that?", False),
            ("I like pizza and sandwiches", False),
            ("I am a software engineer at Microsoft", False), 
            ("My company is Apple Inc", False),
            ("I work at Google as a developer", False),
            ("search the web for latest news", True),  # Should trigger
            ("what are the latest updates today", True),  # Should trigger
            ("what is Python programming", False),  # Should not trigger
        ]
        
        passed = 0
        total = len(test_cases)
        
        print("\n🧪 Testing Legacy Trigger Scenarios:")
        print("-" * 50)
        
        for query, expected in test_cases:
            result = should_trigger_web_search(query, "")
            status = "✅" if result == expected else "❌"
            trigger_text = "triggers" if result else "doesn't trigger"
            expected_text = "should trigger" if expected else "shouldn't trigger"
            
            print(f"{status} '{query[:40]}...' → {trigger_text} ({expected_text})")
            
            if result == expected:
                passed += 1
        
        print(f"\n📊 Results: {passed}/{total} tests passed")
        return passed == total
        
    except Exception as e:
        print(f"❌ Legacy trigger test failed: {e}")
        return False

def test_deprecation_cleanup():
    """Test that deprecated modules have been removed."""
    deprecated_files = [
        "utilities/structured_logging.py",
        "utilities/structured_logging_new.py", 
        "utilities/structured_logging_backup.py",
        "pipelines/failed"
    ]
    
    print("\n🗑️ Testing Deprecated File Cleanup:")
    print("-" * 50)
    
    all_cleaned = True
    for file_path in deprecated_files:
        if os.path.exists(file_path):
            print(f"❌ Still exists: {file_path}")
            all_cleaned = False
        else:
            print(f"✅ Removed: {file_path}")
    
    return all_cleaned

def main():
    """Run all modernization validation tests."""
    print("🔍 LEGACY CODE MODERNIZATION VALIDATION")
    print("=" * 60)
    
    tests = [
        ("Enhanced Web Search Import", test_enhanced_web_search_import()),
        ("Legacy Trigger Scenarios", test_legacy_trigger_scenarios()),
        ("Deprecation Cleanup", test_deprecation_cleanup())
    ]
    
    passed = sum(1 for _, result in tests if result)
    total = len(tests)
    
    print("\n" + "=" * 60)
    print("📋 FINAL VALIDATION SUMMARY:")
    print("-" * 30)
    
    for test_name, result in tests:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\n📊 Overall Result: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 MODERNIZATION COMPLETE!")
        print("✅ All legacy code issues have been resolved")
        print("✅ Web search triggering fixed") 
        print("✅ Deprecated modules removed")
        print("✅ System ready for production")
    else:
        print(f"\n⚠️ {total - passed} validation issues remain")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
