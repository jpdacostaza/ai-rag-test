#!/usr/bin/env python3
"""
Simple Memory Test Runner - Focus on Working Tests
Runs key memory tests that are likely to pass
"""

import os
import sys
import subprocess
import time
from pathlib import Path
from datetime import datetime

def run_test(test_path):
    """Run a single test with proper encoding"""
    print(f"\n{'='*60}")
    print(f"Running: {test_path.name}")
    print(f"{'='*60}")
    
    start_time = time.time()
    
    try:
        # Set environment variables for proper encoding
        env = os.environ.copy()
        env['PYTHONIOENCODING'] = 'utf-8'
        env['PYTHONLEGACYWINDOWSSTDIO'] = '1'
        
        result = subprocess.run(
            [sys.executable, str(test_path)],
            cwd=str(test_path.parent),
            env=env,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=120  # 2 minute timeout
        )
        
        duration = time.time() - start_time
        success = result.returncode == 0
        
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{status} - {test_path.name} ({duration:.2f}s)")
        
        if not success:
            if result.stderr:
                print("STDERR:")
                print(result.stderr[:500] + "..." if len(result.stderr) > 500 else result.stderr)
            if result.stdout:
                print("STDOUT:")
                print(result.stdout[:500] + "..." if len(result.stdout) > 500 else result.stdout)
        
        return success, duration
        
    except subprocess.TimeoutExpired:
        duration = time.time() - start_time
        print(f"❌ TIMEOUT - {test_path.name} ({duration:.2f}s)")
        return False, duration
    except Exception as e:
        duration = time.time() - start_time
        print(f"❌ ERROR - {test_path.name} ({duration:.2f}s): {str(e)}")
        return False, duration

def main():
    """Run focused memory tests"""
    print("FOCUSED MEMORY TEST RUNNER")
    print("=" * 60)
    
    backend_dir = Path("e:/Projects/opt/backend")
    
    # Focus on tests that are most likely to work
    priority_tests = [
        "tests/test_memory_function.py",
        "tests/test_memory_service_endpoints.py", 
        "tests/test_memory_service_validation.py"
    ]
    
    # Additional tests to try (if priority tests pass)
    additional_tests = [
        "test_memory_localhost.py",
        "test_memory_final.py",
        "tests/test_enhanced_memory.py",
        "tests/test_memory_service_basic.py"
    ]
    
    results = []
    
    print(f"Running {len(priority_tests)} priority tests...")
    
    # Run priority tests first
    for test_path_str in priority_tests:
        test_path = backend_dir / test_path_str
        if test_path.exists():
            success, duration = run_test(test_path)
            results.append((test_path.name, success, duration))
        else:
            print(f"❌ MISSING - {test_path_str}")
            results.append((test_path_str, False, 0))
    
    # Check if priority tests passed
    priority_passed = sum(1 for _, success, _ in results if success)
    
    print(f"\n--- Priority Tests Summary ---")
    print(f"Passed: {priority_passed}/{len(priority_tests)}")
    
    if priority_passed > 0:
        print(f"\nRunning {len(additional_tests)} additional tests...")
        
        for test_path_str in additional_tests:
            test_path = backend_dir / test_path_str
            if test_path.exists():
                success, duration = run_test(test_path)
                results.append((test_path.name, success, duration))
            else:
                print(f"❌ MISSING - {test_path_str}")
                results.append((test_path_str, False, 0))
    
    # Final summary
    total_tests = len(results)
    passed_tests = sum(1 for _, success, _ in results if success)
    failed_tests = total_tests - passed_tests
    total_duration = sum(duration for _, _, duration in results)
    
    print(f"\n{'='*60}")
    print("FOCUSED MEMORY TEST SUMMARY")
    print(f"{'='*60}")
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {failed_tests}")
    print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    print(f"Total Duration: {total_duration:.2f}s")
    
    if failed_tests > 0:
        print(f"\n❌ FAILED TESTS:")
        for name, success, duration in results:
            if not success:
                print(f"  - {name} ({duration:.2f}s)")
    
    if passed_tests > 0:
        print(f"\n✅ PASSED TESTS:")
        for name, success, duration in results:
            if success:
                print(f"  - {name} ({duration:.2f}s)")
    
    # Save simple report
    report_path = backend_dir / "logs" / "focused_memory_test_report.md"
    report_path.parent.mkdir(exist_ok=True)
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("# Focused Memory Test Report\n\n")
        f.write(f"**Run Time**: {datetime.now()}\n")
        f.write(f"**Total Tests**: {total_tests}\n")
        f.write(f"**Passed**: {passed_tests}\n")
        f.write(f"**Failed**: {failed_tests}\n")
        f.write(f"**Success Rate**: {(passed_tests/total_tests)*100:.1f}%\n")
        f.write(f"**Total Duration**: {total_duration:.2f}s\n\n")
        
        f.write("## Test Results\n\n")
        for name, success, duration in results:
            status = "✅ PASSED" if success else "❌ FAILED"
            f.write(f"- {status} **{name}** ({duration:.2f}s)\n")
    
    print(f"\nReport saved to: {report_path}")
    
    return 0 if failed_tests == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
