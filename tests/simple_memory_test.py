#!/usr/bin/env python3
"""
Simple Memory Test Runner - Test Core Memory Functions
"""

import os
import sys
import subprocess
import time
from pathlib import Path

def run_test(test_path):
    """Run a single test"""
    print(f"\n{'='*50}")
    print(f"Running: {test_path.name}")
    print(f"{'='*50}")
    
    start_time = time.time()
    
    try:
        # Set environment for UTF-8 handling
        env = os.environ.copy()
        env['PYTHONIOENCODING'] = 'utf-8'
        
        result = subprocess.run(
            [sys.executable, str(test_path)],
            cwd=str(test_path.parent),
            env=env,
            capture_output=True,
            text=True,
            errors='replace',
            timeout=60
        )
        
        duration = time.time() - start_time
        success = result.returncode == 0
        
        if success:
            print(f"✅ PASSED ({duration:.2f}s)")
        else:
            print(f"❌ FAILED ({duration:.2f}s)")
            if result.stderr:
                print("Error:")
                print(result.stderr[:300])
        
        return success, duration
        
    except Exception as e:
        duration = time.time() - start_time
        print(f"❌ ERROR ({duration:.2f}s): {str(e)}")
        return False, duration

def main():
    """Run key memory tests"""
    print("SIMPLE MEMORY TEST RUNNER")
    print("=" * 50)
    
    backend_dir = Path(".")
    
    # Key tests to run
    tests = [
        "tests/test_memory_function.py",
        "tests/test_memory_service_endpoints.py"
    ]
    
    results = []
    
    for test_path_str in tests:
        test_path = backend_dir / test_path_str
        if test_path.exists():
            success, duration = run_test(test_path)
            results.append((test_path.name, success, duration))
        else:
            print(f"❌ MISSING: {test_path_str}")
    
    # Summary
    total = len(results)
    passed = sum(1 for _, success, _ in results if success)
    
    print(f"\n{'='*50}")
    print("SUMMARY")
    print(f"{'='*50}")
    print(f"Total: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    
    if passed > 0:
        print("\n✅ PASSED:")
        for name, success, duration in results:
            if success:
                print(f"  - {name} ({duration:.2f}s)")
    
    if total - passed > 0:
        print("\n❌ FAILED:")
        for name, success, duration in results:
            if not success:
                print(f"  - {name} ({duration:.2f}s)")

if __name__ == "__main__":
    main()
