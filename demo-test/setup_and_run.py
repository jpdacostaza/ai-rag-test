#!/usr/bin/env python3
"""
Demo Test Setup and Quick Runner
===============================

This script provides easy setup and execution of the backend demo tests.
It checks prerequisites, sets up the environment, and provides menu-driven
test execution.
"""

import os
import subprocess
import sys
import time
from pathlib import Path


def check_python_version():
    """Check if Python version is adequate."""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        return False
    print(f"✅ Python version: {sys.version.split()[0]}")
    return True


def check_backend_status():
    """Check if backend is running."""
    try:
        import requests
        response = requests.get("http://localhost:8001/health/simple", timeout=5)
        if response.status_code == 200:
            print("✅ Backend is running and responding")
            return True
        else:
            print(f"⚠️  Backend responding with status {response.status_code}")
            return False
    except ImportError:
        print("❌ requests module not available - run: pip install requests")
        return False
    except Exception as e:
        print(f"❌ Backend not accessible: {e}")
        print("   💡 Start the backend with: uvicorn app:app --host 0.0.0.0 --port 8001")
        return False


def check_dependencies():
    """Check required Python packages."""
    required_packages = ["requests", "httpx"]
    missing = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package} is available")
        except ImportError:
            missing.append(package)
            print(f"❌ {package} is missing")
    
    if missing:
        print(f"\n💡 Install missing packages with:")
        print(f"   pip install {' '.join(missing)}")
        return False
    
    return True


def show_main_menu():
    """Display main menu options."""
    print("\n" + "="*50)
    print("🧪 BACKEND DEMO TEST SUITE")
    print("="*50)
    print("1. Quick Health Check (2 min)")
    print("2. Complete Test Suite (15-20 min)")
    print("3. AI Tools Tests Only (5-10 min)")
    print("4. Security Tests Only (3-5 min)")
    print("5. Performance Tests Only (5-10 min)")
    print("6. Check System Status")
    print("7. View Test Documentation")
    print("8. Exit")
    print("="*50)


def run_test_command(command_args):
    """Run a test command and display results."""
    print(f"\n🚀 Executing: python {' '.join(command_args)}")
    print("⏳ Please wait...")
    
    try:
        result = subprocess.run(
            [sys.executable] + command_args,
            cwd=Path(__file__).parent.parent,  # Run from backend root
            text=True,
            capture_output=False  # Show output in real-time
        )
        
        if result.returncode == 0:
            print("\n✅ Tests completed successfully!")
        else:
            print(f"\n❌ Tests completed with issues (exit code: {result.returncode})")
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"\n❌ Error running tests: {e}")
        return False


def show_system_status():
    """Display current system status."""
    print("\n" + "="*40)
    print("📊 SYSTEM STATUS CHECK")
    print("="*40)
    
    # Check Python
    check_python_version()
    
    # Check dependencies
    deps_ok = check_dependencies()
    
    # Check backend
    backend_ok = check_backend_status()
    
    # Check test files
    test_dir = Path(__file__).parent
    test_files = [
        "master_test_runner.py",
        "comprehensive_test_suite_v2.py",
        "tool_integration_tests.py",
        "security_tests.py",
        "performance_tests.py"
    ]
    
    print("\n📁 Test Files:")
    all_files_exist = True
    for file in test_files:
        if (test_dir / file).exists():
            print(f"✅ {file}")
        else:
            print(f"❌ {file} - MISSING")
            all_files_exist = False
    
    print(f"\n📋 OVERALL STATUS:")
    if deps_ok and backend_ok and all_files_exist:
        print("✅ System ready for testing!")
        return True
    else:
        print("❌ System not ready - please resolve issues above")
        return False


def show_documentation():
    """Display test documentation."""
    print("\n" + "="*60)
    print("📚 TEST DOCUMENTATION")
    print("="*60)
    print("""
🧪 AVAILABLE TEST SUITES:

1. QUICK HEALTH CHECK
   - Basic API endpoints
   - Authentication verification
   - Core functionality
   - Duration: ~2 minutes
   - Use: Daily health check

2. COMPLETE TEST SUITE
   - All test modules
   - Comprehensive coverage
   - Full system validation
   - Duration: ~15-20 minutes
   - Use: Weekly/release testing

3. AI TOOLS TESTS
   - Weather, time, math tools
   - Web search, Wikipedia
   - Python code execution
   - Unit conversions
   - Duration: ~5-10 minutes
   - Use: Tool functionality verification

4. SECURITY TESTS
   - Authentication/authorization
   - Input validation
   - Injection attack prevention
   - Security headers
   - Duration: ~3-5 minutes
   - Use: Security validation

5. PERFORMANCE TESTS
   - Response time measurement
   - Concurrent load handling
   - Memory leak detection
   - Cache performance
   - Duration: ~5-10 minutes
   - Use: Performance validation

📊 REPORTS:
All tests generate detailed JSON reports in demo-test/ directory
containing pass/fail statistics, timing data, and recommendations.

🔧 REQUIREMENTS:
- Backend running on http://localhost:8001
- Python 3.8+ with requests, httpx packages
- Redis and ChromaDB services available
- Valid API key configured
""")


def main():
    """Main interactive menu."""
    print("🔍 Checking system prerequisites...")
    
    # Initial checks
    if not check_python_version():
        sys.exit(1)
    
    while True:
        show_main_menu()
        
        try:
            choice = input("\nSelect option (1-8): ").strip()
            
            if choice == "1":
                # Quick health check
                if check_backend_status():
                    run_test_command(["demo-test/master_test_runner.py", "--quick"])
                else:
                    print("❌ Backend not ready for testing")
                    
            elif choice == "2":
                # Complete test suite
                if check_backend_status():
                    print("⚠️  Warning: This will run intensive tests for 15-20 minutes")
                    confirm = input("Continue? (y/N): ").strip().lower()
                    if confirm == 'y':
                        run_test_command(["demo-test/master_test_runner.py", "--all"])
                else:
                    print("❌ Backend not ready for testing")
                    
            elif choice == "3":
                # AI Tools tests
                if check_backend_status():
                    run_test_command(["demo-test/master_test_runner.py", "--tools"])
                else:
                    print("❌ Backend not ready for testing")
                    
            elif choice == "4":
                # Security tests
                if check_backend_status():
                    run_test_command(["demo-test/master_test_runner.py", "--security"])
                else:
                    print("❌ Backend not ready for testing")
                    
            elif choice == "5":
                # Performance tests
                if check_backend_status():
                    print("⚠️  Warning: This will generate significant load on the system")
                    confirm = input("Continue? (y/N): ").strip().lower()
                    if confirm == 'y':
                        run_test_command(["demo-test/master_test_runner.py", "--performance"])
                else:
                    print("❌ Backend not ready for testing")
                    
            elif choice == "6":
                # System status
                show_system_status()
                
            elif choice == "7":
                # Documentation
                show_documentation()
                
            elif choice == "8":
                # Exit
                print("👋 Goodbye!")
                break
                
            else:
                print("❌ Invalid option. Please select 1-8.")
                
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            
        if choice in ["1", "2", "3", "4", "5"]:
            input("\nPress Enter to continue...")


if __name__ == "__main__":
    main()
