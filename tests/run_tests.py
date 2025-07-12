"""
Memory System Test Runner
========================

Comprehensive test runner for the memory system with detailed reporting.
"""

import subprocess
import sys
import time
import asyncio
import httpx
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tests.conftest import TEST_CONFIG


class TestRunner:
    """Test runner with pre-flight checks and reporting."""
    
    def __init__(self):
        self.services_status = {}
        self.test_results = {}
    
    async def check_services(self):
        """Check that all required services are running."""
        print("🔍 Checking service availability...")
        
        services = {
            "Backend": f"{TEST_CONFIG['backend_url']}/health",
            "Memory API": f"{TEST_CONFIG['memory_api_url']}/health", 
            "Pipelines": f"{TEST_CONFIG['pipelines_url']}/"
        }
        
        async with httpx.AsyncClient(timeout=10) as client:
            for service_name, url in services.items():
                try:
                    response = await client.get(url)
                    if response.status_code < 400:
                        self.services_status[service_name] = "✅ Running"
                        print(f"  {service_name}: ✅ Running")
                    else:
                        self.services_status[service_name] = f"❌ Error {response.status_code}"
                        print(f"  {service_name}: ❌ Error {response.status_code}")
                except Exception as e:
                    self.services_status[service_name] = f"❌ Unavailable ({str(e)[:50]})"
                    print(f"  {service_name}: ❌ Unavailable")
        
        all_running = all("✅" in status for status in self.services_status.values())
        if not all_running:
            print("\n⚠️  Some services are not available. Tests may fail.")
            return False
        
        print("✅ All services are running!")
        return True
    
    def install_dependencies(self):
        """Install required test dependencies."""
        print("📦 Installing test dependencies...")
        
        dependencies = ["pytest", "pytest-asyncio", "httpx"]
        
        for dep in dependencies:
            try:
                subprocess.check_call([
                    sys.executable, "-m", "pip", "install", dep
                ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                print(f"  ✅ {dep}")
            except subprocess.CalledProcessError:
                print(f"  ❌ Failed to install {dep}")
                return False
        
        return True
    
    def run_tests(self, test_file=None, verbose=True):
        """Run the test suite."""
        print(f"\n🧪 Running memory system tests...")
        
        # Build pytest command
        cmd = [sys.executable, "-m", "pytest"]
        
        if test_file:
            cmd.append(f"tests/{test_file}")
        else:
            cmd.append("tests/")
        
        if verbose:
            cmd.extend(["-v", "--tb=short"])
        
        # Add asyncio mode
        cmd.extend(["--asyncio-mode=auto"])
        
        # Run tests
        start_time = time.time()
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=project_root)
            duration = time.time() - start_time
            
            print(f"\n📊 Test Results (completed in {duration:.2f}s)")
            print("=" * 50)
            
            # Parse output for summary
            if result.returncode == 0:
                print("✅ All tests passed!")
            else:
                print("❌ Some tests failed")
            
            # Show output
            if result.stdout:
                print("\n📝 Test Output:")
                print(result.stdout)
            
            if result.stderr and result.stderr.strip():
                print("\n⚠️  Warnings/Errors:")
                print(result.stderr)
            
            return result.returncode == 0
            
        except Exception as e:
            print(f"❌ Error running tests: {e}")
            return False
    
    def generate_report(self):
        """Generate a test report."""
        print("\n📋 Test Report")
        print("=" * 50)
        
        print("\n🔧 Service Status:")
        for service, status in self.services_status.items():
            print(f"  {service}: {status}")
        
        print(f"\n🕒 Test run completed at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    async def run_all(self):
        """Run complete test suite with pre-checks."""
        print("🚀 Memory System Test Suite")
        print("=" * 50)
        
        # Install dependencies
        if not self.install_dependencies():
            print("❌ Failed to install dependencies")
            return False
        
        # Check services
        services_ok = await self.check_services()
        
        # Run tests
        test_results = {}
        
        # Run main memory system tests
        print(f"\n{'='*50}")
        print("🧪 Running Memory System Tests")
        test_results["memory_system"] = self.run_tests("test_memory_system.py")
        
        # Run memory function tests
        print(f"\n{'='*50}")
        print("🧪 Running Memory Function Tests")
        test_results["memory_function"] = self.run_tests("test_memory_function.py")
        
        # Generate report
        self.test_results = test_results
        self.generate_report()
        
        # Summary
        passed_tests = sum(1 for result in test_results.values() if result)
        total_tests = len(test_results)
        
        print(f"\n🎯 Final Results: {passed_tests}/{total_tests} test suites passed")
        
        if passed_tests == total_tests:
            print("🎉 All test suites completed successfully!")
            return True
        else:
            print("⚠️  Some test suites had failures")
            return False


async def main():
    """Main test runner entry point."""
    runner = TestRunner()
    success = await runner.run_all()
    
    if success:
        print("\n✅ Memory system testing completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Memory system testing completed with issues")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
