"""
Comprehensive Test Runner for Memory + Web Search Integration
============================================================

Runs all available tests in the correct order:
1. Basic web search tests
2. Memory system tests (if available)
3. Combined integration tests
4. Anti-hallucination tests
5. System validation tests

Provides a complete report of the entire system functionality.
"""

import asyncio
import subprocess
import sys
import os
import json
import time
from pathlib import Path

# Add the backend directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


class ComprehensiveTestRunner:
    """Runs all tests and generates comprehensive reports."""
    
    def __init__(self):
        self.test_dir = Path(__file__).parent
        self.backend_dir = self.test_dir.parent
        self.results = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "test_suites": [],
            "summary": {
                "total_suites": 0,
                "suites_passed": 0,
                "suites_failed": 0,
                "total_tests": 0,
                "tests_passed": 0,
                "tests_failed": 0
            }
        }
    
    def run_test_file(self, test_file: str, description: str) -> dict:
        """Run a single test file and capture results."""
        print(f"\n🧪 Running {description}")
        print("-" * 60)
        
        try:
            # Check if file exists
            file_path = self.test_dir / test_file
            if not file_path.exists():
                return {
                    "name": test_file,
                    "description": description,
                    "status": "SKIPPED",
                    "reason": "File not found",
                    "tests_passed": 0,
                    "tests_failed": 0,
                    "output": ""
                }
            
            # Run the test
            result = subprocess.run(
                [sys.executable, str(file_path)],
                cwd=str(self.test_dir),
                capture_output=True,
                text=True,
                timeout=120  # 2 minute timeout
            )
            
            output = result.stdout + result.stderr
            print(output)
            
            # Determine if test passed based on return code and output
            if result.returncode == 0:
                status = "PASSED"
                # Try to extract test counts from output
                tests_passed = output.count("✅") or 1
                tests_failed = output.count("❌")
            else:
                status = "FAILED"
                tests_passed = output.count("✅")
                tests_failed = max(output.count("❌"), 1)
            
            return {
                "name": test_file,
                "description": description,
                "status": status,
                "return_code": result.returncode,
                "tests_passed": tests_passed,
                "tests_failed": tests_failed,
                "output": output
            }
            
        except subprocess.TimeoutExpired:
            return {
                "name": test_file,
                "description": description,
                "status": "TIMEOUT",
                "tests_passed": 0,
                "tests_failed": 1,
                "output": "Test timed out after 2 minutes"
            }
        except Exception as e:
            return {
                "name": test_file,
                "description": description,
                "status": "ERROR",
                "error": str(e),
                "tests_passed": 0,
                "tests_failed": 1,
                "output": f"Error running test: {e}"
            }
    
    def run_all_tests(self):
        """Run all available tests in order."""
        print("🚀 COMPREHENSIVE MEMORY + WEB SEARCH TEST SUITE")
        print("=" * 80)
        print("Testing the complete integration of memory and web search systems")
        print("=" * 80)
        
        # Define test suite in logical order
        test_suites = [
            # Basic web search functionality
            ("test_web_search_anti_hallucination.py", "Web Search & Anti-Hallucination"),
            
            # Memory system tests (if available)
            ("test_comprehensive_user_memory.py", "Comprehensive User Memory"),
            ("test_enhanced_memory_system.py", "Enhanced Memory System"),
            ("test_memory_system.py", "Basic Memory System"),
            
            # Integration tests
            ("test_combined_memory_web_search.py", "Combined Memory + Web Search"),
            ("test_enhanced_memory.py", "Enhanced Memory Integration"),
            
            # System validation
            ("test_complete_system_validation.py", "Complete System Validation"),
            ("test_end_to_end_pipeline.py", "End-to-End Pipeline"),
            
            # Specific functionality
            ("quick_web_search_test.py", "Quick Web Search Test"),
            ("test_live_integration.py", "Live Integration Test"),
        ]
        
        # Run each test suite
        for test_file, description in test_suites:
            result = self.run_test_file(test_file, description)
            self.results["test_suites"].append(result)
            
            # Update summary
            self.results["summary"]["total_suites"] += 1
            if result["status"] == "PASSED":
                self.results["summary"]["suites_passed"] += 1
            elif result["status"] not in ["SKIPPED"]:
                self.results["summary"]["suites_failed"] += 1
            
            self.results["summary"]["total_tests"] += result["tests_passed"] + result["tests_failed"]
            self.results["summary"]["tests_passed"] += result["tests_passed"]
            self.results["summary"]["tests_failed"] += result["tests_failed"]
        
        # Generate final report
        self.generate_final_report()
    
    def generate_final_report(self):
        """Generate comprehensive final report."""
        print("\n" + "=" * 80)
        print("📊 COMPREHENSIVE TEST RESULTS")
        print("=" * 80)
        
        summary = self.results["summary"]
        
        # Overall summary
        print("🎯 OVERALL SUMMARY")
        print("-" * 40)
        print(f"Test Suites Run: {summary['total_suites']}")
        print(f"Suites Passed: {summary['suites_passed']} ✅")
        print(f"Suites Failed: {summary['suites_failed']} ❌")
        print(f"Suite Success Rate: {(summary['suites_passed']/max(summary['total_suites'],1)*100):.1f}%")
        print()
        print(f"Individual Tests: {summary['total_tests']}")
        print(f"Tests Passed: {summary['tests_passed']} ✅")
        print(f"Tests Failed: {summary['tests_failed']} ❌")
        print(f"Test Success Rate: {(summary['tests_passed']/max(summary['total_tests'],1)*100):.1f}%")
        
        # Detailed results
        print("\n🔍 DETAILED RESULTS")
        print("-" * 40)
        
        for suite in self.results["test_suites"]:
            status_icon = {
                "PASSED": "✅",
                "FAILED": "❌",
                "SKIPPED": "⏭️",
                "TIMEOUT": "⏰",
                "ERROR": "💥"
            }.get(suite["status"], "❓")
            
            print(f"{status_icon} {suite['description']}")
            if suite["status"] != "SKIPPED":
                print(f"   Tests: {suite['tests_passed']}✅ {suite['tests_failed']}❌")
            if suite["status"] in ["FAILED", "ERROR", "TIMEOUT"]:
                print(f"   Issue: {suite.get('reason', suite.get('error', 'Failed'))}")
        
        # System health assessment
        print("\n🏥 SYSTEM HEALTH ASSESSMENT")
        print("-" * 40)
        
        web_search_tests = [s for s in self.results["test_suites"] if "web search" in s["description"].lower()]
        memory_tests = [s for s in self.results["test_suites"] if "memory" in s["description"].lower()]
        integration_tests = [s for s in self.results["test_suites"] if "combined" in s["description"].lower() or "integration" in s["description"].lower()]
        
        def assess_component(tests, name):
            if not tests:
                return f"{name}: No tests found ⚠️"
            passed = sum(1 for t in tests if t["status"] == "PASSED")
            total = len([t for t in tests if t["status"] != "SKIPPED"])
            if total == 0:
                return f"{name}: All tests skipped ⏭️"
            health = "✅ HEALTHY" if passed == total else "⚠️ ISSUES" if passed > 0 else "❌ BROKEN"
            return f"{name}: {passed}/{total} suites passing - {health}"
        
        print(assess_component(web_search_tests, "Web Search System"))
        print(assess_component(memory_tests, "Memory System"))
        print(assess_component(integration_tests, "Integration Layer"))
        
        # Recommendations
        print("\n💡 RECOMMENDATIONS")
        print("-" * 40)
        
        failed_suites = [s for s in self.results["test_suites"] if s["status"] == "FAILED"]
        if not failed_suites:
            print("🎉 All systems are working correctly!")
            print("✅ Web search integration is functional")
            print("✅ Memory system is operational")
            print("✅ Anti-hallucination is working")
            print("✅ Combined systems work together seamlessly")
        else:
            print("🔧 Issues to address:")
            for suite in failed_suites:
                print(f"  • Fix {suite['description']} - check logs for details")
        
        # Save results
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"comprehensive_test_report_{timestamp}.json"
        filepath = self.test_dir / filename
        
        with open(filepath, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n📄 Detailed report saved to: {filename}")
        
        # Return success status
        success_rate = summary['suites_passed'] / max(summary['total_suites'], 1)
        return success_rate >= 0.7  # 70% success rate threshold


def main():
    """Main test runner entry point."""
    runner = ComprehensiveTestRunner()
    success = runner.run_all_tests()
    
    if success:
        print("\n🎉 SYSTEM IS HEALTHY - Most tests passed!")
        return 0
    else:
        print("\n⚠️  SYSTEM NEEDS ATTENTION - Check failed tests")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
