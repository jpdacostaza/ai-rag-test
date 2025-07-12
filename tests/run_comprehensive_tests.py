#!/usr/bin/env python3
"""
Comprehensive Test Runner for Enhanced Memory Pipeline v4.0

This script runs all tests to validate the user ID extraction,
memory management, and pipeline integration functionality.

Usage:
    python run_comprehensive_tests.py [--unit-only] [--integration-only] [--live-only]
"""

import sys
import os
import subprocess
import argparse
import json
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def print_banner(title: str):
    """Print a formatted banner"""
    print("\n" + "="*80)
    print(f"🧪 {title}")
    print("="*80)


def run_unit_tests():
    """Run comprehensive unit tests"""
    print_banner("Running Unit Tests")
    
    try:
        # Run the comprehensive unit test suite
        result = subprocess.run([
            sys.executable, 
            "test_comprehensive_user_memory.py"
        ], capture_output=True, text=True, cwd=os.path.dirname(__file__))
        
        print("📋 Unit Test Output:")
        print(result.stdout)
        
        if result.stderr:
            print("⚠️  Unit Test Errors:")
            print(result.stderr)
        
        success = result.returncode == 0
        print(f"\n{'✅' if success else '❌'} Unit Tests {'PASSED' if success else 'FAILED'}")
        
        return success, {
            "exit_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr
        }
        
    except Exception as e:
        print(f"❌ Error running unit tests: {e}")
        return False, {"error": str(e)}


def run_integration_tests():
    """Run live system integration tests"""
    print_banner("Running Live Integration Tests")
    
    try:
        # Run the live integration test suite
        result = subprocess.run([
            sys.executable, 
            "test_live_integration.py"
        ], capture_output=True, text=True, cwd=os.path.dirname(__file__))
        
        print("📋 Integration Test Output:")
        print(result.stdout)
        
        if result.stderr:
            print("⚠️  Integration Test Errors:")
            print(result.stderr)
        
        success = result.returncode == 0
        print(f"\n{'✅' if success else '❌'} Integration Tests {'PASSED' if success else 'FAILED'}")
        
        return success, {
            "exit_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr
        }
        
    except Exception as e:
        print(f"❌ Error running integration tests: {e}")
        return False, {"error": str(e)}


def run_existing_tests():
    """Run existing test suite"""
    print_banner("Running Existing Test Suite")
    
    try:
        # Run existing tests
        result = subprocess.run([
            sys.executable, 
            "run_all_tests.py"
        ], capture_output=True, text=True, cwd=os.path.dirname(__file__))
        
        print("📋 Existing Test Output:")
        print(result.stdout)
        
        if result.stderr:
            print("⚠️  Existing Test Errors:")
            print(result.stderr)
        
        success = result.returncode == 0
        print(f"\n{'✅' if success else '❌'} Existing Tests {'PASSED' if success else 'FAILED'}")
        
        return success, {
            "exit_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr
        }
        
    except Exception as e:
        print(f"❌ Error running existing tests: {e}")
        return False, {"error": str(e)}


def check_system_requirements():
    """Check that the system is ready for testing"""
    print_banner("Checking System Requirements")
    
    requirements = [
        ("Python 3.8+", sys.version_info >= (3, 8)),
        ("pytest", check_package_available("pytest")),
        ("requests", check_package_available("requests")),
    ]
    
    all_met = True
    for req_name, req_met in requirements:
        status = "✅" if req_met else "❌"
        print(f"{status} {req_name}")
        if not req_met:
            all_met = False
    
    return all_met


def check_package_available(package_name: str) -> bool:
    """Check if a Python package is available"""
    try:
        __import__(package_name)
        return True
    except ImportError:
        return False


def check_system_running():
    """Check if the system services are running"""
    print_banner("Checking System Services")
    
    try:
        import requests
        
        services = [
            ("Backend", "http://localhost:3000/health"),
            ("Memory API", "http://localhost:8001/health"),
            ("Pipelines", "http://localhost:9099/"),
            ("OpenWebUI", "http://localhost:8080"),
        ]
        
        all_running = True
        for service_name, url in services:
            try:
                response = requests.get(url, timeout=5)
                running = response.status_code < 500
                status = "✅" if running else "❌"
                print(f"{status} {service_name} ({'Running' if running else 'Not Running'})")
                if not running:
                    all_running = False
            except Exception:
                print(f"❌ {service_name} (Not Accessible)")
                all_running = False
        
        if not all_running:
            print("\n💡 To start the system, run: docker-compose up -d")
        
        return all_running
        
    except ImportError:
        print("❌ requests package not available - cannot check services")
        return False


