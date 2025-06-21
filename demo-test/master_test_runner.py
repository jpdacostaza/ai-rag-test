#!/usr/bin/env python3
"""
Master Test Runner for Backend Demo Tests
=========================================

This is the main entry point for running comprehensive real-life simulation tests
of the entire backend system. It orchestrates all test modules and provides
unified reporting and analysis.

Test Modules Included:
- comprehensive_test_suite_v2.py: Basic API and integration testing
- tool_integration_tests.py: Comprehensive AI tool testing
- security_tests.py: Authentication, authorization, and security testing
- performance_tests.py: Load testing, performance, and stress testing

Usage:
    python master_test_runner.py --all                    # Run all tests
    python master_test_runner.py --quick                  # Run quick smoke tests
    python master_test_runner.py --tools                  # Run only tool tests
    python master_test_runner.py --security               # Run only security tests
    python master_test_runner.py --performance            # Run only performance tests
    python master_test_runner.py --report-only            # Generate report from existing results

Author: Backend Test Suite
Version: 1.0.0
"""

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


class MasterTestRunner:
    """Master orchestrator for all backend tests."""
    
    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.results_dir = self.base_dir / "results"
        self.results_dir.mkdir(exist_ok=True)
        
        self.test_modules = {
            "comprehensive": "comprehensive_test_suite_v2.py",
            "tools": "tool_integration_tests.py", 
            "security": "security_tests.py",
            "performance": "performance_tests.py"
        }
        
        self.test_results = {}
        self.overall_start_time = time.time()
    
    def check_system_readiness(self) -> bool:
        """Check if the backend system is ready for testing."""
        print("🔍 Checking system readiness...")
        
        try:
            import requests
            response = requests.get("http://localhost:8001/health/simple", timeout=10)
            if response.status_code == 200:
                print("  ✅ Backend system is ready")
                return True
            else:
                print(f"  ❌ Backend health check failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"  ❌ Cannot connect to backend: {e}")
            print("  💡 Make sure the backend is running on http://localhost:8001")
            return False
    
    def run_test_module(self, module_name: str, description: str) -> Dict:
        """Run a specific test module."""
        print(f"\n{'='*60}")
        print(f"🧪 RUNNING {description.upper()}")
        print(f"{'='*60}")
        
        module_file = self.base_dir / self.test_modules[module_name]
        if not module_file.exists():
            return {
                "module": module_name,
                "description": description,
                "success": False,
                "error": f"Test module {module_file} not found",
                "duration": 0
            }
        
        start_time = time.time()
        
        try:
            # Run the test module as a subprocess
            result = subprocess.run(
                [sys.executable, str(module_file)],
                cwd=str(self.base_dir.parent),  # Run from backend root
                capture_output=True,
                text=True,
                timeout=600  # 10 minute timeout
            )
            
            duration = time.time() - start_time
            success = result.returncode == 0
            
            test_result = {
                "module": module_name,
                "description": description,
                "success": success,
                "return_code": result.returncode,
                "duration": f"{duration:.2f}s",
                "stdout": result.stdout,
                "stderr": result.stderr,
                "timestamp": datetime.now().isoformat()
            }
            
            # Try to extract results from the module's output
            if success:
                print(f"  ✅ {description} completed successfully")
            else:
                print(f"  ❌ {description} failed")
                print(f"     Error output: {result.stderr[:200]}..." if result.stderr else "No error output")
            
            return test_result
            
        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            return {
                "module": module_name,
                "description": description,
                "success": False,
                "error": "Test module timed out after 10 minutes",
                "duration": f"{duration:.2f}s",
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            duration = time.time() - start_time
            return {
                "module": module_name,
                "description": description,
                "success": False,
                "error": str(e),
                "duration": f"{duration:.2f}s",
                "timestamp": datetime.now().isoformat()
            }
    
    def run_quick_tests(self):
        """Run a quick smoke test suite."""
        print("🚀 Running Quick Smoke Tests")
        print("=" * 40)
        
        # Just run basic health and auth tests
        result = self.run_test_module("comprehensive", "Quick Integration Tests")
        self.test_results["quick"] = result
    
    def run_all_tests(self):
        """Run all test suites in sequence."""
        print("🚀 Running Complete Test Suite")
        print("=" * 60)
        print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        # Run tests in logical order
        test_sequence = [
            ("comprehensive", "Comprehensive Integration Tests"),
            ("tools", "AI Tool Integration Tests"),
            ("security", "Security & Authentication Tests"),
            ("performance", "Performance & Load Tests")
        ]
        
        for module_name, description in test_sequence:
            result = self.run_test_module(module_name, description)
            self.test_results[module_name] = result
            
            # Brief pause between test suites
            if module_name != test_sequence[-1][0]:  # Not the last test
                print("\n⏳ Waiting 10 seconds before next test suite...")
                time.sleep(10)
    
    def generate_master_report(self):
        """Generate comprehensive master test report."""
        print("\n" + "=" * 80)
        print("📊 MASTER TEST SUITE RESULTS")
        print("=" * 80)
        
        total_duration = time.time() - self.overall_start_time
        
        # Overall statistics
        total_modules = len(self.test_results)
        successful_modules = sum(1 for r in self.test_results.values() if r["success"])
        failed_modules = total_modules - successful_modules
        
        print(f"📋 OVERALL SUMMARY")
        print(f"   Total Test Modules: {total_modules}")
        print(f"   Successful Modules: {successful_modules}")
        print(f"   Failed Modules: {failed_modules}")
        print(f"   Success Rate: {(successful_modules/total_modules*100):.1f}%" if total_modules > 0 else "0%")
        print(f"   Total Duration: {total_duration/60:.1f} minutes")
        
        # Module-by-module results
        print(f"\n📋 MODULE RESULTS")
        for module_name, result in self.test_results.items():
            status = "✅ PASS" if result["success"] else "❌ FAIL"
            duration = result.get("duration", "Unknown")
            print(f"   {status} {result['description']} ({duration})")
            
            if not result["success"]:
                error = result.get("error", "Unknown error")
                print(f"        Error: {error}")
        
        # Collect any generated report files
        report_files = []
        for file_pattern in ["*test_report_*.json", "*results*.json"]:
            report_files.extend(self.base_dir.glob(file_pattern))
        
        if report_files:
            print(f"\n📄 GENERATED REPORTS:")
            for report_file in sorted(report_files):
                print(f"   - {report_file.name}")
        
        # System health recommendations
        print(f"\n💡 RECOMMENDATIONS:")
        
        if failed_modules > 0:
            print("   - Review failed test modules and address issues")
            
        if "security" in self.test_results and not self.test_results["security"]["success"]:
            print("   - Security tests failed - review authentication and security measures")
            
        if "performance" in self.test_results and not self.test_results["performance"]["success"]:
            print("   - Performance tests failed - optimize system resources and caching")
            
        if successful_modules == total_modules:
            print("   - All tests passed! System appears to be functioning correctly")
            print("   - Consider running these tests regularly to ensure continued quality")
        
        # Save master report
        master_report = {
            "summary": {
                "timestamp": datetime.now().isoformat(),
                "total_modules": total_modules,
                "successful_modules": successful_modules,
                "failed_modules": failed_modules,
                "success_rate": f"{(successful_modules/total_modules*100):.1f}%" if total_modules > 0 else "0%",
                "total_duration_minutes": f"{total_duration/60:.1f}"
            },
            "module_results": self.test_results,
            "report_files": [str(f.name) for f in report_files]
        }
        
        master_report_file = self.results_dir / f"master_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        try:
            with open(master_report_file, 'w') as f:
                json.dump(master_report, f, indent=2)
            print(f"\n📊 Master report saved: {master_report_file}")
        except Exception as e:
            print(f"\n⚠️  Could not save master report: {e}")
        
        return successful_modules == total_modules
    
    def print_usage_info(self):
        """Print usage information and available test modules."""
        print("🧪 Backend Demo Test Suite")
        print("=" * 40)
        print("Available test modules:")
        
        descriptions = {
            "comprehensive": "Basic API endpoints, integration, and core functionality",
            "tools": "AI tools (weather, time, math, search, etc.)",
            "security": "Authentication, authorization, input validation, security headers",
            "performance": "Load testing, response times, concurrent requests, memory usage"
        }
        
        for module, desc in descriptions.items():
            print(f"  --{module}: {desc}")
        
        print("\nUsage examples:")
        print("  python master_test_runner.py --all           # Run all tests")
        print("  python master_test_runner.py --quick         # Quick smoke tests")
        print("  python master_test_runner.py --tools         # Only AI tool tests")
        print("  python master_test_runner.py --security      # Only security tests")
        print("  python master_test_runner.py --performance   # Only performance tests")


def main():
    """Main function with command line argument handling."""
    parser = argparse.ArgumentParser(description="Backend Demo Test Suite Master Runner")
    parser.add_argument("--all", action="store_true", help="Run all test suites")
    parser.add_argument("--quick", action="store_true", help="Run quick smoke tests")
    parser.add_argument("--comprehensive", action="store_true", help="Run comprehensive integration tests")
    parser.add_argument("--tools", action="store_true", help="Run AI tool integration tests")
    parser.add_argument("--security", action="store_true", help="Run security tests")
    parser.add_argument("--performance", action="store_true", help="Run performance tests")
    parser.add_argument("--report-only", action="store_true", help="Generate report from existing results")
    parser.add_argument("--help-tests", action="store_true", help="Show detailed test information")
    
    args = parser.parse_args()
    
    runner = MasterTestRunner()
    
    if args.help_tests:
        runner.print_usage_info()
        return 0
    
    if not any(vars(args).values()):
        print("❌ No test option specified. Use --help for usage information or --help-tests for test details.")
        return 1
    
    if not args.report_only:
        # Check system readiness before running tests
        if not runner.check_system_readiness():
            print("\n❌ System not ready for testing. Please start the backend and try again.")
            return 1
        
        print("\n✅ System ready - starting tests...")
        time.sleep(2)
    
    try:
        if args.report_only:
            # Just generate report from existing data
            runner.generate_master_report()
        elif args.all:
            runner.run_all_tests()
            success = runner.generate_master_report()
        elif args.quick:
            runner.run_quick_tests()
            success = runner.generate_master_report()
        elif args.comprehensive:
            result = runner.run_test_module("comprehensive", "Comprehensive Integration Tests")
            runner.test_results["comprehensive"] = result
            success = runner.generate_master_report()
        elif args.tools:
            result = runner.run_test_module("tools", "AI Tool Integration Tests")
            runner.test_results["tools"] = result
            success = runner.generate_master_report()
        elif args.security:
            result = runner.run_test_module("security", "Security & Authentication Tests")
            runner.test_results["security"] = result
            success = runner.generate_master_report()
        elif args.performance:
            result = runner.run_test_module("performance", "Performance & Load Tests")
            runner.test_results["performance"] = result
            success = runner.generate_master_report()
        else:
            print("❌ Invalid test option combination")
            return 1
        
        print("\n🏁 Master test runner completed!")
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Test suite interrupted by user")
        return 1
    except Exception as e:
        print(f"\n\n❌ Master test runner failed: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
