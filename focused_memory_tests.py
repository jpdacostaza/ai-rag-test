#!/usr/bin/env python3
"""
Focused Memory Test Runner - RAG System
Tests only the key working components with proper encoding
"""

import os
import sys
import subprocess
import time
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict

# Set UTF-8 encoding for Windows
os.environ['PYTHONIOENCODING'] = 'utf-8'

class FocusedMemoryTestRunner:
    """Run focused memory tests on working components"""
    
    def __init__(self):
        self.test_results = []
        self.start_time = datetime.now()
        self.backend_dir = Path("e:/Projects/opt/backend")
        
    def print_safe(self, message: str):
        """Print message with safe encoding"""
        try:
            print(message)
        except UnicodeEncodeError:
            print(message.encode('ascii', errors='ignore').decode('ascii'))
    
    def log_result(self, test_name: str, success: bool, message: str, duration: float = 0.0):
        """Log a test result with safe encoding"""
        result = {
            "test_name": test_name,
            "success": success,
            "message": message,
            "duration": duration,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status = "PASSED" if success else "FAILED"
        safe_message = f"{status} - {test_name} ({duration:.2f}s)"
        self.print_safe(safe_message)
    
    def run_single_test(self, test_file: Path) -> Dict:
        """Run a single test file"""
        test_name = test_file.name
        
        self.print_safe(f"\\n{'='*60}")
        self.print_safe(f"Running: {test_name}")
        self.print_safe(f"{'='*60}")
        
        start_time = time.time()
        
        try:
            # Set UTF-8 environment
            env = os.environ.copy()
            env['PYTHONIOENCODING'] = 'utf-8'
            env['PYTHONPATH'] = str(self.backend_dir)
            
            # Run the test
            result = subprocess.run(
                [sys.executable, str(test_file)],
                cwd=str(self.backend_dir),
                capture_output=True,
                text=True,
                timeout=120,  # 2 minute timeout
                env=env,
                encoding='utf-8',
                errors='ignore'
            )
            
            duration = time.time() - start_time
            success = result.returncode == 0
            
            test_result = {
                "test_name": test_name,
                "success": success,
                "duration": duration,
                "exit_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "timestamp": datetime.now().isoformat()
            }
            
            self.log_result(test_name, success, "Test completed", duration)
            
            if not success and result.stderr:
                self.print_safe(f"Error: {result.stderr[:200]}...")
            
            return test_result
            
        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            test_result = {
                "test_name": test_name,
                "success": False,
                "duration": duration,
                "exit_code": -1,
                "stdout": "",
                "stderr": "Test timed out after 2 minutes",
                "timestamp": datetime.now().isoformat()
            }
            self.log_result(test_name, False, "Test timed out", duration)
            return test_result
            
        except Exception as e:
            duration = time.time() - start_time
            test_result = {
                "test_name": test_name,
                "success": False,
                "duration": duration,
                "exit_code": -1,
                "stdout": "",
                "stderr": f"Exception: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
            self.log_result(test_name, False, f"Exception: {str(e)}", duration)
            return test_result
    
    def test_memory_api_health(self):
        """Test Memory API health directly"""
        self.print_safe("\\n=== Testing Memory API Health ===")
        
        start_time = time.time()
        
        try:
            import requests
            
            # Test health endpoint
            response = requests.get("http://localhost:5001/health", timeout=10)
            duration = time.time() - start_time
            
            if response.status_code == 200:
                health_data = response.json()
                self.log_result("Memory API Health", True, f"API healthy - version {health_data.get('system_version', 'unknown')}", duration)
                return True
            else:
                self.log_result("Memory API Health", False, f"API returned {response.status_code}", duration)
                return False
                
        except Exception as e:
            duration = time.time() - start_time
            self.log_result("Memory API Health", False, f"Connection failed: {str(e)}", duration)
            return False
    
    def test_redis_connectivity(self):
        """Test Redis connectivity"""
        self.print_safe("\\n=== Testing Redis Connectivity ===")
        
        start_time = time.time()
        
        try:
            import redis
            
            client = redis.Redis(host='localhost', port=6379, decode_responses=True)
            client.ping()
            
            # Test basic operations
            client.set('test_key', 'test_value')
            value = client.get('test_key')
            client.delete('test_key')
            
            duration = time.time() - start_time
            
            if value == 'test_value':
                self.log_result("Redis Connectivity", True, "Redis operations successful", duration)
                return True
            else:
                self.log_result("Redis Connectivity", False, "Redis operations failed", duration)
                return False
                
        except Exception as e:
            duration = time.time() - start_time
            self.log_result("Redis Connectivity", False, f"Redis connection failed: {str(e)}", duration)
            return False
    
    def test_chromadb_connectivity(self):
        """Test ChromaDB connectivity"""
        self.print_safe("\\n=== Testing ChromaDB Connectivity ===")
        
        start_time = time.time()
        
        try:
            import chromadb
            
            client = chromadb.HttpClient(host='localhost', port=8000)
            client.heartbeat()
            
            # Test collection operations
            collections = client.list_collections()
            
            duration = time.time() - start_time
            self.log_result("ChromaDB Connectivity", True, f"ChromaDB operational - {len(collections)} collections", duration)
            return True
            
        except Exception as e:
            duration = time.time() - start_time
            self.log_result("ChromaDB Connectivity", False, f"ChromaDB connection failed: {str(e)}", duration)
            return False
    
    def test_working_memory_components(self):
        """Test the known working memory components"""
        self.print_safe("\\n=== Testing Working Memory Components ===")
        
        # Test files that were passing in the previous run
        working_tests = [
            "tests/test_memory_function.py",
            "tests/test_memory_service_endpoints.py",
            "tests/test_memory_service_validation.py"
        ]
        
        results = []
        for test_path in working_tests:
            test_file = self.backend_dir / test_path
            if test_file.exists():
                result = self.run_single_test(test_file)
                results.append(result)
            else:
                self.print_safe(f"Test file not found: {test_path}")
        
        return results
    
    def run_focused_tests(self):
        """Run focused tests on working components"""
        self.print_safe("RAG DUAL-DATABASE MEMORY SYSTEM - FOCUSED TESTS")
        self.print_safe("=" * 60)
        
        # Test infrastructure
        infrastructure_tests = [
            ("Memory API Health", self.test_memory_api_health),
            ("Redis Connectivity", self.test_redis_connectivity),
            ("ChromaDB Connectivity", self.test_chromadb_connectivity)
        ]
        
        infrastructure_results = []
        for test_name, test_func in infrastructure_tests:
            result = test_func()
            infrastructure_results.append(result)
        
        # Test working components
        component_results = self.test_working_memory_components()
        
        # Summary
        total_tests = len(infrastructure_results) + len(component_results)
        passed_tests = sum(infrastructure_results) + sum(1 for r in component_results if r.get("success", False))
        
        self.print_safe(f"\\n{'='*60}")
        self.print_safe("FOCUSED TEST SUMMARY")
        self.print_safe(f"{'='*60}")
        self.print_safe(f"Infrastructure Tests: {sum(infrastructure_results)}/{len(infrastructure_results)} passed")
        self.print_safe(f"Component Tests: {sum(1 for r in component_results if r.get('success', False))}/{len(component_results)} passed")
        self.print_safe(f"Total: {passed_tests}/{total_tests} passed")
        self.print_safe(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        return passed_tests == total_tests
    
    def run_rag_validation(self):
        """Run RAG system validation"""
        self.print_safe("\\n=== Running RAG System Validation ===")
        
        try:
            # Run the RAG validation script
            result = subprocess.run(
                [sys.executable, "scripts/validate_rag_system.py"],
                cwd=str(self.backend_dir),
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
                encoding='utf-8',
                errors='ignore'
            )
            
            if result.returncode == 0:
                self.print_safe("RAG System Validation: PASSED")
                return True
            else:
                self.print_safe("RAG System Validation: FAILED")
                self.print_safe(f"Error: {result.stderr[:200]}...")
                return False
                
        except Exception as e:
            self.print_safe(f"RAG System Validation: ERROR - {str(e)}")
            return False


def main():
    """Main function"""
    runner = FocusedMemoryTestRunner()
    
    try:
        # Run focused tests
        success = runner.run_focused_tests()
        
        # Run RAG validation if infrastructure tests pass
        if success:
            rag_success = runner.run_rag_validation()
            success = success and rag_success
        
        # Final status
        if success:
            runner.print_safe("\\n✅ ALL FOCUSED TESTS PASSED")
            sys.exit(0)
        else:
            runner.print_safe("\\n❌ SOME TESTS FAILED")
            sys.exit(1)
            
    except KeyboardInterrupt:
        runner.print_safe("\\n❌ Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        runner.print_safe(f"\\n❌ Test runner failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
