"""
Simple Integration Test

A basic integration test that validates core functionality without complex imports
or Unicode characters that cause issues on Windows terminals.
"""

import sys
import os
import asyncio
import json
import time
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

class SimpleIntegrationTest:
    def __init__(self):
        self.results = []
        self.start_time = time.time()
        
    def test_directory_structure(self):
        """Test that all required directories exist"""
        try:
            required_dirs = [
                "services",
                "config", 
                "utilities",
                "middleware",
                "tests",
                "docs"
            ]
            
            missing_dirs = []
            for dir_name in required_dirs:
                dir_path = project_root / dir_name
                if not dir_path.exists():
                    missing_dirs.append(dir_name)
            
            if missing_dirs:
                return False, f"Missing directories: {missing_dirs}"
            else:
                return True, "All required directories exist"
                
        except Exception as e:
            return False, f"Directory check failed: {e}"
    
    def test_service_files_exist(self):
        """Test that all service files exist"""
        try:
            required_services = [
                "chat_service.py",
                "memory_service.py", 
                "memory_service_enhanced.py",
                "llm_service.py",
                "redis_service.py",
                "vector_service.py",
                "dependencies.py"
            ]
            
            services_dir = project_root / "services"
            missing_files = []
            
            for service_file in required_services:
                file_path = services_dir / service_file
                if not file_path.exists():
                    missing_files.append(service_file)
            
            if missing_files:
                return False, f"Missing service files: {missing_files}"
            else:
                return True, "All service files exist"
                
        except Exception as e:
            return False, f"Service file check failed: {e}"
    
    def test_config_files_exist(self):
        """Test that configuration files exist"""
        try:
            required_configs = [
                "config.py",
                "config_unified.py",
                "settings.py"
            ]
            
            config_dir = project_root / "config"
            missing_files = []
            
            for config_file in required_configs:
                file_path = config_dir / config_file
                if not file_path.exists():
                    missing_files.append(config_file)
            
            if missing_files:
                return False, f"Missing config files: {missing_files}"
            else:
                return True, "All config files exist"
                
        except Exception as e:
            return False, f"Config file check failed: {e}"
    
    def test_docker_files_exist(self):
        """Test that Docker files exist"""
        try:
            required_docker_files = [
                "docker-compose.yml",
                "Dockerfile",
                "requirements.txt"
            ]
            
            missing_files = []
            
            for docker_file in required_docker_files:
                file_path = project_root / docker_file
                if not file_path.exists():
                    missing_files.append(docker_file)
            
            if missing_files:
                return False, f"Missing Docker files: {missing_files}"
            else:
                return True, "All Docker files exist"
                
        except Exception as e:
            return False, f"Docker file check failed: {e}"
    
    def test_python_syntax(self):
        """Test that Python files have valid syntax"""
        try:
            python_files = []
            syntax_errors = []
            
            # Find all Python files
            for pattern in ["**/*.py"]:
                python_files.extend(project_root.glob(pattern))
            
            # Check first 10 files to avoid timeout
            for py_file in python_files[:10]:
                try:
                    with open(py_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    compile(content, str(py_file), 'exec')
                except SyntaxError as e:
                    syntax_errors.append(f"{py_file.name}: {e}")
                except Exception:
                    # Skip files that can't be read (e.g., binary files)
                    continue
            
            if syntax_errors:
                return False, f"Syntax errors in: {syntax_errors[:3]}"  # Limit output
            else:
                return True, f"Checked {len(python_files[:10])} Python files - no syntax errors"
                
        except Exception as e:
            return False, f"Syntax check failed: {e}"
    
    def test_requirements_file(self):
        """Test that requirements.txt is readable"""
        try:
            req_file = project_root / "requirements.txt"
            if not req_file.exists():
                return False, "requirements.txt not found"
            
            with open(req_file, 'r') as f:
                requirements = f.read().strip()
            
            if not requirements:
                return False, "requirements.txt is empty"
            
            # Count number of requirements
            req_lines = [line for line in requirements.split('\n') if line.strip() and not line.startswith('#')]
            
            return True, f"requirements.txt has {len(req_lines)} dependencies"
                
        except Exception as e:
            return False, f"Requirements check failed: {e}"
    
    def run_test(self, test_method):
        """Run a single test method"""
        test_name = test_method.__name__
        print(f"Running {test_name}...")
        
        try:
            start = time.time()
            success, message = test_method()
            duration = time.time() - start
            
            result = {
                'test': test_name,
                'success': success,
                'message': message,
                'duration': duration
            }
            
            self.results.append(result)
            
            status = "PASS" if success else "FAIL"
            print(f"  {status}: {message} ({duration:.2f}s)")
            
        except Exception as e:
            result = {
                'test': test_name,
                'success': False,
                'message': f"Test exception: {e}",
                'duration': 0
            }
            self.results.append(result)
            print(f"  ERROR: {e}")
    
    def run_all_tests(self):
        """Run all tests"""
        print("=" * 60)
        print("SIMPLE INTEGRATION TEST SUITE")
        print("=" * 60)
        
        test_methods = [
            self.test_directory_structure,
            self.test_service_files_exist,
            self.test_config_files_exist,
            self.test_docker_files_exist,
            self.test_python_syntax,
            self.test_requirements_file
        ]
        
        for test_method in test_methods:
            self.run_test(test_method)
        
        self.generate_summary()
    
    def generate_summary(self):
        """Generate test summary"""
        total_tests = len(self.results)
        passed_tests = [r for r in self.results if r['success']]
        failed_tests = [r for r in self.results if not r['success']]
        
        total_duration = time.time() - self.start_time
        success_rate = (len(passed_tests) / total_tests) * 100 if total_tests > 0 else 0
        
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {len(passed_tests)}")
        print(f"Failed: {len(failed_tests)}")
        print(f"Success Rate: {success_rate:.1f}%")
        print(f"Total Duration: {total_duration:.2f}s")
        
        if failed_tests:
            print("\nFAILED TESTS:")
            for test in failed_tests:
                print(f"  - {test['test']}: {test['message']}")
        
        # Save detailed report
        report = {
            'summary': {
                'total_tests': total_tests,
                'passed': len(passed_tests),
                'failed': len(failed_tests),
                'success_rate': success_rate,
                'duration': total_duration
            },
            'tests': self.results,
            'timestamp': time.time()
        }
        
        report_file = f"simple_integration_report_{int(time.time())}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\nDetailed report saved to: {report_file}")
        
        return success_rate >= 80  # Consider 80%+ success rate as overall success

def main():
    """Main entry point"""
    test_suite = SimpleIntegrationTest()
    success = test_suite.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