def generate_final_report(test_results: dict):
    """Generate final comprehensive test report"""
    print_banner("Final Test Report")
    
    total_suites = len(test_results)
    passed_suites = sum(1 for result in test_results.values() if result["success"])
    
    print(f"📊 Test Suite Summary:")
    print(f"   Total Test Suites: {total_suites}")
    print(f"   Passed: {passed_suites} ✅")
    print(f"   Failed: {total_suites - passed_suites} ❌")
    
    print(f"\n📋 Detailed Results:")
    for suite_name, result in test_results.items():
        status = "✅" if result["success"] else "❌"
        print(f"   {status} {suite_name}")
        if not result["success"] and "error" in result["details"]:
            print(f"      Error: {result['details']['error']}")
    
    # Save comprehensive report
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_file = f"comprehensive_test_report_{timestamp}.json"
    
    report_data = {
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "total_suites": total_suites,
            "passed_suites": passed_suites,
            "failed_suites": total_suites - passed_suites,
            "success_rate": (passed_suites / total_suites * 100) if total_suites > 0 else 0
        },
        "test_results": test_results
    }
    
    try:
        with open(report_file, 'w') as f:
            json.dump(report_data, f, indent=2)
        print(f"\n📄 Comprehensive report saved to: {report_file}")
    except Exception as e:
        print(f"\n⚠️  Could not save report: {e}")
    
    # Final verdict
    all_passed = passed_suites == total_suites
    print(f"\n🎯 Overall Result: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
    
    if all_passed:
        print("🎉 Enhanced Memory Pipeline v4.0 is fully validated!")
        print("✅ User ID extraction working correctly")
        print("✅ Memory operations isolated per user")
        print("✅ Pipeline integration functioning") 
        print("✅ No memory bleed detected")
        print("✅ Error handling robust")
    else:
        print("🔧 Some issues detected - please review the test output above")
    
    return all_passed


def main():
    """Main test runner"""
    parser = argparse.ArgumentParser(description="Run comprehensive tests for Enhanced Memory Pipeline v4.0")
    parser.add_argument("--unit-only", action="store_true", help="Run only unit tests")
    parser.add_argument("--integration-only", action="store_true", help="Run only integration tests")
    parser.add_argument("--live-only", action="store_true", help="Run only live system tests")
    parser.add_argument("--skip-existing", action="store_true", help="Skip existing test suite")
    parser.add_argument("--no-system-check", action="store_true", help="Skip system requirements check")
    
    args = parser.parse_args()
    
    print("🚀 Enhanced Memory Pipeline v4.0 - Comprehensive Test Suite")
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check system requirements
    if not args.no_system_check:
        if not check_system_requirements():
            print("\n❌ System requirements not met. Please install missing packages.")
            return 1
    
    # Check if system is running for integration tests
    system_running = True
    if not args.unit_only:
        system_running = check_system_running()
        if not system_running and not args.unit_only:
            print("\n⚠️  System services not running. Some tests may fail.")
            response = input("Continue anyway? (y/N): ")
            if response.lower() != 'y':
                return 1
    
    # Run test suites based on arguments
    test_results = {}
    
    if not args.integration_only and not args.live_only:
        # Run unit tests
        success, details = run_unit_tests()
        test_results["Unit Tests"] = {"success": success, "details": details}
    
    if not args.unit_only and not args.live_only:
        # Run integration tests
        success, details = run_integration_tests()
        test_results["Integration Tests"] = {"success": success, "details": details}
    
    if args.live_only or (not args.unit_only and not args.integration_only and system_running):
        # Run live system tests
        success, details = run_integration_tests()
        test_results["Live System Tests"] = {"success": success, "details": details}
    
    if not args.skip_existing and not args.unit_only and not args.integration_only:
        # Run existing test suite
        success, details = run_existing_tests()
        test_results["Existing Tests"] = {"success": success, "details": details}
    
    # Generate final report
    final_success = generate_final_report(test_results)
    
    return 0 if final_success else 1


if __name__ == "__main__":
    exit(main())
