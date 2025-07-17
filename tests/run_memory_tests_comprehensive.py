#!/usr/bin/env python3
"""
Memory Test Runner - Run all memory-related tests
"""

import os
import sys
import subprocess
import time
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple

class MemoryTestRunner:
    """Run all memory tests and generate comprehensive report"""
    
    def __init__(self):
        self.test_results = []
        self.start_time = datetime.now()
        self.backend_dir = Path("e:/Projects/opt/backend")
        
    def find_memory_tests(self) -> List[Path]:
        """Find all memory test files"""
        test_files = []
        
        # Root level memory tests
        for pattern in ["test*memory*.py", "test_explicit_memory*.py", "test_pipeline_memory*.py"]:
            test_files.extend(self.backend_dir.glob(pattern))
        
        # Tests subdirectory
        tests_dir = self.backend_dir / "tests"
        if tests_dir.exists():
            for pattern in ["test*memory*.py", "test_*memory*.py"]:
                test_files.extend(tests_dir.glob(pattern))
        
        return sorted(test_files)
    
    def run_single_test(self, test_file: Path) -> Dict:
        """Run a single test file and return results"""
        test_name = test_file.name
        relative_path = test_file.relative_to(self.backend_dir)
        
        print(f"\\n{'='*60}")
        print(f"Running: {relative_path}")
        print(f"{'='*60}")
        
        start_time = time.time()
        
        try:
            # Change to the test file's directory
            test_dir = test_file.parent
            
            # Run the test
            result = subprocess.run(
                [sys.executable, str(test_file)],
                cwd=str(test_dir),
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            duration = time.time() - start_time
            
            # Determine success based on exit code
            success = result.returncode == 0
            
            test_result = {
                "test_name": test_name,
                "relative_path": str(relative_path),
                "success": success,
                "duration": duration,
                "exit_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "timestamp": datetime.now().isoformat()
            }
            
            # Print result
            status = "✅ PASSED" if success else "❌ FAILED"
            print(f"{status} - {test_name} ({duration:.2f}s)")
            
            if not success:
                print("STDERR:")
                print(result.stderr)
                print("STDOUT:")
                print(result.stdout[:1000] + "..." if len(result.stdout) > 1000 else result.stdout)
            
            return test_result
            
        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            test_result = {
                "test_name": test_name,
                "relative_path": str(relative_path),
                "success": False,
                "duration": duration,
                "exit_code": -1,
                "stdout": "",
                "stderr": "Test timed out after 5 minutes",
                "timestamp": datetime.now().isoformat()
            }
            print(f"❌ TIMEOUT - {test_name} ({duration:.2f}s)")
            return test_result
            
        except Exception as e:
            duration = time.time() - start_time
            test_result = {
                "test_name": test_name,
                "relative_path": str(relative_path),
                "success": False,
                "duration": duration,
                "exit_code": -1,
                "stdout": "",
                "stderr": f"Exception: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
            print(f"❌ ERROR - {test_name} ({duration:.2f}s): {str(e)}")
            return test_result
    
    def run_all_tests(self) -> Dict:
        """Run all memory tests and return summary"""
        print("MEMORY TEST RUNNER - RAG DUAL-DATABASE SYSTEM")
        print("=" * 60)
        
        test_files = self.find_memory_tests()
        
        if not test_files:
            print("❌ No memory test files found!")
            return {
                "summary": {
                    "total_tests": 0,
                    "passed": 0,
                    "failed": 0,
                    "success_rate": 0,
                    "total_duration": 0
                },
                "test_results": []
            }
        
        print(f"Found {len(test_files)} memory test files")
        print()
        
        # Run each test
        for test_file in test_files:
            result = self.run_single_test(test_file)
            self.test_results.append(result)
        
        # Calculate summary
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r["success"])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        total_duration = sum(r["duration"] for r in self.test_results)
        
        summary = {
            "total_tests": total_tests,
            "passed": passed_tests,
            "failed": failed_tests,
            "success_rate": success_rate,
            "total_duration": total_duration,
            "run_timestamp": self.start_time.isoformat()
        }
        
        return {
            "summary": summary,
            "test_results": self.test_results
        }
    
    def print_summary(self, results: Dict):
        """Print test summary"""
        summary = results["summary"]
        
        print("\\n" + "=" * 60)
        print("MEMORY TEST SUMMARY")
        print("=" * 60)
        
        print(f"Total Tests: {summary['total_tests']}")
        print(f"Passed: {summary['passed']}")
        print(f"Failed: {summary['failed']}")
        print(f"Success Rate: {summary['success_rate']:.1f}%")
        print(f"Total Duration: {summary['total_duration']:.2f}s")
        print(f"Run Time: {self.start_time}")
        
        if summary['failed'] > 0:
            print("\\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['test_name']} ({result['duration']:.2f}s)")
                    if result["stderr"]:
                        print(f"    Error: {result['stderr'][:200]}...")
        
        if summary['passed'] > 0:
            print("\\n✅ PASSED TESTS:")
            for result in self.test_results:
                if result["success"]:
                    print(f"  - {result['test_name']} ({result['duration']:.2f}s)")
    
    def save_report(self, results: Dict):
        """Save detailed test report"""
        report_path = self.backend_dir / "logs" / "memory_test_report.json"
        report_path.parent.mkdir(exist_ok=True)
        
        with open(report_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\\nDetailed report saved to: {report_path}")
        
        # Also save a summary report
        summary_path = self.backend_dir / "logs" / "memory_test_summary.md"
        with open(summary_path, 'w') as f:
            f.write("# Memory Test Summary\\n\\n")
            f.write(f"**Run Time**: {self.start_time}\\n")
            f.write(f"**Total Tests**: {results['summary']['total_tests']}\\n")
            f.write(f"**Passed**: {results['summary']['passed']}\\n")
            f.write(f"**Failed**: {results['summary']['failed']}\\n")
            f.write(f"**Success Rate**: {results['summary']['success_rate']:.1f}%\\n")
            f.write(f"**Total Duration**: {results['summary']['total_duration']:.2f}s\\n\\n")
            
            if results['summary']['failed'] > 0:
                f.write("## Failed Tests\\n\\n")
                for result in self.test_results:
                    if not result["success"]:
                        f.write(f"- **{result['test_name']}** ({result['duration']:.2f}s)\\n")
                        if result["stderr"]:
                            f.write(f"  - Error: {result['stderr'][:200]}...\\n")
                f.write("\\n")
            
            if results['summary']['passed'] > 0:
                f.write("## Passed Tests\\n\\n")
                for result in self.test_results:
                    if result["success"]:
                        f.write(f"- **{result['test_name']}** ({result['duration']:.2f}s)\\n")
        
        print(f"Summary report saved to: {summary_path}")


def main():
    """Main function"""
    runner = MemoryTestRunner()
    
    try:
        results = runner.run_all_tests()
        runner.print_summary(results)
        runner.save_report(results)
        
        # Exit with appropriate code
        sys.exit(0 if results['summary']['failed'] == 0 else 1)
        
    except KeyboardInterrupt:
        print("\\n❌ Test run interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\\n❌ Test runner failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
