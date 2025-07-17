#!/usr/bin/env python3
"""
Test Runner for AI RAG Backend
==============================
This script runs tests from the tests/ directory.

Usage:
    python run_tests.py                    # Run all tests
    python run_tests.py --memory           # Run memory tests only
    python run_tests.py --focused          # Run focused memory tests
    python run_tests.py --comprehensive    # Run comprehensive memory tests
    python run_tests.py --help             # Show help
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

def run_tests_in_directory(test_script: str, description: str) -> bool:
    """Run a test script in the tests directory"""
    tests_dir = Path("tests")
    test_path = tests_dir / test_script
    
    if not test_path.exists():
        print(f"❌ Test script not found: {test_path}")
        return False
    
    print(f"\n🚀 {description}")
    print("=" * 60)
    
    try:
        # Change to tests directory and run the script
        result = subprocess.run(
            [sys.executable, test_script],
            cwd=str(tests_dir),
            timeout=600  # 10 minute timeout
        )
        
        success = result.returncode == 0
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"\n{status} - {description}")
        return success
        
    except subprocess.TimeoutExpired:
        print(f"\n❌ TIMEOUT - {description} (exceeded 10 minutes)")
        return False
    except Exception as e:
        print(f"\n❌ ERROR - {description}: {str(e)}")
        return False

def main():
    parser = argparse.ArgumentParser(description="AI RAG Backend Test Runner")
    parser.add_argument("--memory", action="store_true", help="Run memory tests only")
    parser.add_argument("--focused", action="store_true", help="Run focused memory tests")
    parser.add_argument("--comprehensive", action="store_true", help="Run comprehensive memory tests")
    
    args = parser.parse_args()
    
    print("AI RAG Backend Test Runner")
    print("=" * 60)
    print("Running tests from tests/ directory...")
    
    success = True
    
    if args.focused:
        success = run_tests_in_directory("run_focused_memory_tests.py", "Focused Memory Tests")
    elif args.comprehensive:
        success = run_tests_in_directory("run_memory_tests_comprehensive.py", "Comprehensive Memory Tests")
    elif args.memory:
        success = run_tests_in_directory("run_memory_tests.py", "Memory Tests")
    else:
        # Run all available test runners
        test_runners = [
            ("run_focused_memory_tests.py", "Focused Memory Tests"),
            ("run_memory_tests.py", "Memory Tests"),
            ("run_comprehensive_tests.py", "Comprehensive Tests"),
            ("run_all_tests.py", "All Tests")
        ]
        
        for script, description in test_runners:
            if (Path("tests") / script).exists():
                test_success = run_tests_in_directory(script, description)
                success = success and test_success
            else:
                print(f"⚠️  Skipping {description} - script not found")
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 All tests completed successfully!")
    else:
        print("❌ Some tests failed. Please check the output above.")
    print("=" * 60)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
