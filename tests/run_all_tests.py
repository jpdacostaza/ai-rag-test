#!/usr/bin/env python3
"""
Memory System Test Runner - Quick Start
=======================================

Simple script to run all memory system tests.

Usage:
  python run_all_tests.py                    # Run all tests
  python run_all_tests.py --quick            # Run only basic tests  
  python run_all_tests.py --integration      # Run only integration test
"""

import subprocess
import sys
import argparse
from pathlib import Path

def run_command(cmd, description):
    """Run a command and return success status."""
    print(f"\n🔄 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed")
        if e.stdout:
            print("STDOUT:", e.stdout)
        if e.stderr:
            print("STDERR:", e.stderr)
        return False

def main():
    parser = argparse.ArgumentParser(description="Memory System Test Runner")
    parser.add_argument("--quick", action="store_true", help="Run only basic tests")
    parser.add_argument("--integration", action="store_true", help="Run only integration test")
    parser.add_argument("--report", action="store_true", help="Generate test report")
    
    args = parser.parse_args()
    
    print("🧪 Memory System Test Runner")
    print("=" * 40)
    
    # Get Python executable
    python_exe = "C:/Users/jdaco/AppData/Local/Programs/Python/Python312/python.exe"
    
    success_count = 0
    total_tests = 0
    
    if args.integration:
        # Run only integration test
        total_tests = 1
        if run_command(f'"{python_exe}" tests/integration_test.py', "Integration Test"):
            success_count += 1
    
    elif args.quick:
        # Run only basic memory API tests
        total_tests = 1
        if run_command(f'"{python_exe}" -m pytest tests/test_memory_system.py::TestMemoryAPI -v --asyncio-mode=auto', "Basic Memory API Tests"):
            success_count += 1
    
    else:
        # Run full test suite
        total_tests = 3
        
        # Run memory system tests
        if run_command(f'"{python_exe}" -m pytest tests/test_memory_system.py -v --asyncio-mode=auto', "Memory System Tests"):
            success_count += 1
        
        # Run memory function tests  
        if run_command(f'"{python_exe}" -m pytest tests/test_memory_function.py -v --asyncio-mode=auto', "Memory Function Tests"):
            success_count += 1
        
        # Run integration test
        if run_command(f'"{python_exe}" tests/integration_test.py', "Integration Test"):
            success_count += 1
    
    # Generate report if requested
    if args.report:
        total_tests += 1
        if run_command(f'"{python_exe}" tests/test_report.py', "Test Report Generation"):
            success_count += 1
    
    # Final summary
    print(f"\n🎯 FINAL RESULTS")
    print("=" * 40)
    print(f"Tests Passed: {success_count}/{total_tests}")
    
    if success_count == total_tests:
        print("🎉 All tests completed successfully!")
        print("✅ Memory system is fully functional!")
        return 0
    else:
        print("⚠️  Some tests failed!")
        print("❌ Memory system may have issues!")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
